#!/usr/bin/env python3
"""bondctl.py up   <bond> <state.json> NIC [NIC ...] [--mode 802.3ad] [--miimon 100] [--lacp-rate fast] [--xmit-hash layer2]
bondctl.py down <bond> <state.json>
bondctl.py status <bond>

Builds (up) or removes (down) a Linux bonding interface from host NICs for a LAG test, and restores
the NICs' addresses exactly. ROOT: every change is an `ip` command; each one is printed before it runs
and the first failure stops the run. It is a root CHANGE on the testbox host, so use it only when the
Test Engineer has allowed the bond for the case (STANDING-ORDERS section 4).

up:   records `ip -br addr` and each NIC's global addresses into <state.json> FIRST, then
      ip link add <bond> type bond mode <mode> miimon <n> lacp_rate <r> xmit_hash_policy <p>
      ip addr flush dev NIC ; ip link set NIC down ; ip link set NIC master <bond>   (per NIC)
      ip link set <bond> up ; ip link set NIC up (per NIC)
      then prints /proc/net/bonding/<bond>.
down: ip link set NIC nomaster (per NIC) ; ip link del <bond> ; ip [-6] addr replace <addr> dev NIC ;
      ip link set NIC up ; then diffs `ip -br addr` against the recorded one. Exit 1 if the diff is not
      empty (printed), 0 if it is: "RESTORE DIFF: empty".
status: prints /proc/net/bonding/<bond> (no change).
"""
import json, os, subprocess, sys, time

def sh(cmd, check=True):
    print('# ' + cmd, flush=True)
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if p.stdout:
        print(p.stdout.rstrip(), flush=True)
    if check and p.returncode != 0:
        raise SystemExit('bondctl: FAILED (%d): %s' % (p.returncode, cmd))
    return p.stdout

def global_addrs(nic):
    out = subprocess.run(['ip', '-o', 'addr', 'show', 'dev', nic, 'scope', 'global'],
                         stdout=subprocess.PIPE, universal_newlines=True).stdout
    found = []
    for line in out.splitlines():
        t = line.split()
        for i, w in enumerate(t):
            if w in ('inet', 'inet6') and i + 1 < len(t):
                found.append((w, t[i + 1]))
    return found

def brief():
    return subprocess.run(['ip', '-br', 'addr'], stdout=subprocess.PIPE, universal_newlines=True).stdout

def opt(a, name, default):
    if name in a:
        i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
    return default

def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ('up', 'down', 'status'):
        sys.stderr.write('usage: ' + __doc__.split('\n\n')[0] + '\n'); sys.exit(2)
    action, bond = a[0], a[1]
    if action == 'status':
        sh('cat /proc/net/bonding/%s' % bond); return
    state = a[2]
    if action == 'up':
        mode = opt(a, '--mode', '802.3ad'); miimon = opt(a, '--miimon', '100')
        rate = opt(a, '--lacp-rate', 'fast'); xmit = opt(a, '--xmit-hash', 'layer2')
        nics = a[3:]
        if not nics:
            raise SystemExit('bondctl: up needs at least one NIC')
        if os.path.exists('/sys/class/net/' + bond):
            raise SystemExit('bondctl: %s already exists; refusing' % bond)
        st = {'bond': bond, 'nics': nics, 'before': brief(), 'addrs': {n: global_addrs(n) for n in nics},
              'when': time.strftime('%Y-%m-%d %H:%M:%S %Z')}
        with open(state, 'w') as f:
            json.dump(st, f, indent=1)
        print('bondctl: recorded %s (%s)' % (state, ', '.join('%s=%s' % (n, ' '.join(x[1] for x in st['addrs'][n])) for n in nics)), flush=True)
        extra = ' lacp_rate %s xmit_hash_policy %s' % (rate, xmit) if mode == '802.3ad' else ''
        sh('ip link add %s type bond mode %s miimon %s%s' % (bond, mode, miimon, extra))
        for n in nics:
            sh('ip addr flush dev %s' % n)
            sh('ip link set %s down' % n)
            sh('ip link set %s master %s' % (n, bond))
        sh('ip link set %s up' % bond)
        for n in nics:
            sh('ip link set %s up' % n)
        time.sleep(3)
        sh('ip -br link show %s' % bond); sh('ip -br addr show %s' % bond)
        sh('cat /proc/net/bonding/%s' % bond)
        return
    # down
    with open(state) as f:
        st = json.load(f)
    if st['bond'] != bond:
        raise SystemExit('bondctl: state file is for %s, not %s' % (st['bond'], bond))
    for n in st['nics']:
        sh('ip link set %s nomaster' % n, check=False)
    sh('ip link del %s' % bond, check=False)
    for n in st['nics']:
        for fam, addr in st['addrs'][n]:
            sh('ip %saddr replace %s dev %s' % ('-6 ' if fam == 'inet6' else '', addr, n))
        sh('ip link set %s up' % n)
    time.sleep(3)
    after = brief()
    import difflib
    d = list(difflib.unified_diff(st['before'].splitlines(), after.splitlines(), 'before', 'after', lineterm=''))
    if d:
        print('RESTORE DIFF (not empty):'); print('\n'.join(d)); sys.exit(1)
    print('RESTORE DIFF: empty'); print(after.rstrip())

if __name__ == '__main__':
    main()
