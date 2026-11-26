# From an MT-RAG prompt to a KV block

Slurm job `30734` ran one five-turn CLAPNQ conversation in V2 with one prefill worker (P) and three decode workers (D). It ran the same turns in two layouts and two storage tiers. The model was `Qwen/Qwen3-4B-Instruct-2507` at revision `cdbee75f17c01a7cc42f958dc650907174af0554`. The conversation ID was `1534a095279f2cb888fb0bea17bd70da`. [Runbook](kv-block-lifecycle-runbook.md) · [Frozen retrieval workload](../workloads/mtrag-multi-turn-repeat.json)

## 1. Assemble and tokenize the prompt

Each turn uses six passages from its frozen retrieval results in rank order. Both layouts include earlier questions and their reference answers. Carry-forward also replays the earlier turns' passages in place. The fixture uses the reference answers even when the model generates different text, which keeps later prompts fixed across storage modes. Each current question ends in an answer cue. [Prompt builder](../scripts/lifecycle_prepare.py)

| Turn | Chat RAG | Carry-forward RAG |
| --- | --- | --- |
| 1 | Instructions → turn 1 passages → Q1 → answer cue | Same prompt |
| 2 | Instructions → Q1 and reference A1 → turn 2 passages → Q2 → answer cue | Instructions → turn 1 passages → Q1 and reference A1 → turn 2 passages → Q2 → answer cue |
| 3 | Instructions → Q1/A1 → Q2/A2 → turn 3 passages → Q3 → answer cue | Instructions → turn 1 passages and Q1/A1 → turn 2 passages and Q2/A2 → turn 3 passages → Q3 → answer cue |

The tokenizer runs on the assembled prompt and records each passage's half-open token span. On turn 1, the first passage text starts at token 15 and ends before token 92. The first logical GPU block `[0, 16)` therefore contains the instructions, the passage markers, and the first token of passage 1. Passage 1 continues across later blocks. The first LMCache object `[0, 256)` covers 16 blocks, including all of passages 1 and 2 and the beginning of passage 3. Document boundaries and block boundaries are independent.

The frozen manifest has SHA-256 `7b1b9360bc5be717b50387e197c10db8d1255574aabea76380994dee7d24136f`. These are its exact prompt lengths and the prefix and tail coverage checked by the runner. Every full 256-token object in the measured prefix represents 16 blocks of 16 tokens. D workers are selected in round-robin order.

| Turn | Decode worker | Chat prompt / restored / tail tokens | Chat restored blocks | Carry-forward prompt / restored / tail tokens | Carry-forward restored blocks |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | d0 | 702 / 512 / 190 | 32 | 702 / 512 / 190 | 32 |
| 2 | d1 | 669 / 512 / 157 | 32 | 1,350 / 1,280 / 70 | 80 |
| 3 | d2 | 723 / 512 / 211 | 32 | 2,007 / 1,792 / 215 | 112 |
| 4 | d0 | 765 / 512 / 253 | 32 | 2,660 / 2,560 / 100 | 160 |
| 5 | d1 | 851 / 768 / 83 | 48 | 3,357 / 3,328 / 29 | 208 |
| **Total per storage mode** | | **3,710 / 2,816 / 894** | **176** | **10,076 / 9,472 / 604** | **592** |

## 2. Follow a block from P to D

Turn 1 makes the flow concrete. P starts with an empty GPU prefix cache and computes the 702 prompt tokens. D restores tokens `[0, 512)` as two LMCache objects, then computes the remaining 190 prompt tokens. D samples eight tokens. Its later forward passes write KV for the first seven generated tokens when those tokens become inputs. The final sampled token would get KV on a further forward pass.

