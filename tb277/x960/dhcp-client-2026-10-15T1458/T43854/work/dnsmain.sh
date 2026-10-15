#!/bin/bash
# $1=label  $2=settle seconds
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-client-2026-10-15T1458/T43854/work
LBL=$1; SETTLE=${2:-20}
cd $S/tools || exit 1
sleep $SETTLE
sudo -n timeout 45 /usr/sbin/tcpdump -i eth4 -nn -w $S/cap/$LBL-eth4.pcap -s 400 udp port 53 2>/dev/null &
sudo -n timeout 45 /usr/sbin/tcpdump -i eth3 -nn -w $S/cap/$LBL-eth3.pcap -s 400 udp port 53 2>/dev/null &
sudo -n python3.8 dnsresp.py respond eth4 --for 192.168.48.9 --default-answer 10.9.9.9 \
  --ttl 30 --duration 38 --json $S/cap/$LBL-r9.json > $S/cap/$LBL-r9.out 2>$S/cap/$LBL-r9.err &
for i in $(seq 1 25); do grep -q responder $S/cap/$LBL-r9.err 2>/dev/null && break; sleep 1; done
sleep 2
sudo -n python3.8 dnsresp.py query eth3 --server 192.168.10.1 --server-mac e0:1a:ea:d4:70:43 \
  --src-ip 192.168.10.50 \
  --name ck1.test --name ck2.test --name ck3.test --name ck4.test --name ck5.test \
  --wait 12 --json $S/cap/$LBL-cli.json > $S/cap/$LBL-cli.out 2>$S/cap/$LBL-cli.err
wait
sudo -n chown -R $(id -u):$(id -g) $S/cap; cp $S/cap/$LBL-* $W/ 2>/dev/null
echo "===== LEG $LBL ====="
echo "eth3 DNS frames (queries we sent + answers returned): $(sudo -n /usr/sbin/tcpdump -r $S/cap/$LBL-eth3.pcap -nn 2>/dev/null | wc -l)"
echo "eth4 DNS frames (forwarded upstream + upstream replies): $(sudo -n /usr/sbin/tcpdump -r $S/cap/$LBL-eth4.pcap -nn 2>/dev/null | wc -l)"
echo "upstream queries the DUT FORWARDED: $(sudo -n /usr/sbin/tcpdump -r $S/cap/$LBL-eth4.pcap -nn 2>/dev/null | grep -c 'A?')"
grep 'UPSTREAM QUERIES' $S/cap/$LBL-r9.err
grep -E "QUERIES SENT|->" $S/cap/$LBL-cli.err
