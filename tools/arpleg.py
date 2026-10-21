#!/usr/bin/env python3
"""ARP / L2-L3 test leg: capture on one or more NICs, send crafted frames, report
who answered and with which MAC.

One leg = start tcpdump on every NIC named, send a known count of crafted frames,
stop, then decode the captures and print a grouped count of everything seen.

It is the evidence instrument for ARP cases (STANDING-ORDERS Section 7): the verdict rests
on the crafted frame and the control flow sent in the same leg, counted from the
wire -- never on a `show arp` read-back.

Two independent counters, always: the tool prints what it SENT beside what the
CAPTURE holds, and exits 7 when the capture of the sending NIC holds fewer of the
tool's own frames than were sent (the capture and the sender disagree).

Must run as root (raw sockets + tcpdump). Outputs are chowned back to SUDO_UID.

Run:
  sudo python3 arpleg.py --tag NAME --out DIR --iface eth3 [--watch eth4 ...]
       [--arp TARGET[,TARGET...]] [--probe DST[,DST...]] [--icmp DST[,DST...]]
       [--udp DST[:PORT][@SRC][%L2DST][,...]] [--tcp DST[:PORT][@SRC][%L2DST][,...]]
       [--l2-dst MAC|broadcast]
       [--show-ttl] [--sport N] [--ttl N]
       [--sender-ip IP] [--sender-mac MAC] [--gw-mac MAC]
       [--count N] [--settle S] [--wait S] [--filter BPF] [--vlan V]
       [--sniff-only]

Examples:
  # does the DUT proxy-ARP for an address in its other subnet?
  sudo arpleg.py --tag proxy-on --out /tmp/ck/T43848 --iface eth3 \
      --arp 192.168.48.5,10.99.99.99 --sender-ip 192.168.10.2 \
      --sender-mac 00:11:22:33:44:01 --count 3

  # does a static ARP entry stop the DUT ARPing, and does the frame egress with that MAC?
  sudo arpleg.py --tag static-on --out /tmp/ck/T33248 --iface eth3 --watch eth4 \
      --probe 192.168.48.9,192.168.48.10 --sender-ip 192.168.10.2 \
      --sender-mac 00:11:22:33:44:01 --gw-mac ee:ee:6b:xx:xx:xx --count 5

  # UDP broadcast helper: a helped port and an unhelped control port in ONE leg,
  # sent as a true link-layer broadcast, counted on the far segment
  sudo arpleg.py --tag helper-on --out /tmp/ck/T44378 --iface eth3 --watch eth4 \
       --udp 255.255.255.255:69,255.255.255.255:7777 --l2-dst broadcast \
       --sender-ip 10.38.22.40 --sender-mac 00:11:22:33:44:01 --count 5

  # passive: watch a NIC for 60 s (ARP polling, gratuitous ARP, a deauth)
  # TCP SYN leg: is a management port open, refused, or silently FILTERED?  The
  # three answers are SYN-ACK, RST, and nothing back -- and only the wire tells
  # them apart.  Send the subject and a control that must NOT be filtered in one leg.
  sudo arpleg.py --tag acl-on --out /tmp/ck/T33386 --iface eth3 --watch eth4 \
       --tcp 10.38.22.34:22,10.38.22.34:23 --sender-ip 10.38.22.33 \
       --sender-mac <eth3 mac> --gw-mac <DUT SVI mac> --count 4

  sudo arpleg.py --tag poll --out /tmp/ck/T33246 --iface eth3 --sniff-only --wait 60
"""
import argparse
import os
import subprocess
import sys
import time
from collections import OrderedDict

os.environ.setdefault("SCAPY_USE_PCAPDNET", "0")
import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import (  # noqa: E402
    ARP,
    AsyncSniffer,
    Dot1Q,
    Ether,
    ICMP,
    IP,
    UDP,
    PcapReader,
    Raw,
    TCP,
    sendp,
)

BCAST = "ff:ff:ff:ff:ff:ff"


def _sh(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, universal_newlines=True)


