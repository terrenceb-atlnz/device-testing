#!/usr/bin/env python3
"""bench_topology.py -- turn a bench_probe.py sweep into a live physical-topology
.md, and semantically diff a live topology against an immutable .setup template.

    bench_topology.py generate <probe.json>      # live .md (with ```setup fences) -> stdout
    bench_topology.py diff <live> <template>      # semantic .setup-vs-.setup diff

Both <live> and <template> may be a .md (its ```setup fences are extracted and
concatenated) or a raw .setup file. The diff IGNORES ### comments, blank lines,
section/line ordering, and comma-list ordering -- it compares the DECLARED PHYSICAL
topology, not formatting. Exit 0 = match, 1 = differences, 2 = usage/parse error.

Physical facts SENSED by the probe and written into the .md:
  console<->serial, stack membership + member IDs, per-member build/.rel,
  host NIC <-> member switch port.
Facts DECLARED (not sensed) come from the static scaffold below -- PDU outlet per
unit, port caps, ck_profile, baud. Because both live and template carry the same
declared values, they never show as a diff; only sensed reality can.

NOTE (2026-09-15): the id->serial and boot parsing are written defensively and must
be validated against a real sweep -- see `_members_from_probe`.
"""
import json
import re
import sys
import time

# ---- static scaffold: declared, not sensed ---------------------------------
PDU_IP = "10.36.150.14"
OUTLET_BY_SERIAL = {           # PDU outlet per physical unit (by serial); PDU is static
    "264A23061": 6,            # /dev/u2  member 1  (F)
    "264A23068": 8,            # /dev/u3  member 2  (H)
    "264A23066": 5,            # /dev/u5  member 3  (E)
    "264A23052": 4,            # /dev/u4  member 4  (D)
}
CAP = "polarity"               # every IE520 supports it (verified at the console)
PROFILE = ""                   # ck_profile deliberately empty
DEFAULT_BAUD = 115200
STALE_HOURS = 48               # .rel age boundary for the advisory warning

# ---- parsing ---------------------------------------------------------------
SERIAL_RE = re.compile(r"\b(\d{2,3}[A-Z]\d{4,6})\b")
# a `show stack` member row: ID  PendingID  MAC  Priority  Status  Role
STACK_ROW_RE = re.compile(
    r"^\s*(\d+)\s+\S+\s+([0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})\s+(\d+)\s+\S+\s+"
    r"(Active Master|Backup Member|Standalone unit)\s*$", re.I)
BANNER_ID_RE = re.compile(r"-(\d+)$")
BUILD_DATE_RE = re.compile(r"(\d{8})-(\d{4})")       # awplus_main-20260913-1734
PHYS_PORT_RE = re.compile(r"\b(port\d+\.\d+\.\d+)\b")
SWI_LETTERS = "abcdefghijklmnop"


