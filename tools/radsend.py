#!/usr/bin/env python3
"""Send a RADIUS Access-Request or Accounting-Request and report the reply, in pure Python.

A NAS in one command, so a switch's RADIUS *server* (local or proxy) can be tested
without a second switch and without `radclient`.  It is also the CONTROL instrument:
`--secret` and `--password` can deliberately be wrong, and a RADIUS server that holds
a different secret answers nothing at all -- which is itself the measurement.

It verifies the reply's Response Authenticator against the shared secret, so a reply
is only called valid when the responder demonstrably holds the secret.  That is the
one fact no `show` command on either box can give you.

Usage:
  radsend.py <server-ip> --user NAME --password PW --secret S [options]
  radsend.py <server-ip> --acct start|stop --user NAME --secret S [options]

  --port N          server UDP port (default 1812 auth, 1813 accounting)
  --acct TYPE       send Accounting-Request instead: start, stop or interim
  --nas-ip IP       NAS-IP-Address attribute (default: the local address used)
  --nas-id TEXT     NAS-Identifier attribute
  --service-type N  Service-Type (default 1 = Login; 0 omits it)
  --session-id TEXT Acct-Session-Id (default a generated one)
  --session-time N  Acct-Session-Time for a stop
  --msg-auth        also send a Message-Authenticator(80)
  --count N         send N identical requests (default 1)
  --timeout S       seconds to wait for each reply (default 5)
  --retries N       retransmits per request when no reply (default 0)
  --bind IP         source address to bind (picks the egress interface)
  --id N            start the RADIUS identifier here (default random)
  --quiet           one summary line only

Exit: 0 if every request got a reply whose authenticator verified,
      1 if any request got no reply (an ICMP port-unreachable is reported and counts
        as no reply -- it proves nothing is listening, which is often the control),
      3 if a reply arrived whose Response Authenticator did NOT verify,
      4 if the reply was an Access-Reject (a reject is a real answer, not an error,
        so a case that EXPECTS one treats 4 as success),
      2 on a usage or socket error.
"""
import argparse
import random
import socket
import sys
import time

import radius as R


def describe(body, secret=None, authenticator=None):
    out = []
    for t, v in R.parse_attrs(body):
        if t == 2 and secret is not None and authenticator is not None:
            out.append("User-Password=<hidden,%d bytes>" % len(v))
        else:
            out.append("%s=%s" % (R.attr_name(t), R.show_value(t, v)))
    return ", ".join(out) if out else "(no attributes)"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("server")
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--secret", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", default="")
    ap.add_argument("--acct", choices=["start", "stop", "interim"])
    ap.add_argument("--nas-ip")
    ap.add_argument("--nas-id")
    ap.add_argument("--service-type", type=int, default=1)
    ap.add_argument("--session-id")
    ap.add_argument("--session-time", type=int, default=0)
    ap.add_argument("--msg-auth", action="store_true")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--retries", type=int, default=0)
    ap.add_argument("--bind")
    ap.add_argument("--id", type=int, default=-1)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    port = a.port or (1813 if a.acct else 1812)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if a.bind:
            sock.bind((a.bind, 0))
        sock.connect((a.server, port))
    except OSError as e:
        print("radsend: cannot reach %s:%d -- %s" % (a.server, port, e), file=sys.stderr)
        return 2
    local_ip = sock.getsockname()[0]
    nas_ip = a.nas_ip or local_ip
    sess = a.session_id or ("rs%08x" % random.getrandbits(32))
    ident = a.id if a.id >= 0 else random.randrange(256)

    replies, no_reply, bad_auth, rejects = 0, 0, 0, 0
    for n in range(a.count):
        auth = R.new_authenticator()
        if a.acct:
            st = {"start": 1, "stop": 2, "interim": 3}[a.acct]
            attrs = [(1, a.user), (4, nas_ip), (40, st), (44, sess), (61, 5)]
            if a.nas_id:
                attrs.append((32, a.nas_id))
            if a.acct == "stop":
                attrs += [(46, a.session_time), (49, 1)]
            code = 4
            body = R.pack_attrs(attrs)
            auth = R.acct_request_authenticator(ident, body, a.secret)
            pkt = R.build(code, ident, auth, body)
        else:
            code = 1
            attrs = [(1, a.user), (2, R.pap_hide(a.password, a.secret, auth)),
                     (4, nas_ip), (5, 0), (61, 5)]
            if a.service_type:
                attrs.append((6, a.service_type))
            if a.nas_id:
                attrs.append((32, a.nas_id))
            if a.msg_auth:
                attrs = R.add_message_authenticator(code, ident, auth, attrs, a.secret)
            body = R.pack_attrs(attrs)
            pkt = R.build(code, ident, auth, body)

        if not a.quiet:
            print("-> %s id=%d to %s:%d from %s  %s"
                  % (R.code_name(code), ident, a.server, port, local_ip,
                     describe(body, a.secret, auth)))

        got, refused = None, False
        for _try in range(a.retries + 1):
            sock.settimeout(a.timeout)
            t0 = time.time()
            try:
                sock.send(pkt)
                data = sock.recv(4096)
            except socket.timeout:
                continue
            except ConnectionRefusedError:
                # The destination answered ICMP port-unreachable: a measurement in its
                # own right -- nothing is listening on that UDP port.
                refused = True
                continue
            got = (data, time.time() - t0)
            break

        if got is None:
            no_reply += 1
            if not a.quiet:
                print("<- NO REPLY after %.1fs (x%d)%s"
                      % (a.timeout, a.retries + 1,
                         "  [ICMP port unreachable: nothing listening on that UDP port]"
                         if refused else ""))
        else:
            data, rtt = got
            try:
                rcode, rid, rauth, rbody = R.parse(data)
            except ValueError as e:
                bad_auth += 1
                print("<- MALFORMED reply: %s" % e)
                ident = (ident + 1) % 256
                continue
            want = R.response_authenticator(rcode, rid, rbody, auth, a.secret)
            ok = (rauth == want) and (rid == ident)
            replies += 1
            if not ok:
                bad_auth += 1
            if rcode == 3:
                rejects += 1
            if not a.quiet:
                print("<- %s id=%d in %.3fs  authenticator=%s  %s"
                      % (R.code_name(rcode), rid, rtt,
                         "VALID (responder holds the secret)" if ok else "INVALID",
                         describe(rbody)))
        ident = (ident + 1) % 256

    print("radsend: sent=%d replies=%d no_reply=%d rejects=%d bad_authenticator=%d"
          % (a.count, replies, no_reply, rejects, bad_auth))
    sock.close()
    if bad_auth:
        return 3
    if no_reply:
        return 1
    if rejects:
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
