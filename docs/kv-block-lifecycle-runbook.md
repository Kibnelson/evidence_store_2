# Trace the KV block lifecycle in V2

The pilot runs one complete five-turn MT-RAG CLAPNQ conversation through one prefill engine (P) and three decode engines (D) using vLLM prefix prefill. Start at Step 1 on the login node and choose the deployment in Step 2 inside the GPU allocation. Each deployment runs all four arms below with the same pinned revision of `Qwen/Qwen3-4B-Instruct-2507`, reference Q&A, and six ranked current passages per turn. [Frozen workload](../workloads/mtrag-multi-turn-repeat.json) · [Prompt preparation](../scripts/lifecycle_prepare.py)

| LMCache mode | Chat RAG | Carry-forward RAG |
| --- | --- | --- |
| CPU memory | Current passages and prior Q&A | Current passages, prior passages, and prior Q&A |
| Disk | Same chat token IDs | Same carry-forward token IDs |

Each vLLM GPU block holds 16 tokens. LMCache stores complete 256-token objects, each covering 16 GPU blocks. In the shared-LMCache arm, D pulls those complete objects and computes the prompt tail. In the NIXL arm, D receives native vLLM block coverage and the trace records the prompt tokens D actually computes. Both use a one-token P completion and an eight-token D completion. D's later forwards record seven generated tokens when they become inputs.

The pilot uses small GPU block pools. The LMCache connector uses same-node CUDA IPC to support fixed block counts on this pin.

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

## 2. Choose the deployment and clone V2

At the `gpu-grad-01` prompt, run one of the three export blocks. Keep that shell for Steps 3–5. If you open a new shell, set the three variables again before continuing.

| Deployment | P → D prompt KV handoff | LMCache topology | Runtime receipt | Default port base |
| --- | --- | --- | --- | ---: |
| Shared LMCache | D pulls from LMCache | One 8 GB server shared by P and D | `activation.path` | 18640 |
| Native NIXL with per-engine LMCache | D pulls from P over NIXL | One 2 GB server per engine | `activation-nixl.path` | 18700 |
| Native NIXL with shared LMCache | D pulls from P over NIXL | One 8 GB server shared by P and D | `activation-nixl.path` | 18800 |

### Shared LMCache

```bash
export EVIDENCESTORE_PD_HANDOFF=lmcache
export EVIDENCESTORE_LMCACHE_TOPOLOGY=shared
export EVIDENCESTORE_PD_COLD_D=1
```

### Native NIXL with per-engine LMCache

```bash
export EVIDENCESTORE_PD_HANDOFF=nixl
export EVIDENCESTORE_LMCACHE_TOPOLOGY=per_engine
export EVIDENCESTORE_PD_COLD_D=0
```

### Native NIXL with shared LMCache

