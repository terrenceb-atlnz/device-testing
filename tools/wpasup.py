#!/usr/bin/env python3
"""wpasup.py -- drive wpa_supplicant as a WIRED 802.1X supplicant, with its own
filtered EAPOL capture, and grade the result.

Why this exists
---------------
An 802.1X case needs three things in one window: a supplicant that really speaks the
EAP method under test (so real crypto, not a hand-rolled frame), the EAPOL exchange on
the wire as evidence (STANDING-ORDERS §7: frame-level evidence or it did not happen),
and a verdict that is a comparison against what was EXPECTED rather than a human
reading a log. This does all three in one process, so the capture can never start
after the exchange it was meant to record (memory
`two-console-calls-in-one-block-run-sequentially`).

🔴 The capture is ALWAYS filtered `ether proto 0x888e`. On a bench running
loop-protection (tb277: 1 LDF/s across 57 instances) an unfiltered capture drowns.

What it does, in order
----------------------
1. starts `tcpdump` on the interface, filtered to EAPOL only, into --pcap;
2. writes a wpa_supplicant.conf for the chosen method into a private temp dir
   (mode 0600; it holds the password);
3. runs `wpa_supplicant -D wired` and watches its output for the CTRL-EVENT-EAP-*
   events;
4. stops at EAP-SUCCESS, EAP-FAILURE or --timeout, then sends EAPOL-Logoff by
   terminating wpa_supplicant;
5. stops tcpdump, decodes the pcap with scapy and prints one line per EAPOL frame;
6. grades the run against --expect and exits 0 only if it matched.

Run as root (tcpdump and a raw 802.1X socket): `tools/tb sudotool <TB> <scratch>
wpasup <iface> ...`.
"""

import argparse
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

EAPOL_TYPE = {0: 'EAP-Packet', 1: 'EAPOL-Start', 2: 'EAPOL-Logoff',
              3: 'EAPOL-Key', 4: 'EAPOL-Encapsulated-ASF-Alert'}
EAP_CODE = {1: 'Request', 2: 'Response', 3: 'Success', 4: 'Failure'}
EAP_METHOD = {1: 'Identity', 2: 'Notification', 3: 'Legacy-Nak', 4: 'MD5-Challenge',
              6: 'GTC', 13: 'TLS', 21: 'TTLS', 25: 'PEAP', 26: 'MSCHAPv2',
              43: 'FAST', 254: 'Expanded'}

# The wpa_supplicant network block per method. `identity` and `password` are filled in.
METHODS = {
    'peap': {'eap': 'PEAP', 'needs_password': True, 'phase2': 'auth=MSCHAPV2'},
    'peap-gtc': {'eap': 'PEAP', 'needs_password': True, 'phase2': 'auth=GTC'},
    'ttls': {'eap': 'TTLS', 'needs_password': True, 'phase2': 'auth=MSCHAPV2'},
    'md5': {'eap': 'MD5', 'needs_password': True, 'phase2': None},
    'tls': {'eap': 'TLS', 'needs_password': False, 'phase2': None},
}


def log(msg):
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()


