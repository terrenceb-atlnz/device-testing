#!/usr/bin/env python3
"""speedrow.py <dut-tty> <partner-tty> <baud> <dut-transcript> <partner-transcript>
              --dut-port P --partner-port P [options] ROW [ROW ...]
One speed/duplex row at a time on a DUT port and its link partner, BOTH ends driven from this
one process, so the partner is watched while the DUT changes (two console tools in one tool
block run one AFTER the other: that cost T47208 four minutes and a second pass on 2026-10-21).
Per ROW it: sets the DUT port; sets the partner per --match; polls BOTH ends' `show interface
<port> status` in parallel until each reads connected at the expected speed; optionally waits
for the LLDP neighbour on both ends (--lldp), decodes the DUT's MAC/PHY TLV at the partner
(--tlv: selects `lldp tlv-select mac-phy-config` on both ports for the run, removes it at
restore; reads auto-negotiation, advertised set, operational MAU type, and the reverse
direction at the DUT; polls until the MAU type matches the DUT's operational speed/duplex,
1000FD 30, 100FD 16, 100HD 15, 10FD 11, 10HD 10), holds the row (--hold S) and
flaps the link N times from one end (--flap N --flap-end dut|partner|both). It prints ONE
summary line per row (and per flap) and writes every command with its full output to <save>
in the `HH:MM:SS >>> cmd` format, prefixed [dut] / [partner], for the working log.
ROW grammar (copper): auto | auto-<speed> | auto-<speed>-half | <speed> | <speed>-full | <speed>-half
  auto            -> no speed; no duplex              (expect a-full a-<any>)
  auto-100        -> speed auto 100; no duplex        (expect a-full a-100)
  auto-100-half   -> speed auto 100; duplex half      (expect a-half a-100)
  1000            -> speed 1000; no duplex            (expect full 1000; partner left at auto)
  100-full        -> speed 100; duplex full           (forced; partner matched with --match forced)
  10-half         -> speed 10; duplex half            (forced)
--match forced (default): the partner mirrors forced rows (<speed>-full/-half) and returns
  to auto on every other row; always: the partner mirrors every row; never: untouched.
--wait S link-up timeout per end (60); --lldp-wait S (60); --hold S after link (0);
--no-restore: leave the last row in place (default: both ends back to `no speed`/`no duplex`,
  in a finally:, even after an error). --save FILE (default <dut transcript dir>/speedrow-<stamp>.out).
A `% ` rejection on a row is printed verbatim as REFUSED and the next row runs. Exit: 0 every
row linked as expected; 3 a row timed out or read a different speed/duplex; 4 a row was
refused; 7 no privileged prompt; 2 usage. Env CKTO per-command timeout s (default 90),
CK_USER / CK_PASSWORD credentials. Both consoles stay in config-if for the run (`do show`),
and are left at exec with `terminal no monitor`. Verified on copper (AW+ status columns
`Status Vlan Duplex Speed`); a fibre module refuses most rows, which this reports as REFUSED."""
import os, re, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
USAGE = ("usage: speedrow.py <dut-tty> <partner-tty> <baud> <dut-transcript> <partner-transcript> "
         "--dut-port P --partner-port P [--match forced|always|never] [--wait S] [--lldp] [--lldp-wait S] "
         "[--tlv] [--hold S] [--flap N] [--flap-end dut|partner|both] [--no-restore] [--save FILE] ROW [ROW ...]")
if len(sys.argv) < 6 or sys.argv[1] in ("-h", "--help"):
    print(USAGE); sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
try:
    dtty, ptty, baud, dtr, ptr = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
opt = {"dut-port": None, "partner-port": None, "match": "forced", "wait": "60", "lldp-wait": "60",
       "hold": "0", "flap": "0", "flap-end": "dut", "save": None}
flags = {"lldp": False, "tlv": False, "no-restore": False}
rows = []
a = sys.argv[6:]
while a:
    k = a.pop(0)
    if k.startswith("--") and k[2:] in flags:
        flags[k[2:]] = True
    elif k.startswith("--") and k[2:] in opt and a:
        opt[k[2:]] = a.pop(0)
    elif k.startswith("--"):
        print(USAGE); print("bad option: %r" % k); sys.exit(2)
    else:
        rows.append(k)