This is the experimental topology. The pinned upstream NIXL recipe uses per-engine LMCache. Both NIXL deployments require measured NIXL bytes on the first cold request. [Pinned NIXL and LMCache recipe](https://github.com/LMCache/LMCache/blob/042d47abdef0d460cf2cb0d5720e8a59280cda8a/docs/source/mp/disaggregated_prefill.rst)

```bash
export EVIDENCESTORE_PD_HANDOFF=nixl
export EVIDENCESTORE_LMCACHE_TOPOLOGY=shared_engine
export EVIDENCESTORE_PD_COLD_D=0
```

`EVIDENCESTORE_PD_COLD_D=1` resets the selected D worker's GPU prefix cache before each request. Shared-LMCache handoff requires this setting to measure an LMCache restore each time. `0` leaves D's GPU prefix cache warm across turns. For a comparison with the same D reset control as shared LMCache, set the NIXL arm to `1` too. NIXL also keeps native LMCache prompt lookup and offload enabled. D writes answer KV on its GPU, and generated-answer offload to LMCache is disabled.

### Clone or update V2 inside the allocation

Run this in the same GPU shell. It uses your GitHub SSH key and creates or updates the node-local checkout.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  test "$(hostname -s)" = gpu-grad-01
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  mkdir -p "$root"
  df -h "$root"

  export GIT_SSH_COMMAND='ssh -o BatchMode=yes'
  if [[ -d "$root/source/.git" ]]; then
    git -C "$root/source" pull --ff-only
  else
    git clone --depth=1 --single-branch --no-tags --branch kv-block-lifecycle \
      git@github.com:Kibnelson/evidence_store_2.git "$root/source"
  fi
  git -C "$root/source" log -1 --oneline
)
```

## 3. Verify and copy the source pins

The pilot uses pristine vLLM `b24eda7`, LMCache `042d47a`, and MT-RAG `e0970de`. The command verifies any existing V2 copies. For missing copies, it uses staged donors under `/tmp/nbore` when present, or the V1 checkout in your home directory. To use an earlier allocation's copies, set `EVIDENCESTORE_LIFECYCLE_DONORS` to its absolute `source/third_party/checkouts` directory. For example, if job 30734's copies are still on the node, use the export below. If you have no copies, follow [Stage the local donors](#stage-the-local-donors-if-needed) and return here. [V2 source pins](../third_party/sources.json)

```bash
export EVIDENCESTORE_LIFECYCLE_DONORS=/tmp/nbore/es2-lifecycle-30734/source/third_party/checkouts
```

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

Run this in the GPU shell with the deployment selected in Step 2. The runtime uses the verified local pins, applies the lifecycle hooks to scratch copies, installs the matching vLLM native wheel, and builds the LMCache CUDA extension. For NIXL, it also installs the pinned NIXL packages and checks UCX GPU memory support. Build and model caches are under `/tmp/nbore`. Check the free space printed before building. [Runtime build](../scripts/lifecycle_runtime.sh)

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  : "${EVIDENCESTORE_PD_HANDOFF:?Choose a deployment in Step 2}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  cd "$root/source"
  df -h "$root"

  base_receipt="$root/activation.path"
  nixl_receipt="$root/activation-nixl.path"
  receipt="$base_receipt"
  if [[ "$EVIDENCESTORE_PD_HANDOFF" == nixl ]]; then
    receipt="$nixl_receipt"
  fi

  if [[ ! -s "$receipt" ]] || [[ ! -r "$(cat "$receipt")" ]]; then
    build_receipt="$(mktemp "$root/activation-build.XXXXXX")"
    if [[ "$EVIDENCESTORE_PD_HANDOFF" == nixl && -s "$base_receipt" &&
          -r "$(cat "$base_receipt")" ]]; then
      runtime="$(dirname -- "$(cat "$base_receipt")")"
      bash scripts/lifecycle_runtime.sh --enable-nixl "$runtime" "$build_receipt"
    elif [[ "$EVIDENCESTORE_PD_HANDOFF" == lmcache && -s "$nixl_receipt" &&
            -r "$(cat "$nixl_receipt")" ]]; then
      cp -- "$nixl_receipt" "$build_receipt"
    else
      bash scripts/lifecycle_runtime.sh "$build_receipt"
    fi
    mv -- "$build_receipt" "$receipt"
  fi

  source "$(cat "$receipt")"
  python -B scripts/lifecycle_prepare.py --output "$root/manifest.json"
  df -h "$root"
)
```

### Resume an interrupted runtime build

