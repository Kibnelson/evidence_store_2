# Trace the KV block lifecycle in V2

The pilot runs one complete five-turn MT-RAG CLAPNQ conversation through one prefill engine (P) and three decode engines (D). It uses normal vLLM prefix prefill. Step 5 selects either a shared-LMCache handoff or a native NIXL handoff with per-engine or experimental shared LMCache. The four arms for each deployment use the same pinned revision of `Qwen/Qwen3-4B-Instruct-2507`, reference Q&A, and six ranked current passages per turn. [Frozen workload](../workloads/mtrag-multi-turn-repeat.json) · [Prompt preparation](../scripts/lifecycle_prepare.py)

| LMCache mode | Chat RAG | Carry-forward RAG |
| --- | --- | --- |
| CPU memory | Current passages and prior Q&A | Current passages, prior passages, and prior Q&A |
| Disk | Same chat token IDs | Same carry-forward token IDs |

Each vLLM GPU block holds 16 tokens. LMCache stores complete 256-token objects, each covering 16 GPU blocks. In the shared-LMCache arm, D pulls those complete objects and computes the prompt tail. In the NIXL arm, D receives native vLLM block coverage and the trace records the prompt tokens D actually computes. Both use a one-token P completion and an eight-token D completion. D's later forwards record seven generated tokens when they become inputs.

The pilot uses small GPU block pools. The LMCache connector uses same-node CUDA IPC to support fixed block counts on this pin. Step 5 selects the handoff and storage tier.

In memory mode, LMCache holds objects in CPU memory. In disk mode, LMCache writes them with `O_DIRECT` and releases the resident CPU copy. A disk restore reads into a temporary CPU buffer before copying to GPU. The shared deployment uses that tier for the handoff. The NIXL deployment uses the tier for worker-local LMCache reuse and records its GPU handoff separately. [vLLM hooks](../third_party/lifecycle/vllm.patch) · [LMCache hooks](../third_party/lifecycle/lmcache.patch)

## 1. Start tmux and allocate four GPUs

At the `teach-node-09` login shell, start a regular tmux session.

```bash
tmux new-session -A -s es2-lifecycle /bin/bash -il
```

Inside tmux, load Slurm and start the allocation.

```bash
module unload slurm 2>/dev/null || true
module load slurm &&
  command -v srun &&
  srun -p all -A oana2026 -q research12h -N 1 -w gpu-grad-01 \
    --gpus=4 -c 16 --mem=192G -t 12:00:00 --pty /bin/bash -l
```

At the resulting `gpu-grad-01` prompt, check the job ID, GPU assignment, and node-local space.

```bash
printf 'Host %s | job %s | GPUs %s\n' \
  "$(hostname -s)" "${SLURM_JOB_ID:-unset}" "${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi --query-gpu=uuid,name,driver_version --format=csv
df -h /tmp
```

Keep this window open for the build and runs. Detach with `Ctrl+b` then `d`, and reattach on the same login node with `tmux attach-session -t es2-lifecycle`.

## 2. Clone V2 inside the allocation

Run this at the `gpu-grad-01` prompt. It uses the GitHub SSH key from the earlier cluster runs and places the checkout on node-local scratch.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  test "$(hostname -s)" = gpu-grad-01
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  mkdir -p "$root"
  df -h "$root"

  if [[ ! -d "$root/source/.git" ]]; then
    GIT_SSH_COMMAND='ssh -o BatchMode=yes' \
      git clone --depth=1 --single-branch --no-tags --branch kv-block-lifecycle \
      git@github.com:Kibnelson/evidence_store_2.git "$root/source"
  fi
  git -C "$root/source" log -1 --oneline
)
```

## 3. Verify and copy the source pins

The pilot uses pristine vLLM `b24eda7`, LMCache `042d47a`, and MT-RAG `e0970de`. The build uses the verified local Git copies. Set `EVIDENCESTORE_LIFECYCLE_DONORS` to the absolute checkout directory from an earlier cluster run if it contains the three pristine copies. The command defaults to the V1 checkout under your home directory and writes the new copies to scratch. If the three donors are absent, follow [Stage the local donors](#stage-the-local-donors-if-needed) once and return here. [V2 source pins](../third_party/sources.json)

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  node="/tmp/$(id -un)"
  cd "$node/es2-lifecycle-$SLURM_JOB_ID/source"
  donors="${EVIDENCESTORE_LIFECYCLE_DONORS:-$HOME/evidence_store_1/third_party/checkouts}"
  if [[ -z "${EVIDENCESTORE_LIFECYCLE_DONORS:-}" && -d "$node/es2-lifecycle-donors" ]]; then
    donors="$node/es2-lifecycle-donors"
  fi
  python3 -B scripts/checkout_sources.py --from-checkouts "$donors" vllm lmcache mt-rag
)
```

