#!/usr/bin/env python3
"""lldpwire.py -- decode the LLDP frames in a `tcpdump -w` pcap, in pure Python.

Why it exists.  A verdict on LLDP cannot come from `show lldp neighbors`: that table is the
device's own answer about itself, and `platforms/x960.md` §5 records this very platform
reporting a feature Enabled while the dataplane did nothing.  What settles an LLDP case is the
frames on the wire -- how many, how far apart, from which chassis, and which TLVs they carry.
This decodes exactly that, so an on/off/removed arc is graded on packets (STANDING-ORDERS §7).

It is the counterpart to `lldpmed_phone.py`, which SENDS an LLDP-MED endpoint: this one reads
what the switch sent back.

What it prints, per source MAC:
  * frame count, first/last timestamp, and the inter-frame gaps (min/mean/max) -- which is how
    you see a Tx Timer change, and how you see LLDP-MED fast start (three ~1 s frames where
    the steady state is 30 s);
  * the decoded TLVs of the most recent frame (--tlv prints every frame);
  * mandatory-TLV and TTL checks, so a malformed advertisement is visible.

It knows the base TLVs (chassis, port, TTL, port/system description, capabilities, management
address) and the organisationally-specific sets for IEEE 802.1, IEEE 802.3 and TIA LLDP-MED,
including the Network Policy TLV that a voice-VLAN case turns on.

No scapy: the pcap reader is `tcpflow.py`'s, so this runs anywhere Python does.

Usage:
  lldpwire.py <file.pcap> [--src MAC] [--tlv] [--quiet] [--expect-med] [--json]

  --src MAC       only frames from this source MAC (accepts 00:11:.., 0011.2233.4455, bare hex)
  --tlv           print the decoded TLVs of EVERY frame, not just the latest per source
  --expect-med    exit 1 unless at least one frame carried an LLDP-MED TLV
  --quiet         counts and timing only, no TLV decode
  --json          machine-readable summary on stdout instead of the report

Exit: 0 if at least one LLDP frame was found (and --expect-med satisfied), 1 if not,
      2 on a usage or format error.
"""

import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tcpflow import read_pcap                                    # noqa: E402

LLDP_ETHERTYPE = 0x88CC
LLDP_GROUP_MACS = {"01:80:c2:00:00:0e", "01:80:c2:00:00:03", "01:80:c2:00:00:00"}

TLV_END = 0
TLV_CHASSIS_ID = 1
TLV_PORT_ID = 2
TLV_TTL = 3
TLV_PORT_DESC = 4
TLV_SYS_NAME = 5
TLV_SYS_DESC = 6
TLV_SYS_CAP = 7
TLV_MGMT_ADDR = 8
TLV_ORG = 127

TLV_NAMES = {
    TLV_END: "End of LLDPDU", TLV_CHASSIS_ID: "Chassis ID", TLV_PORT_ID: "Port ID",
    TLV_TTL: "Time To Live", TLV_PORT_DESC: "Port Description", TLV_SYS_NAME: "System Name",
    TLV_SYS_DESC: "System Description", TLV_SYS_CAP: "System Capabilities",
    TLV_MGMT_ADDR: "Management Address", TLV_ORG: "Organizationally Specific",
}

CHASSIS_SUBTYPE = {1: "Chassis component", 2: "Interface alias", 3: "Port component",
                   4: "MAC address", 5: "Network address", 6: "Interface name",
                   7: "Locally assigned"}
PORT_SUBTYPE = {1: "Interface alias", 2: "Port component", 3: "MAC address",
                4: "Network address", 5: "Interface name", 6: "Agent circuit ID",
                7: "Locally assigned"}

CAP_BITS = [(0x01, "Other"), (0x02, "Repeater"), (0x04, "Bridge"), (0x08, "WLAN AP"),
            (0x10, "Router"), (0x20, "Telephone"), (0x40, "DOCSIS cable device"),
            (0x80, "Station only"), (0x100, "C-VLAN"), (0x200, "S-VLAN"),
            (0x400, "Two-port MAC relay")]

OUI_8021 = b"\x00\x80\xc2"
OUI_8023 = b"\x00\x12\x0f"
OUI_MED = b"\x00\x12\xbb"

SUB_8021 = {1: "Port VLAN ID", 2: "Port and Protocol VLAN ID", 3: "VLAN Name",
            4: "Protocol Identity", 8: "Congestion Notification", 9: "ETS Configuration"}
SUB_8023 = {1: "MAC/PHY Configuration/Status", 2: "Power Via MDI", 3: "Link Aggregation",
            4: "Maximum Frame Size"}
