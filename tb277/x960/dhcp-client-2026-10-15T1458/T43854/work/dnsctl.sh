#!/bin/bash
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-client-2026-10-15T1458/T43854/work
cd $S/tools || exit 1
echo "### CONTROL: re-lease with the DHCP server offering NO option 6."
echo "### Same address, same bench -- only the DHCP-learned DNS entry is absent."
sudo -n python3.8 dhcp4.py server eth4 --server-ip 192.168.48.2 --pool-start 192.168.48.100 \
  --pool-end 192.168.48.110 --mask 255.255.255.0 --router 192.168.48.1 \
  --lease 3600 --duration 35 --json $S/cap/nodns-srv.json > $S/cap/nodns-srv.out 2>$S/cap/nodns-srv.err &
for i in $(seq 1 25); do grep -q "dhcp4 server on" $S/cap/nodns-srv.err 2>/dev/null && break; sleep 1; done
sleep 1
python3.8 cfg.py /dev/u2 115200 $S/console-u2.log "configure terminal" "interface vlan48" \
  "no ip address dhcp" "ip address dhcp" "end" > $S/cap/nodns-bounce.log 2>&1
wait
sleep 3
python3.8 ckcon.py /dev/u2 115200 $S/console-u2.log "show ip name-server" "show ip interface brief" > $W/ns-only-static.log 2>&1
echo "--- name servers now (expect ONLY the static .9) ---"
sed -n '/show ip name-server/,/show ip interface/p' $W/ns-only-static.log
grep -E "vlan48 " $W/ns-only-static.log | tail -1
sleep 3
echo "### query again -- can the DUT reach and use the STATIC .9 at all?"
sudo -n timeout 30 /usr/sbin/tcpdump -i eth4 -nn -w $S/cap/ctl-eth4.pcap -s 400 udp port 53 2>/dev/null &
sudo -n python3.8 dnsresp.py respond eth4 --for 192.168.48.9 --default-answer 10.9.9.9 \
  --ttl 30 --duration 25 --json $S/cap/ctl-r9.json > $S/cap/ctl-r9.out 2>$S/cap/ctl-r9.err &
sudo -n python3.8 dnsresp.py respond eth4 --for 192.168.48.2 --default-answer 10.2.2.2 \
  --ttl 30 --duration 25 --json $S/cap/ctl-r2.json > $S/cap/ctl-r2.out 2>$S/cap/ctl-r2.err &
for i in $(seq 1 25); do grep -q responder $S/cap/ctl-r9.err 2>/dev/null && break; sleep 1; done
sleep 2
sudo -n python3.8 dnsresp.py query eth3 --server 192.168.10.1 --server-mac e0:1a:ea:d4:70:43 \
  --src-ip 192.168.10.50 --name ck-ctl.test --wait 10 --json $S/cap/ctl-cli.json \
  > $S/cap/ctl-cli.out 2>$S/cap/ctl-cli.err
wait
sudo -n chown -R $(id -u):$(id -g) $S/cap; cp $S/cap/ctl-* $S/cap/nodns-* $W/ 2>/dev/null
echo "  .9 static : $(grep 'UPSTREAM QUERIES' $S/cap/ctl-r9.err)"
echo "  .2 dynamic: $(grep 'UPSTREAM QUERIES' $S/cap/ctl-r2.err)"
sudo -n /usr/sbin/tcpdump -r $S/cap/ctl-eth4.pcap -nn 2>/dev/null | head -4
grep -E "QUERIES SENT|->" $S/cap/ctl-cli.err
