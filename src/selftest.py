#!/usr/bin/env python3
"""
End-to-end check of the signup funnel, run against a LOCAL copy of the built
site with the counter and mail endpoints stubbed.

Why stubbed rather than live:
  * hits.sh counters are incremented by every hit, including ours. Testing
    against the real base would inflate the very numbers the experiment
    reports, and the read-ledger exists precisely to stop that.
  * FormSubmit would deliver a junk signup into the contact list.

Stubbing lets us assert something stronger than "it seemed to work": we see the
exact counter paths that fired and the exact JSON body that would have been
mailed, including the platform field.

Usage:  python3 src/selftest.py
Exits non-zero and prints FAIL lines if any expectation is unmet.
"""

import http.server
import json
import pathlib
import re
import shutil
import socketserver
import subprocess
import sys
import threading
import time

import websocket  # websocket-client

ROOT = pathlib.Path(__file__).resolve().parent.parent
PORT = 8899
BASE = f"http://127.0.0.1:{PORT}"

# The homebrew `chromium` shim on this machine points at an app that is not
# installed, so resolve a real binary rather than trusting PATH.
CHROME = next(
    (c for c in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ) if pathlib.Path(c).exists()),
    None,
)
if not CHROME:
    raise SystemExit("FAIL: no Chrome/Chromium binary found to drive")

hits = []          # counter paths that fired
mails = []         # JSON bodies posted to the mail stub
PIXEL = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>'
)


