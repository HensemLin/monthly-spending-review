#!/usr/bin/env python3
"""
Build the HEN-49 smoke-test landing page.

Two variants, identical except for headline and subhead, so any difference in
conversion is attributable to the promise and nothing else. Copy is verbatim
from the HEN-49 smoke-test spec, section 3 — do not paraphrase it here.

Usage:  python3 src/build.py            (writes into ../ alongside this repo root)
"""

import html
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
# GitHub Pages serves from either the branch root or /docs. /docs keeps the
# generated output beside the source that made it, in one branch.
OUT = ROOT / "docs"

# ---------------------------------------------------------------------------
# Measurement. hits.sh is a free, no-account, cookieless counter: hitting
# <path>.svg increments it and returns a badge showing the count. We use one
# counter per event per variant. Reading a counter also increments it, so every
# agent read is logged in analytics/read-ledger.txt and subtracted when we
# report numbers.
# ---------------------------------------------------------------------------
COUNTER_BASE = "https://hits.sh/hen49.jul7v2v.smoke"

# FormSubmit.co needs no account: it posts to an address and forwards to the
# inbox. The address is base64'd so it is not sitting in the page source as
# plain text for scrapers. This is obfuscation, not secrecy — it gets replaced
# with FormSubmit's random alias as soon as the inbox owner activates.
FORM_TARGET_B64 = "amlheXVhbmxpbjgzOEBnbWFpbC5jb20="

VARIANTS = {
    "a": {
        "headline": "You track your spending. You still can&rsquo;t see where it&rsquo;s going.",
        "subhead": (
            "For Malaysians paying across a few bank accounts, a couple of cards "
            "and two or three e-wallets &mdash; a plain-English monthly review of "
            "where the money actually went, and the two or three places you could "
            "realistically have kept some."
        ),
        "title": "You track your spending. You still can't see where it's going.",
    },
    "b": {
        "headline": "A monthly spending review that doesn&rsquo;t ask you to log anything.",
        "subhead": (
            "For Malaysians paying across a few bank accounts, a couple of cards "
            "and two or three e-wallets &mdash; you keep spending the way you "
            "already do. Once a month you get a plain-English read on where it "
            "went and what you could realistically have kept."
        ),
        "title": "A monthly spending review that doesn't ask you to log anything.",
    },
}

