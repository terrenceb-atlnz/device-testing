#!/usr/bin/env python3
"""Decode and COUNT the syslog messages in a `tcpdump -w` pcap -- IPv4 and IPv6.

Why it exists
-------------
A syslog case is graded on the **PRI byte that actually arrived**, never on the device's own
`show log config`. PRI is a single number carrying two fields:

    PRI = facility * 8 + severity

so "the facility override worked" is a statement about one number on the wire, and nothing a
`show` command prints can settle it (STANDING-ORDERS §7; platforms/x960.md §5 is the same
lesson from mirroring). On a bench with no UDP/514 listener -- which is the normal case, since
starting one is a root change on the testbox -- a bounded `tcpdump -w ... udp port 514` plus
this decoder IS the collector.

It also answers the negative half of such a case: a destination that was configured and is
unreachable, or one whose configuration was removed, must draw ZERO syslog packets in the same
window. `--to` counts one destination at a time, and an empty result exits 2 so a control leg
reads as a measurement rather than as an error.

What it prints
--------------
one line per message (time, family, addresses, PRI with its facility and severity decoded,
and the RFC3164/RFC5424 header and text), then a summary: totals by facility, by severity, by
facility.severity pair and by address pair. `--expect-facility` / `--expect-severity` turn the
summary into a pass/fail statement about every decoded message.
"""

import argparse
import re
import struct
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from snmpwire import packets                             # noqa: E402  (classic pcap reader)
from ntpwire import udp                               # noqa: E402  (IPv4/IPv6 + 802.1Q + UDP walk)

# RFC 3164 / RFC 5424 facility numbers. AW+ `log facility ?` offers the twenty named here
# with a name; 12-15 exist in the RFC but AW+ does not offer them, so seeing one of those on
# the wire from an AW+ device would itself be a finding.
FACILITY = {
    0: "kern", 1: "user", 2: "mail", 3: "daemon", 4: "auth", 5: "syslog", 6: "lpr",
    7: "news", 8: "uucp", 9: "cron", 10: "authpriv", 11: "ftp",
    12: "ntp", 13: "audit", 14: "console", 15: "cron2",
    16: "local0", 17: "local1", 18: "local2", 19: "local3",
    20: "local4", 21: "local5", 22: "local6", 23: "local7",
}
AWPLUS_FACILITIES = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20, 21, 22, 23}

# severity: the RFC short name, then the word AlliedWare Plus uses for the same level
SEVERITY = {
    0: ("emerg", "emergencies"), 1: ("alert", "alerts"), 2: ("crit", "critical"),
    3: ("err", "errors"), 4: ("warning", "warnings"), 5: ("notice", "notices"),
    6: ("info", "informational"), 7: ("debug", "debugging"),
}

PRI_RE = re.compile(rb"^<(\d{1,3})>")
# RFC3164: "MMM [D]D HH:MM:SS host tag: msg".  RFC5424: "1 2026-10-21T23:54:25Z host app ..."
R3164_RE = re.compile(
    r"^([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*)$", re.S)
R5424_RE = re.compile(r"^(\d)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(.*)$", re.S)


def stamp(t, absolute):
    if absolute:
        return time.strftime("%H:%M:%S", time.localtime(t)) + ("%.6f" % (t % 1))[1:]
    return "%+10.3fs" % t


def decode(pay):
    """Decode one UDP payload as a syslog message. Returns None if it carries no PRI."""
    m = PRI_RE.match(pay)
    if not m:
        return None
    pri = int(m.group(1))
    if pri > 191:                       # facility 23 severity 7 is the largest legal PRI
        return None
    rest = pay[m.end():].decode("utf-8", "replace").rstrip("\r\n\0")
    out = {"pri": pri, "facility": pri // 8, "severity": pri % 8, "rest": rest,
           "format": "raw", "ts": "", "host": "", "tag": "", "msg": rest}
    m5 = R5424_RE.match(rest)
    m3 = R3164_RE.match(rest)
    if m5 and m5.group(1) == "1":
        out.update({"format": "5424", "ts": m5.group(2), "host": m5.group(3),
                    "tag": m5.group(4), "msg": m5.group(7)})
    elif m3:
        tail = m3.group(3)
        tag, _, text = tail.partition(": ")
        if len(tag) > 48 or " " in tag.strip() and not tag.endswith("]"):
            tag, text = "", tail
        out.update({"format": "3164", "ts": m3.group(1), "host": m3.group(2),
                    "tag": tag, "msg": text or tail})
    return out


def fname(n):
    return FACILITY.get(n, "fac%d" % n)


def sname(n):
    return SEVERITY.get(n, ("sev%d" % n, "sev%d" % n))[0]


