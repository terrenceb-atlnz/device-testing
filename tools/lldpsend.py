#!/usr/bin/env python3
"""lldpsend.py -- advertise a controllable LLDP neighbour from a host NIC, with scapy.

Why it exists.  `lldpmed_phone.py` emulates an IP phone: it always sends the LLDP-MED endpoint
TLV set and then does DHCP, ARP and a ping.  An LLDP case usually needs something plainer and
more controllable -- a neighbour whose chassis ID, port ID and **TTL** you choose, which you
can start and stop on command.  That is what makes neighbour ageing measurable in seconds
instead of waiting out a partner switch's 120 s default, and what gives a receive-side test a
control flow (STANDING-ORDERS §7: the exact frame, plus one that must NOT match).

It is the sender half of `lldpwire.py`, which decodes what comes back.

Usage:
  sudo lldpsend.py <iface> [--count N] [--interval S] [--ttl S]
                   [--chassis-mac MAC] [--port-id STR] [--sys-name STR] [--sys-desc STR]
                   [--mgmt-ip A.B.C.D] [--caps bridge,router,telephone] [--vlan V]
                   [--med-class N] [--med-policy voice:VLAN:PRIO:DSCP] [--shutdown]
                   [--pcap FILE]

  --count N         how many advertisements to send (default 3); 0 with --shutdown sends
                    only the shutdown frame
  --interval S      seconds between advertisements (default 1.0)
  --ttl S           the TTL this neighbour advertises (default 30).  The switch must hold the
                    entry for exactly this long after the last frame -- that is the ageing test
  --chassis-mac     chassis ID to advertise (default: the interface's own MAC)
  --port-id         port ID string to advertise (default: the interface name)
  --caps            comma list from: other repeater bridge wlan router telephone docsis station
  --vlan V          send the advertisements 802.1Q-tagged in VLAN V
  --med-class N     add the LLDP-MED Capabilities TLV with Endpoint Class N (1, 2 or 3)
  --med-policy      add an LLDP-MED Network Policy TLV, e.g. voice:70:5:46
  --shutdown        after the advertisements, send one frame with TTL 0 (the LLDP shutdown
                    frame), which asks the neighbour to delete the entry immediately
  --pcap FILE       also write every frame sent to this pcap, so the sent side is on record

Exit: 0 when every frame was sent, 2 on a usage error.
"""

import argparse
import os
import struct
import sys
import time

CHASSIS_SUBTYPE_MAC = 4
PORT_SUBTYPE_IFNAME = 5
LLDP_MULTICAST = "01:80:c2:00:00:0e"

OUI_8021 = b"\x00\x80\xc2"
OUI_MED = b"\x00\x12\xbb"

CAP_BITS = {"other": 0x01, "repeater": 0x02, "bridge": 0x04, "wlan": 0x08,
            "router": 0x10, "telephone": 0x20, "docsis": 0x40, "station": 0x80}

MED_APP = {"voice": 1, "voice-signaling": 2, "guest-voice": 3, "guest-voice-signaling": 4,
           "softphone": 5, "video-conferencing": 6, "streaming-video": 7,
           "video-signaling": 8}


def tlv(ttype, value):
    if len(value) > 511:
        raise ValueError("TLV %d too long (%d bytes)" % (ttype, len(value)))
    return struct.pack("!H", (ttype << 9) | len(value)) + value


def mac_bytes(text):
    hexes = "".join(c for c in text.lower() if c in "0123456789abcdef")
    if len(hexes) != 12:
        raise ValueError("not a MAC address: %r" % text)
    return bytes.fromhex(hexes)


def iface_mac(iface):
    with open("/sys/class/net/%s/address" % iface) as fh:
        return fh.read().strip()


def network_policy(app, vlan, prio, dscp, tagged=True):
    bits = ((0 << 23) | ((1 if tagged else 0) << 22) | ((vlan & 0x0FFF) << 9)
            | ((prio & 0x07) << 6) | (dscp & 0x3F))
    return bytes([app, (bits >> 16) & 0xFF, (bits >> 8) & 0xFF, bits & 0xFF])


