#!/usr/bin/env python3
"""poll.py <tty> <baud> <transcript> <interval_s> <duration_s> <donefile> CMD [CMD ...]
Every <interval_s>, run each CMD and print it with an epoch stamp. When the session is
lost (the master reloaded and a relayed backup session dropped to login:), log in again
and carry on; a failed login is recorded and retried next interval. Touches <donefile>.
<tty> is the unit's console device on the testbox you run it on; <transcript> and
<donefile> are paths you choose. Login is awlogin.login (env CK_USER / CK_PASSWORD,
default manager / friend)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
USAGE = "usage: poll.py <tty> <baud> <transcript> <interval_s> <duration_s> <donefile> CMD [CMD ...]"
if len(sys.argv) < 8 or sys.argv[1] in ("-h", "--help"):
    print(USAGE); sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
try:
    tty, baud, tr, iv, dur, done = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
import console, awlogin as L
cmds = sys.argv[7:]
c = console.Console(tty, tr, baud=baud)
t_end = time.time() + dur
logged = False
try:
    while time.time() < t_end:
        t_it = time.time()
        if not logged:
            try:
                logged = L.login(c)
            except SystemExit as e:
                print(L.stamp(), "LOGIN REFUSED", e); break
            print(L.stamp(), "login", "ok" if logged else "FAILED")
        if logged:
            for cmd in cmds:
                out = c.cmd(cmd, timeout=30)
                print("=== %s >>> %s" % (L.stamp(), cmd))
                print(out)
                if "login:" in out or "connection abort" in out:
                    logged = False
                    print(L.stamp(), "SESSION LOST")
                    break
                if out.strip() == "":
                    # no output at all: prompt may be gone; re-check next round
                    logged = False
                    print(L.stamp(), "EMPTY -> re-login next round")
                    break
        sys.stdout.flush()
        rest = iv - (time.time() - t_it)
        if rest > 0:
            time.sleep(rest)
finally:
    try:
        if logged:
            raw = c.send("", timeout=5.0)
            if "(config" in raw: c.cmd("end", timeout=15.0)
            c.cmd("terminal no monitor", timeout=15.0)
    except Exception as e:
        print("cleanup:", e)
    c.close()
    open(done, "w").write("%.3f\n" % time.time())
