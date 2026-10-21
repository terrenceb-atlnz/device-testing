#!/usr/bin/env python3
"""eventwin.py -- one traffic EVENT WINDOW in one call: start the flows, fire timed console actions,
take timed reads, poll until the DUT is ready again, then analyse. Built 2026-10-21 from T17584
(tb101), where each of 6 events took 15-20 hand-made tool calls.

Run it ON the testbox, as the normal user, from a scratch copy of tools/ (`tools/tb scratch`):
    tools/tb tool <TB> <scratch> eventwin --out /tmp/<scratch>/e3 --nic-a bond0 --nic-b eth2 ...
It starts the root traffic tools itself with `sudo -n` (l2flows.py, linerate.py). Console tools
(cfg, ckcon, ckyn, reloadc, ckreload, listen) run as the user, write their transcript to
/tmp/<scratch>/console-<uN>.log (what the sentinel watches), use one console at a time per console
(a lock), and refuse a console that another process holds (fuser, as tools/tb does).

  --out DIR            results go here (a /tmp path: root writes the flow files). Must not exist yet.
  --nic-a / --nic-b    the two host NICs of l2flows.py and linerate.py (A -> B is direction A).
  --flows-secs S       l2flows duration (default 360); --pps (default 100); --per-link N (default 1;
                       use 2 x the LAG links when a host bond is one side: see l2flows.py).
  --rate MBPS          also run linerate both ways at this rate (`top` = as fast as possible) for
                       --rate-secs (default 300), starting 2 s after the flows. Needs --a-dst-mac
                       and --b-dst-mac; --a-src-ip / --b-src-ip when a NIC has no IPv4 (a bond);
                       --src-macs (default 16). Directions use UDP sport 5010 (A) and 5011 (B).
  --act AT TOOL uN [ARG ...]   at AT s after the flows start, run TOOL on console uN with ARGs, e.g.
                       --act 25 cfg u0 "configure terminal" "interface port1.0.1" "shutdown" "end"
                       --act 25 reloadc u1 240 /tmp/s/e3.done reload stack-member 1
                       --act 20 listen u0 330 /tmp/s/e3-u0.done
                       Every act except `listen` is an EVENT: its time is ev0, ev1 ... in flowstat.
                       The event time is the tool's own: reloadc's `EVENT y-sent`, else the header
                       of the last command that is not `end`/`exit`/`configure terminal`.
  --read AT uN CMD ... at AT s, run these show commands through ckcon (saved per read).
  --bond BOND          also save /proc/net/bonding/BOND at every --read time and at the end.
  --poll uN SECS REGEX CMD   after the last act: ckcon `@poll` until REGEX (no spaces) matches CMD.
  --after uN CMD ...   show commands after the poll (repeatable).
  --stats-nics a,b,c   host NICs for `hostinfo.py --stats` before and after (default nic-a,nic-b).
  --baud               console rate (default 115200).
  --save DIR           copy every text result (not the raw flow files) into DIR at the end. Use one
                       folder per event, e.g. ~/claude/device-testing/<group>/<id>/work/e3 on the NFS
                       home, so the final log can quote every read verbatim.
  --dry-run            print the plan with every command, run nothing.

Writes in --out: plan.txt, act<N>-<tool>-<uN>.out, read-<AT>-<uN>.out, bond-<AT>.txt, poll.out,
after<N>-<uN>.out, l2flows.out, linerate-a.out, linerate-b.out, hoststats-before/after.txt,
flowstat.txt, loopwin.txt, summary.txt (also printed). Exit 0 = every step ran; 1 = a step failed
(a held console, a tool error, a `% ` CLI error or `!!!` line), see summary.txt; 2 = usage error.
"""
import argparse, datetime, os, re, shutil, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.dirname(HERE)
PY = sys.executable
CON_TOOLS = ('cfg', 'ckcon', 'ckyn', 'reloadc', 'ckreload', 'listen')
CON_RE = re.compile(r'^u\d+$')
HDR = re.compile(r'^(?:(\d+\.\d+) )?(\d\d:\d\d:\d\d) >>> (.*?)\s*$')
NOT_EVENT = ('end', 'exit', 'configure terminal', 'conf t')
OK_PCT = ('% Comparing', '% Results are identical')


