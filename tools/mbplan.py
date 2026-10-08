#!/usr/bin/env python3
"""mbplan.py -- run a Modbus/TCP test plan and grade every line against its expected result.

A plan is a text file, one action per line, run top to bottom. The runner prints ONE summary
row per line (PASS / FAIL / INFO / ERROR, what came back) and writes everything else -- the raw
TX/RX bytes, the full CLI output -- to the --log and --out files. Grading is a comparison against
the plan, not a reading of raw output, and the context only takes the summary.

  mbplan.py --host H [--port 502] [--console /dev/uN --baud B --transcript F]
            [--log mb.log] [--out plan.out] [--var NAME=VALUE ...] PLAN

Plan lines (a line starting `#`, or ` # ` mid-line, is a comment; `${NAME}` is replaced from --var):
  step <label...>                         start a step: rows after it are graded under <label>
  read  <unit> <addr> <count> <type> <expect> [desc]
  write <unit> <addr> <value> <expect> [desc]
  probe <tcp-port> ok|refused             TCP connect only (port-change and disable tests)
  cli   <cmd> [;; <cmd> ...] [=~ <regex>] run on --console through ckcon.py, all commands in one
                                          session (so `configure terminal ;; ... ;; end` works);
                                          with =~ the regex must match somewhere in the output
  log   <regex>                           `show log | include <regex>` on --console; must match
  sleep <seconds>
  port  <tcp-port>                        Modbus TCP port for the lines after it (default --port)

<unit>: stack member id (0 = the system block / the master's per-member block).
<addr>: a number (0x3001), or @<port>[+<offset>] -- the port-register block, 13 words per port
        from 0x5000, ports in order per member: @1.0.2 = unit 1, 0x500d; @3.0.13+1 = unit 3, 0x509d.
        With @, <unit> may be `-` (taken from the port).
<type>: UINT ASCII HEX ENUM FLOAT BOOL RAW (as tools/mb.py).
<expect> for read: the decoded value as mb.py prints it (5, 'IE520-stk' without quotes, 0000,
        True), `~` to record without grading, `>N` / `<N` for numbers, `exc` or `exc:N` for an
        exception (N = the Modbus exception code).
<expect> for write: `ok` (FC06 echo) or `exc` / `exc:N`.

Exit 0 = every graded line PASSed, 1 = a FAIL, 2 = an ERROR (no connection, CLI failure).
Needs pymodbus 3.x (tb470 has 3.8.6) and, for cli/log lines, ckcon.py + console.py beside it.
"""
import argparse
import os
import re
import shlex
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mb import decode, exc_text  # noqa: E402  (same directory, tools/)

PORT_BASE, PORT_WORDS = 0x5000, 13


def port_addr(tok):
    """@M.0.N[+k] -> (unit M, 0x5000 + 13*(N-1) + k)."""
    m = re.fullmatch(r'@(\d+)\.0\.(\d+)(?:\+(\d+))?', tok)
    if not m:
        raise ValueError('bad port address %r (want @<member>.0.<port>[+offset])' % tok)
    member, port, off = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    return member, PORT_BASE + PORT_WORDS * (port - 1) + off


