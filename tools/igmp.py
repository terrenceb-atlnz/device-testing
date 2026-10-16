#!/usr/bin/env python3
"""igmp.py <iface> <join|leave> <group> <src_ip> <src_mac> [count] [interval_s] [options]

Send IGMP Membership Reports (join) or Leaves from a FAKE receiver host on
<iface>, with scapy (run with sudo).  IP.src is a real on-subnet address (an AW+
DUT's IGMP source-address check drops 0.0.0.0, seen on IE520); igmpize() adds the
router-alert option, TTL 1 and the checksum.  count defaults to 2, interval_s to
0.5.  The receiver is a fake MAC so the host's own IP stack (which may forward IP
between its NICs) never answers as, or for, the receiver.

  -2 / --v2   IGMPv2 (the default): a (*,G) ANY-SOURCE join.
  -3 / --v3   IGMPv3: the version that can carry a SOURCE LIST, and therefore the
              only one that can express an (S,G) join.  PIM-SSM is DEFINED by that
              join, so an SSM case cannot be graded without it.

IGMPv3 options:
  --source A[,B...]   the source list of the group record
  --record TYPE       is-include | is-exclude | to-include | to-exclude |
                      allow | block   (default: to-include on join -- what a real
                      host sends when it joins an SSM channel -- and to-include
                      with an EMPTY source list on leave, which is how IGMPv3
                      leaves an include-mode group)

An IGMPv3 report goes to 224.0.0.22 (all IGMPv3-capable routers), not to the
group, and carries one group record per --group.  An IGMPv2 report goes to the
group itself and an IGMPv2 leave to 224.0.0.2.

Examples
  sudo igmp.py eth4 join  239.1.1.1 10.38.22.70 00:11:22:33:44:77
  sudo igmp.py eth4 join  232.5.5.5 10.38.22.70 00:11:22:33:44:77 -3 --source 10.38.22.40
  sudo igmp.py eth4 leave 232.5.5.5 10.38.22.70 00:11:22:33:44:77 -3
"""
import argparse, sys, time

RECORDS = {"is-include": 1, "is-exclude": 2, "to-include": 3,
           "to-exclude": 4, "allow": 5, "block": 6}


def mcast_mac(addr):
    """The IANA link-layer address for an IPv4 multicast group (RFC 1112 s.6.4)."""
    o = [int(x) for x in addr.split(".")]
    return "01:00:5e:%02x:%02x:%02x" % (o[1] & 0x7f, o[2], o[3])


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("iface")
    ap.add_argument("what", choices=["join", "leave"])
    ap.add_argument("group")
    ap.add_argument("src_ip")
    ap.add_argument("src_mac")
    ap.add_argument("count", nargs="?", type=int, default=2)
    ap.add_argument("interval_s", nargs="?", type=float, default=0.5)
    v = ap.add_mutually_exclusive_group()
    v.add_argument("-2", "--v2", dest="ver", action="store_const", const=2)
    v.add_argument("-3", "--v3", dest="ver", action="store_const", const=3)
    ap.set_defaults(ver=2)
    ap.add_argument("--source", default="",
                    help="IGMPv3 only: comma list of sources for the group record")
    ap.add_argument("--record", default="", choices=[""] + sorted(RECORDS),
                    help="IGMPv3 group record type (default: to-include)")
    args = ap.parse_args()

    from scapy.all import Ether, IP, sendp
    sources = [s for s in args.source.split(",") if s]

    if args.ver == 2:
        if sources:
            sys.exit("igmp.py: --source needs -3 (IGMPv2 cannot carry a source list)")
        from scapy.contrib.igmp import IGMP
        if args.what == "join":
            dst, typ = args.group, 0x16
        else:
            dst, typ = "224.0.0.2", 0x17
        p = (Ether(src=args.src_mac, dst=mcast_mac(dst))
             / IP(src=args.src_ip, dst=dst) / IGMP(type=typ, gaddr=args.group))
        p[IGMP].igmpize()
        what = "IGMPv2 %s %s" % (args.what, args.group)
    else:
        from scapy.contrib.igmpv3 import IGMPv3, IGMPv3mr, IGMPv3gr
        rt = RECORDS[args.record] if args.record else 3     # to-include
        if args.what == "leave" and not args.record:
            sources = []            # to-include with no sources == leave the channel
        dst = "224.0.0.22"
        rec = IGMPv3gr(rtype=rt, maddr=args.group, srcaddrs=sources)
        p = (Ether(src=args.src_mac, dst=mcast_mac(dst))
             / IP(src=args.src_ip, dst=dst)
             / IGMPv3(type=0x22) / IGMPv3mr(records=[rec]))
        p[IGMPv3].igmpize()
        name = args.record or "to-include"
        what = "IGMPv3 %s %s rtype=%s(%d) sources=[%s]" % (
            args.what, args.group, name, rt, ",".join(sources) or "-")

    for i in range(args.count):
        sendp(p, iface=args.iface, verbose=False)
        if i + 1 < args.count:
            time.sleep(args.interval_s)
    print("%s %s x%d from %s/%s on %s -> %s"
          % (time.strftime("%T"), what, args.count, args.src_ip, args.src_mac,
             args.iface, dst))


if __name__ == "__main__":
    main()
