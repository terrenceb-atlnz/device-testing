#!/usr/bin/env python3
"""ixtcl.py <action> --chassis IP [--login NAME] --ports C/P[,C/P...] [options]

Drive an IXIA chassis through the lab's IxOS Tcl client (IxTclHal, its own tclsh8.5) on a testbox.
Every call connects (ixConnectToTclServer FIRST, then ixConnectToChassis, ixLogin), acts, disconnects.
Every IxTclHal action's return code is printed as `RC <label> <code>`; a non-zero code (or a Tcl error)
makes the call exit 1 -- never ignored. Memory `ixia-chassis-82-tcl-access` holds the background.

Actions
  status                    read-only: owner, link, speed/duplex, transmit state, rates, stream 1 summary
  counters [--tsv FILE]     read-only: one `TSV` line per port (absolute + rate; header with --header);
                            --tsv appends the lines to FILE as well
  take [--force]            ixTakeOwnership (force: steal from the current owner)
  release                   ixClearOwnership (ports back to no owner)
  reset                     port setFactoryDefaults + write (clears streams AND filters)
  stream --port C/P --sa MAC --da MAC [--sip IP --dip IP --sport N --dport N] --size N --percent P
         (--continuous | --count N) [--vlan VID] [--stream-id 1]
                            one EthernetII/IPv4/UDP stream, fixed addresses, written to hardware
  filter --port C/P [--uds1-sa MAC] [--uds1-da MAC] [--uds2-sa MAC] [--uds2-da MAC]
                            user-defined stats: UDS1 = frames matching SA1/DA1, UDS2 = SA2/DA2
                            (an omitted address is "any"); counted as userDefinedStat1/2
  clear                     ixClearStats on --ports
  start | stop              ixStartTransmit / ixStopTransmit on --ports
  burst [--timeout S]       clear, start, wait for ixCheckTransmitDone (count streams), print counters

MACs as 00:00:00:00:00:01 (or 00-00-..., or 6 space-separated bytes). Ports as card/port; the chassis id
is the one ixGetChassisID returns. Env IXOS_HOME (default /home/ixos-IxNetwork), IXIA_VERSION (default 9.20).
Exit: 0 ok, 1 an RC was non-zero or Tcl failed, 2 usage.
"""
import argparse, os, re, subprocess, sys, tempfile, time

H = os.environ.get('IXOS_HOME', '/home/ixos-IxNetwork')
FIELDS = ['link', 'transmitState', 'framesSent', 'framesReceived', 'userDefinedStat1', 'userDefinedStat2',
          'fcsErrors', 'bytesSent', 'bytesReceived', 'undersize', 'oversize']
RATE_FIELDS = ['framesSent', 'framesReceived', 'userDefinedStat1']
TSV_HEADER = ('epoch\ttime\tport\t' + '\t'.join(FIELDS) + '\t' + '\t'.join('rate_' + f for f in RATE_FIELDS))


def mac(s):
    b = re.split(r'[:\- ]', s.strip())
    if len(b) != 6 or not all(re.match(r'^[0-9A-Fa-f]{1,2}$', x) for x in b):
        raise argparse.ArgumentTypeError('bad MAC %r' % s)
    return '{%s}' % ' '.join(x.zfill(2).upper() for x in b)


def port(s):
    m = re.match(r'^(\d+)/(\d+)$', s.strip())
    if not m:
        raise argparse.ArgumentTypeError('bad port %r (want card/port)' % s)
    return (int(m.group(1)), int(m.group(2)))


def env():
    return dict(os.environ, IXIA_HOME=H, IXIA_TCL_DIR=H + '/lib', TCLLIBPATH=H + '/lib',
                TCL_LIBRARY=H + '/lib/tcl8.5', TK_LIBRARY=H + '/lib/tk8.5',
                LD_LIBRARY_PATH='/usr/lib:' + H + '/lib', IXIA_VERSION=os.environ.get('IXIA_VERSION', '9.20'))


