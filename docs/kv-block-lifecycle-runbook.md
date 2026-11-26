# Trace the KV block lifecycle in V2

The pilot runs one complete five-turn MT-RAG CLAPNQ conversation through one prefill engine (P) and three decode engines (D). It uses normal vLLM prefix prefill and the LMCache multiprocess connector. All four runs use the same pinned revision of `Qwen/Qwen3-4B-Instruct-2507`, reference Q&A, and six ranked current passages per turn. [Frozen workload](../workloads/mtrag-multi-turn-repeat.json) · [Prompt preparation](../scripts/lifecycle_prepare.py)

| LMCache mode | Chat RAG | Carry-forward RAG |
| --- | --- | --- |
| CPU memory | Current passages and prior Q&A | Current passages, prior passages, and prior Q&A |
| Disk | Same chat token IDs | Same carry-forward token IDs |

Each vLLM GPU block holds 16 tokens. LMCache stores complete 256-token objects, each covering 16 of those blocks. The natural tail remains in the prompt and is tracked separately. P keeps its GPU prefix cache warm across the five turns and skips LMCache lookups. The launcher rotates through the three decode engines and clears the selected engine's GPU prefix cache before each measured request. The handoff is P GPU → shared LMCache → D GPU. P samples one token to finish prefill. D generates eight tokens with greedy decoding, and the driver checks that D's model writes cover the prompt tail and the first seven generated tokens. D needs a further generation step to write KV for its eighth sampled token.

In memory mode, LMCache keeps the objects in CPU memory. Both modes use the four GPUs for the model. In disk mode, LMCache writes to a local disk with `O_DIRECT`, releases the CPU-resident copy after the write, then reads it from disk for D. CPU buffers still stage the GPU transfers. The disk phase records the completed direct write and read for the matched objects. [vLLM hooks](../third_party/lifecycle/vllm.patch) · [LMCache hooks](../third_party/lifecycle/lmcache.patch)

## 1. Package the local V2 sources on the Mac

Use the lifecycle worktree and the three verified V2 source checkouts. This pilot uses the pristine `vllm` and `lmcache` pins `b24eda7` and `042d47a`, plus MT-RAG at `e0970de`. The package carries the local Git objects so the GPU build can verify every pin. Its source files come from the working tree, so review the current diff before packaging. The build can download pinned binary dependencies and model assets. [V2 source pins](../third_party/sources.json)

```bash
(
  set -euo pipefail
  umask 077
  base=/Users/nelson/workspace/Research/Nutanix
  lifecycle="$base/evidence_store_2_lifecycle"
  v2="$base/evidence_store_2"
  login=nbore@teach-node-09.cs.mcgill.ca

  git -C "$lifecycle" status --short
  python3 -B "$v2/scripts/checkout_sources.py" --verify vllm lmcache mt-rag

  package="$(mktemp -d /tmp/es2-lifecycle-package.XXXXXX)"
  COPYFILE_DISABLE=1 tar -czf "$package/lifecycle-source.tar.gz" \
    -C "$lifecycle" scripts workloads third_party/sources.json third_party/lifecycle \
    -C "$v2" third_party/checkouts/vllm third_party/checkouts/lmcache third_party/checkouts/mt-rag
  cd "$package"
  shasum -a 256 lifecycle-source.tar.gz > lifecycle-source.tar.gz.sha256

  inbox="$(ssh "$login" '
    set -eu
    umask 077
    node="/tmp/$(id -un)"
    mkdir -p "$node"
    test -O "$node"
    test ! -L "$node"
    mktemp -d "$node/es2-lifecycle-inbox.XXXXXX"
  ')"
  scp lifecycle-source.tar.gz lifecycle-source.tar.gz.sha256 "$login:$inbox/"
  printf 'Mac package %s\nLogin inbox %s\n' "$package" "$inbox"
)
```

Keep the printed login inbox path for the next steps.

## 2. Start tmux and allocate four GPUs

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

## 3. Relay the package to the allocation

