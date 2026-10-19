#!/usr/bin/env python3
"""A RADIUS authentication and accounting server, in pure Python, on any UDP port.

Why this exists: a testbox's packaged RADIUS server keeps its clients and users under
/etc/, which is root to edit, and binding 1812/1813 is root as well (STANDING-ORDERS
s4).  This one runs as an ordinary user on unprivileged ports -- a switch under test is
pointed at it with `radius-server host <box> auth-port <n> acct-port <n>` -- and every
client, user and secret is given on the command line, so the whole server side of a
case is visible in the working log.

It is also an instrument: each packet it handles is logged with one line, and the log
is the server-side half of the evidence that the wire capture is the other half of.

Usage:
  radsrv.py --secret S --client IP [--client IP ...] --user NAME:PASSWORD [...] [options]

  --auth-port N     authentication port  (default 11812; 0 disables)
  --acct-port N     accounting port      (default 11813; 0 disables)
  --bind IP         address to listen on (default 0.0.0.0)
  --secret S        shared secret for every client, unless --client-secret is used
  --client IP       a NAS allowed to use --secret; repeatable.  With none, any source
                    is accepted (say so in the log when you do that)
  --client-secret IP=SECRET   a per-client secret; repeatable
  --user NAME:PASSWORD        a known user; repeatable
  --user-file PATH            one NAME:PASSWORD per line, # comments allowed
  --reply-attr N=VALUE        extra attribute on every Access-Accept
                              (integer N; VALUE is text, or 0x... for raw bytes)
  --reject-all      answer every Access-Request with Access-Reject (a control run)
  --drop-all        answer nothing at all (a control run: proves the DUT's retry and
                    dead-server behaviour, and that a capture really is empty)
  --log PATH        append one line per packet here as well as to stdout
  --seconds N       exit after N seconds (default 0 = until --stopfile or SIGTERM)
  --stopfile PATH   exit as soon as this file exists
  --pidfile PATH    write the pid here at startup

Behaviour, deliberately plain so a log reads unambiguously:
  * a request from an unlisted client, or one whose Message-Authenticator does not
    verify, is DROPPED and logged as such -- that is what a real server does, and it
    is how a wrong-secret control shows up as silence rather than a Reject;
  * a known user with the right password gets Access-Accept, anything else
    Access-Reject with a Reply-Message;
  * every Accounting-Request that authenticates gets an Accounting-Response.

Exit: 0 normally, 2 on a usage or bind error.
"""
import argparse
import os
import select
import signal
import socket
import sys
import time

import radius as R

RUNNING = True


def _stop(_sig, _frm):
    global RUNNING
    RUNNING = False


