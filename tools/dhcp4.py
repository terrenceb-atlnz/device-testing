#!/usr/bin/env python3
"""IPv4 DHCP/BOOTP test tool: crafted client, minimal server, and a pcap decoder.

The IPv4 counterpart to dhc6.py (DHCPv6). Built for DHCP server, relay and client
cases where a verdict needs the exact bytes on the wire: option 51 lease time,
option 61 client identifier, option 12 hostname, option 82 relay agent
information, giaddr rewriting, and the ARP probes a server emits before it
offers an address.

Nothing is installed on the host and no host IP, route or interface change is
made: every frame is crafted and read at layer 2, so the only privilege needed
is a raw socket (sudo).

  dhcp4.py client <iface> [...]    one DHCP transaction + ARP-probe observation
  dhcp4.py server <iface> [...]    minimal pool server (+ ARP responder)
  dhcp4.py decode <pcap> [...]     count and dump DHCP/BOOTP and ARP frames

!! scapy option 82 trap (measured, scapy 2.4.4) !!
    DHCP(options=[(82, raw)])                        -> SILENTLY DROPPED
    DHCP(options=[("relay_agent_information", raw)]) -> correct
  Building option 82 by its integer key serialises a frame WITHOUT the option
  and raises nothing. A test that did that would read "the relay did not insert
  option 82" and grade a working device defective. Always use OPT82 below.
"""

import argparse
import ipaddress
import json
import os
import random
import sys
import time

os.environ.setdefault("SCAPY_USE_PCAPDNET", "no")

from scapy.all import (  # noqa: E402
    ARP,
    BOOTP,
    DHCP,
    ICMP,
    Ether,
    IP,
    UDP,
    AsyncSniffer,
    bind_layers,
    conf,
    get_if_hwaddr,
    mac2str,
    rdpcap,
    sendp,
    str2mac,
    wrpcap,
)

# The ONE correct spelling of option 82 for this scapy. See the module docstring.
OPT82 = "relay_agent_information"

# !! Relayed DHCP arrives from an EPHEMERAL source port !!
# scapy binds BOOTP to UDP only for the exact pairs (sport 68, dport 67) and
# (sport 67, dport 68). An AW+ DHCP relay forwards to the server from an ephemeral
# source port (measured on tb277: 192.168.48.1:57304 -> 192.168.48.2:67), so the
# relayed frame is NOT dissected as BOOTP and silently reads as Raw -- a server or
# decoder would report "nothing arrived" while tcpdump on the same NIC shows the
# packet plainly. Bind on destination port alone so any DHCP frame is dissected.
bind_layers(UDP, BOOTP, dport=67)
bind_layers(UDP, BOOTP, dport=68)

BCAST = "ff:ff:ff:ff:ff:ff"
MSGTYPE = {
    1: "DISCOVER", 2: "OFFER", 3: "REQUEST", 4: "DECLINE",
    5: "ACK", 6: "NAK", 7: "RELEASE", 8: "INFORM",
}
BPF = "arp or icmp or (udp and (port 67 or port 68))"


# ---------------------------------------------------------------- helpers

def _jsonable(v):
    if isinstance(v, bytes):
        return {"hex": v.hex(), "ascii": v.decode("latin-1")}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    return v


def opts_of(pkt):
    """DHCP options of a packet as an ordered list of (name, value) and a dict."""
    out, d = [], {}
    if DHCP not in pkt:
        return out, d
    for o in pkt[DHCP].options:
        if isinstance(o, tuple) and len(o) >= 2:
            name, val = o[0], o[1] if len(o) == 2 else list(o[1:])
            out.append((name, val))
            d.setdefault(name, val)
        elif o in ("end", "pad"):
            break
    return out, d


def msgtype_of(pkt):
    _, d = opts_of(pkt)
    mt = d.get("message-type")
    return MSGTYPE.get(mt, str(mt))


def sub_tlvs(raw):
    """Split an option-82 payload into its sub-options {code: bytes}."""
    out, i = {}, 0
    while i + 2 <= len(raw):
        code, ln = raw[i], raw[i + 1]
        out[code] = raw[i + 2:i + 2 + ln]
        i += 2 + ln
    return out