ROW_RE = re.compile(r"^(auto|auto-(10|100|1000|2500|10000)(-half)?|(10|100|1000|2500|10000)(-full|-half)?)$")
if not (opt["dut-port"] and opt["partner-port"] and rows and all(ROW_RE.match(r) for r in rows)
        and opt["match"] in ("forced", "always", "never") and opt["flap-end"] in ("dut", "partner", "both")):
    print(USAGE); print("need --dut-port, --partner-port and valid ROWs (%s)" % ", ".join(r for r in rows if not ROW_RE.match(r))); sys.exit(2)
try:
    WAIT, LWAIT, HOLD, FLAP = float(opt["wait"]), float(opt["lldp-wait"]), float(opt["hold"]), int(opt["flap"])
except ValueError as e:
    print(USAGE); print("bad number: %s" % e); sys.exit(2)
CKTO = float(os.environ.get("CKTO", "90"))
STAMP = time.strftime("%Y%m%dT%H%M%S")
SAVE = opt["save"] or os.path.join(os.path.dirname(os.path.abspath(dtr)), "speedrow-%s.out" % STAMP)
MAU = {("1000", "full"): "30", ("100", "full"): "16", ("100", "half"): "15", ("10", "full"): "11", ("10", "half"): "10"}

import console, awlogin as L

ESC = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[78()=>]")
STATUS = re.compile(r"^(port[\d.]+)\s+\S+\s+(\S+)\s+(\S+)\s+(a-full|a-half|full|half|\S+)\s+(a-\d+|\d+|\S+)\s+(\S+)")
savef = open(SAVE, "w")
savelock = threading.Lock()


def now():
    return time.strftime("%H:%M:%S")


class End:
    def __init__(self, tag, tty, tr, port):
        self.tag, self.port = tag, port
        self.c = console.Console(tty, tr, baud=baud)
        self.ok = False
        self.lock = threading.Lock()

    def login(self):
        self.ok = L.login(self.c)
        return self.ok

    def cmd(self, line, timeout=None):
        """Send one line; completion = a prompt after the echo (chatter-immune). Returns the
        cleaned output without echo/prompt, and records it in the save file."""
        with self.lock:
            raw = self.c.send_until_prompt(line, timeout=timeout or CKTO)
        out = ESC.sub("", raw.replace("\r", ""))
        lines = out.splitlines()
        if lines and line.strip() and line.strip() in lines[0]:
            lines = lines[1:]
        while lines and console.PROMPT_RE.search(lines[-1].rstrip()):
            lines.pop()
        out = "\n".join(lines).strip()
        with savelock:
            savef.write("[%s] %s >>> %s\n%s\n" % (self.tag, now(), line, out))
            savef.flush()
        if not self.c.last_prompt_seen:
            out += "\n!!! no prompt within %.0f s" % (timeout or CKTO)
        return out

    def errors(self, out):
        return [l.strip() for l in out.splitlines() if l.lstrip().startswith("%") and not console.is_advisory(l)]

    def status(self):
        out = self.cmd("do show interface %s status" % self.port, timeout=30)
        for l in out.splitlines():
            m = STATUS.match(l.strip())
            if m and m.group(1) == self.port:
                return {"status": m.group(2), "vlan": m.group(3), "duplex": m.group(4), "speed": m.group(5), "type": m.group(6)}
        return {"status": "?", "duplex": "?", "speed": "?", "raw": out[-200:]}

    def wait_status(self, want_status, want_speed, want_duplex, timeout):
        """Poll until status == want_status and (speed, duplex match when given). Returns (seconds, last)."""
        t0 = time.time(); last = {}
        while True:
            last = self.status()
            okst = last.get("status") == want_status
            oksp = want_speed is None or last.get("speed", "").lstrip("a-") == want_speed
            okdu = want_duplex is None or last.get("duplex", "").lstrip("a-") == want_duplex
            if okst and oksp and okdu:
                return time.time() - t0, last
            if time.time() - t0 > timeout:
                return None, last
            time.sleep(0.7)

    def wait_lldp(self, far_port, timeout):
        t0 = time.time()
        while True:
            out = self.cmd("do show lldp neighbors", timeout=30)
            if re.search(r"\b%s\b" % re.escape(far_port), out):
                return time.time() - t0
            if time.time() - t0 > timeout:
                return None
            time.sleep(1.0)

    def tlv(self, want_mau, timeout):
        """Read the neighbour's MAC/PHY TLV from `show lldp neighbors detail`; with want_mau,
        poll until the operational MAU type number matches (the TLV refreshes after the link)."""
        t0 = time.time(); got = {}
        while True:
            out = self.cmd("do show lldp neighbors detail", timeout=45)
            blk = out.split("Local %s:" % self.port, 1)[1] if ("Local %s:" % self.port) in out else out
            m1 = re.search(r"MAC/PHY Auto-negotiation\s*\.+\s*(.+)", blk)
            m2 = re.search(r"Advertised Capability\s*\.+\s*(.*?)\n\s*Operational MAU Type", blk, re.S)
            m3 = re.search(r"Operational MAU Type\s*\.+\s*(.+?)\s*\((\d+)\)", blk)
            adv = re.sub(r"\s+", " ", m2.group(1)).strip() if m2 else ""
            got = {"autoneg": m1.group(1).strip() if m1 else "?", "advertised": adv or "?",
                   "mau": m3.group(1).strip() if m3 else "?", "mau_n": m3.group(2) if m3 else "?"}
            if m3 and (want_mau is None or got["mau_n"] == want_mau):
                return time.time() - t0, got
            if m1 and "not advertised" in got["autoneg"]:
                return None, got        # the far end does not select the TLV: polling cannot change that
            if time.time() - t0 > timeout:
                return None, got
            time.sleep(1.0)