def start_caps(ifaces, outdir, tag, bpf, promisc=True):
    """Start one tcpdump per iface. Returns {iface: (popen, path)}.

    PROMISCUOUS BY DEFAULT, and it must stay that way. A routed frame leaves the
    DUT with the destination MAC of the *next hop*, which on a test bench is
    almost never the capturing NIC's own MAC -- a static ARP entry's fake MAC, a
    proxy-ARP target, a partner switch. A non-promiscuous capture silently drops
    every one of them and the leg reads as "the DUT forwarded nothing", which is
    indistinguishable from the feature being broken. Measured on tb277
    2026-10-15: T33248 leg 1 read 0 forwarded frames with `-p`, and 5 of 5 with
    the identical configuration once `-p` was removed.
    """
    caps = {}
    for ifc in ifaces:
        path = os.path.join(outdir, "%s-%s.pcap" % (tag, ifc))
        cmd = ["tcpdump", "-i", ifc, "-w", path, "-U", "-s", "0", "-n"]
        if not promisc:
            cmd.append("-p")
        if bpf:
            cmd.append(bpf)
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        caps[ifc] = (p, path)
    return caps


def stop_caps(caps):
    for ifc, (p, path) in caps.items():
        p.terminate()
    time.sleep(0.6)
    for ifc, (p, path) in caps.items():
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()


def chown_back(paths):
    uid = os.environ.get("SUDO_UID")
    gid = os.environ.get("SUDO_GID")
    if not uid:
        return
    for p in paths:
        try:
            os.chown(p, int(uid), int(gid))
        except OSError:
            pass


def tag_frame(pkt, vlan):
    if vlan:
        return pkt[Ether] / Dot1Q(vlan=vlan) / pkt.payload
    return pkt


class Answerer(object):
    """Answer ARP requests for given IPs, each with its own MAC, while a leg runs.

    A DUT only creates a DYNAMIC ARP entry for a neighbour that ANSWERS the ARP
    request the DUT itself sent. Measured on an x960-56YSQ 2026-10-15: sending the
    DUT an unsolicited ARP request -- even one asking for the DUT's own address,
    which RFC 826 says should populate the table -- left `show arp` empty. So any
    leg that needs a dynamic entry to exist must answer, not merely ask.

    It also lets a case STOP answering, which is how a poll/ageing/deauth timeout
    is driven (web-auth ARP polling, ARP ageing).
    """

    def __init__(self, iface, table, verbose=True):
        self.iface = iface
        self.table = table           # {ip: mac}
        self.sent = 0
        self.verbose = verbose
        self._s = None

    def _handle(self, pkt):
        if not pkt.haslayer(ARP):
            return
        a = pkt[ARP]
        if a.op != 1:
            return
        mac = self.table.get(a.pdst)
        if not mac:
            return
        if a.hwsrc in self.table.values():
            return               # never answer ourselves
        rep = (Ether(src=mac, dst=a.hwsrc) /
               ARP(op=2, hwsrc=mac, psrc=a.pdst, hwdst=a.hwsrc, pdst=a.psrc))
        sendp(rep, iface=self.iface, verbose=0)
        self.sent += 1

    def start(self):
        self._s = AsyncSniffer(iface=self.iface, filter="arp", store=False,
                               prn=self._handle)
        self._s.start()

    def stop(self):
        if self._s is not None:
            try:
                self._s.stop()
            except Exception:  # noqa: BLE001
                pass


def is_v4_multicast(addr):
    """True for an IPv4 address in 224.0.0.0/4."""
    try:
        return 224 <= int(addr.split(".")[0]) <= 239 and len(addr.split(".")) == 4
    except (ValueError, IndexError):
        return False


def mcast_mac(addr):
    """The IANA link-layer address for an IPv4 multicast group (RFC 1112 s.6.4)."""
    o = [int(x) for x in addr.split(".")]
    return "01:00:5e:%02x:%02x:%02x" % (o[1] & 0x7f, o[2], o[3])


