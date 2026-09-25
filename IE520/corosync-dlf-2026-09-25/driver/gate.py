from am2 import *
def poll(c, tag, cmd, pat, secs=120, every=5):
    t0 = time.time()
    while time.time() - t0 < secs:
        o = do(c, tag, cmd, allow_err=True)
        if re.search(pat, o): return o
        time.sleep(every)
    log("[GATE FAILED: %s !~ %s -- STOP]" % (cmd, pat)); raise SystemExit(1)
def conf(c, tag, lines):
    do(c, tag, "configure terminal")
    for l in lines: do(c, tag, l)
    do(c, tag, "end")