def build_lldpdu(args, chassis, port_id, ttl):
    pdu = tlv(1, bytes([CHASSIS_SUBTYPE_MAC]) + chassis)
    pdu += tlv(2, bytes([PORT_SUBTYPE_IFNAME]) + port_id.encode())
    pdu += tlv(3, struct.pack("!H", ttl))
    if args.port_desc:
        pdu += tlv(4, args.port_desc.encode())
    if args.sys_name:
        pdu += tlv(5, args.sys_name.encode())
    if args.sys_desc:
        pdu += tlv(6, args.sys_desc.encode())
    if args.caps:
        mask = 0
        for name in args.caps.split(","):
            key = name.strip().lower()
            if key not in CAP_BITS:
                raise ValueError("unknown capability %r" % name)
            mask |= CAP_BITS[key]
        pdu += tlv(7, struct.pack("!HH", mask, mask))
    if args.mgmt_ip:
        octets = bytes(int(x) for x in args.mgmt_ip.split("."))
        pdu += tlv(8, bytes([len(octets) + 1, 1]) + octets + bytes([2])
                   + struct.pack("!I", 1) + bytes([0]))
    if args.vlan:
        pdu += tlv(127, OUI_8021 + b"\x01" + struct.pack("!H", args.vlan))
    if args.med_class:
        caps = 0x01 | (0x02 if args.med_policy else 0)
        pdu += tlv(127, OUI_MED + b"\x01" + struct.pack("!H", caps) + bytes([args.med_class]))
    if args.med_policy:
        name, vlan, prio, dscp = args.med_policy.split(":")
        if name.lower() not in MED_APP:
            raise ValueError("unknown MED application %r" % name)
        pdu += tlv(127, OUI_MED + b"\x02"
                   + network_policy(MED_APP[name.lower()], int(vlan), int(prio), int(dscp)))
    return pdu + tlv(0, b"")


def main(argv=None):
    ap = argparse.ArgumentParser(description="advertise an LLDP neighbour from a host NIC")
    ap.add_argument("iface")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--ttl", type=int, default=30)
    ap.add_argument("--chassis-mac")
    ap.add_argument("--port-id")
    ap.add_argument("--port-desc")
    ap.add_argument("--sys-name")
    ap.add_argument("--sys-desc")
    ap.add_argument("--mgmt-ip")
    ap.add_argument("--caps")
    ap.add_argument("--vlan", type=int)
    ap.add_argument("--med-class", type=int, choices=(1, 2, 3))
    ap.add_argument("--med-policy", help="app:vlan:priority:dscp, e.g. voice:70:5:46")
    ap.add_argument("--shutdown", action="store_true")
    ap.add_argument("--src-mac", help="source MAC of the frames (default: the interface's)")
    ap.add_argument("--pcap")
    args = ap.parse_args(argv)

    if args.ttl < 0 or args.ttl > 65535:
        print("lldpsend: --ttl out of range", file=sys.stderr)
        return 2
    try:
        from scapy.all import Ether, Dot1Q, Raw, sendp, wrpcap
    except ImportError:
        print("lldpsend: scapy is required (STANDING-ORDERS §7)", file=sys.stderr)
        return 2
    if os.geteuid() != 0:
        print("lldpsend: must run as root to send raw frames", file=sys.stderr)
        return 2

    try:
        own = iface_mac(args.iface)
        chassis = mac_bytes(args.chassis_mac or own)
        src = args.src_mac or (args.chassis_mac or own)
        port_id = args.port_id or args.iface
        pdu = build_lldpdu(args, chassis, port_id, args.ttl)
    except (OSError, ValueError) as e:
        print("lldpsend: %s" % e, file=sys.stderr)
        return 2

    def frame(payload):
        eth = Ether(dst=LLDP_MULTICAST, src=src, type=0x88CC)
        if args.vlan:
            eth = Ether(dst=LLDP_MULTICAST, src=src) / Dot1Q(vlan=args.vlan, type=0x88CC)
        return eth / Raw(load=payload)

    sent = []
    print("lldpsend %s: chassis %s, port-id %s, ttl %d s, %d frame(s) every %.2f s%s"
          % (args.iface, ":".join("%02x" % b for b in chassis), port_id, args.ttl,
             args.count, args.interval,
             ", vlan %d" % args.vlan if args.vlan else ""))
    for i in range(args.count):
        pkt = frame(pdu)
        sendp(pkt, iface=args.iface, verbose=False)
        sent.append(pkt)
        print("  %.3f sent frame %d/%d" % (time.time(), i + 1, args.count))
        if i + 1 < args.count:
            time.sleep(args.interval)
    if args.shutdown:
        bye = build_lldpdu(args, chassis, port_id, 0)
        pkt = frame(bye)
        sendp(pkt, iface=args.iface, verbose=False)
        sent.append(pkt)
        print("  %.3f sent SHUTDOWN frame (TTL 0)" % time.time())
    if args.pcap and sent:
        wrpcap(args.pcap, sent)
        print("wrote %d frame(s) to %s" % (len(sent), args.pcap))
    print("done: %d frame(s) sent on %s" % (len(sent), args.iface))
    return 0


if __name__ == "__main__":
    sys.exit(main())
