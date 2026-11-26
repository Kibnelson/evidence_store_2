# EvidenceStore 2

This baseline preserves V1's pinned third-party source, historical Full Blend snapshots, and frozen workload inputs.

## Set up local source copies

Run from the V2 repo root with Python and Git available.

```sh
python3 -B scripts/checkout_sources.py
python3 -B scripts/prepare_full_blend.py
```

The checkout helper uses the neighboring `evidence_store_1/third_party/checkouts/` directory. It fetches each exact commit in [the source manifest](third_party/sources.json) from a local Git repository. Each V2 checkout has its own Git objects, a detached HEAD, and zero remotes. The upstream URLs in the manifest record provenance. For a different local source location, use `--from-checkouts /path/to/checkouts`.

The Full Blend helper restores the two historical snapshots from their original bundles and the corresponding pristine bases in V2. It checks the bundle checksum and ref, the recorded snapshot commit and tree, and the upstream parent.

| Component | Pristine base in `third_party/checkouts/` | Historical snapshot in `third_party/forks/` |
| --- | --- | --- |
| vLLM | `vllm-legacy-base`, v0.23.0 at `0fc695f` | `vllm-full-blend` at `164debe` |
| LMCache | `lmcache-legacy-base`, v0.5.0 at `389b9cf` | `lmcache-full-blend` at `c5c0b8e` |

The original standalone and lane-support patches are stored alongside the bundles. V1 applied them to scratch build copies before adding trace hooks. The V2 source setup leaves both the upstream bases and committed snapshots at their recorded revisions. The V1 build and trace recipe is recorded at experiment commit `5fc1c4b5f3e37f44eaa75bcfd765bfb88ecde380`. [vLLM receipt](third_party/vllm-full-blend-fork.json) · [LMCache receipt](third_party/lmcache-full-blend-fork.json)

Verify both source sets after checkout or on an existing workspace.

```sh
python3 -B scripts/checkout_sources.py --verify
python3 -B scripts/prepare_full_blend.py --verify
```

## Workload inputs

`workloads/` contains the original MT-RAG and MuSiQue selections and the four CLAPNQ files for the carry-forward checkpoints. All six are byte-for-byte copies from V1 experiment commit `5fc1c4b`. They record the selected queries, conversations, and retrieval provenance. Workload execution uses prepared inputs and an index that match the recorded pins.

## KV block lifecycle pilot

The [runbook](docs/kv-block-lifecycle-runbook.md) runs one five-turn MT-RAG conversation in 1P/3D normal prefix mode. It pairs CPU memory and direct disk LMCache runs under both current-docs and carry-forward prompt layouts.