def build(args):
    """Return a list of (description, frame) to send, in order."""
    out = []
    smac, sip = args.sender_mac, args.sender_ip
    for t in args.arp:
        eth = Ether(src=smac, dst=BCAST)
        op = 2 if args.announce else 1
        if op == 2:
            a = ARP(op=2, hwsrc=smac, psrc=sip, hwdst=BCAST, pdst=sip)
            f = eth / Dot1Q(vlan=args.vlan) / a if args.vlan else eth / a
            out.append(("gratuitous arp: %s is-at %s" % (sip, smac), f))
            continue
        a = ARP(op=1, hwsrc=smac, psrc=sip, hwdst="00:00:00:00:00:00", pdst=t)
        f = eth / Dot1Q(vlan=args.vlan) / a if args.vlan else eth / a
        out.append(("arp who-has %s tell %s" % (t, sip), f))
    l2 = args.l2_dst or args.gw_mac      # --l2-dst applies to --udp only
    for d in args.probe:
        if not args.gw_mac:
            sys.exit("--probe needs --gw-mac (the L2 next hop, i.e. the DUT SVI MAC)"
                     " or an explicit --l2-dst")
        eth = Ether(src=smac, dst=args.gw_mac)
        ip = IP(src=sip, dst=d, ttl=64) / UDP(sport=args.sport, dport=9) / Raw(
            load=b"CKARPLEG-" + args.tag.encode())
        f = eth / Dot1Q(vlan=args.vlan) / ip if args.vlan else eth / ip
        out.append(("udp %s -> %s:9 (eth dst %s)" % (sip, d, args.gw_mac), f))
    for spec in args.udp:
        # DST[:PORT][@SRC][%L2DST] -- %L2DST is parsed first because it is last.
        # A PER-SPEC Ethernet destination lets ONE leg carry a frame addressed to a
        # first-hop-redundancy virtual MAC AND a control addressed to a MAC nobody
        # owns; a single --l2-dst applies to every --udp spec and cannot.
        spec, _, l2_over = spec.partition("%")
        body, _, src_over = spec.partition("@")     # DST[:PORT][@SRC]
        ssrc = src_over or sip
        d, _, p = body.partition(":")
        port = int(p) if p else 9
        # An IPv4 MULTICAST destination has exactly one correct link-layer address
        # (RFC 1112 s.6.4: 01:00:5e + the low 23 bits), and it differs per group.
        # Deriving it means one leg can carry the subject group AND a control group
        # that was never joined, each correctly addressed -- which is what a
        # multicast verdict needs, and what a single --l2-dst cannot give.  An
        # explicit --l2-dst still wins, so a deliberately MISMATCHED L2 address
        # (a group's frame sent to another group's MAC) remains testable.
        l2d = l2
        if not args.l2_dst and is_v4_multicast(d):
            l2d = mcast_mac(d)
        if l2_over:                       # an explicit per-spec MAC wins over both
            l2d = BCAST if l2_over == "broadcast" else l2_over
        if not l2d:
            sys.exit("--udp needs --gw-mac or --l2-dst (use 'broadcast' for a true"
                     " link-layer broadcast, which a UDP-helper or directed-broadcast"
                     " case needs); an IPv4 multicast destination derives its own")
        eth = Ether(src=smac, dst=l2d)
        ip = IP(src=ssrc, dst=d, ttl=args.ttl) / UDP(sport=args.sport, dport=port) / Raw(
            load=b"CKARPLEG-" + args.tag.encode() + b"-p%d" % port)
        f = eth / Dot1Q(vlan=args.vlan) / ip if args.vlan else eth / ip
        out.append(("udp %s -> %s:%d (eth dst %s, ttl %d)"
                    % (ssrc, d, port, l2d, args.ttl), f))
    for spec in args.tcp:
        # DST[:PORT][@SRC][%L2DST], parsed exactly like --udp.  A TCP SYN is the
        # only probe that can tell an OPEN management port (SYN-ACK), a REFUSED one
        # (RST) and a SILENTLY FILTERED one (nothing back) apart -- a management-ACL
        # or port-filter verdict is precisely that three-way discrimination, and no
        # `show` command on the device can give it (platforms/x960.md s.5).
        spec, _, l2_over = spec.partition("%")
        body, _, src_over = spec.partition("@")
        ssrc = src_over or sip
        d, _, p = body.partition(":")
        port = int(p) if p else 22
        l2d = l2
        if l2_over:
            l2d = BCAST if l2_over == "broadcast" else l2_over
        if not l2d:
            sys.exit("--tcp needs --gw-mac or --l2-dst (the L2 next hop, i.e. the "
                     "DUT SVI MAC for a management address on a connected subnet)")
        eth = Ether(src=smac, dst=l2d)
        # The SYN carries the leg marker as payload, like every other frame this tool
        # sends, so the [ours] marking and the two-counter guard work for TCP too.
        # Data on a SYN is legal and a Linux-based target answers it normally -- but
        # that is exactly why the ACL-OFF baseline leg is run FIRST: a SYN-ACK there
        # proves the instrument before any silence is read as a filter.
        ip = IP(src=ssrc, dst=d, ttl=args.ttl) / TCP(
            sport=args.sport, dport=port, flags="S") / Raw(
            load=b"CKARPLEG-" + args.tag.encode() + b"-t%d" % port)
        f = eth / Dot1Q(vlan=args.vlan) / ip if args.vlan else eth / ip
        out.append(("tcp SYN %s:%d -> %s:%d (eth dst %s, ttl %d)"
                    % (ssrc, args.sport, d, port, l2d, args.ttl), f))
    for d in args.icmp:
        if not args.gw_mac:
            sys.exit("--icmp needs --gw-mac")
        eth = Ether(src=smac, dst=args.gw_mac)
        ip = IP(src=sip, dst=d, ttl=64) / ICMP() / Raw(
            load=b"CKARPLEG-" + args.tag.encode())
        f = eth / Dot1Q(vlan=args.vlan) / ip if args.vlan else eth / ip
        out.append(("icmp %s -> %s (eth dst %s)" % (sip, d, args.gw_mac), f))
    return out


