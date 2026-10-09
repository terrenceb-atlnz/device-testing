#!/usr/bin/env python3
"""linerate.py -- send a stream at a chosen rate (up to 1G line rate) from one host NIC and
count what arrives on others. tcpreplay does the sending, scapy builds the frames, tcpdump
counts. Measured 2026-09-24/25 on a testbox with 1G host NICs: ~984 Mbps of frame bytes with
1500-byte frames (= 1G line rate once preamble + IFG are added), two NICs at once, zero
kernel drops.

Run ON the testbox as root (raw sockets, tcpreplay, tcpdump). NIC_A/NIC_B/NIC_C are host
NICs cabled to DUT ports in the same VLAN:

  # 10 s of known-unicast at 100 Mbps from NIC_C to NIC_A's MAC, count on NIC_A and NIC_B
  sudo python3 linerate.py --tx NIC_C --dst-mac $(cat /sys/class/net/NIC_A/address) \\
       --rate 100 --rx NIC_A,NIC_B

  # 10 s of DLF (a never-learned destination) at line rate -- floods every port in the VLAN
  sudo python3 linerate.py --tx NIC_C --dst-mac 02:00:00:00:99:99 --rate top --rx NIC_A,NIC_B

  # two senders at once: run two copies with --rx naming the OTHER sender's NIC as well

--size is the frame size ON THE WIRE (default 1500 = 1496 built + 4 FCS; AW+ treats anything
over 1508 as jumbo). Source MAC and IPv4 default to the sending NIC's own. The stream is UDP
--sport (default 5010) -> --dport (use a different dport per kind of traffic so receivers can
filter), IPv4 TTL --ttl (default 2). Receivers count frames whose source MAC is the sender's
and UDP sport is --sport, so a flooded copy of the sender's own frames is what they see.

The pcap is a build artefact, rebuilt on every run: by default it is a temporary file in the
system temp directory, removed when the run ends; --pcap PATH writes it there and keeps it.

The corosync DLF drivers (IE520/corosync-dlf-2026-09-25/tdlf*.py) are this loop with a
console session around it (terminal monitor + sdma counters); this file is the traffic half.
"""
import argparse
import os
import re
import signal
import subprocess
import sys
import tempfile
import time


def nic_mac(nic):
    return open("/sys/class/net/%s/address" % nic).read().strip()


def nic_ipv4(nic):
    r = subprocess.run(["ip", "-4", "-o", "addr", "show", nic], capture_output=True, text=True)
    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", r.stdout)
    return m.group(1) if m else "10.0.0.1"


def src_mac_list(src_mac, n, prefix="02:cc:00:00"):
    """n source MACs: the given one, then locally-administered <prefix>:HH:LL variants."""
    if n <= 1:
        return [src_mac]
    return [src_mac] + ["%s:%02x:%02x" % (prefix, i >> 8, i & 0xFF) for i in range(1, n)]


def build_pcap(path, src_mac, dst_mac, src_ip, dst_ip, dport, wire_size, count=500,
               sport=5010, ttl=2, ipv6=False, src_macs=1, mac_prefix="02:cc:00:00"):
    from scapy.all import Ether, IP, IPv6, UDP, Raw, wrpcap
    built = wire_size - 4                                 # FCS is added by the NIC
    l3 = 40 if ipv6 else 20
    payload = built - 14 - l3 - 8                         # Ether + IP + UDP headers
    if payload < 0:
        sys.exit("frame too small: %d on the wire" % wire_size)
    macs = src_mac_list(src_mac, src_macs, mac_prefix)
    count = max(count, len(macs))
    frames = []
    for i in range(count):
        ip = IPv6(src=src_ip, dst=dst_ip, hlim=ttl) if ipv6 else IP(src=src_ip, dst=dst_ip, ttl=ttl)
        p = Ether(src=macs[i % len(macs)], dst=dst_mac) / ip / \
            UDP(sport=sport, dport=dport) / Raw(bytes(payload))
        assert len(p) == built, len(p)
        frames.append(p)
    wrpcap(path, frames)                                  # tcpreplay loops it
    return built


def run(args):
    src_mac = args.src_mac or nic_mac(args.tx)
    if args.ipv6 and not (args.src_ip and args.dst_ip):
        sys.exit("--ipv6 needs --src-ip and --dst-ip (IPv6 addresses)")
    src_ip = args.src_ip or nic_ipv4(args.tx)
    args.dst_ip = args.dst_ip or "192.0.2.1"
    if args.pcap:
        pcap = args.pcap
    else:                                                 # scratch: removed after the run
        fd, pcap = tempfile.mkstemp(prefix="linerate-%s-%d-" % (args.tx, args.size),
                                    suffix=".pcap")
        os.close(fd)
    try:
        return send_and_count(args, pcap, src_mac, src_ip)
    finally:
        if not args.pcap and os.path.exists(pcap):
            os.unlink(pcap)


