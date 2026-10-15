#!/usr/bin/env python3
"""Send many flows with varying 5-tuples through a router, for load-sharing tests.

Written for ECMP (one prefix, several equal-cost next hops) but it is generic: any case that
asks "does the device spread traffic, and across which egress ports?" needs many DISTINCT flows,
because a single flow can legitimately sit on one path. It pairs with per-egress-port counters
read on the devices themselves -- this tool is the stimulus and the near-side witness, not the
counter.

It builds N flows that differ in source IP, destination IP, source port and destination port
(any subset, chosen with --vary), sends M frames of each from one host NIC at layer 2 with an
explicit next-hop MAC, and -- unless --no-capture -- runs tcpdump on the sending NIC for the
duration and reports what came back, grouped by ICMP type/code and by SOURCE ADDRESS. That last
grouping is the useful part: when a destination prefix is unrouted at the far end, each router
that received a packet answers with its own address, so the replies attribute flows to next hops
without reading a single counter.

Every payload carries CKECMP-<tag> so the tool's own frames are never confused with the bench's.

Exit codes: 0 ok; 2 bad arguments; 7 the capture on the sending NIC holds fewer of our own
marked frames than we sent (an instrument fault -- the measurement is void).
"""

import argparse
import ipaddress
import os
import pwd
import re
import shutil
import signal
import subprocess
import sys
import time

MARK = "CKECMP-"


def _die(msg, code=2):
    sys.stderr.write("ecmpflows: %s\n" % msg)
    sys.exit(code)


def _chown_back(paths):
    """tcpdump runs as root; give the files back to the invoking user."""
    uid = os.environ.get("SUDO_UID")
    gid = os.environ.get("SUDO_GID")
    if uid is None:
        return
    for p in paths:
        try:
            os.chown(p, int(uid), int(gid) if gid else -1)
        except OSError:
            pass


def start_cap(iface, outdir, tag, bpf):
    path = os.path.join(outdir, "%s-%s.pcap" % (tag, iface))
    cmd = ["tcpdump", "-i", iface, "-s", "0", "-U", "-w", path, bpf]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return {"proc": proc, "path": path, "iface": iface}


def stop_cap(cap):
    if cap is None:
        return
    try:
        cap["proc"].send_signal(signal.SIGINT)
        cap["proc"].wait(timeout=10)
    except Exception:
        try:
            cap["proc"].kill()
        except Exception:
            pass
    _chown_back([cap["path"]])


def build_flows(args):
    """Return a list of (src_ip, dst_ip, sport, dport) tuples, all distinct."""
    vary = set(x.strip() for x in args.vary.split(",") if x.strip())
    bad = vary - {"src", "dst", "sport", "dport"}
    if bad:
        _die("unknown --vary field(s): %s" % ",".join(sorted(bad)))
    if not vary:
        _die("--vary must name at least one of src,dst,sport,dport")

    src0 = int(ipaddress.IPv4Address(args.src_base))
    dst0 = int(ipaddress.IPv4Address(args.dst_base))
    flows = []
    for i in range(args.flows):
        src = src0 + (i % args.src_span if "src" in vary else 0)
        dst = dst0 + (i % args.dst_span if "dst" in vary else 0)
        sport = args.sport_base + (i if "sport" in vary else 0)
        dport = args.dport_base + (i if "dport" in vary else 0)
        flows.append((str(ipaddress.IPv4Address(src)),
                      str(ipaddress.IPv4Address(dst)),
                      sport % 65536, dport % 65536))
    if len(set(flows)) != len(flows):
        _die("the chosen --vary fields do not make %d distinct flows "
             "(widen --src-span/--dst-span or vary more fields)" % args.flows)
    return flows