| Stage | What happens to the first block `[0, 16)` | Trace evidence |
| --- | --- | --- |
| P receives the prompt | The API sends the frozen token IDs. The scheduler joins the request to the MT-RAG turn and checks its local GPU prefix cache. | Request ID, prompt count, and local prefix lookup |
| P allocates and writes KV | vLLM assigns a GPU slot. Attention writes K and V for the block. The trace fences the GPU write and records the slot and token positions. When a full block is indexed for prefix reuse, the scheduler records its prefix hash. | Slot allocation, allocation generation, fenced writes, and block publication |
| P stores through LMCache | The completed GPU-to-host store covers the 256-token object containing this block. Memory mode leaves the object resident in CPU memory. Disk mode writes it with `O_DIRECT` and releases the CPU copy. | Object ID, token range, source GPU slots, bytes, and storage receipts |
| D loads the object | The launcher resets the selected D worker's GPU prefix cache before each request. D allocates its own slots, then LMCache fills them from its CPU tier or from fresh direct disk reads through staging memory. | D lookup, destination slots, direct read in disk mode, completed GPU restore, and KV-ready |
| D uses the block | The restored prefix supplies KV for attention while D computes the prompt tail and continuation. D's published prefix hash matches P's hash for the same token span. | P/D block join and D's fenced writes for the remaining token positions |
| The request releases the slot | A request can drop its reference while the block remains indexed. A reset or eviction removes that mapping. Reallocating the physical slot gives it a new generation. | Request release, block reference count, reset or eviction reason, and slot generation |

Use the worker, pool, block ID, and allocation generation to identify a physical block lifetime. Use the LMCache object ID and token range to follow the handoff between P and D. The block hash identifies the token prefix. The receipts record movement and byte counts. A study of byte-level KV deltas requires tensor payload capture. [vLLM hooks](../third_party/lifecycle/vllm.patch) · [LMCache hooks](../third_party/lifecycle/lmcache.patch) · [Receipt joins](../scripts/lifecycle_receipts.py)

## 3. Results from job 30734

All four arms passed. Token IDs from the eight-token completions agreed between memory and disk on each turn within each layout. In carry-forward, P reused 6,688 of its 10,076 prompt token positions on its own GPU. D was reset before each turn and restored the full measured prefix from LMCache.

| Disk carry-forward measurement | Observed |
| --- | ---: |
| Bytes copied from P GPU into LMCache | 1,396,703,232 B |
| Direct disk writes | 13 objects, 490,733,568 B |
| Direct disk reads | 37 reads, 1,396,703,232 B |
| Bytes restored into D GPU | 1,396,703,232 B |
| Restored 16-token GPU block occurrences | 592 |
| Disk I/O failures | 0 |
| GPU evictions | 838, all tagged as resets |

The same 256-token prefix object can be requested on multiple turns. The disk run committed 13 objects and later served 37 reads. The P-to-LMCache copy counter still includes repeated offloads, so it is larger than the disk write counter. The CPU-memory carry-forward arm recorded zero disk reads and writes. The disk carry-forward arm exercised reset eviction. Capacity eviction requires a workload that puts pressure on the GPU pool.

## 4. Inspect the published trace

In the report directory, `manifest.json` gives the token IDs and passage spans. Each arm's `requests.jsonl` joins the P and D block IDs and transfer receipts. The compressed `traces/` files preserve the per-process lifecycle events and their timestamps. `comparison.json` summarizes both storage modes for both prompt layouts. [Publication commands](kv-block-lifecycle-runbook.md#7-publish-the-pilot-traces)

From the report directory, print the first carried-forward disk request and its first block. All IDs below come directly from the published receipt.

```bash
python3 -B - <<'PY'
import json
from pathlib import Path

with Path("disk-carry_forward/requests.jsonl").open() as rows:
    turn = json.loads(next(rows))
obj = turn["objects"][0]
print(json.dumps({
    "turn": turn["turn"],
    "prefill_store_request": obj["p_store_request_id"],
    "decode_request": turn["d_request_id"],
    "object_id": obj["object_id"],
    "object_span": [obj["token_start"], obj["token_end"]],
    "object_bytes": obj["bytes"],
    "first_block": obj["blocks"][0],
    "disk_reads": obj["disk_reads"],
}, indent=2))
PY
```
