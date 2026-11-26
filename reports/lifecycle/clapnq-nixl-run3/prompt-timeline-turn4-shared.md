# Prompt timeline for turn 4 · shared_engine

MT-RAG CLAPNQ `1534a095279f2cb888fb0bea17bd70da` · disk · carry_forward · decoder `d0`.

[Request timeline](#request-timeline) · [Block map](#token-ids-and-physical-block-movement) · [LMCache events](#lmcache-copies-and-storage-events)

## Prompt

Request `mtrag:1534a095279f2cb888fb0bea17bd70da<::>4` · token SHA-256 `b1f9566938122d27b76644fb5b98270d833f47df32544137295400a74c33781d`.

<details>
<summary>Read the exact prompt text</summary>

```text
Answer each question using the supplied evidence.

Evidence:
[Document 1]
Aviation photography
In ground - to - air photography , photos of aircraft in flight are taken with the photographer on the ground . This type of photography is common at airshows or airports . Generally , a long focus photographic lens is necessary due to the greater distance between the photographer and the target aircraft . Along with ground - static photography , this is the most popular form of aviation photography .
[/Document]
[Document 2]
Aviation photography
Aviation photography is the act of taking images of aircraft , either in flight , or on the ground . Types of aviation photography include air - to - air , ground - to - air , ground - static , and remote photography . Military aviation photography , especially air - to - air , requires additional skills , as the photo and target aircraft often fly at velocities of over Mach 1 , while under moderate to high G .
[/Document]
[Document 3]
Aviation photography
In ground - static photography , photos of stationary aircraft are taken by photographers on the ground . Photos can be of aircraft exteriors , interiors , and aircraft details . The photographer has full control over lighting , aircraft placement , camera angles , and background . Involving other subjects such as the pilot or other aircraft is much easier to accomplish in ground - static photography than in other forms of aerial photography .
[/Document]
[Document 4]
Aviation photography
Air - to - air photography is the art of photographing aircraft in the air , while using another aircraft as a photo platform . The subject aircraft is photographed while both aircraft are in flight . This allows the photographer to position the subject in specific locations and angles to get the most desirable shot . Some things that must be considered to achieve best results are lighting and background . Proper lighting is achieved through correct placement of the aircraft relative to the sun , and is accomplished flying only at certain times of the day and / or by flying at a heading that lines the sun up on the subject aircraft properly . The background can highlight or distract from the subject and must be carefully considered when taking shots . Air - to - air photography uses include commercial use and advertising . Remote
[/Document]
[Document 5]
Aviation photography
Remote photography is a variation on aerial air - to - air photography , whereby the camera is mounted onto the external aircraft structure away from the photographer and is triggered remotely using a mechanical or electrical shutter release . The image has to be composed when the aircraft is on the ground , because the photographer has no access to the camera while the aircraft is in flight . Much brainstorming and planning must be done while setting up the camera to get the desired shot . Remote photography is the least common type of aviation photography .
[/Document]
[Document 6]
Aviation photography
Ground to air photograph of an Emirates Airbus A380 departing London Heathrow Airport A Qantas Boeing 747 - 400 overflying Starbeyevo , Moscow at 11,000 m . The aircraft was photographed from the ground using a Canon 400D , a 1200mm telescope and 2x Barlow lens . Fat Albert , a U.S. Marine Corps C - 130T Hercules with the Blue Angels , flies over Marines with the Silent Drill Platoon at Marine Corps Air Station Yuma
[/Document]
Question: who takes photos of planes in the air
Answer: In ground-to-air photography, photos of aircraft in flight are taken with the photographer on the ground. This type of photography is common at airshows or airports.

Evidence:
[Document 1]
Aviation photography
Aviation photography is the act of taking images of aircraft , either in flight , or on the ground . Types of aviation photography include air - to - air , ground - to - air , ground - static , and remote photography . Military aviation photography , especially air - to - air , requires additional skills , as the photo and target aircraft often fly at velocities of over Mach 1 , while under moderate to high G .
[/Document]
[Document 2]
Aviation photography
In ground - to - air photography , photos of aircraft in flight are taken with the photographer on the ground . This type of photography is common at airshows or airports . Generally , a long focus photographic lens is necessary due to the greater distance between the photographer and the target aircraft . Along with ground - static photography , this is the most popular form of aviation photography .
[/Document]
[Document 3]
Aviation photography
Remote photography is a variation on aerial air - to - air photography , whereby the camera is mounted onto the external aircraft structure away from the photographer and is triggered remotely using a mechanical or electrical shutter release . The image has to be composed when the aircraft is on the ground , because the photographer has no access to the camera while the aircraft is in flight . Much brainstorming and planning must be done while setting up the camera to get the desired shot . Remote photography is the least common type of aviation photography .
[/Document]
[Document 4]
Aviation photography
In ground - static photography , photos of stationary aircraft are taken by photographers on the ground . Photos can be of aircraft exteriors , interiors , and aircraft details . The photographer has full control over lighting , aircraft placement , camera angles , and background . Involving other subjects such as the pilot or other aircraft is much easier to accomplish in ground - static photography than in other forms of aerial photography .
[/Document]
[Document 5]
Aviation photography
Air - to - air photography is the art of photographing aircraft in the air , while using another aircraft as a photo platform . The subject aircraft is photographed while both aircraft are in flight . This allows the photographer to position the subject in specific locations and angles to get the most desirable shot . Some things that must be considered to achieve best results are lighting and background . Proper lighting is achieved through correct placement of the aircraft relative to the sun , and is accomplished flying only at certain times of the day and / or by flying at a heading that lines the sun up on the subject aircraft properly . The background can highlight or distract from the subject and must be carefully considered when taking shots . Air - to - air photography uses include commercial use and advertising . Remote
[/Document]
[Document 6]
Aviation photography
Databases exist on the internet , cataloguing aviation photographs . These include airliners.net , jetphotos.net and airplane-pictures.net allow users to search them for photographs of aircraft based on user - specified criteria .
[/Document]
Question: No, I meant photos in the air.
Answer: Air - to - air aviation photography is the art of photographing aircraft in the air, while using another aircraft as a photo platform.

Evidence:
[Document 1]
Aviation photography
Aviation photography is the act of taking images of aircraft , either in flight , or on the ground . Types of aviation photography include air - to - air , ground - to - air , ground - static , and remote photography . Military aviation photography , especially air - to - air , requires additional skills , as the photo and target aircraft often fly at velocities of over Mach 1 , while under moderate to high G .
[/Document]
[Document 2]
Aviation photography
In ground - static photography , photos of stationary aircraft are taken by photographers on the ground . Photos can be of aircraft exteriors , interiors , and aircraft details . The photographer has full control over lighting , aircraft placement , camera angles , and background . Involving other subjects such as the pilot or other aircraft is much easier to accomplish in ground - static photography than in other forms of aerial photography .
[/Document]
[Document 3]
Aviation photography
In ground - to - air photography , photos of aircraft in flight are taken with the photographer on the ground . This type of photography is common at airshows or airports . Generally , a long focus photographic lens is necessary due to the greater distance between the photographer and the target aircraft . Along with ground - static photography , this is the most popular form of aviation photography .
[/Document]
[Document 4]
Aviation photography
Remote photography is a variation on aerial air - to - air photography , whereby the camera is mounted onto the external aircraft structure away from the photographer and is triggered remotely using a mechanical or electrical shutter release . The image has to be composed when the aircraft is on the ground , because the photographer has no access to the camera while the aircraft is in flight . Much brainstorming and planning must be done while setting up the camera to get the desired shot . Remote photography is the least common type of aviation photography .
[/Document]
[Document 5]
Aviation photography
Air - to - air photography is the art of photographing aircraft in the air , while using another aircraft as a photo platform . The subject aircraft is photographed while both aircraft are in flight . This allows the photographer to position the subject in specific locations and angles to get the most desirable shot . Some things that must be considered to achieve best results are lighting and background . Proper lighting is achieved through correct placement of the aircraft relative to the sun , and is accomplished flying only at certain times of the day and / or by flying at a heading that lines the sun up on the subject aircraft properly . The background can highlight or distract from the subject and must be carefully considered when taking shots . Air - to - air photography uses include commercial use and advertising . Remote
[/Document]
[Document 6]
Aviation photography
This article needs additional citations for verification . Please help improve this article by adding citations to reliable sources . Unsourced material may be challenged and removed . ( September 2009 ) ( Learn how and when to remove this template message ) Air
[/Document]
Question: So does that mean pilot of the second aircraft also acts as a photographer?
Answer: I am sorry I don't have any specific knowledge about who acts as a photographer in air-to-air aviation photography. 

Evidence:
[Document 1]
Aviation photography
In ground - to - air photography , photos of aircraft in flight are taken with the photographer on the ground . This type of photography is common at airshows or airports . Generally , a long focus photographic lens is necessary due to the greater distance between the photographer and the target aircraft . Along with ground - static photography , this is the most popular form of aviation photography .
[/Document]
[Document 2]
Aviation photography
Aviation photography is the act of taking images of aircraft , either in flight , or on the ground . Types of aviation photography include air - to - air , ground - to - air , ground - static , and remote photography . Military aviation photography , especially air - to - air , requires additional skills , as the photo and target aircraft often fly at velocities of over Mach 1 , while under moderate to high G .
[/Document]
[Document 3]
Aviation photography
Remote photography is a variation on aerial air - to - air photography , whereby the camera is mounted onto the external aircraft structure away from the photographer and is triggered remotely using a mechanical or electrical shutter release . The image has to be composed when the aircraft is on the ground , because the photographer has no access to the camera while the aircraft is in flight . Much brainstorming and planning must be done while setting up the camera to get the desired shot . Remote photography is the least common type of aviation photography .
[/Document]
[Document 4]
Aviation photography
Air - to - air photography is the art of photographing aircraft in the air , while using another aircraft as a photo platform . The subject aircraft is photographed while both aircraft are in flight . This allows the photographer to position the subject in specific locations and angles to get the most desirable shot . Some things that must be considered to achieve best results are lighting and background . Proper lighting is achieved through correct placement of the aircraft relative to the sun , and is accomplished flying only at certain times of the day and / or by flying at a heading that lines the sun up on the subject aircraft properly . The background can highlight or distract from the subject and must be carefully considered when taking shots . Air - to - air photography uses include commercial use and advertising . Remote
[/Document]
[Document 5]
Aviation photography
In ground - static photography , photos of stationary aircraft are taken by photographers on the ground . Photos can be of aircraft exteriors , interiors , and aircraft details . The photographer has full control over lighting , aircraft placement , camera angles , and background . Involving other subjects such as the pilot or other aircraft is much easier to accomplish in ground - static photography than in other forms of aerial photography .
[/Document]
[Document 6]
Aviation photography
This article needs additional citations for verification . Please help improve this article by adding citations to reliable sources . Unsourced material may be challenged and removed . ( September 2009 ) ( Learn how and when to remove this template message ) Air
[/Document]
Question: Is air-to-air phtography more difficult that ground-to-air?
Answer:
```

</details>

**2,660 tokens** occupy **167 logical GPU blocks** with 12 unused prompt slots at the end. The prompt fits 10 complete 256-token LMCache objects and a 100-token tail.

P reused **2,000** prompt tokens on GPU and computed **660**. d0 reused **688** on GPU and pulled **1,972** over NIXL in **124 blocks** (292,552,704 B).

## Request timeline

Times are milliseconds from P scheduler arrival. NIXL readiness covers the request's transfer batch.

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| 0.000 | p0 | Prompt arrived |
| 6.177 | p0 | GPU prefix lookup · 2,000 local tokens |
| 103.652 | p0 | Last prompt KV write completed |
| 108.884 | Driver | Dispatched to d0 |
| 112.360 | d0 | Prompt arrived |
| 114.852 | p0 | GPU → lmcache · 3 objects · 113,246,208 B |
| 247.293 | d0 | Prefix decision · 688 local · 1,972 NIXL tokens |
| 731.079 | d0 | NIXL batch ready on GPU |
| 773.477 | d0 | Wrote final prompt token for logits |
| 900.119 | d0 | Released request's block references |

## Token IDs and physical block movement

Logical blocks are zero-based and stay tied to prompt positions. Physical block IDs are local to each worker. Each slot cell shows block ID/generation and valid GPU token slots. P pool `135444014760544` · d0 pool `140433746993056`. The request timeline gives NIXL readiness for all rows marked NIXL. LMCache links identify whole objects for the same prompt prefix. Their event lists show which worker copied each object and any later CPU or disk activity.

| Logical block | Prompt positions | Exact token IDs | P block/gen · slots | P source | d0 block/gen · slots | D source | LMCache objects |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `[0, 16)` | `[16141, 1817, 3405, 1667, 279, 17221, 5904, 382, 92602, 510, 58, 7524, 220, 16, 921, 9865]` | 1/1 · `[16, 32)` | GPU prefix | 1/1 · `[16, 32)` | GPU prefix | [M01](#lmcache-object-m01) |
| 1 | `[16, 32)` | `[7101, 23751, 198, 641, 4910, 481, 311, 481, 3720, 23751, 1154, 7249, 315, 14135, 304, 10971]` | 2/1 · `[32, 48)` | GPU prefix | 2/1 · `[32, 48)` | GPU prefix | [M01](#lmcache-object-m01) |
| 2 | `[32, 48)` | `[525, 4429, 448, 279, 28767, 389, 279, 4910, 659, 1096, 943, 315, 23751, 374, 4185, 518]` | 3/1 · `[48, 64)` | GPU prefix | 3/1 · `[48, 64)` | GPU prefix | [M01](#lmcache-object-m01) |
| 3 | `[48, 64)` | `[3720, 59456, 476, 45063, 659, 43393, 1154, 264, 1293, 5244, 69064, 18342, 374, 5871, 4152, 311]` | 4/1 · `[64, 80)` | GPU prefix | 4/1 · `[64, 80)` | GPU prefix | [M01](#lmcache-object-m01) |
| 4 | `[64, 80)` | `[279, 7046, 6010, 1948, 279, 28767, 323, 279, 2169, 14135, 659, 31844, 448, 4910, 481, 1099]` | 5/1 · `[80, 96)` | GPU prefix | 5/1 · `[80, 96)` | GPU prefix | [M01](#lmcache-object-m01) |
| 5 | `[80, 96)` | `[23751, 1154, 419, 374, 279, 1429, 5411, 1352, 315, 45530, 23751, 16448, 24157, 7524, 921, 58]` | 6/1 · `[96, 112)` | GPU prefix | 6/1 · `[96, 112)` | GPU prefix | [M01](#lmcache-object-m01) |
| 6 | `[96, 112)` | `[7524, 220, 17, 921, 9865, 7101, 23751, 198, 9865, 7101, 23751, 374, 279, 1160, 315, 4633]` | 7/1 · `[112, 128)` | GPU prefix | 7/1 · `[112, 128)` | GPU prefix | [M01](#lmcache-object-m01) |
| 7 | `[112, 128)` | `[5335, 315, 14135, 1154, 2987, 304, 10971, 1154, 476, 389, 279, 4910, 659, 20768, 315, 45530]` | 8/1 · `[128, 144)` | GPU prefix | 8/1 · `[128, 144)` | GPU prefix | [M01](#lmcache-object-m01) |
| 8 | `[128, 144)` | `[23751, 2924, 3720, 481, 311, 481, 3720, 1154, 4910, 481, 311, 481, 3720, 1154, 4910, 481]` | 9/1 · `[144, 160)` | GPU prefix | 9/1 · `[144, 160)` | GPU prefix | [M01](#lmcache-object-m01) |
| 9 | `[144, 160)` | `[1099, 1154, 323, 8699, 23751, 659, 26960, 45530, 23751, 1154, 5310, 3720, 481, 311, 481, 3720]` | 10/1 · `[160, 176)` | GPU prefix | 10/1 · `[160, 176)` | GPU prefix | [M01](#lmcache-object-m01) |
| 10 | `[160, 176)` | `[1154, 7460, 5107, 7361, 1154, 438, 279, 6548, 323, 2169, 14135, 3545, 11466, 518, 74057, 315]` | 11/1 · `[176, 192)` | GPU prefix | 11/1 · `[176, 192)` | GPU prefix | [M01](#lmcache-object-m01) |
| 11 | `[176, 192)` | `[916, 18294, 220, 16, 1154, 1393, 1212, 23193, 311, 1550, 479, 16448, 24157, 7524, 921, 58]` | 12/1 · `[192, 208)` | GPU prefix | 12/1 · `[192, 208)` | GPU prefix | [M01](#lmcache-object-m01) |
| 12 | `[192, 208)` | `[7524, 220, 18, 921, 9865, 7101, 23751, 198, 641, 4910, 481, 1099, 23751, 1154, 7249, 315]` | 13/1 · `[208, 224)` | GPU prefix | 13/1 · `[208, 224)` | GPU prefix | [M01](#lmcache-object-m01) |
| 13 | `[208, 224)` | `[52635, 14135, 525, 4429, 553, 47177, 389, 279, 4910, 659, 16505, 646, 387, 315, 14135, 54267]` | 14/1 · `[224, 240)` | GPU prefix | 14/1 · `[224, 240)` | GPU prefix | [M01](#lmcache-object-m01) |
| 14 | `[224, 240)` | `[21867, 1154, 73464, 1154, 323, 14135, 3565, 659, 576, 28767, 702, 2480, 2524, 916, 17716, 1154]` | 15/1 · `[240, 256)` | GPU prefix | 15/1 · `[240, 256)` | GPU prefix | [M01](#lmcache-object-m01) |
| 15 | `[240, 256)` | `[14135, 21448, 1154, 6249, 25941, 1154, 323, 4004, 659, 758, 12536, 4405, 1008, 14878, 1741, 438]` | 16/1 · `[256, 272)` | GPU prefix | 16/1 · `[256, 272)` | GPU prefix | [M01](#lmcache-object-m01) |
| 16 | `[256, 272)` | `[279, 17708, 476, 1008, 14135, 374, 1753, 8661, 311, 22054, 304, 4910, 481, 1099, 23751, 1091]` | 17/1 · `[272, 288)` | GPU prefix | 17/1 · `[272, 288)` | GPU prefix | [M02](#lmcache-object-m02) |
| 17 | `[272, 288)` | `[304, 1008, 7586, 315, 40784, 23751, 16448, 24157, 7524, 921, 58, 7524, 220, 19, 921, 9865]` | 18/1 · `[288, 304)` | GPU prefix | 18/1 · `[288, 304)` | GPU prefix | [M02](#lmcache-object-m02) |
| 18 | `[288, 304)` | `[7101, 23751, 198, 25693, 481, 311, 481, 3720, 23751, 374, 279, 1947, 315, 10300, 287, 14135]` | 19/1 · `[304, 320)` | GPU prefix | 19/1 · `[304, 320)` | GPU prefix | [M02](#lmcache-object-m02) |
| 19 | `[304, 320)` | `[304, 279, 3720, 1154, 1393, 1667, 2441, 14135, 438, 264, 6548, 5339, 659, 576, 3832, 14135]` | 20/1 · `[320, 336)` | GPU prefix | 20/1 · `[320, 336)` | GPU prefix | [M02](#lmcache-object-m02) |
| 20 | `[320, 336)` | `[374, 56203, 1393, 2176, 14135, 525, 304, 10971, 659, 1096, 6147, 279, 28767, 311, 2309, 279]` | 21/1 · `[336, 352)` | GPU prefix | 21/1 · `[336, 352)` | GPU prefix | [M02](#lmcache-object-m02) |
| 21 | `[336, 352)` | `[3832, 304, 3151, 10468, 323, 25941, 311, 633, 279, 1429, 34846, 6552, 659, 4329, 2513, 429]` | 22/1 · `[352, 368)` | GPU prefix | 22/1 · `[352, 368)` | GPU prefix | [M02](#lmcache-object-m02) |
| 22 | `[352, 368)` | `[1969, 387, 6509, 311, 11075, 1850, 3059, 525, 17716, 323, 4004, 659, 64558, 17716, 374, 16994]` | 23/1 · `[368, 384)` | GPU prefix | 23/1 · `[368, 384)` | GPU prefix | [M02](#lmcache-object-m02) |
| 23 | `[368, 384)` | `[1526, 4396, 21448, 315, 279, 14135, 8674, 311, 279, 7015, 1154, 323, 374, 26237, 16307, 1172]` | 24/1 · `[384, 400)` | GPU prefix | 24/1 · `[384, 400)` | GPU prefix | [M02](#lmcache-object-m02) |
| 24 | `[384, 400)` | `[518, 3654, 3039, 315, 279, 1899, 323, 608, 476, 553, 16307, 518, 264, 14496, 429, 5128]` | 25/1 · `[400, 416)` | GPU prefix | 25/1 · `[400, 416)` | GPU prefix | [M02](#lmcache-object-m02) |
| 25 | `[400, 416)` | `[279, 7015, 705, 389, 279, 3832, 14135, 10277, 659, 576, 4004, 646, 11167, 476, 63817, 504]` | 26/1 · `[416, 432)` | GPU prefix | 26/1 · `[416, 432)` | GPU prefix | [M02](#lmcache-object-m02) |
| 26 | `[416, 432)` | `[279, 3832, 323, 1969, 387, 15516, 6509, 979, 4633, 14951, 659, 6553, 481, 311, 481, 3720]` | 27/1 · `[432, 448)` | GPU prefix | 27/1 · `[432, 448)` | GPU prefix | [M02](#lmcache-object-m02) |
| 27 | `[432, 448)` | `[23751, 5711, 2924, 8353, 990, 323, 12876, 659, 20738, 198, 24157, 7524, 921, 58, 7524, 220]` | 28/1 · `[448, 464)` | GPU prefix | 28/1 · `[448, 464)` | GPU prefix | [M02](#lmcache-object-m02) |
| 28 | `[448, 464)` | `[20, 921, 9865, 7101, 23751, 198, 24703, 23751, 374, 264, 22990, 389, 40784, 3720, 481, 311]` | 29/1 · `[464, 480)` | GPU prefix | 29/1 · `[464, 480)` | GPU prefix | [M02](#lmcache-object-m02) |
| 29 | `[464, 480)` | `[481, 3720, 23751, 1154, 47901, 279, 6249, 374, 21810, 8630, 279, 9250, 14135, 5944, 3123, 504]` | 30/1 · `[480, 496)` | GPU prefix | 30/1 · `[480, 496)` | GPU prefix | [M02](#lmcache-object-m02) |
| 30 | `[480, 496)` | `[279, 28767, 323, 374, 22119, 38429, 1667, 264, 22148, 476, 19734, 47956, 4879, 659, 576, 2168]` | 31/1 · `[496, 512)` | GPU prefix | 31/1 · `[496, 512)` | GPU prefix | [M02](#lmcache-object-m02) |
| 31 | `[496, 512)` | `[702, 311, 387, 23415, 979, 279, 14135, 374, 389, 279, 4910, 1154, 1576, 279, 28767, 702]` | 32/1 · `[512, 528)` | GPU prefix | 32/1 · `[512, 528)` | GPU prefix | [M02](#lmcache-object-m02) |
| 32 | `[512, 528)` | `[902, 2615, 311, 279, 6249, 1393, 279, 14135, 374, 304, 10971, 659, 23309, 86781, 287, 323]` | 33/1 · `[528, 544)` | GPU prefix | 33/1 · `[528, 544)` | GPU prefix | [M03](#lmcache-object-m03) |
| 33 | `[528, 544)` | `[9115, 1969, 387, 2814, 1393, 6243, 705, 279, 6249, 311, 633, 279, 12685, 6552, 659, 20738]` | 34/1 · `[544, 560)` | GPU prefix | 34/1 · `[544, 560)` | GPU prefix | [M03](#lmcache-object-m03) |
| 34 | `[544, 560)` | `[23751, 374, 279, 3245, 4185, 943, 315, 45530, 23751, 16448, 24157, 7524, 921, 58, 7524, 220]` | 35/1 · `[560, 576)` | GPU prefix | 35/1 · `[560, 576)` | GPU prefix | [M03](#lmcache-object-m03) |
| 35 | `[560, 576)` | `[21, 921, 9865, 7101, 23751, 198, 30714, 311, 3720, 10300, 315, 458, 48701, 80374, 362, 18]` | 36/1 · `[576, 592)` | GPU prefix | 36/1 · `[576, 592)` | GPU prefix | [M03](#lmcache-object-m03) |
| 36 | `[576, 592)` | `[23, 15, 80473, 7148, 47462, 651, 20691, 362, 1207, 76814, 41859, 220, 22, 19, 22, 481]` | 37/1 · `[592, 608)` | GPU prefix | 37/1 · `[592, 608)` | GPU prefix | [M03](#lmcache-object-m03) |
| 37 | `[592, 608)` | `[220, 19, 15, 15, 916, 69, 6711, 7679, 65, 18958, 3334, 1154, 22415, 518, 220, 16]` | 38/1 · `[608, 624)` | GPU prefix | 38/1 · `[608, 624)` | GPU prefix | [M03](#lmcache-object-m03) |
| 38 | `[608, 624)` | `[16, 11, 15, 15, 15, 296, 659, 576, 14135, 572, 56203, 504, 279, 4910, 1667, 264]` | 39/1 · `[624, 640)` | GPU prefix | 39/1 · `[624, 640)` | GPU prefix | [M03](#lmcache-object-m03) |
| 39 | `[624, 640)` | `[38116, 220, 19, 15, 15, 35, 1154, 264, 220, 16, 17, 15, 15, 3821, 55825, 323]` | 40/1 · `[640, 656)` | GPU prefix | 40/1 · `[640, 656)` | GPU prefix | [M03](#lmcache-object-m03) |
| 40 | `[640, 656)` | `[220, 17, 87, 4716, 10303, 18342, 659, 25348, 17513, 1154, 264, 547, 808, 13, 22963, 30142]` | 41/1 · `[656, 672)` | GPU prefix | 41/1 · `[656, 672)` | GPU prefix | [M03](#lmcache-object-m03) |
| 41 | `[656, 672)` | `[356, 481, 220, 16, 18, 15, 51, 93534, 448, 279, 8697, 42045, 1154, 37104, 916, 50789]` | 42/1 · `[672, 688)` | GPU prefix | 42/1 · `[672, 688)` | GPU prefix | [M03](#lmcache-object-m03) |
| 42 | `[672, 688)` | `[448, 279, 59455, 76874, 1818, 51675, 518, 22963, 30142, 6553, 16629, 809, 13416, 198, 24157, 7524]` | 43/1 · `[688, 704)` | GPU prefix | 43/1 · `[688, 704)` | GPU prefix | [M03](#lmcache-object-m03) |
| 43 | `[688, 704)` | `[921, 14582, 25, 879, 4990, 7249, 315, 24730, 304, 279, 3720, 198, 16141, 25, 758, 4910]` | 44/2 · `[704, 720)` | GPU prefix | 45/2 · `[720, 736)` | NIXL | [M03](#lmcache-object-m03) |
| 44 | `[704, 720)` | `[4686, 37535, 23751, 11, 7249, 315, 14135, 304, 10971, 525, 4429, 448, 279, 28767, 389, 279]` | 45/1 · `[720, 736)` | GPU prefix | 46/1 · `[736, 752)` | NIXL | [M03](#lmcache-object-m03) |
| 45 | `[720, 736)` | `[4910, 13, 1096, 943, 315, 23751, 374, 4185, 518, 3720, 59456, 476, 45063, 382, 92602, 510]` | 46/1 · `[736, 752)` | GPU prefix | 47/1 · `[752, 768)` | NIXL | [M03](#lmcache-object-m03) |
| 46 | `[736, 752)` | `[58, 7524, 220, 16, 921, 9865, 7101, 23751, 198, 9865, 7101, 23751, 374, 279, 1160, 315]` | 47/1 · `[752, 768)` | GPU prefix | 48/1 · `[768, 784)` | NIXL | [M03](#lmcache-object-m03) |
| 47 | `[752, 768)` | `[4633, 5335, 315, 14135, 1154, 2987, 304, 10971, 1154, 476, 389, 279, 4910, 659, 20768, 315]` | 48/1 · `[768, 784)` | GPU prefix | 49/1 · `[784, 800)` | NIXL | [M03](#lmcache-object-m03) |
| 48 | `[768, 784)` | `[45530, 23751, 2924, 3720, 481, 311, 481, 3720, 1154, 4910, 481, 311, 481, 3720, 1154, 4910]` | 49/1 · `[784, 800)` | GPU prefix | 50/1 · `[800, 816)` | NIXL | [M04](#lmcache-object-m04) |
| 49 | `[784, 800)` | `[481, 1099, 1154, 323, 8699, 23751, 659, 26960, 45530, 23751, 1154, 5310, 3720, 481, 311, 481]` | 50/1 · `[800, 816)` | GPU prefix | 51/1 · `[816, 832)` | NIXL | [M04](#lmcache-object-m04) |
| 50 | `[800, 816)` | `[3720, 1154, 7460, 5107, 7361, 1154, 438, 279, 6548, 323, 2169, 14135, 3545, 11466, 518, 74057]` | 51/1 · `[816, 832)` | GPU prefix | 52/1 · `[832, 848)` | NIXL | [M04](#lmcache-object-m04) |
| 51 | `[816, 832)` | `[315, 916, 18294, 220, 16, 1154, 1393, 1212, 23193, 311, 1550, 479, 16448, 24157, 7524, 921]` | 52/1 · `[832, 848)` | GPU prefix | 53/1 · `[848, 864)` | NIXL | [M04](#lmcache-object-m04) |
| 52 | `[832, 848)` | `[58, 7524, 220, 17, 921, 9865, 7101, 23751, 198, 641, 4910, 481, 311, 481, 3720, 23751]` | 53/1 · `[848, 864)` | GPU prefix | 54/1 · `[864, 880)` | NIXL | [M04](#lmcache-object-m04) |
| 53 | `[848, 864)` | `[1154, 7249, 315, 14135, 304, 10971, 525, 4429, 448, 279, 28767, 389, 279, 4910, 659, 1096]` | 54/1 · `[864, 880)` | GPU prefix | 55/1 · `[880, 896)` | NIXL | [M04](#lmcache-object-m04) |
| 54 | `[864, 880)` | `[943, 315, 23751, 374, 4185, 518, 3720, 59456, 476, 45063, 659, 43393, 1154, 264, 1293, 5244]` | 55/1 · `[880, 896)` | GPU prefix | 56/1 · `[896, 912)` | NIXL | [M04](#lmcache-object-m04) |
| 55 | `[880, 896)` | `[69064, 18342, 374, 5871, 4152, 311, 279, 7046, 6010, 1948, 279, 28767, 323, 279, 2169, 14135]` | 56/1 · `[896, 912)` | GPU prefix | 57/1 · `[912, 928)` | NIXL | [M04](#lmcache-object-m04) |
| 56 | `[896, 912)` | `[659, 31844, 448, 4910, 481, 1099, 23751, 1154, 419, 374, 279, 1429, 5411, 1352, 315, 45530]` | 57/1 · `[912, 928)` | GPU prefix | 58/1 · `[928, 944)` | NIXL | [M04](#lmcache-object-m04) |
| 57 | `[912, 928)` | `[23751, 16448, 24157, 7524, 921, 58, 7524, 220, 18, 921, 9865, 7101, 23751, 198, 24703, 23751]` | 58/1 · `[928, 944)` | GPU prefix | 59/1 · `[944, 960)` | NIXL | [M04](#lmcache-object-m04) |
| 58 | `[928, 944)` | `[374, 264, 22990, 389, 40784, 3720, 481, 311, 481, 3720, 23751, 1154, 47901, 279, 6249, 374]` | 59/1 · `[944, 960)` | GPU prefix | 60/1 · `[960, 976)` | NIXL | [M04](#lmcache-object-m04) |
| 59 | `[944, 960)` | `[21810, 8630, 279, 9250, 14135, 5944, 3123, 504, 279, 28767, 323, 374, 22119, 38429, 1667, 264]` | 60/1 · `[960, 976)` | GPU prefix | 61/1 · `[976, 992)` | NIXL | [M04](#lmcache-object-m04) |
| 60 | `[960, 976)` | `[22148, 476, 19734, 47956, 4879, 659, 576, 2168, 702, 311, 387, 23415, 979, 279, 14135, 374]` | 61/1 · `[976, 992)` | GPU prefix | 62/1 · `[992, 1008)` | NIXL | [M04](#lmcache-object-m04) |
| 61 | `[976, 992)` | `[389, 279, 4910, 1154, 1576, 279, 28767, 702, 902, 2615, 311, 279, 6249, 1393, 279, 14135]` | 62/1 · `[992, 1008)` | GPU prefix | 63/1 · `[1008, 1024)` | NIXL | [M04](#lmcache-object-m04) |
| 62 | `[992, 1008)` | `[374, 304, 10971, 659, 23309, 86781, 287, 323, 9115, 1969, 387, 2814, 1393, 6243, 705, 279]` | 63/1 · `[1008, 1024)` | GPU prefix | 64/1 · `[1024, 1040)` | NIXL | [M04](#lmcache-object-m04) |
| 63 | `[1008, 1024)` | `[6249, 311, 633, 279, 12685, 6552, 659, 20738, 23751, 374, 279, 3245, 4185, 943, 315, 45530]` | 64/1 · `[1024, 1040)` | GPU prefix | 65/1 · `[1040, 1056)` | NIXL | [M04](#lmcache-object-m04) |
| 64 | `[1024, 1040)` | `[23751, 16448, 24157, 7524, 921, 58, 7524, 220, 19, 921, 9865, 7101, 23751, 198, 641, 4910]` | 65/1 · `[1040, 1056)` | GPU prefix | 66/1 · `[1056, 1072)` | NIXL | [M05](#lmcache-object-m05) |
| 65 | `[1040, 1056)` | `[481, 1099, 23751, 1154, 7249, 315, 52635, 14135, 525, 4429, 553, 47177, 389, 279, 4910, 659]` | 66/1 · `[1056, 1072)` | GPU prefix | 67/1 · `[1072, 1088)` | NIXL | [M05](#lmcache-object-m05) |
| 66 | `[1056, 1072)` | `[16505, 646, 387, 315, 14135, 54267, 21867, 1154, 73464, 1154, 323, 14135, 3565, 659, 576, 28767]` | 67/1 · `[1072, 1088)` | GPU prefix | 68/1 · `[1088, 1104)` | NIXL | [M05](#lmcache-object-m05) |
| 67 | `[1072, 1088)` | `[702, 2480, 2524, 916, 17716, 1154, 14135, 21448, 1154, 6249, 25941, 1154, 323, 4004, 659, 758]` | 68/1 · `[1088, 1104)` | GPU prefix | 69/1 · `[1104, 1120)` | NIXL | [M05](#lmcache-object-m05) |
| 68 | `[1088, 1104)` | `[12536, 4405, 1008, 14878, 1741, 438, 279, 17708, 476, 1008, 14135, 374, 1753, 8661, 311, 22054]` | 69/1 · `[1104, 1120)` | GPU prefix | 70/1 · `[1120, 1136)` | NIXL | [M05](#lmcache-object-m05) |
| 69 | `[1104, 1120)` | `[304, 4910, 481, 1099, 23751, 1091, 304, 1008, 7586, 315, 40784, 23751, 16448, 24157, 7524, 921]` | 70/1 · `[1120, 1136)` | GPU prefix | 71/1 · `[1136, 1152)` | NIXL | [M05](#lmcache-object-m05) |
| 70 | `[1120, 1136)` | `[58, 7524, 220, 20, 921, 9865, 7101, 23751, 198, 25693, 481, 311, 481, 3720, 23751, 374]` | 71/1 · `[1136, 1152)` | GPU prefix | 72/1 · `[1152, 1168)` | NIXL | [M05](#lmcache-object-m05) |
| 71 | `[1136, 1152)` | `[279, 1947, 315, 10300, 287, 14135, 304, 279, 3720, 1154, 1393, 1667, 2441, 14135, 438, 264]` | 72/1 · `[1152, 1168)` | GPU prefix | 73/1 · `[1168, 1184)` | NIXL | [M05](#lmcache-object-m05) |
| 72 | `[1152, 1168)` | `[6548, 5339, 659, 576, 3832, 14135, 374, 56203, 1393, 2176, 14135, 525, 304, 10971, 659, 1096]` | 73/1 · `[1168, 1184)` | GPU prefix | 74/1 · `[1184, 1200)` | NIXL | [M05](#lmcache-object-m05) |
| 73 | `[1168, 1184)` | `[6147, 279, 28767, 311, 2309, 279, 3832, 304, 3151, 10468, 323, 25941, 311, 633, 279, 1429]` | 74/1 · `[1184, 1200)` | GPU prefix | 75/1 · `[1200, 1216)` | NIXL | [M05](#lmcache-object-m05) |
| 74 | `[1184, 1200)` | `[34846, 6552, 659, 4329, 2513, 429, 1969, 387, 6509, 311, 11075, 1850, 3059, 525, 17716, 323]` | 75/1 · `[1200, 1216)` | GPU prefix | 76/1 · `[1216, 1232)` | NIXL | [M05](#lmcache-object-m05) |
| 75 | `[1200, 1216)` | `[4004, 659, 64558, 17716, 374, 16994, 1526, 4396, 21448, 315, 279, 14135, 8674, 311, 279, 7015]` | 76/1 · `[1216, 1232)` | GPU prefix | 77/1 · `[1232, 1248)` | NIXL | [M05](#lmcache-object-m05) |
| 76 | `[1216, 1232)` | `[1154, 323, 374, 26237, 16307, 1172, 518, 3654, 3039, 315, 279, 1899, 323, 608, 476, 553]` | 77/1 · `[1232, 1248)` | GPU prefix | 78/1 · `[1248, 1264)` | NIXL | [M05](#lmcache-object-m05) |
| 77 | `[1232, 1248)` | `[16307, 518, 264, 14496, 429, 5128, 279, 7015, 705, 389, 279, 3832, 14135, 10277, 659, 576]` | 78/1 · `[1248, 1264)` | GPU prefix | 79/1 · `[1264, 1280)` | NIXL | [M05](#lmcache-object-m05) |
| 78 | `[1248, 1264)` | `[4004, 646, 11167, 476, 63817, 504, 279, 3832, 323, 1969, 387, 15516, 6509, 979, 4633, 14951]` | 79/1 · `[1264, 1280)` | GPU prefix | 80/1 · `[1280, 1296)` | NIXL | [M05](#lmcache-object-m05) |
| 79 | `[1264, 1280)` | `[659, 6553, 481, 311, 481, 3720, 23751, 5711, 2924, 8353, 990, 323, 12876, 659, 20738, 198]` | 80/1 · `[1280, 1296)` | GPU prefix | 81/1 · `[1296, 1312)` | NIXL | [M05](#lmcache-object-m05) |
| 80 | `[1280, 1296)` | `[24157, 7524, 921, 58, 7524, 220, 21, 921, 9865, 7101, 23751, 198, 35, 23822, 3000, 389]` | 81/1 · `[1296, 1312)` | GPU prefix | 82/1 · `[1312, 1328)` | NIXL | [M06](#lmcache-object-m06) |
| 81 | `[1296, 1312)` | `[279, 7602, 1154, 16403, 7471, 45530, 24248, 659, 4220, 2924, 82657, 39699, 5071, 1154, 16594, 24603]` | 82/1 · `[1312, 1328)` | GPU prefix | 83/1 · `[1328, 1344)` | NIXL | [M06](#lmcache-object-m06) |
| 82 | `[1312, 1328)` | `[5071, 323, 42924, 2268, 7489, 5071, 2138, 3847, 311, 2711, 1105, 369, 24248, 315, 14135, 3118]` | 83/1 · `[1328, 1344)` | GPU prefix | 84/1 · `[1344, 1360)` | NIXL | [M06](#lmcache-object-m06) |
| 83 | `[1328, 1344)` | `[389, 1196, 481, 5189, 12890, 16448, 24157, 7524, 921, 14582, 25, 2308, 11, 358, 8791, 7249]` | 84/1 · `[1344, 1360)` | GPU prefix | 85/1 · `[1360, 1376)` | NIXL | [M06](#lmcache-object-m06) |
| 84 | `[1344, 1360)` | `[304, 279, 3720, 624, 16141, 25, 6553, 481, 311, 481, 3720, 45530, 23751, 374, 279, 1947]` | 85/2 · `[1360, 1376)` | GPU prefix | 86/1 · `[1376, 1392)` | NIXL | [M06](#lmcache-object-m06) |
| 85 | `[1360, 1376)` | `[315, 10300, 287, 14135, 304, 279, 3720, 11, 1393, 1667, 2441, 14135, 438, 264, 6548, 5339]` | 86/1 · `[1376, 1392)` | GPU prefix | 87/1 · `[1392, 1408)` | NIXL | [M06](#lmcache-object-m06) |
| 86 | `[1376, 1392)` | `[382, 92602, 510, 58, 7524, 220, 16, 921, 9865, 7101, 23751, 198, 9865, 7101, 23751, 374]` | 87/1 · `[1392, 1408)` | GPU prefix | 88/1 · `[1408, 1424)` | NIXL | [M06](#lmcache-object-m06) |
| 87 | `[1392, 1408)` | `[279, 1160, 315, 4633, 5335, 315, 14135, 1154, 2987, 304, 10971, 1154, 476, 389, 279, 4910]` | 88/1 · `[1408, 1424)` | GPU prefix | 89/1 · `[1424, 1440)` | NIXL | [M06](#lmcache-object-m06) |
| 88 | `[1408, 1424)` | `[659, 20768, 315, 45530, 23751, 2924, 3720, 481, 311, 481, 3720, 1154, 4910, 481, 311, 481]` | 89/1 · `[1424, 1440)` | GPU prefix | 90/1 · `[1440, 1456)` | NIXL | [M06](#lmcache-object-m06) |
| 89 | `[1424, 1440)` | `[3720, 1154, 4910, 481, 1099, 1154, 323, 8699, 23751, 659, 26960, 45530, 23751, 1154, 5310, 3720]` | 90/1 · `[1440, 1456)` | GPU prefix | 91/1 · `[1456, 1472)` | NIXL | [M06](#lmcache-object-m06) |
| 90 | `[1440, 1456)` | `[481, 311, 481, 3720, 1154, 7460, 5107, 7361, 1154, 438, 279, 6548, 323, 2169, 14135, 3545]` | 91/1 · `[1456, 1472)` | GPU prefix | 92/1 · `[1472, 1488)` | NIXL | [M06](#lmcache-object-m06) |
| 91 | `[1456, 1472)` | `[11466, 518, 74057, 315, 916, 18294, 220, 16, 1154, 1393, 1212, 23193, 311, 1550, 479, 16448]` | 92/1 · `[1472, 1488)` | GPU prefix | 93/1 · `[1488, 1504)` | NIXL | [M06](#lmcache-object-m06) |
| 92 | `[1472, 1488)` | `[24157, 7524, 921, 58, 7524, 220, 17, 921, 9865, 7101, 23751, 198, 641, 4910, 481, 1099]` | 93/1 · `[1488, 1504)` | GPU prefix | 94/1 · `[1504, 1520)` | NIXL | [M06](#lmcache-object-m06) |
| 93 | `[1488, 1504)` | `[23751, 1154, 7249, 315, 52635, 14135, 525, 4429, 553, 47177, 389, 279, 4910, 659, 16505, 646]` | 94/1 · `[1504, 1520)` | GPU prefix | 95/1 · `[1520, 1536)` | NIXL | [M06](#lmcache-object-m06) |
| 94 | `[1504, 1520)` | `[387, 315, 14135, 54267, 21867, 1154, 73464, 1154, 323, 14135, 3565, 659, 576, 28767, 702, 2480]` | 95/1 · `[1520, 1536)` | GPU prefix | 96/1 · `[1536, 1552)` | NIXL | [M06](#lmcache-object-m06) |
| 95 | `[1520, 1536)` | `[2524, 916, 17716, 1154, 14135, 21448, 1154, 6249, 25941, 1154, 323, 4004, 659, 758, 12536, 4405]` | 96/1 · `[1536, 1552)` | GPU prefix | 97/1 · `[1552, 1568)` | NIXL | [M06](#lmcache-object-m06) |
| 96 | `[1536, 1552)` | `[1008, 14878, 1741, 438, 279, 17708, 476, 1008, 14135, 374, 1753, 8661, 311, 22054, 304, 4910]` | 97/1 · `[1552, 1568)` | GPU prefix | 98/1 · `[1568, 1584)` | NIXL | [M07](#lmcache-object-m07) |
| 97 | `[1552, 1568)` | `[481, 1099, 23751, 1091, 304, 1008, 7586, 315, 40784, 23751, 16448, 24157, 7524, 921, 58, 7524]` | 98/1 · `[1568, 1584)` | GPU prefix | 99/1 · `[1584, 1600)` | NIXL | [M07](#lmcache-object-m07) |
| 98 | `[1568, 1584)` | `[220, 18, 921, 9865, 7101, 23751, 198, 641, 4910, 481, 311, 481, 3720, 23751, 1154, 7249]` | 99/1 · `[1584, 1600)` | GPU prefix | 100/1 · `[1600, 1616)` | NIXL | [M07](#lmcache-object-m07) |
| 99 | `[1584, 1600)` | `[315, 14135, 304, 10971, 525, 4429, 448, 279, 28767, 389, 279, 4910, 659, 1096, 943, 315]` | 100/1 · `[1600, 1616)` | GPU prefix | 101/1 · `[1616, 1632)` | NIXL | [M07](#lmcache-object-m07) |
| 100 | `[1600, 1616)` | `[23751, 374, 4185, 518, 3720, 59456, 476, 45063, 659, 43393, 1154, 264, 1293, 5244, 69064, 18342]` | 101/1 · `[1616, 1632)` | GPU prefix | 102/1 · `[1632, 1648)` | NIXL | [M07](#lmcache-object-m07) |
| 101 | `[1616, 1632)` | `[374, 5871, 4152, 311, 279, 7046, 6010, 1948, 279, 28767, 323, 279, 2169, 14135, 659, 31844]` | 102/1 · `[1632, 1648)` | GPU prefix | 103/1 · `[1648, 1664)` | NIXL | [M07](#lmcache-object-m07) |
| 102 | `[1632, 1648)` | `[448, 4910, 481, 1099, 23751, 1154, 419, 374, 279, 1429, 5411, 1352, 315, 45530, 23751, 16448]` | 103/1 · `[1648, 1664)` | GPU prefix | 104/1 · `[1664, 1680)` | NIXL | [M07](#lmcache-object-m07) |
| 103 | `[1648, 1664)` | `[24157, 7524, 921, 58, 7524, 220, 19, 921, 9865, 7101, 23751, 198, 24703, 23751, 374, 264]` | 104/1 · `[1664, 1680)` | GPU prefix | 105/1 · `[1680, 1696)` | NIXL | [M07](#lmcache-object-m07) |
| 104 | `[1664, 1680)` | `[22990, 389, 40784, 3720, 481, 311, 481, 3720, 23751, 1154, 47901, 279, 6249, 374, 21810, 8630]` | 105/1 · `[1680, 1696)` | GPU prefix | 106/1 · `[1696, 1712)` | NIXL | [M07](#lmcache-object-m07) |
| 105 | `[1680, 1696)` | `[279, 9250, 14135, 5944, 3123, 504, 279, 28767, 323, 374, 22119, 38429, 1667, 264, 22148, 476]` | 106/1 · `[1696, 1712)` | GPU prefix | 107/1 · `[1712, 1728)` | NIXL | [M07](#lmcache-object-m07) |
| 106 | `[1696, 1712)` | `[19734, 47956, 4879, 659, 576, 2168, 702, 311, 387, 23415, 979, 279, 14135, 374, 389, 279]` | 107/1 · `[1712, 1728)` | GPU prefix | 108/1 · `[1728, 1744)` | NIXL | [M07](#lmcache-object-m07) |
| 107 | `[1712, 1728)` | `[4910, 1154, 1576, 279, 28767, 702, 902, 2615, 311, 279, 6249, 1393, 279, 14135, 374, 304]` | 108/1 · `[1728, 1744)` | GPU prefix | 109/1 · `[1744, 1760)` | NIXL | [M07](#lmcache-object-m07) |
| 108 | `[1728, 1744)` | `[10971, 659, 23309, 86781, 287, 323, 9115, 1969, 387, 2814, 1393, 6243, 705, 279, 6249, 311]` | 109/1 · `[1744, 1760)` | GPU prefix | 110/1 · `[1760, 1776)` | NIXL | [M07](#lmcache-object-m07) |
| 109 | `[1744, 1760)` | `[633, 279, 12685, 6552, 659, 20738, 23751, 374, 279, 3245, 4185, 943, 315, 45530, 23751, 16448]` | 110/1 · `[1760, 1776)` | GPU prefix | 111/1 · `[1776, 1792)` | NIXL | [M07](#lmcache-object-m07) |
| 110 | `[1760, 1776)` | `[24157, 7524, 921, 58, 7524, 220, 20, 921, 9865, 7101, 23751, 198, 25693, 481, 311, 481]` | 111/1 · `[1776, 1792)` | GPU prefix | 112/1 · `[1792, 1808)` | NIXL | [M07](#lmcache-object-m07) |
| 111 | `[1776, 1792)` | `[3720, 23751, 374, 279, 1947, 315, 10300, 287, 14135, 304, 279, 3720, 1154, 1393, 1667, 2441]` | 112/1 · `[1792, 1808)` | GPU prefix | 113/1 · `[1808, 1824)` | NIXL | [M07](#lmcache-object-m07) |
| 112 | `[1792, 1808)` | `[14135, 438, 264, 6548, 5339, 659, 576, 3832, 14135, 374, 56203, 1393, 2176, 14135, 525, 304]` | 113/1 · `[1808, 1824)` | GPU prefix | 114/1 · `[1824, 1840)` | NIXL | [M08](#lmcache-object-m08) |
| 113 | `[1808, 1824)` | `[10971, 659, 1096, 6147, 279, 28767, 311, 2309, 279, 3832, 304, 3151, 10468, 323, 25941, 311]` | 114/1 · `[1824, 1840)` | GPU prefix | 115/1 · `[1840, 1856)` | NIXL | [M08](#lmcache-object-m08) |
| 114 | `[1824, 1840)` | `[633, 279, 1429, 34846, 6552, 659, 4329, 2513, 429, 1969, 387, 6509, 311, 11075, 1850, 3059]` | 115/1 · `[1840, 1856)` | GPU prefix | 116/1 · `[1856, 1872)` | NIXL | [M08](#lmcache-object-m08) |
| 115 | `[1840, 1856)` | `[525, 17716, 323, 4004, 659, 64558, 17716, 374, 16994, 1526, 4396, 21448, 315, 279, 14135, 8674]` | 116/1 · `[1856, 1872)` | GPU prefix | 117/1 · `[1872, 1888)` | NIXL | [M08](#lmcache-object-m08) |
| 116 | `[1856, 1872)` | `[311, 279, 7015, 1154, 323, 374, 26237, 16307, 1172, 518, 3654, 3039, 315, 279, 1899, 323]` | 117/1 · `[1872, 1888)` | GPU prefix | 118/1 · `[1888, 1904)` | NIXL | [M08](#lmcache-object-m08) |
| 117 | `[1872, 1888)` | `[608, 476, 553, 16307, 518, 264, 14496, 429, 5128, 279, 7015, 705, 389, 279, 3832, 14135]` | 118/1 · `[1888, 1904)` | GPU prefix | 119/1 · `[1904, 1920)` | NIXL | [M08](#lmcache-object-m08) |
| 118 | `[1888, 1904)` | `[10277, 659, 576, 4004, 646, 11167, 476, 63817, 504, 279, 3832, 323, 1969, 387, 15516, 6509]` | 119/1 · `[1904, 1920)` | GPU prefix | 120/1 · `[1920, 1936)` | NIXL | [M08](#lmcache-object-m08) |
| 119 | `[1904, 1920)` | `[979, 4633, 14951, 659, 6553, 481, 311, 481, 3720, 23751, 5711, 2924, 8353, 990, 323, 12876]` | 120/1 · `[1920, 1936)` | GPU prefix | 121/1 · `[1936, 1952)` | NIXL | [M08](#lmcache-object-m08) |
| 120 | `[1920, 1936)` | `[659, 20738, 198, 24157, 7524, 921, 58, 7524, 220, 21, 921, 9865, 7101, 23751, 198, 1986]` | 121/1 · `[1936, 1952)` | GPU prefix | 122/1 · `[1952, 1968)` | NIXL | [M08](#lmcache-object-m08) |
| 121 | `[1936, 1952)` | `[4549, 3880, 5107, 51846, 369, 22901, 659, 5209, 1492, 7269, 419, 4549, 553, 7842, 51846, 311]` | 122/1 · `[1952, 1968)` | GPU prefix | 123/1 · `[1968, 1984)` | NIXL | [M08](#lmcache-object-m08) |
| 122 | `[1952, 1968)` | `[14720, 8173, 659, 61043, 53392, 3684, 1231, 387, 28891, 323, 6963, 659, 320, 6122, 220, 17]` | 123/1 · `[1968, 1984)` | GPU prefix | 124/1 · `[1984, 2000)` | NIXL | [M08](#lmcache-object-m08) |
| 123 | `[1968, 1984)` | `[15, 15, 24, 873, 320, 14934, 1246, 323, 979, 311, 4057, 419, 3811, 1943, 873, 6553]` | 124/1 · `[1984, 2000)` | GPU prefix | 125/1 · `[2000, 2016)` | NIXL | [M08](#lmcache-object-m08) |
| 124 | `[1984, 2000)` | `[198, 24157, 7524, 921, 14582, 25, 2055, 1558, 429, 3076, 17708, 315, 279, 2086, 14135, 1083]` | 125/1 · `[2000, 2016)` | GPU prefix | 126/1 · `[2016, 2032)` | NIXL | [M08](#lmcache-object-m08) |
| 125 | `[2000, 2016)` | `[14056, 438, 264, 28767, 5267, 16141, 25, 358, 1079, 14589, 358, 1513, 944, 614, 894, 3151]` | 126/2 · `[2016, 2032)` | GPU write 102.562 ms | 127/1 · `[2032, 2048)` | NIXL | [M08](#lmcache-object-m08) |
| 126 | `[2016, 2032)` | `[6540, 911, 879, 14056, 438, 264, 28767, 304, 3720, 4686, 37535, 45530, 23751, 13, 4710, 92602]` | 127/1 · `[2032, 2048)` | GPU write 102.645 ms | 128/1 · `[2048, 2064)` | NIXL | [M08](#lmcache-object-m08) |
| 127 | `[2032, 2048)` | `[510, 58, 7524, 220, 16, 921, 9865, 7101, 23751, 198, 641, 4910, 481, 311, 481, 3720]` | 128/1 · `[2048, 2064)` | GPU write 102.679 ms | 129/1 · `[2064, 2080)` | NIXL | [M08](#lmcache-object-m08) |
| 128 | `[2048, 2064)` | `[23751, 1154, 7249, 315, 14135, 304, 10971, 525, 4429, 448, 279, 28767, 389, 279, 4910, 659]` | 129/1 · `[2064, 2080)` | GPU write 102.714 ms | 130/1 · `[2080, 2096)` | NIXL | [M09](#lmcache-object-m09) |
| 129 | `[2064, 2080)` | `[1096, 943, 315, 23751, 374, 4185, 518, 3720, 59456, 476, 45063, 659, 43393, 1154, 264, 1293]` | 130/1 · `[2080, 2096)` | GPU write 102.743 ms | 131/1 · `[2096, 2112)` | NIXL | [M09](#lmcache-object-m09) |
| 130 | `[2080, 2096)` | `[5244, 69064, 18342, 374, 5871, 4152, 311, 279, 7046, 6010, 1948, 279, 28767, 323, 279, 2169]` | 131/1 · `[2096, 2112)` | GPU write 102.769 ms | 132/1 · `[2112, 2128)` | NIXL | [M09](#lmcache-object-m09) |
| 131 | `[2096, 2112)` | `[14135, 659, 31844, 448, 4910, 481, 1099, 23751, 1154, 419, 374, 279, 1429, 5411, 1352, 315]` | 132/1 · `[2112, 2128)` | GPU write 102.794 ms | 133/1 · `[2128, 2144)` | NIXL | [M09](#lmcache-object-m09) |
| 132 | `[2112, 2128)` | `[45530, 23751, 16448, 24157, 7524, 921, 58, 7524, 220, 17, 921, 9865, 7101, 23751, 198, 9865]` | 133/1 · `[2128, 2144)` | GPU write 102.830 ms | 134/1 · `[2144, 2160)` | NIXL | [M09](#lmcache-object-m09) |
| 133 | `[2128, 2144)` | `[7101, 23751, 374, 279, 1160, 315, 4633, 5335, 315, 14135, 1154, 2987, 304, 10971, 1154, 476]` | 134/1 · `[2144, 2160)` | GPU write 102.855 ms | 135/1 · `[2160, 2176)` | NIXL | [M09](#lmcache-object-m09) |
| 134 | `[2144, 2160)` | `[389, 279, 4910, 659, 20768, 315, 45530, 23751, 2924, 3720, 481, 311, 481, 3720, 1154, 4910]` | 135/1 · `[2160, 2176)` | GPU write 102.879 ms | 136/1 · `[2176, 2192)` | NIXL | [M09](#lmcache-object-m09) |
| 135 | `[2160, 2176)` | `[481, 311, 481, 3720, 1154, 4910, 481, 1099, 1154, 323, 8699, 23751, 659, 26960, 45530, 23751]` | 136/1 · `[2176, 2192)` | GPU write 102.903 ms | 137/1 · `[2192, 2208)` | NIXL | [M09](#lmcache-object-m09) |
| 136 | `[2176, 2192)` | `[1154, 5310, 3720, 481, 311, 481, 3720, 1154, 7460, 5107, 7361, 1154, 438, 279, 6548, 323]` | 137/1 · `[2192, 2208)` | GPU write 102.928 ms | 138/1 · `[2208, 2224)` | NIXL | [M09](#lmcache-object-m09) |
| 137 | `[2192, 2208)` | `[2169, 14135, 3545, 11466, 518, 74057, 315, 916, 18294, 220, 16, 1154, 1393, 1212, 23193, 311]` | 138/1 · `[2208, 2224)` | GPU write 102.951 ms | 139/1 · `[2224, 2240)` | NIXL | [M09](#lmcache-object-m09) |
| 138 | `[2208, 2224)` | `[1550, 479, 16448, 24157, 7524, 921, 58, 7524, 220, 18, 921, 9865, 7101, 23751, 198, 24703]` | 139/1 · `[2224, 2240)` | GPU write 102.975 ms | 140/1 · `[2240, 2256)` | NIXL | [M09](#lmcache-object-m09) |
| 139 | `[2224, 2240)` | `[23751, 374, 264, 22990, 389, 40784, 3720, 481, 311, 481, 3720, 23751, 1154, 47901, 279, 6249]` | 140/1 · `[2240, 2256)` | GPU write 102.998 ms | 141/1 · `[2256, 2272)` | NIXL | [M09](#lmcache-object-m09) |
| 140 | `[2240, 2256)` | `[374, 21810, 8630, 279, 9250, 14135, 5944, 3123, 504, 279, 28767, 323, 374, 22119, 38429, 1667]` | 141/1 · `[2256, 2272)` | GPU write 103.022 ms | 142/1 · `[2272, 2288)` | NIXL | [M09](#lmcache-object-m09) |
| 141 | `[2256, 2272)` | `[264, 22148, 476, 19734, 47956, 4879, 659, 576, 2168, 702, 311, 387, 23415, 979, 279, 14135]` | 142/1 · `[2272, 2288)` | GPU write 103.046 ms | 143/1 · `[2288, 2304)` | NIXL | [M09](#lmcache-object-m09) |
| 142 | `[2272, 2288)` | `[374, 389, 279, 4910, 1154, 1576, 279, 28767, 702, 902, 2615, 311, 279, 6249, 1393, 279]` | 143/1 · `[2288, 2304)` | GPU write 103.070 ms | 144/1 · `[2304, 2320)` | NIXL | [M09](#lmcache-object-m09) |
| 143 | `[2288, 2304)` | `[14135, 374, 304, 10971, 659, 23309, 86781, 287, 323, 9115, 1969, 387, 2814, 1393, 6243, 705]` | 144/1 · `[2304, 2320)` | GPU write 103.094 ms | 145/1 · `[2320, 2336)` | NIXL | [M09](#lmcache-object-m09) |
| 144 | `[2304, 2320)` | `[279, 6249, 311, 633, 279, 12685, 6552, 659, 20738, 23751, 374, 279, 3245, 4185, 943, 315]` | 145/1 · `[2320, 2336)` | GPU write 103.119 ms | 146/1 · `[2336, 2352)` | NIXL | [M10](#lmcache-object-m10) |
| 145 | `[2320, 2336)` | `[45530, 23751, 16448, 24157, 7524, 921, 58, 7524, 220, 19, 921, 9865, 7101, 23751, 198, 25693]` | 146/1 · `[2336, 2352)` | GPU write 103.143 ms | 147/1 · `[2352, 2368)` | NIXL | [M10](#lmcache-object-m10) |
| 146 | `[2336, 2352)` | `[481, 311, 481, 3720, 23751, 374, 279, 1947, 315, 10300, 287, 14135, 304, 279, 3720, 1154]` | 147/1 · `[2352, 2368)` | GPU write 103.167 ms | 148/1 · `[2368, 2384)` | NIXL | [M10](#lmcache-object-m10) |
| 147 | `[2352, 2368)` | `[1393, 1667, 2441, 14135, 438, 264, 6548, 5339, 659, 576, 3832, 14135, 374, 56203, 1393, 2176]` | 148/1 · `[2368, 2384)` | GPU write 103.195 ms | 149/1 · `[2384, 2400)` | NIXL | [M10](#lmcache-object-m10) |
| 148 | `[2368, 2384)` | `[14135, 525, 304, 10971, 659, 1096, 6147, 279, 28767, 311, 2309, 279, 3832, 304, 3151, 10468]` | 149/1 · `[2384, 2400)` | GPU write 103.218 ms | 150/1 · `[2400, 2416)` | NIXL | [M10](#lmcache-object-m10) |
| 149 | `[2384, 2400)` | `[323, 25941, 311, 633, 279, 1429, 34846, 6552, 659, 4329, 2513, 429, 1969, 387, 6509, 311]` | 150/1 · `[2400, 2416)` | GPU write 103.242 ms | 151/1 · `[2416, 2432)` | NIXL | [M10](#lmcache-object-m10) |
| 150 | `[2400, 2416)` | `[11075, 1850, 3059, 525, 17716, 323, 4004, 659, 64558, 17716, 374, 16994, 1526, 4396, 21448, 315]` | 151/1 · `[2416, 2432)` | GPU write 103.267 ms | 152/1 · `[2432, 2448)` | NIXL | [M10](#lmcache-object-m10) |
| 151 | `[2416, 2432)` | `[279, 14135, 8674, 311, 279, 7015, 1154, 323, 374, 26237, 16307, 1172, 518, 3654, 3039, 315]` | 152/1 · `[2432, 2448)` | GPU write 103.291 ms | 153/1 · `[2448, 2464)` | NIXL | [M10](#lmcache-object-m10) |
| 152 | `[2432, 2448)` | `[279, 1899, 323, 608, 476, 553, 16307, 518, 264, 14496, 429, 5128, 279, 7015, 705, 389]` | 153/1 · `[2448, 2464)` | GPU write 103.316 ms | 154/1 · `[2464, 2480)` | NIXL | [M10](#lmcache-object-m10) |
| 153 | `[2448, 2464)` | `[279, 3832, 14135, 10277, 659, 576, 4004, 646, 11167, 476, 63817, 504, 279, 3832, 323, 1969]` | 154/1 · `[2464, 2480)` | GPU write 103.340 ms | 155/1 · `[2480, 2496)` | NIXL | [M10](#lmcache-object-m10) |
| 154 | `[2464, 2480)` | `[387, 15516, 6509, 979, 4633, 14951, 659, 6553, 481, 311, 481, 3720, 23751, 5711, 2924, 8353]` | 155/1 · `[2480, 2496)` | GPU write 103.364 ms | 156/1 · `[2496, 2512)` | NIXL | [M10](#lmcache-object-m10) |
| 155 | `[2480, 2496)` | `[990, 323, 12876, 659, 20738, 198, 24157, 7524, 921, 58, 7524, 220, 20, 921, 9865, 7101]` | 156/1 · `[2496, 2512)` | GPU write 103.387 ms | 157/1 · `[2512, 2528)` | NIXL | [M10](#lmcache-object-m10) |
| 156 | `[2496, 2512)` | `[23751, 198, 641, 4910, 481, 1099, 23751, 1154, 7249, 315, 52635, 14135, 525, 4429, 553, 47177]` | 157/1 · `[2512, 2528)` | GPU write 103.411 ms | 158/1 · `[2528, 2544)` | NIXL | [M10](#lmcache-object-m10) |
| 157 | `[2512, 2528)` | `[389, 279, 4910, 659, 16505, 646, 387, 315, 14135, 54267, 21867, 1154, 73464, 1154, 323, 14135]` | 158/1 · `[2528, 2544)` | GPU write 103.434 ms | 159/1 · `[2544, 2560)` | NIXL | [M10](#lmcache-object-m10) |
| 158 | `[2528, 2544)` | `[3565, 659, 576, 28767, 702, 2480, 2524, 916, 17716, 1154, 14135, 21448, 1154, 6249, 25941, 1154]` | 159/1 · `[2544, 2560)` | GPU write 103.458 ms | 160/1 · `[2560, 2576)` | NIXL | [M10](#lmcache-object-m10) |
| 159 | `[2544, 2560)` | `[323, 4004, 659, 758, 12536, 4405, 1008, 14878, 1741, 438, 279, 17708, 476, 1008, 14135, 374]` | 160/1 · `[2560, 2576)` | GPU write 103.482 ms | 161/1 · `[2576, 2592)` | NIXL | [M10](#lmcache-object-m10) |
| 160 | `[2560, 2576)` | `[1753, 8661, 311, 22054, 304, 4910, 481, 1099, 23751, 1091, 304, 1008, 7586, 315, 40784, 23751]` | 161/1 · `[2576, 2592)` | GPU write 103.505 ms | 162/1 · `[2592, 2608)` | NIXL | — |
| 161 | `[2576, 2592)` | `[16448, 24157, 7524, 921, 58, 7524, 220, 21, 921, 9865, 7101, 23751, 198, 1986, 4549, 3880]` | 162/1 · `[2592, 2608)` | GPU write 103.533 ms | 163/1 · `[2608, 2624)` | NIXL | — |
| 162 | `[2592, 2608)` | `[5107, 51846, 369, 22901, 659, 5209, 1492, 7269, 419, 4549, 553, 7842, 51846, 311, 14720, 8173]` | 163/1 · `[2608, 2624)` | GPU write 103.557 ms | 164/1 · `[2624, 2640)` | NIXL | — |
| 163 | `[2608, 2624)` | `[659, 61043, 53392, 3684, 1231, 387, 28891, 323, 6963, 659, 320, 6122, 220, 17, 15, 15]` | 164/1 · `[2624, 2640)` | GPU write 103.581 ms | 165/1 · `[2640, 2656)` | NIXL | — |
| 164 | `[2624, 2640)` | `[24, 873, 320, 14934, 1246, 323, 979, 311, 4057, 419, 3811, 1943, 873, 6553, 198, 24157]` | 165/1 · `[2640, 2656)` | GPU write 103.605 ms | 166/1 · `[2656, 2672)` | NIXL | — |
| 165 | `[2640, 2656)` | `[7524, 921, 14582, 25, 2160, 3720, 4686, 37535, 281, 426, 5696, 803, 5000, 429, 4910, 4686]` | 166/1 · `[2656, 2672)` | GPU write 103.629 ms | 167/1 · `[2672, 2688)` | NIXL | — |
| 166 | `[2656, 2660)` | `[37535, 5267, 16141, 25]` | 167/1 · `[2672, 2676)` | GPU write 103.652 ms | 168/1 · `[2688, 2692)` | NIXL · final token written at 773.477 ms | — |

## LMCache copies and storage events

These events follow each `(server, object ID)` through the conversation. Negative times precede the selected turn. GPU copies list the source block IDs and generations in prompt order. A disk read records movement into CPU memory. The GPU source is shown in the block table.

### LMCache object M01

`lmcache` · prompt positions `[0, 256)` · logical blocks `0–15`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@50153990487b16bc1a2d83374d2e220c569d07c97bb84b96319abeabdf30479b@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| -2357.224 | lmcache | CPU placement · 37,748,736 B · store |
| -2356.167 | p0 | Turn 1 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `1/1, 2/1, 3/1, 4/1, 5/1, 6/1, 7/1, 8/1, 9/1, 10/1, 11/1, 12/1, 13/1, 14/1, 15/1, 16/1` |
| -2304.819 | lmcache | Disk write complete · 37,748,736 B |
| -2250.834 | lmcache | CPU release · 37,748,736 B · l1_remove |
| -1698.678 | lmcache | Disk read complete · 37,748,736 B |
| -1674.734 | lmcache | CPU placement · 37,748,736 B · prefetch |
| -1669.430 | lmcache | CPU release · 37,748,736 B · read_finished |
| -862.663 | lmcache | Disk read complete · 37,748,736 B |
| -768.321 | lmcache | CPU placement · 37,748,736 B · prefetch |
| -755.563 | lmcache | CPU release · 37,748,736 B · read_finished |

### LMCache object M02

`lmcache` · prompt positions `[256, 512)` · logical blocks `16–31`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@2336474730a8bc97ed45ce9df60c9706eba904599e049110497663c8a6fb9237@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| -2357.130 | lmcache | CPU placement · 37,748,736 B · store |
| -2356.167 | p0 | Turn 1 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `17/1, 18/1, 19/1, 20/1, 21/1, 22/1, 23/1, 24/1, 25/1, 26/1, 27/1, 28/1, 29/1, 30/1, 31/1, 32/1` |
| -2251.569 | lmcache | Disk write complete · 37,748,736 B |
| -2250.757 | lmcache | CPU release · 37,748,736 B · l1_remove |
| -1675.166 | lmcache | Disk read complete · 37,748,736 B |
| -1674.647 | lmcache | CPU placement · 37,748,736 B · prefetch |
| -1669.341 | lmcache | CPU release · 37,748,736 B · read_finished |
| -839.540 | lmcache | Disk read complete · 37,748,736 B |
| -767.831 | lmcache | CPU placement · 37,748,736 B · prefetch |
| -755.496 | lmcache | CPU release · 37,748,736 B · read_finished |

### LMCache object M03

`lmcache` · prompt positions `[512, 768)` · logical blocks `32–47`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@0c6ab3331945c15d51ce3d0e66b8a9dd605958d0e20d70a55372363ffb45c8a4@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| -1728.031 | lmcache | CPU placement · 37,748,736 B · store |
| -1727.024 | p0 | Turn 2 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `33/1, 34/1, 35/1, 36/1, 37/1, 38/1, 39/1, 40/1, 41/1, 42/1, 43/1, 44/2, 45/1, 46/1, 47/1, 48/1` |
| -1625.834 | lmcache | Disk write complete · 37,748,736 B |
| -1518.865 | lmcache | CPU release · 37,748,736 B · l1_remove |
| -815.759 | lmcache | Disk read complete · 37,748,736 B |
| -767.679 | lmcache | CPU placement · 37,748,736 B · prefetch |
| -755.447 | lmcache | CPU release · 37,748,736 B · read_finished |
| 145.785 | lmcache | Disk read complete · 37,748,736 B |
| 244.890 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 256.960 | lmcache | CPU release · 37,748,736 B · read_finished |

### LMCache object M04

`lmcache` · prompt positions `[768, 1024)` · logical blocks `48–63`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@5970387e4c08a6614c881070b9cb15e817ba0bf1412e107b83d2df71d9ffb73e@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| -1727.948 | lmcache | CPU placement · 37,748,736 B · store |
| -1727.024 | p0 | Turn 2 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `49/1, 50/1, 51/1, 52/1, 53/1, 54/1, 55/1, 56/1, 57/1, 58/1, 59/1, 60/1, 61/1, 62/1, 63/1, 64/1` |
| -1572.809 | lmcache | Disk write complete · 37,748,736 B |
| -1518.728 | lmcache | CPU release · 37,748,736 B · l1_remove |
| -792.199 | lmcache | Disk read complete · 37,748,736 B |
| -767.569 | lmcache | CPU placement · 37,748,736 B · prefetch |
| -755.405 | lmcache | CPU release · 37,748,736 B · read_finished |
| 170.290 | lmcache | Disk read complete · 37,748,736 B |
| 245.098 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 257.105 | lmcache | CPU release · 37,748,736 B · read_finished |

### LMCache object M05

`lmcache` · prompt positions `[1024, 1280)` · logical blocks `64–79`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@190ef730046889c38062793e73e8c2a09594b974ef87f88ca6dbc1978a516974@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| -1727.885 | lmcache | CPU placement · 37,748,736 B · store |
| -1727.024 | p0 | Turn 2 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `65/1, 66/1, 67/1, 68/1, 69/1, 70/1, 71/1, 72/1, 73/1, 74/1, 75/1, 76/1, 77/1, 78/1, 79/1, 80/1` |
| -1519.740 | lmcache | Disk write complete · 37,748,736 B |
| -1518.641 | lmcache | CPU release · 37,748,736 B · l1_remove |
| -768.782 | lmcache | Disk read complete · 37,748,736 B |
| -767.464 | lmcache | CPU placement · 37,748,736 B · prefetch |
| -755.366 | lmcache | CPU release · 37,748,736 B · read_finished |
| 194.835 | lmcache | Disk read complete · 37,748,736 B |
| 245.224 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 257.206 | lmcache | CPU release · 37,748,736 B · read_finished |

### LMCache object M06

`lmcache` · prompt positions `[1280, 1536)` · logical blocks `80–95`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@d263b5c26af3c6f37ebde65e454d9744b32e0bfae62fa59bfe5f5823ef00e572@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| -895.612 | lmcache | CPU placement · 37,748,736 B · store |
| -894.786 | p0 | Turn 3 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `81/1, 82/1, 83/1, 84/1, 85/2, 86/1, 87/1, 88/1, 89/1, 90/1, 91/1, 92/1, 93/1, 94/1, 95/1, 96/1` |
| -758.197 | lmcache | Disk write complete · 37,748,736 B |
| -691.851 | lmcache | CPU release · 37,748,736 B · l1_remove |
| 219.662 | lmcache | Disk read complete · 37,748,736 B |
| 245.317 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 257.309 | lmcache | CPU release · 37,748,736 B · read_finished |
| 1136.558 | lmcache | Disk read complete · 37,748,736 B |
| 1229.860 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 1243.733 | lmcache | CPU release · 37,748,736 B · read_finished |

### LMCache object M07

`lmcache` · prompt positions `[1536, 1792)` · logical blocks `96–111`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@cf52abc84ffaeb3ccce9c6949e80b98d662034f4c49a82701b3ce2fcd4135ce1@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| -895.463 | lmcache | CPU placement · 37,748,736 B · store |
| -894.786 | p0 | Turn 3 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `97/1, 98/1, 99/1, 100/1, 101/1, 102/1, 103/1, 104/1, 105/1, 106/1, 107/1, 108/1, 109/1, 110/1, 111/1, 112/1` |
| -692.615 | lmcache | Disk write complete · 37,748,736 B |
| -691.711 | lmcache | CPU release · 37,748,736 B · l1_remove |
| 244.211 | lmcache | Disk read complete · 37,748,736 B |
| 245.402 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 257.391 | lmcache | CPU release · 37,748,736 B · read_finished |
| 1159.714 | lmcache | Disk read complete · 37,748,736 B |
| 1230.022 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 1243.882 | lmcache | CPU release · 37,748,736 B · read_finished |

### LMCache object M08

`lmcache` · prompt positions `[1792, 2048)` · logical blocks `112–127`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@e35d02871e45f4b0049b8ae066840770a081e98a2237218666792a9f4983347c@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| 114.698 | lmcache | CPU placement · 37,748,736 B · store |
| 114.852 | p0 | Turn 4 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `113/1, 114/1, 115/1, 116/1, 117/1, 118/1, 119/1, 120/1, 121/1, 122/1, 123/1, 124/1, 125/1, 126/2, 127/1, 128/1` |
| 260.184 | lmcache | Disk write complete · 37,748,736 B |
| 378.595 | lmcache | CPU release · 37,748,736 B · l1_remove |
| 1182.479 | lmcache | Disk read complete · 37,748,736 B |
| 1230.131 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 1243.986 | lmcache | CPU release · 37,748,736 B · read_finished |

### LMCache object M09

`lmcache` · prompt positions `[2048, 2304)` · logical blocks `128–143`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@d10b3087706c09e8bdcda8958b5eeb87e7a8db75b987e45067712eac6448e65e@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| 114.852 | p0 | Turn 4 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `129/1, 130/1, 131/1, 132/1, 133/1, 134/1, 135/1, 136/1, 137/1, 138/1, 139/1, 140/1, 141/1, 142/1, 143/1, 144/1` |
| 115.112 | lmcache | CPU placement · 37,748,736 B · store |
| 326.192 | lmcache | Disk write complete · 37,748,736 B |
| 378.766 | lmcache | CPU release · 37,748,736 B · l1_remove |
| 1205.786 | lmcache | Disk read complete · 37,748,736 B |
| 1230.217 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 1244.075 | lmcache | CPU release · 37,748,736 B · read_finished |

### LMCache object M10

`lmcache` · prompt positions `[2304, 2560)` · logical blocks `144–159`.

`Qwen-SEP-Qwen3-4B-Instruct-2507@0x01000100@0@ea172edce462a856bb82b7d45348ad7d5c79373e5f5d232212a82746e865a077@@x1-eyJyZXZpc2lvbiI6ImNkYmVlNzVmMTdjMDFhN2NjNDJmOTU4ZGM2NTA5MDcxNzRhZjA1NTQifQ.data`

| Elapsed (ms) | Actor | Event |
| --- | --- | --- |
| 114.852 | p0 | Turn 4 GPU → LMCache · 37,748,736 B · pool `135444014760544` · block/gen `145/1, 146/1, 147/1, 148/1, 149/1, 150/1, 151/1, 152/1, 153/1, 154/1, 155/1, 156/1, 157/1, 158/1, 159/1, 160/1` |
| 115.168 | lmcache | CPU placement · 37,748,736 B · store |
| 377.896 | lmcache | Disk write complete · 37,748,736 B |
| 378.884 | lmcache | CPU release · 37,748,736 B · l1_remove |
| 1229.280 | lmcache | Disk read complete · 37,748,736 B |
| 1230.298 | lmcache | CPU placement · 37,748,736 B · prefetch |
| 1244.173 | lmcache | CPU release · 37,748,736 B · read_finished |
