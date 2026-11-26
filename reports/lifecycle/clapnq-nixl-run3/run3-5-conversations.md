# NIXL run 3 lifecycle milestone for 5 conversations

5 CLAPNQ conversations · 33 turns per phase and topology.

Each arm starts with fresh workers, GPU caches, LMCache servers, and a separate disk directory. Within each layout the two topologies use the same frozen prompt IDs and round-robin D routing. GPU prefixes can stay warm within each conversation.

Disk amounts count completed events in the raw traces, including completions after the runner's summary snapshot. Disk reads enter CPU memory. LMCache GPU restores are counted separately. Native NIXL time sums the transfer metrics recorded for each turn.

Paired cells list per-engine first and shared second. Mismatch turn numbers refer to the turns within that conversation. KV mismatches compare per-turn GPU prefix hits, P LMCache hits, NIXL coverage, D prompt compute, and NIXL bytes and block counts.

## Memory-chat

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 2,344 | 2,344 |
| NIXL payload (B) | 5,530,189,824 | 5,530,189,824 |
| Native NIXL transfer time (s) | 9.720 | 9.661 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 9,399,435,264 | 4,416,602,112 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 0 | 0 |
| Disk write bytes | 0 | 0 |
| Completed disk reads | 0 | 0 |
| Disk read bytes | 0 | 0 |
| Total disk I/O (B) | 0 | 0 |

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 231 / 231 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |
| `0208bf26ec357a803445290fa88a2e9e` | 7 | 561 / 561 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/02-0208bf26ec357a803445290fa88a2e9e/traces.tar.gz) |
| `a2698b2973ea7db1ee5adb5e70ec02e4` | 9 | 677 / 677 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/03-a2698b2973ea7db1ee5adb5e70ec02e4/traces.tar.gz) |
| `c1e53df98a28f19448f4af244304b89a` | 6 | 305 / 305 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/04-c1e53df98a28f19448f4af244304b89a/traces.tar.gz) |
| `cfbcfa3e382f12aed450b10f87a72aeb` | 6 | 570 / 570 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/05-cfbcfa3e382f12aed450b10f87a72aeb/traces.tar.gz) |

## Memory-carry-forward

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 4,967 | 4,967 |
| NIXL payload (B) | 11,718,623,232 | 11,718,623,232 |
| Native NIXL transfer time (s) | 18.900 | 18.910 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 15,967,715,328 | 4,567,597,056 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 0 | 0 |
| Disk write bytes | 0 | 0 |
| Completed disk reads | 0 | 0 |
| Disk read bytes | 0 | 0 |
| Total disk I/O (B) | 0 | 0 |

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 505 / 505 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |
| `0208bf26ec357a803445290fa88a2e9e` | 7 | 1,314 / 1,314 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/02-0208bf26ec357a803445290fa88a2e9e/traces.tar.gz) |
| `a2698b2973ea7db1ee5adb5e70ec02e4` | 9 | 1,249 / 1,249 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/03-a2698b2973ea7db1ee5adb5e70ec02e4/traces.tar.gz) |
| `c1e53df98a28f19448f4af244304b89a` | 6 | 625 / 625 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/04-c1e53df98a28f19448f4af244304b89a/traces.tar.gz) |
| `cfbcfa3e382f12aed450b10f87a72aeb` | 6 | 1,274 / 1,274 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/05-cfbcfa3e382f12aed450b10f87a72aeb/traces.tar.gz) |

## Disk-chat

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 2,344 | 2,344 |
| NIXL payload (B) | 5,530,189,824 | 5,530,189,824 |
| Native NIXL transfer time (s) | 9.653 | 9.688 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 9,399,435,264 | 7,776,239,616 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 249 | 117 |
| Disk write bytes | 9,399,435,264 | 4,416,602,112 |
| Completed disk reads | 0 | 15 |
| Disk read bytes | 0 | 566,231,040 |
| Total disk I/O (B) | 9,399,435,264 | 4,982,833,152 |

