#!/usr/bin/env python3
"""An SMTP server, in pure Python, on any TCP port, that can REQUIRE authentication.

Why this exists: a device under test that is an SMTP *client* (AlliedWare Plus
`mail smtpserver <ip> [port N] [authentication plain|login|crammd5|oauth2]`,
triggered by `log email <address>`) can only be graded on what it puts on the wire --
which `AUTH` verb it sends, with which mechanism, carrying which credential, and what
it does with the server's answer.  A testbox's packaged MTA is no use for that: a
stock Postfix advertises no `AUTH` at all, and adding SASL to it means editing files
under /etc/ and restarting a system service, which is root (STANDING-ORDERS s4).
Binding port 25 is root as well.

This one runs as an ordinary user on an unprivileged port -- the DUT is pointed at it
with `mail smtpserver <box> port <n>` -- and every user, password, mechanism and
behaviour switch is on the command line, so the whole server side of a case is visible
in the working log.

It is an instrument first and a mail server second.  Every byte in each direction is
logged as a timestamped `C:` / `S:` transcript, so the log IS the server-side half of
the wire evidence (the other half being a tcpdump capture of the same exchange).  At
exit it prints a SUMMARY block counting connections, AUTH attempts per mechanism,
successes and failures, which is what a working log quotes.

Usage:
  smtpsrv.py [--port N] [--bind IP] [--user NAME:PASSWORD ...] [options]

  --port N          TCP port to listen on (default 11025).  Must be >= 1024 unless
                    you are root, which you should not be.
  --bind IP         address to listen on (default 0.0.0.0)
  --hostname NAME   the name in the 220 banner and the EHLO reply (default ck-smtp)
  --user NAME:PASSWORD   a known user; repeatable.  With none, every credential is
                    wrong, which is a perfectly good negative control.
  --mech M          an AUTH mechanism to ADVERTISE; repeatable; one of PLAIN, LOGIN,
                    CRAM-MD5.  Default: all three.  `--mech none` advertises no AUTH
                    line at all (what a stock Postfix looks like).
  --require-auth    refuse MAIL FROM with 530 5.7.0 until the session has
                    authenticated.  This is what makes a client that CAN authenticate
                    actually do so, and what makes one that cannot fail visibly.
  --reject-auth     answer every AUTH, right credential or not, with 535.  A control
                    that separates "the DUT sent the verb" from "the DUT was let in".
  --maildir PATH    write each accepted message to PATH/msg-<n>.eml
  --log PATH        append the transcript here as well as to stdout
  --seconds N       exit after N seconds (default 0 = until --stopfile or SIGTERM)
  --stopfile PATH   exit as soon as this file exists
  --pidfile PATH    write the pid here at startup

Behaviour, deliberately plain so a transcript reads unambiguously:
  * EHLO is answered with 250-PIPELINING, 250-SIZE, 250-AUTH <mechs> (unless
    `--mech none`) and 250 HELP.  HELO gets a bare 250.
  * AUTH PLAIN accepts both the initial-response form (`AUTH PLAIN <b64>`) and the
    two-step form (`AUTH PLAIN` then 334 then the b64 line).
  * AUTH LOGIN prompts `334 VXNlcm5hbWU6` then `334 UGFzc3dvcmQ6`, as every client
    expects, and the decoded username and password are logged.
  * AUTH CRAM-MD5 sends a real challenge and checks a real HMAC-MD5 digest, so a
    success PROVES the client computed the digest from the shared password -- the
    password itself never crosses the wire.  A client that merely echoes something is
    rejected.
  * An unknown mechanism gets 504, a bad credential 535, a malformed base64 501.
  * Credentials are logged as `user=<name> pass=<n> chars` -- never the password
    itself, per the standing rule about secrets in transcripts.  `--show-secrets`
    overrides that for a bench account whose password is already in the case text.

Limits: no TLS (STARTTLS is not advertised and not accepted -- this server exists to
read the AUTH dialogue in clear), no relaying, no spool, one connection at a time
(a DUT's log-email client opens one), IPv4 and IPv6 both.
"""