def describe82(raw):
    t = sub_tlvs(raw)
    d = {"raw": raw.hex()}
    if 1 in t:
        d["circuit_id"] = {"hex": t[1].hex(), "ascii": t[1].decode("latin-1")}
    if 2 in t:
        d["remote_id"] = {"hex": t[2].hex(), "ascii": t[2].decode("latin-1")}
    for c, v in t.items():
        if c not in (1, 2):
            d.setdefault("other", {})[c] = v.hex()
    return d


def summarize(pkt):
    """One DHCP/BOOTP frame as a plain dict."""
    out, d = opts_of(pkt)
    s = {
        "type": msgtype_of(pkt),
        "xid": hex(pkt[BOOTP].xid),
        "chaddr": str2mac(pkt[BOOTP].chaddr[:6]),
        "yiaddr": pkt[BOOTP].yiaddr,
        "siaddr": pkt[BOOTP].siaddr,
        "giaddr": pkt[BOOTP].giaddr,
        "hops": pkt[BOOTP].hops,
        "eth_src": pkt[Ether].src,
        "eth_dst": pkt[Ether].dst,
        "ip_src": pkt[IP].src,
        "ip_dst": pkt[IP].dst,
        "options": {},
    }
    for k, v in d.items():
        if k == "message-type":
            continue
        s["options"][str(k)] = _jsonable(v)
    # Option 82 can legitimately appear TWICE: `ip dhcp-relay information policy append`
    # puts the relay's own TLV after the client's. opts_of()'s dict keeps only the first,
    # so always report every occurrence or an appended field silently disappears
    # (measured on tb277, 2026-10-15 -- it briefly read as "append did not append").
    all82 = [v for (k, v) in out if k == OPT82]
    if all82:
        s["option82"] = describe82(all82[0])
        s["option82_count"] = len(all82)
        if len(all82) > 1:
            s["option82_all"] = [describe82(v) for v in all82]
    return s


def parse_optfile(spec):
    """--option82 accepts raw hex, or circuit-id/remote-id ascii shorthand."""
    if spec is None:
        return None
    if spec.startswith("hex:"):
        return bytes.fromhex(spec[4:])
    out = b""
    for part in spec.split(","):
        if ":" not in part:
            raise ValueError("option82 part needs circuit:/remote:/hex: prefix")
        k, v = part.split(":", 1)
        if k == "circuit":
            out += bytes([1, len(v)]) + v.encode()
        elif k == "remote":
            out += bytes([2, len(v)]) + v.encode()
        else:
            raise ValueError("unknown option82 part %r" % k)
    return out


def rand_mac(seed=None):
    r = random.Random(seed)
    return "02:%02x:%02x:%02x:%02x:%02x" % tuple(r.randint(0, 255) for _ in range(5))


def parse_client_id(spec):
    """Option 61. 'hex:..' is raw; a bare MAC becomes type-01 + 6 bytes
    (RFC 2132 hardware type 1 = Ethernet); anything else is sent as ASCII."""
    if spec.startswith("hex:"):
        return bytes.fromhex(spec[4:])
    bare = spec.replace("-", ":")
    if len(bare) == 17 and bare.count(":") == 5:
        return b"\x01" + mac2str(bare)
    return spec.encode()


# ---------------------------------------------------------------- client

def build_dhcp(mac, mtype, xid, args, requested=None, server_id=None):
    opts = [("message-type", mtype)]
    if args.client_id:
        opts.append(("client_id", parse_client_id(args.client_id)))
    if args.hostname:
        opts.append(("hostname", args.hostname.encode()))
    if requested:
        opts.append(("requested_addr", requested))
    if server_id:
        opts.append(("server_id", server_id))
    if args.prl:
        opts.append(("param_req_list", [int(x) for x in args.prl.split(",")]))
    o82 = parse_optfile(args.option82)
    if o82:
        opts.append((OPT82, o82))          # never (82, ...) -- see module docstring
    opts.append("end")

    eth_src = args.src_mac or mac
    ip_src = args.giaddr if args.giaddr else "0.0.0.0"
    ip_dst = args.server_ip if args.giaddr else "255.255.255.255"
    eth_dst = args.dst_mac or BCAST
    sport, dport = (67, 67) if args.giaddr else (68, 67)

    return (Ether(src=eth_src, dst=eth_dst)
            / IP(src=ip_src, dst=ip_dst)
            / UDP(sport=sport, dport=dport)
            / BOOTP(chaddr=mac2str(mac), xid=xid, flags=0x8000 if args.broadcast else 0,
                    giaddr=args.giaddr or "0.0.0.0", hops=args.hops)
            / DHCP(options=opts))


