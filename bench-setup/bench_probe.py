#!/usr/bin/env python3
"""bench_probe.py -- the one bench-state tool for tb470 (consolidated 2026-09-25).

It sees what is actually THERE and nothing else. Four steps, one script:

  1. capture   read a short, fixed list of `show` commands from every console
               (/dev/u0..u6 over pyserial, ON tb470) and save the raw output under
               captures/<UTC stamp>/ so the parser can be re-run without the bench.
  2. generate  parse a capture offline into bench-state.md: a device table, the links,
               advisories, and ONE ```setup fence that IS the tb470.setup.
  3. diff      compare that fence against the deployed tb470.setup (the intended
               template), ignoring comments and ordering.
               Exit 0 MATCH / 1 MISMATCH / 2 NEEDS-CHECK.
  4. apply     (optional) write the fence to the box as tb470.setup: snapshot the
               outgoing pair into backups/ first, write in place, verify by readback.

    bench_probe.py run [--consoles 0-6] [--template PATH]    # 1 -> 2 -> 3, ON tb470
    bench_probe.py capture [--consoles 0-6]                  # 1 only, ON tb470
    bench_probe.py generate captures/<stamp>                 # 2 only, anywhere
    bench_probe.py diff [live.md|.setup] [template.setup]    # 3 only, anywhere
    bench_probe.py render                                    # print what apply would write
    bench_probe.py apply [--force]                           # 4, from tb470 or the dev host

It holds no bench facts of its own. The facts no `show` command can reveal -- a unit's
swi_ name, its PDU outlet, the PDU's IP -- live in tb470.static, entered once by the
user (the script asks when it meets a unit it has no name for, if it has a terminal).
bench-state.md carries nothing beyond what the run measured (Terrence, 2026-09-25).

LLDP is what proves switch-to-switch cabling, so a device found with `lldp run` OFF
gets it switched on for the capture and OFF again at the end (running-config only;
nothing is written). Devices that already ran LLDP are left alone.

Captures are raw text, one file per command per console, plus meta.json. They are not
committed (captures/ is gitignored); the generated bench-state.md names its source.
"""
import argparse
import configparser
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "bench-state.md")            # generated, measured state only
STATE_MIRROR = os.path.join(HERE, "bench-state.current.md")   # the last APPLIED version
CURRENT = os.path.join(HERE, "tb470.setup.current")     # local copy of the deployed file
STATIC = os.path.join(HERE, "tb470.static")             # hand-entered facts (names, PDU)
CAPTURES = os.path.join(HERE, "captures")
BACKUPS = os.path.join(HERE, "backups")

BOX = "tb470"
REMOTE = "/home/st-art/st-art/configs/tb470.setup"
SOCK = "/run/user/1971/keyring/ssh"                     # the agent that holds the key

BAUDS = [115200, 9600]
USERNAME = "manager"
PASSWORDS = ["friend", "P@ssw0rd", "awplus"]
LLDP_SETTLE = 35            # seconds for neighbours to appear after `lldp run`

# What we capture, the same way every time. `show system` carries every member's model,
# serial and bootloader; `show stack` the membership and MACs; `show mac address-table`
# the device's own CPU MACs (LLDP chassis IDs) and where each host NIC landed; LLDP the
# switch-to-switch cabling; `show boot` the boot source; `show running-config` is saved
# for a plain `diff` against a recorded .cfg.
COMMANDS = [
    "show system",
    "show stack",
    "show boot",
    "show interface status",
    "show lldp neighbors",
    "show mac address-table",
    "show running-config",
]
CMD_TIMEOUT = {"show running-config": 120.0, "show interface status": 90.0}

PROMPT_RE = re.compile(r"([\w.-]+)(?:\([\w -]+\))?[#>][ \t]*$")
PROMPT_ANYWHERE_RE = re.compile(r"(?:^|\r?\n)([\w.-]+)(?:\([\w -]+\))?[#>]")
PRIV_RE = re.compile(r"[\w.-]+(?:\([\w -]+\))?#[ \t]*$")
PRIV_ANYWHERE_RE = re.compile(r"(?:^|\r?\n)[\w.-]+(?:\([\w -]+\))?#")
LOGIN_RE = re.compile(r"([\w.-]+) login:\s*$")
MAC_RE = r"[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4}"
PHYS_PORT_RE = re.compile(r"^port(\d+)\.\d+\.\d+$")
PRINTABLE = set(bytes(range(0x20, 0x7F))) | {0x09, 0x0A, 0x0D}
LETTERS = "abcdefghijklmnop"


def utc_stamp():
    return time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())


