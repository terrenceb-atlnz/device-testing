#!/usr/bin/env python3
"""bench_probe.py -- the SOLE SOURCE OF TRUTH for the tb470 bench.

Sweeps /dev/u0..u6 IDENTICALLY on every run and drives each console directly
over pyserial. It depends on NOTHING else: no AT framework, no tb470.setup, no
bench-state.md. It is the tool that FEEDS bench-state.md (which generates
tb470.setup) -- never the reverse -- so it must never read either of them.

For every console it: checks the node exists and is free (never collides with a
live session), auto-detects baud (115200 then 9600), forces the login banner to
identify the physical unit, logs in if needed, and captures one FIXED set of
read-only `show` commands. Output: JSON (machine source of truth) + a summary.

Run ON tb470 (the consoles are local to it); serial access needs no sudo:
    python3 bench_probe.py [--consoles 0-6] [--json out.json] [--quiet]
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

# Any prompt (user `>` or privileged `#`) -- "the console is alive / a command finished".
PROMPT_RE = re.compile(r"[\w.-]+(?:\([\w -]+\))?[#>][ \t]*$")
PROMPT_ANYWHERE_RE = re.compile(r"(?:^|\r?\n)[\w.-]+(?:\([\w -]+\))?[#>]")
# PRIVILEGED prompt only (`#`). Many `show` commands (boot, running-config, dir,
# file systems, cpu, spanning-tree) are invalid at user exec `>`, so we must
# reach `#` before running the set -- never treat `>` as "logged in".
PRIV_RE = re.compile(r"[\w.-]+(?:\([\w -]+\))?#[ \t]*$")
PRIV_ANYWHERE_RE = re.compile(r"(?:^|\r?\n)[\w.-]+(?:\([\w -]+\))?#")
LOGIN_RE = re.compile(r"([\w.-]+) login:\s*$")
PRINTABLE = set(bytes(range(0x20, 0x7F))) | {0x09, 0x0A, 0x0D}


class Probe:
    def __init__(self, port):
        self.port = port
        self.s = None
        self.baud = None

    # ---- low level ----
    def _open(self, baud):
        os.system("stty -F {} -hupcl 2>/dev/null".format(os.path.realpath(self.port)))
        self.s = serial.Serial(self.port, baud, timeout=0.2)
        self.baud = baud

    def _drain(self, quiet=0.8, timeout=30.0, need_prompt=False):
        """Read until `quiet`s of silence; with need_prompt, keep going through
        silence until a prompt appears (SPIFlash/slow commands stay silent for
        minutes -- only a prompt or the timeout ends the wait)."""
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

    # ---- baud + identity ----
    @staticmethod
    def _looks_valid(raw):
        if not raw:
            return False
        good = sum(1 for c in raw.encode(errors="replace") if c in PRINTABLE)
        return good / max(1, len(raw)) > 0.85

    def detect_baud(self):
        """Return (baud, initial_output) or (None, reason)."""
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
        # nothing sensible at any baud
        return None, ("no_response (powered off / absent)" if empty_all
                      else "garbage at all bauds (unknown baud / not an AW+ console)")

    def capture_banner(self, initial):
        """Force the login banner so the physical unit is identifiable, and
        return (banner_hostname, raw). On a formed stack a backup console shows
        `awplus-N login:`; the master shows bare `awplus login:`."""
        m = LOGIN_RE.search(initial.rstrip()[-120:]) or LOGIN_RE.search(initial)
        if m:
            return m.group(1), initial
        # Logged in already -> escape any config mode, log out to reveal banner.
        self._send("end", quiet=0.5, timeout=8.0, need_prompt=False)
        out = self._send("logout", quiet=1.0, timeout=12.0, need_prompt=False)
        m = LOGIN_RE.search(out.rstrip()[-160:]) or LOGIN_RE.search(out)
        return (m.group(1) if m else None), out

    def login(self):
        """Reach a PRIVILEGED (`#`) prompt. Returns (ok, note)."""
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
                if "login:" in out.lower():          # wrong pw -> re-feed username
                    self.s.write((USERNAME + "\r").encode())
                    self._drain(quiet=1.0, timeout=10.0, need_prompt=False)
        if "new password" in out.lower():
            return False, "forced password-change dialog; refused"
        # Ensure PRIVILEGED exec -- `enable` if we are only at user exec `>`.
        if not PRIV_RE.search(out.rstrip()[-120:]):
            self.s.write(b"enable\r")
            out = self._drain(quiet=1.0, timeout=15.0, need_prompt=False)
            if "password" in out.lower() and not PRIV_ANYWHERE_RE.search(out):
                self.s.write((PASSWORDS[0] + "\r").encode())
                out = self._drain(quiet=1.0, timeout=12.0, need_prompt=False)
        # Deterministic session state: escape config mode, no paging, no logs.
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


def probe_console(path):
    rec = {"path": path, "status": None, "baud": None, "banner_hostname": None,
           "login": None, "commands": {}, "notes": []}
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
    role = _first([r"(Active Master|Backup Member|Standalone unit)"], stk)
    return {"banner": rec.get("banner_hostname"), "model": model, "serial": serial,
            "sw": swver, "stack_role": role}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--consoles", default="0-6",
                    help="range/list of /dev/uN, e.g. 0-6 or 2,3,4,5 (default 0-6)")
    ap.add_argument("--json", metavar="FILE", help="write the full capture here (default: stdout)")
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

    result = {"probe_meta": {"tool": "bench_probe.py", "version": 1,
                             "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "host": os.uname().nodename,
                             "consoles": ["/dev/u{}".format(n) for n in nums],
                             "commands": COMMANDS},
              "consoles": {}}

    for n in nums:
        path = "/dev/u{}".format(n)
        if not args.quiet:
            print("probing {} ...".format(path), file=sys.stderr, flush=True)
        rec = probe_console(path)
        result["consoles"]["u{}".format(n)] = rec
        if not args.quiet:
            s = summarize(rec) if rec["status"] == "ok" else {}
            print("  u{}: {} baud={} banner={} model={} serial={} sw={} role={}".format(
                n, rec["status"], rec["baud"], rec.get("banner_hostname"),
                s.get("model"), s.get("serial"), s.get("sw"), s.get("stack_role")),
                file=sys.stderr, flush=True)

    out = json.dumps(result, indent=2)
    if args.json:
        with open(args.json, "w") as f:
            f.write(out)
        if not args.quiet:
            print("\nfull capture -> {}".format(args.json), file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