def classify(pkt):
    """One short line describing a captured packet, for grouping."""
    from scapy.layers.inet import IP, ICMP, UDP, TCP
    from scapy.layers.l2 import Ether

    if IP not in pkt:
        return None
    ip = pkt[IP]
    if ICMP in pkt:
        ic = pkt[ICMP]
        kind = "ICMP t%d/c%d" % (ic.type, ic.code)
    elif UDP in pkt:
        kind = "UDP"
    elif TCP in pkt:
        kind = "TCP"
    else:
        kind = "IP proto %d" % ip.proto
    eth = pkt[Ether] if Ether in pkt else None
    emac = ("[eth %s -> %s]" % (eth.src, eth.dst)) if eth else ""
    return "%-14s %-15s -> %-15s %s" % (kind, ip.src, ip.dst, emac)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True, help="leg name; names the pcap")
    ap.add_argument("--out", required=True,
                    help="output dir -- use a LOCAL /tmp path on the box, never the NFS home")
    ap.add_argument("--iface", required=True, help="host NIC the flows are sent from")
    ap.add_argument("--gw-mac", required=True,
                    help="L2 next hop: the router's SVI MAC on the sending NIC's segment")
    ap.add_argument("--src-mac", default="00:11:22:33:44:01")
    ap.add_argument("--src-base", default="192.168.10.100", help="first source IP")
    ap.add_argument("--dst-base", default="198.51.100.10", help="first destination IP")
    ap.add_argument("--src-span", type=int, default=64,
                    help="how many consecutive source IPs to cycle through")
    ap.add_argument("--dst-span", type=int, default=64,
                    help="how many consecutive destination IPs to cycle through")
    ap.add_argument("--sport-base", type=int, default=40000)
    ap.add_argument("--dport-base", type=int, default=7000)
    ap.add_argument("--vary", default="src,dst,sport,dport",
                    help="comma list of the 5-tuple fields that differ between flows")
    ap.add_argument("--flows", type=int, default=64, help="number of distinct flows")
    ap.add_argument("--per-flow", type=int, default=10, help="frames per flow")
    ap.add_argument("--proto", default="udp", choices=["udp", "tcp", "icmp"])
    ap.add_argument("--ttl", type=int, default=64)
    ap.add_argument("--size", type=int, default=0,
                    help="pad the payload to this many bytes of L3 (0 = just the mark)")
    ap.add_argument("--gap", type=float, default=0.0, help="seconds between frames")
    ap.add_argument("--settle", type=float, default=1.5, help="wait after starting the capture")
    ap.add_argument("--wait", type=float, default=3.0, help="wait after sending, before stopping")
    ap.add_argument("--filter", default="ip", help="BPF for the capture")
    ap.add_argument("--no-capture", action="store_true", help="send only, capture nothing")
    ap.add_argument("--top", type=int, default=14, help="distinct captured flows to print")
    args = ap.parse_args()

    if args.flows < 1 or args.per_flow < 1:
        _die("--flows and --per-flow must be >= 1")
    if not args.no_capture and shutil.which("tcpdump") is None:
        _die("tcpdump not found; pass --no-capture or install it")
    os.makedirs(args.out, exist_ok=True)

    from scapy.all import Ether, IP, UDP, TCP, ICMP, Raw, sendp, rdpcap, conf
    conf.verb = 0

    flows = build_flows(args)
    mark = (MARK + args.tag).encode()
    pad = b""
    if args.size > 28 + len(mark):
        pad = b"\x00" * (args.size - 28 - len(mark))

    total = len(flows) * args.per_flow
    print("LEG %s  iface=%s  flows=%d x %d = %d frame(s)  proto=%s  vary=%s"
          % (args.tag, args.iface, len(flows), args.per_flow, total, args.proto, args.vary))
    show = flows if len(flows) <= 6 else flows[:3] + [("...", "...", "...", "...")] + flows[-2:]
    for f in show:
        print("  flow %-15s -> %-15s  sport=%-6s dport=%s" % f)

    cap = None
    if not args.no_capture:
        cap = start_cap(args.iface, args.out, args.tag, args.filter)
        time.sleep(args.settle)

    pkts = []
    for (sip, dip, sport, dport) in flows:
        eth = Ether(src=args.src_mac, dst=args.gw_mac)
        ip = IP(src=sip, dst=dip, ttl=args.ttl)
        if args.proto == "udp":
            l4 = UDP(sport=sport, dport=dport)
        elif args.proto == "tcp":
            l4 = TCP(sport=sport, dport=dport, flags="S")
        else:
            l4 = ICMP(type=8, id=sport % 65536, seq=dport % 65536)
        pkts.append(eth / ip / l4 / Raw(load=mark + pad))

    t0 = time.time()
    for _ in range(args.per_flow):
        sendp(pkts, iface=args.iface, inter=args.gap, verbose=0)
    elapsed = time.time() - t0
    print("  sent %d frame(s) in %.2f s" % (total, elapsed))

    if cap is None:
        return 0

    time.sleep(args.wait)
    stop_cap(cap)

    try:
        caught = rdpcap(cap["path"])
    except Exception as exc:
        print("  cap %s: UNREADABLE (%s)" % (os.path.basename(cap["path"]), exc))
        return 7

    ours = 0
    groups = {}
    for p in caught:
        if Raw in p and mark in bytes(p[Raw].load):
            ours += 1
        line = classify(p)
        if line is None:
            continue
        groups[line] = groups.get(line, 0) + 1

    print("  cap %s: %d frame(s), %d of them ours"
          % (os.path.basename(cap["path"]), len(caught), ours))
    for line, n in sorted(groups.items(), key=lambda kv: -kv[1])[:args.top]:
        print("    x%-6d %s" % (n, line))

    # The attribution that makes this tool worth running: who answered, by source address.
    by_src = {}
    for p in caught:
        from scapy.layers.inet import IP as _IP, ICMP as _ICMP
        if _IP in p and _ICMP in p and p[_ICMP].type == 3:
            key = (p[_IP].src, p[_ICMP].code)
            by_src[key] = by_src.get(key, 0) + 1
    if by_src:
        print("  ICMP unreachables by SOURCE (which router received the flow):")
        for (src, code), n in sorted(by_src.items(), key=lambda kv: -kv[1]):
            print("    %-15s code %d   x%d" % (src, code, n))

    print("  pcap: %s" % cap["path"])
    if ours < total:
        print("  !! INSTRUMENT FAULT: sent %d marked frames, capture holds %d -- measurement void"
              % (total, ours))
        return 7
    return 0


if __name__ == "__main__":
    sys.exit(main())