def sha(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def mac_dotted(mac):
    h = re.sub(r"[^0-9a-fA-F]", "", mac or "").lower()
    return "{}.{}.{}".format(h[0:4], h[4:8], h[8:12]) if len(h) == 12 else (mac or "")


# =============================================================================
# 1. capture -- the console driver (pyserial, ON tb470)
# =============================================================================

class Probe:
    """One console. Opens with -hupcl (a DTR drop reads as a BREAK to the IE520), detects
    the baud, forces the login banner to learn which unit this is, logs in to `#`."""

    def __init__(self, port):
        self.port = port
        self.s = None
        self.baud = None
        self.slow = 1.0          # quiet-time multiplier; 9600 needs longer waits

    def _open(self, baud):
        import serial
        os.system("stty -F {} -hupcl 2>/dev/null".format(os.path.realpath(self.port)))
        self.s = serial.Serial(self.port, baud, timeout=0.2)
        self.baud = baud
        self.slow = 2.0 if baud <= 9600 else 1.0

    def _drain(self, quiet=0.8, timeout=30.0, need_prompt=False):
        buf = ""
        quiet *= self.slow
        deadline = time.time() + timeout
        last = time.time()
        while time.time() < deadline:
            chunk = self.s.read(4096)
            if chunk:
                buf += chunk.decode(errors="replace").replace("\x00", "")
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
        if not raw.strip():
            return False
        good = sum(1 for c in raw.encode(errors="replace") if c in PRINTABLE)
        return good / max(1, len(raw)) > 0.85

    def detect_baud(self):
        """Try each baud twice: a bare CR must draw printable text with a prompt, a
        login: or a banner. NULs are stripped first (the x230 at the wrong rate sends
        them, and at the right rate the first byte can be one -- 2026-09-23 defect)."""
        notes = []
        for baud in BAUDS:
            for _ in range(2):
                try:
                    if self.s:
                        self.s.close()
                    self._open(baud)
                    self.s.reset_input_buffer()
                except Exception as e:
                    return None, "open failed: {}: {}".format(type(e).__name__, e)
                self.s.write(b"\r")
                out = self._drain(quiet=1.0, timeout=6.0, need_prompt=False)
                low = out.lower()
                if self._looks_valid(out) and (PROMPT_ANYWHERE_RE.search(out)
                                               or "login:" in low or "password:" in low
                                               or "alliedware" in low):
                    return baud, out
                notes.append("{}: {}".format(baud, "silent" if not out.strip()
                                             else "garbage {!r}".format(out[-32:])))
        return None, ("no_response (powered off / absent)" if all("silent" in n for n in notes)
                      else "no AW+ prompt at any baud: " + "; ".join(notes))

    def capture_banner(self, initial):
        m = LOGIN_RE.search(initial.rstrip()[-120:]) or LOGIN_RE.search(initial)
        if m:
            return m.group(1)
        self._send("end", quiet=0.5, timeout=8.0, need_prompt=False)
        out = self._send("logout", quiet=1.0, timeout=12.0, need_prompt=False)
        m = LOGIN_RE.search(out.rstrip()[-160:]) or LOGIN_RE.search(out)
        return m.group(1) if m else None

    def login(self):
        self.s.write(b"\r")
        out = self._drain(quiet=1.0, timeout=8.0, need_prompt=False)
        if "password:" in out.lower() and "login:" not in out.lower():
            self.s.write(b"\r")                      # port left mid-dialog: reset it
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
            return True, "user-exec only (could not reach #)"
        return False, "no prompt after login. tail={!r}".format(out[-160:])

    def hostname(self):
        out = self._send("", quiet=0.4, timeout=6.0, need_prompt=True)
        m = PROMPT_RE.search(out.rstrip())
        return m.group(1) if m else None

    def run_cmd(self, cmd, timeout=45.0):
        raw = self._send(cmd, quiet=0.8, timeout=timeout, need_prompt=True)
        lines = raw.splitlines()
        if lines and cmd in lines[0]:
            lines = lines[1:]
        while lines and PROMPT_RE.search(lines[-1].rstrip()):
            lines.pop()
        return "\n".join(lines).strip()

    def config(self, *lines):
        """Send config lines and return to exec. Running-config only; never `write`."""
        self._send("configure terminal", quiet=0.5, timeout=10.0)
        for ln in lines:
            self._send(ln, quiet=0.5, timeout=10.0)
        self._send("end", quiet=0.4, timeout=8.0)

    def close(self):
        try:
            if self.s:
                self._send("end", quiet=0.3, timeout=4.0, need_prompt=False)
                self.s.close()
        except Exception:
            pass


def _sudo_ok():
    return subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode == 0


def console_holder(path, use_sudo):
    """Who holds the node, or '' if nobody. Root-owned holders are invisible without sudo."""
    pre = ["sudo", "-n"] if use_sudo else []
    r = subprocess.run(pre + ["fuser", "-v", path], capture_output=True, text=True)
    return (r.stdout + r.stderr).strip() if r.returncode == 0 else ""


def host_nics():
    """{ethN: {mac, carrier_up, ipv4}} for the testbox's own NICs."""
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
        ipv4 = None
        r = subprocess.run(["ip", "-4", "-o", "addr", "show", n], capture_output=True, text=True)
        m = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", r.stdout)
        if m:
            ipv4 = m.group(1)
        nics[n] = {"mac": _read("address"), "carrier_up": _read("carrier") == "1", "ipv4": ipv4}
    return nics


def force_learn(nics):
    """Ping a likely-unanswered neighbour out of each up NIC so the switch on the far
    end learns the NIC's MAC on its ingress port."""
    for n, info in nics.items():
        if not info["carrier_up"] or not info["ipv4"]:
            continue
        ip = info["ipv4"].split("/")[0].split(".")
        ip[-1] = str((int(ip[-1]) + 2) % 256)
        subprocess.run(["ping", "-c1", "-w1", "-I", n, ".".join(ip)], capture_output=True)


def _open_console(path, use_sudo):
    rec = {"path": path, "status": None, "baud": None, "banner": None, "hostname": None,
           "login": None, "lldp": None, "notes": [], "commands": {}}
    if not os.path.exists(path):
        rec["status"] = "absent"
        return rec, None
    holder = console_holder(path, use_sudo)
    if holder:
        rec["status"] = "busy"
        rec["notes"].append("held by: " + " ".join(holder.split()))
        return rec, None
    p = Probe(path)
    try:
        baud, initial = p.detect_baud()
        if baud is None:
            rec["status"] = "unreachable"
            rec["notes"].append(initial)
            p.close()
            return rec, None
        rec["baud"] = baud
        rec["banner"] = p.capture_banner(initial)
        ok, note = p.login()
        rec["login"] = note
        if not ok:
            rec["status"] = "login_failed"
            p.close()
            return rec, None
        rec["hostname"] = p.hostname()
        rec["status"] = "ok"
        return rec, p
    except Exception as e:
        rec["status"] = "error"
        rec["notes"].append("{}: {}".format(type(e).__name__, e))
        p.close()
        return rec, None


def _slug(cmd):
    return cmd.replace(" ", "_")


def capture(nums, out_dir=None, quiet=False):
    """Read every console and save the raw output. Returns the capture directory."""
    stamp = utc_stamp()
    out_dir = out_dir or os.path.join(CAPTURES, stamp)
    os.makedirs(out_dir, exist_ok=True)
    say = (lambda *a: None) if quiet else (lambda *a: print(*a, file=sys.stderr, flush=True))
    use_sudo = _sudo_ok()
    paths = ["/dev/u{}".format(n) for n in nums]
    recs, probes = {}, {}
    lock = threading.Lock()

    # Phase A -- open, identify and log in to every console at once.
    def _a(path):
        rec, p = _open_console(path, use_sudo)
        with lock:
            recs[path] = rec
            if p:
                probes[path] = p
        say("  {}: {} baud={} banner={} hostname={} {}".format(
            path, rec["status"], rec["baud"], rec["banner"], rec["hostname"],
            "; ".join(rec["notes"])))
    say("opening {} ...".format(", ".join(paths)))
    threads = [threading.Thread(target=_a, args=(path,)) for path in paths]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    enabled = []            # consoles where WE switched lldp on; reverted in `finally`
    try:
        # Phase B -- LLDP, one console at a time so the stack's second console sees it
        # already on and only one console reverts it.
        for path in paths:
            p = probes.get(path)
            if not p:
                continue
            o = p.run_cmd("show running-config | include lldp run", timeout=20)
            on = any(ln.strip() == "lldp run" for ln in o.splitlines())
            if on:
                recs[path]["lldp"] = "on"
            else:
                p.config("lldp run")
                o = p.run_cmd("show running-config | include lldp run", timeout=20)
                if any(ln.strip() == "lldp run" for ln in o.splitlines()):
                    recs[path]["lldp"] = "enabled-for-capture"
                    enabled.append(path)
                    say("  {}: lldp run was OFF -> on for this capture".format(path))
                else:
                    recs[path]["lldp"] = "off (could not enable)"
                    recs[path]["notes"].append("lldp run refused; cabling from this device unproven")
        if enabled:
            say("waiting {}s for LLDP neighbours to appear ...".format(LLDP_SETTLE))
            time.sleep(LLDP_SETTLE)

        nics = host_nics()
        force_learn(nics)

        # Phase C -- the fixed command list, all consoles at once, raw to disk.
        def _c(path):
            p = probes[path]
            rec = recs[path]
            for cmd in COMMANDS:
                fn = "{}.{}.txt".format(os.path.basename(path), _slug(cmd))
                try:
                    txt = p.run_cmd(cmd, timeout=CMD_TIMEOUT.get(cmd, 45.0))
                except Exception as e:
                    txt = "!! probe error: {}: {}".format(type(e).__name__, e)
                    rec["notes"].append("{}: {}".format(cmd, e))
                io.open(os.path.join(out_dir, fn), "w", encoding="utf-8").write(txt + "\n")
                rec["commands"][cmd] = fn
        say("capturing {} commands per console ...".format(len(COMMANDS)))
        threads = [threading.Thread(target=_c, args=(path,)) for path in probes]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        for path in enabled:
            p = probes.get(path)
            if not p:
                continue
            try:
                p.config("no lldp run")
                o = p.run_cmd("show running-config | include lldp run", timeout=20)
                if any(ln.strip() == "lldp run" for ln in o.splitlines()):
                    recs[path]["notes"].append("!! `no lldp run` did not take -- remove it by hand")
                    say("  {}: !! lldp run is STILL on -- remove it by hand".format(path))
                else:
                    say("  {}: lldp run -> off again".format(path))
            except Exception as e:
                recs[path]["notes"].append("!! lldp revert failed: {} -- remove it by hand".format(e))
        for p in probes.values():
            p.close()

    meta = {"tool": "bench_probe.py", "version": 3, "utc": stamp, "host": os.uname().nodename,
            "commands": COMMANDS, "consoles": recs, "host_nics": nics}
    io.open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8").write(
        json.dumps(meta, indent=2, sort_keys=True))
    say("capture -> {}".format(out_dir))
    return out_dir