SUB_MED = {1: "LLDP-MED Capabilities", 2: "Network Policy", 3: "Location Identification",
           4: "Extended Power-via-MDI", 5: "Inventory - Hardware Revision",
           6: "Inventory - Firmware Revision", 7: "Inventory - Software Revision",
           8: "Inventory - Serial Number", 9: "Inventory - Manufacturer Name",
           10: "Inventory - Model Name", 11: "Inventory - Asset ID"}

MED_DEVICE_TYPE = {0: "Not Defined", 1: "Endpoint Class I", 2: "Endpoint Class II",
                   3: "Endpoint Class III", 4: "Network Connectivity"}
MED_CAP_BITS = [(0x01, "Capabilities"), (0x02, "Network Policy"), (0x04, "Location ID"),
                (0x08, "Extended Power via MDI-PSE"), (0x10, "Extended Power via MDI-PD"),
                (0x20, "Inventory")]
MED_APP_TYPE = {1: "Voice", 2: "Voice Signaling", 3: "Guest Voice",
                4: "Guest Voice Signaling", 5: "Softphone Voice", 6: "Video Conferencing",
                7: "Streaming Video", 8: "Video Signaling"}


def mac_str(raw):
    return ":".join("%02x" % b for b in raw)


def norm_mac(text):
    """Accept 00:11:22:33:44:55, 0011.2233.4455 or bare hex; return the colon form."""
    hexes = "".join(c for c in text.lower() if c in "0123456789abcdef")
    if len(hexes) != 12:
        raise ValueError("not a MAC address: %r" % text)
    return ":".join(hexes[i:i + 2] for i in range(0, 12, 2))


def ether_lldp(data):
    """Return (src_mac, dst_mac, vlan, lldpdu) for an LLDP frame, else None.

    The VLAN id is the outer 802.1Q tag when the frame carried one, else None -- an
    LLDP-MED voice-VLAN case needs to know whether the advertisement itself was tagged.
    """
    if len(data) < 14:
        return None
    dst, src = data[0:6], data[6:12]
    et = struct.unpack("!H", data[12:14])[0]
    off, vlan = 14, None
    while et in (0x8100, 0x88a8, 0x9100) and len(data) >= off + 4:
        tci = struct.unpack("!H", data[off:off + 2])[0]
        if vlan is None:
            vlan = tci & 0x0FFF
        et = struct.unpack("!H", data[off + 2:off + 4])[0]
        off += 4
    if et != LLDP_ETHERTYPE:
        return None
    return mac_str(src), mac_str(dst), vlan, data[off:]


def parse_tlvs(pdu):
    """Yield (tlv_type, value_bytes). Stops at End-of-LLDPDU or a truncated TLV."""
    i = 0
    while i + 2 <= len(pdu):
        head = struct.unpack("!H", pdu[i:i + 2])[0]
        ttype, tlen = head >> 9, head & 0x01FF
        i += 2
        if ttype == TLV_END:
            return
        if i + tlen > len(pdu):
            return
        yield ttype, pdu[i:i + tlen]
        i += tlen


def _text(raw):
    return raw.decode("utf-8", "replace").rstrip("\x00")


def _id_value(subtype, raw, names):
    label = names.get(subtype, "subtype %d" % subtype)
    if subtype == 4 and len(raw) == 6 and names is CHASSIS_SUBTYPE:
        return label, mac_str(raw)
    if subtype == 3 and len(raw) == 6 and names is PORT_SUBTYPE:
        return label, mac_str(raw)
    if subtype == 5 and names is CHASSIS_SUBTYPE:
        return label, _network_address(raw)
    return label, _text(raw)


def _network_address(raw):
    if not raw:
        return ""
    fam, rest = raw[0], raw[1:]
    if fam == 1 and len(rest) >= 4:
        return ".".join(str(b) for b in rest[:4])
    if fam == 2 and len(rest) >= 16:
        return ":".join("%02x%02x" % (rest[i], rest[i + 1]) for i in range(0, 16, 2))
    return "family %d %s" % (fam, rest.hex())


def _caps(value):
    if len(value) < 4:
        return "(short)"
    supported, enabled = struct.unpack("!HH", value[:4])
    sup = [n for b, n in CAP_BITS if supported & b]
    ena = [n for b, n in CAP_BITS if enabled & b]
    return "supported=[%s] enabled=[%s]" % (", ".join(sup) or "-", ", ".join(ena) or "-")


def _mgmt_addr(value):
    if len(value) < 2:
        return "(short)"
    alen = value[0]
    addr = value[1:1 + alen]
    out = _network_address(addr)
    rest = value[1 + alen:]
    if len(rest) >= 5:
        iface_sub, iface_num = rest[0], struct.unpack("!I", rest[1:5])[0]
        kind = {1: "unknown", 2: "ifIndex", 3: "system port number"}.get(iface_sub, str(iface_sub))
        out += "  (interface %s %d)" % (kind, iface_num)
    return out