import argparse
import base64
import binascii
import hashlib
import hmac
import os
import random
import socket
import sys
import time

EXIT_OK = 0
EXIT_ARGS = 2


def b64d(s):
    """Decode base64 strictly; return None on anything malformed."""
    try:
        return base64.b64decode(s.encode("ascii"), validate=True)
    except (binascii.Error, UnicodeEncodeError, ValueError):
        return None


def b64e(b):
    if isinstance(b, str):
        b = b.encode("utf-8")
    return base64.b64encode(b).decode("ascii")


class Log(object):
    def __init__(self, path=None):
        self.fh = open(path, "a") if path else None
        self.t0 = time.time()

    def __call__(self, fmt, *args):
        line = fmt % args if args else fmt
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        out = "%sZ %s" % (stamp, line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
        if self.fh:
            self.fh.write(out + "\n")
            self.fh.flush()


class Stats(object):
    def __init__(self):
        self.connections = 0
        self.ehlo = 0
        self.helo = 0
        self.auth_attempts = {}      # mech -> count
        self.auth_ok = {}            # mech -> count
        self.auth_fail = {}          # mech -> count
        self.auth_unknown = []       # mechanisms we were offered but do not do
        self.mail_from = 0
        self.mail_from_denied = 0
        self.messages = 0
        self.quit = 0
        self.no_auth_sessions = 0    # sessions that reached MAIL FROM without AUTH

    def bump(self, d, k):
        d[k] = d.get(k, 0) + 1


class Session(object):
    """One SMTP conversation."""

    def __init__(self, conn, peer, args, log, stats):
        self.c = conn
        self.peer = peer
        self.a = args
        self.log = log
        self.st = stats
        self.buf = b""
        self.authed_as = None
        self.mailfrom = None
        self.rcpt = []

    # -- wire -------------------------------------------------------------
    def send(self, line):
        self.log("S: %s", line)
        self.c.sendall((line + "\r\n").encode("utf-8"))

    def readline(self):
        while b"\r\n" not in self.buf:
            try:
                chunk = self.c.recv(4096)
            except socket.timeout:
                self.log("   (read timeout, closing)")
                return None
            if not chunk:
                return None
            self.buf += chunk
        line, self.buf = self.buf.split(b"\r\n", 1)
        text = line.decode("utf-8", "replace")
        self.log("C: %s", text)
        return text

    # -- credential checking ----------------------------------------------
    def cred_note(self, user, password):
        if self.a.show_secrets:
            return "user=%r pass=%r" % (user, password)
        return "user=%r pass=<%d chars>" % (user, len(password or ""))

    def check_plain(self, user, password, mech):
        want = self.a.users.get(user)
        if self.a.reject_auth:
            return False, "--reject-auth in force"
        if want is None:
            return False, "no such user"
        if want != password:
            return False, "wrong password"
        return True, "ok"

    def check_cram(self, user, digest_hex, challenge):
        if self.a.reject_auth:
            return False, "--reject-auth in force"
        want = self.a.users.get(user)
        if want is None:
            return False, "no such user"
        expect = hmac.new(want.encode("utf-8"), challenge.encode("utf-8"),
                          hashlib.md5).hexdigest()
        if not hmac.compare_digest(expect, (digest_hex or "").lower()):
            return False, "digest mismatch (expected %s, got %s)" % (expect, digest_hex)
        return True, "ok"

    # -- AUTH --------------------------------------------------------------
    def do_auth(self, arg):
        parts = arg.split(None, 1)
        mech = parts[0].upper() if parts else ""
        initial = parts[1].strip() if len(parts) > 1 else None
        self.st.bump(self.st.auth_attempts, mech or "(empty)")
        self.log("** AUTH verb from DUT: mechanism=%s initial-response=%s",
                 mech or "(none)", "yes" if initial else "no")

        if mech not in self.a.mechs:
            if mech not in self.st.auth_unknown:
                self.st.auth_unknown.append(mech)
            self.st.bump(self.st.auth_fail, mech or "(empty)")
            self.send("504 5.5.4 Unrecognized authentication type")
            return

        if mech == "PLAIN":
            if initial is None:
                self.send("334 ")
                initial = self.readline()
                if initial is None:
                    return
            raw = b64d(initial.strip())
            if raw is None:
                self.st.bump(self.st.auth_fail, mech)
                self.send("501 5.5.2 Cannot decode response")
                return
            fields = raw.split(b"\0")
            if len(fields) != 3:
                self.st.bump(self.st.auth_fail, mech)
                self.log("   PLAIN payload has %d NUL-separated fields, expected 3: %r",
                         len(fields), raw)
                self.send("501 5.5.2 Malformed PLAIN response")
                return
            authzid = fields[0].decode("utf-8", "replace")
            user = fields[1].decode("utf-8", "replace")
            password = fields[2].decode("utf-8", "replace")
            self.log("   PLAIN decoded: authzid=%r %s", authzid,
                     self.cred_note(user, password))
            ok, why = self.check_plain(user, password, mech)
            self.finish_auth(mech, user, ok, why)
            return

        if mech == "LOGIN":
            if initial is None:
                self.send("334 %s" % b64e("Username:"))
                line = self.readline()
                if line is None:
                    return
            else:
                line = initial
            raw = b64d(line.strip())
            if raw is None:
                self.st.bump(self.st.auth_fail, mech)
                self.send("501 5.5.2 Cannot decode response")
                return
            user = raw.decode("utf-8", "replace")
            self.send("334 %s" % b64e("Password:"))
            line = self.readline()
            if line is None:
                return
            raw = b64d(line.strip())
            if raw is None:
                self.st.bump(self.st.auth_fail, mech)
                self.send("501 5.5.2 Cannot decode response")
                return
            password = raw.decode("utf-8", "replace")
            self.log("   LOGIN decoded: %s", self.cred_note(user, password))
            ok, why = self.check_plain(user, password, mech)
            self.finish_auth(mech, user, ok, why)
            return

        if mech == "CRAM-MD5":
            challenge = "<%d.%d@%s>" % (random.randint(10000, 99999),
                                        int(time.time()), self.a.hostname)
            self.log("   CRAM-MD5 challenge (cleartext): %s", challenge)
            self.send("334 %s" % b64e(challenge))
            line = self.readline()
            if line is None:
                return
            raw = b64d(line.strip())
            if raw is None:
                self.st.bump(self.st.auth_fail, mech)
                self.send("501 5.5.2 Cannot decode response")
                return
            text = raw.decode("utf-8", "replace")
            bits = text.rsplit(" ", 1)
            if len(bits) != 2:
                self.st.bump(self.st.auth_fail, mech)
                self.log("   CRAM-MD5 response is not '<user> <digest>': %r", text)
                self.send("501 5.5.2 Malformed CRAM-MD5 response")
                return
            user, digest = bits[0], bits[1]
            self.log("   CRAM-MD5 decoded: user=%r digest=%s", user, digest)
            ok, why = self.check_cram(user, digest, challenge)
            self.finish_auth(mech, user, ok, why)
            return

        # advertised but not implemented here
        self.st.bump(self.st.auth_fail, mech)
        self.send("504 5.5.4 Unrecognized authentication type")

    def finish_auth(self, mech, user, ok, why):
        if ok:
            self.authed_as = user
            self.st.bump(self.st.auth_ok, mech)
            self.log("** AUTH %s SUCCEEDED for user=%r", mech, user)
            self.send("235 2.7.0 Authentication successful")
        else:
            self.st.bump(self.st.auth_fail, mech)
            self.log("** AUTH %s FAILED for user=%r -- %s", mech, user, why)
            self.send("535 5.7.8 Authentication credentials invalid")

    # -- main loop ----------------------------------------------------------
    def run(self):
        self.send("220 %s ESMTP ck-smtpsrv ready" % self.a.hostname)
        while True:
            line = self.readline()
            if line is None:
                self.log("   (peer closed)")
                return
            if not line.strip():
                self.send("500 5.5.2 Error: bad syntax")
                continue
            bits = line.split(None, 1)
            verb = bits[0].upper()
            arg = bits[1] if len(bits) > 1 else ""

            if verb == "EHLO":
                self.st.ehlo += 1
                self.send("250-%s" % self.a.hostname)
                self.send("250-PIPELINING")
                self.send("250-SIZE 10240000")
                if self.a.mechs:
                    mechlist = " ".join(sorted(self.a.mechs))
                    self.send("250-AUTH %s" % mechlist)
                    self.send("250-AUTH=%s" % mechlist)   # the old Outlook-era form
                self.send("250 HELP")
            elif verb == "HELO":
                self.st.helo += 1
                self.send("250 %s" % self.a.hostname)
            elif verb == "AUTH":
                self.do_auth(arg)
            elif verb == "MAIL":
                self.st.mail_from += 1
                if self.a.require_auth and not self.authed_as:
                    self.st.mail_from_denied += 1
                    self.st.no_auth_sessions += 1
                    self.log("** MAIL FROM with NO successful AUTH -- refusing (530)")
                    self.send("530 5.7.0 Authentication required")
                    continue
                if not self.authed_as:
                    self.st.no_auth_sessions += 1
                    self.log("** MAIL FROM with NO AUTH (accepted: --require-auth is off)")
                self.mailfrom = arg
                self.send("250 2.1.0 Ok")
            elif verb == "RCPT":
                if self.a.require_auth and not self.authed_as:
                    self.send("530 5.7.0 Authentication required")
                    continue
                self.rcpt.append(arg)
                self.send("250 2.1.5 Ok")
            elif verb == "DATA":
                if self.a.require_auth and not self.authed_as:
                    self.send("530 5.7.0 Authentication required")
                    continue
                self.send("354 End data with <CR><LF>.<CR><LF>")
                body = []
                while True:
                    dl = self.readline()
                    if dl is None:
                        return
                    if dl == ".":
                        break
                    body.append(dl[1:] if dl.startswith("..") else dl)
                self.st.messages += 1
                self.send("250 2.0.0 Ok: queued as ck%06d" % self.st.messages)
                if self.a.maildir:
                    path = os.path.join(self.a.maildir,
                                        "msg-%03d.eml" % self.st.messages)
                    with open(path, "w") as f:
                        f.write("X-ck-peer: %s\n" % (self.peer,))
                        f.write("X-ck-authenticated-as: %s\n" % (self.authed_as,))
                        f.write("X-ck-mail-from: %s\n" % (self.mailfrom,))
                        f.write("X-ck-rcpt-to: %s\n" % ("; ".join(self.rcpt),))
                        f.write("\n")
                        f.write("\n".join(body) + "\n")
                    self.log("** message %d stored at %s (%d body lines)",
                             self.st.messages, path, len(body))
            elif verb == "RSET":
                self.mailfrom = None
                self.rcpt = []
                self.send("250 2.0.0 Ok")
            elif verb == "NOOP":
                self.send("250 2.0.0 Ok")
            elif verb == "STARTTLS":
                self.send("454 4.7.0 TLS not available on this instrument")
            elif verb == "QUIT":
                self.st.quit += 1
                self.send("221 2.0.0 Bye")
                return
            else:
                self.send("502 5.5.2 Error: command not recognized")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--port", type=int, default=11025)
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--hostname", default="ck-smtp")
    ap.add_argument("--user", action="append", default=[])
    ap.add_argument("--mech", action="append", default=[])
    ap.add_argument("--require-auth", action="store_true")
    ap.add_argument("--reject-auth", action="store_true")
    ap.add_argument("--show-secrets", action="store_true")
    ap.add_argument("--maildir")
    ap.add_argument("--log")
    ap.add_argument("--seconds", type=int, default=0)
    ap.add_argument("--stopfile")
    ap.add_argument("--pidfile")
    a = ap.parse_args()

    known = {"PLAIN", "LOGIN", "CRAM-MD5"}
    if not a.mech:
        a.mechs = set(known)
    elif len(a.mech) == 1 and a.mech[0].lower() == "none":
        a.mechs = set()
    else:
        a.mechs = set()
        for m in a.mech:
            mm = m.strip().upper()
            if mm not in known:
                sys.stderr.write("smtpsrv: unknown --mech %r (want %s or none)\n"
                                 % (m, "/".join(sorted(known))))
                return EXIT_ARGS
            a.mechs.add(mm)

    a.users = {}
    for u in a.user:
        if ":" not in u:
            sys.stderr.write("smtpsrv: --user wants NAME:PASSWORD, got %r\n" % u)
            return EXIT_ARGS
        name, _, pw = u.partition(":")
        a.users[name] = pw

    if a.port < 1024 and os.geteuid() != 0:
        sys.stderr.write("smtpsrv: port %d needs root; use >= 1024 "
                         "(STANDING-ORDERS s4)\n" % a.port)
        return EXIT_ARGS

    if a.maildir:
        try:
            os.makedirs(a.maildir)
        except OSError:
            pass

    log = Log(a.log)
    stats = Stats()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((a.bind, a.port))
    srv.listen(5)
    srv.settimeout(1.0)

    if a.pidfile:
        with open(a.pidfile, "w") as f:
            f.write("%d\n" % os.getpid())

    log("smtpsrv listening on %s:%d hostname=%s", a.bind, a.port, a.hostname)
    log("  advertising AUTH: %s",
        " ".join(sorted(a.mechs)) if a.mechs else "(none -- no AUTH line in EHLO)")
    log("  known users: %s", ", ".join(sorted(a.users)) or "(none -- every credential is wrong)")
    log("  require-auth=%s reject-auth=%s", a.require_auth, a.reject_auth)

    t_end = time.time() + a.seconds if a.seconds else None
    try:
        while True:
            if t_end and time.time() >= t_end:
                log("smtpsrv: --seconds reached")
                break
            if a.stopfile and os.path.exists(a.stopfile):
                log("smtpsrv: stopfile %s appeared", a.stopfile)
                break
            try:
                conn, peer = srv.accept()
            except socket.timeout:
                continue
            stats.connections += 1
            log("=== connection %d from %s:%d ===", stats.connections, peer[0], peer[1])
            conn.settimeout(30.0)
            try:
                Session(conn, "%s:%d" % (peer[0], peer[1]), a, log, stats).run()
            except (socket.error, OSError) as e:
                log("   (socket error: %s)", e)
            finally:
                try:
                    conn.close()
                except OSError:
                    pass
            log("=== connection %d closed ===", stats.connections)
    except KeyboardInterrupt:
        log("smtpsrv: interrupted")
    finally:
        srv.close()

    log("SUMMARY connections=%d ehlo=%d helo=%d mail_from=%d mail_from_denied=%d "
        "messages=%d quit=%d sessions_without_auth=%d",
        stats.connections, stats.ehlo, stats.helo, stats.mail_from,
        stats.mail_from_denied, stats.messages, stats.quit, stats.no_auth_sessions)
    for mech in sorted(stats.auth_attempts):
        log("SUMMARY auth mech=%s attempts=%d ok=%d fail=%d",
            mech, stats.auth_attempts[mech],
            stats.auth_ok.get(mech, 0), stats.auth_fail.get(mech, 0))
    if not stats.auth_attempts:
        log("SUMMARY auth: NO AUTH verb was ever sent by any client")
    if stats.auth_unknown:
        log("SUMMARY auth: client asked for mechanism(s) we do not offer: %s",
            ", ".join(stats.auth_unknown))
    if a.pidfile:
        try:
            os.unlink(a.pidfile)
        except OSError:
            pass
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
