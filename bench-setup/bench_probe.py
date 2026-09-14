#!/usr/bin/env python3
"""bench_probe.py -- the SOLE SOURCE OF TRUTH for the tb470 bench.

Sweeps /dev/u0..u6 IDENTICALLY on every run and drives each console directly
over pyserial. It depends on NOTHING else: no AT framework, no tb470.setup, no
bench-state.md. It is the tool that FEEDS bench-state.md (which generates
tb470.setup) -- never the reverse -- so it must never read either of them.

For every console it: checks the node exists and is free (never collides with a
live session), auto-detects baud (115200 then 9600), forces the login banner to
identify the physical unit, logs in to a PRIVILEGED prompt if needed, and
captures one FIXED set of read-only `show` commands. On a formed stack it also
lists EACH member's own flash (`dir awplus-N/flash:`), and it maps every live
host NIC to the switch port that learned its MAC (host-side ping + filtered
`show mac address-table`).

Output is JSON on STDOUT (summary on stderr) -- nothing is written to disk. The
JSON is transient: pipe it, read it, update bench-state.md, discard it.

Run ON tb470 (the consoles are local to it); serial access needs no sudo:
    python3 bench_probe.py [--consoles 0-6] [--quiet] > /tmp/probe.json
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

import serial

# ---- what we capture, the same way every time -------------------------------

BAUDS = [115200, 9600]
USERNAME = "manager"
PASSWORDS = ["friend", "P@ssw0rd", "awplus"]

# Fixed, comprehensive, read-only. Order is stable so runs diff cleanly. A
# command a product lacks records its own error string and never aborts the run.
COMMANDS = [
    "show system",
    "show system serialnumber",
    "show version",
    "show stack",
    "show stack detail",
    "show boot",
    "show reboot history",
    "show file systems",
    "dir",
    "show ip interface brief",
    "show interface status",
    "show vlan brief",
    "show system pluggable",
    "show system pluggable detail",
    "show lldp neighbors",
    "show etherchannel detail",
    "show arp",
    "show ip route",
    "show ip route summary",
    "show ip ospf neighbor",
    "show spanning-tree",
    "show cpu",
    "show memory",
    "show system environment",
    "show clock",
    "show users",
    "show running-config",
    "show startup-config",
]

PROMPT_RE = re.compile(r"[\w.-]+(?:\([\w -]+\))?[#>][ \t]*$")
PROMPT_ANYWHERE_RE = re.compile(r"(?:^|\r?\n)[\w.-]+(?:\([\w -]+\))?[#>]")
PRIV_RE = re.compile(r"[\w.-]+(?:\([\w -]+\))?#[ \t]*$")
PRIV_ANYWHERE_RE = re.compile(r"(?:^|\r?\n)[\w.-]+(?:\([\w -]+\))?#")
LOGIN_RE = re.compile(r"([\w.-]+) login:\s*$")
PHYS_PORT_RE = re.compile(r"\b(port(\d+)\.\d+\.\d+)\b")
STACK_ID_RE = re.compile(r"^\s*(\d+)\s+\S+\s+[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4}\b")
# a `show stack` member row carries the ID first and its Role last; capture both so
# a console's role is looked up by the unit it is ON, not the first row in the table
# (every relayed console sees the same table, so _first() reported member 1's role
# for all of them -- the master console read "Backup Member").
STACK_ROW_RE = re.compile(
    r"^\s*(\d+)\b.*?\b(Active Master|Backup Member|Standalone unit)\s*$", re.I)
PRINTABLE = set(bytes(range(0x20, 0x7F))) | {0x09, 0x0A, 0x0D}


def mac_dotted(mac):
    h = re.sub(r"[^0-9a-fA-F]", "", mac or "").lower()
    return "{}.{}.{}".format(h[0:4], h[4:8], h[8:12]) if len(h) == 12 else (mac or "")


def stack_member_ids(show_stack):
    return [int(m.group(1)) for line in (show_stack or "").splitlines()
            for m in [STACK_ID_RE.match(line)] if m]


def stack_roles(show_stack):
    """{stack-id: role} parsed from `show stack`."""
    roles = {}
    for line in (show_stack or "").splitlines():
        m = STACK_ROW_RE.match(line)
        if m:
            roles[int(m.group(1))] = m.group(2)
    return roles


def role_for(banner, show_stack):
    """Role of the unit THIS console is on. `awplus-N` is member N; bare `awplus`
    is whichever member currently holds Active Master. Returns None off-stack."""
    roles = stack_roles(show_stack)
    if not roles:
        return None
    if banner:
        m = re.search(r"-(\d+)$", banner)
        if m:
            return roles.get(int(m.group(1)))
    for rid, r in roles.items():
        if r.lower() == "active master":
            return r
    return None


class Probe:
    def __init__(self, port):
        self.port = port
        self.s = None
        self.baud = None

    def _open(self, baud):
        os.system("stty -F {} -hupcl 2>/dev/null".format(os.path.realpath(self.port)))
        self.s = serial.Serial(self.port, baud, timeout=0.2)
        self.baud = baud

    def _drain(self, quiet=0.8, timeout=30.0, need_prompt=False):
        buf = ""
        deadline = time.time() + timeout
        last = time.time()
        while time.time() < deadline:
            chunk = self.s.read(4096)
            if chunk:
                buf += chunk.decode(errors="replace")
                last = time.time()
                if "--More--" in buf[-24:]:
                    self.s.write(b" ")
                continue
            if time.time() - last >= quiet:
                if not need_prompt or PROMPT_ANYWHERE_RE.search(buf):
                    return buf
            time.sleep(0.03)
        return buf

    def _send(self, line, quiet=0.8, timeout=30.0, need_prompt=True):
        self.s.write((line + "\r").encode())
        return self._drain(quiet=quiet, timeout=timeout, need_prompt=need_prompt)

    @staticmethod
    def _looks_valid(raw):
        if not raw:
            return False
        good = sum(1 for c in raw.encode(errors="replace") if c in PRINTABLE)
        return good / max(1, len(raw)) > 0.85

    def detect_baud(self):
        empty_all = True
        for baud in BAUDS:
            try:
                if self.s:
                    self.s.close()
                self._open(baud)
            except Exception as e:
                return None, "open failed: {}: {}".format(type(e).__name__, e)
            self.s.write(b"\r")
            out = self._drain(quiet=1.0, timeout=6.0, need_prompt=False)
            if out:
                empty_all = False
            if self._looks_valid(out) and (PROMPT_ANYWHERE_RE.search(out)
                                           or "login:" in out.lower()
                                           or "AlliedWare" in out):
                return baud, out
        return None, ("no_response (powered off / absent)" if empty_all
                      else "garbage at all bauds (unknown baud / not an AW+ console)")

    def capture_banner(self, initial):
        m = LOGIN_RE.search(initial.rstrip()[-120:]) or LOGIN_RE.search(initial)
        if m:
            return m.group(1), initial
        self._send("end", quiet=0.5, timeout=8.0, need_prompt=False)
        out = self._send("logout", quiet=1.0, timeout=12.0, need_prompt=False)
        m = LOGIN_RE.search(out.rstrip()[-160:]) or LOGIN_RE.search(out)
        return (m.group(1) if m else None), out

    def login(self):
        self.s.write(b"\r")
        out = self._drain(quiet=1.0, timeout=8.0, need_prompt=False)
        if "login:" in out.lower():
            self.s.write((USERNAME + "\r").encode())
            self._drain(quiet=1.0, timeout=10.0, need_prompt=False)
            for pw in PASSWORDS:
                self.s.write((pw + "\r").encode())
                out = self._drain(quiet=1.2, timeout=12.0, need_prompt=False)
                if "new password" in out.lower():
                    return False, "forced password-change dialog; refused"
                if PROMPT_ANYWHERE_RE.search(out):
                    break
                if "login:" in out.lower():
                    self.s.write((USERNAME + "\r").encode())
                    self._drain(quiet=1.0, timeout=10.0, need_prompt=False)
        if "new password" in out.lower():
            return False, "forced password-change dialog; refused"
        if not PRIV_RE.search(out.rstrip()[-120:]):
            self.s.write(b"enable\r")
            out = self._drain(quiet=1.0, timeout=15.0, need_prompt=False)
            if "password" in out.lower() and not PRIV_ANYWHERE_RE.search(out):
                self.s.write((PASSWORDS[0] + "\r").encode())
                out = self._drain(quiet=1.0, timeout=12.0, need_prompt=False)
        self._send("end", quiet=0.4, timeout=8.0, need_prompt=False)
        self._send("terminal length 0", quiet=0.5, timeout=8.0, need_prompt=False)
        out = self._send("terminal no monitor", quiet=0.5, timeout=8.0, need_prompt=False)
        if PRIV_ANYWHERE_RE.search(out) or PRIV_RE.search(out.rstrip()[-120:]):
            return True, "privileged"
        if PROMPT_ANYWHERE_RE.search(out):
            return True, "user-exec only (could not reach #; privileged commands will be invalid)"
        return False, "no prompt after login. tail={!r}".format(out[-160:])

    def run_cmd(self, cmd, timeout=45.0):
        raw = self._send(cmd, quiet=0.8, timeout=timeout, need_prompt=True)
        lines = raw.splitlines()
        if lines and cmd in lines[0]:
            lines = lines[1:]
        while lines and PROMPT_RE.search(lines[-1].rstrip()):
            lines.pop()
        return "\n".join(lines).strip()

    def close(self):
        try:
            if self.s:
                self.s.close()
        except Exception:
            pass


def fuser_holder(port):
    r = subprocess.run(["fuser", "-v", port], capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def host_nics():
    """{ethN: {mac, carrier_up, ipv4, _ip}} for host NICs, newest kernel order."""
    nics = {}
    base = "/sys/class/net"
    for n in sorted(os.listdir(base)):
        if not n.startswith("eth"):
            continue

        def _read(f):
            try:
                return open(os.path.join(base, n, f)).read().strip()
            except Exception:
                return ""
        ip = None
        try:
            r = subprocess.run(["ip", "-4", "-o", "addr", "show", n],
                               capture_output=True, text=True)
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", r.stdout)
            if m:
                ip = (m.group(1), int(m.group(2)))
        except Exception:
            pass
        nics[n] = {"mac": _read("address"), "carrier_up": _read("carrier") == "1",
                   "ipv4": "{}/{}".format(*ip) if ip else None, "_ip": ip}
    return nics


def force_arp(nics):
    """Flood a who-has out each up NIC so the switches learn its MAC on ingress."""
    for n, info in nics.items():
        if not info["carrier_up"] or not info["_ip"]:
            continue
        ip, _ = info["_ip"]
        oct_ = ip.split(".")
        oct_[-1] = str((int(oct_[-1]) + 2) % 256)          # a likely-unanswered nbr
        subprocess.run(["ping", "-c1", "-w1", "-I", n, ".".join(oct_)],
                       capture_output=True)


def probe_console(path, host_macs):
    rec = {"path": path, "status": None, "baud": None, "banner_hostname": None,
           "login": None, "commands": {}, "per_member_flash": {},
           "host_mac_lookups": {}, "notes": []}
    if not os.path.exists(path):
        rec["status"] = "absent"
        return rec
    if subprocess.run(["fuser", "-s", path]).returncode == 0:
        rec["status"] = "busy"
        rec["notes"].append("held by: " + fuser_holder(path))
        return rec
    p = Probe(path)
    try:
        baud, initial = p.detect_baud()
        if baud is None:
            rec["status"] = "unreachable"
            rec["notes"].append(initial)
            return rec
        rec["baud"] = baud
        rec["banner_hostname"], _ = p.capture_banner(initial)
        ok, note = p.login()
        rec["login"] = note
        if not ok:
            rec["status"] = "login_failed"
            return rec
        rec["status"] = "ok"
        for cmd in COMMANDS:
            try:
                rec["commands"][cmd] = p.run_cmd(cmd)
            except Exception as e:
                rec["commands"][cmd] = "!! probe error: {}: {}".format(type(e).__name__, e)
        # 3a: per-member flash -- a stack console relays to the master, so `dir`
        # shows only the master's flash. List each member's OWN flash explicitly.
        ids = stack_member_ids(rec["commands"].get("show stack", ""))
        if len(ids) > 1:
            for mid in ids:
                try:
                    rec["per_member_flash"][str(mid)] = p.run_cmd(
                        "dir awplus-{}/flash:".format(mid))
                except Exception as e:
                    rec["per_member_flash"][str(mid)] = "!! {}: {}".format(
                        type(e).__name__, e)
        # 3b: host-edge -- where did each host NIC's MAC land on THIS switch?
        for nic, dm in (host_macs or {}).items():
            try:
                rec["host_mac_lookups"][nic] = p.run_cmd(
                    "show mac address-table | include " + dm)
            except Exception as e:
                rec["host_mac_lookups"][nic] = "!! {}: {}".format(type(e).__name__, e)
    except Exception as e:
        rec["status"] = rec["status"] or "error"
        rec["notes"].append("{}: {}".format(type(e).__name__, e))
    finally:
        p.close()
    return rec


def _first(patterns, text):
    for pat in patterns:
        m = re.search(pat, text or "", re.I)
        if m:
            return m.group(1).strip()
    return None


def summarize(rec):
    sys_out = rec["commands"].get("show system", "")
    ver = rec["commands"].get("show version", "")
    stk = rec["commands"].get("show stack", "")
    dtl = rec["commands"].get("show stack detail", "")
    ser_out = rec["commands"].get("show system serialnumber", "")
    model = _first([r"Product type\s*[:.]\s*(\S+)", r"\b(AT-[\w-]+)"], dtl + "\n" + sys_out)
    serials = re.findall(r"\b\d{2,3}[A-Z]\d{4,6}\b", sys_out + "\n" + ser_out)
    serial = ",".join(dict.fromkeys(serials)) or _first(
        [r"Serial [Nn]umber\s*[:.]*\s*([A-Z0-9]+)"], sys_out)
    swver = _first([r"Software version\s*[:.]\s*(\S+)", r"Build name\s*[:.]\s*(\S+)"], sys_out) or \
        _first([r"Build name\s*[:.]\s*(\S+)"], ver)
    role = role_for(rec.get("banner_hostname"), stk)
    return {"banner": rec.get("banner_hostname"), "model": model, "serial": serial,
            "sw": swver, "stack_role": role}


def derive_host_edges(host, consoles):
    """host NIC -> the switch physical port(s) that learned its MAC. Stack consoles
    relay to one CLI and agree, so ports dedupe; a physical `portX.0.Y` is the
    cabled edge (member X), a trunk/`saN` is arrival via aggregation, not the edge."""
    edges = {}
    for nic, info in host.items():
        ports = set()
        for rec in consoles.values():
            look = (rec.get("host_mac_lookups") or {}).get(nic, "") or ""
            for line in look.splitlines():
                pm = PHYS_PORT_RE.search(line)
                if pm:
                    ports.add((pm.group(1), int(pm.group(2))))
        edges[nic] = {"mac": info["mac"], "carrier_up": info["carrier_up"],
                      "ipv4": info["ipv4"],
                      "physical_ports": sorted(p for p, _ in ports),
                      "members": sorted({m for _, m in ports})}
    return edges


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--consoles", default="0-6",
                    help="range/list of /dev/uN, e.g. 0-6 or 2,3,4,5 (default 0-6)")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-console summary")
    args = ap.parse_args(argv)

    nums = []
    for part in args.consoles.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            nums += list(range(int(a), int(b) + 1))
        elif part:
            nums.append(int(part))

    host = host_nics()
    force_arp(host)                                        # learn NIC MACs on ingress
    host_macs = {n: mac_dotted(i["mac"]) for n, i in host.items() if i["mac"]}

    result = {"probe_meta": {"tool": "bench_probe.py", "version": 2,
                             "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "host": os.uname().nodename,
                             "consoles": ["/dev/u{}".format(n) for n in nums],
                             "commands": COMMANDS},
              "host": {n: {k: i[k] for k in ("mac", "carrier_up", "ipv4")}
                       for n, i in host.items()},
              "consoles": {}}

    for n in nums:
        path = "/dev/u{}".format(n)
        if not args.quiet:
            print("probing {} ...".format(path), file=sys.stderr, flush=True)
        rec = probe_console(path, host_macs)
        result["consoles"]["u{}".format(n)] = rec
        if not args.quiet:
            s = summarize(rec) if rec["status"] == "ok" else {}
            print("  u{}: {} baud={} banner={} model={} serial={} sw={} role={}".format(
                n, rec["status"], rec["baud"], rec.get("banner_hostname"),
                s.get("model"), s.get("serial"), s.get("sw"), s.get("stack_role")),
                file=sys.stderr, flush=True)

    result["host_edges"] = derive_host_edges(host, result["consoles"])
    if not args.quiet:
        print("\nhost edges:", file=sys.stderr)
        for nic, e in result["host_edges"].items():
            print("  {} ({}, carrier={}) -> {} member(s) {}".format(
                nic, e["ipv4"], e["carrier_up"],
                e["physical_ports"] or "(not learned)", e["members"]),
                file=sys.stderr)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