def resolve(word, table, awplus_alias=None):
    """Turn a facility/severity name or number given on the command line into its number."""
    if word is None:
        return None
    if word.isdigit():
        return int(word)
    for num, val in table.items():
        names = (val,) if isinstance(val, str) else val
        if word in names:
            return num
    if awplus_alias:
        for num, val in table.items():
            if isinstance(val, tuple) and word.startswith(val[0]):
                return num
    raise SystemExit("syslogwire: unknown name %r" % word)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pcap")
    ap.add_argument("--port", type=int, action="append", default=[],
                    help="UDP port(s) to treat as syslog; any --port REPLACES the default [514]")
    ap.add_argument("--from", dest="src", action="append", default=[],
                    help="only messages with this source address (repeatable)")
    ap.add_argument("--to", dest="dst", action="append", default=[],
                    help="only messages with this destination address (repeatable)")
    ap.add_argument("--grep", default=None,
                    help="only messages whose decoded text matches this regular expression")
    ap.add_argument("--limit", type=int, default=0, help="print at most N message lines")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    ap.add_argument("--abs", action="store_true",
                    help="absolute local time per message instead of the offset from the first")
    ap.add_argument("--msg-width", type=int, default=90, help="truncate the message text (0 = full)")
    ap.add_argument("--expect-facility", default=None,
                    help="name or number every decoded message must carry (sets exit 4 if not)")
    ap.add_argument("--expect-severity", default=None,
                    help="name or number every decoded message must carry (sets exit 4 if not)")
    args = ap.parse_args()

    want_f = resolve(args.expect_facility, FACILITY)
    want_s = resolve(args.expect_severity, SEVERITY, awplus_alias=True)
    ports = set(args.port) if args.port else {514}
    grep = re.compile(args.grep) if args.grep else None

    try:
        stream = packets(args.pcap)
    except (OSError, ValueError) as e:
        print("syslogwire: %s" % e)
        return 3

    rows, total, t0, shown = [], 0, None, 0
    for when, data in stream:
        total += 1
        u = udp(data, ports)
        if not u:
            continue
        src, sp, dst, dp, pay, fam = u
        if args.src and src not in args.src:
            continue
        if args.dst and dst not in args.dst:
            continue
        d = decode(pay)
        if d is None:
            continue
        if grep and not grep.search(d["rest"]):
            continue
        if t0 is None:
            t0 = when
        d.update({"when": when, "src": src, "sport": sp, "dst": dst, "dport": dp, "family": fam})
        rows.append(d)
        if not args.quiet and (args.limit == 0 or shown < args.limit):
            shown += 1
            text = d["msg"] if args.msg_width <= 0 else d["msg"][:args.msg_width]
            print("%s v%s %s:%d -> %s:%d  PRI=%-3d %s.%s (fac %d, sev %d)  %s%s"
                  % (stamp(when if args.abs else when - t0, args.abs), d["family"],
                     src, sp, dst, dp, d["pri"], fname(d["facility"]), sname(d["severity"]),
                     d["facility"], d["severity"],
                     (d["tag"] + " ") if d["tag"] else "", text))

    print("")
    print("syslogwire: %s -- %d frames in the capture, %d syslog message(s) on port(s) %s"
          % (args.pcap, total, len(rows), ",".join(str(p) for p in sorted(ports))))
    if not rows:
        print("  NO SYSLOG MESSAGES. For a control leg that is the measurement, not an error.")
        return 2

    by_f, by_s, by_fs, by_pair, by_fam = {}, {}, {}, {}, {}
    for d in rows:
        by_f[d["facility"]] = by_f.get(d["facility"], 0) + 1
        by_s[d["severity"]] = by_s.get(d["severity"], 0) + 1
        k = (d["facility"], d["severity"])
        by_fs[k] = by_fs.get(k, 0) + 1
        p = "%s -> %s" % (d["src"], d["dst"])
        by_pair[p] = by_pair.get(p, 0) + 1
        by_fam[d["family"]] = by_fam.get(d["family"], 0) + 1
    print("  by family:   " + "  ".join("IPv%s=%d" % (f, n) for f, n in sorted(by_fam.items())))
    print("  by facility: " + "  ".join("%s(%d)=%d" % (fname(f), f, n)
                                        for f, n in sorted(by_f.items())))
    print("  by severity: " + "  ".join("%s(%d)=%d" % (sname(s), s, n)
                                        for s, n in sorted(by_s.items())))
    print("  by PRI:      " + "  ".join("%d=%s.%s x%d" % (f * 8 + s, fname(f), sname(s), n)
                                        for (f, s), n in sorted(by_fs.items())))
    for k in sorted(by_pair):
        print("  %-60s %d" % (k, by_pair[k]))

    odd = sorted(f for f in by_f if f not in AWPLUS_FACILITIES)
    if odd:
        print("  note: facility %s is in the RFC but is NOT offered by AW+ `log facility ?`"
              % ",".join("%d(%s)" % (f, fname(f)) for f in odd))

    rc = 0
    if want_f is not None:
        bad = len(rows) - by_f.get(want_f, 0)
        print("  EXPECT facility %s(%d): %d of %d message(s) match%s"
              % (fname(want_f), want_f, by_f.get(want_f, 0), len(rows),
                 "" if not bad else "  !! %d DO NOT" % bad))
        rc = rc or (4 if bad else 0)
    if want_s is not None:
        bad = len(rows) - by_s.get(want_s, 0)
        print("  EXPECT severity %s(%d): %d of %d message(s) match%s"
              % (sname(want_s), want_s, by_s.get(want_s, 0), len(rows),
                 "" if not bad else "  !! %d DO NOT" % bad))
        rc = rc or (4 if bad else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main())