def cmd_client(args):
    iface = args.iface
    conf.iface = iface
    mac = args.mac or rand_mac()
    xid = args.xid if args.xid is not None else random.getrandbits(32)
    answer_for = set(args.arp_answer.split(",")) if args.arp_answer else set()
    icmp_for = set(args.icmp_answer.split(",")) if args.icmp_answer else set()
    watch = ipaddress.ip_network(args.arp_watch, strict=False) if args.arp_watch else None
    my_mac = get_if_hwaddr(iface)

    seen = {"arp": [], "icmp": [], "dhcp": []}
    t0 = time.time()

    def on(pkt):
        now = round(time.time() - t0, 4)
        if ARP in pkt and pkt[ARP].op == 1:
            tgt = pkt[ARP].pdst
            if watch and ipaddress.ip_address(tgt) not in watch:
                return
            seen["arp"].append({"t": now, "target": tgt,
                                "sender_ip": pkt[ARP].psrc, "sender_mac": pkt[ARP].hwsrc})
            if tgt in answer_for:
                # pretend that address is already in use by some other host
                rep = (Ether(src=my_mac, dst=pkt[Ether].src)
                       / ARP(op=2, hwsrc=my_mac, psrc=tgt,
                             hwdst=pkt[ARP].hwsrc, pdst=pkt[ARP].psrc))
                sendp(rep, iface=iface, verbose=0)
                seen["arp"][-1]["answered"] = True
            return
        if ICMP in pkt and pkt[ICMP].type == 8:
            tgt = pkt[IP].dst
            if watch and ipaddress.ip_address(tgt) not in watch:
                return
            ent = {"t": now, "target": tgt, "sender_ip": pkt[IP].src,
                   "id": pkt[ICMP].id, "seq": pkt[ICMP].seq}
            seen["icmp"].append(ent)
            if tgt in icmp_for:
                # the simulated host is alive: answer the server's ping probe
                sendp(Ether(src=my_mac, dst=pkt[Ether].src)
                      / IP(src=tgt, dst=pkt[IP].src)
                      / ICMP(type=0, id=pkt[ICMP].id, seq=pkt[ICMP].seq)
                      / bytes(pkt[ICMP].payload),
                      iface=iface, verbose=0)
                ent["answered"] = True
            return
        if BOOTP in pkt and DHCP in pkt and pkt[BOOTP].op == 2:
            s = summarize(pkt)
            s["t"] = now
            seen["dhcp"].append(s)

    sniffer = AsyncSniffer(iface=iface, filter=BPF, prn=on, store=bool(args.pcap))
    sniffer.start()
    time.sleep(0.4)

    sent = {"discover": 0, "request": 0}
    txs = []

    def wait_for(kinds, want_xid, secs):
        deadline = time.time() + secs
        while time.time() < deadline:
            hit = next((d for d in seen["dhcp"]
                        if d["type"] in kinds and int(d["xid"], 16) == want_xid), None)
            if hit:
                return hit
            time.sleep(0.05)
        return None

    def one(tx_mac, tx_xid):
        sendp(build_dhcp(tx_mac, 1, tx_xid, args), iface=iface, verbose=0, count=args.count)
        sent["discover"] += args.count
        off = wait_for(("OFFER",), tx_xid, args.wait)
        a = None
        if off and not args.discover_only:
            req = build_dhcp(tx_mac, 3, tx_xid, args, requested=off["yiaddr"],
                             server_id=off["options"].get("server_id") or off["siaddr"])
            sendp(req, iface=iface, verbose=0)
            sent["request"] += 1
            a = wait_for(("ACK", "NAK"), tx_xid, args.wait)
        txs.append({"chaddr": tx_mac, "xid": hex(tx_xid),
                    "offer": off["yiaddr"] if off else None,
                    "ack": (a["type"] + " " + a["yiaddr"]) if a else None,
                    "lease_time": (a or off or {}).get("options", {}).get("lease_time"),
                    "offer_frame": off, "ack_frame": a})
        return off, a

    # N distinct clients in ONE process: a fresh subprocess per client costs several
    # seconds of scapy import, which silently skews any timed count (measured 2026-10-15).
    base = [int(x, 16) for x in mac.split(":")]
    offer = ack = None
    for i in range(args.clients):
        b = list(base)
        b[5] = (b[5] + i) & 0xFF
        tx_mac = ":".join("%02x" % x for x in b)
        tx_xid = (xid + i) & 0xFFFFFFFF
        o, a = one(tx_mac, tx_xid)
        if i == 0:
            offer, ack = o, a
        if args.gap and i < args.clients - 1:
            time.sleep(args.gap)

    time.sleep(0.3)
    sniffer.stop()
    if args.pcap and sniffer.results:
        wrpcap(args.pcap, sniffer.results)

    res = {
        "iface": iface, "chaddr": mac, "xid": hex(xid),
        "sent": sent,
        "arp_probes": seen["arp"],
        "arp_probe_count": len(seen["arp"]),
        "arp_answered": sum(1 for a in seen["arp"] if a.get("answered")),
        "icmp_probes": seen["icmp"],
        "icmp_probe_count": len(seen["icmp"]),
        "icmp_answered": sum(1 for a in seen["icmp"] if a.get("answered")),
        "offer": offer, "ack": ack,
        "clients": args.clients,
        "transactions": txs,
        "offers_received": sum(1 for t in txs if t["offer"]),
        "acks_received": sum(1 for t in txs if t["ack"]),
        "dhcp_frames": seen["dhcp"],
    }
    if len(seen["arp"]) > 1:
        gaps = [round(seen["arp"][i + 1]["t"] - seen["arp"][i]["t"], 3)
                for i in range(len(seen["arp"]) - 1)]
        res["arp_gaps_s"] = gaps

    print(json.dumps(res, indent=2, default=str))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, indent=2, default=str)

    print("\n--- summary ---", file=sys.stderr)
    print("chaddr %s xid %s" % (mac, hex(xid)), file=sys.stderr)
    print("sent: %d DISCOVER, %d REQUEST  (clients=%d)" % (
        sent["discover"], sent["request"], args.clients), file=sys.stderr)
    if args.clients > 1:
        print("offers received: %d/%d   acks received: %d/%d" % (
            res["offers_received"], args.clients,
            res["acks_received"], args.clients), file=sys.stderr)
        for t in txs:
            print("   %s -> offer %s ack %s" % (t["chaddr"], t["offer"], t["ack"]),
                  file=sys.stderr)
    print("ARP probes seen: %d%s" % (len(seen["arp"]),
          (" gaps=%s" % res.get("arp_gaps_s")) if len(seen["arp"]) > 1 else ""), file=sys.stderr)
    for a in seen["arp"]:
        print("   t=%-8s target=%-16s from=%s%s" % (a["t"], a["target"], a["sender_ip"],
              "  <- ANSWERED" if a.get("answered") else ""), file=sys.stderr)
    print("ICMP probes seen: %d (answered %d)" % (
        len(seen["icmp"]), sum(1 for a in seen["icmp"] if a.get("answered"))), file=sys.stderr)
    for a in seen["icmp"]:
        print("   t=%-8s target=%-16s from=%s%s" % (a["t"], a["target"], a["sender_ip"],
              "  <- ANSWERED" if a.get("answered") else ""), file=sys.stderr)
    print("OFFER: %s" % (offer["yiaddr"] if offer else "NONE"), file=sys.stderr)
    if offer:
        print("   lease_time=%s" % offer["options"].get("lease_time"), file=sys.stderr)
    print("ACK  : %s" % (("%s %s" % (ack["type"], ack["yiaddr"])) if ack else "NONE"),
          file=sys.stderr)
    if ack:
        print("   lease_time=%s renewal=%s rebinding=%s" % (
            ack["options"].get("lease_time"), ack["options"].get("renewal_time"),
            ack["options"].get("rebinding_time")), file=sys.stderr)
    return 0 if offer else 2


