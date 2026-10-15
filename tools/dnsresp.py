#!/usr/bin/env python3
"""IPv4 DNS test tool: a crafted query client and a fake authoritative responder.

Built for DNS relay / DNS forwarding cases, where the verdict needs to count the
queries a device forwards upstream and the answers it returns downstream, and to
prove a cache hit by the ABSENCE of an upstream query.

Everything is crafted and read at layer 2, so no host IP, route or resolver
change is made and the only privilege needed is a raw socket. Both modes answer
ARP for the address they impersonate, so the device under test can resolve them
without a static ARP entry.

  dnsresp.py respond <iface> --for <ip> [--zone name=ip ...]   fake DNS server
  dnsresp.py query   <iface> --server <ip> --server-mac <mac> --name <qname>

Counting note (learned the hard way on tb277, 2026-10-15): a scapy sniffer
starts several seconds after the process does, because importing scapy is slow.
Run tcpdump alongside and treat IT as authoritative for what was on the wire;
this tool's counts are what it decoded.
"""

import argparse
import json
import os
import sys
import time

os.environ.setdefault("SCAPY_USE_PCAPDNET", "no")

from scapy.all import (  # noqa: E402
    ARP,
    DNS,
    DNSQR,
    DNSRR,
    Ether,
    IP,
    UDP,
    AsyncSniffer,
    conf,
    get_if_hwaddr,
    sendp,
    wrpcap,
)

BPF = "arp or udp port 53"


def qname_of(pkt):
    try:
        return pkt[DNS].qd.qname.decode().rstrip(".")
    except Exception:
        return None


def arp_reply(pkt, ip, my_mac, iface):
    sendp(Ether(src=my_mac, dst=pkt[Ether].src)
          / ARP(op=2, hwsrc=my_mac, psrc=ip, hwdst=pkt[ARP].hwsrc, pdst=pkt[ARP].psrc),
          iface=iface, verbose=0)


# ---------------------------------------------------------------- respond

def cmd_respond(args):
    iface = args.iface
    conf.iface = iface
    my_mac = get_if_hwaddr(iface)
    zone = {}
    for z in args.zone or []:
        name, _, addr = z.partition("=")
        zone[name.rstrip(".").lower()] = addr
    seen = {"arp": 0, "queries": [], "answered": 0, "refused": 0}
    t0 = time.time()

    def on(pkt):
        now = round(time.time() - t0, 4)
        if ARP in pkt and pkt[ARP].op == 1 and pkt[ARP].pdst == args.for_ip:
            seen["arp"] += 1
            arp_reply(pkt, args.for_ip, my_mac, iface)
            return
        if DNS not in pkt or pkt[DNS].qr != 0 or pkt[IP].dst != args.for_ip:
            return
        name = qname_of(pkt)
        rec = {"t": now, "qname": name, "id": pkt[DNS].id,
               "src_ip": pkt[IP].src, "src_port": pkt[UDP].sport}
        seen["queries"].append(rec)
        addr = zone.get((name or "").lower(), args.default_answer)
        if not addr:
            seen["refused"] += 1
            rec["answered"] = False
            return
        sendp(Ether(src=my_mac, dst=pkt[Ether].src)
              / IP(src=args.for_ip, dst=pkt[IP].src)
              / UDP(sport=53, dport=pkt[UDP].sport)
              / DNS(id=pkt[DNS].id, qr=1, aa=1, qd=pkt[DNS].qd,
                    an=DNSRR(rrname=pkt[DNS].qd.qname, type="A",
                             ttl=args.ttl, rdata=addr)),
              iface=iface, verbose=0)
        seen["answered"] += 1
        rec["answered"] = True
        rec["rdata"] = addr

    print("dnsresp responder on %s as %s (zone: %s, default %s, ttl %d)"
          % (iface, args.for_ip, zone or "-", args.default_answer, args.ttl),
          file=sys.stderr)
    s = AsyncSniffer(iface=iface, filter=BPF, prn=on, store=bool(args.pcap))
    s.start()
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        pass
    s.stop()
    if args.pcap and s.results:
        wrpcap(args.pcap, s.results)
    print(json.dumps(seen, indent=2, default=str))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(seen, f, indent=2, default=str)
    print("UPSTREAM QUERIES RECEIVED: %d   answered %d   arp answered %d"
          % (len(seen["queries"]), seen["answered"], seen["arp"]), file=sys.stderr)
    for q in seen["queries"]:
        print("   t=%-8s %-28s from %s" % (q["t"], q["qname"], q["src_ip"]), file=sys.stderr)
    return 0