SHOW_TTL = False     # set from --show-ttl in main()


def classify(pkt):
    """Return (kind, key) for grouping, or None to drop."""
    if not pkt.haslayer(Ether):
        return None
    e = pkt[Ether]
    vlan = pkt[Dot1Q].vlan if pkt.haslayer(Dot1Q) else None
    vtxt = " vlan%s" % vlan if vlan is not None else ""
    if pkt.haslayer(ARP):
        a = pkt[ARP]
        if a.op == 1:
            k = "ARP-REQ  who-has %-15s tell %-15s" % (a.pdst, a.psrc)
        elif a.op == 2:
            k = "ARP-REPLY %-15s is-at %s" % (a.psrc, a.hwsrc)
        else:
            k = "ARP-op%d  %s -> %s" % (a.op, a.psrc, a.pdst)
        return (k + vtxt, e.src, e.dst)
    if pkt.haslayer(IP):
        ip = pkt[IP]
        # Scan the WHOLE frame, not pkt[Raw]: scapy dissects well-known UDP ports into
        # their own layer (69 -> TFTP, 67/68 -> BOOTP, 53 -> DNS ...), so the marker is
        # not in Raw and the tool's own frames would read as foreign. Measured on tb277
        # 2026-10-16: a --udp ...:69 burst reported 0 of 5 as [ours].
        mine = b"CKARPLEG" in bytes(pkt)
        mark = " [ours]" if mine else ""
        # The TTL is the only field on the wire that says how many routers forwarded
        # a frame.  When two routers share one virtual MAC (VRRP/first-hop
        # redundancy) the hop count is what attributes a forwarded frame to ONE of
        # them -- the L2 and L3 headers are identical either way.
        if SHOW_TTL:
            mark += " ttl=%d" % ip.ttl
        if pkt.haslayer(ICMP):
            ic = pkt[ICMP]
            k = "ICMP t%d/c%d %-15s -> %-15s%s" % (ic.type, ic.code, ip.src,
                                                   ip.dst, mark)
        elif pkt.haslayer(TCP):
            t = pkt[TCP]
            # The FLAG COMBINATION is the whole measurement for a TCP leg: S is the
            # probe, SA an open port, R/RA a refused one, and the absence of any
            # reply row at all is a silent drop.
            k = "TCP  %-15s:%-5d -> %-15s:%-5d %-4s%s" % (
                ip.src, t.sport, ip.dst, t.dport, t.sprintf("%TCP.flags%"), mark)
        elif pkt.haslayer(UDP):
            u = pkt[UDP]
            k = "UDP  %-15s -> %-15s :%d%s" % (ip.src, ip.dst, u.dport, mark)
        else:
            k = "IP p%d %-15s -> %-15s%s" % (ip.proto, ip.src, ip.dst, mark)
        return (k + vtxt, e.src, e.dst)
    return ("ETH 0x%04x" % e.type + vtxt, e.src, e.dst)