# =============================================================================
# 2. generate -- parse a capture offline into bench-state.md
# =============================================================================

def parse_show_system(text):
    """[{member, model, rev, serial, bootloader}], software. A stack prints one
    'Stack member N' block per member; a standalone prints one Base row."""
    boards, member, software = [], None, None
    for ln in (text or "").splitlines():
        m = re.match(r"^\s*Stack member (\d+)\s*$", ln)
        if m:
            member = int(m.group(1))
            continue
        m = re.match(r"^\s*Base\s+\d+\s+Base\s+(.+?)\s+(\S+)\s+(\S+)\s*$", ln)
        if m:
            boards.append({"member": member, "model": m.group(1).strip(), "rev": m.group(2),
                           "serial": m.group(3), "bootloader": None})
            continue
        m = re.match(r"^\s*Bootloader version\s*:\s*(\S+)", ln)
        if m and boards:
            boards[-1]["bootloader"] = m.group(1)
            continue
        # the BUILD, never the filename: `Current software` is the constant-by-convention
        # IE520-tb470.rel; `Software version` carries the dated build name
        m = re.match(r"^\s*Software version\s*:\s*(\S+)", ln)
        if m:
            software = m.group(1)
            continue
        m = re.match(r"^\s*Current software\s*:\s*(\S+)", ln)
        if m and not software:
            software = m.group(1)
    return boards, software


def parse_show_stack(text):
    """{members: {id: {mac, prio, status, role}}, oper, stack_mac}. Rows without a MAC
    (Provisioned) are dropped; a device that cannot stack yields no members."""
    members, oper, smac = {}, None, None
    for ln in (text or "").splitlines():
        m = re.match(r"^\s*(\d+)\s+\S+\s+(" + MAC_RE + r")\s+(\d+)\s+(\S+)\s+(.+?)\s*$", ln)
        if m:
            members[int(m.group(1))] = {"mac": m.group(2), "prio": int(m.group(3)),
                                        "status": m.group(4), "role": m.group(5)}
            continue
        m = re.match(r"^\s*Operational Status\s+(.+?)\s*$", ln)
        if m:
            oper = m.group(1)
        m = re.match(r"^\s*Stack MAC address\s+(" + MAC_RE + r")", ln)
        if m:
            smac = m.group(1)
    return {"members": members, "oper": oper, "stack_mac": smac}


def parse_show_boot(text):
    for ln in (text or "").splitlines():
        m = re.match(r"^\s*Current boot image\s*:\s*(\S+)", ln)
        if m:
            return {"image": m.group(1), "flash": m.group(1).lower().startswith("flash:")}
    return {"image": None, "flash": None}


def parse_if_status(text):
    st = {}
    for ln in (text or "").splitlines():
        m = re.match(r"^\s*((?:port\d+\.\d+\.\d+)|eth\d+|sa\d+|po\d+)\s+.*?\b"
                     r"(connected|notconnect|disabled|err-?disabled)\b", ln)
        if m:
            st[m.group(1)] = m.group(2)
    return st


def parse_lldp(text):
    """rows: (local port, neighbour chassis MAC, neighbour port id, rest). Local ports
    print without the 'port' prefix ('3.0.2'); it is added back."""
    rows, total = [], None
    for ln in (text or "").splitlines():
        m = re.match(r"^\s*Total number of neighbors on these ports\s*\.*\s*(\d+)", ln)
        if m:
            total = int(m.group(1))
            continue
        m = re.match(r"^\s*((?:port)?\d+\.\d+\.\d+|eth\d+)\s+(" + MAC_RE + r")\s+(\S+)\s*(.*)$", ln)
        if m:
            lp = m.group(1)
            if lp[0].isdigit():
                lp = "port" + lp
            rows.append((lp, m.group(2), m.group(3), m.group(4).strip()))
    return {"rows": rows, "total": total}


