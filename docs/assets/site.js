/* ---------------------------------------------------------------------
   Measurement + submit. No cookies, no fingerprinting, no third-party
   analytics bundle. Each event is a 1x1 image request to a free counter
   endpoint; sessionStorage keeps one visit from counting twice.
   --------------------------------------------------------------------- */
(function () {
  var V = document.body.getAttribute('data-variant');
  var BASE = 'https://hits.sh/hen49.jul7v2v.smoke';

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
     Park the preview on the "if you read nothing else" box so the visible
     slice is the four findings, each with a figure in it.

     It parked on Part 1 until HEN-44 re-cut the review and moved that box
     to the top. Not parking at all was the obvious answer afterwards and
     it is wrong here: this frame is 27rem tall, not a phone screen, so an
     unparked preview spends its whole height on two stacked synthetic
     banners and a title, and the first figure falls below the fold. The
     box is the only slice that fits and carries a number.

     It also keeps the reader-addressing line — "every you below is P0,
     the invented person" — inside the visible slice, which parking on
     part 1 did not.

     Done by scrolling the same-origin child document, NOT by a #fragment
     in the iframe src: fragment navigation inside an iframe scrolls the
     PARENT page too, which would carry visitors straight past the
     headline being tested and void the whole A/B comparison. If this
     fails the preview simply shows the top of the review, which is still
     honest and still a real render. */
  var rf = document.getElementById('review-frame');
  function parkPreview() {
    try {
      var d = rf.contentDocument;
      var target = d.getElementById('upfront') || d.getElementById('part1');
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

  /* Tell a non-Android visitor the truth at the moment they pick, not after
     they have handed over an email. They can still sign up — an iPhone-heavy
     list is a finding about who the promise attracts, and suppressing it would
     destroy exactly the signal HEN-42 says to watch for. */
  var phoneSel = document.getElementById('phone');
  var phoneNote = document.getElementById('platform-note');
  var NOTES = {
    iphone: 'Then this could not work for you, and we would rather say so now. Reading payment ' +
            'notifications is Android-only \u2014 not a feature we have yet, one the iPhone does ' +
            'not allow at all. You are welcome to leave your email anyway and we will tell you ' +
            'honestly if that ever changes.',
    other: 'Worth knowing: this would only work on the Android one. Reading payment ' +
           'notifications is not possible on iPhone.'
  };
  if (phoneSel && phoneNote) {
    phoneSel.addEventListener('change', function () {
      var t = NOTES[phoneSel.value];
      phoneNote.textContent = t || '';
      phoneNote.className = t ? 'platform-note show' : 'platform-note';
    });
  }

  function say(text, isErr) {
    msg.textContent = text;
    msg.className = isErr ? 'msg err' : 'msg';
  }

  el.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (el.querySelector('input[name=_honey]').value) return; /* bot */

    var email = el.email.value.trim();
    var accounts = el.accounts.value;
    var phone = el.phone.value;
    if (!email || !accounts || !phone) { say('Please fill in all three fields.', true); return; }

    btn.disabled = true;
    say('Sending\u2026', false);

    /* Count the submit, the qualification bucket and the platform before the
       network call, so the funnel is measurable even if mail delivery is down.
       Platform is counted separately because an iPhone-heavy list means the
       promise is attracting people the product structurally cannot serve —
       good-looking conversion that is actually a stop signal. No email address
       is ever sent to the counter. */
    ping('submit');
    ping('q-' + accounts);
    ping('p-' + phone);

    var endpoint = 'https://formsubmit.co/ajax/' + atob('amlheXVhbmxpbjgzOEBnbWFpbC5jb20=');
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        email: email,
        accounts: accounts,
        phone: phone,
        variant: V,
        _subject: 'Spending review smoke test \u2014 new signup (variant ' + V + ')',
        _captcha: 'false',
        _template: 'table'
      })
    })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (data) {
        if (data && String(data.success) === 'true') {
          window.location.href = '../thanks/?v=' + V;
        } else {
          /* Say plainly that it did not send. It would be easy to write
             "nothing is lost" here and it would not be true. */
          ping('submit-undelivered');
          say('That didn\u2019t send, and the problem is on our end rather than yours \u2014 ' +
              'our mail setup isn\u2019t finished. Sorry. Please do try again later.', true);
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
