#!/usr/bin/env python3
"""netlogin.py -- log in to a device over TELNET or SSH and report what the login did.

The console drivers in this directory (console.py, conlogin.py, ckcon.py ...) drive a serial
console.  This one is their network twin: it opens a TCP session to a device's telnet or ssh
server, authenticates with a username and password, and prints EVERY byte the device sent
during the login -- banner included -- before running any commands.

That full login transcript is the point.  A case about a login-time message (a MOTD, a login
banner, a "default password needs to be changed" warning, an expiry warning) cannot be graded
from a `show` command: the message exists only in the bytes a real login receives, and it
differs between the console, telnet, ssh and http paths.  A refused login is a first-class
result here, not an error.

No third-party modules: telnet is a raw socket with minimal IAC handling (every option is
refused), ssh is the system `ssh` client driven through a pty.

Usage:
  netlogin.py --proto telnet|ssh --host H [--port N] --user U --password P
              [--transcript FILE] [--timeout S] [--login-timeout S]
              [--cmd CMD]... [--no-logout] [--expect priv|user|fail]

Exit codes:
  0  logged in and reached a privileged '#' prompt   (or --expect matched)
  1  logged in and reached an unprivileged '>' prompt
  2  the device refused the credentials
  3  nothing recognisable within the timeout
  4  the transport failed (connection refused, no route, ssh exited)
  5  --expect was given and the outcome did not match
  6  usage error
"""

import argparse
import errno
import os
import pty
import re
import select
import signal
import socket
import sys
import time

# ---------------------------------------------------------------- prompt grammar

LOGIN_RE = re.compile(rb"(?:^|\n)[^\r\n]*(?:[Ll]ogin|[Uu]sername)\s*:\s*$")
PASSWORD_RE = re.compile(rb"[Pp]assword\s*:\s*$")
PRIV_RE = re.compile(rb"(?:^|\n)[\w .:\-/\[\]()@]+#\s*$")
USER_RE = re.compile(rb"(?:^|\n)[\w .:\-/\[\]()@]+>\s*$")
FAIL_RE = re.compile(
    rb"Login incorrect|Permission denied|Authentication failed|"
    rb"Too many authentication failures|Access denied|"
    rb"Account locked|maximum number of login attempts",
    re.I,
)
# A pager page-break.  AW+ uses '--More--'; we answer it with a space.
MORE_RE = re.compile(rb"--\s*More\s*--")


class Transport(object):
    """Common interface: send(bytes), recv(timeout) -> bytes or None, close()."""

    def send(self, data):
        raise NotImplementedError

    def recv(self, timeout):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


# ---------------------------------------------------------------- telnet

IAC, DONT, DO, WONT, WILL, SB, SE = (255, 254, 253, 252, 251, 250, 240)


class TelnetTransport(Transport):
    """Raw-socket telnet.  Every option the server offers is refused, which is enough for
    an AW+ telnet server and keeps the byte stream clean for the caller to read."""

    def __init__(self, host, port, timeout):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.setblocking(False)
        self._pending = b""

    def send(self, data):
        self.sock.setblocking(True)
        self.sock.sendall(data)
        self.sock.setblocking(False)

    def _strip_iac(self, buf):
        """Remove telnet commands from buf, answering each one.  Returns clean data."""
        out = bytearray()
        i = 0
        n = len(buf)
        while i < n:
            b = buf[i]
            if b != IAC:
                out.append(b)
                i += 1
                continue
            if i + 1 >= n:
                self._pending = bytes(buf[i:])   # split IAC; keep for next read
                return bytes(out)
            cmd = buf[i + 1]
            if cmd == IAC:                       # escaped 0xff
                out.append(IAC)
                i += 2
            elif cmd in (DO, DONT, WILL, WONT):
                if i + 2 >= n:
                    self._pending = bytes(buf[i:])
                    return bytes(out)
                opt = buf[i + 2]
                # refuse everything: DO -> WONT, WILL -> DONT
                reply = WONT if cmd == DO else (DONT if cmd == WILL else None)
                if reply is not None:
                    try:
                        self.send(bytes([IAC, reply, opt]))
                    except OSError:
                        pass
                i += 3
            elif cmd == SB:
                end = buf.find(bytes([IAC, SE]), i)
                if end == -1:
                    self._pending = bytes(buf[i:])
                    return bytes(out)
                i = end + 2
            else:
                i += 2
        return bytes(out)

    def recv(self, timeout):
        r, _, _ = select.select([self.sock], [], [], timeout)
        if not r:
            return None
        try:
            chunk = self.sock.recv(4096)
        except OSError as exc:
            if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return b""
            raise
        if not chunk:
            return None if not self._pending else b""
        buf = self._pending + chunk
        self._pending = b""
        return self._strip_iac(buf)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


