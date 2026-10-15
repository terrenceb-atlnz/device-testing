#!/bin/bash
# $1=label  $2=client MAC base  $3..=extra client args
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-relay-2026-10-15T1458/T43850/work
LBL=$1; MACBASE=$2; shift 2
mkdir -p $S/cap $W; cd $S/tools || exit 1
cp $HOME/claude/device-testing/tools/dhcp4.py $S/tools/dhcp4.py
sudo -n timeout 45 /usr/sbin/tcpdump -i eth4 -nn -w $S/cap/$LBL-eth4.pcap -s 400 udp port 67 2>/dev/null &
sudo -n python3.8 dhcp4.py server eth4 --server-ip 192.168.48.2 --pool-start 192.168.10.100 \
  --pool-end 192.168.10.110 --mask 255.255.255.0 --router 192.168.10.1 --lease 3600 \
  --echo-option82 --duration 38 --json $S/cap/$LBL-srv.json > $S/cap/$LBL-srv.out 2>$S/cap/$LBL-srv.err &
for i in $(seq 1 25); do grep -q "dhcp4 server on" $S/cap/$LBL-srv.err 2>/dev/null && break; sleep 1; done
sleep 1
sudo -n python3.8 dhcp4.py client eth3 --mac $MACBASE --clients 3 --gap 1 --broadcast \
  --prl 1,3,6,51 --wait 3 "$@" --json $S/cap/$LBL-cli.json > $S/cap/$LBL-cli.out 2>$S/cap/$LBL-cli.err
wait
sudo -n chown -R $(id -u):$(id -g) $S/cap
cp $S/cap/$LBL-* $W/ 2>/dev/null
echo "===== LEG $LBL ====="
grep -E "offers received|acks received" $S/cap/$LBL-cli.err
echo "eth4 frames relayed by DUT: $(sudo -n /usr/sbin/tcpdump -r $S/cap/$LBL-eth4.pcap -nn 2>/dev/null | grep -c 'Request from')"
python3.8 - "$S/cap/$LBL-srv.json" "$S/cap/$LBL-cli.json" <<'PY'
import json,sys
srv=json.load(open(sys.argv[1])); cli=json.load(open(sys.argv[2]))
ds=[e for e in srv["events"] if e.get("type")=="DISCOVER"]
print("SERVER side -- relayed DISCOVERs arriving on eth4:",len(ds))
for e in ds[:3]:
    o=e.get("option82")
    if o is None:
        print("   chaddr=%s giaddr=%s  option82: ABSENT" % (e["chaddr"],e["giaddr"]))
    else:
        print("   chaddr=%s giaddr=%s" % (e["chaddr"],e["giaddr"]))
        print("      circuit_id=%s  remote_id=%s  raw=%s"
              % (o.get("circuit_id"),o.get("remote_id"),o["raw"]))
print("CLIENT side -- option 82 in the OFFER delivered back to the client:")
for t in cli.get("transactions",[]):
    f=t.get("offer_frame")
    if not f: print("   %s -> no OFFER" % t["chaddr"]); continue
    print("   %s -> OFFER %s  option82: %s"
          % (t["chaddr"], t["offer"], f.get("option82") or "ABSENT (stripped)"))
PY
