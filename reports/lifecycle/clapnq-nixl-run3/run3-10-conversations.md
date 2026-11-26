# NIXL run 3 lifecycle milestone for 10 conversations

10 CLAPNQ conversations · 69 turns per phase and topology.

Each arm starts with fresh workers, GPU caches, LMCache servers, and a separate disk directory. Within each layout the two topologies use the same frozen prompt IDs and round-robin D routing. GPU prefixes can stay warm within each conversation.

Disk amounts count completed events in the raw traces, including completions after the runner's summary snapshot. Disk reads enter CPU memory. LMCache GPU restores are counted separately. Native NIXL time sums the transfer metrics recorded for each turn.

Paired cells list per-engine first and shared second. Mismatch turn numbers refer to the turns within that conversation. KV mismatches compare per-turn GPU prefix hits, P LMCache hits, NIXL coverage, D prompt compute, and NIXL bytes and block counts.

## Memory-chat

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 4,989 | 4,989 |
| NIXL payload (B) | 11,770,527,744 | 11,770,527,744 |
| Native NIXL transfer time (s) | 20.561 | 20.444 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 19,893,583,872 | 9,172,942,848 |
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
| `3f5fa378239f7475baac89fa40288aaa` | 6 | 470 / 470 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/06-3f5fa378239f7475baac89fa40288aaa/traces.tar.gz) |
| `5c13daa9432149f6243aa1115629cd1a` | 7 | 475 / 475 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/07-5c13daa9432149f6243aa1115629cd1a/traces.tar.gz) |
| `694e275f1a01ad0e8ac448ad809f7930` | 8 | 593 / 593 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/08-694e275f1a01ad0e8ac448ad809f7930/traces.tar.gz) |
| `aea2634b0e5f1c2444550d31c41adc94` | 8 | 623 / 623 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/09-aea2634b0e5f1c2444550d31c41adc94/traces.tar.gz) |
| `79f0d0539d9ec0acbf90cb3388b30c17` | 7 | 484 / 484 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/10-79f0d0539d9ec0acbf90cb3388b30c17/traces.tar.gz) |

## Memory-carry-forward

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 10,494 | 10,494 |
| NIXL payload (B) | 24,758,452,224 | 24,758,452,224 |
| Native NIXL transfer time (s) | 40.043 | 40.103 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 33,596,375,040 | 9,437,184,000 |
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
| `3f5fa378239f7475baac89fa40288aaa` | 6 | 981 / 981 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/06-3f5fa378239f7475baac89fa40288aaa/traces.tar.gz) |
| `5c13daa9432149f6243aa1115629cd1a` | 7 | 997 / 997 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/07-5c13daa9432149f6243aa1115629cd1a/traces.tar.gz) |
| `694e275f1a01ad0e8ac448ad809f7930` | 8 | 1,181 / 1,181 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/08-694e275f1a01ad0e8ac448ad809f7930/traces.tar.gz) |
| `aea2634b0e5f1c2444550d31c41adc94` | 8 | 1,369 / 1,369 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/09-aea2634b0e5f1c2444550d31c41adc94/traces.tar.gz) |
| `79f0d0539d9ec0acbf90cb3388b30c17` | 7 | 999 / 999 | 0 / 0 | 0 / 0 | 0 / 0 | None | None | [Trace bundle](conversations/10-79f0d0539d9ec0acbf90cb3388b30c17/traces.tar.gz) |

## Disk-chat

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 4,989 | 4,989 |
| NIXL payload (B) | 11,770,527,744 | 11,770,527,744 |
| Native NIXL transfer time (s) | 20.549 | 20.471 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 19,893,583,872 | 15,325,986,816 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 527 | 243 |
| Disk write bytes | 19,893,583,872 | 9,172,942,848 |
| Completed disk reads | 0 | 41 |
| Disk read bytes | 0 | 1,547,698,176 |
| Total disk I/O (B) | 19,893,583,872 | 10,720,641,024 |