# ---------------------------------------------------------------- ssh

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",      # writes no trust anywhere
    "-o", "GlobalKnownHostsFile=/dev/null",
    "-o", "PubkeyAuthentication=no",
    "-o", "PreferredAuthentications=keyboard-interactive,password",
    "-o", "NumberOfPasswordPrompts=1",
    "-o", "LogLevel=ERROR",
]


class SshTransport(Transport):
    """The system ssh client, driven through a pty so it asks us for the password."""

    def __init__(self, host, port, user, timeout):
        argv = ["ssh"] + SSH_OPTS + ["-p", str(port), "%s@%s" % (user, host)]
        pid, fd = pty.fork()
        if pid == 0:
            os.environ["TERM"] = "dumb"
            try:
                os.execvp("ssh", argv)
            finally:
                os._exit(127)
        self.pid = pid
        self.fd = fd
        self.argv = argv

    def send(self, data):
        os.write(self.fd, data)

    def recv(self, timeout):
        r, _, _ = select.select([self.fd], [], [], timeout)
        if not r:
            return None
        try:
            chunk = os.read(self.fd, 4096)
        except OSError:
            return None
        return chunk or None

    def close(self):
        try:
            os.close(self.fd)
        except OSError:
            pass
        try:
            os.kill(self.pid, signal.SIGTERM)
        except OSError:
            pass
        try:
            os.waitpid(self.pid, os.WNOHANG)
        except OSError:
            pass


# ---------------------------------------------------------------- the session

class Session(object):
    def __init__(self, transport, transcript=None):
        self.t = transport
        self.buf = b""
        self.all = bytearray()
        self.tr = open(transcript, "ab") if transcript else None

    def _record(self, data):
        self.all.extend(data)
        if self.tr:
            self.tr.write(data)
            self.tr.flush()

    def read_until(self, patterns, timeout):
        """Read until one of (name, regex) matches the tail of the buffer.
        Returns (name, text_since_last_match).  (None, text) on timeout."""
        start = time.time()
        got = bytearray()
        while True:
            left = timeout - (time.time() - start)
            if left <= 0:
                self.buf = b""
                return None, bytes(got)
            chunk = self.t.recv(min(left, 0.5))
            if chunk is None and not select_alive(self.t):
                self.buf = b""
                return "EOF", bytes(got)
            if chunk:
                self._record(chunk)
                got.extend(chunk)
                self.buf += chunk
                if MORE_RE.search(self.buf[-40:]):
                    self.t.send(b" ")
                    self.buf = b""
                    continue
                tail = self.buf[-400:]
                for name, rx in patterns:
                    if rx.search(tail):
                        self.buf = b""
                        return name, bytes(got)

    def send_line(self, text):
        data = text.encode("utf-8", "replace") + b"\r"
        self._record(b"<<< " + data + b"\n")
        self.t.send(data)

    def close(self):
        if self.tr:
            self.tr.close()
        self.t.close()


