# Run 3 NIXL lifecycle campaign for 1, 5, and 10 conversations

The original one-conversation run tested both NIXL topologies in memory and disk with chat and carry-forward prompts. Run 2 repeated the disk carry-forward pair. **Run 3 repeats the full matrix** on a frozen CLAPNQ cohort. The first conversation is the same five-turn pilot and has the same manifest SHA-256 as job `30750`. [Published Run 1 comparison](https://github.com/Kibnelson/evidence_store_2/blob/4530fa3d8dfacc782afd68f7276144c30cbe5244/reports/lifecycle/mtrag-30750-nixl-shared/topology-comparison.json)

| Checkpoint | Unique conversations | Turns per phase and topology | Fresh arms through checkpoint | Markdown report |
| --- | ---: | ---: | ---: | --- |
| 1 | 1 | 5 | 8 | `run3-1-conversations.md` |
| 5 | 5 | 33 | 40 | `run3-5-conversations.md` |
| 10 | 10 | 69 | 80 | `run3-10-conversations.md` |

Each conversation has eight arms. The matrix is **per-engine or shared LMCache × memory or disk × chat or carry-forward**. Both topology choices use native NIXL and an 8 GB aggregate LMCache budget. Chat carries prior reference Q&A and the current documents. Carry-forward also carries earlier documents. Every arm starts with fresh workers, GPU caches, and LMCache servers. Disk arms get separate empty disk directories. D's GPU prefix cache stays warm within each conversation. This isolates each conversation and leaves cross-conversation reuse for a separate measurement.

The plan keeps the exact six ranked passages per turn from the saved CLAPNQ workloads. It starts with the original pilot, then follows the frozen workload order. Two candidate conversations exceed the existing 8,191-token prompt budget and are listed in `campaign.json`. The largest selected prompt has 8,177 tokens. The conservative maximum disk bound for any one arm is 11.11 GiB, based on the full 256-token objects P and D could write. The runner checks free space before each disk arm and reclaims completed disk objects between arms. Failed attempts keep their logs and scratch for inspection. [Cohort preparation](../scripts/lifecycle_scale_prepare.py) · [Campaign runner](../scripts/lifecycle_scale_run.py)

Prompt preparation reads questions and prior reference answers from MT-RAG's `reference.jsonl`. The six passages per turn come from the saved V1 retrieval ranks in the frozen workloads. V2 resolves those passage IDs and checks their text hashes against the pinned CLAPNQ passage archive. For the five-turn pilot, chat includes six passages on each turn and carry-forward includes 6, 12, 18, 24, and 30 passage occurrences. [Prompt preparation](../scripts/lifecycle_prepare.py) · [Pilot ranks](../workloads/mtrag-multi-turn-repeat.json)

## 1. Prepare the four-GPU allocation

Start a new Slurm job for the end-to-end test. Run 3 builds a new runtime and regenerates the prompts from the pinned MT-RAG checkout and the workload files in V2. The first prompt manifest is compared with the saved checksum for job `30750`. The source checkouts, `uv` downloads, and model files can be reused as build inputs. Each arm starts with empty GPU and LMCache caches.

On `teach-node-09`, start a regular tmux session for Run 3.

```bash
tmux new-session -A -s es2-lifecycle-run3 /bin/bash -il
```

Inside tmux, load Slurm and request the allocation.

```bash
module unload slurm 2>/dev/null || true
module load slurm &&
  command -v srun &&
  srun -p all -A oana2026 -q research12h -N 1 -w gpu-grad-01 \
    --gpus=4 -c 16 --mem=192G -t 12:00:00 --pty /bin/bash -l
```

At the `gpu-grad-01` prompt, check the job, the four assigned GPUs, and the free space for the build, model, and disk arms. Keep the allocation shell open for the remaining steps. Detach with `Ctrl+b` then `d` and reattach from the login node with `tmux attach-session -t es2-lifecycle-run3`.

```bash
printf 'Host %s | job %s | GPUs %s\n' \
  "$(hostname -s)" "${SLURM_JOB_ID:-unset}" "${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi --query-gpu=uuid,name,driver_version --format=csv
df -h /tmp
```

## 2. Clone V2 and verify the three local source pins

The clone goes in the new job's scratch directory. The donor path points to pristine `vllm`, `lmcache`, and `mt-rag` Git checkouts. Use the staged node-local donors or a verified path you already have. When neither is available, [stage the three checkouts from the Mac](kv-block-lifecycle-runbook.md#stage-the-local-donors-if-needed) using the new job ID, then rerun this block. The verification prints each detached commit.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run inside the four-GPU Slurm allocation}"
  test "$(hostname -s)" = gpu-grad-01
  node="/tmp/$(id -un)"
  root="$node/es2-lifecycle-$SLURM_JOB_ID"
  mkdir -p "$root"
  export GIT_SSH_COMMAND='ssh -o BatchMode=yes'

  if [[ ! -d "$root/source/.git" ]]; then
    git clone --depth=1 --single-branch --no-tags --branch kv-block-lifecycle \
      git@github.com:Kibnelson/evidence_store_2.git "$root/source"
  fi
  cd "$root/source"
  git log -1 --oneline
  test -s scripts/lifecycle_scale_run.py

  donors="${EVIDENCESTORE_LIFECYCLE_DONORS:-$node/es2-lifecycle-donors}"
  python3 -B scripts/checkout_sources.py --from-checkouts "$donors" vllm lmcache mt-rag
)
```

## 3. Build and verify a new NIXL runtime

The build uses the new job's verified checkouts. It needs `uv` on `PATH` or at `/tmp/$(id -un)/uv-bin/uv`. Both NIXL topologies use this one runtime. If a build stops midway, follow the [runtime recovery commands](kv-block-lifecycle-runbook.md#resume-an-interrupted-runtime-build) with the scratch path printed by the build and `EVIDENCESTORE_PD_HANDOFF=nixl`.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run inside the four-GPU Slurm allocation}"
  test "$(hostname -s)" = gpu-grad-01
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  cd "$root/source"
  export EVIDENCESTORE_PD_HANDOFF=nixl
  export EVIDENCESTORE_LIFECYCLE_CHECKOUTS="$root/source/third_party/checkouts"

  receipt="$root/activation-nixl.path"
  if [[ ! -s "$receipt" ]] || [[ ! -r "$(cat "$receipt")" ]]; then
    build_receipt="$(mktemp "$root/activation-nixl.XXXXXX")"
    bash scripts/lifecycle_runtime.sh "$build_receipt" 2>&1 | tee "$root/runtime-build.log"
    mv -- "$build_receipt" "$receipt"
  fi
  source "$(cat "$receipt")"
  test -s "$EVIDENCESTORE_LIFECYCLE_RUNTIME/check/runtime.json"
  df -h "$root"
)
```