## 4. Build and freeze the prompts

Return to the `gpu-grad-01` shell inside tmux. The runtime verifies the pristine V2 pins and applies the lifecycle hooks in scratch build copies. The vLLM native wheel matches its source commit. The script builds the LMCache CUDA extension and verifies that both load with four visible GPUs. Build and model caches use `/tmp/nbore`, including `uv-cache` and `huggingface/hub`. [Runtime build](../scripts/lifecycle_runtime.sh)

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  cd "$root/source"
  df -h "$root"
  if [[ ! -s "$root/activation.path" ]]; then
    bash scripts/lifecycle_runtime.sh "$root/activation.path"
  fi
  source "$(cat "$root/activation.path")"
  python -B scripts/lifecycle_prepare.py --output "$root/manifest.json"
)
```

If a previous Step 4 stopped with the OpenTelemetry dependency conflict, reuse the runtime path shown after `Runtime scratch` in the build log. Pull the runbook branch before resuming. The repair preserves the existing environment and vLLM install, reinstalls LMCache with the compatible OpenTelemetry requirements, and runs the full dependency and GPU checks before generating the activation receipt.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  runtime=/tmp/nbore/REPLACE_WITH_PRINTED_RUNTIME_DIRECTORY
  cd "$root/source"
  GIT_SSH_COMMAND='ssh -o BatchMode=yes' git pull --ff-only
  bash scripts/lifecycle_runtime.sh --resume "$runtime" "$root/activation.path"
  source "$(cat "$root/activation.path")"
  python -B scripts/lifecycle_prepare.py --output "$root/manifest.json"
)
```

If the dependency check already passed and activation stopped at the legacy `vllm._C` import, use `--verify-only` in place of `--resume` in the preceding block. It uses the installed Python environment, checks the CUDA-native vLLM extension and LMCache, then writes the same activation receipt.

Preparation reads the pinned MT-RAG reference tasks and passage archive from the verified local checkout. It uses the saved retrieval ranks and verifies each passage identity and content hash. For an offline model cache, supply the pinned `tokenizer.json` with `--tokenizer-file /path/to/tokenizer.json`. Stage the model weights for the manifest's revision in the runtime's Hugging Face cache before starting the workers.

The conversation ID is `1534a095279f2cb888fb0bea17bd70da`. For example, if turn 1 retrieved A and B and turn 2 retrieves B and C, the second prompt contains these sections in this order.

| Layout | Turn 2 structure |
| --- | --- |
| Chat RAG | Instructions → Q1 and its reference A1 → evidence B, C → Q2 → answer cue |
| Carry-forward RAG | Instructions → evidence A, B → Q1 and its reference A1 → evidence B, C → Q2 → answer cue |

The five chat prompts have 702, 669, 723, 765, and 851 tokens. Carry-forward has 702, 1,350, 2,007, 2,660, and 3,357. The inputs include their natural tails and the earlier reference answers. Turn 1 has identical token IDs in both layouts. In carry-forward, the next prompt preserves 2, 5, 7, and 10 complete chunks from the preceding prompt. The pilot uses the saved reference answers so changes in model output do not alter later prompts.

### Enable NIXL in the verified runtime

