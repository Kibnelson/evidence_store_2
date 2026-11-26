#!/usr/bin/env python3
"""Run one 1P/3D MT-RAG lifecycle arm in a four-GPU Slurm allocation."""

import argparse
from collections import Counter
from contextlib import ExitStack
from hashlib import sha256
import json
import mmap
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from lifecycle_nixl import nixl_block_receipt, nixl_metrics
from lifecycle_receipts import Trace, prefix_keys, restore_receipt, storage_ready, store_sources


def http(port, path, timeout, body=None):
    encoded = None if body is None else json.dumps(body).encode()
    request = Request(f"http://127.0.0.1:{port}{path}", encoded,
                      {"Content-Type": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        content = response.read()
    return json.loads(content) if content else {}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def stop_process(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            pass
    # An engine child may still own a GPU after its API process exits.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


DECODE_OUTPUT_TOKENS = 8
WORKERS = ("p0", "d0", "d1", "d2")
L1_BUDGET_GB = 8


def deployment_from_env(env):
    handoff = env.get("EVIDENCESTORE_PD_HANDOFF", "lmcache")
    supported = {"lmcache": "shared", "nixl": "per_engine"}
    if handoff not in supported:
        raise ValueError("EVIDENCESTORE_PD_HANDOFF must be lmcache or nixl")
    topology = env.get("EVIDENCESTORE_LMCACHE_TOPOLOGY", supported[handoff])
    if topology != supported[handoff]:
        raise ValueError(f"{handoff} handoff requires EVIDENCESTORE_LMCACHE_TOPOLOGY={supported[handoff]}")
    cold = env.get("EVIDENCESTORE_PD_COLD_D", "1" if handoff == "lmcache" else "0")
    if cold not in {"0", "1"}:
        raise ValueError("EVIDENCESTORE_PD_COLD_D must be 0 or 1")
    if handoff == "lmcache" and cold != "1":
        raise ValueError("The shared-LMCache restore pilot requires EVIDENCESTORE_PD_COLD_D=1")
    return handoff, topology, cold == "1"


class Arm:
    def __init__(self, args, fixture):
        self.args = args
        self.fixture = fixture
        self.directory = args.run_dir.resolve()
        self.trace = Trace(self.directory / "traces", args.mode)
        self.processes = {}
        self.ports = {worker: args.port_base + i for i, worker in enumerate(WORKERS)}
        if args.topology == "shared":
            self.cache_ports = {"lmcache": args.port_base + len(WORKERS)}
            self.worker_caches = dict.fromkeys(WORKERS, "lmcache")
        else:
            self.cache_ports = {f"lmcache-{worker}": args.port_base + len(WORKERS) + 2 * i
                                for i, worker in enumerate(WORKERS)}
            self.worker_caches = {worker: f"lmcache-{worker}" for worker in WORKERS}
        self.side_ports = {worker: args.port_base + 3 * len(WORKERS) + i
                           for i, worker in enumerate(WORKERS)} if args.handoff == "nixl" else {}
        self.max_len = max(len(row["token_ids"]) for row in fixture["layouts"][args.layout])
        self.max_len += DECODE_OUTPUT_TOKENS

    def wait(self, label, check):
        deadline = time.monotonic() + self.args.timeout
        while time.monotonic() < deadline:
            for name, process in self.processes.items():
                if process.poll() is not None:
                    raise RuntimeError(f"{name} exited {process.returncode}. See {self.directory / (name + '.log')}")
            self.trace.refresh()
            result = check()
            if result is not None:
                return result
            time.sleep(0.10)
        raise TimeoutError(f"Timed out waiting for {label}")

    def start(self, stack, worker, command, gpu=None):
        environment = {
            **os.environ,
            "EVIDENCESTORE_LIFECYCLE_TRACE_DIR": str(self.trace.path),
            "EVIDENCESTORE_LIFECYCLE_WORKER": worker,
            "EVIDENCESTORE_LIFECYCLE_MODE": self.args.mode,
            "PYTHONHASHSEED": "0",
            "VLLM_SERVER_DEV_MODE": "1",
            "VLLM_DISABLE_REQUEST_ID_RANDOMIZATION": "1",
        }
        if gpu is not None:
            environment["CUDA_VISIBLE_DEVICES"] = gpu
            # Each engine owns its metrics, so a D scrape covers only that worker.
            environment.pop("PROMETHEUS_MULTIPROC_DIR", None)
        if worker in self.side_ports:
            environment.update({
                "VLLM_NIXL_SIDE_CHANNEL_HOST": "127.0.0.1",
                "VLLM_NIXL_SIDE_CHANNEL_PORT": str(self.side_ports[worker]),
                "UCX_NET_DEVICES": os.environ.get("UCX_NET_DEVICES", "all"),
                "NCCL_CUMEM_ENABLE": "1",
            })
        with (self.directory / f"{worker}.log").open("wb") as log:
            process = subprocess.Popen(command, env=environment, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        self.processes[worker] = process
        stack.callback(stop_process, process)

    def cache_command(self, port, disk_dir):
        command = [
            str(Path(sys.executable).with_name("lmcache")), "server",
            "--host", "127.0.0.1", "--port", str(port), "--http-port", str(port + 1),
            "--chunk-size", str(self.fixture["chunk_size"]),
            "--l1-size-gb", str(L1_BUDGET_GB // len(self.cache_ports)),
            "--supported-transfer-mode", "lmcache_driven", "--kv-load-policy", "DEFAULT",
            "--eviction-policy", "LRU" if disk_dir is None else "noop",
        ]
        if disk_dir is not None:
            command += [
                "--l2-adapter", json.dumps({"type": "fs", "base_path": str(disk_dir), "use_odirect": True}),
                "--l1-align-bytes", "4096", "--l2-store-policy", "skip_l1",
                "--l2-prefetch-policy", "skip_l1",
            ]
        return command

    def connector_config(self, worker):
        role = "kv_producer" if worker == "p0" else "kv_consumer"
        lmcache = {
            "kv_connector": "LMCacheMPConnector",
            "kv_connector_module_path": "lmcache.integration.vllm.lmcache_mp_connector",
            "kv_role": role if self.args.handoff == "lmcache" else "kv_both",
            "kv_connector_extra_config": {
                "lmcache.mp.host": "tcp://127.0.0.1",
                "lmcache.mp.port": self.cache_ports[self.worker_caches[worker]],
                # Fixed-size GPU pools use the connector's CUDA IPC path.
                "lmcache.mp.use_vmm_api": False,
                "lmcache.mp.save_unfull_chunk": False,
                "lmcache.mp.save_decode_cache": False,
            },
        }
        if self.args.handoff == "lmcache":
            return lmcache
        return {
            "kv_connector": "MultiConnector",
            "kv_role": role,
            "kv_load_failure_policy": "fail",
            "kv_connector_extra_config": {"connectors": [
                {"kv_connector": "NixlConnector", "kv_role": role, "kv_load_failure_policy": "fail"},
                lmcache,
            ]},
        }

    def launch(self, stack, gpus, disk_dir):
        ports = [*self.ports.values(), *self.side_ports.values()]
        for port in self.cache_ports.values():
            ports.extend((port, port + 1))
        for port in ports:
            with socket.socket() as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                probe.bind(("127.0.0.1", port))
        for name, port in self.cache_ports.items():
            path = disk_dir
            if disk_dir is not None and self.args.topology == "per_engine":
                path = disk_dir / name
                path.mkdir()
            self.start(stack, name, self.cache_command(port, path))
        for name, port in self.cache_ports.items():
            self.wait(f"{name} to bind", lambda: listening(port))

        block_size = self.fixture["block_size"]
        # Small GPU pools expose physical-slot reuse during the pilot.
        blocks = (self.max_len + block_size - 1) // block_size + 16
        for (worker, engine_port), gpu in zip(self.ports.items(), gpus, strict=True):
            connector = self.connector_config(worker)
            self.start(stack, worker, [
                str(Path(sys.executable).with_name("vllm")), "serve", self.fixture["model"],
                "--revision", self.fixture["model_revision"],
                "--tokenizer-revision", self.fixture["model_revision"],
                "--host", "127.0.0.1", "--port", str(engine_port), "--tensor-parallel-size", "1",
                "--enable-prefix-caching", "--enforce-eager", "--max-num-seqs", "1",
                "--max-model-len", str(self.max_len), "--max-num-batched-tokens", str(self.max_len),
                "--gpu-memory-utilization", "0.75",
                "--block-size", str(block_size), "--num-gpu-blocks-override", str(blocks),
                "--kv-transfer-config", json.dumps(connector),
            ], gpu)
        for worker, engine_port in self.ports.items():
            self.wait(f"{worker} health", lambda: health(engine_port))

    def complete(self, worker, label, tokens, max_tokens, transfer=None):
        request = {
            "model": self.fixture["model"], "request_id": label, "prompt": tokens,
            "add_special_tokens": False, "temperature": 0, "max_tokens": max_tokens,
            "ignore_eos": True,
            "return_token_ids": True,
        }
        if transfer is not None:
            request["kv_transfer_params"] = transfer
        raw = http(self.ports[worker], "/v1/completions", self.args.timeout, request)
        choice = raw["choices"][0]
        if choice["prompt_token_ids"] != tokens:
            raise RuntimeError(f"Engine changed the frozen token IDs for {label}")
        return choice["token_ids"], raw.get("kv_transfer_params")

    def run(self):
        gpus = os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")
        if not os.environ.get("SLURM_JOB_ID") or len(gpus) != 4 or not all(gpus) or len(set(gpus)) != 4:
            raise RuntimeError("Run inside a Slurm step with four distinct visible GPUs")
        if self.args.handoff == "nixl":
            result = subprocess.run(
                [sys.executable, "-c", "from nixl._api import nixl_agent"],
                capture_output=True, text=True,
            )
            if result.returncode:
                raise RuntimeError(f"Enable NIXL in the lifecycle runtime before launching. {result.stderr.strip()}")
        self.directory.mkdir(parents=False, exist_ok=False)
        self.trace.path.mkdir()
        write_json(self.directory / "fixture.json", self.fixture)
        with ExitStack() as stack:
            disk_dir = direct_io_directory(self.args.disk_dir) if self.args.mode == "disk" else None
            self.launch(stack, gpus, disk_dir)
            sources = {}
            turns = []
            with (self.directory / "requests.jsonl").open("x", encoding="utf-8") as output:
                for index, prompt in enumerate(self.fixture["layouts"][self.args.layout]):
                    worker = f"d{index % 3}"
                    result = self.turn(prompt, worker, sources)
                    output.write(json.dumps(result, separators=(",", ":")) + "\n")
                    output.flush()
                    turns.append(result)
                    print(f"Turn {result['turn']} · {worker} · "
                          f"{result['d_prefix_loaded_tokens']} external KV tokens", flush=True)
            if self.args.handoff == "nixl":
                self.wait("P's LMCache offload in the combined connector", lambda: self.trace.select(
                    "lmcache_store_completed", worker=self.worker_caches["p0"], success=True,
                ) or None)
            # Trace explicit resets after the measured turns so even the final D assignments
            # have release/eviction evidence. Preserve P's cache until the arm is completed.
            for worker in self.ports:
                self.reset(worker)
            self.trace.refresh()
            event_counts = {event: len(rows) for event, rows in self.trace.by_event.items()}
        restored = [obj for turn in turns for obj in turn["objects"]]
        lmcache_by_server = {
            name: {
                "gpu_to_lmcache_bytes": sum(row["bytes"] for row in self.trace.select(
                    "lmcache_store_completed", worker=name, success=True)),
                "lmcache_to_gpu_bytes": sum(row["bytes"] for row in self.trace.select(
                    "lmcache_retrieve_completed", worker=name, success=True)),
                "disk_read_bytes": sum(row["bytes"] for row in self.trace.select(
                    "lmcache_disk_read_completed", worker=name)),
                "disk_write_bytes": sum(row["bytes"] for row in self.trace.select(
                    "lmcache_disk_write_completed", worker=name)),
            }
            for name in self.cache_ports
        }
        nixl_bytes = sum(turn.get("nixl_transferred_bytes", 0) for turn in turns)
        if self.args.handoff == "nixl" and not nixl_bytes:
            raise RuntimeError("No native NIXL transfer was observed in the arm")
        write_json(self.directory / "summary.json", {
            "status": "passed", "mode": self.args.mode, "layout": self.args.layout,
            "handoff": self.args.handoff, "lmcache_topology": self.args.topology,
            "cold_d": self.args.cold_d, "lmcache_l1_budget_gb": L1_BUDGET_GB,
            "lmcache_by_server": lmcache_by_server,
            "nixl_transferred_bytes": nixl_bytes,
            "nixl_transfers": sum(turn.get("nixl_transfers", 0) for turn in turns),
            "nixl_restored_blocks": sum(len(turn.get("blocks", [])) for turn in turns),
            "nixl_transfer_seconds": sum(turn.get("nixl_transfer_seconds", 0.0) for turn in turns),
            "d_gpu_prefix_tokens": sum(turn.get("d_gpu_prefix_tokens", 0) for turn in turns),
            "d_tail_computed_tokens": sum(turn["d_tail_computed_tokens"] for turn in turns),
            "manifest_sha256": sha256(self.args.manifest.read_bytes()).hexdigest(),
            "conversation_id": self.fixture["conversation_id"], "turns": len(turns),
            "prompt_tokens": sum(turn["prompt_tokens"] for turn in turns),
            "d_restored_objects": len(restored),
            "d_restored_blocks": sum(len(obj["blocks"]) for obj in restored),
            "d_restored_bytes": sum(obj["bytes"] for obj in restored),
            "p_gpu_prefix_tokens": sum(turn["p_gpu_prefix_tokens"] for turn in turns),
            "d_disk_read_bytes": sum(row["bytes"] for obj in restored for row in obj["disk_reads"]),
            "disk_write_bytes": sum(row["bytes"] for row in self.trace.by_event["lmcache_disk_write_completed"]),
            "p_gpu_to_lmcache_bytes": lmcache_by_server[self.worker_caches["p0"]]["gpu_to_lmcache_bytes"],
            "gpu_evictions_by_reason": dict(Counter(
                row["reason"] for row in self.trace.by_event["vllm_gpu_block_evicted"]
            )),
            "disk_directory": str(disk_dir) if disk_dir is not None else None,
            "event_counts": event_counts,
        })
        print(f"Verified {self.directory / 'summary.json'}", flush=True)

    def reset(self, worker):
        self.wait(f"{worker} prefix reset", lambda: True if http(
            self.ports[worker], "/reset_prefix_cache", self.args.timeout, {}
        ).get("success") else None)

    def lmcache_prefix(self, prompt, p_label, p_id, sources):
        tokens = prompt["token_ids"]
        chunk_size = self.fixture["chunk_size"]
        prefix_tokens = prompt["measured_prefix_tokens"]
        if not 0 < len(tokens) - prefix_tokens < chunk_size or prefix_tokens % chunk_size:
            raise ValueError(f"Turn {prompt['turn']} needs a non-empty short tail")
        if prefix_tokens < chunk_size:
            raise ValueError(f"Turn {prompt['turn']} has no full LMCache chunk")
        prefixes = prefix_keys(tokens, prefix_tokens, chunk_size)
        self.complete("p0", p_label, tokens, 1, {"lmcache.skip_load": True})

        def ready_to_decode():
            store_sources(self.trace, p_id, prefixes, chunk_size, sources)
            return storage_ready(self.trace, prefixes, sources)

        return self.wait(f"turn {prompt['turn']} P stores and storage placement", ready_to_decode)

    def nixl_handoff(self, tokens, p_label, p_id):
        _, remote = self.complete("p0", p_label, tokens, 1, {
            "do_remote_decode": True,
            "do_remote_prefill": False,
            "remote_engine_id": None,
            "remote_block_ids": None,
            "remote_host": None,
            "remote_port": None,
        })
        if not isinstance(remote, dict) or not remote.get("do_remote_prefill"):
            raise RuntimeError(f"P did not return the native NIXL handshake for {p_id}")
        if remote.get("remote_request_id") != p_id or not remote.get("remote_block_ids"):
            raise RuntimeError(f"NIXL handshake does not identify P's KV for {p_id}")
        if remote.get("remote_port") != self.side_ports["p0"] or remote.get("remote_host") != "127.0.0.1":
            raise RuntimeError(f"NIXL handshake does not identify this arm's P endpoint for {p_id}")
        return remote

    def turn(self, prompt, worker, sources):
        turn = prompt["turn"]
        tokens = prompt["token_ids"]
        block_size = self.fixture["block_size"]
        p_label, d_label = f"lifecycle-t{turn}-p", f"lifecycle-t{turn}-{worker}"
        p_id, d_id = f"cmpl-{p_label}-0", f"cmpl-{d_label}-0"
        remote = expected = None
        if self.args.handoff == "nixl":
            if self.args.cold_d:
                self.reset(worker)
            before = nixl_metrics(self.ports[worker], self.args.timeout)
            remote = self.nixl_handoff(tokens, p_label, p_id)
        else:
            expected = self.lmcache_prefix(prompt, p_label, p_id, sources)
            self.reset(worker)

        dispatch = time.monotonic_ns()
        output_ids, _ = self.complete(worker, d_label, tokens, DECODE_OUTPUT_TOKENS, remote)
        if len(output_ids) != DECODE_OUTPUT_TOKENS:
            raise RuntimeError(f"Incomplete D output for turn {turn}: {output_ids}")

        if remote is not None:
            transfer = self.wait(f"turn {turn} NIXL handoff", lambda: nixl_block_receipt(
                self.trace, d_id, worker, len(tokens), block_size, remote, before,
                nixl_metrics(self.ports[worker], self.args.timeout),
            ))
            transfer["objects"] = []
            if self.args.cold_d and transfer["d_gpu_prefix_tokens"]:
                raise RuntimeError(f"Controlled D request used a GPU prefix hit: {d_id}")
            if turn == 1 and not transfer["nixl_transferred_bytes"]:
                raise RuntimeError("The initial cold request did not transfer KV over NIXL")
        else:
            prefix_tokens = prompt["measured_prefix_tokens"]
            objects = self.wait(f"turn {turn} D loads", lambda: restore_receipt(
                self.trace, d_id, worker, expected, dispatch, block_size, prefix_tokens,
            ))
            writes = self.trace.select("vllm_gpu_kv_written", worker=worker, request_id=d_id)
            positions = {position for row in writes for position in range(row["token_start"], row["token_end"])}
            if positions != set(range(prefix_tokens, len(tokens) + len(output_ids) - 1)):
                raise RuntimeError(f"D model writes did not cover exactly its tail and sampled inputs for {d_id}")
            transfer = {
                "d_prefix_loaded_tokens": prefix_tokens,
                "d_gpu_prefix_tokens": 0,
                "d_tail_computed_tokens": len(tokens) - prefix_tokens,
                "d_generated_input_tokens_written": len(output_ids) - 1,
                "objects": objects,
            }

        for engine, request_id in (("p0", p_id), (worker, d_id)):
            self.wait(f"{engine} turn {turn} request release", lambda: self.trace.select(
                "vllm_request_blocks_release", worker=engine, request_id=request_id,
            ) or None)
            arrivals = self.trace.select("vllm_request_arrived", worker=engine, request_id=request_id)
            if len(arrivals) != 1 or arrivals[0]["prompt_tokens"] != len(tokens):
                raise RuntimeError(f"Prompt receipt mismatch for {request_id}")
        p_lookup = self.trace.select("vllm_prefix_lookup", worker="p0", request_id=p_id)
        if not p_lookup:
            raise RuntimeError(f"Missing P prefix lookup for {p_id}")
        if self.args.handoff == "lmcache" and any(row["external_tokens"] for row in p_lookup):
            raise RuntimeError(f"Unexpected external hit on P for {p_id}")
        ready = self.trace.select("vllm_external_kv_ready", worker=worker, request_id=d_id, success=True)
        ready_ns = ready[-1]["ts_ns"] if ready else None
        if ready_ns is not None and ready_ns < dispatch:
            raise RuntimeError(f"D KV-ready precedes dispatch for {d_id}")
        return {
            **transfer,
            "d_kv_ready_ns": ready_ns,
            "d_dispatch_to_kv_ready_ns": None if ready_ns is None else ready_ns - dispatch,
            "turn": turn, "request_key": prompt["request_key"], "prompt_sha256": prompt["prompt_sha256"],
            "prompt_tokens": len(tokens),
            "p_gpu_prefix_tokens": p_lookup[0]["local_tokens"],
            "p_lmcache_prefix_tokens": p_lookup[0]["external_tokens"],
            "p_request_id": p_id, "d_request_id": d_id, "decode_worker": worker,
            "decode_dispatch_ns": dispatch, "output_token_ids": output_ids,
        }


def listening(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return None


def health(port):
    try:
        http(port, "/health", 3)
        return True
    except (OSError, URLError):
        return None


def direct_io_directory(path):
    path = path.resolve()
    fs = subprocess.check_output(["stat", "-f", "-c", "%T", str(path.parent)], text=True).strip()
    if fs in {"tmpfs", "ramfs", "devtmpfs"}:
        raise RuntimeError(f"Disk mode requires a filesystem outside RAM: {path.parent} ({fs})")
    path.mkdir(exist_ok=False)
    probe = path / ".direct-io-probe"
    try:
        with mmap.mmap(-1, 4096) as buffer:
            buffer[:] = b"\xa5" * len(buffer)
            fd = os.open(probe, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_DIRECT, 0o600)
            try:
                if os.write(fd, buffer) != len(buffer):
                    raise RuntimeError("Short direct I/O preflight write")
            finally:
                os.close(fd)
            fd = os.open(probe, os.O_RDONLY | os.O_DIRECT)
            try:
                buffer[:] = b"\0" * len(buffer)
                if os.readv(fd, [buffer]) != len(buffer) or buffer[:] != b"\xa5" * len(buffer):
                    raise RuntimeError("Direct I/O preflight read mismatch")
            finally:
                os.close(fd)
    finally:
        probe.unlink(missing_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--mode", choices=("memory", "disk"), required=True)
    parser.add_argument("--layout", choices=("chat", "carry_forward"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--disk-dir", type=Path)
    parser.add_argument("--port-base", type=int, default=18640)
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args()
    if (args.disk_dir is not None) != (args.mode == "disk"):
        parser.error("--disk-dir is required exactly in disk mode")
    try:
        args.handoff, args.topology, args.cold_d = deployment_from_env(os.environ)
    except ValueError as error:
        parser.error(str(error))
    last_offset = 15 if args.handoff == "nixl" else 5
    if not 1024 <= args.port_base <= 65535 - last_offset or args.timeout <= 0:
        parser.error(f"invalid timeout or port base for {args.handoff} handoff")

    def interrupted(signum, _frame):
        raise KeyboardInterrupt(f"Signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    arm = Arm(args, json.loads(args.manifest.read_text()))
    fresh = not arm.directory.exists()
    try:
        arm.run()
    except (OSError, RuntimeError, ValueError, KeyError, KeyboardInterrupt) as error:
        if fresh and arm.trace.path.is_dir():
            write_json(arm.directory / "failure.json", {"status": "failed", "error": str(error)})
        parser.exit(1, f"Lifecycle arm failed: {error}\n")


if __name__ == "__main__":
    main()
