#!/usr/bin/env python3
"""startjobs.py <console-log> [--from-line N] [--to-line M] [--boot REGEX] [--all]
Summarise the systemd start jobs of each boot in a console transcript (a console.py /
ckcon transcript or a framework swi_*.log): per boot, each job's longest
"A start job is running for <job> (<elapsed> / <limit>)" sighting and how it ended
("Finished", "Started", "FAILED", "Timed out"), plus whether a login prompt followed.
Read-only; runs anywhere the file is (on a testbox: `tools/tb tool <box> <scratch> startjobs
/tmp/<scratch>/console-uN.log`). Replaces the hand-built grep/awk passes the 2026-10-27
campaign rebuilt for each of four x230 reloads (review platform-2026-10-27T0855/REVIEW.md).

systemd truncates long names with an ellipsis ("TPM2 Acc...ement Daemon",
"...gement Daemon"); a truncated name is matched to the full name from its "Starting
<name>..." line, preferring the jobs still running at that point, so "...gement Daemon"
resolves to whichever Management Daemon has not finished yet. An unresolvable one is
shown as printed, marked (?).
  --from-line / --to-line   limit to that line range (1-based, after CR -> newline)
  --boot REGEX              what starts a new boot (default below)
  --all                     list every job, not only the ones with a start-job line
Exit 0; 1 no start job and no boot marker found; 2 usage."""
import re, sys

USAGE = "usage: startjobs.py <console-log> [--from-line N] [--to-line M] [--boot REGEX] [--all]"
BOOT_DEFAULT = r"Bootloader [\d.]+ loaded|BootROM|U-Boot \d|Starting kernel|Booting Linux"
ESC = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[78()=>]|\x1b\][^\x07]*\x07")
JOB = re.compile(r"A start job is running for (.+?) \(([^/()]+?) / ([^()]+?)\)")
STARTING = re.compile(r"^\s*Starting (.+?)\.\.\.\s*$")
DONE = re.compile(r"\[\s*(OK|FAILED|DEPEND|TIME)\s*\]\s+(Finished|Started|Failed to start|Timed out waiting for|Dependency failed for)\s+(.+?)\.?\s*$")
LOGIN = re.compile(r"\S+ login:\s*(<EOS>)?\s*$")
ELL = "…"


def secs(t):
    """'1min 20s' / '58s' / '242ms' / '1h 48s' / 'no limit' -> seconds (float) or None."""
    t = t.strip()
    if t == "no limit":
        return None
    total, found = 0.0, False
    for n, u in re.findall(r"([\d.]+)\s*(ms|min|h|s)", t):
        total += float(n) * {"ms": 0.001, "s": 1, "min": 60, "h": 3600}[u]; found = True
    return total if found else None


def resolve(shown, full_names, running):
    """Map a possibly truncated job name to a full one."""
    if ELL not in shown:
        return shown, True
    head, tail = shown.split(ELL, 1)
    cands = [f for f in full_names if f.startswith(head) and f.endswith(tail)]
    live = [f for f in cands if f in running]
    for pool in (live, cands):
        if len(pool) == 1:
            return pool[0], True
    return shown, False


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__ if argv else USAGE); return 0 if argv else 2
    path, a = argv[0], argv[1:]
    lo, hi, boot_rx, show_all = 1, None, BOOT_DEFAULT, False
    while a:
        k = a.pop(0)
        if k == "--all":
            show_all = True
        elif k in ("--from-line", "--to-line", "--boot") and a:
            v = a.pop(0)
            if k == "--boot":
                boot_rx = v
            elif not v.isdigit():
                print(USAGE); print("%s needs a number" % k); return 2
            elif k == "--from-line":
                lo = int(v)
            else:
                hi = int(v)
        else:
            print(USAGE); print("bad argument: %r" % k); return 2
    boot_re = re.compile(boot_rx)
    with open(path, "rb") as f:
        text = f.read().decode("utf-8", "replace").replace("\x00", "")
    lines = ESC.sub("", text.replace("\r\n", "\n").replace("\r", "\n")).split("\n")

    boots = []          # each: dict(start=line no, jobs={name: info}, order=[...], login=line no or None)
    cur = None

    def new_boot(n):
        b = {"start": n, "jobs": {}, "order": [], "login": None, "full": [], "running": set()}
        boots.append(b)
        return b

    for n, raw in enumerate(lines, 1):
        if n < lo or (hi and n > hi):
            continue
        line = raw.rstrip()
        if boot_re.search(line):
            if cur is None or cur["jobs"] or cur["login"] or n - cur["start"] > 50:
                cur = new_boot(n)
            continue
        if cur is None:
            cur = new_boot(n)
        m = STARTING.match(line)
        if m:
            name = m.group(1)
            if name not in cur["full"]:
                cur["full"].append(name)
            cur["running"].add(name)
            if show_all and name not in cur["jobs"]:
                cur["jobs"][name] = {"max": 0.0, "max_txt": "-", "limit": "-", "end": "running?", "sure": True}
                cur["order"].append(name)
            continue
        m = JOB.search(line)
        if m:
            name, sure = resolve(m.group(1), cur["full"], cur["running"])
            el, lim = m.group(2).strip(), m.group(3).strip()
            j = cur["jobs"].setdefault(name, {"max": -1.0, "max_txt": "", "limit": lim, "end": "running?", "sure": sure})
            if name not in cur["order"]:
                cur["order"].append(name)
            s = secs(el) or 0.0
            if s >= j["max"]:
                j["max"], j["max_txt"], j["limit"] = s, el, lim
            continue
        m = DONE.search(line)
        if m:
            name = m.group(3)
            cur["running"].discard(name)
            if name in cur["jobs"]:
                cur["jobs"][name]["end"] = "%s %s" % (m.group(1), m.group(2))
            continue
        if LOGIN.search(line) and cur["login"] is None and (cur["jobs"] or cur["full"]):
            cur["login"] = n

    boots = [b for b in boots if b["jobs"] or b["full"]]
    if not boots:
        print("%s: no boot with start jobs found (lines %d-%s)" % (path, lo, hi or "end"))
        return 1
    for i, b in enumerate(boots, 1):
        print("boot %d (from line %d%s)" % (i, b["start"], ", login prompt at line %d" % b["login"] if b["login"] else ", no login prompt seen"))
        if not b["jobs"]:
            print("  no start job ran long enough to be reported")
            continue
        print("  %-52s %-10s %-11s %s" % ("job", "longest", "limit", "ended"))
        for name in b["order"]:
            j = b["jobs"][name]
            print("  %-52s %-10s %-11s %s" % ((name + ("" if j["sure"] else " (?)"))[:52], j["max_txt"] or "-", j["limit"], j["end"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