class Runner:
    def __init__(self, a):
        self.a = a
        self.log = open(a.log, 'a', buffering=1)
        self.out = open(a.out, 'a', buffering=1)
        self.step = '-'
        self.mbport = a.port
        self.rows = []
        self.worst = 0

    # -- output ---------------------------------------------------------------------------
    def trace(self, s):
        line = '%s %s' % (time.strftime('%H:%M:%S'), s)
        self.log.write(line + '\n')
        self.out.write(line + '\n')

    def row(self, verdict, n, what, got):
        self.rows.append((self.step, verdict))
        if verdict == 'FAIL':
            self.worst = max(self.worst, 1)
        if verdict == 'ERROR':
            self.worst = 2
        line = '%-5s L%-3d %-60s -> %s' % (verdict, n, what[:60], got)
        print(line, flush=True)
        self.out.write(line + '\n')

    # -- modbus ---------------------------------------------------------------------------
    def client(self, port=None):
        from pymodbus.client import ModbusTcpClient
        pkts = []

        def tr(sending, data):
            pkts.append(('TX' if sending else 'RX', data.hex(' ')))
            return data
        c = ModbusTcpClient(self.a.host, port=port or self.mbport, timeout=self.a.timeout,
                            retries=0, trace_packet=tr)
        return c, pkts

    def modbus(self, n, op, unit, addr, arg, typ, expect, desc):
        c, pkts = self.client()
        what = '%s u%d 0x%04x %s %s' % (op, unit, addr, arg if op == 'write' else 'x%s %s' % (arg, typ), desc)
        if not c.connect():
            self.trace('CONNECT %s:%d -> FAILED' % (self.a.host, self.mbport))
            return self.row('ERROR', n, what, 'no TCP connection')
        try:
            if op == 'read':
                rsp = c.read_holding_registers(addr, count=int(arg), slave=unit)
            else:
                rsp = c.write_register(addr, int(arg, 0), slave=unit)
        except Exception as e:                       # no response / timeout
            c.close()
            return self.row('ERROR', n, what, 'no response: %s' % e)
        c.close()
        for d, h in pkts:
            self.trace('  %s %s' % (d, h))
        if rsp.isError():
            got = 'EXCEPTION ' + exc_text(rsp, pkts)
            code = re.search(r'code=(\d+)', got).group(1)
            self.trace('%s -> %s' % (what, got))
            if expect.startswith('exc'):
                ok = expect == 'exc' or expect == 'exc:%s' % code
                return self.row('PASS' if ok else 'FAIL', n, what, got)
            return self.row('INFO' if expect == '~' else 'FAIL', n, what, got)
        if op == 'write':
            got = 'ok (echo 0x%04x)' % (rsp.registers[0] if rsp.registers else -1)
            self.trace('%s -> %s' % (what, got))
            return self.row('PASS' if expect == 'ok' else ('INFO' if expect == '~' else 'FAIL'), n, what, got)
        regs = rsp.registers
        val = decode(regs, typ.upper())
        shown = val if not isinstance(val, float) else round(val, 3)
        got = '%s  words=%s' % (shown, ' '.join('%04x' % r for r in regs[:8]) + (' ...' if len(regs) > 8 else ''))
        self.trace('%s -> %s' % (what, got))
        if expect == '~':
            return self.row('INFO', n, what, got)
        if expect[0] in '<>':
            try:
                ok = (float(val) > float(expect[1:])) if expect[0] == '>' else (float(val) < float(expect[1:]))
            except (TypeError, ValueError):
                ok = False
        else:
            ok = str(shown) == expect or (isinstance(val, float) and _num(expect) == round(val, 3))
        return self.row('PASS' if ok else 'FAIL', n, what, got)

    def probe(self, n, port, expect):
        c, _ = self.client(int(port))
        ok = c.connect()
        c.close()
        got = 'connected' if ok else 'refused'
        self.trace('PROBE %s:%s -> %s' % (self.a.host, port, got))
        self.row('PASS' if (ok == (expect == 'ok')) else 'FAIL', n, 'probe tcp %s' % port, got)

    # -- console --------------------------------------------------------------------------
    def cli(self, n, cmd, regex):
        if not self.a.console:
            return self.row('ERROR', n, 'cli ' + cmd, 'no --console given')
        cmds = [c.strip() for c in cmd.split(';;') if c.strip()]
        argv = [sys.executable, os.path.join(HERE, 'ckcon.py'), self.a.console, str(self.a.baud),
                self.a.transcript, '--stop-on-error'] + cmds
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=self.a.cli_timeout)
        except subprocess.TimeoutExpired:
            return self.row('ERROR', n, 'cli ' + cmd, 'ckcon timed out')
        text = p.stdout.replace('\r', '')
        self.out.write('%s >>> cli %s\n%s\n' % (time.strftime('%H:%M:%S'), cmd, text))
        m = re.search(regex, text, re.M) if regex else None
        if m:                                   # an expected refusal (% Invalid input) also stops ckcon
            return self.row('PASS', n, 'cli %s =~ %s' % (cmd, regex), m.group(0).strip()[:90])
        if p.returncode != 0:
            return self.row('ERROR', n, 'cli ' + cmd, 'ckcon rc=%d %s' % (p.returncode, (p.stderr or text).strip()[-120:]))
        if not regex:
            first = next((l.strip() for l in text.splitlines() if l.strip() and not any(c in l for c in cmds)), '')
            return self.row('INFO', n, 'cli ' + cmd, first[:90])
        return self.row('FAIL', n, 'cli %s =~ %s' % (cmd, regex), 'no match')