def report(path, limit):
    groups = OrderedDict()
    total = 0
    ours = 0
    try:
        with PcapReader(path) as pr:
            for pkt in pr:
                total += 1
                c = classify(pkt)
                if c is None:
                    continue
                if b"CKARPLEG" in bytes(pkt):   # whole frame -- see classify()
                    ours += 1
                groups[c] = groups.get(c, 0) + 1
    except Exception as exc:  # noqa: BLE001
        print("    !! cannot read %s: %s" % (path, exc))
        return total, ours
    print("  cap %s: %d frame(s)" % (os.path.basename(path), total))
    for (k, esrc, edst), n in sorted(groups.items(), key=lambda kv: -kv[1])[:limit]:
        print("    x%-5d %s   [eth %s -> %s]" % (n, k, esrc, edst))
    if len(groups) > limit:
        print("    ... %d more distinct flow(s)" % (len(groups) - limit))
    return total, ours


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True, help="leg name; names the pcaps")
    ap.add_argument("--out", required=True, help="output dir (use a local /tmp path)")
    ap.add_argument("--iface", required=True, help="NIC the frames are sent from")
    ap.add_argument("--watch", action="append", default=[],
                    help="extra NIC to capture on (repeatable)")
    ap.add_argument("--arp", default="", help="comma list of ARP targets to ask for")
    ap.add_argument("--probe", default="",
                    help="comma list of IPv4 dsts for routed UDP probes (dport 9)")
    ap.add_argument("--udp", default="",
                    help="comma list of DST[:PORT][@SRC] UDP probes with a CHOSEN dport "
                         "(default 9) and optionally a per-spec source address; pair a "
                         "matched port or source with an unmatched one in the SAME leg "
                         "as the control (an ACL-filtered forwarding case needs two "
                         "sources in one capture)")
    ap.add_argument("--tcp", default="",
                    help="comma list of DST[:PORT][@SRC][%L2DST] TCP SYN probes "
                         "(default port 22). SYN-ACK = open, RST = refused, nothing "
                         "back = silently filtered -- the three-way answer a "
                         "management-ACL or port-filter case is graded on")
    ap.add_argument("--l2-dst", default="",
                    help="Ethernet destination for --udp ONLY (--probe and --icmp keep "
                         "--gw-mac, so one leg can carry a broadcast flow and a unicast "
                         "control). Use 'broadcast' for a true link-layer broadcast")
    ap.add_argument("--show-ttl", action="store_true",
                    help="append the received IPv4 TTL to each flow in the report; "
                         "the hop count is what tells two routers sharing one "
                         "virtual MAC apart (VRRP and other first-hop redundancy)")
    ap.add_argument("--sport", type=int, default=40000,
                    help="UDP/TCP source port")
    ap.add_argument("--ttl", type=int, default=64, help="IPv4 TTL of --udp frames")
    ap.add_argument("--icmp", default="", help="comma list of IPv4 dsts for ICMP echo")
    ap.add_argument("--sender-ip", default="192.168.10.2")
    ap.add_argument("--sender-mac", default="00:11:22:33:44:01")
    ap.add_argument("--gw-mac", default="", help="L2 next hop for --probe/--icmp")
    ap.add_argument("--count", type=int, default=3, help="frames per spec")
    ap.add_argument("--vlan", type=int, default=0, help="802.1Q tag to add")
    ap.add_argument("--settle", type=float, default=1.5,
                    help="seconds between tcpdump start and the first frame")
    ap.add_argument("--wait", type=float, default=3.0,
                    help="seconds to keep capturing after the last frame")
    ap.add_argument("--gap", type=float, default=0.25, help="seconds between frames")
    ap.add_argument("--filter", default="arp or ip or icmp", help="BPF for tcpdump")
    ap.add_argument("--answer", default="",
                    help="comma list of IP=MAC to answer ARP requests for, for the "
                         "duration of the leg (makes the DUT learn a DYNAMIC entry)")
    ap.add_argument("--answer-iface", default="",
                    help="comma list of NICs the answerer listens/replies on "
                         "(default: --iface). One answerer per NIC, sharing the "
                         "same IP=MAC table; each only ever sees its own wire")
    ap.add_argument("--announce", action="store_true",
                    help="send the --arp specs as GRATUITOUS ARP replies instead of requests")
    ap.add_argument("--no-promisc", action="store_true",
                    help="capture non-promiscuously; drops frames not addressed to the NIC")
    ap.add_argument("--sniff-only", action="store_true", help="capture only, send nothing")
    ap.add_argument("--top", type=int, default=12, help="distinct flows to print per cap")
    args = ap.parse_args()

    global SHOW_TTL
    SHOW_TTL = args.show_ttl

    if os.geteuid() != 0:
        sys.exit("arpleg.py must run as root (raw sockets + tcpdump)")

    args.arp = [x for x in args.arp.split(",") if x]
    args.probe = [x for x in args.probe.split(",") if x]
    args.udp = [x for x in args.udp.split(",") if x]
    args.tcp = [x for x in args.tcp.split(",") if x]
    if args.l2_dst.lower() in ("broadcast", "bcast"):
        args.l2_dst = "ff:ff:ff:ff:ff:ff"
    args.icmp = [x for x in args.icmp.split(",") if x]
    os.makedirs(args.out, exist_ok=True)
    chown_back([args.out])   # a root-owned --out dir blocks later non-root tools writing into it

    ifaces = [args.iface] + [w for w in args.watch if w != args.iface]
    frames = [] if args.sniff_only else build(args)

    print("LEG %s  iface=%s watch=%s count=%d" %
          (args.tag, args.iface, ",".join(args.watch) or "-", args.count))
    answer_tbl = {}
    for item in [x for x in args.answer.split(",") if x]:
        ip, _, mac = item.partition("=")
        if not mac:
            sys.exit("--answer wants IP=MAC, got %r" % item)
        answer_tbl[ip] = mac

    caps = start_caps(ifaces, args.out, args.tag, args.filter,
                      promisc=not args.no_promisc)
    answerers = []
    if answer_tbl:
        aifs = [x for x in (args.answer_iface or args.iface).split(",") if x]
        for aif in aifs:
            a = Answerer(aif, answer_tbl)
            a.start()
            answerers.append(a)
        print("  answering ARP for: %s  on %s" %
              (", ".join("%s=%s" % kv for kv in sorted(answer_tbl.items())),
               ",".join(aifs)))
    time.sleep(args.settle)

    sent = 0
    for desc, f in frames:
        print("  sent: %s  x%d" % (desc, args.count))
        for _ in range(args.count):
            sendp(f, iface=args.iface, verbose=0)
            sent += 1
            time.sleep(args.gap)
    if args.sniff_only:
        print("  sniff-only, %.1f s" % args.wait)
    time.sleep(args.wait)

    for a in answerers:
        a.stop()
    if answerers:
        print("  answerer sent %d ARP reply/replies (%s)" %
              (sum(a.sent for a in answerers),
               ", ".join("%s:%d" % (a.iface, a.sent) for a in answerers)))
    stop_caps(caps)
    paths = [p for (_, p) in caps.values()]
    chown_back(paths)

    print("  sent total: %d frame(s)" % sent)
    tx_seen = 0
    for ifc in ifaces:
        _, path = caps[ifc]
        tot, ours = report(path, args.top)
        if ifc == args.iface:
            tx_seen = ours
    print("  pcaps: %s" % " ".join(paths))

    # two independent counters: our own marked frames must appear on the sending NIC
    marked = len([1 for d, _ in frames if d.startswith(("udp", "icmp", "tcp"))]) * args.count
    if marked and tx_seen < marked:
        print("  !! COUNTER DISAGREEMENT: sent %d marked frame(s), capture on %s holds %d"
              % (marked, args.iface, tx_seen))
        return 7
    return 0


if __name__ == "__main__":
    sys.exit(main())