def parse(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True)
    ap.add_argument('--nic-a', required=True); ap.add_argument('--nic-b', required=True)
    ap.add_argument('--flows-secs', type=float, default=360); ap.add_argument('--pps', type=int, default=100)
    ap.add_argument('--per-link', type=int, default=1)
    ap.add_argument('--rate'); ap.add_argument('--rate-secs', type=float, default=300)
    ap.add_argument('--a-dst-mac'); ap.add_argument('--b-dst-mac')
    ap.add_argument('--a-src-ip'); ap.add_argument('--b-src-ip')
    ap.add_argument('--src-macs', type=int, default=16)
    ap.add_argument('--act', nargs='+', action='append', default=[], metavar='AT TOOL uN ARG')
    ap.add_argument('--read', nargs='+', action='append', default=[], metavar='AT uN CMD')
    ap.add_argument('--bond')
    ap.add_argument('--poll', nargs=4, metavar=('uN', 'SECS', 'REGEX', 'CMD'))
    ap.add_argument('--after', nargs='+', action='append', default=[], metavar='uN CMD')
    ap.add_argument('--stats-nics')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--save')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)
    if a.rate and not (a.a_dst_mac and a.b_dst_mac):
        ap.error('--rate needs --a-dst-mac and --b-dst-mac')
    acts = []
    for x in a.act:
        if len(x) < 3 or x[1] not in CON_TOOLS or not CON_RE.match(x[2]):
            ap.error('--act AT TOOL uN [ARG ...]; TOOL in %s, got %r' % (', '.join(CON_TOOLS), x))
        acts.append((float(x[0]), x[1], x[2], x[3:]))
    reads = []
    for x in a.read:
        if len(x) < 3 or not CON_RE.match(x[1]):
            ap.error('--read AT uN CMD ...; got %r' % (x,))
        reads.append((float(x[0]), x[1], x[2:]))
    after = []
    for x in a.after:
        if len(x) < 2 or not CON_RE.match(x[0]):
            ap.error('--after uN CMD ...; got %r' % (x,))
        after.append((x[0], x[1:]))
    if a.poll and (not CON_RE.match(a.poll[0]) or ' ' in a.poll[2]):
        ap.error('--poll uN SECS REGEX CMD (REGEX without spaces)')
    last = max([t for t, *_ in acts] + [t for t, *_ in reads] + [0])
    if last >= a.flows_secs:
        ap.error('an act or read at %.0f s is after the flows end (%.0f s)' % (last, a.flows_secs))
    return a, sorted(acts, key=lambda x: x[0]), sorted(reads, key=lambda x: x[0]), after


class Run:
    def __init__(self, a, out):
        self.a, self.out = a, out
        self.locks = {}
        self.problems = []
        self.events = []                      # (epoch, label)
        self.mu = threading.Lock()
        self.sudo_ok = subprocess.call(['sudo', '-n', 'true'], stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL) == 0 if not a.dry_run else True

    def note(self, msg):
        with self.mu:
            self.problems.append(msg)

    def lock(self, con):
        with self.mu:
            return self.locks.setdefault(con, threading.Lock())

    def holders(self, con):
        dev = os.path.realpath('/dev/' + con)
        if not os.path.exists(dev):
            return ['(no %s)' % dev]
        cmd = (['sudo', '-n'] if self.sudo_ok else []) + ['fuser', dev]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
        return p.stdout.split()

    def console(self, tool, con, args, outfile):
        """Run one console tool; returns its stdout text ('' on refusal)."""
        argv = [PY, os.path.join(HERE, tool + '.py'), '/dev/' + con, str(self.a.baud),
                os.path.join(SCRATCH, 'console-%s.log' % con)] + list(args)
        with self.lock(con):
            held = self.holders(con)
            if held:
                msg = '%s: /dev/%s is held by %s -- not opened' % (os.path.basename(outfile), con, ' '.join(held))
                self.note(msg); open(outfile, 'w').write(msg + '\n')
                return ''
            p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        text = p.stdout
        open(outfile, 'w').write(text + '\nexit=%d\n' % p.returncode)
        if p.returncode:
            self.note('%s: %s exit %d' % (os.path.basename(outfile), tool, p.returncode))
        for line in text.splitlines():
            s = line.strip()
            if s.startswith('!!!') or (s.startswith('% ') and not s.startswith(OK_PCT)):
                self.note('%s: %s' % (os.path.basename(outfile), s[:120]))
        return text