If a build stopped at the OpenTelemetry dependency check, use the `Runtime scratch` path from that build's log in the same allocation. `--resume` reinstalls LMCache with the compatible OpenTelemetry requirements. If dependencies passed and verification stopped at the legacy `vllm._C` import, use `--verify-only`. For a NIXL runtime, `--enable-nixl` installs and verifies NIXL in an existing compatible environment.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  : "${EVIDENCESTORE_PD_HANDOFF:?Choose a deployment in Step 2}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  runtime=/tmp/nbore/REPLACE_WITH_PRINTED_RUNTIME_DIRECTORY
  action=--resume
  cd "$root/source"
  GIT_SSH_COMMAND='ssh -o BatchMode=yes' git pull --ff-only
  receipt="$root/activation.path"
  if [[ "$EVIDENCESTORE_PD_HANDOFF" == nixl ]]; then
    receipt="$root/activation-nixl.path"
  fi
  build_receipt="$(mktemp "$root/activation-build.XXXXXX")"
  bash scripts/lifecycle_runtime.sh "$action" "$runtime" "$build_receipt"
  mv -- "$build_receipt" "$receipt"
)
```

After recovery, rerun the Step 4 build block. It uses the recovered activation receipt and freezes the prompts. If the old runtime was removed during cleanup, the build block creates a fresh runtime and replaces the stale receipt after verification.

If scratch space is tight and no build is using the package cache, `uv cache clean --cache-dir "/tmp/$(id -un)/uv-cache"` clears the regenerable package downloads. The Hugging Face model cache and prior `results.*` directories are separate. Run `df -h /tmp` again before retrying the build.

Preparation reads the pinned MT-RAG reference tasks and passage archive from the verified local checkout. It uses the saved retrieval ranks and verifies each passage identity and content hash. For an offline model cache, supply the pinned `tokenizer.json` with `--tokenizer-file /path/to/tokenizer.json`. Stage the model weights for the manifest's revision in the runtime's Hugging Face cache before starting the workers.

The conversation ID is `1534a095279f2cb888fb0bea17bd70da`. For example, if turn 1 retrieved A and B and turn 2 retrieves B and C, the second prompt contains these sections in this order.

| Layout | Turn 2 structure |
| --- | --- |
| Chat RAG | Instructions → Q1 and its reference A1 → evidence B, C → Q2 → answer cue |
| Carry-forward RAG | Instructions → evidence A, B → Q1 and its reference A1 → evidence B, C → Q2 → answer cue |

The five chat prompts have 702, 669, 723, 765, and 851 tokens. Carry-forward has 702, 1,350, 2,007, 2,660, and 3,357. The inputs include their natural tails and the earlier reference answers. Turn 1 has identical token IDs in both layouts. In carry-forward, the next prompt preserves 2, 5, 7, and 10 complete chunks from the preceding prompt. The pilot uses the saved reference answers so changes in model output do not alter later prompts.

### Enable NIXL in the verified runtime

To switch from shared-LMCache handoff to NIXL in the same allocation, run the new export block from Step 2 and rerun the Step 4 build block. It adds NIXL to the verified runtime when available. Both NIXL topologies use `activation-nixl.path`. To switch between those two topologies after a successful build, change the exports in Step 2 and go straight to Step 5.

## 5. Run both storage tiers and both prompt layouts

Run this in the GPU shell with the deployment selected in Step 2. It runs `memory-chat`, `memory-carry_forward`, `disk-chat`, and `disk-carry_forward` in order, stopping on the first failure. Each invocation creates a fresh results directory. The disk arms use fresh directories under `/tmp` on the node-local filesystem for `O_DIRECT` reads and writes. Keep the disk tier on a filesystem that supports `O_DIRECT`.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  cd "$root/source"
  : "${EVIDENCESTORE_PD_HANDOFF:?Choose a deployment in Step 2}"
  : "${EVIDENCESTORE_LMCACHE_TOPOLOGY:?Choose a deployment in Step 2}"
  : "${EVIDENCESTORE_PD_COLD_D:?Choose a deployment in Step 2}"
  case "$EVIDENCESTORE_PD_HANDOFF/$EVIDENCESTORE_LMCACHE_TOPOLOGY" in
    lmcache/shared) receipt="$root/activation.path"; port_base=18640 ;;
    nixl/per_engine) receipt="$root/activation-nixl.path"; port_base=18700 ;;
    nixl/shared_engine) receipt="$root/activation-nixl.path"; port_base=18800 ;;
    *) printf 'Choose a supported handoff and topology in Step 2.\n' >&2; exit 1 ;;
  esac
  port_base="${LIFECYCLE_PORT_BASE:-$port_base}"
  if [[ ! -s "$receipt" ]] || [[ ! -r "$(cat "$receipt")" || ! -s "$root/manifest.json" ]]; then
    printf 'Complete Step 4 for the selected handoff. Expected %s and a frozen manifest.\n' "$receipt" >&2
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
      args=(--manifest "$root/manifest.json" --mode "$mode" --layout "$layout"
        --run-dir "$results/$phase" --port-base "$port_base" --timeout 900)
      if [[ "$mode" == disk ]]; then
        args+=(--disk-dir "$tier/$phase")
      fi
      printf '\nRunning %s\n' "$phase"
      python -B scripts/lifecycle_run.py "${args[@]}"
    done
  done
  python -B scripts/lifecycle_compare.py "$results" | tee "$results/comparison.json.tmp"
  mv -- "$results/comparison.json.tmp" "$results/comparison.json"
)
```