Total disk I/O fell by 9,172,942,848 B (46.1%).

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 231 / 231 | 0 / 0 | 830,472,192 / 415,236,096 | 0 / 0 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |
| `0208bf26ec357a803445290fa88a2e9e` | 7 | 561 / 561 | 0 / 0 | 2,453,667,840 / 1,207,959,552 | 0 / 37,748,736 | None | None | [Trace bundle](conversations/02-0208bf26ec357a803445290fa88a2e9e/traces.tar.gz) |
| `a2698b2973ea7db1ee5adb5e70ec02e4` | 9 | 677 / 677 | 0 / 0 | 2,566,914,048 / 1,094,713,344 | 0 / 377,487,360 | None | None | [Trace bundle](conversations/03-a2698b2973ea7db1ee5adb5e70ec02e4/traces.tar.gz) |
| `c1e53df98a28f19448f4af244304b89a` | 6 | 305 / 305 | 0 / 0 | 1,207,959,552 / 566,231,040 | 0 / 75,497,472 | None | None | [Trace bundle](conversations/04-c1e53df98a28f19448f4af244304b89a/traces.tar.gz) |
| `cfbcfa3e382f12aed450b10f87a72aeb` | 6 | 570 / 570 | 0 / 0 | 2,340,421,632 / 1,132,462,080 | 0 / 75,497,472 | None | None | [Trace bundle](conversations/05-cfbcfa3e382f12aed450b10f87a72aeb/traces.tar.gz) |
| `3f5fa378239f7475baac89fa40288aaa` | 6 | 470 / 470 | 0 / 0 | 1,736,441,856 / 792,723,456 | 0 / 150,994,944 | None | None | [Trace bundle](conversations/06-3f5fa378239f7475baac89fa40288aaa/traces.tar.gz) |
| `5c13daa9432149f6243aa1115629cd1a` | 7 | 475 / 475 | 0 / 0 | 1,811,939,328 / 830,472,192 | 0 / 150,994,944 | None | None | [Trace bundle](conversations/07-5c13daa9432149f6243aa1115629cd1a/traces.tar.gz) |
| `694e275f1a01ad0e8ac448ad809f7930` | 8 | 593 / 593 | 0 / 0 | 2,453,667,840 / 1,094,713,344 | 0 / 264,241,152 | None | None | [Trace bundle](conversations/08-694e275f1a01ad0e8ac448ad809f7930/traces.tar.gz) |
| `aea2634b0e5f1c2444550d31c41adc94` | 8 | 623 / 623 | 0 / 0 | 2,566,914,048 / 1,170,210,816 | 0 / 226,492,416 | None | None | [Trace bundle](conversations/09-aea2634b0e5f1c2444550d31c41adc94/traces.tar.gz) |
| `79f0d0539d9ec0acbf90cb3388b30c17` | 7 | 484 / 484 | 0 / 0 | 1,925,185,536 / 868,220,928 | 0 / 188,743,680 | None | None | [Trace bundle](conversations/10-79f0d0539d9ec0acbf90cb3388b30c17/traces.tar.gz) |

## Disk-carry-forward

| Measured total | Per-engine LMCache | Shared LMCache |
| --- | --- | --- |
| NIXL GPU blocks | 10,494 | 10,494 |
| NIXL payload (B) | 24,758,452,224 | 24,758,452,224 |
| Native NIXL transfer time (s) | 40.210 | 39.855 |
| P external prefix tokens from LMCache lookups | 0 | 0 |
| GPU-to-LMCache copy bytes | 33,596,375,040 | 12,381,585,408 |
| LMCache-to-GPU restores | 0 | 0 |
| Completed disk writes | 890 | 250 |
| Disk write bytes | 33,596,375,040 | 9,437,184,000 |
| Completed disk reads | 0 | 390 |
| Disk read bytes | 0 | 14,722,007,040 |
| Total disk I/O (B) | 33,596,375,040 | 24,159,191,040 |

Total disk I/O fell by 9,437,184,000 B (28.1%).