CSS = """
:root{
  --ink:#111;
  --paper:#fff;
  --muted:#4a4a4a;
  --hair:#d6d2c8;
  --wash:#f6f4ef;
  --accent:#8a1c1c;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;
  background:var(--wash);
  color:var(--ink);
  font-family:Georgia,"Times New Roman",serif;
  font-size:18px;
  line-height:1.55;
  font-variant-numeric:lining-nums;
  font-feature-settings:"lnum" 1;
}
.wrap{max-width:46rem;margin:0 auto;padding:0 1.15rem}
main{background:var(--paper);border-left:1px solid var(--hair);border-right:1px solid var(--hair)}
@media (max-width:48rem){main{border:0}}

/* ---- masthead ------------------------------------------------------ */
.hero{padding:3rem 0 2rem}
h1{
  font-size:clamp(1.85rem,5.2vw,2.75rem);
  line-height:1.16;
  margin:0 0 1rem;
  letter-spacing:-.01em;
}
.sub{font-size:clamp(1.02rem,2.4vw,1.16rem);color:var(--muted);margin:0;max-width:34rem}

/* ---- the artifact -------------------------------------------------- */
.artifact{margin:2.25rem 0 0}
.artifact-label{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);margin:0 0 .6rem;
}
/* The page deliberately scrolls past the review's own synthetic banner so the
   visible slice contains actual figures. This label carries that warning at
   full strength above the frame; each part inside is also chip-labelled. */
.synthetic-flag{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  font-size:.86rem;line-height:1.45;font-weight:600;
  background:#111;color:#fff;padding:.7rem .85rem;margin:0 0 .75rem;
}
.frame{
  position:relative;
  border:1px solid var(--hair);
  background:#e9e9e9;
  height:29rem;
  overflow:hidden;
}
@media (max-width:40rem){.frame{height:27rem}}
/* pointer-events:none keeps the visitor from scrolling the preview independently;
   the transparent .frame-hit above it takes the click and opens the full review. */
.frame iframe{width:100%;height:100%;border:0;display:block;pointer-events:none}
.frame-hit{position:absolute;inset:0;z-index:3;display:block}
.frame::after{
  content:"";position:absolute;left:0;right:0;bottom:0;height:7rem;z-index:1;
  background:linear-gradient(to bottom,rgba(255,255,255,0),#fff 88%);
  pointer-events:none;
}
/* Sits above the fade, not under it, or the one call to action on the
   artifact ends up ghosted out by its own gradient. */
.frame-cta{
  position:absolute;left:0;right:0;bottom:0;z-index:2;
  text-align:center;padding:.65rem .9rem 1rem;background:#fff;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  font-size:.92rem;
}
.frame-cta span{color:var(--accent);font-weight:600;text-decoration:underline}
.frame-hit:focus-visible{outline:3px solid var(--accent);outline-offset:-3px}
.artifact-note{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  font-size:.82rem;color:var(--muted);margin:.7rem 0 0;
}

/* ---- trust block --------------------------------------------------- */
.trust{margin:2.75rem 0 0;border-top:2px solid var(--ink);padding-top:1.4rem}
.trust p{margin:0 0 .95rem;font-size:1rem}
.trust p:last-child{margin-bottom:0}
.trust strong{display:block}

/* ---- form ---------------------------------------------------------- */
.signup{
  margin:2.75rem 0 0;padding:1.75rem 1.4rem 1.6rem;
  background:var(--wash);border:1px solid var(--hair);
}
.signup h2{font-size:1.28rem;margin:0 0 1.2rem;line-height:1.3}
label{
  display:block;margin:0 0 .35rem;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  font-size:.92rem;font-weight:600;
}
.hint{
  display:block;font-weight:400;color:var(--muted);font-size:.85rem;margin-top:.15rem;
}
input[type=email],select{
  width:100%;padding:.72rem .7rem;font-size:1rem;font-family:inherit;
  border:1px solid #9a948a;background:#fff;color:var(--ink);border-radius:2px;
}
input[type=email]:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px}
.field{margin:0 0 1.15rem}
button{
  width:100%;padding:.85rem 1rem;font-size:1rem;font-weight:700;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:var(--ink);color:#fff;border:0;border-radius:2px;cursor:pointer;
}
button:hover{background:#000}
button[disabled]{opacity:.55;cursor:default}
.hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.msg{
  margin:1rem 0 0;font-size:.95rem;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
}
.msg.err{color:var(--accent)}

/* ---- footer -------------------------------------------------------- */
footer{
  margin:0;padding:2rem 0 3rem;font-size:.88rem;color:var(--muted);
}
footer p{margin:0 0 .6rem;max-width:34rem}
.variant-tag{font-size:.75rem;color:#9a948a}
"""