# ---------------------------------------------------------------- server

def cmd_server(args):
    iface = args.iface
    conf.iface = iface
    my_mac = get_if_hwaddr(iface)
    addrs = []
    cur = ipaddress.ip_address(args.pool_start)
    end = ipaddress.ip_address(args.pool_end)
    while cur <= end:
        addrs.append(str(cur))
        cur += 1
    leased, log = {}, []
    arp_for = set((args.arp_for or args.server_ip).split(","))
    t0 = time.time()

    def reply(pkt, mtype, yip):
        _, d = opts_of(pkt)
        opts = [("message-type", mtype),
                ("server_id", args.server_ip),
                ("lease_time", args.lease),
                ("subnet_mask", args.mask)]
        if args.router:
            opts.append(("router", args.router))
        if args.dns:
            opts.append(("name_server", args.dns))
        if args.option82_override:
            # deliberately return option 82 that does NOT match what the relay inserted,
            # to exercise `ip dhcp-relay agent-option checking` on the response path
            opts.append((OPT82, parse_optfile(args.option82_override)))
        elif args.echo_option82 and OPT82 in d:
            opts.append((OPT82, d[OPT82]))      # RFC 3046 echo; never (82, ...)
        opts.append("end")
        gi = pkt[BOOTP].giaddr
        relayed = gi not in ("0.0.0.0", None)
        return (Ether(src=my_mac, dst=pkt[Ether].src if relayed else BCAST)
                / IP(src=args.server_ip, dst=gi if relayed else "255.255.255.255")
                / UDP(sport=67, dport=67 if relayed else 68)
                / BOOTP(op=2, chaddr=pkt[BOOTP].chaddr, xid=pkt[BOOTP].xid,
                        yiaddr=yip, siaddr=args.server_ip, giaddr=gi,
                        flags=pkt[BOOTP].flags)
                / DHCP(options=opts))

    def on(pkt):
        now = round(time.time() - t0, 4)
        if ARP in pkt and pkt[ARP].op == 1 and pkt[ARP].pdst in arp_for:
            sendp(Ether(src=my_mac, dst=pkt[Ether].src)
                  / ARP(op=2, hwsrc=my_mac, psrc=pkt[ARP].pdst,
                        hwdst=pkt[ARP].hwsrc, pdst=pkt[ARP].psrc),
                  iface=iface, verbose=0)
            log.append({"t": now, "ev": "arp-reply", "for": pkt[ARP].pdst})
            return
        if BOOTP not in pkt or DHCP not in pkt or pkt[BOOTP].op != 1:
            return
        mt = msgtype_of(pkt)
        chaddr = str2mac(pkt[BOOTP].chaddr[:6])
        rec = summarize(pkt)
        rec["t"] = now
        log.append(rec)
        if mt == "DISCOVER":
            yip = leased.get(chaddr) or next((a for a in addrs if a not in leased.values()), None)
            if yip:
                leased[chaddr] = yip
                sendp(reply(pkt, 2, yip), iface=iface, verbose=0)
                log.append({"t": now, "ev": "OFFER-sent", "chaddr": chaddr, "yiaddr": yip})
        elif mt == "REQUEST":
            yip = leased.get(chaddr) or addrs[0]
            sendp(reply(pkt, 5, yip), iface=iface, verbose=0)
            log.append({"t": now, "ev": "ACK-sent", "chaddr": chaddr, "yiaddr": yip})

    print("dhcp4 server on %s: pool %s-%s (%d), server-id %s, lease %ds, ARP for %s"
          % (iface, args.pool_start, args.pool_end, len(addrs), args.server_ip,
             args.lease, ",".join(sorted(arp_for))), file=sys.stderr)
    sniffer = AsyncSniffer(iface=iface, filter=BPF, prn=on, store=bool(args.pcap))
    sniffer.start()
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        pass
    sniffer.stop()
    if args.pcap and sniffer.results:
        wrpcap(args.pcap, sniffer.results)
    out = {"leased": leased, "events": log}
    print(json.dumps(out, indent=2, default=str))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=2, default=str)
    return 0


