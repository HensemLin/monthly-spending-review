# Counter read ledger

hits.sh returns the **post-increment** value, so every read we make adds one to
the counter it reads. Any number reported from these counters must have the
reads below subtracted first.

> reported value = raw value − (reads of that counter listed here)

Log every read. A read that is not logged here becomes an inflated result later,
and there is no way to tell after the fact which hit was ours.

| Date (UTC) | Counter | Raw value returned | Reads by us, cumulative | Purpose |
|---|---|---:|---:|---|
| 2026-09-19 | `a/load` | 9 | 1 | Baseline before instrumentation check |
| 2026-09-19 | `a/session` | 9 | 1 | Baseline before instrumentation check |
| 2026-09-19 | `a/load` | 10 | 2 | Post-load check (run was inconclusive) |
| 2026-09-19 | `a/session` | 10 | 2 | Post-load check (run was inconclusive) |
| 2026-09-19 | `a/load` | 11 | 3 | Baseline for the verified instrumentation test |
| 2026-09-19 | `a/load` | 14 | 4 | Confirmed 2 headless page loads recorded as 2 |

## Pre-launch build traffic

Counters `a/load` and `a/session` reached **9** before any real visitor existed.
Those hits are our own headless-browser screenshots taken while building the
page, plus the reads above.

**Baseline to subtract when Phase B reporting starts:** record the raw value of
every counter immediately before the first real traffic is sent, and treat that
as zero. Do not report cumulative raw totals.
