#!/usr/bin/env python3
"""Decode and COUNT the RADIUS packets in a libpcap file -- the wire half of a RADIUS case.

RADIUS is UDP, so "the login worked" is not a measurement (STANDING-ORDERS s7).  What
can be measured is the exchange itself: how many Access-Requests left the NAS, how many
Access-Accepts or Access-Rejects came back, from and to which address, carrying which
attributes -- and, when the shared secret is given, whether each reply's Response
Authenticator actually verifies against it.  A reply that verifies proves the responder
holds the secret; one that does not is a finding.

No dependencies: it reuses `snmpwire.py`'s pcap and Ethernet/IPv4/UDP walk (classic
pcap, both byte orders, 802.1Q/QinQ aware) and `radius.py`'s codec.

Usage:
  radwire.py <file.pcap> [--port N ...] [--secret S] [--limit N] [--quiet]

  --port N    UDP port(s) that carry RADIUS (default 1812, 1813, 11812, 11813);
              repeatable, and any port given replaces the default list
  --secret S  verify each reply's Response Authenticator against this secret, by
              pairing it with the Access-Request of the same id and 4-tuple
  --limit N   stop after N decoded RADIUS packets
  --quiet     print only the per-code counts and the verification summary

Exit: 0 if at least one RADIUS packet was decoded, 1 if none, 2 on a file/usage error.
"""
import argparse
import sys

import radius as R
import snmpwire

DEFAULT_PORTS = (1812, 1813, 11812, 11813)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pcap")
    ap.add_argument("--port", type=int, action="append", default=[])
    ap.add_argument("--secret")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    ports = set(a.port) if a.port else set(DEFAULT_PORTS)

    counts, n = {}, 0
    pending = {}                     # (cli,srv,port,id) -> request authenticator
    verified = {"valid": 0, "invalid": 0, "unpaired": 0}
    t0 = None
    try:
        for ts, data in snmpwire.packets(a.pcap):
            u = snmpwire.udp_payload(data, ports)
            if u is None:
                continue
            src, sp, dst, dp, payload = u
            try:
                code, ident, auth, body = R.parse(payload)
                attrs = R.parse_attrs(body)
            except ValueError:
                continue
            n += 1
            if t0 is None:
                t0 = ts
            name = R.code_name(code)
            counts[name] = counts.get(name, 0) + 1

            # Pair a reply with its request so the authenticator can be checked.
            note = ""
            if code in (1, 4):
                pending[(src, dst, dp, ident)] = auth
            else:
                key = (dst, src, sp, ident)
                req = pending.get(key)
                if a.secret:
                    if req is None:
                        verified["unpaired"] += 1
                        note = "  [authenticator: no matching request in this capture]"
                    else:
                        want = R.response_authenticator(code, ident, body, req, a.secret)
                        if want == auth:
                            verified["valid"] += 1
                            note = "  [authenticator VALID for the given secret]"
                        else:
                            verified["invalid"] += 1
                            note = "  [authenticator INVALID for the given secret]"

            if not a.quiet:
                shown = ", ".join("%s=%s" % (R.attr_name(t),
                                             "<hidden,%db>" % len(v) if t == 2
                                             else R.show_value(t, v))
                                  for t, v in attrs)
                print("%8.3f  %s:%d -> %s:%d  %-20s id=%-3d len=%d  %s%s"
                      % (ts - t0, src, sp, dst, dp, name, ident, 20 + len(body),
                         shown or "(no attributes)", note))
            if a.limit and n >= a.limit:
                break
    except (OSError, ValueError) as e:
        print("radwire: %s" % e, file=sys.stderr)
        return 2

    print("radwire: %d RADIUS packet(s) in %s" % (n, a.pcap))
    for k in sorted(counts):
        print("  %-22s %d" % (k, counts[k]))
    if a.secret:
        print("  authenticator check: valid=%d invalid=%d unpaired=%d"
              % (verified["valid"], verified["invalid"], verified["unpaired"]))
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
