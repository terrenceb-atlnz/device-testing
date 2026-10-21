#!/usr/bin/env python3
"""health.py <tty> <baud> <transcript> [--before SUMMARY.json] [--save FILE] [--json FILE]
                                       [--tail N] [--label TEXT] [--raw]
The STANDING-ORDERS §8 health sample of one AW+ unit in ONE call, summarised to a few lines.
It logs in (awlogin), runs the read-only health commands, saves every command with its full
output to <save> in the `HH:MM:SS >>> cmd` stdout format (quote it verbatim in the working
log), writes a machine summary to <json>, and prints only the summary:
  BEFORE sample (no --before):  show reboot history, show exception log,
      show log | include kernel|exception|crash|restart|Unexpected, show cpu, show memory
  AFTER sample (--before <the before sample's .json>): the same plus `show log tail N`
      (N = --tail, default 150; 0 = skip), and a HEALTH-DIFF block against the before sample:
      new reboot entries, exception log change, new non-echo filtered lines, the tail's line
      signatures, cpu and memory before -> after, and a CLEAN / DIRTY verdict.
Exit: 0 clean, 4 DIRTY (a new reboot entry, an exception log that is not None, or a new
kernel / crash / daemon-restart line -- report it to the sentinel as NEEDS TEST ENGINEER and
label the run confounded), 7 no privileged prompt, 2 usage.
Defaults: <save> = <transcript dir>/health-<tty name>-<stamp>.out, <json> = <save>.json.
`show cpu` on AW+ prints BUSY averages (1 s / 20 s / 60 s), never an idle figure; the summary
repeats what the device printed and says so. A memory step change across one case is reported
as a number, never as a leak (logged-output.md §2). <tty> is the unit's console on the testbox;
<transcript> is a path you choose (every byte goes there as it arrives). Env CKTO = per-command
timeout s (default 90); CK_USER / CK_PASSWORD = credentials (default manager / friend)."""
import collections, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
USAGE = ("usage: health.py <tty> <baud> <transcript> [--before SUMMARY.json] [--save FILE] "
         "[--json FILE] [--tail N] [--label TEXT] [--raw]")
if len(sys.argv) < 4 or sys.argv[1] in ("-h", "--help"):
    print(USAGE); sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
try:
    tty, baud, transcript = sys.argv[1], int(sys.argv[2]), sys.argv[3]
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
opts = {"before": None, "save": None, "json": None, "tail": "150", "label": "", "raw": False}
a = sys.argv[4:]
while a:
    k = a.pop(0)
    if k == "--raw":
        opts["raw"] = True; continue
    if k.startswith("--") and k[2:] in opts and a:
        opts[k[2:]] = a.pop(0); continue
    print(USAGE); print("bad argument: %r" % k); sys.exit(2)
if not opts["tail"].isdigit():
    print(USAGE); print("--tail must be a number"); sys.exit(2)
TAIL = int(opts["tail"])
STAMP = time.strftime("%Y%m%dT%H%M%S")
name = os.path.basename(tty)
SAVE = opts["save"] or os.path.join(os.path.dirname(os.path.abspath(transcript)), "health-%s-%s.out" % (name, STAMP))
JSON = opts["json"] or SAVE + ".json"
CKTO = float(os.environ.get("CKTO", "90"))

import console, awlogin as L

ESC = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[78()=>]|\x1b\][^\x07]*\x07")
REBOOT = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*?)\s*$")
# AW+ log line: "2026 Oct 21 01:03:56 kern.err x230-28GSv2 snmpd[1482]: snmpd: send_trap: ..."
LOGLINE = re.compile(r"^(\d{4} \w{3} +\d{1,2} \d{2}:\d{2}:\d{2}) (\S+) (\S+) ([\w.-]+)(?:\[\d+\])?: (.*)$")
FLAG = re.compile(r"kernel:|kern\.(crit|alert|emerg)|exception|crash|restart|Unexpected", re.I)
CPU = re.compile(r"1 second:\s*(\d+)%,\s*20 seconds:\s*(\d+)%,\s*60 seconds:\s*(\d+)%")
LOAD = re.compile(r"1 minute:\s*([\d.]+)")
MEM = re.compile(r"RAM total:\s*(\d+) kB; free:\s*(\d+) kB(?:; buffers:\s*(\d+) kB)?")
CMDS = ["show reboot history", "show exception log",
        "show log | include kernel|exception|crash|restart|Unexpected", "show cpu", "show memory"]


def clean(s):
    return ESC.sub("", s.replace("\r", ""))


def is_echo(msg_line):
    """A log line that only records our own typing (IMISH keystroke echo / its suppression note)."""
    return "IMISH[" in msg_line and ("]: [" in msg_line or "Last message" in msg_line)


def parse_reboots(out):
    return [m.group(0).strip() for m in (REBOOT.match(l.strip()) for l in out.splitlines()) if m]


def parse_exception(out):
    body = [l.strip() for l in out.splitlines()[2:] if l.strip() and not l.startswith("---")]
    return "None" if body == ["None"] or not body else "\n".join(body)


def parse_loglines(out):
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    return [l for l in lines if LOGLINE.match(l)]


def signatures(lines, top=6):
    """Group non-echo log lines by program + the start of the message."""
    cnt = collections.Counter(); example = {}
    for l in lines:
        m = LOGLINE.match(l)
        if not m or is_echo(l):
            continue
        key = (m.group(4), m.group(5)[:48])
        cnt[key] += 1; example.setdefault(key, l)
    return [(n, example[k]) for k, n in cnt.most_common(top)]


before = None
if opts["before"]:
    with open(opts["before"]) as f:
        before = json.load(f)
    cmds = CMDS + (["show log tail %d" % TAIL] if TAIL else [])
else:
    cmds = CMDS

