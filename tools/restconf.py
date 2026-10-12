#!/usr/bin/env python3
"""restconf.py -- a minimal RESTCONF (RFC 8040) client for AW+ devices, stdlib only.

    restconf.py <host> <METHOD> <path> [--data JSON|@file] [--user U] [--password P]
                [--port N] [--http] [--root R] [--out FILE] [--max-bytes N] [--timeout S]
                [--grep REGEX]

<path> forms:
  /.well-known/host-meta     sent as given (an absolute path starting with '/')
  data/<...>, operations/<...>, yang-library-version, or ''   relative to the RESTCONF root.
      The root comes from --root, else from GET /.well-known/host-meta (the <Link rel='restconf'
      href='...'> element, RFC 8040 §3.1), discovered once per call.

METHOD: GET, HEAD, OPTIONS, POST, PUT, PATCH, DELETE.  --data takes a JSON string or @file;
it is sent as application/yang-data+json (Accept is the same).

Credentials: --user/--password, else env CK_USER / CK_PASSWORD, else AW+'s manager / friend
(the same defaults as the console tools).  HTTPS by default, certificate NOT verified (bench
units carry self-signed certificates).

Output: one status line `HTTP <code> <reason>  <METHOD> <url>  (<n> bytes, <t> s)`, the
Content-Type / Location / Allow headers when present, then the body: to --out FILE if given
(and only its first --max-bytes to stdout), else the first --max-bytes (default 4000) to stdout.
--grep prints only body lines matching REGEX (applied after pretty-printing JSON).
Exit: 0 for a 2xx answer, 1 for any other HTTP status, 2 usage, 3 connection error.
"""
import argparse
import base64
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

METHODS = ("GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE")
CT = "application/yang-data+json"


def request(base, method, path, user, password, data=None, timeout=30, accept=CT):
    url = base + path
    body = None
    headers = {"Accept": accept,
               "Authorization": "Basic " + base64.b64encode(
                   ("%s:%s" % (user, password)).encode()).decode()}
    if data is not None:
        body = data.encode()
        headers["Content-Type"] = CT
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        code, reason, hdrs, raw = resp.status, resp.reason, resp.headers, resp.read()
    except urllib.error.HTTPError as e:
        code, reason, hdrs, raw = e.code, e.reason, e.headers, e.read()
    return url, code, reason, hdrs, raw, time.time() - t0


def discover_root(base, user, password, timeout):
    url, code, reason, hdrs, raw, _ = request(base, "GET", "/.well-known/host-meta", user,
                                              password, timeout=timeout, accept="application/xrd+xml")
    m = re.search(rb"rel=['\"]restconf['\"]\s+href=['\"]([^'\"]+)['\"]", raw) or \
        re.search(rb"href=['\"]([^'\"]+)['\"]\s+rel=['\"]restconf['\"]", raw)
    if code != 200 or not m:
        sys.exit("restconf root not found at %s: HTTP %s %s\n%s" % (url, code, reason,
                                                                   raw[:500].decode("utf-8", "replace")))
    return m.group(1).decode().rstrip("/")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("host")
    ap.add_argument("method", type=str.upper, choices=METHODS)
    ap.add_argument("path")
    ap.add_argument("--data")
    ap.add_argument("--user", default=os.environ.get("CK_USER", "manager"))
    ap.add_argument("--password", default=os.environ.get("CK_PASSWORD", "friend"))
    ap.add_argument("--port", type=int)
    ap.add_argument("--http", action="store_true", help="plain HTTP instead of HTTPS")
    ap.add_argument("--root", help="RESTCONF root (skip host-meta discovery), e.g. /restconf")
    ap.add_argument("--out", help="write the whole body here")
    ap.add_argument("--max-bytes", type=int, default=4000)
    ap.add_argument("--timeout", type=float, default=30)
    ap.add_argument("--grep", help="print only body lines matching this regex")
    a = ap.parse_args(argv)

    scheme = "http" if a.http else "https"
    port = a.port or (80 if a.http else 443)
    base = "%s://%s:%d" % (scheme, a.host, port)
    data = a.data
    if data and data.startswith("@"):
        with open(data[1:]) as f:
            data = f.read()
    if data:
        try:
            json.loads(data)                              # refuse malformed JSON before sending
        except ValueError as e:
            ap.error("--data is not valid JSON: %s" % e)
    path = a.path
    try:
        if not a.path.startswith("/"):
            root = a.root.rstrip("/") if a.root else discover_root(base, a.user, a.password, a.timeout)
            print("restconf root: %s" % root)
            path = root + ("/" + a.path if a.path else "")
        url, code, reason, hdrs, raw, dt = request(base, a.method, path, a.user, a.password,
                                                   data=data, timeout=a.timeout)
    except (urllib.error.URLError, OSError) as e:
        print("CONNECTION ERROR %s %s%s: %s" % (a.method, base, path if path.startswith("/")
                                                 else "/" + path, e))
        return 3
    print("HTTP %s %s  %s %s  (%d bytes, %.2f s)" % (code, reason, a.method, url, len(raw), dt))
    for h in ("Content-Type", "Location", "Allow"):
        if hdrs.get(h):
            print("  %s: %s" % (h, hdrs.get(h)))
    text = raw.decode("utf-8", "replace")
    try:
        text = json.dumps(json.loads(text), indent=1)
    except ValueError:
        pass
    if a.out:
        with open(a.out, "w") as f:
            f.write(text)
        print("  body -> %s" % a.out)
    if a.grep:
        rx = re.compile(a.grep)
        text = "\n".join(l for l in text.splitlines() if rx.search(l))
    if text:
        print(text[:a.max_bytes] + ("\n... (%d more bytes)" % (len(text) - a.max_bytes)
                                    if len(text) > a.max_bytes else ""))
    return 0 if 200 <= code < 300 else 1


if __name__ == "__main__":
    sys.exit(main())
