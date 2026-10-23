#!/usr/bin/env python3
"""eapol.py -- a scapy 802.1X supplicant that can be SEVERAL supplicants at once on
one wire, each with its own source MAC.

Why this exists
---------------
`wpa_supplicant` is one supplicant per interface. A multi-supplicant case
(`auth host-mode multi-supplicant`, multiple dynamic VLANs, two-step
authentication, `auth max-supplicant`) needs two or more DISTINCT source MACs
authenticating on the SAME physical port, which no number of wpa_supplicant
instances on one NIC will give you. This drives each MAC itself.

It speaks EAP-MD5 (RFC 1994) and EAP-Identity, which is enough for every
authentication-MODE case: those cases are about which supplicants the
authenticator admits, not about the cipher. Use `wpasup.py` where the EAP method
itself is the subject (PEAP, TLS).

🔴 It listens with a BPF filter of `ether proto 0x888e`. On a bench running
loop-protection (tb277: 1 LDF/s across 57 instances) anything less drowns.

Grading
-------
Each supplicant is given an EXPECTED outcome (`success` or `failure`) in its own
spec, so a run carries its own control (STANDING-ORDERS §7: every counted leg
carries a control that must NOT match, in the same run). The exit status is 0
only if every supplicant did what its spec said.

Run as root (raw L2 socket): `tools/tb sudotool <TB> <scratch> eapol <iface> ...`.
"""

import argparse
import binascii
import hashlib
import json
import os
import select
import sys
import time

PAE_GROUP = '01:80:c2:00:00:03'   # the 802.1X PAE group address

EAPOL_EAP, EAPOL_START, EAPOL_LOGOFF = 0, 1, 2
EAP_REQUEST, EAP_RESPONSE, EAP_SUCCESS, EAP_FAILURE = 1, 2, 3, 4
EAP_IDENTITY, EAP_NOTIFICATION, EAP_NAK, EAP_MD5 = 1, 2, 3, 4

EAP_CODE = {1: 'Request', 2: 'Response', 3: 'Success', 4: 'Failure'}
EAP_METHOD = {1: 'Identity', 2: 'Notification', 3: 'Legacy-Nak', 4: 'MD5-Challenge',
              6: 'GTC', 13: 'TLS', 21: 'TTLS', 25: 'PEAP', 26: 'MSCHAPv2'}


def log(msg):
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()


class Supplicant(object):
    """One MAC's state machine."""

    def __init__(self, mac, identity, password, expect, nak_to=None):
        self.mac = mac.lower()
        self.identity = identity
        self.password = password
        self.expect = expect
        self.nak_to = nak_to          # offer this EAP type in a Legacy-Nak, or None
        self.state = 'init'           # init -> started -> identity-sent -> challenged -> done
        self.verdict = None           # 'success' | 'failure' | None (timed out)
        self.frames_rx = 0
        self.frames_tx = 0
        self.methods_offered = []     # EAP types the authenticator asked this MAC for
        self.notifications = []       # EAP-Request/Notification payloads seen (T33354)
        self.t_start = None
        self.t_done = None
        self.log = []

    def note(self, msg):
        self.log.append('%8.3f %s %s' % (time.time() - (self.t_start or time.time()),
                                         self.mac, msg))


def parse_spec(spec):
    """MAC:identity:password[:expect[:nak_to]]  -- expect defaults to success."""
    parts = spec.split(':')
    # a MAC has 6 colon-separated octets
    if len(parts) < 8:
        raise argparse.ArgumentTypeError(
            'bad --supplicant %r: want MAC:identity:password[:expect[:nak_to]]' % spec)
    mac = ':'.join(parts[:6])
    rest = parts[6:]
    identity = rest[0]
    password = rest[1] if len(rest) > 1 else ''
    expect = rest[2] if len(rest) > 2 and rest[2] else 'success'
    nak_to = int(rest[3]) if len(rest) > 3 and rest[3] else None
    if expect not in ('success', 'failure'):
        raise argparse.ArgumentTypeError('bad expect %r: success|failure' % expect)
    return Supplicant(mac, identity, password, expect, nak_to)


