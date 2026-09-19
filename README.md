# Monthly spending review — landing-page smoke test

A two-variant landing page testing whether one sentence earns an email from
Malaysians who pay across several bank accounts, cards and e-wallets.

**Nothing is built. Nothing is for sale.** The page says so on its face. Every
figure in the sample review is invented and labelled as invented.

## What is here

| Path | What it is |
|---|---|
| `src/build.py` | Generates the whole site. Edit this, not `docs/`. |
| `docs/` | Generated output, served by GitHub Pages. Do not hand-edit. |
| `docs/a/`, `docs/b/` | The two variants. Identical except headline and subhead. |
| `docs/review/` | The sample review, copied from its source. Anchor ids added, nothing else. |
| `analytics/read-ledger.md` | Every counter read we have made, and why that matters. |

Build with `python3 src/build.py`.

## The two variants

Both sell exactly one idea, so a difference in conversion is attributable to the
promise rather than to the page.

- **A — the insight angle.** "You track your spending. You still can't see where it's going."
- **B — the effort angle.** "A monthly spending review that doesn't ask you to log anything."

Traffic is split by source URL rather than by a JavaScript splitter. At this
volume that is simpler, and it cannot silently mis-bucket anyone.

## Measurement

Cookieless, no third-party analytics bundle, no fingerprinting. Each event is a
single image request to [hits.sh](https://hits.sh), a free no-account counter.
`sessionStorage` stops one visit counting twice.

| Counter | Fires when |
|---|---|
| `load` | every page load (plus a `<noscript>` image, so JS-off loads count) |
| `session` | once per browser session — the closest thing here to "visitors" |
| `form-seen` | once per session, when the signup block is 40% on screen |
| `submit` | a submit passes client-side validation |
| `q-1-2` … `q-7plus` | the account-count answer, so unqualified signups are separable |
| `submit-undelivered` / `submit-error` | the mail relay refused or the network failed |

No email address is ever sent to a counter.

### Two honest limits on these numbers

1. **Reading a counter increments it.** hits.sh returns the post-increment
   value, so every read we make inflates the total by exactly one. Reads are
   logged in `analytics/read-ledger.md` and subtracted before any number is
   reported. Report adjusted figures, never raw ones.
2. **The counters are public and writable by anyone** who views source. At this
   traffic volume that is an acceptable trade for RM0 and no account, but a
   number that looks too good should be treated as suspect, not as a result.

## Email capture

The form posts to [FormSubmit](https://formsubmit.co), which needs no account
and forwards straight to an inbox. There is no third-party database holding
addresses, which is the point: emails are a contact list, not research data.
They are never published, quoted, or shared between agents — only counts are
reported.

The inbox is activated and the page now posts to FormSubmit's **random
alias**, so the owner's email address is no longer in page source at all. It
was previously base64'd there — obfuscation, not secrecy. The alias is an
opaque routing token: it names no address and can be revoked at FormSubmit
without the owner changing their email.

The alias was verified against the live endpoint on 2026-09-19 with one
submission subject-lined `TEST - ignore`, which returned
`{"success":"true"}`. That test was sent by `curl` straight to FormSubmit, so
it touched **no** hits.sh counter — a GET cannot verify an alias (FormSubmit
answers identically for a valid and an invalid one), so a real POST was the
only check available.

## Rules this page does not bend

- **Never ask for a bank login, statement, screenshot or balance** — not on the
  page, not in the form, not in the follow-up email.
- **Every figure shown is labelled synthetic.**
- **No fabricated traction.** No invented user counts, no fake testimonials, no
  manufactured urgency. Beyond the honesty problem, fake social proof would
  corrupt the only measurement being run here.
- **No implied company.** The footer says what this is: one person in Malaysia.