def _network_policy(info):
    """TIA-1057 Network Policy: app type, U/T/X flags, 12-bit VLAN, 3-bit priority, 6-bit DSCP."""
    if len(info) < 4:
        return {"raw": info.hex()}
    app = info[0]
    bits = (info[1] << 16) | (info[2] << 8) | info[3]
    return {
        "application": MED_APP_TYPE.get(app, "app type %d" % app),
        "unknown_policy": bool(bits & (1 << 23)),
        "tagged": bool(bits & (1 << 22)),
        "vlan": (bits >> 9) & 0x0FFF,
        "l2_priority": (bits >> 6) & 0x07,
        "dscp": bits & 0x3F,
    }


def _med_caps(info):
    if len(info) < 3:
        return "(short)"
    caps = struct.unpack("!H", info[:2])[0]
    names = [n for b, n in MED_CAP_BITS if caps & b]
    return "caps=[%s] device type=%s" % (", ".join(names) or "-",
                                         MED_DEVICE_TYPE.get(info[2], str(info[2])))


def decode_org(value):
    """Return (family, label, rendered) for an organizationally-specific TLV."""
    if len(value) < 4:
        return "?", "(short)", value.hex()
    oui, sub, info = value[:3], value[3], value[4:]
    if oui == OUI_MED:
        label = SUB_MED.get(sub, "MED subtype %d" % sub)
        if sub == 1:
            return "MED", label, _med_caps(info)
        if sub == 2:
            p = _network_policy(info)
            if "raw" in p:
                return "MED", label, p["raw"]
            return "MED", label, ("application=%s vlan=%d tagged=%s priority=%d dscp=%d "
                                  "unknown_policy=%s"
                                  % (p["application"], p["vlan"], p["tagged"],
                                     p["l2_priority"], p["dscp"], p["unknown_policy"]))
        if 5 <= sub <= 11:
            return "MED", label, _text(info)
        return "MED", label, info.hex()
    if oui == OUI_8021:
        label = SUB_8021.get(sub, "802.1 subtype %d" % sub)
        if sub == 1 and len(info) >= 2:
            return "802.1", label, str(struct.unpack("!H", info[:2])[0])
        if sub == 3 and len(info) >= 4:
            return "802.1", label, "vlan %d name %s" % (struct.unpack("!H", info[:2])[0],
                                                        _text(info[3:3 + info[2]]))
        return "802.1", label, info.hex()
    if oui == OUI_8023:
        label = SUB_8023.get(sub, "802.3 subtype %d" % sub)
        if sub == 4 and len(info) >= 2:
            return "802.3", label, str(struct.unpack("!H", info[:2])[0])
        if sub == 3 and len(info) >= 5:
            return "802.3", label, "status=0x%02x port=%d" % (info[0],
                                                              struct.unpack("!I", info[1:5])[0])
        return "802.3", label, info.hex()
    return "OUI " + oui.hex(), "subtype %d" % sub, info.hex()


def decode_frame(pdu):
    """Return an ordered list of (label, rendered) plus a dict of the fields a case grades on."""
    rows, fields = [], {"med": False, "org": []}
    for ttype, value in parse_tlvs(pdu):
        if ttype == TLV_CHASSIS_ID and value:
            label, text = _id_value(value[0], value[1:], CHASSIS_SUBTYPE)
            rows.append(("Chassis ID", "%s: %s" % (label, text)))
            fields["chassis_id"] = text
            fields["chassis_subtype"] = label
        elif ttype == TLV_PORT_ID and value:
            label, text = _id_value(value[0], value[1:], PORT_SUBTYPE)
            rows.append(("Port ID", "%s: %s" % (label, text)))
            fields["port_id"] = text
            fields["port_subtype"] = label
        elif ttype == TLV_TTL and len(value) >= 2:
            ttl = struct.unpack("!H", value[:2])[0]
            rows.append(("Time To Live", "%d s" % ttl))
            fields["ttl"] = ttl
        elif ttype == TLV_PORT_DESC:
            rows.append(("Port Description", _text(value)))
            fields["port_desc"] = _text(value)
        elif ttype == TLV_SYS_NAME:
            rows.append(("System Name", _text(value)))
            fields["sys_name"] = _text(value)
        elif ttype == TLV_SYS_DESC:
            rows.append(("System Description", _text(value)))
            fields["sys_desc"] = _text(value)
        elif ttype == TLV_SYS_CAP:
            rows.append(("System Capabilities", _caps(value)))
            fields["sys_cap"] = _caps(value)
        elif ttype == TLV_MGMT_ADDR:
            rows.append(("Management Address", _mgmt_addr(value)))
            fields.setdefault("mgmt_addrs", []).append(_mgmt_addr(value))
        elif ttype == TLV_ORG:
            family, label, text = decode_org(value)
            rows.append(("%s %s" % (family, label), text))
            fields["org"].append((family, label, text))
            if family == "MED":
                fields["med"] = True
                if label == "Network Policy":
                    fields["network_policy"] = text
        else:
            rows.append((TLV_NAMES.get(ttype, "TLV type %d" % ttype), value.hex()))
    fields["tlv_types"] = [t for t, _ in parse_tlvs(pdu)]
    return rows, fields


