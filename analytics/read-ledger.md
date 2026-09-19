# Counter baseline and read ledger

## The zero point

Every counter carries build-time noise: our own headless-browser screenshots,
the instrumentation tests, and the reads themselves. **The values below are the
zero point.** Subtract them from any raw value before reporting anything.

> reported = raw − baseline

**Superseded for eight counters.** The 2026-09-19 decision read at the bottom of
this file re-zeroed `load`, `session`, `form-seen` and `submit` on both
variants. Use the table there for those eight; the tables below still hold for
the rest.

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
| 2026-09-19 | `a/load`, `b/load`, `a/session`, `b/session`, `a/submit`, `b/submit`, `a/form-seen`, `b/form-seen` ×1 each | Decision read: HEN-44 asked whether changing the preview mid-flight would break comparability, which turns on whether any traffic had landed |

**Every read after this line must be added to this table.**

## 2026-09-19 decision read — and three hits nobody logged

Eight counters read once each, to answer one question: had anything landed that
a page change would invalidate? Answer: **nothing that can support a rate, but
not the clean zero the baseline above claims.**

Raw values are post-increment, so the pre-read figure is one less. Against the
baseline:

| Counter | Baseline | Raw pre-read | Unaccounted |
|---|---:|---:|---:|
| `a/load` | 17 | 19 | **+2** |
| `a/session` | 15 | 17 | **+2** |
| `a/form-seen` | 5 | 6 | **+1** |
| `a/submit` | 4 | 4 | 0 |
| `b/load` | 3 | 4 | **+1** |
| `b/session` | 3 | 4 | **+1** |
| `b/form-seen` | 5 | 5 | 0 |
| `b/submit` | 1 | 1 | 0 |

Three loads, three sessions, one form-seen, **zero submits.**

`session` rising in lockstep with `load` is the informative part: `session`
only fires from JavaScript that can reach `sessionStorage`, so these were three
separate JS-executing browser sessions, not a plain HTML crawler. Beyond that
they are **not attributable**. They could be a real person who found the URL, a
JS-rendering preview or scanner bot, or an agent's own headless render that was
never written down. We cannot tell, and saying which one it was would be
inventing a fact.

What is safe to say: **three sessions, one of which scrolled to the form, none
of which signed up.** That is not a conversion rate and should never be
reported as one — 0/3 tells you nothing at this size.

### The baseline has been reset to absorb them

The eight counters read above are re-zeroed to their **post-read** values. The
three unattributed sessions are therefore folded into the zero point rather
than counted as traffic. That is the conservative direction: it can only make a
future result look smaller, never larger.

| Counter | New baseline (= zero) | Was |
|---|---:|---:|
| `a/load` | 20 | 17 |
| `a/session` | 18 | 15 |
| `a/form-seen` | 7 | 5 |
| `a/submit` | 5 | 4 |
| `b/load` | 5 | 3 |
| `b/session` | 5 | 3 |
| `b/form-seen` | 6 | 5 |
| `b/submit` | 2 | 1 |

The twelve counters not read this round (`q-*`, `p-*`, `submit-undelivered`,
`submit-error`) keep the baselines given earlier in this file.

### The discipline failed once, so state the limit it leaves

Something incremented these counters without a line in this table. Whatever it
was, it means the ledger cannot prove the zero point was ever clean, only that
it is clean **from here**. Two consequences worth carrying forward:

1. Any future render of the live page — screenshot, smoke check, "just looking"
   — must be run against a **local stubbed copy**, the way `src/selftest.py`
   does it, or logged here. The park-comparison screenshots taken on
   2026-09-19 were run locally against a stub for exactly this reason and
   touched no live counter.
2. The first real reporting run should quote the **sample size next to the
   rate**, as the spec requires, and name this reset. A reader who is told
   "3 sessions were absorbed into the baseline" can judge the number. A reader
   handed a bare percentage cannot.

## What these numbers cannot do

The counters are public and writable by anyone who views page source. At this
volume that is an acceptable trade for RM0 and no account, but it means a result
that looks too good is suspect rather than proven. `session` is a
`sessionStorage` approximation of a visitor, not a unique person: it will
double-count someone returning in a new session and under-count a household.
Treat every figure as directional, and always report the sample size beside the
rate, as the decision table in the smoke-test spec requires.