def select_alive(t):
    """True while the transport might still deliver bytes."""
    if isinstance(t, SshTransport):
        try:
            pid, _ = os.waitpid(t.pid, os.WNOHANG)
            return pid == 0
        except OSError:
            return False
    return True


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--proto", required=True, choices=["telnet", "ssh"])
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--transcript", default=None)
    ap.add_argument("--timeout", type=float, default=30.0,
                    help="per-command read timeout (default 30 s)")
    ap.add_argument("--login-timeout", type=float, default=40.0,
                    help="seconds to wait for the login to resolve (default 40 s; a method "
                         "list with an unreachable RADIUS server can take 25.5 s)")
    ap.add_argument("--cmd", action="append", default=[],
                    help="a command to run after login; repeatable")
    ap.add_argument("--no-logout", action="store_true")
    ap.add_argument("--expect", choices=["priv", "user", "fail"], default=None)
    args = ap.parse_args()

    port = args.port or (23 if args.proto == "telnet" else 22)

    try:
        if args.proto == "telnet":
            tp = TelnetTransport(args.host, port, timeout=10)
        else:
            tp = SshTransport(args.host, port, args.user, timeout=10)
    except OSError as exc:
        print("TRANSPORT FAILED: %s %s:%d -- %s" % (args.proto, args.host, port, exc))
        return 4

    s = Session(tp, args.transcript)
    t0 = time.time()
    # FAIL is tested FIRST: a refused AW+ login prints "Login incorrect" and then re-presents
    # "<host> login:", so a list that tested the login prompt first graded a real refusal as
    # UNKNOWN (measured on tb277 2026-10-20, T33378's bad-credential control).
    pats = [("fail", FAIL_RE), ("login", LOGIN_RE), ("password", PASSWORD_RE),
            ("priv", PRIV_RE), ("user", USER_RE)]
    # After the password has been sent, a fresh "login:" prompt IS the refusal (telnet), and so
    # is a fresh password prompt: the ssh client re-prompts up to three times, so
    # "<user>@<host>'s password:" coming back is ssh's way of saying the credential was rejected.
    # Grading that as UNKNOWN cost a control its verdict on tb277 2026-10-20 (T33411, the
    # wrong-shared-key leg: the login really had failed and the tool would not say so).
    # Caveat: a device that forces a password change at first login also re-prompts, but with
    # "Enter new password:", which FAIL_RE/PASSWORD_RE do not match in that wording.
    post_pats = [("fail", FAIL_RE), ("priv", PRIV_RE), ("user", USER_RE),
                 ("relogin", LOGIN_RE), ("repassword", PASSWORD_RE)]

    print("=== %s %s:%d as %s ===" % (args.proto, args.host, port, args.user))

    # ssh is given the username on the command line, so it may go straight to Password:.
    name, pre = s.read_until(pats, args.login_timeout)
    print("--- bytes before the username prompt ---")
    sys.stdout.write(pre.decode("utf-8", "replace"))
    if not pre.endswith(b"\n"):
        print()

    if name == "login":
        s.send_line(args.user)
        name, mid = s.read_until(pats, args.login_timeout)
        print("--- bytes between username and password prompt ---")
        sys.stdout.write(mid.decode("utf-8", "replace"))
        if not mid.endswith(b"\n"):
            print()

    if name == "password":
        s.send_line(args.password)
        name, post = s.read_until(post_pats, args.login_timeout)
        print("--- bytes after the password was sent (THE LOGIN BANNER) ---")
        sys.stdout.write(post.decode("utf-8", "replace"))
        if not post.endswith(b"\n"):
            print()

    secs = round(time.time() - t0, 1)
    outcome = {"priv": "PRIV", "user": "USER", "fail": "FAIL", "relogin": "FAIL",
               "repassword": "FAIL", "EOF": "EOF", None: "TIMEOUT"}.get(name, "UNKNOWN")
    print("LOGIN RESULT: %s  proto=%s  user=%s  seconds=%s" %
          (outcome, args.proto, args.user, secs))

    rc = {"PRIV": 0, "USER": 1, "FAIL": 2}.get(outcome, 3)
    if outcome in ("EOF", "TIMEOUT", "UNKNOWN"):
        rc = 3 if outcome != "EOF" else 4

    if outcome in ("PRIV", "USER") and args.cmd:
        s.send_line("terminal length 0")
        s.read_until([("priv", PRIV_RE), ("user", USER_RE)], args.timeout)
        for cmd in args.cmd:
            print("=== CMD: %s ===" % cmd)
            s.send_line(cmd)
            nm, out = s.read_until([("priv", PRIV_RE), ("user", USER_RE)], args.timeout)
            sys.stdout.write(out.decode("utf-8", "replace"))
            if not out.endswith(b"\n"):
                print()
            if nm is None:
                print("!! no prompt within %.0f s after [%s]" % (args.timeout, cmd))

    if outcome in ("PRIV", "USER") and not args.no_logout:
        s.send_line("exit")
        time.sleep(0.5)

    s.close()

    if args.expect:
        want = {"priv": "PRIV", "user": "USER", "fail": "FAIL"}[args.expect]
        if outcome != want:
            print("EXPECT MISMATCH: wanted %s, got %s" % (want, outcome))
            return 5
        return 0
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