def parse_mac_table(text):
    rows = []
    for ln in (text or "").splitlines():
        m = re.match(r"^\s*(\d+)\s+(\S+)\s+(" + MAC_RE + r")\s+(\S+)\s+(\S+)", ln)
        if m:
            rows.append((int(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)))
    return rows


def load_static(path=STATIC):
    """tb470.static: [pdu] ip, [units] serial = name, outlet. Missing file -> empty."""
    cp = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=("#",))
    cp.optionxform = str
    units, pdu = {}, None
    if os.path.exists(path):
        cp.read(path, encoding="utf-8")
        pdu = cp.get("pdu", "ip", fallback=None)
        for serial, val in (cp.items("units") if cp.has_section("units") else []):
            parts = [x.strip() for x in val.split(",")]
            name = parts[0]
            outlet = parts[1] if len(parts) > 1 and parts[1] not in ("", "-", "?") else None
            units[serial] = {"name": name, "outlet": outlet}
    return {"pdu": pdu, "units": units}


def save_static_unit(serial, name, outlet, note, path=STATIC):
    with io.open(path, "a", encoding="utf-8") as f:
        f.write("{} = {}, {}{}\n".format(serial, name, outlet or "-",
                                         ("    ### " + note) if note else ""))


def load_capture(cap_dir):
    meta = json.load(io.open(os.path.join(cap_dir, "meta.json"), encoding="utf-8"))
    for rec in meta["consoles"].values():
        rec["out"] = {}
        for cmd, fn in (rec.get("commands") or {}).items():
            fp = os.path.join(cap_dir, fn)
            rec["out"][cmd] = io.open(fp, encoding="utf-8").read() if os.path.exists(fp) else ""
    return meta


class Dev:
    """One physical unit: a stack member or a standalone device."""
    def __init__(self, serial, model, member_id, console, banner, hostname, baud):
        self.serial, self.model, self.member_id = serial, model, member_id
        self.console, self.banner, self.hostname, self.baud = console, banner, hostname, baud
        self.name = None
        self.stack = None        # the Stack it belongs to, or None
        self.role = None
        self.bootloader = None
        self.boot = {"image": None, "flash": None}
        self.software = None
        self.rec = None          # the capture record whose outputs describe this device


class Stack:
    def __init__(self, key):
        self.key = key           # frozenset of member MACs
        self.members = {}        # id -> Dev
        self.rows = {}           # id -> show stack row
        self.stack_mac = None
        self.oper = None
        self.name = None
        self.rec = None          # one console's capture (all relay to the master CLI)


def build_model(meta):
    """Turn the capture into devices, stacks and their outputs."""
    stacks, devs, notes = {}, [], []
    for path in sorted(meta["consoles"], key=lambda p: int(re.sub(r"\D", "", p) or 0)):
        rec = meta["consoles"][path]
        if rec.get("status") != "ok":
            continue
        out = rec["out"]
        boards, software = parse_show_system(out.get("show system", ""))
        stk = parse_show_stack(out.get("show stack", ""))
        boot = parse_show_boot(out.get("show boot", ""))
        real = {i: r for i, r in stk["members"].items()}
        if len(real) >= 2:
            key = frozenset(r["mac"] for r in real.values())
            st = stacks.get(key)
            if st is None:
                st = stacks[key] = Stack(key)
                st.rows, st.stack_mac, st.oper, st.rec = real, stk["stack_mac"], stk["oper"], rec
                for b in boards:
                    if b["member"] in real:
                        d = Dev(b["serial"], b["model"], b["member"], None, None,
                                rec.get("hostname"), None)
                        d.stack, d.role = st, real[b["member"]]["role"]
                        d.bootloader, d.boot, d.software, d.rec = b["bootloader"], boot, software, rec
                        st.members[b["member"]] = d
                        devs.append(d)
                for mid in real:
                    if mid not in st.members:
                        notes.append("stack member {} ({}) has no `show system` block -- serial unknown"
                                     .format(mid, real[mid]["mac"]))
            # which member is THIS console on? bare hostname = master, hostname-N = member N
            host = rec.get("hostname") or ""
            ban = rec.get("banner") or ""
            mid = None
            m = re.match(re.escape(host) + r"-(\d+)$", ban) if host and ban else None
            if m and int(m.group(1)) in real:
                mid = int(m.group(1))
            elif ban and ban == host:
                mid = next((i for i, r in real.items() if "master" in r["role"].lower()), None)
            elif not ban:
                notes.append("{}: no login banner captured; member not identified".format(path))
            else:
                m = re.search(r"-(\d+)$", ban)
                if m and int(m.group(1)) in real:
                    mid = int(m.group(1))
                elif "-" not in ban[len(host):]:
                    mid = next((i for i, r in real.items() if "master" in r["role"].lower()), None)
            if mid is not None and mid in st.members:
                d = st.members[mid]
                if d.console and d.console != path:
                    notes.append("member {} answers on both {} and {}".format(mid, d.console, path))
                d.console, d.banner, d.baud = path, ban, rec.get("baud")
            elif mid is None:
                notes.append("{}: could not map banner {!r} to a stack member".format(path, ban))
        else:
            if not boards:
                notes.append("{}: no Base row in `show system`; device not identified".format(path))
                continue
            b = boards[0]
            member_id = next(iter(real)) if real else (b["member"] or 1)
            d = Dev(b["serial"], b["model"], member_id, path, rec.get("banner"),
                    rec.get("hostname"), rec.get("baud"))
            d.role = real[member_id]["role"] if real else "standalone"
            d.bootloader, d.boot, d.software, d.rec = b["bootloader"], boot, software, rec
            d.own_mac = real[member_id]["mac"] if real else None
            devs.append(d)
    return list(stacks.values()), devs, notes