Steps 1–4 also prepare the prompt manifest for the NIXL configuration. The following optional step adds the pinned CUDA 13 NIXL packages to that runtime and checks the UCX backend. It writes a separate activation receipt that Step 5 selects automatically.

```bash
(
  set -euo pipefail
  umask 077
  root="/tmp/$(id -un)/es2-lifecycle-${SLURM_JOB_ID:?Run in the GPU allocation}"
  cd "$root/source"
  source "$(cat "$root/activation.path")"
  if [[ ! -s "$root/activation-nixl.path" ]]; then
    bash scripts/lifecycle_runtime.sh --enable-nixl \
      "$EVIDENCESTORE_LIFECYCLE_RUNTIME" "$root/activation-nixl.path"
  fi
)
```

## 5. Choose the handoff and run the four comparisons

Select the two environment variables in the GPU shell. Each deployment uses the same one-conversation fixture and 1P/3D worker order.

| `EVIDENCESTORE_PD_HANDOFF` | `EVIDENCESTORE_LMCACHE_TOPOLOGY` | KV path and cache capacity |
| --- | --- | --- |
| `lmcache` | `shared` | One 8 GB LMCache server holds the prefix between P and D. This is the job 30734 setup. |
| `nixl` | `per_engine` | Native NIXL pulls the KV from P into D. Four 2 GB LMCache servers provide the same total CPU cache budget for cross-request reuse. |
| `nixl` | `shared_engine` | Native NIXL pulls the KV from P into D. All four workers use one 8 GB LMCache server for cross-request reuse. Experimental. |

