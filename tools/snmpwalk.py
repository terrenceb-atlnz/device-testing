#!/usr/bin/env python3
"""snmpwalk.py -- walk an SNMP agent's MIB with SNMPv2c (GETBULK, or GETNEXT with --getnext),
stdlib only, so it runs on a testbox that has no net-snmp and no pysnmp.

  python3 snmpwalk.py <agent-ip> <community> <outfile> [--root 1.3.6.1] [--bulk 20]
                      [--timeout 3] [--retries 3] [--max 200000] [--getnext] [--src <ip>]

Every varbind goes to <outfile>, one line each: `<oid> = <TYPE>: <value>`. stdout gets a summary
only: varbinds walked, requests, retries, elapsed time, the first and last OID, the number of
top-level subtrees under --root, and why the walk stopped:
  - END: endOfMibView, or the agent returned an OID outside --root (a complete walk);
  - NOT-INCREASING: the agent returned an OID that is not greater than the previous one
    (an agent defect; the walk stops rather than loop);
  - TIMEOUT: no answer after --retries tries;
  - ERROR: the agent answered with a non-zero error-status (named);
  - MAX: --max varbinds were walked (a guard, not a verdict).
Exit 0 on END, 1 on anything else, 2 on bad arguments.

The walk is read-only (GET-type PDUs only). It is generic: the agent, community and subtree are
arguments; nothing in it is specific to one product.
"""
import argparse
import random
import socket
import sys
import time

# ---- BER encoding -------------------------------------------------------------------------

def enc_len(n):
    if n < 0x80:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(b)]) + b


def tlv(tag, body):
    return bytes([tag]) + enc_len(len(body)) + body