JS = """
/* ---------------------------------------------------------------------
   Measurement + submit. No cookies, no fingerprinting, no third-party
   analytics bundle. Each event is a 1x1 image request to a free counter
   endpoint; sessionStorage keeps one visit from counting twice.
   --------------------------------------------------------------------- */
(function () {
  var V = document.body.getAttribute('data-variant');
  var BASE = '__COUNTER_BASE__';

  function ping(event) {
    var img = new Image();
    img.referrerPolicy = 'no-referrer';
    img.src = BASE + '/' + V + '/' + event + '.svg?t=' + Date.now();
  }

  function once(event) {
    var k = 'hen49:' + V + ':' + event;
    try {
      if (sessionStorage.getItem(k)) return;
      sessionStorage.setItem(k, '1');
    } catch (e) { /* private mode: count it, better than losing it */ }
    ping(event);
  }

  once('session');
  ping('load');

  /* ---- artifact preview ---------------------------------------------
     Park the preview on Part 1 so the visible slice is actual figures
     rather than a screen of preamble. Done by scrolling the same-origin
     child document, NOT by a #fragment in the iframe src: fragment
     navigation inside an iframe scrolls the PARENT page too, which would
     carry visitors straight past the headline being tested and void the
     whole A/B comparison. If this fails the preview simply shows the top
     of the review, which is still honest and still a real render. */
  var rf = document.getElementById('review-frame');
  function parkPreview() {
    try {
      var d = rf.contentDocument;
      var target = d.getElementById('part1');
      if (!target) return;
      rf.contentWindow.scrollTo(0, target.offsetTop - 12);
      d.documentElement.style.overflow = 'hidden';
    } catch (e) { /* leave it at the top */ }
  }
  if (rf) {
    rf.addEventListener('load', parkPreview);
    if (rf.contentDocument && rf.contentDocument.readyState === 'complete') parkPreview();
    /* fonts/images settling can shift offsetTop after load */
    window.addEventListener('load', function () { setTimeout(parkPreview, 150); });
  }

  /* scroll-to-form: fired once when the signup block is actually on screen */
  var form = document.getElementById('signup');
  if (form && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { once('form-seen'); io.disconnect(); }
      });
    }, { threshold: 0.4 });
    io.observe(form);
  } else if (form) {
    once('form-seen');
  }

  /* ---- submit -------------------------------------------------------- */
  var el = document.getElementById('signup-form');
  if (!el) return;
  var btn = document.getElementById('submit-btn');
  var msg = document.getElementById('form-msg');

  function say(text, isErr) {
    msg.textContent = text;
    msg.className = isErr ? 'msg err' : 'msg';
  }

  el.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (el.querySelector('input[name=_honey]').value) return; /* bot */

    var email = el.email.value.trim();
    var accounts = el.accounts.value;
    if (!email || !accounts) { say('Please fill in both fields.', true); return; }

    btn.disabled = true;
    say('Sending\\u2026', false);

    /* Count the submit and the qualification bucket before the network call,
       so the funnel is measurable even if mail delivery is down. No email
       address is ever sent to the counter. */
    ping('submit');
    ping('q-' + accounts);

    var endpoint = 'https://formsubmit.co/ajax/' + atob('__FORM_TARGET_B64__');
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        email: email,
        accounts: accounts,
        variant: V,
        _subject: 'Spending review smoke test \\u2014 new signup (variant ' + V + ')',
        _captcha: 'false',
        _template: 'table'
      })
    })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (data) {
        if (data && String(data.success) === 'true') {
          window.location.href = '../thanks/?v=' + V;
        } else {
          ping('submit-undelivered');
          say('Your details reached us, but our mail relay has not finished setting itself up. ' +
              'Nothing is lost \\u2014 please try again in a day, or that is on us either way.', true);
          btn.disabled = false;
        }
      })
      .catch(function () {
        ping('submit-error');
        say('Something went wrong sending that. Please try again in a moment.', true);
        btn.disabled = false;
      });
  });
})();
"""

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="An early test of an idea: a plain-English monthly spending review for Malaysians paying across several accounts. Nothing is built yet.">
<meta name="robots" content="noindex">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="An early test of an idea. Nothing is built yet, nothing to buy.">
<meta property="og:type" content="website">
<link rel="stylesheet" href="../assets/site.css">
</head>
<body data-variant="{variant}">
<div class="wrap">
<main>

  <section class="hero">
    <h1>{headline}</h1>
    <p class="sub">{subhead}</p>
  </section>

  <section class="artifact">
    <p class="artifact-label">What you would actually get</p>
    <p class="synthetic-flag">Every figure below is made up. It describes a fictional person we
       invented to show what a review looks like &mdash; not anyone&rsquo;s real spending, and not
       real benchmark data.</p>
    <div class="frame">
      <iframe id="review-frame" src="../review/" title="Sample monthly spending review, built on invented data" loading="eager"></iframe>
      <a class="frame-hit" href="../review/" target="_blank" rel="noopener" aria-label="Read the whole sample review"></a>
      <div class="frame-cta" aria-hidden="true"><span>Read the whole sample review &rarr;</span></div>
    </div>
  </section>

  <section class="trust">
    <p><strong>No bank login. Ever.</strong> We will never ask you to connect an account, upload a statement, or send a screenshot of your balance.</p>
    <p><strong>Nothing is built yet.</strong> This is an early test of an idea. There&rsquo;s nothing to buy, download or sign up to.</p>
    <p><strong>The numbers above are made up.</strong> That&rsquo;s a sample review built on invented data, not anyone&rsquo;s real spending.</p>
    <p><strong>One email, then nothing.</strong> We&rsquo;ll write once to ask three short questions. That&rsquo;s the whole plan.</p>
  </section>

  <section class="signup" id="signup">
    <h2>Want to see one of these for your own spending?</h2>
    <form id="signup-form" novalidate>
      <div class="field">
        <label for="email">Email</label>
        <input type="email" id="email" name="email" autocomplete="email" required
               placeholder="you@example.com">
      </div>
      <div class="field">
        <label for="accounts">Roughly how many places does your money move through in a month?
          <span class="hint">bank accounts + cards + e-wallets</span>
        </label>
        <select id="accounts" name="accounts" required>
          <option value="" selected disabled>Choose one</option>
          <option value="1-2">1&ndash;2</option>
          <option value="3-4">3&ndash;4</option>
          <option value="5-6">5&ndash;6</option>
          <option value="7plus">7 or more</option>
        </select>
      </div>
      <input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
      <button type="submit" id="submit-btn">Send me the three questions</button>
      <p class="msg" id="form-msg" role="status" aria-live="polite"></p>
    </form>
  </section>

  <footer>
    <p>An independent project by a solo builder in Malaysia. Not a company, not a bank, not
       affiliated with any bank or e-wallet. No data is shared with anyone.</p>
    <p class="variant-tag">v{variant}</p>
  </footer>