## 4. Run the one-conversation checkpoint

Use `clapnq-nixl-run3` for the fresh campaign. If that results branch already contains a campaign you want to keep, export a new `LIFECYCLE_RUN3_CAMPAIGN` name before this step. Use the same name and source commit for all three checkpoints. Set `LIFECYCLE_RUN3_TOKENIZER` to the pinned local `tokenizer.json` if the allocation needs offline tokenizer preparation.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run inside the four-GPU Slurm allocation}"
  test "$(hostname -s)" = gpu-grad-01
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  campaign="${LIFECYCLE_RUN3_CAMPAIGN:-clapnq-nixl-run3}"
  state="$root/$campaign"

  cd "$root/source"
  export GIT_SSH_COMMAND='ssh -o BatchMode=yes'
  source "$(cat "$root/activation-nixl.path")"
  tokenizer=()
  if [[ -n "${LIFECYCLE_RUN3_TOKENIZER:-}" ]]; then
    tokenizer=(--tokenizer-file "$LIFECYCLE_RUN3_TOKENIZER")
  fi
  if [[ ! -s "$state/campaign.json" ]]; then
    python -B scripts/lifecycle_scale_prepare.py --output "$state" "${tokenizer[@]}"
  fi

  python -B scripts/lifecycle_scale_run.py "$state/campaign.json" \
    --campaign "$campaign" --through 1 2>&1 | tee -a "$state/launch.log"
)
```

The runner checks the frozen prompts and runtime results. It publishes each conversation with raw traces, manifests, comparison receipts, and worker logs. It verifies the GitHub ref before removing that conversation's local trace directory. The first checkpoint is complete when the launcher prints `Published reports/lifecycle/<campaign>/run3-1-conversations.md`. Open the report and confirm five matched turns in each of the four phase comparisons. Check the topology and memory-versus-disk output mismatch rows and inspect any reported differences before expanding.

## 5. Read back the archive and regenerate a block timeline

The branch is `results/lifecycle-clapnq-nixl-run3` for the default campaign name. Open `reports/lifecycle/clapnq-nixl-run3/` on that branch. Each milestone Markdown report links to its conversation bundles. It compares the topologies within each of the four phases and lists any memory-versus-disk output differences. Completed LMCache disk I/O comes from the full raw traces after worker shutdown. P's LMCache lookups, completed GPU restores, and disk reads are counted separately.

After Step 4, run this block in the allocation to test read-back before expanding. It fetches the published commit, checks the first conversation's archive against its published SHA-256, and generates the shared disk carry-forward timeline for logical block 43 on turn 4. It reads the GitHub copy even after the original local traces have been reclaimed. [Offline reader](../scripts/lifecycle_paired_timeline.py)

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run inside the four-GPU Slurm allocation}"
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  campaign="${LIFECYCLE_RUN3_CAMPAIGN:-clapnq-nixl-run3}"
  branch="results/lifecycle-$campaign"
  report="reports/lifecycle/$campaign"
  first="$report/conversations/01-1534a095279f2cb888fb0bea17bd70da"
  review="$(mktemp -d "$root/run3-review.XXXXXX")"

  cd "$root/source"
  export GIT_SSH_COMMAND='ssh -o BatchMode=yes'
  git fetch --depth=1 --no-tags origin "refs/heads/$branch"
  published="$(git rev-parse FETCH_HEAD)"
  git show "$published:$report/run3-1-conversations.md" > "$review/run3-1-conversations.md"
  git show "$published:$first/result.json" > "$review/result.json"
  git show "$published:$first/traces.tar.gz" > "$review/traces.tar.gz"
  digest="$(python3 -c 'import json, sys; print(json.load(sys.stdin)["archive_sha256"])' \
    < "$review/result.json")"
  printf '%s  %s\n' "$digest" "$review/traces.tar.gz" | sha256sum -c -

  mkdir "$review/traces"
  tar -xzf "$review/traces.tar.gz" -C "$review/traces"
  python3 -B scripts/lifecycle_paired_timeline.py "$review/traces/disk-carry_forward" \
    --mode disk --layout carry_forward --topology shared_engine --turn 4 --block 43 \
    | tee "$review/turn4-block43.md"
  printf 'Verified report and timeline in %s\n' "$review"
)
```