def enc_int(v):
    n = max(1, (v.bit_length() + 8) // 8)
    return tlv(0x02, v.to_bytes(n, "big", signed=True))


def enc_oid(oid):
    parts = [int(x) for x in oid.strip(".").split(".")]
    out = bytearray([40 * parts[0] + parts[1]])
    for p in parts[2:]:
        chunk = [p & 0x7F]
        p >>= 7
        while p:
            chunk.append(0x80 | (p & 0x7F))
            p >>= 7
        out += bytes(reversed(chunk))
    return tlv(0x06, bytes(out))


def request(community, pdu_tag, reqid, a, b, oid):
    varbind = tlv(0x30, enc_oid(oid) + tlv(0x05, b""))
    pdu = tlv(pdu_tag, enc_int(reqid) + enc_int(a) + enc_int(b) + tlv(0x30, varbind))
    return tlv(0x30, enc_int(1) + tlv(0x04, community.encode()) + pdu)   # version 1 = v2c

# ---- BER decoding -------------------------------------------------------------------------

def dec_tlv(buf, i):
    tag = buf[i]
    ln = buf[i + 1]
    i += 2
    if ln & 0x80:
        k = ln & 0x7F
        ln = int.from_bytes(buf[i:i + k], "big")
        i += k
    return tag, buf[i:i + ln], i + ln


def dec_oid(b):
    first = b[0]
    parts = [first // 40, first % 40] if first < 80 else [2, first - 80]
    v = 0
    for c in b[1:]:
        v = (v << 7) | (c & 0x7F)
        if not c & 0x80:
            parts.append(v)
            v = 0
    return ".".join(str(p) for p in parts)


TYPES = {0x02: "INTEGER", 0x04: "STRING", 0x05: "NULL", 0x06: "OID", 0x40: "IpAddress",
         0x41: "Counter32", 0x42: "Gauge32", 0x43: "Timeticks", 0x44: "Opaque",
         0x46: "Counter64", 0x80: "noSuchObject", 0x81: "noSuchInstance",
         0x82: "endOfMibView"}
ERRORS = {1: "tooBig", 2: "noSuchName", 3: "badValue", 4: "readOnly", 5: "genErr",
          6: "noAccess", 7: "wrongType", 8: "wrongLength", 9: "wrongEncoding",
          10: "wrongValue", 11: "noCreation", 12: "inconsistentValue",
          13: "resourceUnavailable", 14: "commitFailed", 15: "undoFailed",
          16: "authorizationError", 17: "notWritable", 18: "inconsistentName"}


def fmt_value(tag, b):
    if tag == 0x02:
        return str(int.from_bytes(b, "big", signed=True)) if b else "0"
    if tag in (0x41, 0x42, 0x43, 0x46):
        return str(int.from_bytes(b, "big"))
    if tag == 0x06:
        return dec_oid(b)
    if tag == 0x40 and len(b) == 4:
        return ".".join(str(x) for x in b)
    if tag == 0x04:
        if b and all(32 <= c < 127 or c in (9, 10, 13) for c in b):
            return '"%s"' % b.decode().replace("\n", "\\n").replace("\r", "\\r")
        return "Hex: " + " ".join("%02X" % c for c in b)
    return " ".join("%02X" % c for c in b)


def parse_response(buf):
    _, msg, _ = dec_tlv(buf, 0)
    i = 0
    _, _ver, i = dec_tlv(msg, i)
    _, _comm, i = dec_tlv(msg, i)
    _pdutag, pdu, _ = dec_tlv(msg, i)
    j = 0
    _, rid, j = dec_tlv(pdu, j)
    _, es, j = dec_tlv(pdu, j)
    _, ei, j = dec_tlv(pdu, j)
    _, vbl, _ = dec_tlv(pdu, j)
    out = []
    k = 0
    while k < len(vbl):
        _, vb, k = dec_tlv(vbl, k)
        _, ob, m = dec_tlv(vb, 0)
        vtag, vb2, _ = dec_tlv(vb, m)
        out.append((dec_oid(ob), vtag, vb2))
    return (int.from_bytes(rid, "big", signed=True), int.from_bytes(es, "big"),
            int.from_bytes(ei, "big"), out)

# ---- walk ---------------------------------------------------------------------------------

def oid_key(o):
    return tuple(int(x) for x in o.split("."))


def walk(a):
    root = a.root.strip(".")
    rk = oid_key(root)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if a.src:
        s.bind((a.src, 0))
    s.settimeout(a.timeout)
    cur, prev_key = root, None
    n = reqs = retries = 0
    first = last = None
    subtrees = set()
    reason = "MAX"
    t0 = time.time()
    with open(a.outfile, "w") as f:
        while n < a.max:
            rid = random.randint(1, 2**31 - 1)
            if a.getnext:
                pkt = request(a.community, 0xA1, rid, 0, 0, cur)
            else:
                pkt = request(a.community, 0xA5, rid, 0, a.bulk, cur)
            resp = None
            for attempt in range(a.retries):
                reqs += 1
                s.sendto(pkt, (a.agent, 161))
                try:
                    while True:
                        data, _ = s.recvfrom(65535)
                        r = parse_response(data)
                        if r[0] == rid:
                            resp = r
                            break
                except socket.timeout:
                    retries += 1
                    continue
                break
            if resp is None:
                reason = "TIMEOUT after %d tries at %s" % (a.retries, cur)
                break
            _, es, ei, vbs = resp
            if es:
                reason = "ERROR %s (index %d) at %s" % (ERRORS.get(es, es), ei, cur)
                break
            done = False
            for oid, tag, val in vbs:
                k = oid_key(oid)
                if tag == 0x82 or k[:len(rk)] != rk:
                    reason, done = "END", True
                    break
                if prev_key is not None and k <= prev_key:
                    reason, done = "NOT-INCREASING: %s after %s" % (oid, last), True
                    break
                f.write("%s = %s: %s\n" % (oid, TYPES.get(tag, "0x%02X" % tag),
                                           fmt_value(tag, val)))
                n += 1
                first = first or oid
                last, prev_key = oid, k
                if len(k) > len(rk):
                    subtrees.add(".".join(str(x) for x in k[:len(rk) + 3]))
                if n >= a.max:
                    break
            if done:
                break
            if not vbs:
                reason = "ERROR empty response at %s" % cur
                break
            cur = last
    dt = time.time() - t0
    print("walk %s community=%s root=%s mode=%s" % (a.agent, a.community, root,
                                                    "getnext" if a.getnext else "getbulk/%d" % a.bulk))
    print("  varbinds %d  requests %d  retries %d  elapsed %.1f s" % (n, reqs, retries, dt))
    print("  first %s" % first)
    print("  last  %s" % last)
    print("  subtrees (root + 3 arcs) %d: %s" % (len(subtrees), " ".join(sorted(subtrees, key=oid_key))[:600]))
    print("  stopped: %s" % reason)
    print("  output -> %s" % a.outfile)
    return 0 if reason == "END" else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agent")
    ap.add_argument("community")
    ap.add_argument("outfile")
    ap.add_argument("--root", default="1.3.6.1")
    ap.add_argument("--bulk", type=int, default=20, help="GETBULK max-repetitions (default 20)")
    ap.add_argument("--getnext", action="store_true", help="walk with GETNEXT instead of GETBULK")
    ap.add_argument("--timeout", type=float, default=3.0)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--max", type=int, default=200000)
    ap.add_argument("--src", default=None, help="bind to this local IPv4 address")
    a = ap.parse_args(argv)
    return walk(a)


if __name__ == "__main__":
    sys.exit(main())