def _stacks_from_probe(probe):
    """Return a LIST of stacks (one per formed VCStack), each
    {id: {mac, priority, role, serial, console, banner}}.

    A split bench yields >1 stack. Each console's OWN `show stack` names the stack it
    belongs to; `Provisioned` rows (no MAC -- absent members after a split) are excluded
    by STACK_ROW_RE, which requires a MAC. Consoles are grouped by the frozenset of their
    stack's real member MACs, so the two masters of a split (both bannered bare `awplus`)
    no longer collide. id->serial is zipped PER STACK (each split half's `show system
    serialnumber` lists only its own members, in ascending ID order).
    """
    consoles = probe.get("consoles", {})
    per_console = {}
    for cpath, rec in consoles.items():
        if rec.get("status") != "ok":
            continue
        stk = (rec.get("commands") or {}).get("show stack", "") or ""
        if "disabled" in stk.lower():
            continue                                   # x230 standalone, not an IE520 stack
        rows = {}
        master = None
        for ln in stk.splitlines():
            m = STACK_ROW_RE.match(ln)
            if not m:
                continue
            mid, role = int(m.group(1)), m.group(4)
            rows[mid] = {"mac": m.group(2), "priority": int(m.group(3)), "role": role}
            if role.lower() == "active master":
                master = mid
        if rows:
            per_console[cpath] = {"members": rows, "master": master,
                                  "key": frozenset(v["mac"] for v in rows.values()),
                                  "rec": rec, "banner": rec.get("banner_hostname") or ""}

    groups = {}
    for cpath, info in per_console.items():
        groups.setdefault(info["key"], []).append(cpath)

    stacks = []
    for cpaths in groups.values():
        base = per_console[cpaths[0]]
        members = {mid: dict(row, serial=None, console=None, banner=None)
                   for mid, row in base["members"].items()}
        for cpath in cpaths:
            info = per_console[cpath]
            bm = BANNER_ID_RE.search(info["banner"])
            mid = info["master"] if info["banner"] == "awplus" else (
                int(bm.group(1)) if bm else None)
            if mid in members:
                members[mid]["console"] = info["rec"].get("path") or ("/dev/" + cpath)
                members[mid]["banner"] = info["banner"]
        serials = _serials_in_member_order({c: per_console[c]["rec"] for c in cpaths})
        for mid, ser in zip(sorted(members), serials):
            members[mid]["serial"] = ser
        stacks.append(members)

    stacks.sort(key=lambda mm: min(mm) if mm else 0)   # stk_a = lowest-id stack, stable
    return stacks


def _serials_in_member_order(consoles):
    """AW+ `show system serialnumber` on a VCStack lists members in ascending ID
    order; return that ordered serial list from any stack console."""
    for rec in consoles.values():
        if rec.get("status") != "ok":
            continue
        cmds = rec.get("commands") or {}
        txt = (cmds.get("show system serialnumber", "") or "")
        # keep only lines that look like a member/serial line, in file order
        serials = []
        for ln in txt.splitlines():
            m = SERIAL_RE.search(ln)
            if m:
                serials.append(m.group(1))
        # dedupe preserving order
        seen, out = set(), []
        for s in serials:
            if s not in seen:
                seen.add(s)
                out.append(s)
        if len(out) >= 2:
            return out
    return []


def _member_build(probe, mid, banner):
    """Running build + flash .rel for a member, for the staleness advisory."""
    consoles = probe.get("consoles", {})
    # per-member flash lives on the master's relayed view, keyed by str(id)
    rel = None
    for rec in consoles.values():
        pmf = rec.get("per_member_flash") or {}
        blob = pmf.get(str(mid))
        if blob:
            r = re.search(r"(\S+\.rel)", blob)
            if r:
                rel = r.group(1)
                break
    # build string from any stack console's show system (all members equal normally)
    build = None
    for rec in consoles.values():
        if rec.get("status") != "ok":
            continue
        sysout = (rec.get("commands") or {}).get("show system", "") or ""
        b = re.search(r"Software version\s*[:.]\s*(\S+)", sysout)
        if b:
            build = b.group(1)
            break
    return build, rel


def _rel_age_hours(name):
    """Hours since the build timestamp embedded in a dated .rel/build name."""
    if not name:
        return None
    m = BUILD_DATE_RE.search(name)
    if not m:
        return None
    try:
        t = time.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M")
    except ValueError:
        return None
    return (time.time() - time.mktime(t)) / 3600.0


