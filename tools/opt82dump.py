import sys
from scapy.all import rdpcap, BOOTP, DHCP, UDP, bind_layers
bind_layers(UDP, BOOTP, dport=67); bind_layers(UDP, BOOTP, dport=68)
for path in sys.argv[1:]:
    print("==", path)
    for pkt in rdpcap(path):
        if BOOTP not in pkt or DHCP not in pkt or pkt[BOOTP].op != 1:
            continue
        opts = [o for o in pkt[DHCP].options if isinstance(o, tuple)]
        o82 = [o for o in opts if o[0] in (82, "relay_agent_information")]
        print("  chaddr", pkt[BOOTP].chaddr[:6].hex(),
              "| option-82 TLVs present:", len(o82))
        for i, o in enumerate(o82):
            raw = o[1]
            print("     [%d] len=%d raw=%s" % (i, len(raw), raw.hex()))
            j = 0
            while j + 2 <= len(raw):
                c, ln = raw[j], raw[j+1]
                print("         sub %d len %d = %r" % (c, ln, raw[j+2:j+2+ln]))
                j += 2 + ln
        break
