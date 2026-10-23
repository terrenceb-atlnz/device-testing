#!/usr/bin/env python3
"""radeap.py -- a RADIUS server that speaks enough EAP to drive an EAP-NOTIFICATION case.

Why this exists
---------------
`radsrv.py` is PAP only, and an authenticator never originates an
EAP-Request/Notification by itself: RFC 3748 5.2 notifications come from the
AUTHENTICATION SERVER, inside an Access-Challenge. So the only way to find out whether
a switch RELAYS one to its supplicant is to be the server and send one. The DUT's own
local RADIUS server cannot be made to emit one on demand.

It is deliberately NOT a general EAP server: it does EAP-Identity, EAP-Notification and
EAP-MD5, which is what an authentication-relay case needs. For real crypto use a
supplicant against the DUT's own server (`wpasup.py`).

What it does, per session
-------------------------
1. Access-Request carrying EAP-Response/Identity
     --notify TEXT  -> Access-Challenge with EAP-Request/Notification(TEXT)
     otherwise      -> Access-Challenge with EAP-Request/MD5-Challenge
2. Access-Request carrying EAP-Response/Notification (RFC 3748 5.2: no data)
   -> Access-Challenge with EAP-Request/MD5-Challenge
3. Access-Request carrying EAP-Response/MD5-Challenge
   -> digest verified: Access-Accept + EAP-Success
      digest wrong or user unknown: Access-Reject + EAP-Failure

Every reply carries a Message-Authenticator, which RFC 3579 requires on any RADIUS
packet containing an EAP-Message, and a State attribute so the NAS can correlate.

Run it as an ordinary user on a high port (STANDING-ORDERS 4: 1812 is privileged and
editing a packaged freeradius is root). Point the DUT at it with
`radius-server host <box> auth-port <n> key <secret>`.
"""

import argparse
import hashlib
import os
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import radius as R                                            # noqa: E402

EAP_MESSAGE, MESSAGE_AUTHENTICATOR, STATE, USER_NAME = 79, 80, 24, 1
ACCESS_REQUEST, ACCESS_ACCEPT, ACCESS_REJECT, ACCESS_CHALLENGE = 1, 2, 3, 11

EAP_REQUEST, EAP_RESPONSE, EAP_SUCCESS, EAP_FAILURE = 1, 2, 3, 4
EAP_IDENTITY, EAP_NOTIFICATION, EAP_NAK, EAP_MD5 = 1, 2, 3, 4
EAP_NAME = {1: 'Identity', 2: 'Notification', 3: 'Legacy-Nak', 4: 'MD5-Challenge'}


def eap_packet(code, ident, etype=None, data=b''):
    body = b'' if etype is None else bytes(bytearray([etype])) + data
    total = 4 + len(body)
    return bytes(bytearray([code, ident & 0xff])) + total.to_bytes(2, 'big') + body


def eap_attrs(payload):
    """RFC 3579: an EAP packet longer than 253 bytes is split over several EAP-Message
    attributes, which the receiver concatenates in order."""
    out = []
    while payload:
        out.append((EAP_MESSAGE, payload[:253]))
        payload = payload[253:]
    return out or [(EAP_MESSAGE, b'')]


def eap_from_attrs(attrs):
    """Concatenate every EAP-Message attribute back into one EAP packet."""
    buf = b''.join(v for t, v in attrs if t == EAP_MESSAGE)
    if len(buf) < 4:
        return None
    code, ident = buf[0], buf[1]
    ln = int.from_bytes(buf[2:4], 'big')
    etype = buf[4] if ln > 4 and len(buf) > 4 else None
    data = buf[5:ln] if ln > 5 and ln <= len(buf) else b''
    return {'code': code, 'id': ident, 'type': etype, 'data': data, 'raw': buf[:ln]}


class Log(object):
    def __init__(self, path=None):
        self.fh = open(path, 'a') if path else None

    def __call__(self, msg):
        line = '%s %s' % (time.strftime('%H:%M:%S'), msg)
        sys.stdout.write(line + '\n')
        sys.stdout.flush()
        if self.fh:
            self.fh.write(line + '\n')
            self.fh.flush()