Open a second terminal on `teach-node-09`. Substitute the job ID from the GPU shell and the inbox path printed by the Mac. The relay uses a CPU-only step inside the existing allocation. It checks the archive before and after transfer, then extracts it on the GPU node.

```bash
(
  set -euo pipefail
  module load slurm
  job=REPLACE_WITH_JOB_ID
  inbox=/tmp/nbore/REPLACE_WITH_PRINTED_INBOX_NAME
  cd "$inbox"
  sha256sum -c lifecycle-source.tar.gz.sha256
  read -r digest _ < lifecycle-source.tar.gz.sha256

  srun --jobid="$job" --overlap --gres=none -N 1 -n 1 -c 1 bash -c '
    set -euo pipefail
    umask 077
    root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
    mkdir -p "$root"
    test -O "$root"
    test ! -L "$root"
    if [[ -e "$root/source" ]]; then
      printf "A source package already exists at %s/source\n" "$root" >&2
      exit 1
    fi
    stage="$(mktemp -d "$root/.source.XXXXXX")"
    archive="$(mktemp "$root/.incoming.XXXXXX")"
    trap '\''rm -f -- "$archive"'\'' EXIT
    cat > "$archive"
    printf "%s  %s\n" "$1" "$archive" | sha256sum -c -
    tar -xzf "$archive" -C "$stage"
    mv -T -- "$stage" "$root/source"
    printf "Source ready at %s/source\n" "$root"
  ' lifecycle-relay "$digest" < lifecycle-source.tar.gz
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

Preparation reads the pinned MT-RAG reference tasks and passage archive from the transferred checkout. It uses the saved retrieval ranks and verifies each passage identity and content hash. For an offline model cache, supply the pinned `tokenizer.json` with `--tokenizer-file /path/to/tokenizer.json`. Stage the model weights for the manifest's revision in the runtime's Hugging Face cache before starting the workers.

The conversation ID is `1534a095279f2cb888fb0bea17bd70da`. For example, if turn 1 retrieved A and B and turn 2 retrieves B and C, the second prompt contains these sections in this order.

| Layout | Turn 2 structure |
| --- | --- |
| Chat RAG | Instructions → Q1 and its reference A1 → evidence B, C → Q2 → answer cue |
| Carry-forward RAG | Instructions → evidence A, B → Q1 and its reference A1 → evidence B, C → Q2 → answer cue |

The five chat prompts have 702, 669, 723, 765, and 851 tokens. Carry-forward has 702, 1,350, 2,007, 2,660, and 3,357. The inputs include their natural tails and the earlier reference answers. Turn 1 has identical token IDs in both layouts. In carry-forward, the next prompt preserves 2, 5, 7, and 10 complete chunks from the preceding prompt. The pilot uses the saved reference answers so changes in model output do not alter later prompts.

## 5. Run the four comparisons

Still in the GPU shell, run the modes and layouts sequentially with a fresh output directory per attempt. The same frozen manifest is read by all four phases. For the disk phases, use a fresh directory on the node-local filesystem backed by disk. The default here is `/tmp` on `gpu-grad-01`. Check `findmnt` before running if the allocation is on a different node. [Pilot runner](../scripts/lifecycle_run.py)

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run in the four-GPU allocation}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  cd "$root/source"
  source "$(cat "$root/activation.path")"
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
      python -B scripts/lifecycle_run.py \
        --manifest "$root/manifest.json" --mode "$mode" --layout "$layout" \
        --run-dir "$results/$phase" --port-base 18640 --timeout 900 "${disk[@]}"
    done
  done
  python -B scripts/lifecycle_compare.py "$results" | tee "$results/comparison.json"
)
```

If a phase fails, keep its logs and follow its `failure.json`. For a port conflict, choose a free range of six consecutive ports and retry with a fresh phase directory. For a disk I/O error, check the filesystem and the direct-I/O error receipt before retrying. A full retry with the same manifest produces a new four-phase results directory.

## 6. Read the results

Use `comparison.json` for matched memory-versus-disk totals and output token agreement within each layout. The two layouts produce different prompts, so report their prompt sizes alongside their movement and reuse counts.

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