def assign_names(devs, static, ask):
    """swi_ names come from tb470.static by serial. A unit not listed there gets the next
    free letter -- and, on a terminal, the user is asked once and the answer saved."""
    used = {u["name"] for u in static["units"].values()}
    notes = []
    for d in sorted(devs, key=lambda d: (d.stack is None, d.member_id or 0, d.serial)):
        u = static["units"].get(d.serial)
        if u:
            d.name = u["name"]
            d.outlet = u["outlet"]
            continue
        free = next(("swi_" + c for c in LETTERS if "swi_" + c not in used), None)
        d.name, d.outlet = free, None
        if ask:
            print("\nNew unit: {} S/N {} on {} (hostname {}).".format(
                d.model, d.serial, d.console or "?", d.hostname), file=sys.stderr)
            nm = input("  swi_ name [{}]: ".format(free)).strip() or free
            ol = input("  PDU outlet number (Enter if unknown): ").strip() or None
            d.name, d.outlet = nm, ol
            save_static_unit(d.serial, nm, ol, "{} {} -- added {}".format(
                d.model, d.console or "", time.strftime("%Y-%m-%d")))
            static["units"][d.serial] = {"name": nm, "outlet": ol}
            notes.append("added {} = {} to tb470.static".format(d.serial, nm))
        else:
            notes.append("unit {} S/N {} on {} is not in tb470.static -- named {} for this run; "
                         "add it there (name, PDU outlet)".format(d.model, d.serial, d.console, free))
        used.add(d.name)
    return notes


def mac_sets(stacks, devs):
    """Every MAC a device answers to: its CPU entries in the MAC table, its `show stack`
    MAC(s) and, for a stack, the Stack MAC (the virtual one is the LLDP chassis ID)."""
    owners = {}      # mac -> ("stack", Stack) | ("dev", Dev)
    for st in stacks:
        macs = set(st.key)
        if st.stack_mac:
            macs.add(st.stack_mac)
        for _, port, mac, _, _ in parse_mac_table(st.rec["out"].get("show mac address-table", "")):
            if port.upper() == "CPU":
                macs.add(mac)
        for m in macs:
            owners[m] = ("stack", st)
    for d in devs:
        if d.stack:
            continue
        macs = set()
        if getattr(d, "own_mac", None):
            macs.add(d.own_mac)
        for _, port, mac, _, _ in parse_mac_table(d.rec["out"].get("show mac address-table", "")):
            if port.upper() == "CPU":
                macs.add(mac)
        for m in macs:
            owners[m] = ("dev", d)
    return owners


def port_owner(kind, obj, port):
    """The Dev that owns a port on a stack (by the port's member prefix) or standalone."""
    if kind == "dev":
        return obj
    m = PHYS_PORT_RE.match(port)
    if m and int(m.group(1)) in obj.members:
        return obj.members[int(m.group(1))]
    return None


def derive_links(stacks, devs, meta):
    """(a, pa, b, pb, proof) for every cabled link LLDP can see, plus host edges."""
    owners = mac_sets(stacks, devs)
    hostname_of = {}
    for d in devs:
        if d.hostname:
            hostname_of[d.hostname] = ("stack", d.stack) if d.stack else ("dev", d)
    views = [("stack", st, st.rec) for st in stacks] + [("dev", d, d.rec) for d in devs if not d.stack]
    seen, links, notes = {}, [], []
    for kind, obj, rec in views:
        ll = parse_lldp(rec["out"].get("show lldp neighbors", ""))
        if ll["total"] is not None and ll["total"] > len(ll["rows"]):
            notes.append("{}: LLDP lists {} neighbours but {} rows parsed (non-MAC chassis IDs?)"
                         .format(rec["path"], ll["total"], len(ll["rows"])))
        for lp, chassis, rport, rest in ll["rows"]:
            a = port_owner(kind, obj, lp)
            if a is None:
                notes.append("{}: LLDP local port {} belongs to no known member".format(rec["path"], lp))
                continue
            far = owners.get(chassis)
            if far is None:
                sysname = rest.split()[0] if rest else ""
                far = hostname_of.get(sysname)
            if far is None:
                notes.append("{} {}: neighbour {} {!r} is not a device on any console read"
                             .format(a.name, lp, chassis, rest))
                continue
            b = port_owner(far[0], far[1], rport)
            if b is None:
                notes.append("{} {}: neighbour port {!r} on {} maps to no member"
                             .format(a.name, lp, rport, far[1].name if far[0] == "dev" else "stack"))
                continue
            if a is b or (a.stack and a.stack is b.stack):
                continue                                  # a stack seeing itself (ring residue)
            k = tuple(sorted([(a.name, lp), (b.name, rport)]))
            seen[k] = seen.get(k, 0) + 1
    for (an, ap), (bn, bp) in seen:
        links.append((an, ap, bn, bp, "lldp both ends" if seen[((an, ap), (bn, bp))] >= 2
                      else "lldp one end"))
    # host edges: a NIC's MAC learned on a PHYSICAL port (a LAG hit is arrival, not the edge)
    edges, hostmacs = {}, {n: mac_dotted(i["mac"]) for n, i in meta["host_nics"].items() if i["mac"]}
    for kind, obj, rec in views:
        for _, port, mac, _, _ in parse_mac_table(rec["out"].get("show mac address-table", "")):
            for nic, hm in hostmacs.items():
                if mac == hm and PHYS_PORT_RE.match(port):
                    d = port_owner(kind, obj, port)
                    if d and nic not in edges:
                        edges[nic] = (d.name, port)
                    elif d and edges[nic] != (d.name, port):
                        notes.append("{} learned on {} {} AND {} {}".format(
                            nic, edges[nic][0], edges[nic][1], d.name, port))
    return sorted(links), edges, notes