On success, `comparison.json` is ready under the printed `Results` path. If a phase fails, inspect its `failure.json` and worker logs. If all phases finish and the comparison fails, inspect `comparison.json.tmp`. Shared-LMCache handoff uses six consecutive ports and NIXL uses sixteen. On a port conflict, set `LIFECYCLE_PORT_BASE` to the first port of a free range and rerun Step 5.

## 6. Read the results

Use `comparison.json` for matched memory-versus-disk totals and output token agreement within each layout. The two layouts produce different prompts, so report their prompt sizes alongside their movement and reuse counts.

For NIXL, `summary.json` reports native transferred bytes, block occurrences, and transfer time. `lmcache_by_server` records cache movement and physical disk I/O for each LMCache server. `lmcache_by_worker` attributes GPU↔LMCache bytes to the P or D request ID, including when the workers use a common server. P/D request receipts carry D's local prefix, external prefix, model-written tail, and dispatch-to-ready time when a restore occurred. In the shared deployment, LMCache object and disk receipts describe the handoff directly. On one node these are functional NIXL measurements. Record the actual backend before interpreting network performance.

To compare deployments, use the printed absolute `Results` paths from two completed runs and run the comparison from the cloned source directory. The comparison matches the frozen manifest, turn IDs, and decode-worker routing. It reports output-token differences and whether the D reset control, the LMCache memory budget, and the answer offload setting match.

For shared-LMCache handoff versus native NIXL, set `EVIDENCESTORE_PD_COLD_D=1` for NIXL before Step 5 if you want the same D reset control. The shared-LMCache handoff skips external LMCache loads on P. Native NIXL enables them, so report that difference alongside any changes in P computation or cache movement.

```bash
cd "/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID/source"
nixl_results=/absolute/path/to/nixl/results.XXXXXX
lmcache_results=/absolute/path/to/lmcache/results.XXXXXX
python3 -B scripts/lifecycle_compare.py "$nixl_results" --against "$lmcache_results"
```

For a topology comparison, run both NIXL deployments with the same `EVIDENCESTORE_PD_COLD_D` value. Use their four-arm results directories.

```bash
nixl_shared_results=/absolute/path/to/nixl-shared/results.XXXXXX
nixl_per_engine_results=/absolute/path/to/nixl-per-engine/results.XXXXXX
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

Open the printed `reports/lifecycle/mtrag-<job><suffix>` path on the printed results branch. Shared-LMCache handoff uses an empty suffix, native NIXL with per-engine caches uses `-nixl`, and native NIXL with a shared cache uses `-nixl-shared`. The collector validates the original manifest hash and the four passed arms before writing the report. The checksum list covers the report files, including each compressed trace and log.

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
