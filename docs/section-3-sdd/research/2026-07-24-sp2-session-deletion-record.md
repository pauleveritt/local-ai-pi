# SP2 session transcripts — deletion record

**Date:** 2026-07-24
**Action:** the 46 raw session JSONL transcripts backing the SP2 baseline
reports were deleted to reclaim ~455 MB of local disk.

**Why it was safe.** Every SP2 baseline batch is formally withdrawn by the
[grading-path reboot](../../superpowers/plans/2026-07-24-grading-path-reboot.md):
they were graded by a model-authored oracle (doctrine D3) and, before that,
by an oracle that failed correct solutions. Their numbers are not citable and
their prose is discarded. Re-running under the rebuilt grading path produces
fresh transcripts.

**What was checked before deleting.** The nine sessions cited by *surviving*
reports — self-grade forensics (8) and the write-vs-edit guard experiment (1)
— were confirmed to be absent from this batch and present in
`docs/section-2-measurement/research/sessions/`. The replace-vs-extend 8/8
finding, the strongest surviving evidence, is unaffected.

**What was lost.** [`2026-07-24-sp2-deep-dive.md`](2026-07-24-sp2-deep-dive.md)
was derived by reading these transcripts. Its findings are extracted into
prose and into the roadmap backlog, but they can no longer be re-verified
against the source. Treat its claims as recorded, not reproducible.

**Note on why these were large.** Three transcripts exceeded 30 MB (62 MB,
42 MB, 31 MB) — subagent delegation runs. Full parent-session capture of a
delegating run is expensive; the reboot's distilled-artifact direction exists
partly for this reason.

## Inventory (filename · bytes · mtime)

```
00385cfdd165.jsonl	2791218	2026-07-24T10:04
03b60d2ee8b9.jsonl	5723250	2026-07-23T20:43
03fbeae3549d.jsonl	3202169	2026-07-23T19:11
0c4cb9e51290.jsonl	15400024	2026-07-23T21:04
0d1d54ee57ed.jsonl	3468862	2026-07-24T12:19
11c78d4956d1.jsonl	19378059	2026-07-24T08:14
182b7a12c4bc.jsonl	7805007	2026-07-23T17:51
1929617fa8dd.jsonl	8241004	2026-07-23T20:48
1d4fb2e033b0.jsonl	8472319	2026-07-24T08:31
27b6a8cb533a.jsonl	18470391	2026-07-23T19:08
29db2117ae60.jsonl	6511837	2026-07-24T10:45
2d6a552cfdcf.jsonl	32204049	2026-07-23T19:35
2f2cd6290a07.jsonl	8802564	2026-07-23T18:48
44a9f34c51a5.jsonl	1558097	2026-07-23T21:07
4e90a4ba4d35.jsonl	44315172	2026-07-24T12:04
59a7953f99c2.jsonl	8129088	2026-07-23T18:42
619222649d55.jsonl	540040	2026-07-23T17:28
63ad907b08e0.jsonl	3942864	2026-07-24T11:44
65a74c4b7498.jsonl	1380412	2026-07-23T21:25
6b5c3ef015db.jsonl	5012109	2026-07-23T17:33
8527dc8c3d4d.jsonl	4585040	2026-07-23T21:31
871d212410c7.jsonl	6784387	2026-07-24T12:10
9050ba1ed8fc.jsonl	5834725	2026-07-24T11:53
946bb4d17375.jsonl	10730699	2026-07-24T11:36
947ed30c636b.jsonl	19363982	2026-07-24T07:51
94b460ead812.jsonl	2634768	2026-07-24T10:49
9e7cddfeaed6.jsonl	8358037	2026-07-24T08:23
9fb6c2a64b64.jsonl	1726826	2026-07-24T08:26
a343ffb57fe8.jsonl	7171739	2026-07-24T11:16
a5ec168b8cee.jsonl	8199604	2026-07-24T10:53
aaac34559341.jsonl	4546299	2026-07-24T10:57
b017a8b1dc2b.jsonl	2831721	2026-07-23T21:28
b0d4b5647f6b.jsonl	9124846	2026-07-23T17:59
b206d889c1e8.jsonl	8006497	2026-07-24T08:40
b31afcf6dc58.jsonl	64978702	2026-07-23T20:02
bdf0e1816984.jsonl	6745968	2026-07-24T10:09
c2d816c525ac.jsonl	23605759	2026-07-23T21:22
c40312831cbf.jsonl	22386386	2026-07-24T08:53
c5c3aaef9664.jsonl	2999279	2026-07-23T18:58
c707f8c2d5f6.jsonl	10415400	2026-07-24T07:36
cd42f62601df.jsonl	1344421	2026-07-24T11:40
d1e8f551f274.jsonl	7659962	2026-07-24T12:16
e3f2039e3fd4.jsonl	4175289	2026-07-24T08:57
f4a48bb64868.jsonl	4256636	2026-07-24T11:49
fbb1228e0b31.jsonl	8982677	2026-07-23T18:55
fe16f77e461e.jsonl	14355806	2026-07-23T18:10
```
