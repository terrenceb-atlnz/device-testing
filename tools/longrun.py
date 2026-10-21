#!/usr/bin/env python3
"""longrun.py -- the detached long-run sampler: every --every seconds for --hours, read an AW+ console and
(optionally) an IXIA chassis, save every read to one file per sample, and append one summary line per sample.

  longrun.py --hours 12 --every 3600 --console /dev/u2 --baud 115200 --transcript /tmp/<run>/console-u2.log
             --out <dir> [--ixia IP --ixia-login NAME --ports C/P,C/P] [--members 1,2,3,4]
             [--cmd "show ..." ...] [--start-epoch E] [--held-retry 3000] [--detach]

Per sample k = 0 .. hours*3600/every (so 13 samples for 12 h hourly, the first at the start time):
  * waits until start + k*every (an <out>/STOP file ends the run early, cleanly);
  * the console must be FREE (fuser on the device node, plus a /var/lock LCK.. file): if another process holds it,
    retries every 60 s for up to --held-retry s, then writes the sample as SKIPPED (never a silent gap);
  * logs in (console.py: prompt-after-echo, stty -hupcl), runs `show clock`, `show stack`, per member
    `show memory <m>` and `show cpu <m>`, `show interface <ports>` when --dut-ports is given, the --cmd list, and
    the full `show log` -- every command and its full output to <out>/hourly/sample-<kk>-<stamp>.txt;
    then `terminal no monitor` (exec-safe) and CLOSES the console, so it is free between samples;
  * reads the IXIA counters (tools/ixtcl.py, read-only) into the same file and <out>/ixia.tsv;
  * appends one line to <out>/progress.tsv (header written once; columns named there);
  * any error in a read is written to the sample file and the progress line, and the run goes on to the next
    sample -- it never exits early on one bad read.
Writes <out>/DONE (with the last progress line) after the last sample. --detach: setsid + double fork, stdio to
<out>/sampler.out, PID to <out>/sampler.pid, prints `DETACHED pid=<pid>` and returns at once.
Stop it with `tools/tb killmine <box> <pid>` (it runs as python3 from /tmp/<x>/tools/) or touch <out>/STOP.
"""
import argparse, os, re, subprocess, sys, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ESC = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[78()=>]|\x1b\][^\x07]*\x07")
CPU = re.compile(r"1 second:\s*(\d+)%,\s*20 seconds:\s*(\d+)%,\s*60 seconds:\s*(\d+)%")
MEM = re.compile(r"RAM total:\s*(\d+) kB; free:\s*(\d+) kB")
STACKROW = re.compile(r"^\s*(\d+)\s+\S+\s+[0-9a-f.]{14}\s+(\d+)\s+(\S+(?: \S+)?)\s{2,}(.+?)\s*$", re.M)
OPSTAT = re.compile(r"Operational Status\s+(.+?)\s*$", re.M)


def log(msg):
    print('%s %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg), flush=True)


def held(tty):
    """Return a reason string if another process holds the console, else ''."""
    real = os.path.realpath(tty)
    for cmd in (['sudo', '-n', 'fuser', real], ['fuser', real]):
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20)
        except Exception:
            continue
        pids = r.stdout.decode().split()
        if pids:
            return 'held by pid(s) %s' % ','.join(pids)
        if r.returncode in (0, 1):   # fuser ran: 1 = nobody holds it
            break
    lck = '/var/lock/LCK..' + os.path.basename(real)
    if os.path.exists(lck):
        return 'lock file %s' % lck
    return ''