c = console.Console(tty, transcript, baud=baud)
rc = 0; ok = False; raw = {}; t_first = time.strftime("%H:%M:%S")
try:
    ok = L.login(c)
    if not ok:
        print("no privileged prompt on %s" % tty); sys.exit(7)
    with open(SAVE, "w") as sv:
        sv.write("# health.py %s %s %s\n" % (name, STAMP, opts["label"]))
        for cmd in cmds:
            out = clean(c.cmd(cmd, timeout=CKTO))
            raw[cmd] = out
            sv.write("%s >>> %s\n%s\n" % (time.strftime("%H:%M:%S"), cmd, out))
            if opts["raw"]:
                print("%s >>> %s\n%s" % (time.strftime("%H:%M:%S"), cmd, out))
    t_last = time.strftime("%H:%M:%S")
finally:
    if ok:
        try:
            if not c.monitor_off():
                print("cleanup: console busy or not at exec -- sent nothing")
        except Exception as e:
            print("cleanup: %s" % e)
    c.close()

reboots = parse_reboots(raw[CMDS[0]])
newest = max(reboots, key=lambda l: l[:19]) if reboots else ""
exc = parse_exception(raw[CMDS[1]])
filtered = parse_loglines(raw[CMDS[2]])
filt_other = [l for l in filtered if not is_echo(l)]
m = CPU.search(raw[CMDS[3]]); cpu = [int(x) for x in m.groups()] if m else None
m = LOAD.search(raw[CMDS[3]]); load = m.group(1) if m else None
m = MEM.search(raw[CMDS[4]]); mem = {"total": int(m.group(1)), "free": int(m.group(2)), "buffers": int(m.group(3) or 0)} if m else None
tail = parse_loglines(raw.get("show log tail %d" % TAIL, "")) if TAIL and before else []
summary = {"tty": tty, "stamp": STAMP, "label": opts["label"], "start": t_first, "end": t_last, "save": SAVE,
           "reboots": reboots, "reboot_newest": newest, "exception": exc,
           "filtered": filtered, "filtered_other": filt_other, "cpu": cpu, "load": load, "memory": mem,
           "tail": tail}
with open(JSON, "w") as f:
    json.dump(summary, f, indent=1)

label = (" " + opts["label"]) if opts["label"] else ""
print("HEALTH %s %s-%s%s  saved %s  json %s" % (name, t_first, t_last, label, SAVE, JSON))
print("  reboots ......... %d entries, newest %s" % (len(reboots), newest or "(none)"))
print("  exception log ... %s" % exc.replace("\n", " | "))
print("  log (filtered) .. %d lines: %d echoes of our own commands, %d other" % (len(filtered), len(filtered) - len(filt_other), len(filt_other)))
for l in filt_other[:8]:
    print("      %s" % l)
print("  cpu ............. %s  (show cpu prints BUSY averages 1 s / 20 s / 60 s, not idle)%s"
      % ("%d%% / %d%% / %d%%" % tuple(cpu) if cpu else "not parsed", "; load %s" % load if load else ""))
print("  memory .......... %s" % ("free %d of %d kB (buffers %d)" % (mem["free"], mem["total"], mem["buffers"]) if mem else "not parsed"))

if before:
    dirty = []
    new_reb = list((collections.Counter(reboots) - collections.Counter(before.get("reboots", []))).elements())
    b_exc = before.get("exception", "?")
    new_other = [l for l in filt_other if l not in set(before.get("filtered_other", []))]
    flagged = [l for l in new_other + tail if not is_echo(l) and FLAG.search(l)]
    print("HEALTH-DIFF %s vs %s (%s%s)" % (name, os.path.basename(opts["before"]), before.get("start", "?"),
                                          (" " + before["label"]) if before.get("label") else ""))
    if new_reb:
        dirty.append("new reboot entry: " + "; ".join(new_reb))
        print("  reboots ......... !! %d NEW: %s" % (len(new_reb), "; ".join(new_reb)))
    else:
        print("  reboots ......... no new entry (newest stays %s)" % (newest or "(none)"))
    if exc != "None":
        dirty.append("exception log not None")
    print("  exception log ... %s -> %s" % (b_exc.replace("\n", " | "), exc.replace("\n", " | ")))
    print("  log (filtered) .. %d new non-echo lines" % len(new_other))
    for l in new_other[:8]:
        print("      %s" % l)
    if tail:
        sig = signatures(tail)
        echoes = sum(1 for l in tail if is_echo(l))
        print("  log tail %d .... %d lines, %d echoes of our own commands; other lines by signature:" % (TAIL, len(tail), echoes))
        for n, ex in sig:
            print("      %3d x  %s" % (n, ex))
        if not sig:
            print("      (none)")
    if flagged:
        dirty.append("%d kernel/crash/restart line(s)" % len(flagged))
        print("  !! flagged ...... %d line(s) matching kernel|exception|crash|restart|Unexpected (not an echo):" % len(flagged))
        for l in flagged[:10]:
            print("      %s" % l)
    bc, bm = before.get("cpu"), before.get("memory")
    print("  cpu ............. %s -> %s  (1 s busy average)" % (("%d%%" % bc[0]) if bc else "?", ("%d%%" % cpu[0]) if cpu else "?"))
    if bm and mem:
        d = mem["free"] - bm["free"]
        print("  memory .......... free %d -> %d kB (%+d; one case cannot show a leak)" % (bm["free"], mem["free"], d))
    else:
        print("  memory .......... before %s -> after %s" % (bm, mem))
    if dirty:
        print("  VERDICT ......... !! DIRTY -- " + "; ".join(dirty) + " -- report NEEDS TEST ENGINEER, label the run confounded")
        rc = 4
    else:
        print("  VERDICT ......... CLEAN")
sys.exit(rc)
