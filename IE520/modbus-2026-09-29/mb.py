#!/usr/bin/env python3
"""mb.py -- tb470 Modbus/TCP client for the IE520 SCADA Modbus cases (pymodbus 3.8.6).

  mb.py [--host H] [--port P] [--slave N] [--timeout S] read  ADDR COUNT TYPE [DESC]
  mb.py [...]                                          write ADDR VALUE      [DESC]
  mb.py [...]                                          probe                 (TCP connect only)

TYPE: UINT ASCII HEX ENUM FLOAT BOOL RAW  (ART library_1359 decodings; RAW = the word list).
Every request/response is traced as raw bytes (pymodbus trace_packet) and appended,
with the decoded value, to --log (default ./mb.log). Exit 0 = a Modbus response came
back (an exception response still exits 0 and is printed as EXCEPTION), 2 = no
connection / no response.
"""
import argparse, struct, sys, time
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

def word_to_ascii(w):
    hi, lo = w >> 8, w & 0xFF
    return chr(hi) + (chr(lo) if lo else '')

def decode(regs, typ):
    if typ == 'UINT':
        v = 0
        for i, r in enumerate(reversed(regs)):
            v += r << (16 * i)
        return v
    if typ == 'ASCII':
        return ''.join(word_to_ascii(w) for w in regs if w)
    if typ == 'HEX':
        return ''.join('{:04x}'.format(w) for w in regs)
    if typ == 'ENUM':
        return regs[0]
    if typ == 'FLOAT':
        return struct.unpack('!f', bytes.fromhex(''.join('{:04x}'.format(w) for w in regs)))[0]
    if typ == 'BOOL':
        return regs[0] == 0xFFFF
    return list(regs)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='10.38.215.10')
    ap.add_argument('--port', type=int, default=502)
    ap.add_argument('--slave', type=int, default=0)
    ap.add_argument('--timeout', type=float, default=3.0)
    ap.add_argument('--retries', type=int, default=0)
    ap.add_argument('--log', default='mb.log')
    ap.add_argument('--source', default=None, help='source IP to bind (e.g. an IPv6 LL addr)')
    sub = ap.add_subparsers(dest='op', required=True)
    r = sub.add_parser('read'); r.add_argument('addr'); r.add_argument('count', type=int); r.add_argument('type'); r.add_argument('desc', nargs='?', default='')
    w = sub.add_parser('write'); w.add_argument('addr'); w.add_argument('value'); w.add_argument('desc', nargs='?', default='')
    sub.add_parser('probe')
    a = ap.parse_args()

    log = open(a.log, 'a', buffering=1)
    def out(s):
        line = '{} {}'.format(time.strftime('%H:%M:%S'), s)
        print(line); log.write(line + '\n')

    pkts = []
    def trace(sending, data):
        pkts.append(('TX' if sending else 'RX', data.hex(' ')))
        return data

    kw = dict(port=a.port, timeout=a.timeout, retries=a.retries, trace_packet=trace)
    if a.source:
        kw['source_address'] = (a.source, 0)
    c = ModbusTcpClient(a.host, **kw)
    target = '[{}]:{}'.format(a.host, a.port) if ':' in a.host else '{}:{}'.format(a.host, a.port)
    ok = c.connect()
    if not ok:
        out('CONNECT {} slave={} -> FAILED (no TCP connection)'.format(target, a.slave))
        return 2
    out('CONNECT {} slave={} -> ok'.format(target, a.slave))
    rc = 0
    try:
        if a.op == 'probe':
            pass
        elif a.op == 'read':
            addr = int(a.addr, 0)
            try:
                rsp = c.read_holding_registers(addr, count=a.count, slave=a.slave)
            except ModbusException as e:
                out('READ  0x{:04x} x{} {} {} -> NO RESPONSE: {}'.format(addr, a.count, a.type, a.desc, e)); rc = 2; rsp = None
            if rsp is not None:
                for d, h in pkts: out('  {} {}'.format(d, h))
                if rsp.isError():
                    out('READ  0x{:04x} x{} {} {} -> EXCEPTION {}'.format(addr, a.count, a.type, a.desc, rsp))
                else:
                    regs = rsp.registers
                    out('READ  0x{:04x} x{} {} {} -> words={} value={!r}'.format(
                        addr, a.count, a.type, a.desc, ['0x{:04x}'.format(x) for x in regs], decode(regs, a.type.upper())))
        elif a.op == 'write':
            addr = int(a.addr, 0); val = int(a.value, 0)
            try:
                rsp = c.write_register(addr, val, slave=a.slave)
            except ModbusException as e:
                out('WRITE 0x{:04x} = 0x{:04x} {} -> NO RESPONSE: {}'.format(addr, val, a.desc, e)); rc = 2; rsp = None
            if rsp is not None:
                for d, h in pkts: out('  {} {}'.format(d, h))
                if rsp.isError():
                    out('WRITE 0x{:04x} = 0x{:04x} {} -> EXCEPTION {}'.format(addr, val, a.desc, rsp))
                else:
                    out('WRITE 0x{:04x} = 0x{:04x} {} -> ok (echo addr=0x{:04x} value=0x{:04x})'.format(addr, val, a.desc, rsp.address, rsp.registers[0] if rsp.registers else -1))
    finally:
        c.close()
    return rc

if __name__ == '__main__':
    sys.exit(main())