# ---------------------------------------------------------------- query

def cmd_query(args):
    iface = args.iface
    conf.iface = iface
    my_mac = args.src_mac or get_if_hwaddr(iface)
    results = []
    got = {}
    t0 = time.time()

    def on(pkt):
        # answer ARP for the address we are pretending to be, so the device
        # under test can send its reply back to us
        if ARP in pkt and pkt[ARP].op == 1 and pkt[ARP].pdst == args.src_ip:
            arp_reply(pkt, args.src_ip, my_mac, iface)
            return
        if DNS not in pkt or pkt[DNS].qr != 1:
            return
        if pkt[IP].dst != args.src_ip:
            return
        answers = []
        for i in range(pkt[DNS].ancount or 0):
            try:
                rr = pkt[DNS].an[i]
                answers.append({"rrname": rr.rrname.decode().rstrip("."),
                                "rdata": str(rr.rdata), "ttl": int(rr.ttl)})
            except Exception:
                pass
        got[pkt[DNS].id] = {"t": round(time.time() - t0, 4),
                            "qname": qname_of(pkt), "answers": answers,
                            "rcode": pkt[DNS].rcode}

    s = AsyncSniffer(iface=iface, filter=BPF, prn=on, store=bool(args.pcap))
    s.start()
    time.sleep(0.4)

    names = args.name if args.name else []
    for i in range(args.count):
        for n in names:
            qid = (args.base_id + i * 100 + names.index(n)) & 0xFFFF
            sendp(Ether(src=my_mac, dst=args.server_mac)
                  / IP(src=args.src_ip, dst=args.server)
                  / UDP(sport=40000 + (qid % 20000), dport=53)
                  / DNS(id=qid, rd=1, qd=DNSQR(qname=n, qtype="A")),
                  iface=iface, verbose=0)
            results.append({"qid": qid, "qname": n})
        if args.gap and i < args.count - 1:
            time.sleep(args.gap)

    deadline = time.time() + args.wait
    while time.time() < deadline and len(got) < len(results):
        time.sleep(0.1)
    time.sleep(0.3)
    s.stop()
    if args.pcap and s.results:
        wrpcap(args.pcap, s.results)

    for r in results:
        r.update(got.get(r["qid"], {}) or {"answers": None})
    out = {"sent": len(results), "answered": sum(1 for r in results if r.get("answers")),
           "queries": results}
    print(json.dumps(out, indent=2, default=str))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=2, default=str)
    print("QUERIES SENT: %d   ANSWERS RECEIVED: %d" % (out["sent"], out["answered"]),
          file=sys.stderr)
    for r in results:
        print("   %-28s -> %s" % (r["qname"], r.get("answers") or "NO ANSWER"),
              file=sys.stderr)
    return 0 if out["answered"] else 2


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("respond", help="fake authoritative DNS server + ARP responder")
    r.add_argument("iface")
    r.add_argument("--for", dest="for_ip", required=True,
                   help="the server address to impersonate (ARP is answered for it)")
    r.add_argument("--zone", action="append", help="name=A-record, repeatable")
    r.add_argument("--default-answer", help="A record for any name not in --zone")
    r.add_argument("--ttl", type=int, default=60)
    r.add_argument("--duration", type=float, default=60.0)
    r.add_argument("--pcap")
    r.add_argument("--json")
    r.set_defaults(fn=cmd_respond)

    q = sub.add_parser("query", help="send crafted DNS A queries and count the answers")
    q.add_argument("iface")
    q.add_argument("--server", required=True, help="IP to send the query to (the relay)")
    q.add_argument("--server-mac", required=True, help="L2 destination (the relay's MAC)")
    q.add_argument("--src-ip", required=True, help="our pretend host address")
    q.add_argument("--src-mac")
    q.add_argument("--name", action="append", required=True, help="qname, repeatable")
    q.add_argument("--count", type=int, default=1, help="rounds of the whole name list")
    q.add_argument("--gap", type=float, default=0.0)
    q.add_argument("--base-id", type=lambda x: int(x, 0), default=0x4b00)
    q.add_argument("--wait", type=float, default=8.0)
    q.add_argument("--pcap")
    q.add_argument("--json")
    q.set_defaults(fn=cmd_query)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