PRELUDE = r'''
set ::ixtcl_bad 0
proc rc {label args} {
    if {[catch {uplevel 1 $args} res]} { puts "RC $label ERR [string map {"\n" " | "} $res]"; set ::ixtcl_bad 1; return -1 }
    puts "RC $label $res"
    if {$res ne "0" && $res ne ""} { set ::ixtcl_bad 1 }
    return $res
}
proc opt {obj field} { if {[catch {$obj cget -$field} v]} { return "na" }; return $v }
package require IxTclHal
'''


def run_tcl(chassis, login, body, timeout=180):
    """Run connect + body + disconnect in the client's tclsh8.5. Returns (exit, stdout text)."""
    tcl = [PRELUDE,
           'if {[rc tclserver ixConnectToTclServer %s] != 0} { exit 1 }' % chassis,
           'if {[rc chassis ixConnectToChassis %s] != 0} { exit 1 }' % chassis,
           'set ch [ixGetChassisID %s]' % chassis]
    if login:
        tcl.append('rc login ixLogin %s' % login)
    tcl += body
    tcl += ['catch {ixDisconnectFromChassis %s}' % chassis, 'catch {ixDisconnectTclServer %s}' % chassis,
            'exit $::ixtcl_bad']
    fd, path = tempfile.mkstemp(suffix='.tcl', prefix='ixtcl-')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write('\n'.join(tcl) + '\n')
        try:
            r = subprocess.run([H + '/bin/tclsh8.5', path], env=env(), stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            return 1, (e.stdout or b'').decode('utf-8', 'replace') + '\nRC tclsh TIMEOUT %s s\n' % timeout
        return r.returncode, r.stdout.decode('utf-8', 'replace')
    finally:
        os.unlink(path)


def plist_tcl(ports):
    # a list with $ch substituted (braces would stop substitution)
    return 'set pl [list %s]' % ' '.join('[list $ch %d %d]' % p for p in ports)


def counter_body(ports):
    b = []
    for c, p in ports:
        flds = ' '.join('[opt stat %s]' % f for f in FIELDS)
        b += ['if {[stat get statAllStats $ch %d %d] != 0} { puts "RC stat_%d/%d nonzero"; set ::ixtcl_bad 1 }' % (c, p, c, p),
              'set vals [list %s]' % flds,
              'if {[stat getRate allStats $ch %d %d] != 0} { puts "RC rate_%d/%d nonzero"; set ::ixtcl_bad 1 }' % (c, p, c, p),
              'set rates [list %s]' % ' '.join('[opt stat %s]' % f for f in RATE_FIELDS),
              'puts "TSV\t[clock seconds]\t[clock format [clock seconds] -format {%%Y-%%m-%%dT%%H:%%M:%%S}]\t%d/%d\t[join $vals \\t]\t[join $rates \\t]"' % (c, p)]
    return b


def parse_tsv(out):
    rows = []
    for line in out.splitlines():
        if line.startswith('TSV\t'):
            v = line.split('\t')[1:]
            keys = ['epoch', 'time', 'port'] + FIELDS + ['rate_' + f for f in RATE_FIELDS]
            rows.append(dict(zip(keys, v)))
    return rows


def counters(chassis, login, ports, timeout=120):
    """Library use (longrun.py): returns (exit, rows, raw)."""
    rc, out = run_tcl(chassis, login, counter_body(ports), timeout=timeout)
    return rc, parse_tsv(out), out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('action', choices=['status', 'counters', 'take', 'release', 'reset', 'stream', 'filter',
                                       'clear', 'start', 'stop', 'burst'])
    ap.add_argument('--chassis', required=True)
    ap.add_argument('--login', default=None)
    ap.add_argument('--ports', default=None, help='card/port[,card/port...] for status/counters/take/release/reset/clear/start/stop/burst')
    ap.add_argument('--port', type=port, help='card/port for stream/filter')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--tsv', default=None)
    ap.add_argument('--header', action='store_true')
    ap.add_argument('--sa', type=mac); ap.add_argument('--da', type=mac)
    ap.add_argument('--sip', default='0.0.0.0'); ap.add_argument('--dip', default='0.0.0.0')
    ap.add_argument('--sport', type=int, default=5000); ap.add_argument('--dport', type=int, default=5000)
    ap.add_argument('--size', type=int, default=512)
    ap.add_argument('--percent', type=float, default=1.0)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--continuous', action='store_true'); g.add_argument('--count', type=int)
    ap.add_argument('--vlan', type=int, default=None)
    ap.add_argument('--stream-id', type=int, default=1)
    for n in ('uds1-sa', 'uds1-da', 'uds2-sa', 'uds2-da'):
        ap.add_argument('--' + n, type=mac, default=None)
    ap.add_argument('--timeout', type=int, default=180)
    a = ap.parse_args()

    ports = [port(x) for x in a.ports.split(',')] if a.ports else []
    if a.action in ('status', 'counters', 'take', 'release', 'reset', 'clear', 'start', 'stop', 'burst') and not ports:
        ap.error('--ports is required for %s' % a.action)
    if a.action in ('stream', 'filter') and not a.port:
        ap.error('--port is required for %s' % a.action)
    login = a.login
    if a.action in ('take', 'release', 'reset', 'stream', 'filter', 'clear', 'start', 'stop', 'burst') and not login:
        ap.error('--login is required for an action that writes to the chassis')

    body = []
    if a.action == 'status':
        for c, p in ports:
            body += ['rc port_get_%d/%d port get $ch %d %d' % (c, p, c, p),
                     'puts "PORT %d/%d owner=[port cget -owner] speed=[port cget -speed] duplex=[port cget -duplex] '
                     'autoneg=[port cget -autonegotiate] type=[port cget -type]"' % (c, p),
                     'if {[stream get $ch %d %d 1] == 0} {puts "STREAM %d/%d#1 sa=[stream cget -sa] da=[stream cget -da] '
                     'size=[stream cget -framesize] pct=[stream cget -percentPacketRate] dma=[stream cget -dma] '
                     'num=[stream cget -numFrames]"} else {puts "STREAM %d/%d#1 none"}' % (c, p, c, p, c, p)]
        body += counter_body(ports)
    elif a.action == 'counters':
        body += counter_body(ports)
    elif a.action == 'take':
        body += [plist_tcl(ports), 'rc take ixTakeOwnership $pl%s' % (' force' if a.force else '')]
    elif a.action == 'release':
        body += [plist_tcl(ports), 'rc release ixClearOwnership $pl']
    elif a.action == 'reset':
        body += [plist_tcl(ports)]
        body += ['rc factory_%d/%d port setFactoryDefaults $ch %d %d' % (c, p, c, p) for c, p in ports]
        body += ['rc write ixWriteConfigToHardware pl']
    elif a.action in ('clear', 'start', 'stop'):
        cmd = {'clear': 'ixClearStats', 'start': 'ixStartTransmit', 'stop': 'ixStopTransmit'}[a.action]
        body += [plist_tcl(ports), 'rc %s %s pl' % (a.action, cmd)]
    elif a.action == 'burst':
        body += [plist_tcl(ports), 'rc clear ixClearStats pl', 'after 1000', 'rc start ixStartTransmit pl',
                 'after 500', 'rc done ixCheckTransmitDone pl', 'after 2000']
        body += counter_body(ports)
    elif a.action == 'stream':
        if not (a.sa and a.da) or not (a.continuous or a.count):
            ap.error('stream needs --sa, --da and --continuous or --count N')
        c, p = a.port
        body += [plist_tcl([a.port]),
                 'stream setDefault', 'protocol setDefault',
                 'protocol config -name ipV4', 'protocol config -ethernetType ethernetII']
        if a.vlan is not None:
            body += ['protocol config -enable802dot1qTag 1', 'vlan setDefault',
                     'vlan config -vlanID %d' % a.vlan, 'rc vlan_set vlan set $ch %d %d' % (c, p)]
        body += ['ip setDefault',
                 'ip config -sourceIpAddr %s -destIpAddr %s -ipProtocol ipV4ProtocolUdp' % (a.sip, a.dip),
                 'rc ip_set ip set $ch %d %d' % (c, p),
                 'udp setDefault', 'udp config -sourcePort %d -destPort %d' % (a.sport, a.dport),
                 'rc udp_set udp set $ch %d %d' % (c, p),
                 'stream config -enable true -sa %s -da %s -framesize %d -frameSizeType sizeFixed '
                 '-rateMode usePercentRate -percentPacketRate %s -dma %s%s'
                 % (a.sa, a.da, a.size, a.percent, 'contPacket' if a.continuous else 'stopStream',
                    # -numFrames 0 makes `stream set` return 1 (2026-10-21, chassis 82): a continuous
                    # stream leaves numFrames at its default
                    '' if a.continuous else ' -numFrames %d' % a.count),
                 'rc stream_set stream set $ch %d %d %d' % (c, p, a.stream_id),
                 'rc write ixWriteConfigToHardware pl',
                 'if {[stream get $ch %d %d %d] == 0} {puts "STREAM %d/%d#%d sa=[stream cget -sa] da=[stream cget -da] '
                 'size=[stream cget -framesize] pct=[stream cget -percentPacketRate] dma=[stream cget -dma] '
                 'num=[stream cget -numFrames]"}' % (c, p, a.stream_id, c, p, a.stream_id)]
        if a.vlan is not None:
            body += ['if {[vlan get $ch %d %d] == 0} {puts "VLAN %d/%d id=[vlan cget -vlanID]"}' % (c, p, c, p)]
    elif a.action == 'filter':
        c, p = a.port
        zero = '{00 00 00 00 00 00}'
        pal, fil = [], []
        for n, key in ((1, 'uds1'), (2, 'uds2')):
            sa, da = getattr(a, key + '_sa'), getattr(a, key + '_da')
            if sa:
                pal.append('-SA%d %s -SAMask%d %s' % (n, sa, n, zero))
            if da:
                pal.append('-DA%d %s -DAMask%d %s' % (n, da, n, zero))
            if sa or da:
                fil.append('-userDefinedStat%dEnable true -userDefinedStat%dSA %s -userDefinedStat%dDA %s'
                           % (n, n, ('addr%d' % n) if sa else 'anyAddr', n, ('addr%d' % n) if da else 'anyAddr'))
        if not fil:
            ap.error('filter needs at least one --udsN-sa/--udsN-da')
        body += [plist_tcl([a.port]), 'filterPallette setDefault',
                 'filterPallette config %s' % ' '.join(pal),
                 'rc pallette_set filterPallette set $ch %d %d' % (c, p),
                 'filter setDefault', 'filter config %s' % ' '.join(fil),
                 'rc filter_set filter set $ch %d %d' % (c, p),
                 'rc write ixWriteConfigToHardware pl',
                 'filterPallette get $ch %d %d' % (c, p), 'filter get $ch %d %d' % (c, p),
                 'puts "FILTER %d/%d SA1=[filterPallette cget -SA1] DA1=[filterPallette cget -DA1] '
                 'SA2=[filterPallette cget -SA2] DA2=[filterPallette cget -DA2] uds1=[filter cget -userDefinedStat1Enable]'
                 '/[filter cget -userDefinedStat1SA]/[filter cget -userDefinedStat1DA] uds2=[filter cget -userDefinedStat2Enable]'
                 '/[filter cget -userDefinedStat2SA]/[filter cget -userDefinedStat2DA]"' % (c, p)]

    rc, out = run_tcl(a.chassis, login, body, timeout=a.timeout)
    if a.header and a.action in ('counters', 'status', 'burst'):
        print('TSV\t' + TSV_HEADER)
    sys.stdout.write(out)
    if a.tsv:
        rows = [l[4:] for l in out.splitlines() if l.startswith('TSV\t')]
        new = not os.path.exists(a.tsv)
        with open(a.tsv, 'a') as f:
            if new:
                f.write(TSV_HEADER + '\n')
            for r in rows:
                f.write(r + '\n')
    print('IXTCL %s exit=%d' % (a.action, rc))
    sys.exit(1 if rc else 0)


if __name__ == '__main__':
    main()