def render_setup(stacks, devs, links, edges, static, stamp):
    """The .setup sections, in the order the deployed file has always used."""
    L = []
    w = L.append
    named = sorted([d for d in devs if d.console and d.name], key=lambda d: d.name)
    pdu = static.get("pdu") or "?"
    w("### GENERATED {} by bench_probe.py from a console capture -- DO NOT HAND-EDIT.".format(stamp))
    w("### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with")
    w("### `bench_probe.py run` on tb470; `bench_probe.py apply` writes this file).")
    w("### Names and PDU outlets come from bench-setup/tb470.static.")
    w("")
    w("[power]")
    for d in named:
        if d.outlet:
            w("pwr_{} = (pdu, {}, {})".format(d.name[-1], pdu, d.outlet))
    w("")
    w("[switch]")
    for d in named:
        w("{} = {}".format(d.name, d.console))
    w("")
    w("[baudrates]")
    for d in named:
        w("{} = {}".format(d.name, d.baud))
    w("")
    w("[stack]")
    for st in stacks:
        mem = [st.members[i] for i in sorted(st.members) if st.members[i].console]
        if mem:
            w("{} = {}".format(st.name, ", ".join(d.name for d in mem)))
    w("")
    w("[configured_stackport]")
    w("")
    w("[powerlink]")
    for d in named:
        if d.outlet:
            w("{} = pwr_{}".format(d.name, d.name[-1]))
    w("")
    w("[boot_from_flash]")
    for st in stacks:
        flags = [d.boot.get("flash") for d in st.members.values() if d.console]
        if flags and all(f is True for f in flags):
            w("{} = True".format(st.name))
        elif flags and all(f is False for f in flags):
            w("{} = False".format(st.name))
    for d in named:
        if d.boot.get("flash") is not None:
            w("{} = {}".format(d.name, d.boot["flash"]))
    w("")
    w("[portlink]")
    by_dev = {}
    for nic, (dn, port) in sorted(edges.items()):
        by_dev.setdefault(dn, []).append("{}-{}".format(nic, port))
    for dn in sorted(by_dev):
        w("tb-{} = {}".format(dn, ", ".join(by_dev[dn])))
    pairs = {}
    for a, pa, b, pb, _ in links:
        pairs.setdefault((a, b), []).append("{}-{}".format(pa, pb))
    for (a, b) in sorted(pairs):
        w("{}-{} = {}".format(a, b, ", ".join(sorted(pairs[(a, b)]))))
    return "\n".join(L) + "\n"


def generate(cap_dir, static=None, ask=False):
    meta = load_capture(cap_dir)
    static = static or load_static()
    stacks, devs, notes = build_model(meta)
    notes += assign_names(devs, static, ask)
    # stack names: stk_a = the stack holding the lowest-named member
    for i, st in enumerate(sorted(stacks, key=lambda s: min(d.name for d in s.members.values()))):
        st.name = "stk_" + LETTERS[i]
    links, edges, lnotes = derive_links(stacks, devs, meta)
    notes += lnotes
    for p, r in sorted(meta["consoles"].items()):
        if r.get("lldp") == "enabled-for-capture":
            notes.append("`lldp run` was OFF on {} ({}); it was switched on for this capture and off "
                         "again afterwards, so the saved `show running-config` for that console "
                         "carries the temporary line".format(r.get("hostname") or "?", p))
    for d in devs:
        if d.stack and not d.console:
            notes.append("{} (stack member {}, S/N {}) has no console read this run -- left out "
                         "of [switch] and [stack]".format(d.name, d.member_id, d.serial))
    builds = {d.software for d in devs if d.software}
    for st in stacks:
        mb = {d.software for d in st.members.values() if d.software}
        if len(mb) > 1:
            notes.append("!! {} members disagree on build: {} -- split hazard".format(st.name, sorted(mb)))
    unread = {p: r for p, r in meta["consoles"].items() if r.get("status") != "ok"}
    stamp = meta["utc"]

    L = []
    w = L.append
    w("# tb470 — bench state")
    w("")
    w("> **Generated {} by `bench_probe.py`** from `captures/{}/` on {}. Measured state only;".format(
        stamp, os.path.basename(os.path.normpath(cap_dir)), meta.get("host", "?")))
    w("> nothing here is hand-written. Regenerate with `./bench_probe.py run` on tb470. The")
    w("> `setup` fence at the end IS `tb470.setup`; `./bench_probe.py apply` writes it to the box.")
    w("> Names and PDU outlets come from `tb470.static`; platform mechanics live in the orient-dt")
    w("> skill; what a session did lives in its handover.")
    w("")
    w("## Devices")
    w("")
    w("| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |")
    w("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for d in sorted(devs, key=lambda d: (d.console is None, d.console or "", d.name or "")):
        w("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            d.console or "—", d.baud or "—", d.name or "?", d.model, d.serial, d.hostname or "?",
            "{} member {}".format(d.stack.name, d.member_id) if d.stack else "standalone",
            d.role or "?", d.software or "?", d.bootloader or "?", d.boot.get("image") or "?"))
    for p, r in sorted(unread.items()):
        w("| {} | — | ? | ? | ? | ? | — | {} | | | {} |".format(p, r.get("status"), "; ".join(r.get("notes") or [])))
    w("")
    for st in stacks:
        w("**{}**: {}; Stack MAC {}; members {}.".format(
            st.name, st.oper or "?", st.stack_mac or "?",
            ", ".join("{}={} ({}, prio {}, {})".format(i, st.members[i].name if i in st.members else "?",
                                                      st.rows[i]["mac"], st.rows[i]["prio"], st.rows[i]["role"])
                      for i in sorted(st.rows))))
        w("")
    w("## Links")
    w("")
    w("| A | port | B | port | proof |")
    w("| --- | --- | --- | --- | --- |")
    for nic, (dn, port) in sorted(edges.items()):
        n = meta["host_nics"].get(nic, {})
        w("| tb | {} ({}) | {} | {} | MAC learned on a physical port |".format(nic, n.get("ipv4") or "no IPv4", dn, port))
    for a, pa, b, pb, proof in links:
        w("| {} | {} | {} | {} | {} |".format(a, pa, b, pb, proof))
    for nic, n in sorted(meta["host_nics"].items()):
        if nic not in edges:
            w("| tb | {} ({}) | — | — | {} |".format(nic, n.get("ipv4") or "no IPv4",
                                                  "carrier DOWN" if not n.get("carrier_up") else "carrier up, MAC not learned"))
    w("")
    w("## Advisories")
    w("")
    if notes:
        for n in notes:
            w("- " + n)
    else:
        w("- none")
    w("")
    w("## tb470.setup")
    w("")
    w("```setup")
    w(render_setup(stacks, devs, links, edges, static, stamp).rstrip("\n"))
    w("```")
    w("")
    w("```nic-state")
    w("# NIC  carrier  learned_on")
    for nic, n in sorted(meta["host_nics"].items()):
        e = edges.get(nic)
        w("{} {} {}".format(nic, "up" if n.get("carrier_up") else "down", "{}:{}".format(*e) if e else "-"))
    w("```")
    w("")
    w("```probe-meta")
    w("capture {}".format(os.path.basename(os.path.normpath(cap_dir))))
    for p, r in sorted(unread.items()):
        w("unread {} {}".format(p, r.get("status")))
    w("```")
    w("")
    return "\n".join(L)


# =============================================================================
# 3. diff -- semantic .setup comparison
# =============================================================================

FENCE_OPEN, FENCE_CLOSE = "```setup", "```"