| Conversation | Turns | NIXL blocks | P LMCache tokens | Disk writes (B) | Disk reads (B) | Output mismatches | KV mismatches | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | 5 | 505 / 505 | 0 / 0 | 1,623,195,648 / 490,733,568 | 0 / 641,728,512 | None | None | [Trace bundle](conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |
| `0208bf26ec357a803445290fa88a2e9e` | 7 | 1,314 / 1,314 | 0 / 0 | 4,190,109,696 / 1,170,210,816 | 0 / 1,849,688,064 | None | None | [Trace bundle](conversations/02-0208bf26ec357a803445290fa88a2e9e/traces.tar.gz) |
| `a2698b2973ea7db1ee5adb5e70ec02e4` | 9 | 1,249 / 1,249 | 0 / 0 | 4,001,366,016 / 1,132,462,080 | 0 / 1,736,441,856 | None | None | [Trace bundle](conversations/03-a2698b2973ea7db1ee5adb5e70ec02e4/traces.tar.gz) |
| `c1e53df98a28f19448f4af244304b89a` | 6 | 625 / 625 | 0 / 0 | 2,038,431,744 / 603,979,776 | 0 / 830,472,192 | None | None | [Trace bundle](conversations/04-c1e53df98a28f19448f4af244304b89a/traces.tar.gz) |
| `cfbcfa3e382f12aed450b10f87a72aeb` | 6 | 1,274 / 1,274 | 0 / 0 | 4,114,612,224 / 1,170,210,816 | 0 / 1,774,190,592 | None | None | [Trace bundle](conversations/05-cfbcfa3e382f12aed450b10f87a72aeb/traces.tar.gz) |
| `3f5fa378239f7475baac89fa40288aaa` | 6 | 981 / 981 | 0 / 0 | 3,170,893,824 / 905,969,664 | 0 / 1,358,954,496 | None | None | [Trace bundle](conversations/06-3f5fa378239f7475baac89fa40288aaa/traces.tar.gz) |
| `5c13daa9432149f6243aa1115629cd1a` | 7 | 997 / 997 | 0 / 0 | 3,208,642,560 / 905,969,664 | 0 / 1,396,703,232 | None | None | [Trace bundle](conversations/07-5c13daa9432149f6243aa1115629cd1a/traces.tar.gz) |
| `694e275f1a01ad0e8ac448ad809f7930` | 8 | 1,181 / 1,181 | 0 / 0 | 3,737,124,864 / 1,019,215,872 | 0 / 1,698,693,120 | None | None | [Trace bundle](conversations/08-694e275f1a01ad0e8ac448ad809f7930/traces.tar.gz) |
| `aea2634b0e5f1c2444550d31c41adc94` | 8 | 1,369 / 1,369 | 0 / 0 | 4,341,104,640 / 1,170,210,816 | 0 / 2,000,683,008 | None | None | [Trace bundle](conversations/09-aea2634b0e5f1c2444550d31c41adc94/traces.tar.gz) |
| `79f0d0539d9ec0acbf90cb3388b30c17` | 7 | 999 / 999 | 0 / 0 | 3,170,893,824 / 868,220,928 | 0 / 1,434,451,968 | None | None | [Trace bundle](conversations/10-79f0d0539d9ec0acbf90cb3388b30c17/traces.tar.gz) |

## Memory versus disk output mismatches

| Conversation | Chat per-engine | Chat shared | Carry-forward per-engine | Carry-forward shared |
| --- | --- | --- | --- | --- |
| `1534a095279f2cb888fb0bea17bd70da` | None | None | None | None |
| `0208bf26ec357a803445290fa88a2e9e` | None | None | None | None |
| `a2698b2973ea7db1ee5adb5e70ec02e4` | None | None | None | None |
| `c1e53df98a28f19448f4af244304b89a` | None | None | None | None |
| `cfbcfa3e382f12aed450b10f87a72aeb` | None | None | None | None |
| `3f5fa378239f7475baac89fa40288aaa` | None | None | None | None |
| `5c13daa9432149f6243aa1115629cd1a` | None | None | None | None |
| `694e275f1a01ad0e8ac448ad809f7930` | None | None | None | None |
| `aea2634b0e5f1c2444550d31c41adc94` | None | None | None | None |
| `79f0d0539d9ec0acbf90cb3388b30c17` | None | None | None | None |

Each trace bundle contains the frozen manifest, both request streams, and the raw engine and LMCache events for each phase. The offline timeline and slot tools can inspect an individual turn or block.
