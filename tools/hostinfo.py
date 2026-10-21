#!/usr/bin/env python3
"""hostinfo.py [NIC ...]
Read-only inventory of a testbox HOST for a traffic or bonding case: who manages the NICs
(NetworkManager / networkd / ifupdown), their addresses and link details, any bonding
interfaces already present, the bonding module, and the traffic tool versions (tcpreplay,
tcpdump, scapy). It changes nothing and needs no root; the one `sudo -n true` call only
reports whether passwordless sudo is available to the caller (a bond cannot be built
without it). Run it ON the box. Output is plain text, one section per probe; a probe whose
command is missing prints `<name>: not found` instead of failing the run."""
import os, subprocess, sys


def sh(cmd):
    try:
        p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=30, universal_newlines=True)
        return p.returncode, p.stdout.strip()
    except subprocess.TimeoutExpired:
        return 124, '(timed out)'


def section(title, cmd):
    print('=== %s  [%s]' % (title, cmd))
    rc, out = sh(cmd)
    print(out if out else '(no output, rc=%d)' % rc)
    print()


def main(argv=None):
    nics = (argv if argv is not None else sys.argv[1:]) or []
    if '--stats' in nics:                                   # 2026-10-21: NIC drop/miss counters only
        nics.remove('--stats')
        for n in nics:
            section('ip -s -s link show ' + n, 'ip -s -s link show ' + n)
            section('ethtool -S ' + n + ' (drop/miss/err/fifo/no_buffer)',
                    'ethtool -S %s 2>&1 | grep -E -i "drop|miss|err|fifo|no_buffer|rx_packets|tx_packets" || echo "ethtool: not found"' % n)
        return
    section('host', 'hostname; uname -r; cat /etc/os-release 2>/dev/null | head -2')
    section('python', 'for p in python3 python3.8; do command -v $p >/dev/null && $p -V; done')
    section('NetworkManager', 'systemctl is-active NetworkManager 2>&1; nmcli -t dev status 2>&1 || echo "nmcli: not found"')
    section('NetworkManager connections', 'nmcli -t con show 2>&1 || echo "nmcli: not found"')
    section('systemd-networkd', 'systemctl is-active systemd-networkd 2>&1; ls /etc/systemd/network/ 2>/dev/null')
    section('ifupdown', 'grep -v "^\\s*#" /etc/network/interfaces 2>/dev/null; ls /etc/network/interfaces.d/ 2>/dev/null')
    section('netplan', 'ls /etc/netplan/ 2>/dev/null; cat /etc/netplan/*.yaml 2>/dev/null')
    section('ip -br addr', 'ip -br addr')
    section('ip -br link', 'ip -br link')
    for n in nics:
        section('ip -d link show ' + n, 'ip -d link show ' + n)
        section('ethtool ' + n, 'ethtool %s 2>&1 | grep -E "Speed|Duplex|Auto-neg|Link detected" || echo "ethtool: not found"' % n)
        section('ethtool -i ' + n, 'ethtool -i %s 2>&1 | grep -E "^driver|^version" || echo "ethtool: not found"' % n)
        section('ip route for ' + n, 'ip route show dev %s; ip -6 route show dev %s | grep -v fe80' % (n, n))
    section('bonding interfaces', 'ls /proc/net/bonding/ 2>/dev/null && cat /proc/net/bonding/* 2>/dev/null || echo "none"')
    section('bonding module', 'modinfo bonding 2>&1 | head -3; lsmod | grep -w bonding || echo "bonding: not loaded"')
    section('sudo -n', 'sudo -n true 2>&1 && echo "sudo -n: OK" || echo "sudo -n: NOT available"')
    section('tcpreplay', 'tcpreplay -V 2>&1 | grep -i "version" | head -1 || echo "tcpreplay: not found"')
    section('tcpdump', 'ls -l /usr/sbin/tcpdump /usr/bin/tcpdump 2>/dev/null || echo "tcpdump: not found"')
    section('memory and /tmp', 'free -m | head -2; df -h /tmp | tail -1; nproc')
    section('scapy', 'for p in python3 python3.8; do command -v $p >/dev/null && echo -n "$p: " && $p -c "import scapy; print(scapy.__version__)" 2>&1 | tail -1; done')
    section('iproute2', 'ip -V')
    return 0


if __name__ == '__main__':
    sys.exit(main())