def extract_fence(text, tag="setup"):
    """Concatenate the ```<tag> fences of a .md; a raw .setup is returned whole."""
    open_ = "```" + tag
    if open_ not in text:
        return text if tag == "setup" else ""
    out, inside = [], False
    for ln in text.splitlines():
        if not inside:
            if ln.rstrip() == open_:
                inside = True
        elif ln.rstrip() == FENCE_CLOSE:
            inside = False
        else:
            out.append(ln)
    return "\n".join(out) + "\n"


def _norm(v):
    v = re.sub(r"\s+", " ", v).strip()
    if "," in v:
        return frozenset(p.strip() for p in v.split(",") if p.strip())
    return v


def _canon_link(key, val):
    """A pair key names two devices; orient it alphabetically and swap each value's
    port pair to match, so `swi_d-swi_b = port4.0.9-port1.0.9` equals
    `swi_b-swi_d = port1.0.9-port4.0.9`. `tb-` keys keep tb first."""
    if key.startswith("tb-") or "-" not in key:
        return key, val
    a, b = key.split("-", 1)
    if a <= b:
        return key, val
    items = [p.strip() for p in val.split(",") if p.strip()]
    sw = []
    for it in items:
        if "-" in it:
            pa, pb = it.split("-", 1)
            sw.append(pb.strip() + "-" + pa.strip())
        else:
            sw.append(it)
    return b + "-" + a, ", ".join(sw)


def parse_setup(text):
    """{section: {key: normalized value}}; ### comments, blanks, order all dropped."""
    sections, cur = {}, None
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            cur = s[1:-1].strip()
            sections.setdefault(cur, {})
            continue
        if cur is None or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k, v = k.strip(), v.strip()
        if cur == "portlink":
            k, v = _canon_link(k, v)
        sections[cur][k] = _norm(v)
    return sections


def _show(v):
    return "{" + ", ".join(sorted(v)) + "}" if isinstance(v, frozenset) else (v if v is not None else "(absent)")


def load_nic_state(text):
    state, inside = {}, False
    for ln in text.splitlines():
        s = ln.rstrip()
        if not inside:
            if s == "```nic-state":
                inside = True
            continue
        if s == "```":
            break
        parts = s.split()
        if len(parts) >= 3 and not s.startswith("#"):
            state[parts[0]] = {"carrier": parts[1] == "up", "port": None if parts[2] == "-" else parts[2]}
    return state


def load_unread(text):
    """Consoles the live capture could not read: {'/dev/u1': 'busy'}."""
    out = {}
    for ln in extract_fence(text, "probe-meta").splitlines():
        parts = ln.split()
        if len(parts) >= 3 and parts[0] == "unread":
            out[parts[1]] = parts[2]
    return out


LABELS = {
    "CHANGED": "value differs",
    "MOVED": "host NIC now cabled to a DIFFERENT switch port",
    "MISSING_IN_LIVE": "template expects it; the bench does NOT have it",
    "EXTRA_IN_LIVE": "the bench has it; the template does NOT",
    "LINK_DOWN": "host NIC has NO carrier -- check the cable / SFP / far-end port state",
    "CHECK_CABLE": "NIC has link but its MAC was not learned on any switch port -- mis-cabled or not transiting",
    "CONSOLE_BUSY": "that device's console was held by someone else -- nothing about it could be read",
    "CONSOLE_DOWN": "that device's console gave no AW+ prompt -- powered off, absent or mid-boot",
}
NEEDS_CHECK = {"LINK_DOWN", "CHECK_CABLE", "CONSOLE_BUSY", "CONSOLE_DOWN"}


def run_diff(live_path, tmpl_path):
    live_txt = io.open(live_path, encoding="utf-8").read()
    tmpl_txt = io.open(tmpl_path, encoding="utf-8").read()
    live = parse_setup(extract_fence(live_txt))
    tmpl = parse_setup(extract_fence(tmpl_txt))
    nic_state = load_nic_state(live_txt)
    unread = load_unread(live_txt)
    # a template device whose console the live run could not read
    unread_names = {}
    for name, path in tmpl.get("switch", {}).items():
        if isinstance(path, str) and path in unread:
            unread_names[name] = "CONSOLE_BUSY" if unread[path] == "busy" else "CONSOLE_DOWN"

    def mentions_unread(key, *vals):
        toks = set(re.split(r"[^\w]+", key))
        for v in vals:
            for it in (v if isinstance(v, frozenset) else [v] if v else []):
                toks |= set(re.split(r"[^\w]+", str(it)))
        for n, kind in unread_names.items():
            if n in toks:
                return kind
        return None

    mismatches, checks = [], []
    for sec in sorted(set(live) | set(tmpl)):
        lk, tk = live.get(sec, {}), tmpl.get(sec, {})
        for k in sorted(set(lk) | set(tk)):
            lv, tv = lk.get(k), tk.get(k)
            if lv == tv:
                continue
            if sec == "portlink" and k.startswith("tb-"):
                # per-NIC view so a moved cable reads as ONE change with a reason
                lset = lv if isinstance(lv, frozenset) else ({lv} if lv else set())
                tset = tv if isinstance(tv, frozenset) else ({tv} if tv else set())
                lnic = {x.split("-", 1)[0]: x for x in lset}
                tnic = {x.split("-", 1)[0]: x for x in tset}
                for nic in sorted(set(lnic) | set(tnic)):
                    if lnic.get(nic) == tnic.get(nic):
                        continue
                    if lnic.get(nic) and tnic.get(nic):
                        kind = "MOVED"
                    elif tnic.get(nic):
                        st = nic_state.get(nic)
                        kind = ("LINK_DOWN" if st and not st["carrier"] else
                                "CHECK_CABLE" if st and st["carrier"] and not st["port"] else
                                mentions_unread(k) or "MISSING_IN_LIVE")
                    else:
                        kind = "EXTRA_IN_LIVE"
                    row = ("[portlink] {} {}".format(k, nic), kind, lnic.get(nic) or "(absent)",
                           tnic.get(nic) or "(absent)")
                    (checks if kind in NEEDS_CHECK else mismatches).append(row)
                continue
            kind = ("MISSING_IN_LIVE" if lv is None else "EXTRA_IN_LIVE" if tv is None else "CHANGED")
            if lv is None or kind == "CHANGED":
                u = mentions_unread(k, lv, tv)
                if u:
                    kind = u
            row = ("[{}] {}".format(sec, k), kind, _show(lv), _show(tv))
            (checks if kind in NEEDS_CHECK else mismatches).append(row)

    print("live      {}".format(live_path))
    print("template  {}".format(tmpl_path))
    print()
    if not mismatches and not checks:
        print("MATCH -- the bench equals the template.")
        return 0

    def block(title, rows):
        print("{} ({}):\n".format(title, len(rows)))
        for label, kind, lv, tv in rows:
            print("  {}".format(label))
            print("      {:<16} {}".format(kind, LABELS[kind]))
            print("      bench    = {}".format(lv))
            print("      template = {}".format(tv))
        print()
    if mismatches:
        block("MISMATCH -- the bench is not the template", mismatches)
    if checks:
        block("NEEDS-CHECK -- unverifiable this run, human decision", checks)
    return 1 if mismatches else 2