The pinned upstream NIXL recipe uses one LMCache server per engine. The `shared_engine` arm is an opt-in experiment and requires measured NIXL traffic on the first cold request. Comparing the two NIXL arms holds the handoff fixed and changes the LMCache topology. [Pinned NIXL and LMCache recipe](https://github.com/LMCache/LMCache/blob/042d47abdef0d460cf2cb0d5720e8a59280cda8a/docs/source/mp/disaggregated_prefill.rst)

For the original shared-LMCache run, set:

```bash
export EVIDENCESTORE_PD_HANDOFF=lmcache
export EVIDENCESTORE_LMCACHE_TOPOLOGY=shared
export EVIDENCESTORE_PD_COLD_D=1
```

For the native NIXL run with one LMCache server per engine, set:

```bash
export EVIDENCESTORE_PD_HANDOFF=nixl
export EVIDENCESTORE_LMCACHE_TOPOLOGY=per_engine
export EVIDENCESTORE_PD_COLD_D=0
```

For the experimental NIXL run with one shared LMCache server, set:

```bash
export EVIDENCESTORE_PD_HANDOFF=nixl
export EVIDENCESTORE_LMCACHE_TOPOLOGY=shared_engine
export EVIDENCESTORE_PD_COLD_D=0
```

Both NIXL topologies keep `lmcache.mp.save_decode_cache=false`. D creates generated-answer KV on its GPU during decode. The LMCache store receipts are checked against the prompt boundary, and native LMCache prompt offload remains enabled.

NIXL's default retains D's local GPU prefix state and uses the native P response handshake to dispatch the original prompt to D. P and D also retain their native LMCache lookup and offload behavior. Set `EVIDENCESTORE_PD_COLD_D=1` in the NIXL run when you want the same reset-before-request control as the shared run. The original `lmcache` + `shared` arm also skips external LMCache loads on P. The comparison prints the D cache control and memory budget for each deployment.

After selecting a deployment, run this block from the GPU shell. The first arm is CPU memory with the chat layout. The loop stops on the first failed arm. The disk arms use fresh directories on the node-local filesystem.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  cd "$root/source"
  receipt="$root/activation.path"
  port_base=18640
  if [[ "${EVIDENCESTORE_PD_HANDOFF:-lmcache}" == nixl ]]; then
    receipt="$root/activation-nixl.path"
    port_base=18700
    if [[ "${EVIDENCESTORE_LMCACHE_TOPOLOGY:-per_engine}" == shared_engine ]]; then
      port_base=18800
    fi
  fi
  if [[ ! -s "$receipt" ]]; then
    printf 'Missing runtime receipt %s. Complete Step 4 for the selected handoff.\n' "$receipt" >&2
    exit 1
  fi
  source "$(cat "$receipt")"
  results="$(mktemp -d "$root/results.XXXXXX")"
  tier="$(mktemp -d "$root/disk.XXXXXX")"
  printf 'Results %s\nDisk tier %s\n' "$results" "$tier"
  findmnt -T "$tier" -o TARGET,SOURCE,FSTYPE

  for mode in memory disk; do
    for layout in chat carry_forward; do
      phase="$mode-$layout"
      disk=()
      if [[ "$mode" == disk ]]; then
        disk=(--disk-dir "$tier/$phase")
      fi
      printf '\nRunning %s\n' "$phase"
      python -B scripts/lifecycle_run.py \
        --manifest "$root/manifest.json" --mode "$mode" --layout "$layout" \
        --run-dir "$results/$phase" --port-base "$port_base" --timeout 900 "${disk[@]}"
    done
  done
  python -B scripts/lifecycle_compare.py "$results" | tee "$results/comparison.json"
)
```

If a phase fails, keep its logs and inspect `failure.json`. The LMCache-only handoff needs a six-port range. The NIXL handoff uses a sixteen-port range. Choose a fresh range on a port conflict. A retry with the same manifest creates a fresh results directory.

## 6. Read the results

Use `comparison.json` for matched memory-versus-disk totals and output token agreement within each layout. The two layouts produce different prompts, so report their prompt sizes alongside their movement and reuse counts.

For NIXL, `summary.json` reports native transferred bytes, block occurrences, and transfer time. `lmcache_by_server` records cache movement and physical disk I/O for each LMCache server. `lmcache_by_worker` attributes GPU↔LMCache bytes to the P or D request ID, including when the workers use a common server. P/D request receipts carry D's local prefix, external prefix, model-written tail, and dispatch-to-ready time when a restore occurred. In the shared deployment, LMCache object and disk receipts describe the handoff directly. On one node these are functional NIXL measurements. Record the actual backend before interpreting network performance.

Once both four-arm directories are complete, compare them from the cloned source directory.

```bash
python3 -B scripts/lifecycle_compare.py "$nixl_results" --against "$shared_results"
```

Set `nixl_results` and `shared_results` to the printed absolute results paths. The comparison checks the original manifest and turn routing and records output-token differences and whether the D reset control and total LMCache budget match.

To compare only the LMCache topology, run both NIXL configurations and compare their four-arm results directories with the same D reset control.

```bash
python3 -B scripts/lifecycle_compare.py "$nixl_shared_results" --against "$nixl_per_engine_results"
```



| Artifact per phase | What to inspect |
| --- | --- |
| `fixture.json` | Frozen prompt token IDs, evidence spans, and model revision |
| `summary.json` | Pass status and movement accounting |
| `requests.jsonl` | Each MT-RAG turn, P/D request IDs, and joined block map |
| `traces/*.jsonl` | Scheduler, GPU block, LMCache object, and disk receipts |
| Worker logs | Startup, connector configuration, and shutdown |
| `failure.json` | Error details for a failed phase |

For one turn, follow the request ID from arrival to prefix lookup, slot allocation, GPU KV writes, block publication, and request release. Then match the LMCache object across the P GPU store and D GPU retrieve. In disk mode, verify the object was written, released from CPU residency, and read through a completed direct-I/O receipt before its D load. Use the worker, pool, slot, and allocation generation to tell two uses of the same physical GPU slot apart. For D's own KV writes, use the token ranges in the fenced `vllm_gpu_kv_written` receipts. A request can release its reference while the block stays indexed for prefix reuse. An eviction or reset removes that cached mapping.

For a quick per-turn readout, set `result_dir` to the absolute results path printed by the launcher. The P columns give the scheduler's local GPU and external LMCache prefix counts. The D columns distinguish the handed-off prefix from the slots D writes itself.

```bash
result_dir=REPLACE_WITH_PRINTED_ABSOLUTE_RESULTS_PATH
python3 -B - "$result_dir" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
for phase in ("memory-chat", "memory-carry_forward", "disk-chat", "disk-carry_forward"):
    print(f"\n{phase}")
    print("turn  P GPU  P LMCache  D loaded  D tail  D generated KV")
    with (root / phase / "requests.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            print(
                f"{row['turn']:>4}  {row['p_gpu_prefix_tokens']:>5}"
                f"  {row['p_lmcache_prefix_tokens']:>9}  {row['d_prefix_loaded_tokens']:>8}"
                f"  {row['d_tail_computed_tokens']:>6}  {row['d_generated_input_tokens_written']:>14}"
            )
PY
```

To preserve the small review artifacts before the allocation ends, package the manifest and selected results directory in GPU scratch. Leave the disk tier directory outside the package.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  cd "$root"
  result_dir=REPLACE_WITH_PRINTED_RESULTS_BASENAME
  test -f "$result_dir/disk-carry_forward/summary.json"
  tar -czf lifecycle-review.tar.gz manifest.json "$result_dir"
  sha256sum lifecycle-review.tar.gz
)
```

From the second terminal on `teach-node-09`, copy the package into login scratch while the allocation is live. Compare the printed digest with the GPU shell digest.

```bash
(
  set -euo pipefail
  umask 077
  module load slurm
  job=REPLACE_WITH_JOB_ID
  gpu_archive="/tmp/$(id -un)/es2-lifecycle-$job/lifecycle-review.tar.gz"
  review="$(mktemp -d "/tmp/$(id -un)/es2-lifecycle-review.XXXXXX")"
  srun --jobid="$job" --overlap --gres=none -N 1 -n 1 -c 1 \
    cat "$gpu_archive" > "$review/lifecycle-review.tar.gz"
  sha256sum "$review/lifecycle-review.tar.gz"
)
```

From the Mac, substitute the login review directory printed with the digest and copy the archive.

```bash
(
  set -euo pipefail
  umask 077
  login=nbore@teach-node-09.cs.mcgill.ca
  review=/tmp/nbore/REPLACE_WITH_PRINTED_REVIEW_DIRECTORY
  destination="$(mktemp -d /tmp/es2-lifecycle-review.XXXXXX)"
  scp "$login:$review/lifecycle-review.tar.gz" "$destination/"
  shasum -a 256 "$destination/lifecycle-review.tar.gz"
  printf 'Local review archive %s/lifecycle-review.tar.gz\n' "$destination"
)
```

Increase the workload after all four pilot phases pass. Freeze each additional conversation once, run both layouts in both tiers, and keep the four reports tied to that conversation's fixture.

## 7. Publish the pilot traces

Run this once the four-arm comparison passes. The report bundles the frozen prompt IDs and evidence spans, per-turn block joins, event traces, and worker logs. The publication step uses a fresh scratch clone and a results branch for this job. [Pilot walkthrough](kv-block-lifecycle-mtrag-pilot.md) · [Report collector](../scripts/lifecycle_collect.py)

If the job has multiple completed results directories, set `LIFECYCLE_RESULTS_DIR` to the absolute path printed by the successful run you want to publish.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the allocation that produced the results}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  results="${LIFECYCLE_RESULTS_DIR:-}"
  if [[ -z "$results" ]]; then
    shopt -s nullglob
    comparisons=("$root"/results.*/comparison.json)
    if (( ${#comparisons[@]} != 1 )); then
      printf 'Set LIFECYCLE_RESULTS_DIR to the completed results directory.\n' >&2
      exit 1
    fi
    results="${comparisons[0]%/comparison.json}"
  fi

  export GIT_SSH_COMMAND='ssh -o BatchMode=yes'
  publisher="$(mktemp -d "$root/publish-traces.XXXXXX")"
  suffix="$(python3 -c 'import json, sys
with open(sys.argv[1]) as stream:
    summary = json.load(stream)
if summary.get("handoff") == "nixl":
    print("-nixl-shared" if summary.get("lmcache_topology") == "shared_engine" else "-nixl")' \
    "$results/memory-chat/summary.json")"
  branch="results/lifecycle-$SLURM_JOB_ID$suffix"
  report="reports/lifecycle/mtrag-$SLURM_JOB_ID$suffix"
  printf 'Results %s\nPublish checkout %s\n' "$results" "$publisher"
  git clone --depth=1 --single-branch --no-tags --branch kv-block-lifecycle \
    git@github.com:Kibnelson/evidence_store_2.git "$publisher"
  cd "$publisher"
  git switch -c "$branch"
  python3 -B scripts/lifecycle_collect.py "$results" \
    --manifest "$root/manifest.json" --output "$report" --include-worker-logs
  (cd "$report" && sha256sum -c SHA256SUMS)
  git add -- "$report"
  git commit -m "Archive lifecycle traces from Slurm job $SLURM_JOB_ID"
  git push --set-upstream origin "HEAD:refs/heads/$branch"
  printf 'Published %s on %s at %s\n' "$report" "$branch" "$(git rev-parse --short HEAD)"
)
```

Open the results branch and select `reports/lifecycle/mtrag-<job>`. The NIXL result uses the `-nixl` suffix for per-engine caches and `-nixl-shared` for the experimental shared cache. The collector validates the original manifest hash and the four passed arms before writing the report. The checksum list covers the report files, including each compressed trace and log.

## Stage the local donors if needed

Use this once when the cluster has no pristine copies at the pinned commits. The Git clone in step 2 supplies the lifecycle code. This transfer supplies the three verified third-party Git checkouts.

On the Mac, use the existing V2 checkout to package the donors. The inbox is on the login node's scratch filesystem.

```bash
(
  set -euo pipefail
  umask 077
  v2=/Users/nelson/workspace/Research/Nutanix/evidence_store_2
  login=nbore@teach-node-09.cs.mcgill.ca
  python3 -B "$v2/scripts/checkout_sources.py" --verify vllm lmcache mt-rag
  package="$(mktemp -d /tmp/es2-lifecycle-donors.XXXXXX)"
  cd "$package"
  COPYFILE_DISABLE=1 tar -czf donors.tar.gz \
    -C "$v2/third_party/checkouts" vllm lmcache mt-rag
  shasum -a 256 donors.tar.gz > donors.tar.gz.sha256
  inbox="$(ssh "$login" 'umask 077
    node="/tmp/$(id -un)"
    mkdir -p "$node" && mktemp -d "$node/es2-donor-inbox.XXXXXX"')"
  scp donors.tar.gz donors.tar.gz.sha256 "$login:$inbox/"
  printf 'Login inbox %s\n' "$inbox"
)
```

From a second `teach-node-09` terminal, relay the verified archive into the active allocation. Substitute the job ID and the inbox path printed on the Mac.

```bash
(
  set -euo pipefail
  module load slurm
  job=REPLACE_WITH_JOB_ID
  inbox=/tmp/nbore/REPLACE_WITH_PRINTED_INBOX_NAME
  cd "$inbox"
  sha256sum -c donors.tar.gz.sha256
  read -r digest _ < donors.tar.gz.sha256

  srun --jobid="$job" --overlap --gres=none -N 1 -n 1 -c 1 bash -c '
    set -euo pipefail
    umask 077
    node="/tmp/$(id -un)"
    stage="$(mktemp -d "$node/.es2-donors.XXXXXX")"
    archive="$(mktemp "$node/.es2-archive.XXXXXX")"
    cleanup() { rm -f -- "$archive"; }
    trap cleanup EXIT
    cat > "$archive"
    printf "%s  %s\n" "$1" "$archive" | sha256sum -c -
    tar -xzf "$archive" -C "$stage"
    mv -T -- "$stage" "$node/es2-lifecycle-donors"
    printf "Donors ready at %s/es2-lifecycle-donors\n" "$node"
  ' donor-relay "$digest" < donors.tar.gz
)
```

Return to step 3 in the GPU shell to verify and materialize the staged donors.