def hhmmss_epoch(hms, near):
    """Epoch of HH:MM:SS (local) closest to `near` (handles a midnight crossing)."""
    d = datetime.datetime.fromtimestamp(near)
    best = None
    for day in (-1, 0, 1):
        t = datetime.datetime.combine((d + datetime.timedelta(days=day)).date(),
                                      datetime.datetime.strptime(hms, '%H:%M:%S').time()).timestamp()
        if best is None or abs(t - near) < abs(best - near):
            best = t
    return best


def event_epoch(tool, text, launched):
    m = re.search(r'EVENT y-sent (\d+\.\d+)', text)
    if m:
        return float(m.group(1))
    when = None
    for line in text.splitlines():
        h = HDR.match(line)
        if h and h.group(3).lower() not in NOT_EVENT:
            when = float(h.group(1)) if h.group(1) else hhmmss_epoch(h.group(2), launched)
    return when if when is not None else launched


def wait_until(t):
    while True:
        d = t - time.time()
        if d <= 0:
            return
        time.sleep(min(d, 1.0))


def main(argv=None):
    a, acts, reads, after = parse(argv)
    out = os.path.abspath(a.out)
    flows = os.path.join(out, 'flows')
    stats_nics = (a.stats_nics or '%s,%s' % (a.nic_a, a.nic_b)).split(',')
    lf = [PY, os.path.join(HERE, 'l2flows.py'), str(a.flows_secs), str(a.pps), flows, a.nic_a, a.nic_b]
    if a.per_link > 1:
        lf += ['--per-link', str(a.per_link)]
    lr = []
    if a.rate:
        for tx, rx, dst, sip, sport, pre in ((a.nic_a, a.nic_b, a.a_dst_mac, a.a_src_ip, 5010, '02:cc:0a:00'),
                                             (a.nic_b, a.nic_a, a.b_dst_mac, a.b_src_ip, 5011, '02:cc:0b:00')):
            c = [PY, os.path.join(HERE, 'linerate.py'), '--tx', tx, '--dst-mac', dst, '--rx', rx,
                 '--sport', str(sport), '--src-macs', str(a.src_macs), '--mac-prefix', pre,
                 '--rate', a.rate, '--secs', str(a.rate_secs)]
            if sip:
                c += ['--src-ip', sip]
            lr.append(c)
    plan = ['eventwin plan (times are seconds after the flows start)',
            '  +0     sudo -n ' + ' '.join(lf)]
    for i, c in enumerate(lr):
        plan.append('  +2     sudo -n ' + ' '.join(c) + '   > linerate-%s.out' % 'ab'[i])
    for t, tool, con, args in acts:
        plan.append('  +%-5.0f %s %s %s%s' % (t, tool, con, ' '.join(repr(x) for x in args),
                                             '' if tool == 'listen' else '   [EVENT]'))
    for t, con, cmds in reads:
        plan.append('  +%-5.0f read %s: %s%s' % (t, con, ' | '.join(cmds), ('  + bond %s' % a.bond) if a.bond else ''))
    if a.poll:
        plan.append('  then   poll %s: @poll %s %s %s' % tuple(a.poll))
    for con, cmds in after:
        plan.append('  then   after %s: %s' % (con, ' | '.join(cmds)))
    plan.append('  end    flowstat + loopwin (events = the acts marked EVENT), hostinfo --stats %s'
                % ','.join(stats_nics))
    if a.save:
        plan.append('  save   text results -> %s' % a.save)
    if a.dry_run:
        print('\n'.join(plan))
        return 0
    if os.path.exists(out):
        print('eventwin: %s already exists; use a new --out per event' % out, file=sys.stderr)
        return 2
    os.makedirs(out)
    open(os.path.join(out, 'plan.txt'), 'w').write('\n'.join(plan) + '\n')
    run = Run(a, out)

    def hoststats(name):
        p = subprocess.run([PY, os.path.join(HERE, 'hostinfo.py'), '--stats'] + stats_nics,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        open(os.path.join(out, name), 'w').write(p.stdout)

    def bond(tag):
        if a.bond:
            try:
                shutil.copyfile('/proc/net/bonding/' + a.bond, os.path.join(out, 'bond-%s.txt' % tag))
            except OSError as e:
                run.note('bond-%s: %s' % (tag, e))

    hoststats('hoststats-before.txt')
    launched = time.time()
    flows_p = subprocess.Popen(['sudo', '-n'] + lf, stdout=open(os.path.join(out, 'l2flows.out'), 'w'),
                               stderr=subprocess.STDOUT)
    start_file = os.path.join(flows, 'START')
    while not os.path.exists(start_file) and time.time() - launched < 15:
        time.sleep(0.1)
    try:
        t0 = float(open(start_file).read())
    except (OSError, ValueError):
        t0 = launched + 1.0
        run.note('l2flows START file not seen; times use launch + 1 s')
    lr_p = []
    if lr:
        wait_until(t0 + 2)
        for i, c in enumerate(lr):
            lr_p.append(subprocess.Popen(['sudo', '-n'] + c, stdout=open(os.path.join(out, 'linerate-%s.out' % 'ab'[i]), 'w'),
                                         stderr=subprocess.STDOUT))

    def do_act(i, t, tool, con, args):
        wait_until(t0 + t)
        st = time.time()
        text = run.console(tool, con, args, os.path.join(out, 'act%d-%s-%s.out' % (i, tool, con)))
        if tool != 'listen' and text:
            ev = event_epoch(tool, text, st)
            with run.mu:
                run.events.append((ev, 'act%d %s %s %s' % (i, tool, con, ' '.join(args)[:60])))

    def do_read(t, con, cmds):
        wait_until(t0 + t)
        bond('%.0f' % t)
        run.console('ckcon', con, cmds, os.path.join(out, 'read-%.0f-%s.out' % (t, con)))

    threads = [threading.Thread(target=do_act, args=(i, *x)) for i, x in enumerate(acts, 1)]
    threads += [threading.Thread(target=do_read, args=x) for x in reads]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    if a.poll:
        con, secs, rx, cmd = a.poll
        run.console('ckcon', con, ['@poll %s %s %s' % (secs, rx, cmd)], os.path.join(out, 'poll.out'))
    for i, (con, cmds) in enumerate(after, 1):
        run.console('ckcon', con, cmds, os.path.join(out, 'after%d-%s.out' % (i, con)))
    bond('end')
    flows_p.wait()
    for p in lr_p:
        p.wait()
    hoststats('hoststats-after.txt')

    events = sorted(run.events)
    fs = subprocess.run([PY, os.path.join(HERE, 'flowstat.py'), flows, a.nic_a, a.nic_b] + ['%.3f' % e for e, _ in events],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True).stdout
    lw = subprocess.run([PY, os.path.join(HERE, 'loopwin.py'), flows, a.nic_a, a.nic_b],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True).stdout
    open(os.path.join(out, 'flowstat.txt'), 'w').write(fs)
    open(os.path.join(out, 'loopwin.txt'), 'w').write(lw)

    S = ['eventwin summary -- %s' % out, 'flows start %.3f (%s)' % (t0, time.strftime('%H:%M:%S', time.localtime(t0)))]
    for k, (e, label) in enumerate(events):
        S.append('ev%d %.3f %s  +%.1f s  %s' % (k, e, time.strftime('%H:%M:%S', time.localtime(e)), e - t0, label))
    S.append('-- flows (lost / dups / longest outage; full detail in flowstat.txt)')
    for line in fs.splitlines():
        if re.match(r'^\S+ (sent=|ALL )', line) or 'LONGEST' in line:
            S.append('  ' + line.strip())
    S.append('-- loopwin: ' + ' / '.join(l.strip() for l in lw.splitlines()[-2:]))
    for i, _ in enumerate(lr_p):
        try:
            for line in open(os.path.join(out, 'linerate-%s.out' % 'ab'[i])):
                if re.match(r'^\s+(sent|rx) ', line):
                    S.append('-- linerate %s: %s' % ('AB'[i], line.strip()))
        except OSError:
            pass
    S.append('-- problems: none' if not run.problems else '-- problems:')
    S += ['  ' + p for p in run.problems]
    text = '\n'.join(S) + '\n'
    open(os.path.join(out, 'summary.txt'), 'w').write(text)
    print(text, end='')
    if a.save:
        os.makedirs(a.save, exist_ok=True)
        for name in sorted(os.listdir(out)):
            src = os.path.join(out, name)
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(a.save, name))
    return 1 if run.problems else 0


if __name__ == '__main__':
    sys.exit(main())