# ---- generate --------------------------------------------------------------
def generate(probe):
    stacks = _stacks_from_probe(probe)
    if not stacks:
        sys.exit("generate: no formed IE520 stack found in the probe -- cannot build topology")

    # flatten to a global member map; swi_* is assigned by GLOBAL member ID so the
    # mapping is stable whether the bench is one stack or several (a split keeps each
    # member's ID). stk_a, stk_b, ... name the stacks in lowest-member-id order.
    members, mem_stack = {}, {}
    for si, st in enumerate(stacks):
        for mid, info in st.items():
            members[mid], mem_stack[mid] = info, si
    ids = sorted(members)
    swi = {mid: "swi_" + SWI_LETTERS[i] for i, mid in enumerate(ids)}
    stack_names = ["stk_" + SWI_LETTERS[si] for si in range(len(stacks))]
    host = probe.get("host_edges", {})

    # host portlinks: NIC -> (member, physical port); only physical (portN.0.x) edges
    portlinks, unknown_nics = [], []
    for nic, e in sorted(host.items()):
        ports, mems = e.get("physical_ports") or [], e.get("members") or []
        if ports and mems and mems[0] in swi:
            portlinks.append((swi[mems[0]], nic, ports[0]))
        elif not e.get("carrier_up"):
            unknown_nics.append(nic)

    # advisories (NOT topology diffs): stack count, .rel age, intra-bench build disagreement
    notes = []
    if len(stacks) > 1:
        notes.append("%d separate stacks present (split bench): %s"
                     % (len(stacks), "; ".join(
                         "%s={%s}" % (stack_names[si], ",".join(str(m) for m in sorted(st)))
                         for si, st in enumerate(stacks))))
    builds = {}
    for mid in ids:
        build, rel = _member_build(probe, mid, members[mid]["banner"])
        builds[mid] = build
        age = _rel_age_hours(build or rel)
        if age is not None and age >= STALE_HOURS:
            notes.append("member %d build %s is %.0fh old (>= %dh) -- consider re-flashing latest"
                         % (mid, build or rel, age, STALE_HOURS))
    distinct = {b for b in builds.values() if b}
    if len(distinct) > 1:
        notes.append("!! members disagree on build: %s -- split hazard" % sorted(distinct))

    L = []
    w = L.append
    w("# tb470 -- live physical topology (generated by bench_topology.py)")
    w("")
    w("> Generated %s from a bench_probe.py sweep. Physical state only; the test suite"
      % probe.get("probe_meta", {}).get("utc", "?"))
    w("> supplies device configs. Diff this against an immutable `.setup` template.")
    w("")
    if notes:
        w("**Advisories (not topology diffs):**")
        for n in notes:
            w("- " + n)
        w("")
    if unknown_nics:
        w("**Unverifiable (carrier down, edge not learned):** " + ", ".join(unknown_nics))
        w("")

    # human-readable member table
    w("## Members")
    w("")
    w("| swi | stack | member ID | serial | console | role | prio | outlet |")
    w("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for mid in ids:
        m = members[mid]
        outlet = OUTLET_BY_SERIAL.get(m["serial"] or "", "?")
        w("| %s | %s | %d | %s | %s | %s | %d | %s |" % (
            swi[mid], stack_names[mem_stack[mid]], mid, m["serial"] or "?",
            m["console"] or "?", m["role"], m["priority"], outlet))
    w("")

    # ---- the deployable / comparable fences ----
    def fence(lines):
        w("```setup")
        for ln in lines:
            w(ln)
        w("```")
        w("")

    w("## §switch")
    w("")
    fence(["[switch]"] + ["%s = %s" % (swi[mid], members[mid]["console"] or "?") for mid in ids]
          + [""] + ["[baudrates]"] + ["%s = %d" % (swi[mid], DEFAULT_BAUD) for mid in ids])

    w("## §power")
    w("")
    pw = ["[power]"]
    for i, mid in enumerate(ids):
        outlet = OUTLET_BY_SERIAL.get(members[mid]["serial"] or "", "?")
        pw.append("pwr_%s = (pdu, %s, %s)" % (SWI_LETTERS[i], PDU_IP, outlet))
    pw += [""] + ["[powerlink]"] + ["%s = pwr_%s" % (swi[mid], SWI_LETTERS[i])
                                    for i, mid in enumerate(ids)]
    fence(pw)

    w("## §stack")
    w("")
    stk_lines = ["[stack]"]
    for si, st in enumerate(stacks):
        stk_lines.append("%s = %s" % (stack_names[si], ", ".join(swi[mid] for mid in sorted(st))))
    stk_lines += ["", "[configured_stackport]"]
    fence(stk_lines)

    w("## §boot")
    w("")
    fence(["[boot_from_flash]"] + ["%s = True" % sn for sn in stack_names]
          + ["%s = True" % swi[mid] for mid in ids])

    w("## §portlink")
    w("")
    pl = ["[portlink]"]
    for swname, nic, port in sorted(portlinks):
        pl.append("tb-%s = %s-%s" % (swname, nic, port))
    fence(pl)

    # host NIC physical state -- NOT a ```setup fence, so it never reaches the deployed
    # .setup; the diff reads it to explain WHY an expected edge is absent (LINK_DOWN /
    # CHECK_CABLE) instead of a bare "missing".
    w("## §nic-state (host NIC physical state -- read by the diff, NOT deployed)")
    w("")
    w("```nic-state")
    w("# NIC  carrier  learned_port  member")
    for nic, e in sorted(host.items()):
        ports, mems = e.get("physical_ports") or [], e.get("members") or []
        w("%s %s %s %s" % (nic, "up" if e.get("carrier_up") else "down",
                           ports[0] if ports else "-", mems[0] if mems else "-"))
    w("```")
    w("")

    w("## §misc")
    w("")
    mc = ["[misc]", "ck_profile     = " + PROFILE, "ck_role_dut    = " + stack_names[0]]
    for mid in ids:
        mc.append("ck_cap_%s   = %s" % (swi[mid], CAP))
    fence(mc)

    return "\n".join(L) + "\n"


# ---- diff ------------------------------------------------------------------
FENCE_OPEN, FENCE_CLOSE = "```setup", "```"


def extract_setup(text):
    """If the text has ```setup fences, concatenate them; else return it whole."""
    if FENCE_OPEN not in text:
        return text
    out, inside = [], False
    for ln in text.splitlines():
        if not inside:
            if ln.rstrip() == FENCE_OPEN:
                inside = True
        elif ln.rstrip() == FENCE_CLOSE:
            inside = False
        else:
            out.append(ln)
    return "\n".join(out)


def parse_setup(text):
    """{section: {key: normalized_value}}; ### comments, blanks, order all dropped."""
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
        sections[cur][k.strip()] = _norm(v.strip())
    return sections


def _norm(v):
    """Collapse whitespace; a comma-list becomes an order-independent frozenset."""
    v = re.sub(r"\s+", " ", v).strip()
    if "," in v:
        return frozenset(p.strip() for p in v.split(",") if p.strip())
    return v


def _show(v):
    return "{" + ", ".join(sorted(v)) + "}" if isinstance(v, frozenset) else v


def load_nic_state(text):
    """Parse a ```nic-state block (present only in a generated live .md):
    {nic: {"carrier": bool, "port": str|None}}. Empty if absent (e.g. a template)."""
    state, inside = {}, False
    for ln in text.splitlines():
        s = ln.rstrip()
        if not inside:
            if s == "```nic-state":
                inside = True
            continue
        if s == "```":
            break
        parts = s.strip().split()
        if len(parts) >= 3 and not s.strip().startswith("#"):
            state[parts[0]] = {"carrier": parts[1].lower() == "up",
                               "port": None if parts[2] == "-" else parts[2]}
    return state


def portlinks_by_nic(section):
    """[portlink] {tb-swi_X: ethN-portZ} -> {ethN: (swi_X, portZ)}, keyed by the host
    NIC so a NIC moving between switch ports reads as ONE change, not missing+extra."""
    out = {}
    for key, val in section.items():
        if key.startswith("tb-") and isinstance(val, str) and "-" in val:
            nic, port = val.split("-", 1)
            out[nic] = (key[3:], port)
    return out


def diff_setups(live, tmpl, ignore=()):
    """Generic per-section diff. kind in EXTRA_IN_LIVE / MISSING_IN_LIVE / CHANGED."""
    out = []
    for sec in sorted(set(live) | set(tmpl)):
        if sec in ignore:
            continue
        lk, tk = live.get(sec, {}), tmpl.get(sec, {})
        for k in sorted(set(lk) | set(tk)):
            lv, tv = lk.get(k), tk.get(k)
            if lv == tv:
                continue
            kind = ("MISSING_IN_LIVE" if lv is None else
                    "EXTRA_IN_LIVE" if tv is None else "CHANGED")
            out.append((sec, k, kind, lv, tv))
    return out


def diff_portlinks(live_pl, tmpl_pl, nic_state):
    """Per-NIC portlink diff. Uses the live NIC carrier state to explain an absent edge:
    LINK_DOWN (no carrier) / CHECK_CABLE (link up, MAC not learned) rather than 'missing'.
    Returns (nic, kind, live_detail, tmpl_detail)."""
    rows = []
    for nic in sorted(set(live_pl) | set(tmpl_pl)):
        lv, tv = live_pl.get(nic), tmpl_pl.get(nic)
        if lv == tv:
            continue
        if lv and tv:
            kind = "MOVED"
        elif tv and not lv:                        # template expects it, live lacks it
            st = nic_state.get(nic)
            if st and not st["carrier"]:
                kind = "LINK_DOWN"
            elif st and st["carrier"] and not st["port"]:
                kind = "CHECK_CABLE"
            else:
                kind = "MISSING_IN_LIVE"
        else:                                      # live has it, template does not
            kind = "EXTRA_IN_LIVE"
        rows.append((nic, kind, lv, tv))
    return rows


LABELS = {
    "CHANGED":         "value differs",
    "MOVED":           "host NIC now cabled to a DIFFERENT switch port",
    "MISSING_IN_LIVE": "template expects it; live does NOT have it (unit/member absent?)",
    "EXTRA_IN_LIVE":   "live has it; template does NOT (unexpected cable/unit?)",
    "LINK_DOWN":       "host NIC has NO carrier -- check the cable / SFP / far-end power",
    "CHECK_CABLE":     "NIC has link but its MAC was not learned on any switch port -- "
                       "likely mis-cabled or not transiting",
}
NEEDS_CHECK = {"LINK_DOWN", "CHECK_CABLE"}          # unverifiable, not a hard mismatch


def _pl(detail):
    return "%s %s" % detail if detail else "(absent)"


def run_diff(live_path, tmpl_path):
    live_txt = open(live_path, encoding="utf-8").read()
    tmpl_txt = open(tmpl_path, encoding="utf-8").read()
    live = parse_setup(extract_setup(live_txt))
    tmpl = parse_setup(extract_setup(tmpl_txt))
    nic_state = load_nic_state(live_txt)           # only the live .md carries it

    generic = diff_setups(live, tmpl, ignore={"portlink"})
    plink = diff_portlinks(portlinks_by_nic(live.get("portlink", {})),
                           portlinks_by_nic(tmpl.get("portlink", {})), nic_state)

    mismatches = [("[%s] %s" % (s, k), kind, _show(lv) if lv is not None else "(absent)",
                   _show(tv) if tv is not None else "(absent)")
                  for s, k, kind, lv, tv in generic]
    checks = []
    for nic, kind, lv, tv in plink:
        row = ("[portlink] %s" % nic, kind, _pl(lv), _pl(tv))
        (checks if kind in NEEDS_CHECK else mismatches).append(row)

    print("live      %s" % live_path)
    print("template  %s" % tmpl_path)
    print()
    if not mismatches and not checks:
        print("MATCH -- live physical topology equals the template.")
        return 0

    def block(title, rows):
        print("%s (%d):\n" % (title, len(rows)))
        for label, kind, lv, tv in rows:
            print("  %s" % label)
            print("      %-16s %s" % (kind, LABELS[kind]))
            print("      live     = %s" % lv)
            print("      template = %s" % tv)
        print()

    if mismatches:
        block("MISMATCH -- do NOT deploy", mismatches)
    if checks:
        block("NEEDS-CHECK -- unverifiable, human decision", checks)
    return 1 if mismatches else 2


def main(argv):
    if len(argv) >= 2 and argv[0] == "generate":
        probe = json.load(open(argv[1], encoding="utf-8"))
        sys.stdout.write(generate(probe))
        return 0
    if len(argv) >= 3 and argv[0] == "diff":
        return run_diff(argv[1], argv[2])
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