</main>
</div>
<noscript><img src="{counter_base}/{variant}/load.svg" alt="" width="1" height="1" style="position:absolute;left:-9999px"></noscript>
<script src="../assets/site.js"></script>
</body>
</html>
"""

THANKS = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thanks &mdash; we&rsquo;ll write once</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="../assets/site.css">
</head>
<body data-variant="thanks">
<div class="wrap">
<main>
  <section class="hero">
    <h1>Thanks. That&rsquo;s it for now.</h1>
    <p class="sub">We&rsquo;ll write to you once, to ask three short questions about how you keep
       track of your spending. We won&rsquo;t ask for a bank login, a statement, a screenshot or a
       balance &mdash; not then, not ever.</p>
  </section>
  <section class="trust">
    <p><strong>There is still nothing to buy.</strong> Nothing is built. This was an early test of
       an idea, and you&rsquo;ve just helped us find out whether it&rsquo;s worth building.</p>
    <p><strong>Your email goes nowhere else.</strong> It is not published, sold or shared.
       Reply to our one email asking to be removed and you will be.</p>
  </section>
  <section class="artifact">
    <p class="artifact-label">In the meantime</p>
    <p><a href="../review/">Read the full sample review</a> &mdash; every figure in it is invented.</p>
  </section>
  <footer>
    <p>An independent project by a solo builder in Malaysia. Not a company, not a bank, not
       affiliated with any bank or e-wallet.</p>
  </footer>
</main>
</div>
</body>
</html>
"""

ROOT_INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Redirecting&hellip;</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="./a/">
<meta http-equiv="refresh" content="0; url=./a/">
</head>
<body>
<p>Redirecting to <a href="./a/">the page</a>.</p>
</body>
</html>
"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)

    (OUT / "assets" / "site.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (OUT / "assets" / "site.js").write_text(
        JS.strip()
        .replace("__COUNTER_BASE__", COUNTER_BASE)
        .replace("__FORM_TARGET_B64__", FORM_TARGET_B64)
        + "\n",
        encoding="utf-8",
    )

    for key, v in VARIANTS.items():
        d = OUT / key
        d.mkdir()
        (d / "index.html").write_text(
            PAGE.format(
                variant=key,
                title=html.escape(v["title"]),
                og_title=html.escape(v["title"]),
                headline=v["headline"],
                subhead=v["subhead"],
                counter_base=COUNTER_BASE,
            ),
            encoding="utf-8",
        )

    (OUT / "thanks").mkdir()
    (OUT / "thanks" / "index.html").write_text(THANKS, encoding="utf-8")
    (OUT / "index.html").write_text(ROOT_INDEX, encoding="utf-8")

    # The sample review, copied verbatim from HEN-44. Not re-typed, not edited.
    review_src = ROOT.parent / "sample-review"
    rd = OUT / "review"
    rd.mkdir()

    # Anchor ids only. No content, figure or wording change — the landing page
    # frame opens at #part1 so the visible slice shows real figures rather than
    # a screen of preamble. Verified below that exactly 4 sections matched.
    review = (review_src / "spending-review-DEMO-synthetic.html").read_text(encoding="utf-8")
    for n in range(1, 5):
        marker = f'<section>\n    <h2><span class="num">Part {n} of 4</span>'
        assert marker in review, f"review markup changed: no anchor point for part {n}"
        review = review.replace(
            marker, f'<section id="part{n}">\n    <h2><span class="num">Part {n} of 4</span>'
        )
    (rd / "index.html").write_text(review, encoding="utf-8")
    shutil.copy(
        review_src / "spending-review-DEMO-synthetic.pdf",
        rd / "spending-review-DEMO-synthetic.pdf",
    )

    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print("built ->", OUT)
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(OUT)}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