def main():
    ap = argparse.ArgumentParser(
        description='A scapy 802.1X supplicant; several source MACs on one interface.')
    ap.add_argument('iface', help='host NIC facing the authenticator, e.g. eth4')
    ap.add_argument('--supplicant', action='append', required=True, type=parse_spec,
                    metavar='MAC:identity:password[:expect[:nak_type]]',
                    help='repeatable. expect is success|failure (default success). '
                         'nak_type sends a Legacy-Nak offering that EAP type when the '
                         'authenticator asks for something else')
    ap.add_argument('--timeout', type=float, default=40.0,
                    help='seconds to run the whole exchange (default 40)')
    ap.add_argument('--stagger', type=float, default=0.0,
                    help='seconds between each supplicant\'s EAPOL-Start (default 0, '
                         'i.e. all at once)')
    ap.add_argument('--no-start', action='store_true',
                    help='do not send EAPOL-Start; wait for the authenticator to ask '
                         '(proves the authenticator initiates)')
    ap.add_argument('--logoff', action='store_true',
                    help='send EAPOL-Logoff for every supplicant at the end')
    ap.add_argument('--settle', type=float, default=2.0,
                    help='seconds to keep listening after the last verdict (default 2)')
    ap.add_argument('--pcap', default=None, help='write every EAPOL frame seen here')
    ap.add_argument('--json', default=None, help='write the full result as JSON here')
    ap.add_argument('--label', default='', help='a name for this run, echoed in the output')
    ap.add_argument('--debug', action='store_true',
                    help='also log the raw EAP Type-Data hex of every Request')
    args = ap.parse_args()

    try:
        from scapy.config import conf
        from scapy.layers.l2 import Ether
        from scapy.layers.eap import EAPOL, EAP
        from scapy.utils import wrpcap
    except Exception as exc:
        log('ERROR: scapy unavailable: %s' % exc)
        return 2

    if not os.path.exists('/sys/class/net/%s' % args.iface):
        log('ERROR: no such interface %s' % args.iface)
        return 2

    sups = {s.mac: s for s in args.supplicant}
    if len(sups) != len(args.supplicant):
        log('ERROR: two --supplicant specs share a MAC')
        return 2
    label = args.label or '%d supplicant(s) on %s' % (len(sups), args.iface)

    log('eapol %s' % label)
    for s in sups.values():
        log('  %s  identity=%-12s expect=%-7s %s'
            % (s.mac, s.identity, s.expect,
               ('nak->%s' % EAP_METHOD.get(s.nak_to, s.nak_to)) if s.nak_to else ''))
    log('  filter: ether proto 0x888e   timeout: %.0f s' % args.timeout)

    debug = args.debug

    def eap_type_data(pkt, eap):
        """The EAP Type-Data, taken from the RAW BYTES, never from scapy's dissection.

        🔴 Two traps, both of which silently corrupt an MD5 digest:
        1. scapy may dissect a known EAP method into its own class (EAP_MD5 and friends),
           in which case `eap.payload` is empty and the challenge is in a FIELD;
           or it may leave the Type-Data as a Raw payload. Which one you get depends on
           the scapy version, so neither is safe to rely on.
        2. An EAPOL frame shorter than 60 bytes is PADDED by Ethernet, and the padding
           lands in `eap.payload` whenever scapy has not trimmed it. Hashing the padding
           as part of the challenge produces a digest the server rejects, with no error
           anywhere that names the cause.
        Slicing the EAP header's own length field off the frame avoids both.
        """
        buf = bytes(pkt[EAPOL].payload.original if hasattr(pkt[EAPOL].payload, 'original')
                    else bytes(pkt[EAPOL].payload))
        if len(buf) < 5:
            return b''
        eap_len = int.from_bytes(buf[2:4], 'big')
        # Code(1) Identifier(1) Length(2) Type(1), then Type-Data to the declared length.
        if eap_len < 5 or eap_len > len(buf):
            eap_len = len(buf)
        return buf[5:eap_len]

    conf.verb = 0
    try:
        sock = conf.L2socket(iface=args.iface, filter='ether proto 0x888e')
    except Exception as exc:
        log('ERROR: cannot open a raw socket on %s: %s (need root)' % (args.iface, exc))
        return 2

    seen = []          # every frame, for the pcap and the printed table
    t0 = time.time()

    def send(sup, pkt):
        sup.frames_tx += 1
        seen.append(pkt)
        sock.send(pkt)

    def eapol_start(sup):
        p = Ether(src=sup.mac, dst=PAE_GROUP) / EAPOL(version=2, type=EAPOL_START)
        sup.t_start = sup.t_start or time.time()
        sup.state = 'started'
        sup.note('-> EAPOL-Start')
        send(sup, p)

    def eapol_logoff(sup):
        p = Ether(src=sup.mac, dst=PAE_GROUP) / EAPOL(version=2, type=EAPOL_LOGOFF)
        sup.note('-> EAPOL-Logoff')
        send(sup, p)

    def eap_response(sup, eap_id, eap_type, payload):
        body = bytes(bytearray([EAP_RESPONSE, eap_id & 0xff])) \
            + (5 + len(payload)).to_bytes(2, 'big') \
            + bytes(bytearray([eap_type])) + payload
        p = Ether(src=sup.mac, dst=PAE_GROUP) / EAPOL(version=2, type=EAPOL_EAP) / body
        send(sup, p)

    for s in sups.values():
        s.t_start = time.time()
    if not args.no_start:
        for i, s in enumerate(sups.values()):
            if args.stagger and i:
                time.sleep(args.stagger)
            eapol_start(s)

    deadline = time.time() + args.timeout
    settle_until = None
    while True:
        now = time.time()
        if now > deadline:
            break
        if settle_until and now > settle_until:
            break
        if all(s.verdict for s in sups.values()) and settle_until is None:
            settle_until = now + args.settle
        # 🔴 NEVER call sock.recv() unguarded. A scapy L2socket recv BLOCKS until a frame
        # arrives, so with the BPF filter in place an idle wire means the loop never comes
        # back to check the deadline and --timeout is silently ignored. Measured 2026-10-23:
        # a run with --timeout 25 was still alive 11 minutes later, holding eth4 in
        # promiscuous mode, and had to be killed by PID. select() first, always.
        try:
            ready, _, _ = select.select([sock], [], [], 0.5)
        except Exception:
            break
        if not ready:
            continue
        try:
            pkt = sock.recv(2048)
        except Exception:
            continue
        if pkt is None:
            continue
        if EAPOL not in pkt:
            continue
        seen.append(pkt)
        dst = (pkt.dst or '').lower()
        sup = sups.get(dst)
        if sup is None:
            # Broadcast/PAE-group EAP-Request/Identity: the authenticator asking anyone.
            if dst == PAE_GROUP and EAP in pkt and int(pkt[EAP].code) == EAP_REQUEST:
                targets = [s for s in sups.values() if s.state in ('init', 'started')]
            else:
                continue
        else:
            targets = [sup]

        for sup in targets:
            sup.frames_rx += 1
            if EAP not in pkt:
                sup.note('<- EAPOL type %d (no EAP)' % int(pkt[EAPOL].type))
                continue
            eap = pkt[EAP]
            code = int(eap.code)
            if code == EAP_SUCCESS:
                sup.verdict = 'success'
                sup.t_done = time.time()
                sup.note('<- EAP-Success id=%d' % int(eap.id))
                sup.state = 'done'
                continue
            if code == EAP_FAILURE:
                sup.verdict = 'failure'
                sup.t_done = time.time()
                sup.note('<- EAP-Failure id=%d' % int(eap.id))
                sup.state = 'done'
                continue
            if code != EAP_REQUEST:
                continue
            try:
                etype = int(eap.type)
            except Exception:
                sup.note('<- EAP-Request with no readable type')
                continue
            name = EAP_METHOD.get(etype, 'type%d' % etype)
            if name not in sup.methods_offered:
                sup.methods_offered.append(name)
            raw = eap_type_data(pkt, eap)
            sup.note('<- EAP-Request/%s id=%d len=%d%s'
                     % (name, int(eap.id), len(raw),
                        (' raw=' + binascii.hexlify(raw).decode()) if debug else ''))

            if etype == EAP_IDENTITY:
                eap_response(sup, int(eap.id), EAP_IDENTITY,
                             sup.identity.encode('utf-8'))
                sup.state = 'identity-sent'
                sup.note('-> EAP-Response/Identity "%s"' % sup.identity)
            elif etype == EAP_MD5:
                # RFC 1994: Value-Size, Value, Name
                if not raw:
                    sup.note('   (MD5-Challenge with an empty payload -- cannot answer)')
                    continue
                vsize = raw[0]
                challenge = raw[1:1 + vsize]
                digest = hashlib.md5(
                    bytes(bytearray([int(eap.id) & 0xff]))
                    + sup.password.encode('utf-8') + challenge).digest()
                payload = bytes(bytearray([len(digest)])) + digest \
                    + sup.identity.encode('utf-8')
                eap_response(sup, int(eap.id), EAP_MD5, payload)
                sup.state = 'challenged'
                sup.note('-> EAP-Response/MD5-Challenge digest=%s'
                         % binascii.hexlify(digest).decode())
            elif etype == EAP_NOTIFICATION:
                text = raw.decode('utf-8', 'replace')
                sup.notifications.append(text)
                sup.note('   NOTIFICATION TEXT: %r' % text)
                # RFC 3748 §5.2: a Notification Response carries no data.
                eap_response(sup, int(eap.id), EAP_NOTIFICATION, b'')
                sup.note('-> EAP-Response/Notification (empty, per RFC 3748 5.2)')
            else:
                target = sup.nak_to or EAP_MD5
                eap_response(sup, int(eap.id), EAP_NAK,
                             bytes(bytearray([target])))
                sup.note('-> EAP-Response/Legacy-Nak offering %s'
                         % EAP_METHOD.get(target, target))

    if args.logoff:
        for s in sups.values():
            eapol_logoff(s)
        time.sleep(0.5)

    try:
        sock.close()
    except Exception:
        pass

    if args.pcap and seen:
        try:
            wrpcap(args.pcap, seen)
            log('\npcap -> %s (%d EAPOL frames)' % (args.pcap, len(seen)))
        except Exception as exc:
            log('\nWARNING: could not write %s: %s' % (args.pcap, exc))

    log('')
    ok = True
    out = []
    for s in sups.values():
        for line in s.log:
            log('  ' + line)
        got = s.verdict or 'timeout'
        match = (got == s.expect)
        ok = ok and match
        secs = (s.t_done - s.t_start) if s.t_done else None
        log('  %s  expected %s, got %s -- %s%s'
            % (s.mac, s.expect, got, 'MATCH' if match else 'MISMATCH',
               ('  (%.2f s)' % secs) if secs else ''))
        log('')
        out.append({'mac': s.mac, 'identity': s.identity, 'expect': s.expect,
                    'verdict': got, 'match': match, 'seconds': secs,
                    'frames_tx': s.frames_tx, 'frames_rx': s.frames_rx,
                    'methods_offered': s.methods_offered,
                    'notifications': s.notifications, 'log': s.log})

    result = {'label': label, 'iface': args.iface, 'elapsed': round(time.time() - t0, 2),
              'total_eapol_frames': len(seen), 'supplicants': out, 'all_matched': ok}
    if args.json:
        with open(args.json, 'w') as fh:
            json.dump(result, fh, indent=2)
        log('json -> %s' % args.json)

    log('RESULT %s: %d/%d supplicant(s) matched their expectation -- %s'
        % (label, sum(1 for s in out if s['match']), len(out),
           'MATCH' if ok else 'MISMATCH'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
