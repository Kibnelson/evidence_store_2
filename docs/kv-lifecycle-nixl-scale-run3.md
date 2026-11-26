# Run 3 NIXL lifecycle campaign for 1, 5, and 10 conversations

The original one-conversation run tested both NIXL topologies in memory and disk with chat and carry-forward prompts. Run 2 repeated the disk carry-forward pair. **Run 3 repeats the full matrix** on a frozen CLAPNQ cohort. The first conversation is the same five-turn pilot and has the same manifest SHA-256 as job `30750`. [Published Run 1 comparison](https://github.com/Kibnelson/evidence_store_2/blob/4530fa3d8dfacc782afd68f7276144c30cbe5244/reports/lifecycle/mtrag-30750-nixl-shared/topology-comparison.json)

| Checkpoint | Unique conversations | Turns per phase and topology | Fresh arms through checkpoint | Markdown report |
| --- | ---: | ---: | ---: | --- |
| 1 | 1 | 5 | 8 | `run3-1-conversations.md` |
| 5 | 5 | 33 | 40 | `run3-5-conversations.md` |
| 10 | 10 | 69 | 80 | `run3-10-conversations.md` |

Each conversation has eight arms. The matrix is **per-engine or shared LMCache × memory or disk × chat or carry-forward**. Both topology choices use native NIXL and an 8 GB aggregate LMCache budget. Chat carries prior reference Q&A and the current documents. Carry-forward also carries earlier documents. Every arm starts with fresh workers, GPU caches, and LMCache servers. Disk arms get separate empty disk directories. D's GPU prefix cache stays warm within each conversation. This isolates each conversation and leaves cross-conversation reuse for a separate measurement.

The plan keeps the exact six ranked passages per turn from the saved CLAPNQ workloads. It starts with the original pilot, then follows the frozen workload order. Two candidate conversations exceed the existing 8,191-token prompt budget and are listed in `campaign.json`. The largest selected prompt has 8,177 tokens. The conservative maximum disk bound for any one arm is 11.11 GiB, based on the full 256-token objects P and D could write. The runner checks free space before each disk arm and reclaims completed disk objects between arms. Failed attempts keep their logs and scratch for inspection. [Cohort preparation](../scripts/lifecycle_scale_prepare.py) · [Campaign runner](../scripts/lifecycle_scale_run.py)

## 1. Prepare the four-GPU allocation

Follow Steps 1–4 of the [Slurm lifecycle runbook](kv-block-lifecycle-runbook.md) from a fresh allocation, using either NIXL deployment for the runtime build. In an existing allocation with a verified NIXL runtime, use its `activation-nixl.path`.

Run the next block at `gpu-grad-01` to freeze the whole cohort and run the one-conversation checkpoint. Keep the campaign name and source commit when resuming. Reuse an already-prepared plan to avoid re-rendering all prompts.

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
  git pull --ff-only
  source "$(cat "$root/activation-nixl.path")"
  df -h "$root"

  python -B scripts/lifecycle_scale_prepare.py --output "$state"
  python -B scripts/lifecycle_scale_run.py "$state/campaign.json" \
    --campaign "$campaign" --through 1
)
```

The runner checks the frozen prompts and runtime results. It publishes each conversation with raw traces, manifests, comparison receipts, and worker logs. It verifies the GitHub ref before removing that conversation's local trace directory. The one-conversation Markdown report appears alongside the verified archive.

## 2. Expand to 5 and 10

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
    --campaign "$campaign" --through "$through"
)
```

If a run stops, repeat the same command in the allocation. Completed local arms can be reused, incomplete attempts move under `failed/`, and verified published conversations are skipped. To resume from a new allocation, restore the source commit recorded in the campaign's `provenance.json`, build the verified NIXL runtime there, and regenerate the plan. The runner checks that the plan SHA-256 matches the published campaign before continuing.

## 3. Read the reports or regenerate a block timeline

The branch is `results/lifecycle-clapnq-nixl-run3` for the default campaign name. Open `reports/lifecycle/clapnq-nixl-run3/` on that branch. Each milestone Markdown report links to its conversation bundles. It compares the topologies within each of the four phases and lists any memory-versus-disk output differences. Completed LMCache disk I/O comes from the full raw traces after worker shutdown. P's LMCache lookups, completed GPU restores, and disk reads are counted separately.

To inspect a conversation, verify `traces.tar.gz` against `archive_sha256` in the adjacent `result.json`, then extract it into a new directory. Pass a phase directory to the offline block reader. This example selects logical block 43 on turn 4 of the first conversation's shared disk carry-forward run. [Offline reader](../scripts/lifecycle_paired_timeline.py)

```bash
python3 -B scripts/lifecycle_paired_timeline.py "$extracted/disk-carry_forward" \
  --mode disk --layout carry_forward --topology shared_engine --turn 4 --block 43
```

Use `--movement-csv` in place of `--turn 4 --block 43` to export a verified phase's block rows. The aggregate reports can include a conversation with P-side LMCache restores. That case retains all raw evidence, and the existing detailed block reader's original model-write assumptions can limit a full slot timeline for that arm.

Once GitHub verifies the last desired checkpoint, its prompts, reports, and raw trace bundles remain available for CPU review. Release the original Slurm GPU shell with `exit` after checking the published archive and the scratch you want to remove.
