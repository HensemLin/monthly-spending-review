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
    say('Sending\u2026', false);

    /* Count the submit and the qualification bucket before the network call,
       so the funnel is measurable even if mail delivery is down. No email
       address is ever sent to the counter. */
    ping('submit');
    ping('q-' + accounts);

    var endpoint = 'https://formsubmit.co/ajax/' + atob('amlheXVhbmxpbjgzOEBnbWFpbC5jb20=');
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        email: email,
        accounts: accounts,
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
