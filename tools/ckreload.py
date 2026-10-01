#!/usr/bin/env python3
"""ckreload.py <tty> <baud> <transcript> [wait_s]: with the console ALREADY at a privileged
`#` prompt (it does not log in -- it refuses otherwise; log in first, e.g. with ckcon.py),
send `reload`, answer y ONLY to a reboot/reload (y/n) and n to any save-config (y/n), then
read the console until `login:` appears (or wait_s). Every byte goes to the transcript.
<tty> is the AW+ unit's console device (e.g. /dev/uN on a testbox); <transcript> is a path
you choose. wait_s defaults to 720 s, measured on IE520 (slow SPIFlash boot); other
products may need a different value. Exit 0 = login seen, 1 = not at `#`, 3 = unknown
(y/n), 4 = no login within wait_s."""
import os, sys, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
USAGE = "usage: ckreload.py <tty> <baud> <transcript> [wait_s (default 720)]"
if sys.argv[1:2] in (["-h"], ["--help"]):
    print(USAGE); print(__doc__); sys.exit(0)
if not 4 <= len(sys.argv) <= 5:
    print(USAGE); sys.exit(2)
try:
    tty, baud, tr = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    wait = float(sys.argv[4]) if len(sys.argv) > 4 else 720
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
import console
c = console.Console(tty, tr, baud=baud)
def expect(pats, timeout):
    buf = ""; t0 = time.time()
    while time.time() - t0 < timeout:
        b = c.s.read(4096)
        if b:
            s = b.decode(errors="replace"); c._t.write(s); buf += s
            for p in pats:
                if re.search(p, buf[-600:], re.I): return p, buf
        else: time.sleep(0.05)
    return None, buf
expect([r"$^"], 0.5); c.s.write(b"\r")
p, _ = expect([r"#\s*$", r"login:\s*$"], 10)
if p != r"#\s*$": sys.exit("not at a privileged prompt (p=%r); refusing" % p)
if not c.monitor_off(): sys.exit("cannot reach exec / terminal no monitor refused; refusing to reload")
t0 = time.time(); print(time.strftime("%T"), ">>> reload"); c.s.write(b"reload\r")
YN = r"\(y/n\)\s*:?\s*$"
for _ in range(3):
    p, out = expect([YN, r"going down|Restarting|U-Boot|Bootloader"], 60)
    if p != YN: break
    q = out.replace("\r", "").strip().splitlines()[-1]
    if re.search(r"save|modified|changed", q, re.I):
        print("save question:", repr(q), "-> n"); c.s.write(b"n\r")
    elif re.search(r"reboot|reload|restart", q, re.I):
        print("reboot question:", repr(q), "-> y"); c.s.write(b"y\r")
    else:
        print("unknown question:", repr(q), "-> n, stopping"); c.s.write(b"n\r"); sys.exit(3)
p, out = expect([r"login:\s*$"], wait)
print(time.strftime("%T"), "login seen" if p else "NO login within %ds" % wait, "after %.0f s" % (time.time() - t0))
c.close(); sys.exit(0 if p else 4)