# =============================================================================
# 4. apply -- write the fence to the box
# =============================================================================

def on_box():
    return os.uname().nodename == BOX and os.path.exists(os.path.dirname(REMOTE))


def ssh(args, stdin=None):
    env = dict(os.environ, SSH_AUTH_SOCK=SOCK)
    return subprocess.run(["ssh", BOX] + args, env=env, input=stdin,
                          stdout=subprocess.PIPE, check=True).stdout


def live_setup():
    if on_box():
        return io.open(REMOTE, encoding="utf-8").read()
    return ssh(["cat " + REMOTE]).decode("utf-8")


def write_setup(text):
    if on_box():
        io.open(REMOTE, "w", encoding="utf-8").write(text)
    else:
        ssh(["cat > " + REMOTE], stdin=text.encode("utf-8"))


def render():
    if not os.path.exists(STATE):
        sys.exit("no bench-state.md -- run `bench_probe.py run` (on tb470) or `generate` first")
    text = extract_fence(io.open(STATE, encoding="utf-8").read())
    if not text.strip():
        sys.exit("bench-state.md has no ```setup fence")
    cp = configparser.ConfigParser(strict=True, interpolation=None)   # what Setup.py uses
    cp.optionxform = str
    try:
        cp.read_string(text)
    except configparser.Error as e:
        sys.exit("rendered .setup does not load strictly: {}".format(e))
    return text


def snapshot(setup_text):
    """Archive the outgoing PAIR under one stamp: the .setup being replaced and the
    bench-state.md that produced it (Terrence's rule: the record and its reflection)."""
    os.makedirs(BACKUPS, exist_ok=True)
    stamp = utc_stamp()
    made = []
    p = os.path.join(BACKUPS, stamp + ".tb470.setup")
    io.open(p, "w", encoding="utf-8").write(setup_text)
    made.append(p)
    if os.path.exists(STATE_MIRROR):
        q = os.path.join(BACKUPS, stamp + ".bench-state.md")
        io.open(q, "w", encoding="utf-8").write(io.open(STATE_MIRROR, encoding="utf-8").read())
        made.append(q)
    return made


def apply(force=False):
    want = render()
    have = live_setup()
    cur = io.open(CURRENT, encoding="utf-8").read() if os.path.exists(CURRENT) else None
    print("render  {}  ({} bytes)".format(sha(want), len(want)))
    print("live    {}  ({} bytes)".format(sha(have), len(have)))
    if want == have:
        print("\nthe testbox already has this file -- nothing written there")
        if cur != have:
            io.open(CURRENT, "w", encoding="utf-8").write(have)
        io.open(STATE_MIRROR, "w", encoding="utf-8").write(io.open(STATE, encoding="utf-8").read())
        return 0
    if cur is not None and have != cur and not force:
        print("\nREFUSING: the live file does not match tb470.setup.current -- someone edited")
        print("{}:{} by hand. Look at it first; re-run with --force to overwrite (it is".format(BOX, REMOTE))
        print("snapshotted into backups/ regardless).")
        return 2
    for p in snapshot(have):
        print("snapshot -> {}".format(p))
    write_setup(want)
    back = live_setup()
    if back != want:
        print("VERIFY FAILED: readback does not match the render")
        return 3
    io.open(CURRENT, "w", encoding="utf-8").write(want)
    io.open(STATE_MIRROR, "w", encoding="utf-8").write(io.open(STATE, encoding="utf-8").read())
    print("written in place and verified by readback; tb470.setup.current refreshed")
    return 0


# =============================================================================

def _nums(spec):
    nums = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            nums += list(range(int(a), int(b) + 1))
        elif part:
            nums.append(int(part))
    return nums


def default_template():
    return REMOTE if on_box() and os.path.exists(REMOTE) else CURRENT


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    for name in ("run", "capture"):
        s = sub.add_parser(name)
        s.add_argument("--consoles", default="0-6", help="range/list of /dev/uN (default 0-6)")
        s.add_argument("--quiet", action="store_true")
        s.add_argument("--no-prompt", action="store_true", help="never ask about unnamed units")
        if name == "run":
            s.add_argument("--template", default=None, help="the .setup to diff against")
            s.add_argument("--out", default=STATE, help="where to write bench-state.md")
    s = sub.add_parser("generate")
    s.add_argument("capture_dir")
    s.add_argument("--out", default=STATE)
    s.add_argument("--no-prompt", action="store_true")
    s = sub.add_parser("diff", aliases=["check"])
    s.add_argument("live", nargs="?", default=STATE)
    s.add_argument("template", nargs="?", default=None)
    sub.add_parser("render")
    s = sub.add_parser("apply")
    s.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "capture":
        capture(_nums(args.consoles), quiet=args.quiet)
        return 0
    if args.cmd in ("run", "generate"):
        ask = sys.stdin.isatty() and not args.no_prompt
        cap_dir = args.capture_dir if args.cmd == "generate" else capture(_nums(args.consoles), quiet=args.quiet)
        md = generate(cap_dir, ask=ask)
        io.open(args.out, "w", encoding="utf-8").write(md)
        print("bench-state -> {}".format(args.out), file=sys.stderr)
        if args.cmd == "generate":
            return 0
        tmpl = args.template or default_template()
        if not os.path.exists(tmpl):
            print("no template at {} -- diff skipped".format(tmpl))
            return 0
        return run_diff(args.out, tmpl)
    if args.cmd in ("diff", "check"):
        tmpl = args.template or default_template()
        return run_diff(args.live, tmpl)
    if args.cmd == "render":
        sys.stdout.write(render())
        return 0
    if args.cmd == "apply":
        return apply(force=args.force)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
