"""Shared AW+ login/expect for the console drivers (same prompt-waiting login as ckcon.py).

Library, not a command: `import console, awlogin as L` from a sibling script, then
    c = console.Console(tty, transcript, baud=baud); ok = L.login(c)
Credentials default to console.USERNAME / console.PASSWORD (manager/friend unless the
env vars CK_USER / CK_PASSWORD are set), or pass login(c, username=..., password=...)."""
import os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console

LOGIN, PASSWD, PRIV, USER, NEWPW, BAD = (r"login:\s*$", r"Password:\s*$", r"#\s*$", r">\s*$",
                                         r"new password", r"Login incorrect")
YN = r"\(y/n\)\s*:?\s*$"


def expect(c, pats, timeout):
    buf = ""; t0 = time.time()
    while time.time() - t0 < timeout:
        b = c.s.read(4096)
        if b:
            s = b.decode(errors="replace"); c._t.write(s); buf += s
            for p in pats:
                if re.search(p, buf[-400:]):
                    return p, buf
        else:
            time.sleep(0.05)
    return None, buf


def _type(c, data, baud_floor=19200, per_char=0.02):
    """Write a line, slowly on a slow console.

    At 9600 a single fast write of a username is TRUNCATED on the wire: the device
    echoed `ma`, then `manag`, and went straight to `Password:` (tb277, 2026-10-21).
    The password that followed was then evaluated against a mangled username and
    failed, which is how a CORRECT credential produced a login failure.
    """
    if c.s.baudrate and c.s.baudrate < baud_floor:
        for i in range(len(data)):
            c.s.write(data[i:i + 1]); time.sleep(per_char)
    else:
        c.s.write(data)


def _echo_truncated(user, buf):
    """True only when a PROPER PREFIX of the username came back and the whole did not.

    A console with echo switched off returns neither, and must not be mistaken for
    a truncation, so "no echo at all" is reported as False (cannot tell -> proceed).
    """
    u = user.decode(errors="replace")
    if u in buf:
        return False
    return any(u[:n] in buf for n in range(len(u) - 1, 0, -1))


def login(c, tries=5, username=None, password=None, cred_attempts=1):
    """Log the console in.  Returns True once at a privileged prompt.

    `tries` bounds PROMPT NAVIGATION only (bare CRs, `enable`, an already-open
    session) -- none of which costs an authentication attempt.

    `cred_attempts` bounds how many times a username+password is actually
    SUBMITTED, and it defaults to ONE.  That is the whole point of this function's
    shape: **AW+ locks an account at five failed logins, and every further failure
    re-arms the five-minute timer**, so a lock cannot expire while anything retries.
    This function used to loop `tries=5` times re-sending a full credential on every
    rejection -- a retry count exactly equal to the lockout threshold -- and it
    locked a partner switch mid-campaign (tb277 swi_b, 2026-10-21, five attempts in
    forty seconds).  A credential is evidence, not a dice roll: if it is rejected,
    say so and stop.  Raise `cred_attempts` only with a reason.
    """
    user = (console.USERNAME if username is None else username).encode()
    pw = (console.PASSWORD if password is None else password).encode()
    used = 0                                    # credentials actually submitted
    expect(c, [r"$^"], 0.5)
    c.s.write(b"\r")
    for _ in range(tries):
        p, out = expect(c, [LOGIN, PASSWD, PRIV, USER, NEWPW], 15)
        if p is None:
            c.s.write(b"\r"); continue
        if p == NEWPW:
            raise SystemExit("forced password-change dialog; refusing")
        if p == LOGIN:
            if used >= cred_attempts:
                return False                    # never re-type a credential
            _type(c, user + b"\r")
            p2, buf = expect(c, [PASSWD], 10)
            if p2 is None:
                continue                        # no password prompt: nothing was submitted
            if _echo_truncated(user, buf):
                return False                    # a mangled username would fail and COUNT
            used += 1
            c.s.write(pw + b"\r")
            p3, _ = expect(c, [PRIV, USER, BAD, NEWPW], 25)
            if p3 == BAD:
                return False                    # evaluated and rejected: an answer, not a retry
            if p3 is None:
                return False                    # desynced AFTER submitting: do not submit again
            if p3 == NEWPW: raise SystemExit("forced password-change dialog")
            if p3 == USER: c.s.write(b"enable\r"); expect(c, [PRIV], 15)
            break
        if p == PASSWD:
            if used >= cred_attempts:
                return False
            used += 1
            c.s.write(pw + b"\r")
            p4, _ = expect(c, [PRIV, USER, BAD, LOGIN], 25)
            if p4 in (None, BAD, LOGIN):
                return False                    # rejected, or dropped back to `login:`
            c.s.write(b"\r"); continue
        if p == USER:
            c.s.write(b"enable\r"); expect(c, [PRIV], 15)
        break
    c.s.write(b"\r")
    if expect(c, [PRIV], 8)[0] is None:
        return False
    if not c.to_exec():             # a parked host(config)# prompt -> end first
        return False
    c.cmd("terminal length 0", timeout=15.0)
    return c.monitor_off()          # exec-only; console.py set_monitor()


def stamp():
    t = time.time()
    return "%.3f %s" % (t, time.strftime("%H:%M:%S", time.localtime(t)))


if __name__ == "__main__":
    # A library: running it directly only explains how to use it.
    print("usage: import console, awlogin as L  (library; run a driver such as cfg.py instead)")
    sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
