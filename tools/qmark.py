#!/usr/bin/env python3
"""qmark.py <tty> <baud> <transcript> [--mode CMD ... --] PREFIX [PREFIX ...]
Read-only CLI help probe: for each PREFIX, type "PREFIX ?" WITHOUT a carriage return,
print what the CLI offers, then kill the line with Ctrl-U (AW+ "delete line").  A
self-test ("show clock ?" -> Ctrl-U -> CR must NOT print the clock) runs first and
aborts the whole run if the line-kill does not work, so no probed command is ever
executed (memory never-send-cli-help-through-a-cr-driver).  --mode commands (e.g.
"configure terminal", "interface port1.0.1") are sent normally, and the session is
returned to exec with `end` at the close.
<tty> is the unit's console device on the testbox you run it on; <transcript> is a path you
choose. Env: CK_USER / CK_PASSWORD = login credentials (default manager / friend)."""
import os, sys, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
USAGE = "usage: qmark.py <tty> <baud> <transcript> [--mode CMD ... --] PREFIX [PREFIX ...]"
if len(sys.argv) < 4 or sys.argv[1] in ("-h", "--help"):
    print(USAGE); sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
try:
    tty, baud, transcript = sys.argv[1], int(sys.argv[2]), sys.argv[3]
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
rest = sys.argv[4:]
modes = []
if rest and rest[0] == "--mode":
    if "--" not in rest:
        print(USAGE); print("bad argument: --mode needs a closing --"); sys.exit(2)
    i = rest.index("--"); modes = rest[1:i]; rest = rest[i+1:]
prefixes = rest
import console
c = console.Console(tty, transcript, baud=baud)

def expect(pats, timeout):
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

LOGIN, PASSWD, PRIV, USER, NEWPW, BAD = (r"login:\s*$", r"Password:\s*$", r"#\s*$", r">\s*$", r"new password", r"Login incorrect")
def login():
    expect([r"$^"], 0.5); c.s.write(b"\r")
    for _ in range(5):
        p, out = expect([LOGIN, PASSWD, PRIV, USER, NEWPW], 15)
        if p is None: c.s.write(b"\r"); continue
        if p == NEWPW: raise SystemExit("forced password-change dialog; refusing")
        if p == LOGIN:
            c.s.write((console.USERNAME + "\r").encode())
            if expect([PASSWD], 10)[0] is None: continue
            c.s.write((console.PASSWORD + "\r").encode())
            p3, _ = expect([PRIV, USER, BAD, NEWPW], 25)
            if p3 in (None, BAD): continue
            if p3 == NEWPW: raise SystemExit("forced password-change dialog")
            if p3 == USER: c.s.write(b"enable\r"); expect([PRIV], 15)
            break
        if p == PASSWD:
            c.s.write((console.PASSWORD + "\r").encode()); expect([PRIV, USER, BAD, LOGIN], 25); c.s.write(b"\r"); continue
        if p == USER: c.s.write(b"enable\r"); expect([PRIV], 15)
        break
    c.s.write(b"\r")
    if expect([PRIV], 8)[0] is None: raise SystemExit("no privileged prompt")
    c.cmd("terminal length 0", timeout=15.0); c.cmd("terminal no monitor", timeout=15.0); c.monitor = False

def qmark(prefix):
    c._t.write("\n>>> {} ?   (no CR)\n".format(prefix))
    c.s.write((prefix + " ?").encode())
    _, out = expect([r"#\s*" + re.escape(prefix) + r" ?\s*$"], 6)   # help ends with the re-echoed line
    time.sleep(0.4); out += expect([r"$^"], 0.3)[1]
    c.s.write(b"\x15")                      # Ctrl-U: delete the line
    time.sleep(0.5); expect([r"$^"], 0.3)
    return out

ok = False
try:
    login(); ok = True
    # self-test: the line-kill must leave nothing to execute
    st = qmark("show clock")
    c.s.write(b"\r"); _, after = expect([PRIV], 5)
    # A clock time is the general tell; "UTC"/"NZ" are timezone names `show clock` prints
    # (NZ from the bench it was written on). Extra names only make the abort more cautious.
    if re.search(r"\d\d:\d\d:\d\d", after) or "UTC" in after or "NZ" in after:
        print("!!! SELF-TEST FAILED: Ctrl-U did not clear the line (clock output seen) -- aborting")
        print(after); sys.exit(3)
    print("self-test OK: 'show clock ?' then Ctrl-U then CR executed nothing")
    for m in modes:
        out = c.cmd(m, timeout=30.0); print("{} >>> {}".format(time.strftime("%H:%M:%S"), m)); print(out)
        if any(l.lstrip().startswith("%") for l in out.splitlines()):
            print("!!! mode command refused -- stopping"); sys.exit(2)
    for p in prefixes:
        out = qmark(p)
        print("{} >>> {} ?".format(time.strftime("%H:%M:%S"), p)); print(out)
        c.s.write(b"\r"); expect([PRIV], 5)    # fresh prompt, line is empty after Ctrl-U
finally:
    if ok:
        try:
            raw = c.send("", timeout=5.0)
            if "(config" in raw: c.cmd("end", timeout=15.0)
            c.cmd("terminal no monitor", timeout=15.0)
        except Exception as e: print("cleanup:", e)
    c.close()
