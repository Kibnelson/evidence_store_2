# NIXL with shared LMCache run 3

Slurm job `30758` ran one prefill worker (P) and three decode workers (D0–D2) on four RTX A5000 GPUs on one node. D kept its local GPU prefix cache between turns in a conversation and used NIXL to pull missing prompt blocks from P. Every configuration started with fresh workers, GPU caches, and LMCache state. [Paired per-engine LMCache report](nixl-per-engine-run3.md) · [Runbook and source](https://github.com/Kibnelson/evidence_store_2/blob/6d02f491f8638a473bccbd0b5f4a499dfd6c5df5/docs/kv-lifecycle-nixl-scale-run3.md)

P and D0–D2 used one LMCache server with an 8 GB budget. In disk mode that server can satisfy lookups from the same stored object. Run 3 recorded disk reads into CPU memory and zero LMCache-to-GPU restores. D populated its prompt through local GPU reuse and NIXL.

Each conversation ran in memory and in disk, with both chat and carry-forward prompts. Chat includes prior reference Q&A and the current turn's six frozen passages. Carry-forward also keeps each earlier turn's passages. The archived manifests contain the exact prompt token IDs and evidence spans. Memory keeps LMCache objects in CPU memory. Disk uses direct I/O and can prefetch objects into CPU memory.

## Checkpoint totals

The checkpoints are cumulative on the same cohort. The figures count completed GPU offloads and completed disk operations, including disk events recorded after the initial summary snapshot. I/O totals sum disk reads and writes. The first turn in every configuration started with an empty P and D GPU prefix.

| Conversations | Turns | Phase | NIXL blocks | NIXL bytes | GPU → LMCache bytes | Disk write bytes | Disk read bytes | Total disk I/O bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 | Memory · Chat | 231 | 544,997,376 | 415,236,096 | 0 | 0 | 0 |
| 1 | 5 | Memory · Carry-forward | 505 | 1,191,444,480 | 490,733,568 | 0 | 0 | 0 |
| 1 | 5 | Disk · Chat | 231 | 544,997,376 | 566,231,040 | 415,236,096 | 0 | 415,236,096 |
| 1 | 5 | Disk · Carry-forward | 505 | 1,191,444,480 | 490,733,568 | 490,733,568 | 641,728,512 | 1,132,462,080 |
| 5 | 33 | Memory · Chat | 2,344 | 5,530,189,824 | 4,416,602,112 | 0 | 0 | 0 |
| 5 | 33 | Memory · Carry-forward | 4,967 | 11,718,623,232 | 4,567,597,056 | 0 | 0 | 0 |
| 5 | 33 | Disk · Chat | 2,344 | 5,530,189,824 | 7,776,239,616 | 4,416,602,112 | 566,231,040 | 4,982,833,152 |
| 5 | 33 | Disk · Carry-forward | 4,967 | 11,718,623,232 | 5,775,556,608 | 4,567,597,056 | 6,832,521,216 | 11,400,118,272 |
| 10 | 69 | Memory · Chat | 4,989 | 11,770,527,744 | 9,172,942,848 | 0 | 0 | 0 |
| 10 | 69 | Memory · Carry-forward | 10,494 | 24,758,452,224 | 9,437,184,000 | 0 | 0 | 0 |
| 10 | 69 | Disk · Chat | 4,989 | 11,770,527,744 | 15,325,986,816 | 9,172,942,848 | 1,547,698,176 | 10,720,641,024 |
| 10 | 69 | Disk · Carry-forward | 10,494 | 24,758,452,224 | 12,381,585,408 | 9,437,184,000 | 14,722,007,040 | 24,159,191,040 |

Output token IDs match between memory and disk and between per-engine and shared LMCache for the same layout. The traced P and D prefix coverage, D prompt computation, and NIXL traffic also match across topologies. [1-conversation checkpoint](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/run3-1-conversations.md) · [5-conversation checkpoint](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/run3-5-conversations.md) · [10-conversation checkpoint](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/run3-10-conversations.md)

## Disk operations by conversation

Disk rows count operations completed by the LMCache servers across all turns. Each completed operation transfers a full 256-token object. The bundle links open the raw memory and disk traces in both layouts and topologies.

| Order | Conversation | Turns | Chat writes / bytes | Chat reads / bytes | Carry-forward writes / bytes | Carry-forward reads / bytes | Archive |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | `1534a095279f2cb888fb0bea17bd70da` | 5 | 11 / 415,236,096 | 0 / 0 | 13 / 490,733,568 | 17 / 641,728,512 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/01-1534a095279f2cb888fb0bea17bd70da/traces.tar.gz) |
| 02 | `0208bf26ec357a803445290fa88a2e9e` | 7 | 32 / 1,207,959,552 | 1 / 37,748,736 | 31 / 1,170,210,816 | 49 / 1,849,688,064 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/02-0208bf26ec357a803445290fa88a2e9e/traces.tar.gz) |
| 03 | `a2698b2973ea7db1ee5adb5e70ec02e4` | 9 | 29 / 1,094,713,344 | 10 / 377,487,360 | 30 / 1,132,462,080 | 46 / 1,736,441,856 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/03-a2698b2973ea7db1ee5adb5e70ec02e4/traces.tar.gz) |
| 04 | `c1e53df98a28f19448f4af244304b89a` | 6 | 15 / 566,231,040 | 2 / 75,497,472 | 16 / 603,979,776 | 22 / 830,472,192 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/04-c1e53df98a28f19448f4af244304b89a/traces.tar.gz) |
| 05 | `cfbcfa3e382f12aed450b10f87a72aeb` | 6 | 30 / 1,132,462,080 | 2 / 75,497,472 | 31 / 1,170,210,816 | 47 / 1,774,190,592 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/05-cfbcfa3e382f12aed450b10f87a72aeb/traces.tar.gz) |
| 06 | `3f5fa378239f7475baac89fa40288aaa` | 6 | 21 / 792,723,456 | 4 / 150,994,944 | 24 / 905,969,664 | 36 / 1,358,954,496 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/06-3f5fa378239f7475baac89fa40288aaa/traces.tar.gz) |
| 07 | `5c13daa9432149f6243aa1115629cd1a` | 7 | 22 / 830,472,192 | 4 / 150,994,944 | 24 / 905,969,664 | 37 / 1,396,703,232 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/07-5c13daa9432149f6243aa1115629cd1a/traces.tar.gz) |
| 08 | `694e275f1a01ad0e8ac448ad809f7930` | 8 | 29 / 1,094,713,344 | 7 / 264,241,152 | 27 / 1,019,215,872 | 45 / 1,698,693,120 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/08-694e275f1a01ad0e8ac448ad809f7930/traces.tar.gz) |
| 09 | `aea2634b0e5f1c2444550d31c41adc94` | 8 | 31 / 1,170,210,816 | 6 / 226,492,416 | 31 / 1,170,210,816 | 53 / 2,000,683,008 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/09-aea2634b0e5f1c2444550d31c41adc94/traces.tar.gz) |
| 10 | `79f0d0539d9ec0acbf90cb3388b30c17` | 7 | 23 / 868,220,928 | 5 / 188,743,680 | 23 / 868,220,928 | 38 / 1,434,451,968 | [Trace bundle](https://github.com/Kibnelson/evidence_store_2/blob/5f57c3f51452cdca1f84d858c0e5293f98db8b6d/reports/lifecycle/clapnq-nixl-run3/conversations/10-79f0d0539d9ec0acbf90cb3388b30c17/traces.tar.gz) |

## Per-turn prompt and block coverage

The following rows apply to both memory and disk. P hits are tokens already in P's GPU prefix. D coverage is shown as local GPU blocks + blocks pulled through NIXL. vLLM blocks have 16 token slots, so the prompt block count rounds up. The LMCache tail counts prompt tokens past the last complete 256-token object. D writes the final prompt token for logits and writes seven generated input positions over the rest of its decode steps.

For example, carry-forward turn 4 in conversation 01 had 2,660 tokens, which use 167 GPU blocks. D had 688 local tokens in 43 blocks and pulled 1,972 tokens in 124 blocks over NIXL. The final GPU block covers four prompt tokens. Ten full 256-token LMCache objects cover 2,560 tokens and the tail is 100 tokens.

### Conversation 01

`1534a095279f2cb888fb0bea17bd70da`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 702 / 44 | 0 | 0 + 44 | 190 | 702 / 44 | 0 | 0 + 44 | 190 |
| 2 | D1 | 669 / 42 | 0 | 0 + 42 | 157 | 1,350 / 85 | 688 | 0 + 85 | 70 |
| 3 | D2 | 723 / 46 | 48 | 0 + 46 | 211 | 2,007 / 126 | 1,344 | 0 + 126 | 215 |
| 4 | D0 | 765 / 48 | 80 | 0 + 48 | 253 | 2,660 / 167 | 2,000 | 43 + 124 | 100 |
| 5 | D1 | 851 / 54 | 128 | 3 + 51 | 83 | 3,357 / 210 | 2,656 | 84 + 126 | 29 |

### Conversation 02

`0208bf26ec357a803445290fa88a2e9e`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 1,242 / 78 | 0 | 0 + 78 | 218 | 1,242 / 78 | 0 | 0 + 78 | 218 |
| 2 | D1 | 1,317 / 83 | 0 | 0 + 83 | 37 | 2,537 / 159 | 1,232 | 0 + 159 | 233 |
| 3 | D2 | 1,307 / 82 | 80 | 0 + 82 | 27 | 3,739 / 234 | 2,528 | 0 + 234 | 155 |
| 4 | D0 | 684 / 43 | 176 | 0 + 43 | 172 | 4,218 / 264 | 3,728 | 78 + 186 | 122 |
| 5 | D1 | 1,685 / 106 | 224 | 5 + 101 | 149 | 5,664 / 354 | 4,208 | 158 + 196 | 32 |
| 6 | D2 | 1,727 / 108 | 240 | 11 + 97 | 191 | 7,117 / 445 | 5,664 | 233 + 212 | 205 |
| 7 | D0 | 1,452 / 91 | 368 | 14 + 77 | 172 | 8,177 / 512 | 7,104 | 263 + 249 | 241 |

### Conversation 03

`a2698b2973ea7db1ee5adb5e70ec02e4`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 676 / 43 | 0 | 0 + 43 | 164 | 676 / 43 | 0 | 0 + 43 | 164 |
| 2 | D1 | 641 / 41 | 0 | 0 + 41 | 129 | 1,294 / 81 | 672 | 0 + 81 | 14 |
| 3 | D2 | 931 / 59 | 128 | 0 + 59 | 163 | 2,080 / 130 | 1,280 | 0 + 130 | 32 |
| 4 | D0 | 1,170 / 74 | 384 | 0 + 74 | 146 | 2,841 / 178 | 2,080 | 42 + 136 | 25 |
| 5 | D1 | 1,475 / 93 | 560 | 8 + 85 | 195 | 3,722 / 233 | 2,832 | 81 + 152 | 138 |
| 6 | D2 | 1,762 / 111 | 736 | 24 + 87 | 226 | 4,700 / 294 | 3,712 | 130 + 164 | 92 |
| 7 | D0 | 1,938 / 122 | 1,120 | 35 + 87 | 146 | 5,499 / 344 | 4,688 | 177 + 167 | 123 |
| 8 | D1 | 2,479 / 155 | 1,296 | 46 + 109 | 175 | 6,655 / 416 | 5,488 | 232 + 184 | 255 |
| 9 | D2 | 2,591 / 162 | 1,472 | 70 + 92 | 31 | 7,748 / 485 | 6,640 | 293 + 192 | 68 |

### Conversation 04

`c1e53df98a28f19448f4af244304b89a`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 643 / 41 | 0 | 0 + 41 | 131 | 643 / 41 | 0 | 0 + 41 | 131 |
| 2 | D1 | 769 / 49 | 0 | 0 + 49 | 1 | 1,388 / 87 | 640 | 0 + 87 | 108 |
| 3 | D2 | 672 / 42 | 96 | 0 + 42 | 160 | 1,935 / 121 | 1,376 | 0 + 121 | 143 |
| 4 | D0 | 838 / 53 | 176 | 0 + 53 | 70 | 2,574 / 161 | 1,920 | 40 + 121 | 14 |
| 5 | D1 | 976 / 61 | 272 | 6 + 55 | 208 | 3,249 / 204 | 2,560 | 87 + 117 | 177 |
| 6 | D2 | 1,215 / 76 | 320 | 11 + 65 | 191 | 4,124 / 258 | 3,248 | 120 + 138 | 28 |

### Conversation 05

`cfbcfa3e382f12aed450b10f87a72aeb`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 1,242 / 78 | 0 | 0 + 78 | 218 | 1,242 / 78 | 0 | 0 + 78 | 218 |
| 2 | D1 | 1,460 / 92 | 0 | 0 + 92 | 180 | 2,680 / 168 | 1,232 | 0 + 168 | 120 |
| 3 | D2 | 1,155 / 73 | 64 | 0 + 73 | 131 | 3,747 / 235 | 2,672 | 0 + 235 | 163 |
| 4 | D0 | 1,699 / 107 | 176 | 0 + 107 | 163 | 5,246 / 328 | 3,744 | 78 + 250 | 126 |
| 5 | D1 | 2,044 / 128 | 320 | 4 + 124 | 252 | 6,930 / 434 | 5,232 | 167 + 267 | 18 |
| 6 | D2 | 1,708 / 107 | 480 | 11 + 96 | 172 | 8,145 / 510 | 6,928 | 234 + 276 | 209 |

### Conversation 06

`3f5fa378239f7475baac89fa40288aaa`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 910 / 57 | 0 | 0 + 57 | 142 | 910 / 57 | 0 | 0 + 57 | 142 |
| 2 | D1 | 1,124 / 71 | 0 | 0 + 71 | 100 | 2,013 / 126 | 896 | 0 + 126 | 221 |
| 3 | D2 | 1,526 / 96 | 272 | 0 + 96 | 246 | 3,243 / 203 | 2,000 | 0 + 203 | 171 |
| 4 | D0 | 1,517 / 95 | 560 | 0 + 95 | 237 | 4,190 / 262 | 3,232 | 57 + 205 | 94 |
| 5 | D1 | 1,741 / 109 | 592 | 17 + 92 | 205 | 5,311 / 332 | 4,176 | 126 + 206 | 191 |
| 6 | D2 | 1,501 / 94 | 624 | 35 + 59 | 221 | 6,167 / 386 | 5,296 | 202 + 184 | 23 |

### Conversation 07

`5c13daa9432149f6243aa1115629cd1a`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 962 / 61 | 0 | 0 + 61 | 194 | 962 / 61 | 0 | 0 + 61 | 194 |
| 2 | D1 | 862 / 54 | 0 | 0 + 54 | 94 | 1,799 / 113 | 960 | 0 + 113 | 7 |
| 3 | D2 | 859 / 54 | 112 | 0 + 54 | 91 | 2,519 / 158 | 1,792 | 0 + 158 | 215 |
| 4 | D0 | 1,380 / 87 | 256 | 0 + 87 | 100 | 3,628 / 227 | 2,512 | 60 + 167 | 44 |
| 5 | D1 | 1,000 / 63 | 416 | 7 + 56 | 232 | 4,196 / 263 | 3,616 | 112 + 151 | 100 |
| 6 | D2 | 1,787 / 112 | 528 | 16 + 96 | 251 | 5,440 / 340 | 4,192 | 157 + 183 | 64 |
| 7 | D0 | 1,487 / 93 | 672 | 26 + 67 | 207 | 6,236 / 390 | 5,440 | 226 + 164 | 92 |

### Conversation 08

`694e275f1a01ad0e8ac448ad809f7930`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 1,292 / 81 | 0 | 0 + 81 | 12 | 1,292 / 81 | 0 | 0 + 81 | 12 |
| 2 | D1 | 1,035 / 65 | 0 | 0 + 65 | 11 | 2,305 / 145 | 1,280 | 0 + 145 | 1 |
| 3 | D2 | 1,029 / 65 | 144 | 0 + 65 | 5 | 3,140 / 197 | 2,304 | 0 + 197 | 68 |
| 4 | D0 | 1,127 / 71 | 352 | 0 + 71 | 103 | 3,865 / 242 | 3,136 | 81 + 161 | 25 |
| 5 | D1 | 1,520 / 95 | 656 | 9 + 86 | 240 | 4,706 / 295 | 3,856 | 144 + 151 | 98 |
| 6 | D2 | 1,586 / 100 | 848 | 22 + 78 | 50 | 5,416 / 339 | 4,704 | 196 + 143 | 40 |
| 7 | D0 | 1,971 / 124 | 992 | 41 + 83 | 179 | 6,355 / 398 | 5,408 | 241 + 157 | 211 |
| 8 | D1 | 1,864 / 117 | 1,168 | 53 + 64 | 72 | 7,029 / 440 | 6,352 | 294 + 146 | 117 |

### Conversation 09

`aea2634b0e5f1c2444550d31c41adc94`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 1,321 / 83 | 0 | 0 + 83 | 41 | 1,321 / 83 | 0 | 0 + 83 | 41 |
| 2 | D1 | 1,529 / 96 | 0 | 0 + 96 | 249 | 2,825 / 177 | 1,312 | 0 + 177 | 9 |
| 3 | D2 | 1,748 / 110 | 224 | 0 + 110 | 212 | 4,340 / 272 | 2,816 | 0 + 272 | 244 |
| 4 | D0 | 1,174 / 74 | 336 | 0 + 74 | 150 | 5,159 / 323 | 4,336 | 83 + 240 | 39 |
| 5 | D1 | 1,205 / 76 | 640 | 14 + 62 | 181 | 5,701 / 357 | 5,152 | 176 + 181 | 69 |
| 6 | D2 | 1,555 / 98 | 736 | 21 + 77 | 19 | 6,498 / 407 | 5,696 | 271 + 136 | 98 |
| 7 | D0 | 1,590 / 100 | 832 | 40 + 60 | 54 | 7,240 / 453 | 6,496 | 322 + 131 | 72 |
| 8 | D1 | 1,703 / 107 | 848 | 46 + 61 | 167 | 8,073 / 505 | 7,232 | 356 + 149 | 137 |

### Conversation 10

`79f0d0539d9ec0acbf90cb3388b30c17`

| Turn | D | Chat tokens / blocks | Chat P hit tokens | Chat D blocks | Chat LMCache tail | Carry tokens / blocks | Carry P hit tokens | Carry D blocks | Carry LMCache tail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D0 | 743 / 47 | 0 | 0 + 47 | 231 | 743 / 47 | 0 | 0 + 47 | 231 |
| 2 | D1 | 841 / 53 | 0 | 0 + 53 | 73 | 1,562 / 98 | 736 | 0 + 98 | 26 |
| 3 | D2 | 1,298 / 82 | 128 | 0 + 82 | 18 | 2,722 / 171 | 1,552 | 0 + 171 | 162 |
| 4 | D0 | 1,161 / 73 | 272 | 0 + 73 | 137 | 3,589 / 225 | 2,720 | 46 + 179 | 5 |
| 5 | D1 | 1,321 / 83 | 416 | 8 + 75 | 41 | 4,477 / 280 | 3,584 | 97 + 183 | 125 |
| 6 | D2 | 1,648 / 103 | 688 | 17 + 86 | 112 | 5,415 / 339 | 4,464 | 170 + 169 | 39 |
| 7 | D0 | 1,498 / 94 | 880 | 26 + 68 | 218 | 6,010 / 376 | 5,408 | 224 + 152 | 122 |

## Follow one block in disk carry-forward

[Open the prompt-first view](prompt-timeline-turn4-shared.md) to see the exact prompt, token IDs, all 167 numbered blocks, and their GPU and LMCache events.

Conversation 01, turn 4. Logical block 43 falls immediately after D0's local prefix. The events below follow the P GPU slot, the NIXL handoff into D0's GPU slot, and related LMCache object events.

Prompt tokens `[688, 704)` in a 2,660-token request.

| Worker | Pool | Block ID | Generation | GPU token slots | KV source |
| --- | --- | --- | --- | --- | --- |
| p0 | 135444014760544 | 44 | 2 | `[704, 720)` | Local GPU prefix |
| d0 | 140433746993056 | 45 | 2 | `[720, 736)` | NIXL |

Slot ranges above come from the scheduler block tables. The model write rows use the GPU's recorded token-slot indices. NIXL readiness is measured for the whole request, with the block included in its verified transfer list. Prefix-cache publication records the index entry. The GPU write or NIXL-ready event records when the corresponding KV becomes available.

Object 1 on `lmcache` · `Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@0c6ab3331945c15d51ce3d0e66b8a9dd605958d0e20d70a55372363ffb45c8a4@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

Times are elapsed milliseconds from P scheduler arrival on the selected turn. Negative times show earlier events for the same slot generation or cache object. Disk and CPU events are joined by server and object ID.

| Elapsed (ms) | Actor | Observed event | Detail |
| --- | --- | --- | --- |
| -1,824.245 | p0 | Allocated GPU block |  |
| -1,823.255 | p0 | Indexed block under its prefix hash |  |
| -1,741.218 | p0 | Turn 2 model GPU write | Tokens `[688, 704)` · recorded slots `[704, 720)` |
| -1,728.031 | lmcache | LMCache CPU placement | Object 1 · 37,748,736 B · store |
| -1,727.024 | p0 | Turn 2 GPU offload receipt | lmcache object covers `[512, 768)` |
| -1,625.834 | lmcache | Direct disk write completed | Object 1 · 37,748,736 B |
| -1,518.865 | lmcache | LMCache CPU eviction | Object 1 · 37,748,736 B · l1_remove |
| -1,253.413 | p0 | Released reference to GPU block | reference_release · prefix resident True |
| -996.093 | p0 | Turn 3 local prefix hit | Prompt tokens `[688, 704)` |
| -815.759 | lmcache | Direct disk read completed | Object 1 · 37,748,736 B |
| -767.679 | lmcache | LMCache CPU placement | Object 1 · 37,748,736 B · prefetch |
| -755.447 | lmcache | LMCache CPU eviction | Object 1 · 37,748,736 B · read_finished |
| -256.970 | p0 | Released reference to GPU block | reference_release · prefix resident True |
| 6.177 | p0 | Turn 4 local prefix hit | Prompt tokens `[688, 704)` |
| 145.785 | lmcache | Direct disk read completed | Object 1 · 37,748,736 B |
| 244.890 | lmcache | LMCache CPU placement | Object 1 · 37,748,736 B · prefetch |
| 247.688 | d0 | Allocated GPU block |  |
| 256.960 | lmcache | LMCache CPU eviction | Object 1 · 37,748,736 B · read_finished |
| 731.079 | d0 | Turn 4 NIXL prefix ready | Includes prompt tokens `[688, 704)` |
| 731.437 | d0 | Indexed block under its prefix hash |  |
| 738.337 | p0 | Released reference to GPU block | reference_release · prefix resident True |
| 903.342 | d0 | Released reference to GPU block | reference_release · prefix resident True |
| 991.493 | p0 | Turn 5 local prefix hit | Prompt tokens `[688, 704)` |
| 1,744.459 | p0 | Released reference to GPU block | reference_release · prefix resident True |
| 1,996.841 | p0 | Evicted prefix-cache entry | reset |
| 2,008.311 | d0 | Evicted prefix-cache entry | reset |

## Inspect another turn or export a block map

Extract a conversation trace bundle to a directory and set the shell variable bundle to its path. The directory contains the frozen manifest and four phases. Run these commands from the V2 repository at the source revision above. The first writes a timeline for one logical prompt block. The second writes the physical GPU slots, their generations, and the source of each prompt block for an entire phase.

```bash
python3 -B scripts/lifecycle_paired_timeline.py "$bundle/disk-carry_forward" \
  --mode disk --layout carry_forward --topology shared_engine --turn 4 --block 43

python3 -B scripts/lifecycle_paired_timeline.py "$bundle/disk-carry_forward" \
  --mode disk --layout carry_forward --topology shared_engine --movement-csv > block-map.csv
```

Select another phase and its matching mode and layout arguments to inspect its trace. Use the manifest's token IDs and evidence spans to match a logical block back to the prompt.
