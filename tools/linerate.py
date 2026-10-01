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


def build_pcap(path, src_mac, dst_mac, src_ip, dst_ip, dport, wire_size, count=500,
               sport=5010, ttl=2):
    from scapy.all import Ether, IP, UDP, Raw, wrpcap
    built = wire_size - 4                                 # FCS is added by the NIC
    payload = built - 14 - 20 - 8                         # Ether + IPv4 + UDP headers
    if payload < 0:
        sys.exit("frame too small: %d on the wire" % wire_size)
    p = Ether(src=src_mac, dst=dst_mac) / IP(src=src_ip, dst=dst_ip, ttl=ttl) / \
        UDP(sport=sport, dport=dport) / Raw(bytes(payload))
    assert len(p) == built, len(p)
    wrpcap(path, [p] * count)                             # 500 copies: tcpreplay loops it


def run(args):
    src_mac = args.src_mac or nic_mac(args.tx)
    src_ip = args.src_ip or nic_ipv4(args.tx)
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
    build_pcap(pcap, src_mac, args.dst_mac, src_ip, args.dst_ip, args.dport, args.size,
               sport=args.sport, ttl=args.ttl)

    # receivers first, so the first frame is counted; -s 64 keeps the kernel copy tiny and
    # -B 65536 the ring big enough that "packets dropped by kernel" stays 0 at line rate
    tds = {}
    for rx in args.rx:
        tds[rx] = subprocess.Popen(
            ["tcpdump", "-i", rx, "-nn", "-s", "64", "-B", "65536", "-w", "/dev/null",
             "ether src %s and udp src port %d" % (src_mac, args.sport)],
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
    print("%s-%s  tx %s -> %s  %d-byte frames  rate=%s" % (t0, t1, args.tx, args.dst_mac,
                                                          args.size, args.rate))
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
    ap.add_argument("--dst-ip", default="192.0.2.1")
    ap.add_argument("--dport", type=int, default=9)
    ap.add_argument("--sport", type=int, default=5010,
                    help="UDP source port; receivers filter on it (default 5010)")
    ap.add_argument("--ttl", type=int, default=2, help="IPv4 TTL (default 2)")
    ap.add_argument("--size", type=int, default=1500, help="frame size ON THE WIRE (default 1500)")
    ap.add_argument("--rate", default="top", help="Mbps, or 'top' for line rate (default)")
    ap.add_argument("--secs", type=int, default=10)
    ap.add_argument("--pcap", default=None, help="write the pcap here and keep it (default: a temp file, removed after the run)")
    args = ap.parse_args(argv)
    args.rx = [x for x in args.rx.split(",") if x]
    if os.geteuid() != 0:
        sys.exit("run as root (raw sockets, tcpreplay, tcpdump)")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
