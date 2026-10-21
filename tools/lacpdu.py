#!/usr/bin/env python3
"""lacpdu.py <pcap> [<pcap> ...]

Decodes the LACPDUs (EtherType 0x8809, slow-protocol subtype 1) in a tcpdump pcap and prints, per
sending MAC, how many were seen and the actor / partner fields of the LAST one: system priority,
system MAC, key, port priority, port number and the state byte decoded (Act=LACP_Activity,
Short=timeout, Agg, Sync, Coll, Dist, Def, Exp). Use it to prove which system id a LAG partner
advertises (a VCStack's virtual MAC, for example) and that it is Collecting/Distributing.
Standard library only: it reads the pcap format tcpdump -w writes (link type 1, either byte order,
micro or nanosecond stamps); other link types are skipped with a note.
"""
import struct, sys

STATE_BITS = ['Act', 'Short', 'Agg', 'Sync', 'Coll', 'Dist', 'Def', 'Exp']

def state_str(b):
    return '0x%02x(%s)' % (b, ','.join(n for i, n in enumerate(STATE_BITS) if b & (1 << i)))

def mac(b):
    return ':'.join('%02x' % x for x in b)

def tlv(b):
    # type(1) len(1) sysprio(2) sysmac(6) key(2) portprio(2) port(2) state(1) reserved(3)
    t, l, sp, sm, key, pp, pn, st = struct.unpack('!BBH6sHHHB', b[:17])
    return dict(type=t, len=l, sysprio=sp, sysmac=mac(sm), key=key, portprio=pp, port=pn, state=st)

def read_pcap(path):
    with open(path, 'rb') as f:
        gh = f.read(24)
        if len(gh) < 24:
            return
        magic = gh[:4]
        if magic in (b'\xd4\xc3\xb2\xa1', b'\x4d\x3c\xb2\xa1'):
            e = '<'
        elif magic in (b'\xa1\xb2\xc3\xd4', b'\xa1\xb2\x3c\x4d'):
            e = '>'
        else:
            sys.stderr.write('%s: not a pcap (magic %r)\n' % (path, magic)); return
        linktype = struct.unpack(e + 'I', gh[20:24])[0]
        if linktype != 1:
            sys.stderr.write('%s: link type %d, not Ethernet; skipped\n' % (path, linktype)); return
        while True:
            rh = f.read(16)
            if len(rh) < 16:
                return
            ts_s, ts_f, incl, orig = struct.unpack(e + 'IIII', rh)
            data = f.read(incl)
            if len(data) < incl:
                return
            yield ts_s, data

def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__); sys.exit(2)
    for path in sys.argv[1:]:
        per = {}
        total = 0; first = last = None
        for ts, d in read_pcap(path) or []:
            if len(d) < 14 + 2 + 20 + 20:
                continue
            etype = struct.unpack('!H', d[12:14])[0]
            if etype != 0x8809 or d[14] != 1:        # slow protocols, subtype 1 = LACP
                continue
            total += 1
            first = first if first is not None else ts; last = ts
            src = mac(d[6:12])
            a = tlv(d[16:36]); p = tlv(d[36:56])
            rec = per.setdefault(src, {'n': 0})
            rec['n'] += 1; rec['actor'] = a; rec['partner'] = p
        print('%s: %d LACPDUs%s' % (path, total, '' if total == 0 else ' over %d s' % (last - first)))
        for src, r in sorted(per.items()):
            a, p = r['actor'], r['partner']
            print('  from %s: %d  actor sys %s prio %d key %d port %d/%d state %s' % (
                src, r['n'], a['sysmac'], a['sysprio'], a['key'], a['portprio'], a['port'], state_str(a['state'])))
            print('      %s partner sys %s prio %d key %d port %d/%d state %s' % (
                ' ' * len(src), p['sysmac'], p['sysprio'], p['key'], p['portprio'], p['port'], state_str(p['state'])))

if __name__ == '__main__':
    main()
