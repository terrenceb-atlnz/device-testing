#!/bin/bash
# $1=label  $2=client MAC base  $3..=extra client args
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-relay-2026-10-15T1458/T43852/work
LBL=$1; MACBASE=$2; shift 2
mkdir -p $S/cap $W; cd $S/tools || exit 1
cp $HOME/claude/device-testing/tools/dhcp4.py $S/tools/dhcp4.py
sudo -n timeout 45 /usr/sbin/tcpdump -i eth3 -nn -w $S/cap/$LBL-eth3.pcap -s 400 udp port 67 or udp port 68 2>/dev/null &
sudo -n timeout 45 /usr/sbin/tcpdump -i eth4 -nn -w $S/cap/$LBL-eth4.pcap -s 400 udp port 67 2>/dev/null &
sudo -n python3.8 dhcp4.py server eth4 --server-ip 192.168.48.2 --pool-start 192.168.10.100 \
  --pool-end 192.168.10.110 --mask 255.255.255.0 --router 192.168.10.1 --lease 3600 \
  --echo-option82 --duration 38 --json $S/cap/$LBL-srv.json > $S/cap/$LBL-srv.out 2>$S/cap/$LBL-srv.err &
for i in $(seq 1 25); do grep -q "dhcp4 server on" $S/cap/$LBL-srv.err 2>/dev/null && break; sleep 1; done
sleep 1
sudo -n python3.8 dhcp4.py client eth3 --mac $MACBASE --clients 5 --gap 1 --broadcast \
  --prl 1,3,6,51 --wait 3 "$@" --json $S/cap/$LBL-cli.json > $S/cap/$LBL-cli.out 2>$S/cap/$LBL-cli.err
wait                      # ALL background jobs: both tcpdumps must exit and flush
sudo -n chown -R $(id -u):$(id -g) $S/cap
cp $S/cap/$LBL-* $W/ 2>/dev/null
echo "===== LEG $LBL ====="
grep -E "offers received|acks received" $S/cap/$LBL-cli.err
echo "eth3 DISCOVERs we actually sent : $(sudo -n /usr/sbin/tcpdump -r $S/cap/$LBL-eth3.pcap -nn 2>/dev/null | grep -c 'Request from')"
echo "eth4 DISCOVERs relayed by DUT   : $(sudo -n /usr/sbin/tcpdump -r $S/cap/$LBL-eth4.pcap -nn 2>/dev/null | grep -c 'Request from')"
echo "eth3 replies back to client     : $(sudo -n /usr/sbin/tcpdump -r $S/cap/$LBL-eth3.pcap -nn 2>/dev/null | grep -c 'Reply')"
python3.8 - "$S/cap/$LBL-srv.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
ds=[e for e in d["events"] if e.get("type")=="DISCOVER"]
print("server RECEIVED DISCOVERs on eth4:",len(ds))
for e in ds[:6]:
    print("   giaddr=%-14s hops=%s src=%-14s chaddr=%s" % (e["giaddr"],e["hops"],e["ip_src"],e["chaddr"]))
    if e.get("option82"): print("      option82:",e["option82"])
print("leased:",d["leased"])
PY