def _num(s):
    try:
        return round(float(s), 3)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--host', required=True, help="the DUT's Modbus/TCP address (a bench fact)")
    ap.add_argument('--port', type=int, default=502)
    ap.add_argument('--timeout', type=float, default=3.0)
    ap.add_argument('--console', help='/dev/uN of the stack master, for cli/log lines')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--transcript', default='console.log', help='ckcon transcript path')
    ap.add_argument('--cli-timeout', type=float, default=180)
    ap.add_argument('--log', default='mb.log', help='Modbus trace (appended)')
    ap.add_argument('--out', default='plan.out', help='full output: every row, trace and CLI text (appended)')
    ap.add_argument('--var', action='append', default=[], help='NAME=VALUE for ${NAME} in the plan')
    ap.add_argument('plan')
    a = ap.parse_args()
    import logging
    logging.getLogger('pymodbus').setLevel(logging.CRITICAL)   # its "Exception response 131 / 0" lines
    # print the exception code as 0 and would only add noise: the rows carry the real code
    vars_ = dict(v.split('=', 1) for v in a.var)
    r = Runner(a)
    r.out.write('### %s mbplan %s host=%s\n' % (time.strftime('%F %T %Z'), a.plan, a.host))
    for n, raw in enumerate(open(a.plan), 1):
        body = '' if raw.lstrip().startswith('#') else re.split(r'\s#\s', raw, maxsplit=1)[0]   # '#1 Alarm' is not a comment
        line = re.sub(r'\$\{(\w+)\}', lambda m: vars_.get(m.group(1), m.group(0)), body).strip()
        if not line:
            continue
        if '${' in line:
            r.row('ERROR', n, line, 'unset variable')
            continue
        op, _, rest = line.partition(' ')
        rest = rest.strip()
        try:
            if op == 'step':
                r.step = rest
                print('== %s' % rest, flush=True)
                r.out.write('== %s\n' % rest)
            elif op in ('read', 'write'):
                f = shlex.split(rest)
                unit, addr = f[0], f[1]
                if addr.startswith('@'):
                    pu, addr_i = port_addr(addr)
                    unit_i = pu if unit == '-' else int(unit)
                else:
                    unit_i, addr_i = int(unit), int(addr, 0)
                if op == 'read':
                    r.modbus(n, op, unit_i, addr_i, f[2], f[3], f[4], ' '.join(f[5:]))
                else:
                    r.modbus(n, op, unit_i, addr_i, f[2], None, f[3], ' '.join(f[4:]))
            elif op == 'probe':
                port, expect = rest.split()
                r.probe(n, port, expect)
            elif op == 'cli':
                cmd, _, regex = rest.partition(' =~ ')
                r.cli(n, cmd.strip(), regex.strip() or None)
            elif op == 'log':
                r.cli(n, 'show log | include %s' % rest, rest)
            elif op == 'port':
                r.mbport = int(rest)
            elif op == 'sleep':
                time.sleep(float(rest))
            else:
                r.row('ERROR', n, line, 'unknown action %r' % op)
        except (IndexError, ValueError) as e:
            r.row('ERROR', n, line, 'bad plan line: %s' % e)
    steps = {}
    for s, v in r.rows:
        steps.setdefault(s, []).append(v)
    print('-- per step:')
    for s, vs in steps.items():
        verdict = 'ERROR' if 'ERROR' in vs else 'FAIL' if 'FAIL' in vs else 'PASS' if 'PASS' in vs else 'INFO'
        print('   %-6s %s' % (verdict, s))
    return r.worst


if __name__ == '__main__':
    sys.exit(main())