# ---------------------------------------------------------------- decode

def cmd_decode(args):
    total = {"dhcp": 0, "arp": 0}
    bytype, frames = {}, []
    for path in args.pcap:
        for pkt in rdpcap(path):
            if BOOTP in pkt and DHCP in pkt:
                total["dhcp"] += 1
                s = summarize(pkt)
                bytype[s["type"]] = bytype.get(s["type"], 0) + 1
                if args.chaddr and s["chaddr"].lower() != args.chaddr.lower():
                    continue
                frames.append(s)
            elif ARP in pkt:
                total["arp"] += 1
                if args.arp:
                    frames.append({"type": "ARP-%s" % ("req" if pkt[ARP].op == 1 else "rep"),
                                   "target": pkt[ARP].pdst, "sender_ip": pkt[ARP].psrc,
                                   "sender_mac": pkt[ARP].hwsrc})
    print(json.dumps({"counts": total, "by_type": bytype, "frames": frames},
                     indent=2, default=str))
    return 0


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("client", help="send DISCOVER/REQUEST, watch ARP probes")
    c.add_argument("iface")
    c.add_argument("--mac", help="client hardware address (default: random 02:*)")
    c.add_argument("--src-mac", help="Ethernet source, if different from chaddr")
    c.add_argument("--dst-mac", help="Ethernet destination (default broadcast)")
    c.add_argument("--xid", type=lambda x: int(x, 0))
    c.add_argument("--count", type=int, default=1,
                   help="identical DISCOVER retransmits per client")
    c.add_argument("--clients", type=int, default=1,
                   help="distinct clients in ONE process (MAC and xid increment per client)")
    c.add_argument("--gap", type=float, default=0.0, help="seconds between clients")
    c.add_argument("--client-id", help="option 61: a MAC, 'hex:..' or an ASCII string")
    c.add_argument("--hostname", help="option 12")
    c.add_argument("--prl", help="option 55 parameter request list, e.g. 1,3,6,51")
    c.add_argument("--option82", help="'circuit:<s>,remote:<s>' or 'hex:<bytes>'")
    c.add_argument("--giaddr", help="relay-agent source address (makes it a relayed frame)")
    c.add_argument("--hops", type=int, default=0)
    c.add_argument("--server-ip", default="255.255.255.255", help="unicast target when relayed")
    c.add_argument("--broadcast", action="store_true", help="set the BOOTP broadcast flag")
    c.add_argument("--arp-answer", help="answer ARP requests for these IPs (comma list)")
    c.add_argument("--arp-watch", help="only record ARP/ICMP for targets in this prefix")
    c.add_argument("--icmp-answer", help="answer ICMP echo probes for these IPs (comma list)")
    c.add_argument("--discover-only", action="store_true")
    c.add_argument("--wait", type=float, default=12.0)
    c.add_argument("--pcap")
    c.add_argument("--json")
    c.set_defaults(fn=cmd_client)

    s = sub.add_parser("server", help="minimal DHCP server + ARP responder")
    s.add_argument("iface")
    s.add_argument("--server-ip", required=True)
    s.add_argument("--pool-start", required=True)
    s.add_argument("--pool-end", required=True)
    s.add_argument("--mask", default="255.255.255.0")
    s.add_argument("--router")
    s.add_argument("--dns")
    s.add_argument("--lease", type=int, default=3600)
    s.add_argument("--arp-for", help="IPs to answer ARP for (default: --server-ip)")
    s.add_argument("--echo-option82", action="store_true", help="echo option 82 (RFC 3046)")
    s.add_argument("--option82-override",
                   help="return THIS option 82 instead of echoing, to exercise relay "
                        "response-path checking; 'circuit:<s>,remote:<s>' or 'hex:<bytes>'")
    s.add_argument("--duration", type=float, default=60.0)
    s.add_argument("--pcap")
    s.add_argument("--json")
    s.set_defaults(fn=cmd_server)

    d = sub.add_parser("decode", help="count and dump DHCP/ARP frames in a pcap")
    d.add_argument("pcap", nargs="+")
    d.add_argument("--chaddr", help="only show frames for this client MAC")
    d.add_argument("--arp", action="store_true", help="include ARP frames")
    d.set_defaults(fn=cmd_decode)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
