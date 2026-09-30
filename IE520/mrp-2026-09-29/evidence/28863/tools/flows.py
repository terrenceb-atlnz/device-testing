#!/usr/bin/env python3
"""flows.py <duration_s> <pps_per_flow> <outdir>
Four L2 test flows between tb470 eth3 and eth2 (raw AF_PACKET, ethertype 0x88B5):
  B32 broadcast eth3->eth2   B23 broadcast eth2->eth3
  U32 unicast   eth3->eth2's MAC   U23 unicast eth2->eth3's MAC
Each frame carries tag(3) + seq(4, big-endian) + send epoch (double). Receivers on
eth2/eth3 record (tag, seq, t_send, t_recv) for every frame not sent by that NIC.
Writes <outdir>/rx-eth2.txt, rx-eth3.txt, tx.txt (per-flow sent counts) and touches
<outdir>/DONE when finished. Needs root (raw sockets)."""
import os, socket, struct, sys, threading, time

ETH_P = 0x88B5
dur, pps, outdir = float(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
os.makedirs(outdir, exist_ok=True)

def mac(ifn):
    return bytes.fromhex(open('/sys/class/net/%s/address' % ifn).read().strip().replace(':', ''))

M2, M3 = mac('eth2'), mac('eth3')
BC = b'\xff' * 6
FLOWS = [('eth3', BC, M3, b'B32'), ('eth2', BC, M2, b'B23'),
         ('eth3', M2, M3, b'U32'), ('eth2', M3, M2, b'U23')]
sent = {}
stop = threading.Event()
t_start = time.time() + 1.0          # common start so flows are phase-aligned

def sender(ifn, dst, src, tag):
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    s.bind((ifn, 0))
    hdr = dst + src + struct.pack('!H', ETH_P)
    n = int(dur * pps)
    while time.time() < t_start:
        time.sleep(0.001)
    i = 0
    for i in range(n):
        target = t_start + i / pps
        d = target - time.time()
        if d > 0:
            time.sleep(d)
        s.send(hdr + tag + struct.pack('!Id', i, time.time()) + b'\0' * 30)
    sent[tag.decode()] = n
    s.close()

def receiver(ifn, out):
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P))
    s.bind((ifn, ETH_P))
    s.settimeout(0.2)
    rec = []
    while not stop.is_set():
        try:
            data, addr = s.recvfrom(2048)
        except socket.timeout:
            continue
        tr = time.time()
        if addr[2] == socket.PACKET_OUTGOING:
            continue
        tag = data[14:17]
        seq, ts = struct.unpack('!Id', data[17:29])
        rec.append((tag.decode(errors='replace'), seq, ts, tr))
    s.close()
    with open(out, 'w') as f:
        for r in rec:
            f.write('%s %d %.6f %.6f\n' % r)

rx = [threading.Thread(target=receiver, args=(i, os.path.join(outdir, 'rx-%s.txt' % i)))
      for i in ('eth2', 'eth3')]
for t in rx:
    t.start()
tx = [threading.Thread(target=sender, args=f) for f in FLOWS]
for t in tx:
    t.start()
open(os.path.join(outdir, 'START'), 'w').write('%.6f\n' % t_start)
for t in tx:
    t.join()
time.sleep(1.0)                      # let the last frames land
stop.set()
for t in rx:
    t.join()
with open(os.path.join(outdir, 'tx.txt'), 'w') as f:
    for k, v in sorted(sent.items()):
        f.write('%s %d\n' % (k, v))
    f.write('pps %d start %.6f\n' % (pps, t_start))
open(os.path.join(outdir, 'DONE'), 'w').write('%.6f\n' % time.time())
