#!/bin/bash
# $1=label ; rest = extra args to the scapy server
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-client-2026-10-15T1458/T35370/work
LBL=$1; shift
mkdir -p $S/cap $W; cd $S/tools || exit 1
cp $HOME/claude/device-testing/tools/dhcp4.py $S/tools/dhcp4.py
sudo -n timeout 55 /usr/sbin/tcpdump -i eth4 -nn -w $S/cap/$LBL-eth4.pcap -s 600 udp port 67 or udp port 68 2>/dev/null &
sudo -n python3.8 dhcp4.py server eth4 --server-ip 192.168.48.2 --pool-start 192.168.48.100 \
  --pool-end 192.168.48.110 --mask 255.255.255.0 --router 192.168.48.1 --dns 192.168.48.2 \
  --lease 3600 --duration 50 "$@" --json $S/cap/$LBL-srv.json > $S/cap/$LBL-srv.out 2>$S/cap/$LBL-srv.err &
for i in $(seq 1 25); do grep -q "dhcp4 server on" $S/cap/$LBL-srv.err 2>/dev/null && break; sleep 1; done
sleep 1
# force the DUT's DHCP client to restart its exchange
python3.8 cfg.py /dev/u2 115200 $S/console-u2.log "configure terminal" "interface vlan48" \
  "shutdown" "no shutdown" "end" > $S/cap/$LBL-bounce.log 2>&1
wait
sudo -n chown -R $(id -u):$(id -g) $S/cap
cp $S/cap/$LBL-* $W/ 2>/dev/null
echo "===== LEG $LBL ====="
echo "eth4 DHCP frames (tcpdump): $(sudo -n /usr/sbin/tcpdump -r $S/cap/$LBL-eth4.pcap -nn 2>/dev/null | wc -l)"
python3.8 - "$S/cap/$LBL-srv.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
ds=[e for e in d["events"] if e.get("type") in ("DISCOVER","REQUEST")]
print("server received from the DUT:", len(ds), "frames")
for e in ds[:2]:
    print("  %s  chaddr=%s  ip_src=%s" % (e["type"], e["chaddr"], e["ip_src"]))
    for k,v in sorted(e["options"].items(), key=lambda x: str(x[0])):
        print("      opt %-28s = %s" % (k, v))
print("leased:", d["leased"])
PY
