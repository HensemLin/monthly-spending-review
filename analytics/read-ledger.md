# Counter baseline and read ledger

## The zero point

Every counter carries build-time noise: our own headless-browser screenshots,
the instrumentation tests, and the reads themselves. **The values below are the
zero point.** Subtract them from any raw value before reporting anything.

> reported = raw − baseline

Snapshot taken 2026-09-19, after the self-test harness was removed from the live
site and before any real visitor was sent to the page.

The table has since been adjusted **arithmetically, without re-reading**, to absorb
two final evidence screenshots (one per variant), each firing `load`, `session`
and `form-seen`. Adjusting by hand rather than re-reading avoids adding six more
read-hits just to account for two.

| Counter | Baseline (= zero) |
|---|---:|
| `a/load` | 17 |
| `a/session` | 15 |
| `a/form-seen` | 5 |
| `a/submit` | 4 |
| `a/q-1-2` | 1 |
| `a/q-3-4` | 4 |
| `a/q-5-6` | 1 |
| `a/q-7plus` | 1 |
| `a/submit-undelivered` | 2 |
| `a/submit-error` | 1 |
| `b/load` | 3 |
| `b/session` | 3 |
| `b/form-seen` | 5 |
| `b/submit` | 1 |
| `b/q-1-2` | 1 |
| `b/q-3-4` | 1 |
| `b/q-5-6` | 1 |
| `b/q-7plus` | 1 |
| `b/submit-undelivered` | 1 |
| `b/submit-error` | 1 |

### Platform counters added 2026-09-19 (after the HEN-39 narrow verdict)

The signup now asks which phone the visitor uses, and each answer increments its
own counter. Baseline is **0** for all six, and that zero is *verified rather
than assumed*: these counter paths did not exist before this change, and the
end-to-end test that exercises them (`src/selftest.py`) runs against a local
stub, so not one of the live counters was touched to prove they work.

| Counter | Baseline (= zero) |
|---|---:|
| `a/p-android` | 0 |
| `a/p-iphone` | 0 |
| `a/p-other` | 0 |
| `b/p-android` | 0 |
| `b/p-iphone` | 0 |
| `b/p-other` | 0 |

Why this split matters more than it looks: `p-iphone` rising is **not** a
nuisance metric. [HEN-42](/HEN/issues/HEN-42) established that notification
capture is structurally impossible on iOS, so an iPhone-heavy signup list means
the promise is attracting people the product cannot serve. That is a stop
signal wearing the costume of good conversion. Report qualified conversion as
`p-android / load`, and always report the iPhone share beside it.

Counter base URL: `https://hits.sh/hen49.jul7v2v.smoke/<variant>/<event>.svg`

Note the baselines are uneven between A and B. Variant A absorbed most of the
build and test traffic, B almost none. This is exactly why per-counter baselines
are recorded rather than one global number — subtracting a single figure from
both would hand variant B a false lead.

## Reading a counter increments it

hits.sh returns the **post-increment** value, so every read adds one to the
counter it reads. Two consequences:

1. Log every read below. An unlogged read becomes an inflated result later, and
   there is no way to tell afterwards which hit was ours.
2. Read as rarely as the reporting cadence allows. Do not poll.

| Date (UTC) | Counters read | Why |
|---|---|---|
| 2026-09-19 | `a/load`, `a/session` ×2 | Instrumentation check, inconclusive first run |
| 2026-09-19 | `a/load` ×2 | Confirmed 2 headless loads recorded as exactly 2 |
| 2026-09-19 | `a/submit`, `a/q-3-4`, `a/form-seen` ×2 each | End-to-end submit test |
| 2026-09-19 | `b/form-seen` ×2 | Scroll-to-form check |
| 2026-09-19 | all 20 counters ×1 | Baseline snapshot above |

**Every read after this line must be added to this table.**

## What these numbers cannot do

The counters are public and writable by anyone who views page source. At this
volume that is an acceptable trade for RM0 and no account, but it means a result
that looks too good is suspect rather than proven. `session` is a
`sessionStorage` approximation of a visitor, not a unique person: it will
double-count someone returning in a new session and under-count a household.
Treat every figure as directional, and always report the sample size beside the
rate, as the decision table in the smoke-test spec requires.
