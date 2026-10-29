#!/usr/bin/env python3
"""hostnet.py -- the ONE root host-network change the Test Engineer approved for tb5
(campaign tb490+tb5 auth 2026-10-29T1304, D2 and the 13:3x answer "Yes, add the narrow helper").

It can do exactly these things and nothing else:
    route-add     ip route add 8.8.8.0/24 via 192.168.50.1 dev eth6
    route-del     ip route del 8.8.8.0/24 via 192.168.50.1 dev eth6
    link-up   jmN ip link set jmN up      (N = 1..5, the existing macvlans on eth6)
    link-down jmN ip link set jmN down
    show          print the 8.8.8.0/24 route and the jm1-jm5 link states (no change)

Every change prints the state before and after, so the log carries its own proof, and exits
non-zero if the after-state is not what was asked for. Nothing here takes an address, a prefix,
a gateway or an interface from the command line: widening it is a Test Engineer decision
(STANDING-ORDERS §4), not a flag.

Run: tools/tb sudotool <box> <scratch> hostnet <action> [jmN]
"""
import re
import subprocess
import sys

ROUTE = ["8.8.8.0/24", "via", "192.168.50.1", "dev", "eth6"]
LINKS = ["jm1", "jm2", "jm3", "jm4", "jm5"]


def sh(args):
    p = subprocess.run(["ip"] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True)
    return p.returncode, p.stdout.strip()


def route_present():
    _, out = sh(["route", "show", "8.8.8.0/24"])
    return any(l.startswith("8.8.8.0/24 via 192.168.50.1 dev eth6") for l in out.splitlines()), out


def link_up(name):
    _, out = sh(["-br", "link", "show", name])
    m = re.match(r"^\S+\s+(\S+)", out)
    return (m.group(1) if m else "?"), out


def show():
    present, out = route_present()
    print("route 8.8.8.0/24: %s%s" % ("PRESENT" if present else "absent", (" -- " + out) if out else ""))
    for n in LINKS:
        print("link  %-4s %s" % (n, link_up(n)[1] or "(no such link)"))
    return present


def main(argv):
    if not argv or argv[0] not in ("route-add", "route-del", "link-up", "link-down", "show"):
        print(__doc__)
        return 6
    act = argv[0]
    print("BEFORE:")
    show()
    if act == "show":
        return 0
    if act in ("route-add", "route-del"):
        rc, out = sh(["route", "add" if act == "route-add" else "del"] + ROUTE)
        print("ip route %s %s -> rc %d %s" % ("add" if act == "route-add" else "del", " ".join(ROUTE), rc, out))
        print("AFTER:")
        present = show()
        ok = present if act == "route-add" else not present
    else:
        if len(argv) != 2 or argv[1] not in LINKS:
            print("hostnet: %s needs one of %s" % (act, " ".join(LINKS)))
            return 6
        state = "up" if act == "link-up" else "down"
        rc, out = sh(["link", "set", argv[1], state])
        print("ip link set %s %s -> rc %d %s" % (argv[1], state, rc, out))
        print("AFTER:")
        show()
        now = link_up(argv[1])[0]
        ok = (now in ("UP", "UNKNOWN", "LOWERLAYERDOWN")) if state == "up" else (now == "DOWN")
    print("RESULT %s: %s" % (act, "OK" if ok else "NOT AS ASKED"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
