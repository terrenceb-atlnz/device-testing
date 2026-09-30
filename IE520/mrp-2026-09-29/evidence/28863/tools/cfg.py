#!/usr/bin/env python3
"""cfg.py <tty> <baud> <transcript> CMD [CMD ...]
Config/show driver for the T28863 ring. Completion = a prompt AFTER the echo
(console.send_until_prompt), so async 'switch: port ... entered ... state' lines printed
after the prompt do not stall it. A CMD prefixed "YN:" must prompt (y/n) and is answered
y+CR. Stops at the first "% " line, an unexpected (y/n) (answered n) or a missing prompt.
Always leaves the console at exec (`end`) with terminal no monitor."""
import re, sys, time
sys.path.insert(0, "/tmp/ck15")
import console, ck15lib as L
tty, baud, tr = sys.argv[1], int(sys.argv[2]), sys.argv[3]
cmds = sys.argv[4:]
c = console.Console(tty, tr, baud=baud)
rc = 0; ok = False
try:
    ok = L.login(c)
    if not ok:
        print("no privileged prompt"); rc = 7
    else:
        raw = c.send_until_prompt("", timeout=10.0)
        if "(config" in raw:
            print("%s console was parked in config mode: %r -- sending end" % (L.stamp(), raw.strip()[-40:]))
            c.send_until_prompt("end", timeout=15.0)
            c.cmd("terminal length 0", timeout=15.0); c.cmd("terminal no monitor", timeout=15.0)
    for line in (cmds if ok else []):
        yn = line.startswith("YN:"); cmd = line[3:] if yn else line
        L.expect(c, [r"$^"], 0.2)
        if yn:
            c._t.write('\n>>> {}\n'.format(cmd))
            c.s.write((cmd + "\r").encode())
            p, out = L.expect(c, [L.YN], 60)
            if p is None:
                print(out); print("!!! expected (y/n), none came -- stopping"); rc = 6; break
            c.s.write(b"y\r")
            out += c.send_until_prompt("", timeout=120)
        else:
            out = c.send_until_prompt(cmd, timeout=90)
            if not c.last_prompt_seen:
                if re.search(L.YN, out[-200:]):
                    c.s.write(b"n\r"); out += c.send_until_prompt("", timeout=30)
                    print("%s >>> %s\n%s" % (L.stamp(), cmd, out)); print("!!! unexpected (y/n) -- declined"); rc = 3; break
                print("%s >>> %s\n%s" % (L.stamp(), cmd, out)); print("!!! no prompt within 90 s -- stopping"); rc = 5; break
        print("%s >>> %s" % (L.stamp(), cmd))
        print(out.replace("\r", ""))
        if any(l.lstrip().startswith("%") for l in out.replace("\r", "").splitlines()):
            print("!!! CLI error on {!r} -- stopping".format(cmd)); rc = 2; break
finally:
    if ok:
        try:
            raw = c.send_until_prompt("", timeout=10.0)
            if "(config" in raw:
                c.send_until_prompt("end", timeout=15.0)
            c.cmd("terminal no monitor", timeout=15.0)
        except Exception as e:
            print("cleanup:", e)
    c.close()
sys.exit(rc)