Use `--movement-csv` in place of `--turn 4 --block 43` to export a verified phase's block rows. The aggregate reports can include a conversation with P-side LMCache restores. That case retains all raw evidence, and the existing detailed block reader's original model-write assumptions can limit a full slot timeline for that arm.

### Follow a complete prompt

The prompt-first viewer shows every token ID and logical block for a turn, the corresponding P and D GPU slots, and links to the LMCache objects that cover those positions. Each object has its own event list for P and D copies, CPU placement and release, and disk operations. Run the command from the V2 repository with `extracted` set to the unpacked trace bundle. Supply the verified replication ZIP with `--prompt-archive` to display the exact rendered prompt text.

```bash
python3 -B scripts/lifecycle_prompt_timeline.py "$extracted/disk-carry_forward" \
  --mode disk --layout carry_forward --topology shared_engine --turn 4 \
  > prompt-timeline.md
```

View the same turn with `--topology per_engine` to see D copy some of the same prompt positions into its own LMCache server. The two views use the same recorded prompt.

## 6. Expand to 5 and 10

After the first report is published, run this with `through=5`. Use `through=10` to continue directly through both remaining checkpoints. The runner reads and verifies the published prefix before capturing any remaining conversations.

```bash
(
  set -euo pipefail
  umask 077
  : "${SLURM_JOB_ID:?Run inside the four-GPU Slurm allocation}"
  test "$(hostname -s)" = gpu-grad-01
  root="/tmp/$(id -un)/es2-lifecycle-$SLURM_JOB_ID"
  campaign="${LIFECYCLE_RUN3_CAMPAIGN:-clapnq-nixl-run3}"
  through=5

  cd "$root/source"
  export GIT_SSH_COMMAND='ssh -o BatchMode=yes'
  source "$(cat "$root/activation-nixl.path")"
  python -B scripts/lifecycle_scale_run.py "$root/$campaign/campaign.json" \
    --campaign "$campaign" --through "$through" 2>&1 | tee -a "$root/$campaign/launch.log"
)
```