def which(name):
    p = shutil.which(name)
    if p:
        return p
    for d in ('/sbin', '/usr/sbin', '/bin', '/usr/bin'):
        # `ssh tbNNN 'command -v foo'` misses sbin (memory `ssh-path-has-no-sbin`),
        # so never conclude absence from which() alone.
        cand = os.path.join(d, name)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def build_conf(args):
    m = METHODS[args.method]
    lines = ['ctrl_interface=/var/run/wpa_supplicant-%s' % args.iface,
             'eapol_version=%d' % args.eapol_version,
             'ap_scan=0',
             'fast_reauth=%d' % (1 if args.fast_reauth else 0),
             '',
             'network={',
             '\tkey_mgmt=IEEE8021X',
             '\teap=%s' % m['eap'],
             '\tidentity="%s"' % args.identity,
             '\teapol_flags=0']
    if args.anonymous_identity:
        lines.append('\tanonymous_identity="%s"' % args.anonymous_identity)
    if m['needs_password']:
        lines.append('\tpassword="%s"' % args.password)
    if m['phase2']:
        lines.append('\tphase2="%s"' % m['phase2'])
    if args.phase1:
        lines.append('\tphase1="%s"' % args.phase1)
    if args.ca_cert:
        lines.append('\tca_cert="%s"' % args.ca_cert)
    # No ca_cert: wpa_supplicant accepts the server certificate without validating it.
    # That is deliberate when the subject is the EXCHANGE rather than the trust chain,
    # and the banner says so, so a log can never imply the server was validated when it
    # was not. Do NOT emit tls_disable_tlsv1_3 here: wpa_supplicant 2.6 does not know
    # that field and rejects the whole config file with "unknown network field".
    if args.client_cert:
        lines.append('\tclient_cert="%s"' % args.client_cert)
    if args.private_key:
        lines.append('\tprivate_key="%s"' % args.private_key)
    if args.private_key_passwd:
        lines.append('\tprivate_key_passwd="%s"' % args.private_key_passwd)
    for extra in args.extra or []:
        lines.append('\t' + extra)
    lines.append('}')
    return '\n'.join(lines) + '\n'


def decode_pcap(path):
    """One row per EAPOL frame. Returns (rows, error_or_None)."""
    try:
        from scapy.all import rdpcap           # noqa: E402
        from scapy.layers.l2 import Ether      # noqa: F401,E402
        from scapy.layers.eap import EAPOL, EAP  # noqa: E402
    except Exception as exc:                   # scapy missing or broken
        return [], 'scapy unavailable: %s' % exc
    try:
        pkts = rdpcap(path)
    except Exception as exc:
        return [], 'cannot read %s: %s' % (path, exc)
    rows = []
    t0 = None
    for p in pkts:
        if EAPOL not in p:
            continue
        if t0 is None:
            t0 = float(p.time)
        e = p[EAPOL]
        row = {'t': round(float(p.time) - t0, 4),
               'src': p.src, 'dst': p.dst,
               'eapol_type': int(e.type),
               'eapol_name': EAPOL_TYPE.get(int(e.type), 'type%d' % e.type),
               'eap_code': None, 'eap_code_name': None,
               'eap_id': None, 'eap_type': None, 'eap_type_name': None,
               'len': len(p)}
        if EAP in p:
            a = p[EAP]
            row['eap_code'] = int(a.code)
            row['eap_code_name'] = EAP_CODE.get(int(a.code), 'code%d' % a.code)
            row['eap_id'] = int(a.id)
            # Success/Failure carry no type field.
            if int(a.code) in (1, 2):
                try:
                    row['eap_type'] = int(a.type)
                    row['eap_type_name'] = EAP_METHOD.get(int(a.type), 'type%d' % a.type)
                except Exception:
                    pass
            # Read the EAP header from the RAW bytes: scapy may dissect a known method
            # into its own class, and Ethernet padding otherwise pollutes the payload.
            # (The same two traps eapol.py documents.)
            try:
                buf = bytes(p[EAPOL].payload.original)
            except Exception:
                buf = b''
            if len(buf) >= 4:
                row['eap_len'] = int.from_bytes(buf[2:4], 'big')
                body = buf[5:row['eap_len']] if row['eap_len'] <= len(buf) else buf[5:]
                # RFC 5216 EAP-TLS: one flags octet (L=0x80 length-included,
                # M=0x40 more-fragments, S=0x20 start), then optionally a 4-byte
                # TLS message length, then the TLS data. An EAP-TLS ACK is a packet
                # with flags 0x00 and NO data -- eap_len 6.
                if row.get('eap_type') == 13 and body:
                    fl = body[0]
                    row['tls_flags'] = '0x%02x' % fl
                    row['tls_bits'] = ''.join(
                        [c for c, b in (('L', 0x80), ('M', 0x40), ('S', 0x20)) if fl & b]) or '-'
                    row['tls_is_ack'] = (row['eap_len'] == 6 and fl == 0)
                    if fl & 0x80 and len(body) >= 5:
                        row['tls_msg_len'] = int.from_bytes(body[1:5], 'big')
        rows.append(row)
    return rows, None