def build_test_site(dest: pathlib.Path) -> None:
    """Copy the real build and repoint its two outbound endpoints at us."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "docs", dest)

    js = dest / "assets" / "site.js"
    src = js.read_text(encoding="utf-8")
    src = src.replace("https://hits.sh/hen49.jul7v2v.smoke", f"{BASE}/count")
    # The endpoint is assembled as a literal + a routing token. The token used
    # to be atob(<base64 email>) and is now the FormSubmit alias as a plain
    # string, so match whatever follows the literal rather than one shape of it.
    # The guard below still fires if the assembly changes in a way this misses.
    src = re.sub(
        r"'https://formsubmit\.co/ajax/' \+ [^;]+",
        f"'{BASE}/mail/stub'",
        src,
    )
    if "formsubmit.co" in src:
        raise SystemExit("FAIL: could not repoint the mail endpoint")
    js.write_text(src, encoding="utf-8")

    for v in ("a", "b"):
        p = dest / v / "index.html"
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "https://hits.sh/hen49.jul7v2v.smoke", f"{BASE}/count"
            ),
            encoding="utf-8",
        )


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # keep the test output readable
        pass

    def do_GET(self):
        if self.path.startswith("/count/"):
            hits.append(self.path.split("?")[0][len("/count/"):])
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(PIXEL)))
            self.end_headers()
            self.wfile.write(PIXEL)
            return
        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/mail/"):
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n).decode("utf-8")
            try:
                mails.append(json.loads(raw))
            except ValueError:
                mails.append({"_unparsed": raw})
            body = json.dumps({"success": "true"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)


class CDP:
    """Minimal Chrome DevTools Protocol client: navigate, eval, read state."""

    def __init__(self, ws_url):
        # Chrome rejects the CDP handshake when an Origin header is present and
        # not allow-listed; websocket-client sends one by default.
        self.ws = websocket.create_connection(ws_url, timeout=30, suppress_origin=True)
        self.n = 0

    def send(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def eval(self, expr):
        r = self.send(
            "Runtime.evaluate",
            expression=expr,
            returnByValue=True,
            awaitPromise=True,
        )
        return r.get("result", {}).get("value")

    def goto(self, url):
        self.send("Page.navigate", url=url)
        for _ in range(100):
            time.sleep(0.1)
            if self.eval("document.readyState") == "complete":
                return
        raise RuntimeError(f"timed out loading {url}")


def check(label, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + label + (f"  [{detail}]" if detail else ""))
    return cond


def main():
    site = ROOT / ".selftest-site"
    build_test_site(site)

    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(
        ("127.0.0.1", PORT),
        lambda *a, **kw: Handler(*a, directory=str(site), **kw),
    )
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    chrome = subprocess.Popen(
        [
            CHROME, "--headless=new", "--remote-debugging-port=9222",
            "--no-sandbox", "--disable-gpu", "--window-size=900,900",
            "--remote-allow-origins=*",
            "--user-data-dir=" + str(ROOT / ".selftest-profile"),
            "about:blank",
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    ok = True
    try:
        import urllib.request
        ws_url = None
        for _ in range(60):
            time.sleep(0.25)
            try:
                tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json"))
                pages = [t for t in tabs if t.get("type") == "page"]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                continue
        if not ws_url:
            raise SystemExit("FAIL: chromium devtools never came up")

        cdp = CDP(ws_url)
        cdp.send("Page.enable")
        cdp.send("Runtime.enable")

        # ---- copy assertions, both variants ---------------------------
        for v in ("a", "b"):
            cdp.goto(f"{BASE}/{v}/")
            kicker = cdp.eval("document.querySelector('.kicker').textContent")
            sub = cdp.eval("document.querySelector('.sub').textContent")
            ok &= check(
                f"variant {v}: platform limit stated above the headline",
                kicker and "Android only" in kicker, (kicker or "")[:48],
            )
            ok &= check(
                f"variant {v}: Android named inside the promise sentence",
                sub and "on Android" in sub,
            )
            ok &= check(
                f"variant {v}: price stated on the page",
                "RM10" in (cdp.eval("document.body.innerText") or ""),
            )
            ok &= check(
                f"variant {v}: no bank-credential ask anywhere on the page",
                not re.search(
                    r"bank login|password|statement upload|upload (your )?statement",
                    (cdp.eval("document.body.innerText") or "").lower().replace(
                        "no bank login", ""),
                ),
            )

        # ---- the honest iPhone note fires on selection ----------------
        cdp.goto(f"{BASE}/a/")
        cdp.eval(
            "(function(){var s=document.getElementById('phone');s.value='iphone';"
            "s.dispatchEvent(new Event('change'));return 1})()"
        )
        note = cdp.eval("document.getElementById('platform-note').textContent")
        ok &= check(
            "iPhone selection warns the visitor BEFORE they hand over an email",
            note and "Android-only" in note, (note or "")[:52],
        )
        ok &= check(
            "the warning is actually visible, not just in the DOM",
            cdp.eval(
                "getComputedStyle(document.getElementById('platform-note'))"
                ".display !== 'none'"
            ),
        )

        # ---- required-field enforcement -------------------------------
        hits.clear()
        cdp.eval(
            "(function(){var f=document.getElementById('signup-form');"
            "f.email.value='blocked@example.com';f.accounts.value='3-4';"
            "f.phone.value='';"
            "f.dispatchEvent(new Event('submit',{cancelable:true}));return 1})()"
        )
        time.sleep(0.6)
        ok &= check(
            "submit without a platform answer is refused and NOT counted",
            not any(h.endswith("submit.svg") for h in hits),
            f"hits={hits}",
        )

        # ---- full submit, variant b -----------------------------------
        hits.clear()
        mails.clear()
        cdp.goto(f"{BASE}/b/")
        cdp.eval(
            "(function(){var f=document.getElementById('signup-form');"
            "f.email.value='selftest@example.com';f.accounts.value='5-6';"
            "f.phone.value='android';"
            "f.dispatchEvent(new Event('submit',{cancelable:true}));return 1})()"
        )
        for _ in range(60):
            time.sleep(0.2)
            if mails:
                break
        time.sleep(1.0)

        ok &= check("submission reached the mail endpoint", len(mails) == 1,
                    f"n={len(mails)}")
        if mails:
            m = mails[0]
            ok &= check("platform travels with the signup", m.get("phone") == "android",
                        json.dumps({k: m.get(k) for k in ("accounts", "phone", "variant")}))
            ok &= check("variant travels with the signup", m.get("variant") == "b")
        ok &= check("submit counted once on variant b",
                    hits.count("b/submit.svg") == 1, f"hits={hits}")
        ok &= check("platform counter fired on its own bucket",
                    hits.count("b/p-android.svg") == 1)
        ok &= check("qualification counter fired on its own bucket",
                    hits.count("b/q-5-6.svg") == 1)
        ok &= check("no email address is ever sent to a counter",
                    not any("@" in h or "selftest" in h for h in hits))
        ok &= check(
            "visitor lands on the thank-you page",
            "/thanks/" in (cdp.eval("location.pathname") or ""),
            cdp.eval("location.pathname"),
        )
    finally:
        chrome.terminate()
        httpd.shutdown()
        shutil.rmtree(site, ignore_errors=True)
        shutil.rmtree(ROOT / ".selftest-profile", ignore_errors=True)

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