def gaps(times):
    if len(times) < 2:
        return None
    d = [b - a for a, b in zip(times, times[1:])]
    return min(d), sum(d) / len(d), max(d)


def main(argv=None):
    ap = argparse.ArgumentParser(description="decode the LLDP frames in a pcap")
    ap.add_argument("pcap")
    ap.add_argument("--src", help="only frames from this source MAC")
    ap.add_argument("--tlv", action="store_true", help="decode EVERY frame, not just the latest")
    ap.add_argument("--quiet", action="store_true", help="counts and timing only")
    ap.add_argument("--expect-med", action="store_true", help="exit 1 unless a MED TLV was seen")
    ap.add_argument("--json", action="store_true", help="machine-readable summary")
    args = ap.parse_args(argv)

    want = None
    if args.src:
        try:
            want = norm_mac(args.src)
        except ValueError as e:
            print("lldpwire: %s" % e, file=sys.stderr)
            return 2
    try:
        packets = list(read_pcap(args.pcap))
    except (OSError, ValueError) as e:
        print("lldpwire: %s" % e, file=sys.stderr)
        return 2

    by_src, total, any_med = {}, 0, False
    for ts, linktype, data in packets:
        if linktype != 1:                      # Ethernet only: LLDP is a link-layer protocol
            continue
        got = ether_lldp(data)
        if not got:
            continue
        src, dst, vlan, pdu = got
        if want and src != want:
            continue
        total += 1
        rec = by_src.setdefault(src, {"times": [], "dst": set(), "vlans": set(), "frames": []})
        rec["times"].append(ts)
        rec["dst"].add(dst)
        rec["vlans"].add(vlan)
        rec["frames"].append((ts, pdu))

    if args.json:
        out = {"pcap": args.pcap, "lldp_frames": total, "sources": {}}
        for src, rec in sorted(by_src.items()):
            _, fields = decode_frame(rec["frames"][-1][1])
            g = gaps(rec["times"])
            out["sources"][src] = {
                "frames": len(rec["times"]),
                "first": rec["times"][0], "last": rec["times"][-1],
                "gap_min": g and round(g[0], 3), "gap_mean": g and round(g[1], 3),
                "gap_max": g and round(g[2], 3),
                "vlans": sorted(v for v in rec["vlans"] if v is not None),
                "chassis_id": fields.get("chassis_id"), "port_id": fields.get("port_id"),
                "ttl": fields.get("ttl"), "sys_name": fields.get("sys_name"),
                "med": fields.get("med"), "network_policy": fields.get("network_policy"),
            }
            any_med = any_med or fields.get("med")
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print("pcap      %s" % args.pcap)
        print("packets   %d total, %d LLDP%s" % (len(packets), total,
                                                 " from %s" % want if want else ""))
        print()
        if not total:
            print("NO LLDP FRAMES -- nothing was transmitted, or the capture missed them.")
        for src, rec in sorted(by_src.items()):
            g = gaps(rec["times"])
            span = rec["times"][-1] - rec["times"][0]
            print("source %s -> %s" % (src, ", ".join(sorted(rec["dst"]))))
            print("  frames %d over %.1f s" % (len(rec["times"]), span))
            if g:
                print("  inter-frame gap  min %.2f s  mean %.2f s  max %.2f s" % g)
            tagged = sorted(v for v in rec["vlans"] if v is not None)
            print("  vlan tags        %s" % (", ".join(str(v) for v in tagged)
                                             if tagged else "untagged"))
            if args.quiet:
                print()
                continue
            frames = rec["frames"] if args.tlv else rec["frames"][-1:]
            for ts, pdu in frames:
                rows, fields = decode_frame(pdu)
                any_med = any_med or fields.get("med")
                print("  --- frame at %.3f, %d TLVs ---" % (ts, len(rows)))
                for label, text in rows:
                    print("    %-34s %s" % (label, text))
                missing = [n for t, n in ((TLV_CHASSIS_ID, "Chassis ID"), (TLV_PORT_ID, "Port ID"),
                                          (TLV_TTL, "Time To Live"))
                           if t not in fields["tlv_types"]]
                if missing:
                    print("    !! MANDATORY TLV MISSING: %s" % ", ".join(missing))
            print()

    if args.expect_med and not any_med:
        print("EXPECT-MED FAILED: no LLDP-MED TLV in any frame", file=sys.stderr)
        return 1
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
