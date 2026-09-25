import sys, time, re, os; sys.path.insert(0, "/tmp/ckorient")
from console import Console, PROMPT_RE
RUN = os.environ.get("RUN", "/tmp/ckorient/work")
os.makedirs(RUN, exist_ok=True)
DEV = {"stk": ("/dev/u5", 115200), "ar": ("/dev/u1", 115200), "sa": ("/dev/u3", 115200), "x230": ("/dev/u0", 9600)}
RAW = open(RUN + "/work-raw.log", "a", buffering=1)
YN = re.compile(r"\((y/n|yes/no)\)\s*\??\s*:?\s*$")
def log(s): RAW.write(s + "\n"); print(s, flush=True)
def session(tag):
    port, baud = DEV[tag]
    c = Console(port, "%s/console-%s.log" % (RUN, tag), baud=baud); c.login(timeout=120)
    c.send("terminal length 0", quiet=1.0, timeout=20); return c
def do(c, tag, cmd, answer=None, timeout=120, allow_err=False):
    out = c.send(cmd, quiet=1.5, timeout=timeout, need_prompt=False)
    t0 = time.time()
    while time.time() - t0 < timeout and not (PROMPT_RE.search(out.rstrip()[-120:]) or YN.search(out.rstrip())):
        out += c.read_until_quiet(quiet=1.5, timeout=10, need_prompt=False)
    if YN.search(out.rstrip()):
        if answer is None:
            w = "no" if "yes/no" in out.rstrip()[-20:] else "n"
            out += c.send(w, quiet=2.0, timeout=30)
            log("%s> %s\n%s\n[UNEXPECTED prompt -> %s; STOP]" % (tag, cmd, out, w)); raise SystemExit(1)
        out += "\n[answered %s]\n" % answer + c.send(answer, quiet=2.0, timeout=timeout)
    log("%s> %s\n%s" % (tag, cmd, out))
    if not allow_err and re.search(r"^\s*% ", out, re.M):
        log("[CLI error -- STOP]"); raise SystemExit(1)
    return out
