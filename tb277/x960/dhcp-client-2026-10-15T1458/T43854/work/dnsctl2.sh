#!/bin/bash
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-client-2026-10-15T1458/T43854/work
cd $S/tools || exit 1
python3.8 ckcon.py /dev/u2 115200 $S/console-u2.log "show ip dns forwarding" "show ip name-server" "show arp" > $W/ctl2-state.log 2>&1
sed -n '/show ip dns forwarding/,/show arp/p' $W/ctl2-state.log
grep -E "192.168.48" $W/ctl2-state.log | head -4
echo "### settled 20 s, then THREE queries 3 s apart"
sleep 20
sudo -n timeout 40 /usr/sbin/tcpdump -i eth4 -nn -w $S/cap/ctl2-eth4.pcap -s 400 udp port 53 or arp 2>/dev/null &
sudo -n python3.8 dnsresp.py respond eth4 --for 192.168.48.9 --default-answer 10.9.9.9 \
  --ttl 30 --duration 32 --json $S/cap/ctl2-r9.json > $S/cap/ctl2-r9.out 2>$S/cap/ctl2-r9.err &
for i in $(seq 1 25); do grep -q responder $S/cap/ctl2-r9.err 2>/dev/null && break; sleep 1; done
sleep 2
sudo -n python3.8 dnsresp.py query eth3 --server 192.168.10.1 --server-mac e0:1a:ea:d4:70:43 \
  --src-ip 192.168.10.50 --name ck-a.test --name ck-b.test --count 3 --gap 3 --wait 10 \
  --json $S/cap/ctl2-cli.json > $S/cap/ctl2-cli.out 2>$S/cap/ctl2-cli.err
wait
sudo -n chown -R $(id -u):$(id -g) $S/cap; cp $S/cap/ctl2-* $W/ 2>/dev/null
echo "  .9 static : $(grep 'UPSTREAM QUERIES' $S/cap/ctl2-r9.err)"
echo "--- eth4 wire ---"; sudo -n /usr/sbin/tcpdump -r $S/cap/ctl2-eth4.pcap -nn 2>/dev/null | head -8
echo "--- client ---"; grep -E "QUERIES SENT" $S/cap/ctl2-cli.err