def main():
    ap = argparse.ArgumentParser(
        description='Drive wpa_supplicant as a wired 802.1X supplicant and grade the EAPOL exchange.')
    ap.add_argument('iface', help='host NIC facing the authenticator, e.g. eth4')
    ap.add_argument('--method', required=True, choices=sorted(METHODS),
                    help='EAP method to offer')
    ap.add_argument('--identity', required=True)
    ap.add_argument('--anonymous-identity', default=None,
                    help='outer identity for PEAP/TTLS (default: same as --identity)')
    ap.add_argument('--password', default=None, help='NOT for a real secret; see --password-env')
    ap.add_argument('--password-env', default=None,
                    help='read the password from this environment variable instead of argv')
    ap.add_argument('--ca-cert', default=None, help='PEM CA to validate the server with')
    ap.add_argument('--client-cert', default=None)
    ap.add_argument('--private-key', default=None, help='PEM key, or a PKCS#12 bundle')
    ap.add_argument('--private-key-passwd', default=None)
    ap.add_argument('--phase1', default=None, help='raw wpa_supplicant phase1 string')
    ap.add_argument('--extra', action='append',
                    help='raw extra line for the network block (repeatable)')
    ap.add_argument('--eapol-version', type=int, default=2)
    ap.add_argument('--fast-reauth', action='store_true')
    ap.add_argument('--timeout', type=float, default=45.0,
                    help='seconds to wait for EAP-Success/Failure (default 45)')
    ap.add_argument('--settle', type=float, default=2.0,
                    help='seconds to keep capturing after the verdict (default 2)')
    ap.add_argument('--pcap', default=None, help='where to write the EAPOL capture')
    ap.add_argument('--json', default=None, help='write the full result as JSON here')
    ap.add_argument('--label', default='', help='a name for this run, echoed in the output')
    ap.add_argument('--expect', choices=('success', 'failure', 'timeout'), default='success',
                    help='what this run is supposed to do. Exit 0 only if it matched. '
                         'A CONTROL leg that must not authenticate uses --expect failure')
    ap.add_argument('--keep-conf', action='store_true',
                    help='leave the generated wpa_supplicant.conf in place (it holds the password)')
    ap.add_argument('--wpa-debug', action='store_true', help='pass -dd instead of -d')
    args = ap.parse_args()

    if args.password_env:
        args.password = os.environ.get(args.password_env)
        if args.password is None:
            log('ERROR: $%s is not set' % args.password_env)
            return 2
    if METHODS[args.method]['needs_password'] and not args.password:
        log('ERROR: --method %s needs --password or --password-env' % args.method)
        return 2
    if args.method == 'tls' and not args.private_key:
        log('ERROR: --method tls needs --private-key (a PEM key or a .p12 bundle)')
        return 2

    wpa = which('wpa_supplicant')
    tcpdump = which('tcpdump')
    if not wpa:
        log('ERROR: wpa_supplicant not found')
        return 2
    if not tcpdump:
        log('ERROR: tcpdump not found')
        return 2

    if not os.path.exists('/sys/class/net/%s' % args.iface):
        log('ERROR: no such interface %s' % args.iface)
        return 2

    tmpdir = tempfile.mkdtemp(prefix='wpasup-')
    os.chmod(tmpdir, stat.S_IRWXU)
    conf_path = os.path.join(tmpdir, 'wpa_supplicant.conf')
    with open(conf_path, 'w') as fh:
        fh.write(build_conf(args))
    os.chmod(conf_path, stat.S_IRUSR | stat.S_IWUSR)

    pcap = args.pcap or os.path.join(tmpdir, 'eapol.pcap')
    label = args.label or '%s/%s' % (args.method, args.identity)

    log('wpasup %s' % label)
    log('  iface=%s method=%s identity=%s expect=%s'
        % (args.iface, args.method, args.identity, args.expect))
    log('  server certificate validation: %s'
        % ('ca_cert=%s' % args.ca_cert if args.ca_cert
           else 'NONE -- no ca_cert given, the server certificate is NOT validated'))
    log('  capture: %s  filter: ether proto 0x888e' % pcap)

    # 1. capture first, always filtered -- an unfiltered capture drowns in loop-protection LDFs.
    cap = subprocess.Popen([tcpdump, '-i', args.iface, '-n', '-e', '-s', '0',
                            '-U', '-w', pcap, 'ether', 'proto', '0x888e'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    time.sleep(1.5)   # let tcpdump attach before anything is sent
    if cap.poll() is not None:
        err = cap.stderr.read().decode('utf-8', 'replace')
        log('ERROR: tcpdump exited immediately: %s' % err.strip())
        return 2

    # 2. the supplicant.
    cmd = [wpa, '-D', 'wired', '-i', args.iface, '-c', conf_path,
           '-dd' if args.wpa_debug else '-d', '-t']
    log('  $ %s' % ' '.join(cmd))
    sup = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           bufsize=1, universal_newlines=True)

    events = []
    supout = []            # every line wpa_supplicant printed, for the mismatch diagnosis
    verdict = 'timeout'
    eap_method_seen = None
    deadline = time.time() + args.timeout
    pat = re.compile(r'CTRL-EVENT-EAP-(\w+)')
    try:
        import fcntl
        import select
        fl = fcntl.fcntl(sup.stdout, fcntl.F_GETFL)
        fcntl.fcntl(sup.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        buf = ''
        while time.time() < deadline and verdict == 'timeout':
            r, _, _ = select.select([sup.stdout], [], [], 0.5)
            if not r:
                if sup.poll() is not None:
                    break
                continue
            chunk = sup.stdout.read()
            if not chunk:
                if sup.poll() is not None:
                    break
                continue
            buf += chunk
            while '\n' in buf:
                line, buf = buf.split('\n', 1)
                supout.append(line)
                m = pat.search(line)
                if m:
                    ev = m.group(1)
                    events.append((round(time.time() - (deadline - args.timeout), 3),
                                   line.strip()))
                    if ev == 'METHOD':
                        eap_method_seen = line.strip()
                    elif ev == 'SUCCESS':
                        verdict = 'success'
                    elif ev == 'FAILURE':
                        verdict = 'failure'
    finally:
        time.sleep(args.settle)
        for proc in (sup,):
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
        time.sleep(0.5)
        if cap.poll() is None:
            cap.send_signal(signal.SIGTERM)
            try:
                cap.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cap.kill()
                cap.wait(timeout=5)

    rows, decode_err = decode_pcap(pcap)

    log('')
    log('EAP events from wpa_supplicant (%d):' % len(events))
    if not events:
        log('  (none -- the supplicant reported no CTRL-EVENT-EAP-* line)')
    for _, line in events:
        log('  %s' % line)

    log('')
    if decode_err:
        log('EAPOL frames: NOT DECODED -- %s' % decode_err)
    else:
        log('EAPOL frames on %s (%d, filtered ether proto 0x888e):' % (args.iface, len(rows)))
        log('  %-8s %-17s %-17s %-12s %-9s %-4s %-14s %-6s %s'
            % ('t(s)', 'src', 'dst', 'eapol', 'eap', 'id', 'method', 'eaplen', 'tls'))
        for r in rows:
            tls = ''
            if r.get('tls_flags'):
                tls = '%s %s' % (r['tls_flags'], r.get('tls_bits') or '-')
                if r.get('tls_msg_len') is not None:
                    tls += ' msglen=%d' % r['tls_msg_len']
                if r.get('tls_is_ack'):
                    tls += '  <- EMPTY ACK'
            log('  %-8s %-17s %-17s %-12s %-9s %-4s %-14s %-6s %s'
                % (r['t'], r['src'], r['dst'], r['eapol_name'],
                   r['eap_code_name'] or '-', r['eap_id'] if r['eap_id'] is not None else '-',
                   r['eap_type_name'] or '-', r.get('eap_len', '-'), tls))

    methods_offered = sorted({r['eap_type_name'] for r in rows
                              if r['eap_code'] == 1 and r['eap_type_name']})
    got_success_frame = any(r['eap_code'] == 3 for r in rows)
    got_failure_frame = any(r['eap_code'] == 4 for r in rows)

    result = {
        'label': label, 'iface': args.iface, 'method': args.method,
        'identity': args.identity, 'expect': args.expect, 'verdict': verdict,
        'eap_method_line': eap_method_seen,
        'eapol_frames': len(rows), 'request_methods': methods_offered,
        'eap_success_frame': got_success_frame, 'eap_failure_frame': got_failure_frame,
        'ca_cert': args.ca_cert, 'pcap': pcap,
        'events': [l for _, l in events], 'frames': rows,
    }
    # NOTE: the JSON is written ONCE, further down, only after the verdict is final.
    # Writing it here as well (as an earlier version did) leaves two writes of the same
    # path in one run and makes any disagreement between the file and the printed RESULT
    # impossible to reason about.
    log('')
    log('  EAP-Request methods the authenticator offered: %s'
        % (', '.join(methods_offered) or '(none seen)'))
    log('  EAP-Success frame on the wire: %s' % got_success_frame)
    log('  EAP-Failure frame on the wire: %s' % got_failure_frame)

    # 🔴 THE WIRE IS AUTHORITATIVE (STANDING-ORDERS §7). The verdict above comes from
    # wpa_supplicant's CTRL-EVENT lines, which it does not always emit: measured
    # 2026-10-23 (T9032 control), the DUT sent a clean EAP-Failure frame that is right
    # there in the pcap, wpa_supplicant printed no CTRL-EVENT-EAP-FAILURE for it, and the
    # run was graded "timeout" -- an instrument reporting silence while the evidence sat
    # in its own capture. When the events gave no verdict, read it off the frames instead.
    verdict_from = 'wpa_supplicant events'
    if verdict == 'timeout' and not decode_err:
        if got_success_frame:
            verdict, verdict_from = 'success', 'the WIRE (EAP-Success frame; no CTRL-EVENT line)'
        elif got_failure_frame:
            verdict, verdict_from = 'failure', 'the WIRE (EAP-Failure frame; no CTRL-EVENT line)'
    result['verdict'] = verdict
    result['verdict_from'] = verdict_from
    if args.json:
        with open(args.json, 'w') as fh:
            json.dump(result, fh, indent=2)
        log('')
        log('json -> %s' % args.json)

    ok = (verdict == args.expect)

    # 🔴 On a MISMATCH the CTRL-EVENT lines alone are rarely enough: a TLS handshake that
    # stalls says nothing in them, and the DUT's own log says only "Supplicant <u>
    # unauthorized". The reason is almost always in wpa_supplicant's ordinary output
    # (a certificate that would not load, an OpenSSL error, an alert it received), so
    # print the tail of it rather than leaving the run unexplained. Measured 2026-10-23
    # on T9032: 17 EAPOL frames of EAP-TLS and then silence, with no clue anywhere else.
    supfile = None
    if args.pcap:
        supfile = os.path.splitext(args.pcap)[0] + '-wpa_supplicant.log'
    elif args.json:
        supfile = os.path.splitext(args.json)[0] + '-wpa_supplicant.log'
    if supfile:
        try:
            with open(supfile, 'w') as fh:
                fh.write('\n'.join(supout) + '\n')
            log('')
            log('wpa_supplicant output -> %s (%d lines)' % (supfile, len(supout)))
        except Exception as exc:
            log('WARNING: could not write %s: %s' % (supfile, exc))
    if not ok and supout:
        log('')
        log('last %d lines of wpa_supplicant output (the run did NOT do what --expect said):'
            % min(40, len(supout)))
        for line in supout[-40:]:
            log('  | %s' % line)

    log('')
    log('RESULT %s: expected %s, got %s (from %s) -- %s'
        % (label, args.expect, verdict, verdict_from, 'MATCH' if ok else 'MISMATCH'))

    if not args.keep_conf:
        try:
            os.remove(conf_path)
        except OSError:
            pass
    if not args.pcap and not args.keep_conf:
        shutil.rmtree(tmpdir, ignore_errors=True)
    else:
        log('  (temp dir kept: %s)' % tmpdir)

    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
