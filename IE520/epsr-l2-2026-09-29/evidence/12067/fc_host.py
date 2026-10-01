#!/usr/bin/env python3
"""T12067 host side (tb470 /tmp scratch only).

gen   <pcap>                      500 x 1000-byte unicast frames eth1 -> eth3 MAC,
                                  ethertype 0x88B5 (local experimental: no IP, never routed)
pause <iface> <secs> <period_ms> [quanta]
                                  send 802.3x PAUSE frames (01:80:c2:00:00:01, 0x8808,
                                  opcode 0x0001) every period_ms for secs; prints count
"""
import sys, time, struct
from scapy.all import Ether, Raw, wrpcap, conf

SRC = '00:f0:4d:00:77:16'   # tb470 eth1 (IXIA1)
DST = '00:f0:4d:00:77:18'   # tb470 eth3 (IXIA2)

def mac_of(iface):
    return open('/sys/class/net/%s/address' % iface).read().strip()

if sys.argv[1] == 'gen':
    pkts = [Ether(src=SRC, dst=DST, type=0x88B5) / Raw(struct.pack('!I', i) + b'\x00' * (1000 - 14 - 4))
            for i in range(500)]
    wrpcap(sys.argv[2], pkts)
    print('wrote', len(pkts), 'frames of', len(pkts[0]), 'bytes to', sys.argv[2])
elif sys.argv[1] == 'pause':
    iface, secs, period = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]) / 1000.0
    quanta = int(sys.argv[5], 0) if len(sys.argv) > 5 else 0xFFFF
    frm = bytes(Ether(src=mac_of(iface), dst='01:80:c2:00:00:01', type=0x8808) /
                Raw(struct.pack('!HH', 0x0001, quanta) + b'\x00' * 42))
    s = conf.L2socket(iface=iface)
    n, t0 = 0, time.time()
    nxt = t0
    while time.time() - t0 < secs:
        s.send(frm)
        n += 1
        nxt += period
        d = nxt - time.time()
        if d > 0:
            time.sleep(d)
    s.close()
    print('PAUSE sent: %d frames on %s in %.2f s, period %.1f ms, quanta 0x%04x, len %d'
          % (n, iface, time.time() - t0, period * 1000, quanta, len(frm)))