def send_and_count(args, pcap, src_mac, src_ip):
    built = build_pcap(pcap, src_mac, args.dst_mac, src_ip, args.dst_ip, args.dport, args.size,
                       sport=args.sport, ttl=args.ttl, ipv6=args.ipv6, src_macs=args.src_macs,
                       mac_prefix=args.mac_prefix)

    # receivers first, so the first frame is counted; -s 64 keeps the kernel copy tiny and
    # -B 65536 the ring big enough that "packets dropped by kernel" stays 0 at line rate.
    # Filter: the frames' source MAC as they ARRIVE (--rx-mac: the router's egress MAC for a
    # routed stream, 'any' for none), the UDP source port, and with --rx-len the exact
    # length sent (a frame that lost or gained bytes on the way is then not counted).
    rx_mac = args.rx_mac or (src_mac if args.src_macs <= 1 else "any")
    flt = ["%s and udp src port %d" % ("ip6" if args.ipv6 else "ip", args.sport)]
    if rx_mac != "any":
        flt.insert(0, "ether src %s" % rx_mac)
    if args.rx_len:
        flt.append("len = %d" % built)
    flt = " and ".join(flt)
    tds = {}
    for rx in args.rx:
        tds[rx] = subprocess.Popen(
            ["tcpdump", "-i", rx, "-nn", "-s", "64", "-B", "65536", "-w", "/dev/null", flt],
            stderr=subprocess.PIPE, text=True)
    time.sleep(2)

    cmd = ["tcpreplay", "-i", args.tx, "--duration=%d" % args.secs, "--loop=0"]
    cmd += ["--topspeed"] if args.rate == "top" else ["--mbps=%s" % args.rate]
    cmd.append(pcap)
    t0 = time.strftime("%H:%M:%S")
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    t1 = time.strftime("%H:%M:%S")
    time.sleep(2)                                         # let the last frames land

    got = {}
    for rx, p in tds.items():
        p.send_signal(signal.SIGINT)
        err = p.communicate()[1]
        cap = re.search(r"(\d+) packets captured", err)
        kd = re.search(r"(\d+) packets dropped by kernel", err)
        got[rx] = (int(cap.group(1)) if cap else -1, int(kd.group(1)) if kd else -1)

    m = re.search(r"Actual: (\d+) packets.*?Rated: ([\d.]+) Bps, ([\d.]+) Mbps, ([\d.]+) pps",
                  out, re.S)
    if not m:
        sys.exit("tcpreplay gave no summary:\n" + out)
    sent, mbps, pps = int(m.group(1)), float(m.group(3)), float(m.group(4))
    wire = pps * (args.size + 20) * 8 / 1e6               # + 8 preamble/SFD + 12 IFG
    print("%s-%s  tx %s -> %s  %d-byte frames  rate=%s  %s %s -> %s ttl/hlim %d  src MACs %d"
          % (t0, t1, args.tx, args.dst_mac, args.size, args.rate, "IPv6" if args.ipv6 else "IPv4",
             src_ip, args.dst_ip, args.ttl, args.src_macs))
    print("  rx filter: %s" % flt)
    print("  sent %d   tcpreplay %.1f Mbps (frame bytes)  %.0f pps  = %.1f Mbps on the wire"
          % (sent, mbps, pps, wire))
    for rx, (n, kd) in got.items():
        pct = 100.0 * n / sent if sent else 0
        print("  rx %-5s %9d  (%5.1f%%)  kernel drops %d" % (rx, n, pct, kd))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tx", required=True, help="sending host NIC")
    ap.add_argument("--rx", default="", help="receiving NICs to count on, comma-separated")
    ap.add_argument("--dst-mac", required=True,
                    help="destination MAC: a learned host MAC (unicast) or an unlearned one (DLF)")
    ap.add_argument("--src-mac", default=None, help="default: the sending NIC's MAC")
    ap.add_argument("--src-ip", default=None, help="default: the sending NIC's IPv4")
    ap.add_argument("--dst-ip", default=None, help="default 192.0.2.1 (IPv4); required with --ipv6")
    ap.add_argument("--dport", type=int, default=9)
    ap.add_argument("--sport", type=int, default=5010,
                    help="UDP source port; receivers filter on it (default 5010)")
    ap.add_argument("--ttl", type=int, default=2, help="IPv4 TTL (default 2)")
    ap.add_argument("--size", type=int, default=1500, help="frame size ON THE WIRE (default 1500)")
    ap.add_argument("--rate", default="top", help="Mbps, or 'top' for line rate (default)")
    ap.add_argument("--secs", type=int, default=10)
    ap.add_argument("--ipv6", action="store_true",
                    help="IPv6/UDP instead of IPv4 (needs --src-ip and --dst-ip; --ttl is the hop limit)")
    ap.add_argument("--src-macs", type=int, default=1,
                    help="rotate this many source MACs (the sender's, then 02:cc:00:00:xx:xx; default 1)")
    ap.add_argument("--mac-prefix", default="02:cc:00:00",
                    help="first 4 octets of the generated source MACs (default 02:cc:00:00); use a different "
                         "one per direction so two senders never share a MAC")
    ap.add_argument("--rx-mac", default=None,
                    help="count frames ARRIVING with this source MAC (a router's egress MAC for routed "
                         "traffic), or 'any'; default the sender's MAC (any with --src-macs > 1)")
    ap.add_argument("--rx-len", action="store_true",
                    help="count only frames of exactly the length sent (catches a lost/added tag)")
    ap.add_argument("--pcap", default=None, help="write the pcap here and keep it (default: a temp file, removed after the run)")
    args = ap.parse_args(argv)
    args.rx = [x for x in args.rx.split(",") if x]
    if os.geteuid() != 0:
        sys.exit("run as root (raw sockets, tcpreplay, tcpdump)")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
