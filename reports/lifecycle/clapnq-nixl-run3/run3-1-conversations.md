# NIXL run 3 lifecycle milestone for 1 conversation

1 CLAPNQ conversation · 5 turns per phase and topology.

Each arm starts with fresh workers, GPU caches, LMCache servers, and a separate disk directory. Within each layout the two topologies use the same frozen prompt IDs and round-robin D routing. GPU prefixes can stay warm within each conversation.

Disk amounts count completed events in the raw traces, including completions after the runner's summary snapshot. Disk reads enter CPU memory. LMCache GPU restores are counted separately. Native NIXL time sums the transfer metrics recorded for each turn.

Paired cells list per-engine first and shared second. Mismatch turn numbers refer to the turns within that conversation. KV mismatches compare per-turn GPU prefix hits, P LMCache hits, NIXL coverage, D prompt compute, and NIXL bytes and block counts.

## Memory-chat

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 231 | 231 |
| NIXL payload (B) | 544,997,376 | 544,997,376 |
| Native NIXL transfer time (s) | 0.956 | 0.949 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 830,472,192 | 415,236,096 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 0 | 0 |
| Disk write bytes | 0 | 0 |
| Completed disk reads | 0 | 0 |
| Disk read bytes | 0 | 0 |
| Total disk I/O (B) | 0 | 0 |

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 231 / 231 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |

## Memory-carry-forward

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 505 | 505 |
| NIXL payload (B) | 1,191,444,480 | 1,191,444,480 |
| Native NIXL transfer time (s) | 1.949 | 1.954 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 1,623,195,648 | 490,733,568 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 0 | 0 |
| Disk write bytes | 0 | 0 |
| Completed disk reads | 0 | 0 |
| Disk read bytes | 0 | 0 |
| Total disk I/O (B) | 0 | 0 |

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 505 / 505 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |

## Disk-chat

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 231 | 231 |
| NIXL payload (B) | 544,997,376 | 544,997,376 |
| Native NIXL transfer time (s) | 0.979 | 0.956 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 830,472,192 | 566,231,040 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 22 | 11 |
| Disk write bytes | 830,472,192 | 415,236,096 |
| Completed disk reads | 0 | 0 |
| Disk read bytes | 0 | 0 |
| Total disk I/O (B) | 830,472,192 | 415,236,096 |

Total disk I/O fell by 415,236,096 B (50.0%).

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 231 / 231 | 0 / 0 | 830,472,192 / 415,236,096 | 0 / 0 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |

## Disk-carry-forward

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 505 | 505 |
| NIXL payload (B) | 1,191,444,480 | 1,191,444,480 |
| Native NIXL transfer time (s) | 1.955 | 1.948 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 1,623,195,648 | 490,733,568 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 43 | 13 |
| Disk write bytes | 1,623,195,648 | 490,733,568 |
| Completed disk reads | 0 | 17 |
| Disk read bytes | 0 | 641,728,512 |
| Total disk I/O (B) | 1,623,195,648 | 1,132,462,080 |

Total disk I/O fell by 490,733,568 B (30.2%).

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 505 / 505 | 0 / 0 | 1,623,195,648 / 490,733,568 | 0 / 641,728,512 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |

## Memory versus disk output mismatches

| Conversation | Chat per-engine | Chat shared | Carry-forward per-engine | Carry-forward shared |
| --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | None | None | None | None |

Each trace bundle contains the frozen manifest, both request streams, and the raw engine and LMCache events for each phase. The offline timeline and slot tools can inspect an individual turn or block.