def plan(row):
    """ROW -> (dut commands, expected speed or None, expected duplex, forced?)"""
    if row == "auto":
        return ["no speed", "no duplex"], None, "full", False
    m = re.match(r"^auto-(\d+)(-half)?$", row)
    if m:
        sp, half = m.group(1), bool(m.group(2))
        return ["speed auto %s" % sp, "duplex half" if half else "no duplex"], sp, "half" if half else "full", False
    m = re.match(r"^(\d+)(-full|-half)?$", row)
    sp, du = m.group(1), (m.group(2) or "-full")[1:]
    forced = m.group(2) is not None
    return ["speed %s" % sp] + (["duplex %s" % du] if forced else ["no duplex"]), sp, du, forced


def both(fn_d, fn_p):
    """Run two blocking calls in parallel, one per end; return their results."""
    res = [None, None]
    td = threading.Thread(target=lambda: res.__setitem__(0, fn_d()))
    tp = threading.Thread(target=lambda: res.__setitem__(1, fn_p()))
    td.start(); tp.start(); td.join(); tp.join()
    return res


def fmt(st):
    return "%s %s %s" % (st.get("status", "?"), st.get("duplex", "?"), st.get("speed", "?"))


D = End("dut", dtty, dtr, opt["dut-port"])
P = End("partner", ptty, ptr, opt["partner-port"])
rc = 0
try:
    if not (D.login() and P.login()):
        print("no privileged prompt on %s" % ("the DUT console" if not D.ok else "the partner console")); sys.exit(7)
    for e in (D, P):
        out = e.cmd("configure terminal") + e.cmd("interface %s" % e.port)
        if e.errors(out):
            print("%s: cannot enter interface %s: %s" % (e.tag, e.port, e.errors(out))); sys.exit(7)
    print("speedrow %s  DUT %s <-> partner %s  rows %s  save %s" % (now(), D.port, P.port, " ".join(rows), SAVE))
    if flags["tlv"]:
        # The MAC/PHY TLV is off by default on AW+; --tlv selects it on BOTH ports for the run and
        # removes it at restore, so the decode reads this run's setting and not a leftover.
        for e in (D, P):
            errs = e.errors(e.cmd("lldp tlv-select mac-phy-config"))
            if errs:
                print("%s: lldp tlv-select mac-phy-config refused: %s" % (e.tag, errs)); sys.exit(7)
        print("SETUP     lldp tlv-select mac-phy-config on both ends (removed at restore)")
    b0 = both(D.status, P.status)
    print("BASELINE  dut %s | partner %s" % (fmt(b0[0]), fmt(b0[1])))

    for row in rows:
        dcmds, sp, du, forced = plan(row)
        if opt["match"] == "always" or (opt["match"] == "forced" and forced):
            pcmds = list(dcmds)
        elif opt["match"] == "never":
            pcmds = []
        else:
            pcmds = ["no speed", "no duplex"]
        t_cfg = time.time()
        refused = []
        for line in dcmds:
            refused += D.errors(D.cmd(line))
        for line in pcmds:
            refused += ["partner: " + x for x in P.errors(P.cmd(line))]
        if refused:
            print("ROW %-14s REFUSED  %s" % (row, " | ".join(refused)))
            rc = max(rc, 4)
            continue
        # expected partner reading: mirrored -> same as DUT; left at auto -> a-<speed> at the DUT's duplex
        p_sp = sp if (pcmds or opt["match"] == "never") else sp
        res = both(lambda: D.wait_status("connected", sp, du, WAIT),
                   lambda: P.wait_status("connected", p_sp, du if (opt["match"] != "never") else None, WAIT))
        (dt, dst), (pt, pst) = res
        line = "ROW %-14s dut %s %s | partner %s %s" % (
            row, fmt(dst), ("%.1f s" % dt) if dt is not None else "TIMEOUT %.0f s" % WAIT,
            fmt(pst), ("%.1f s" % pt) if pt is not None else "TIMEOUT %.0f s" % WAIT)
        if dt is None or pt is None:
            rc = max(rc, 3)
        if flags["lldp"]:
            ld, lp = both(lambda: D.wait_lldp(P.port, LWAIT), lambda: P.wait_lldp(D.port, LWAIT))
            line += " | lldp dut %s partner %s" % (("%.1f s" % ld) if ld is not None else "NOT SEEN", ("%.1f s" % lp) if lp is not None else "NOT SEEN")
            if ld is None or lp is None:
                rc = max(rc, 3)
        if flags["tlv"]:
            # the DUT's operational mode decides the MAU the partner should decode
            dsp = (dst.get("speed") or "").lstrip("a-"); ddu = (dst.get("duplex") or "").lstrip("a-")
            want = MAU.get((dsp, ddu))
            tt, tv = P.tlv(want, LWAIT)
            line += " | TLV@partner autoneg=%s adv=[%s] mau=%s (%s)%s" % (
                tv.get("autoneg"), tv.get("advertised"), tv.get("mau"), tv.get("mau_n"),
                (" %.0f s" % tt) if tt is not None else " (expected MAU %s NOT SEEN in %.0f s)" % (want, LWAIT))
            if tt is None:
                rc = max(rc, 3)
            _, rv = D.tlv(None, 5)
            line += " | reverse@dut autoneg=%s mau=%s (%s)" % (rv.get("autoneg"), rv.get("mau"), rv.get("mau_n"))
        print(line); sys.stdout.flush()
        if HOLD:
            time.sleep(HOLD)
        for i in range(FLAP):
            ends = [D, P] if opt["flap-end"] == "both" else [D if opt["flap-end"] == "dut" else P]
            for e in ends:
                e.cmd("shutdown")
                t_dn, _ = e.wait_status("disabled", None, None, 20)
                t_up0 = time.time()
                e.cmd("no shutdown")
                (fd, fds), (fp, fps) = both(lambda: D.wait_status("connected", sp, du, WAIT),
                                            lambda: P.wait_status("connected", p_sp, None, WAIT))
                fl = "FLAP %-14s #%d from %-7s down %s | up: dut %s %s | partner %s %s" % (
                    row, i + 1, e.tag, ("%.1f s" % t_dn) if t_dn is not None else "not seen",
                    fmt(fds), ("%.1f s" % fd) if fd is not None else "TIMEOUT", fmt(fps), ("%.1f s" % fp) if fp is not None else "TIMEOUT")
                if fd is None or fp is None:
                    rc = max(rc, 3)
                if flags["lldp"]:
                    ld, lp = both(lambda: D.wait_lldp(P.port, LWAIT), lambda: P.wait_lldp(D.port, LWAIT))
                    fl += " | lldp dut %s partner %s" % (("%.1f s" % ld) if ld is not None else "NOT SEEN", ("%.1f s" % lp) if lp is not None else "NOT SEEN")
                print(fl); sys.stdout.flush()
finally:
    try:
        if not flags["no-restore"] and D.ok and P.ok:
            for e in (D, P):
                e.cmd("no speed"); e.cmd("no duplex")
                if flags["tlv"]:
                    e.cmd("no lldp tlv-select mac-phy-config")
            r = both(lambda: D.wait_status("connected", None, None, WAIT), lambda: P.wait_status("connected", None, None, WAIT))
            print("RESTORE   both ends no speed / no duplex: dut %s | partner %s" % (fmt(r[0][1]), fmt(r[1][1])))
        for e in (D, P):
            if e.ok:
                try:
                    if not e.c.monitor_off():
                        print("cleanup %s: console busy or not at exec -- sent nothing" % e.tag)
                except Exception as ex:
                    print("cleanup %s: %s" % (e.tag, ex))
            e.c.close()
    finally:
        savef.close()
sys.exit(rc)
