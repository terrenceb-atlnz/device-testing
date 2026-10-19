#!/usr/bin/env python3
"""httpq.py -- one HTTP/HTTPS request to a device's management interface, from the testbox.

A minimal, dependency-free client for the third management access path.  `service http` is a
feature a Management case has to grade just like telnet and ssh, and the only honest way to
say what the web interface does -- or that there is nothing behind it -- is to ask it.

It prints the status line, the response headers and (optionally truncated) body, so a case can
quote what the device actually answered instead of inferring it from `show http`.

Device certificates are self-signed (`CN = AlliedwarePlusDefault`), so TLS verification is OFF
by default: this talks to lab hardware on a lab segment, never to anything that matters.

Usage:
  httpq.py <url> [--method M] [--user U --password P] [--data STR] [--header 'K: V']...
           [--timeout S] [--max-body N] [--verify] [--head-only]

Exit: 0 got a response (whatever its status), 4 the transport failed, 6 usage.
"""

import argparse
import base64
import ssl
import sys
import urllib.error
import urllib.request


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("url")
    ap.add_argument("--method", default="GET")
    ap.add_argument("--user", default=None)
    ap.add_argument("--password", default=None)
    ap.add_argument("--data", default=None,
                    help="request body; sets the method to POST unless --method says otherwise")
    ap.add_argument("--header", action="append", default=[],
                    help="extra request header 'Key: value'; repeatable")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--max-body", type=int, default=4000)
    ap.add_argument("--verify", action="store_true",
                    help="verify TLS (off by default: device certs are self-signed)")
    ap.add_argument("--head-only", action="store_true", help="do not print the body")
    args = ap.parse_args()

    method = args.method.upper()
    body = args.data.encode() if args.data is not None else None
    if body is not None and method == "GET":
        method = "POST"

    req = urllib.request.Request(args.url, data=body, method=method)
    for h in args.header:
        if ":" not in h:
            print("httpq: bad --header %r (want 'Key: value')" % h)
            return 6
        k, v = h.split(":", 1)
        req.add_header(k.strip(), v.strip())
    if args.user is not None:
        token = base64.b64encode(
            ("%s:%s" % (args.user, args.password or "")).encode()).decode()
        req.add_header("Authorization", "Basic " + token)
    if body is not None and not any(h.lower() == "content-type"
                                    for h in req.headers):
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

    # Build the context unconditionally, not just for an https:// URL: an AW+ device answers
    # plain http with a 301 to https, urllib follows it, and a context attached only to an
    # https starting URL is not in play by then -- the redirect then dies on
    # CERTIFICATE_VERIFY_FAILED against the device's self-signed cert (tb277 2026-10-20).
    ctx = ssl.create_default_context()
    if not args.verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    print("=== %s %s ===" % (method, args.url))
    try:
        resp = urllib.request.urlopen(req, timeout=args.timeout, context=ctx)
        status, reason, headers = resp.status, resp.reason, resp.headers
        payload = resp.read(args.max_body + 1)
    except urllib.error.HTTPError as exc:
        status, reason, headers = exc.code, exc.reason, exc.headers
        payload = exc.read(args.max_body + 1)
    except (urllib.error.URLError, OSError, ssl.SSLError) as exc:
        print("TRANSPORT FAILED: %s" % exc)
        return 4

    print("HTTP %s %s" % (status, reason))
    for k, v in sorted(headers.items()):
        print("  %s: %s" % (k, v))
    if args.head_only:
        return 0
    print("--- body (%d bytes shown%s) ---"
          % (min(len(payload), args.max_body),
             ", TRUNCATED" if len(payload) > args.max_body else ""))
    sys.stdout.write(payload[:args.max_body].decode("utf-8", "replace"))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