def detach(out):
    if os.fork():
        # parent: wait for the pid file and report it
        for _ in range(50):
            p = os.path.join(out, 'sampler.pid')
            if os.path.exists(p):
                print('DETACHED pid=%s out=%s' % (open(p).read().strip(), out)); sys.stdout.flush()
                os._exit(0)
            time.sleep(0.1)
        print('DETACHED (pid file not seen yet) out=%s' % out); os._exit(0)
    os.setsid()
    if os.fork():
        os._exit(0)
    fd = os.open(os.path.join(out, 'sampler.out'), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    nul = os.open(os.devnull, os.O_RDONLY)
    os.dup2(nul, 0); os.dup2(fd, 1); os.dup2(fd, 2)
    with open(os.path.join(out, 'sampler.pid'), 'w') as f:
        f.write('%d\n' % os.getpid())


def console_sample(a, f):
    """Run the console reads; write them to f; return a dict of parsed values."""
    import console
    v = {'stack': '?', 'ready': '?', 'master': '?', 'mem': {}, 'cpu': {}, 'loglines': '?', 'errs': 0}
    c = console.Console(a.console, a.transcript, baud=a.baud)
    try:
        if not c.login(monitor=False):
            raise RuntimeError('no privileged prompt')
        cmds = ['show clock', 'show stack']
        for m in a.members:
            cmds += ['show memory %s' % m, 'show cpu %s' % m]
        if a.dut_ports:
            cmds.append('show interface %s' % a.dut_ports)
        cmds += a.cmd + ['show log']
        for cmd in cmds:
            t0 = time.time()
            out = ESC.sub('', c.cmd(cmd, timeout=a.cmd_timeout))
            f.write('%s >>> %s\n%s\n' % (time.strftime('%H:%M:%S', time.localtime(t0)), cmd, out)); f.flush()
            if any(l.startswith('% ') for l in out.splitlines()):
                v['errs'] += 1
            if cmd == 'show stack':
                m = OPSTAT.search(out)
                v['stack'] = m.group(1) if m else '?'
                rows = STACKROW.findall(out)
                v['ready'] = '%d/%d' % (sum(1 for r in rows if r[2] == 'Ready'), len(rows))
                v['master'] = ','.join(r[0] for r in rows if 'Master' in r[3]) or '?'
            elif cmd.startswith('show memory '):
                m = MEM.search(out)
                v['mem'][cmd.split()[-1]] = m.group(2) if m else '?'
            elif cmd.startswith('show cpu '):
                m = CPU.search(out)
                v['cpu'][cmd.split()[-1]] = '/'.join(m.groups()) if m else '?'
            elif cmd == 'show log':
                v['loglines'] = str(sum(1 for l in out.splitlines() if re.match(r'^\d{4} \w{3} ', l)))
        try:
            c.monitor_off()
        except Exception:
            pass
    finally:
        c.close()
    return v


def ixia_sample(a, f):
    import ixtcl
    ports = [ixtcl.port(x) for x in a.ports.split(',')]
    rc, rows, raw = ixtcl.counters(a.ixia, a.ixia_login, ports)
    f.write('%s >>> ixtcl counters %s (exit %d)\nTSV\t%s\n%s\n' % (time.strftime('%H:%M:%S'), a.ports, rc,
                                                                   ixtcl.TSV_HEADER, raw)); f.flush()
    tsv = os.path.join(a.out, 'ixia.tsv')
    new = not os.path.exists(tsv)
    with open(tsv, 'a') as t:
        if new:
            t.write(ixtcl.TSV_HEADER + '\n')
        for line in raw.splitlines():
            if line.startswith('TSV\t'):
                t.write(line[4:] + '\n')
    return rc, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--hours', type=float, required=True)
    ap.add_argument('--every', type=int, default=3600)
    ap.add_argument('--console', required=True)
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--transcript', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--members', default='', help='stack member ids for per-member show memory/cpu, e.g. 1,2,3,4')
    ap.add_argument('--dut-ports', default='', help='e.g. port3.0.25,port4.0.25 (read with show interface)')
    ap.add_argument('--cmd', action='append', default=[])
    ap.add_argument('--ixia'); ap.add_argument('--ixia-login'); ap.add_argument('--ports')
    ap.add_argument('--start-epoch', type=float, default=None)
    ap.add_argument('--held-retry', type=int, default=3000)
    ap.add_argument('--cmd-timeout', type=float, default=120.0)
    ap.add_argument('--detach', action='store_true')
    a = ap.parse_args()
    a.members = [m for m in a.members.split(',') if m]
    a.out = os.path.abspath(a.out)
    os.makedirs(os.path.join(a.out, 'hourly'), exist_ok=True)
    if a.ixia and not a.ports:
        ap.error('--ixia needs --ports')
    if a.detach:
        detach(a.out)
    start = a.start_epoch or time.time()
    n = int(round(a.hours * 3600 / a.every))
    log('longrun start pid=%d start=%s samples=%d every=%ds console=%s ixia=%s ports=%s out=%s' % (
        os.getpid(), time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)), n + 1, a.every, a.console,
        a.ixia, a.ports, a.out))
    prog = os.path.join(a.out, 'progress.tsv')
    cols = (['k', 'target', 'time', 'console', 'stack', 'ready', 'master'] +
            ['memfree_m%s' % m for m in a.members] + ['cpu_m%s(1s/20s/60s)' % m for m in a.members] +
            ['loglines', 'pct_lines', 'ixia'])
    if a.ixia:
        for p in a.ports.split(','):
            cols += ['%s_%s' % (p, k) for k in ('link', 'sent', 'rcvd', 'uds1', 'uds2', 'fcs', 'txfps', 'uds1fps')]
    if not os.path.exists(prog):
        with open(prog, 'w') as f:
            f.write('\t'.join(cols) + '\n')
    last = ''
    for k in range(n + 1):
        target = start + k * a.every
        while time.time() < target:
            if os.path.exists(os.path.join(a.out, 'STOP')):
                log('STOP file seen; ending before sample %d' % k)
                with open(os.path.join(a.out, 'DONE'), 'w') as f:
                    f.write('STOPPED before sample %d at %s\n%s\n' % (k, time.strftime('%Y-%m-%d %H:%M:%S'), last))
                return
            time.sleep(min(30, max(0.5, target - time.time())))
        stamp = time.strftime('%Y%m%dT%H%M%S')
        fn = os.path.join(a.out, 'hourly', 'sample-%02d-%s.txt' % (k, stamp))
        row = {'k': str(k), 'target': time.strftime('%H:%M:%S', time.localtime(target)),
               'time': time.strftime('%Y-%m-%d %H:%M:%S')}
        with open(fn, 'w') as f:
            f.write('# longrun sample %d of %d, target %s, taken %s, console %s\n' % (
                k, n, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(target)), row['time'], a.console))
            # console part (held -> retry every 60 s up to held_retry)
            waited, why = 0, held(a.console)
            while why and waited < a.held_retry:
                f.write('# console %s %s; retry in 60 s (waited %d s)\n' % (a.console, why, waited)); f.flush()
                time.sleep(60); waited += 60
                why = held(a.console)
            if why:
                row['console'] = 'SKIPPED(%s)' % why
                f.write('# SKIPPED console part: %s after %d s\n' % (why, waited))
                v = None
            else:
                try:
                    v = console_sample(a, f)
                    row['console'] = 'ok' + ('(waited %ds)' % waited if waited else '')
                except Exception as e:
                    row['console'] = 'ERR(%s)' % str(e).replace('\t', ' ')[:80]
                    f.write('# console ERROR\n%s\n' % traceback.format_exc())
                    v = None
            if v:
                row.update({'stack': v['stack'], 'ready': v['ready'], 'master': v['master'],
                            'loglines': v['loglines'], 'pct_lines': str(v['errs'])})
                for m in a.members:
                    row['memfree_m%s' % m] = v['mem'].get(m, '?')
                    row['cpu_m%s(1s/20s/60s)' % m] = v['cpu'].get(m, '?')
            # IXIA part
            if a.ixia:
                try:
                    rc, rows = ixia_sample(a, f)
                    row['ixia'] = 'ok' if rc == 0 else 'rc%d' % rc
                    for r in rows:
                        p = r.get('port')
                        for k2, src in (('link', 'link'), ('sent', 'framesSent'), ('rcvd', 'framesReceived'),
                                        ('uds1', 'userDefinedStat1'), ('uds2', 'userDefinedStat2'),
                                        ('fcs', 'fcsErrors'), ('txfps', 'rate_framesSent'),
                                        ('uds1fps', 'rate_userDefinedStat1')):
                            row['%s_%s' % (p, k2)] = r.get(src, '?')
                except Exception as e:
                    row['ixia'] = 'ERR(%s)' % str(e)[:60]
                    f.write('# ixia ERROR\n%s\n' % traceback.format_exc())
        last = '\t'.join(row.get(c, '-') for c in cols)
        with open(prog, 'a') as p:
            p.write(last + '\n')
        log('sample %d written: %s' % (k, fn))
    with open(os.path.join(a.out, 'DONE'), 'w') as f:
        f.write('DONE %d samples at %s\n%s\n%s\n' % (n + 1, time.strftime('%Y-%m-%d %H:%M:%S'), '\t'.join(cols), last))
    log('longrun DONE')


if __name__ == '__main__':
    main()
