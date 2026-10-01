#!/usr/bin/env python3
"""l2flows.py <duration_s> <pps_per_flow> <outdir> <nicA> <nicB> [--ethertype 0x88B5]
Four L2 test flows between two host NICs cabled to the DUT (raw AF_PACKET, ethertype
0x88B5 by default):
  B<a><b> broadcast nicA->nicB          B<b><a> broadcast nicB->nicA
  U<a><b> unicast   nicA->nicB's MAC    U<b><a> unicast   nicB->nicA's MAC
<a>/<b> is the LAST character of each NIC name (eth3 + eth2 -> B32 B23 U32 U23); if the two
NICs end in the same character, A and B are used instead (BAB BBA UAB UBA). The tag is
always 3 bytes, so the frame format does not depend on the NIC names.
Each frame carries tag(3) + seq(4, big-endian) + send epoch (double). Receivers on
nicA/nicB record (tag, seq, t_send, t_recv) for every frame not sent by that NIC.
Writes <outdir>/rx-<nicA>.txt, rx-<nicB>.txt, tx.txt (per-flow sent counts) and touches
<outdir>/DONE when finished. Needs root (raw sockets). Analyse with flowstat.py and
loopwin.py, giving them the same <nicA> <nicB>."""
import argparse, os, socket, struct, sys, threading, time

ETH_P = 0x88B5


def flow_tags(nic_a, nic_b):
    """(B_ab, B_ba, U_ab, U_ba) for flows nicA->nicB and nicB->nicA, plus the receiving
    NIC of each tag -- shared by flowstat.py and loopwin.py so all three agree."""
    a, b = nic_a[-1:], nic_b[-1:]
    if a == b or len(a.encode()) != 1 or len(b.encode()) != 1:
        a, b = 'A', 'B'
    tags = ('B' + a + b, 'B' + b + a, 'U' + a + b, 'U' + b + a)
    rxnic = {tags[0]: nic_b, tags[2]: nic_b, tags[1]: nic_a, tags[3]: nic_a}
    return tags, rxnic


def mac(ifn):
    return bytes.fromhex(open('/sys/class/net/%s/address' % ifn).read().strip().replace(':', ''))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('duration_s', type=float)
    ap.add_argument('pps_per_flow', type=int)
    ap.add_argument('outdir')
    ap.add_argument('nicA', help='first host NIC (e.g. the one cabled to DUT port X)')
    ap.add_argument('nicB', help='second host NIC')
    ap.add_argument('--ethertype', type=lambda x: int(x, 0), default=ETH_P,
                    help='EtherType of the test frames (default 0x88B5, IEEE local experimental)')
    a = ap.parse_args(argv)
    dur, pps, outdir, eth_p = a.duration_s, a.pps_per_flow, a.outdir, a.ethertype
    nic_a, nic_b = a.nicA, a.nicB
    if nic_a == nic_b:
        ap.error('nicA and nicB must differ')
    os.makedirs(outdir, exist_ok=True)

    MA, MB = mac(nic_a), mac(nic_b)
    BC = b'\xff' * 6
    (b_ab, b_ba, u_ab, u_ba), _ = flow_tags(nic_a, nic_b)
    FLOWS = [(nic_a, BC, MA, b_ab.encode()), (nic_b, BC, MB, b_ba.encode()),
             (nic_a, MB, MA, u_ab.encode()), (nic_b, MA, MB, u_ba.encode())]
    sent = {}
    stop = threading.Event()
    t_start = time.time() + 1.0          # common start so flows are phase-aligned

    def sender(ifn, dst, src, tag):
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        s.bind((ifn, 0))
        hdr = dst + src + struct.pack('!H', eth_p)
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
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(eth_p))
        s.bind((ifn, eth_p))
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
          for i in (nic_b, nic_a)]
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
    return 0


if __name__ == '__main__':
    sys.exit(main())