class Log(object):
    def __init__(self, path):
        self.f = open(path, "a", buffering=1) if path else None
        self.counts = {}

    def __call__(self, tag, msg):
        self.counts[tag] = self.counts.get(tag, 0) + 1
        line = "%s %-22s %s" % (time.strftime("%H:%M:%S"), tag, msg)
        print(line, flush=True)
        if self.f:
            self.f.write(line + "\n")

    def summary(self):
        return " ".join("%s=%d" % (k, self.counts[k]) for k in sorted(self.counts))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--auth-port", type=int, default=11812)
    ap.add_argument("--acct-port", type=int, default=11813)
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--secret", default="testing123")
    ap.add_argument("--client", action="append", default=[])
    ap.add_argument("--client-secret", action="append", default=[])
    ap.add_argument("--user", action="append", default=[])
    ap.add_argument("--user-file")
    ap.add_argument("--reply-attr", action="append", default=[])
    ap.add_argument("--reject-all", action="store_true")
    ap.add_argument("--drop-all", action="store_true")
    ap.add_argument("--log")
    ap.add_argument("--seconds", type=int, default=0)
    ap.add_argument("--stopfile")
    ap.add_argument("--pidfile")
    a = ap.parse_args()

    users = {}
    for u in a.user:
        if ":" not in u:
            print("radsrv: --user wants NAME:PASSWORD, got %r" % u, file=sys.stderr)
            return 2
        n, p = u.split(":", 1)
        users[n] = p
    if a.user_file:
        with open(a.user_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and ":" in line:
                    n, p = line.split(":", 1)
                    users[n] = p

    secrets = {}
    for cs in a.client_secret:
        if "=" not in cs:
            print("radsrv: --client-secret wants IP=SECRET", file=sys.stderr)
            return 2
        ip, s = cs.split("=", 1)
        secrets[ip] = s
    for ip in a.client:
        secrets.setdefault(ip, a.secret)
    allow_any = not secrets

    extra = []
    for ra in a.reply_attr:
        if "=" not in ra:
            print("radsrv: --reply-attr wants N=VALUE", file=sys.stderr)
            return 2
        n, v = ra.split("=", 1)
        extra.append((int(n), bytes.fromhex(v[2:]) if v.startswith("0x") else v))

    socks = {}
    try:
        for port, kind in ((a.auth_port, "auth"), (a.acct_port, "acct")):
            if port:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((a.bind, port))
                socks[s] = (kind, port)
    except OSError as e:
        print("radsrv: cannot bind -- %s" % e, file=sys.stderr)
        return 2

    if a.pidfile:
        with open(a.pidfile, "w") as f:
            f.write("%d\n" % os.getpid())
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    log = Log(a.log)
    log("START", "bind=%s auth=%s acct=%s users=%s clients=%s%s%s"
        % (a.bind, a.auth_port or "-", a.acct_port or "-", ",".join(sorted(users)) or "-",
           ",".join(sorted(secrets)) or "ANY", " REJECT-ALL" if a.reject_all else "",
           " DROP-ALL" if a.drop_all else ""))

    t_end = time.time() + a.seconds if a.seconds else None
    while RUNNING:
        if t_end and time.time() >= t_end:
            break
        if a.stopfile and os.path.exists(a.stopfile):
            break
        ready, _, _ = select.select(list(socks), [], [], 0.5)
        for s in ready:
            kind, port = socks[s]
            try:
                data, peer = s.recvfrom(8192)
            except OSError:
                continue
            src = peer[0]
            secret = secrets.get(src, a.secret if allow_any else None)
            if secret is None:
                log("DROP-unknown-client", "from %s:%d on %s/%d (%d bytes)"
                    % (peer[0], peer[1], kind, port, len(data)))
                continue
            try:
                code, ident, auth, body = R.parse(data)
                attrs = R.parse_attrs(body)
            except ValueError as e:
                log("DROP-malformed", "from %s -- %s" % (src, e))
                continue

            shown = ", ".join("%s=%s" % (R.attr_name(t),
                                         "<hidden>" if t == 2 else R.show_value(t, v))
                              for t, v in attrs)
            user = (R.find(attrs, 1) or b"").decode("utf-8", "replace")

            # Message-Authenticator, when present, is the cheapest proof of the secret.
            ma = R.find(attrs, 80)
            if ma is not None:
                zeroed = b"".join(R.attr(t, b"\x00" * 16 if t == 80 else v) for t, v in attrs)
                if R.message_authenticator(code, ident, auth, zeroed, secret) != ma:
                    log("DROP-bad-msg-auth", "from %s user=%r" % (src, user))
                    continue

            if code == 4:                                   # Accounting-Request
                want = R.acct_request_authenticator(ident, body, secret)
                if want != auth:
                    log("DROP-bad-acct-auth", "from %s user=%r (wrong secret)" % (src, user))
                    continue
                st = R.find(attrs, 40)
                stn = int.from_bytes(st, "big") if st else 0
                log("Accounting-Request", "from %s id=%d user=%r %s=%s | %s"
                    % (src, ident, user, "Acct-Status-Type",
                       R.ACCT_STATUS.get(stn, stn), shown))
                if a.drop_all:
                    log("DROP-all", "accounting from %s id=%d" % (src, ident))
                    continue
                rbody = b""
                ra = R.response_authenticator(5, ident, rbody, auth, secret)
                s.sendto(R.build(5, ident, ra, rbody), peer)
                log("Accounting-Response", "to %s id=%d" % (src, ident))
                continue

            if code != 1:
                log("IGNORED", "%s from %s id=%d" % (R.code_name(code), src, ident))
                continue

            log("Access-Request", "from %s id=%d user=%r | %s" % (src, ident, user, shown))
            if a.drop_all:
                log("DROP-all", "auth from %s id=%d" % (src, ident))
                continue

            hidden = R.find(attrs, 2)
            given = R.pap_unhide(hidden, secret, auth) if hidden is not None else None
            if a.reject_all:
                ok, why = False, "reject-all control"
            elif hidden is None:
                ok, why = False, "no User-Password (PAP) attribute"
            elif user not in users:
                ok, why = False, "no such user"
            elif users[user] != given:
                ok, why = False, "wrong password"
            else:
                ok, why = True, "ok"

            if ok:
                rbody = R.pack_attrs([(18, "Access granted by radsrv.py")] + extra)
                rcode = 2
            else:
                rbody = R.pack_attrs([(18, "Rejected: " + why)])
                rcode = 3
            ra = R.response_authenticator(rcode, ident, rbody, auth, secret)
            s.sendto(R.build(rcode, ident, ra, rbody), peer)
            log(R.code_name(rcode), "to %s id=%d user=%r (%s)" % (src, ident, user, why))

    log("STOP", log.summary())
    for s in socks:
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