If a run stops, repeat the same command in the allocation. Completed local arms can be reused, incomplete attempts move under `failed/`, and verified published conversations are skipped. To resume from a new allocation, restore the source commit recorded in the campaign's `provenance.json`, build the verified NIXL runtime there, and regenerate the plan. The runner checks that the plan SHA-256 matches the published campaign before continuing.

## 7. Clear job scratch and release the GPUs

Open the last desired checkpoint on GitHub and verify its trace bundles before cleanup. The launcher reclaims each successful arm's disk objects and each published conversation's local traces. The job directory still contains the clone, launch and build logs, any failed attempts, and any local review exports. Save the local diagnostics or exports you need before removing the job directory.

Run this block in the original GPU shell. The activation receipt identifies the runtime for this Slurm job. The block checks for active workers and moves the verified source checkouts into the staged donor location when that path is available. The initial `cd /` keeps the GPU shell in an existing directory after deletion.

```bash
cd /
(
  set -euo pipefail
  : "${SLURM_JOB_ID:?Run inside the original Slurm allocation}"
  test "$(hostname -s)" = gpu-grad-01

  node="/tmp/$(id -un)"
  root="$node/es2-lifecycle-$SLURM_JOB_ID"
  receipt="$root/activation-nixl.path"
  if ! [[ -f "$receipt" && -O "$receipt" && ! -L "$receipt" ]]; then
    printf 'Expected a local activation receipt at %s\n' "$receipt" >&2
    exit 1
  fi
  activation="$(cat "$receipt")"
  runtime="$(dirname -- "$activation")"
  suffix=${runtime##*.}
  if ! [[ "$activation" == "$runtime/activate.sh" &&
          "$runtime" == "$node/es-kv-lifecycle-$SLURM_JOB_ID.$suffix" &&
          "$suffix" =~ ^[[:alnum:]]{6}$ ]]; then
    printf 'Activation receipt does not point to this job runtime. Cleanup stopped.\n' >&2
    exit 1
  fi
  for path in "$node" "$root" "$runtime"; do
    if ! [[ -d "$path" && -O "$path" && ! -L "$path" && "$(realpath -e -- "$path")" == "$path" ]]; then
      printf 'Unexpected scratch path %s. Cleanup stopped.\n' "$path" >&2
      exit 1
    fi
  done

  gpu_pids="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)"
  workers="[e]s-kv-lifecycle-$SLURM_JOB_ID[.]$suffix/|[e]s2-lifecycle-$SLURM_JOB_ID/source/scripts/lifecycle_"
  if [[ -n "$gpu_pids" ]] || pgrep -af -u "$(id -u)" "$workers"; then
    printf 'A GPU process or lifecycle worker is still active. Cleanup stopped.\n' >&2
    exit 1
  fi

  donors="$node/es2-lifecycle-donors"
  if [[ ! -e "$donors" && ! -L "$donors" ]]; then
    python3 -B "$root/source/scripts/checkout_sources.py" --verify vllm lmcache mt-rag
    mv -T -- "$root/source/third_party/checkouts" "$donors"
  fi

  du -sch -- "$root" "$runtime"
  rm -rf --one-file-system -- "$root" "$runtime"
  df -h "$node"
)
```

`uv-cache` can still hold packages after the runtime is deleted. Check its size and clear it if you need more free space and no other build is using it. The next build can download the packages again. Keep `huggingface` for the model weights and `es2-lifecycle-donors` for the pinned source checkouts.

```bash
node="/tmp/$(id -un)"
du -sh "$node/uv-cache"
uv cache clean --cache-dir "$node/uv-cache"
df -h "$node"
du -xhd1 "$node" | sort -hr | head -12
```

Run `exit` from the original GPU shell to release the allocation. On the login node, `squeue --me` shows whether the job has left the queue.