Total disk I/O fell by 4,416,602,112 B (47.0%).

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 231 / 231 | 0 / 0 | 830,472,192 / 415,236,096 | 0 / 0 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |
| `0208bf26ec357a803445290fa88a2e9e` | 7 | 561 / 561 | 0 / 0 | 2,453,667,840 / 1,207,959,552 | 0 / 37,748,736 | None | None | [Trace bundle](conversations/02-0208bf26ec357a803445290fa88a2e9e/traces.tar.gz) |
| `a2698b2973ea7db1ee5adb5e70ec02e4` | 9 | 677 / 677 | 0 / 0 | 2,566,914,048 / 1,094,713,344 | 0 / 377,487,360 | None | None | [Trace bundle](conversations/03-a2698b2973ea7db1ee5adb5e70ec02e4/traces.tar.gz) |
| `c1e53df98a28f19448f4af244304b89a` | 6 | 305 / 305 | 0 / 0 | 1,207,959,552 / 566,231,040 | 0 / 75,497,472 | None | None | [Trace bundle](conversations/04-c1e53df98a28f19448f4af244304b89a/traces.tar.gz) |
| `cfbcfa3e382f12aed450b10f87a72aeb` | 6 | 570 / 570 | 0 / 0 | 2,340,421,632 / 1,132,462,080 | 0 / 75,497,472 | None | None | [Trace bundle](conversations/05-cfbcfa3e382f12aed450b10f87a72aeb/traces.tar.gz) |

## Disk-carry-forward

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 4,967 | 4,967 |
| NIXL payload (B) | 11,718,623,232 | 11,718,623,232 |
| Native NIXL transfer time (s) | 19.146 | 18.783 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 15,967,715,328 | 5,775,556,608 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 423 | 121 |
| Disk write bytes | 15,967,715,328 | 4,567,597,056 |
| Completed disk reads | 0 | 181 |
| Disk read bytes | 0 | 6,832,521,216 |
| Total disk I/O (B) | 15,967,715,328 | 11,400,118,272 |

Total disk I/O fell by 4,567,597,056 B (28.6%).

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 505 / 505 | 0 / 0 | 1,623,195,648 / 490,733,568 | 0 / 641,728,512 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |
| `0208bf26ec357a803445290fa88a2e9e` | 7 | 1,314 / 1,314 | 0 / 0 | 4,190,109,696 / 1,170,210,816 | 0 / 1,849,688,064 | None | None | [Trace bundle](conversations/02-0208bf26ec357a803445290fa88a2e9e/traces.tar.gz) |
| `a2698b2973ea7db1ee5adb5e70ec02e4` | 9 | 1,249 / 1,249 | 0 / 0 | 4,001,366,016 / 1,132,462,080 | 0 / 1,736,441,856 | None | None | [Trace bundle](conversations/03-a2698b2973ea7db1ee5adb5e70ec02e4/traces.tar.gz) |
| `c1e53df98a28f19448f4af244304b89a` | 6 | 625 / 625 | 0 / 0 | 2,038,431,744 / 603,979,776 | 0 / 830,472,192 | None | None | [Trace bundle](conversations/04-c1e53df98a28f19448f4af244304b89a/traces.tar.gz) |
| `cfbcfa3e382f12aed450b10f87a72aeb` | 6 | 1,274 / 1,274 | 0 / 0 | 4,114,612,224 / 1,170,210,816 | 0 / 1,774,190,592 | None | None | [Trace bundle](conversations/05-cfbcfa3e382f12aed450b10f87a72aeb/traces.tar.gz) |

## Memory versus disk output mismatches

| Conversation | Chat per-engine | Chat shared | Carry-forward per-engine | Carry-forward shared |
| --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | None | None | None | None |
| `0208bf26ec357a803445290fa88a2e9e` | None | None | None | None |
| `a2698b2973ea7db1ee5adb5e70ec02e4` | None | None | None | None |
| `c1e53df98a28f19448f4af244304b89a` | None | None | None | None |
| `cfbcfa3e382f12aed450b10f87a72aeb` | None | None | None | None |

Each trace bundle contains the frozen manifest, both request streams, and the raw engine and LMCache events for each phase. The offline timeline and slot tools can inspect an individual turn or block.