def main():
    ap = argparse.ArgumentParser(description='A RADIUS server that speaks EAP-Identity, '
                                             'EAP-Notification and EAP-MD5.')
    ap.add_argument('--secret', default='testing123')
    ap.add_argument('--client', action='append', default=[],
                    help='IP allowed to send to us (repeatable). Others are DROPPED')
    ap.add_argument('--user', action='append', default=[], metavar='NAME:PASSWORD')
    ap.add_argument('--auth-port', type=int, default=11812)
    ap.add_argument('--bind', default='0.0.0.0')
    ap.add_argument('--notify', default=None,
                    help='send an EAP-Request/Notification carrying this text before the '
                         'MD5 challenge. Omit for the control: an identical run with no '
                         'notification in it')
    ap.add_argument('--notify-only', action='store_true',
                    help='after the Notification response, REJECT instead of challenging. '
                         'Isolates the notification exchange from the credential check')
    ap.add_argument('--log')
    ap.add_argument('--seconds', type=int, default=120)
    ap.add_argument('--stopfile')
    args = ap.parse_args()

    users = {}
    for u in args.user:
        name, _, pw = u.partition(':')
        users[name] = pw
    clients = set(args.client)
    log = Log(args.log)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.bind, args.auth_port))
    sock.settimeout(0.5)
    log('radeap listening on %s:%d  secret=<%d chars>  clients=%s  users=%s'
        % (args.bind, args.auth_port, len(args.secret),
           ','.join(sorted(clients)) or 'ANY', ','.join(sorted(users)) or 'none'))
    log('notification: %s' % (repr(args.notify) if args.notify else 'NONE (control run)'))

    sessions = {}          # State -> {'identity':…, 'challenge':…, 'eap_id':…, 'stage':…}
    counters = {'requests': 0, 'challenges': 0, 'notifications_sent': 0,
                'notification_responses': 0, 'accepts': 0, 'rejects': 0, 'dropped': 0}
    deadline = time.time() + args.seconds

    def reply(addr, code, ident, req_auth, eap_payload, state=None):
        attrs = list(eap_attrs(eap_payload)) if eap_payload is not None else []
        if state is not None:
            attrs.append((STATE, state))
        # Message-Authenticator must be present (as zeros) while it is computed, then
        # replaced -- radius.py's helper does exactly that.
        attrs = R.add_message_authenticator(code, ident, req_auth, attrs, args.secret)
        body = R.pack_attrs(attrs)
        auth = R.response_authenticator(code, ident, body, req_auth, args.secret)
        pkt = R.build(code, ident, auth, attrs)
        sock.sendto(pkt, addr)

    while time.time() < deadline:
        if args.stopfile and os.path.exists(args.stopfile):
            log('stopfile seen -- stopping')
            break
        try:
            data, addr = sock.recvfrom(8192)
        except socket.timeout:
            continue
        except Exception as exc:
            log('recv error: %s' % exc)
            continue

        if clients and addr[0] not in clients:
            counters['dropped'] += 1
            log('DROP packet from %s (not a configured client)' % addr[0])
            continue
        try:
            # radius.parse returns the BODY, not parsed attributes -- parse_attrs does that.
            code, ident, auth, body = R.parse(data)
            attrs = R.parse_attrs(body)
        except Exception as exc:
            counters['dropped'] += 1
            log('DROP malformed packet from %s: %s' % (addr[0], exc))
            continue
        if code != ACCESS_REQUEST:
            log('ignoring %s from %s' % (R.code_name(code), addr[0]))
            continue
        counters['requests'] += 1

        user = R.find(attrs, USER_NAME)
        user = user.decode('utf-8', 'replace') if user else ''
        state = R.find(attrs, STATE)
        eap = eap_from_attrs(attrs)
        if eap is None:
            log('Access-Request id=%d user=%r with NO EAP-Message -- rejecting '
                '(this server is EAP only)' % (ident, user))
            reply(addr, ACCESS_REJECT, ident, auth, None)
            counters['rejects'] += 1
            continue

        ename = EAP_NAME.get(eap['type'], 'type%s' % eap['type'])
        log('Access-Request id=%d user=%r  EAP code=%d(%s) id=%d type=%s len=%d'
            % (ident, user, eap['code'],
               {1: 'Request', 2: 'Response', 3: 'Success', 4: 'Failure'}.get(eap['code'], '?'),
               eap['id'], ename, len(eap['data'])))

        sess = sessions.get(state) if state else None
        if sess is None:
            sess = {'identity': user, 'challenge': None, 'stage': 'start'}

        next_eap_id = (eap['id'] + 1) & 0xff

        # --- EAP-Response/Identity -------------------------------------------------
        if eap['code'] == EAP_RESPONSE and eap['type'] == EAP_IDENTITY:
            sess['identity'] = eap['data'].decode('utf-8', 'replace') or user
            if args.notify:
                payload = eap_packet(EAP_REQUEST, next_eap_id, EAP_NOTIFICATION,
                                     args.notify.encode('utf-8'))
                sess['stage'] = 'notified'
                counters['notifications_sent'] += 1
                log('  -> Access-Challenge  EAP-Request/Notification id=%d text=%r'
                    % (next_eap_id, args.notify))
            else:
                sess['challenge'] = os.urandom(16)
                payload = eap_packet(EAP_REQUEST, next_eap_id, EAP_MD5,
                                     bytes(bytearray([16])) + sess['challenge'])
                sess['stage'] = 'challenged'
                log('  -> Access-Challenge  EAP-Request/MD5-Challenge id=%d' % next_eap_id)
            new_state = os.urandom(8)
            sessions[new_state] = sess
            counters['challenges'] += 1
            reply(addr, ACCESS_CHALLENGE, ident, auth, payload, new_state)
            continue

        # --- EAP-Response/Notification ---------------------------------------------
        if eap['code'] == EAP_RESPONSE and eap['type'] == EAP_NOTIFICATION:
            counters['notification_responses'] += 1
            log('  <- the supplicant ANSWERED the notification (data=%d bytes, RFC 3748 5.2 '
                'says it carries none)' % len(eap['data']))
            if args.notify_only:
                log('  -> Access-Reject + EAP-Failure (--notify-only)')
                reply(addr, ACCESS_REJECT, ident, auth,
                      eap_packet(EAP_FAILURE, eap['id']))
                counters['rejects'] += 1
                continue
            sess['challenge'] = os.urandom(16)
            payload = eap_packet(EAP_REQUEST, next_eap_id, EAP_MD5,
                                 bytes(bytearray([16])) + sess['challenge'])
            sess['stage'] = 'challenged'
            new_state = os.urandom(8)
            sessions[new_state] = sess
            counters['challenges'] += 1
            log('  -> Access-Challenge  EAP-Request/MD5-Challenge id=%d' % next_eap_id)
            reply(addr, ACCESS_CHALLENGE, ident, auth, payload, new_state)
            continue

        # --- EAP-Response/MD5-Challenge --------------------------------------------
        if eap['code'] == EAP_RESPONSE and eap['type'] == EAP_MD5:
            name = sess.get('identity') or user
            pw = users.get(name)
            chal = sess.get('challenge')
            got = eap['data'][1:1 + eap['data'][0]] if eap['data'] else b''
            if pw is None or chal is None:
                log('  -> Access-Reject + EAP-Failure (unknown user %r or no challenge state)'
                    % name)
                reply(addr, ACCESS_REJECT, ident, auth, eap_packet(EAP_FAILURE, eap['id']))
                counters['rejects'] += 1
                continue
            want = hashlib.md5(bytes(bytearray([eap['id']])) + pw.encode('utf-8')
                               + chal).digest()
            if got == want:
                log('  -> Access-Accept + EAP-Success for %r' % name)
                reply(addr, ACCESS_ACCEPT, ident, auth, eap_packet(EAP_SUCCESS, eap['id']))
                counters['accepts'] += 1
            else:
                log('  -> Access-Reject + EAP-Failure for %r (digest mismatch)' % name)
                reply(addr, ACCESS_REJECT, ident, auth, eap_packet(EAP_FAILURE, eap['id']))
                counters['rejects'] += 1
            continue

        # --- EAP-Response/Legacy-Nak and anything else ------------------------------
        if eap['code'] == EAP_RESPONSE and eap['type'] == EAP_NAK:
            log('  <- Legacy-Nak: the supplicant refused the method and asks for %s'
                % ','.join(str(b) for b in eap['data']))
        log('  -> Access-Reject + EAP-Failure (nothing else is implemented)')
        reply(addr, ACCESS_REJECT, ident, auth, eap_packet(EAP_FAILURE, eap['id']))
        counters['rejects'] += 1

    log('stopping. ' + '  '.join('%s=%d' % (k, counters[k]) for k in sorted(counters)))
    # The headline number for an EAP-Notification case: did the NAS carry it, and did a
    # response come back through it?
    log('NOTIFICATIONS SENT=%d  RESPONSES RELAYED BACK=%d'
        % (counters['notifications_sent'], counters['notification_responses']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
