#!/bin/bash
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-client-2026-10-15T1458/T43854/work
cd $S/tools || exit 1
cp $HOME/claude/device-testing/tools/dnsresp.py $S/tools/
echo "### enable DNS forwarding (global, disabled by default)"
python3.8 cfg.py /dev/u2 115200 $S/console-u2.log "configure terminal" "ip dns forwarding" "end" \
  "show ip dns forwarding" > $W/fwd-on.log 2>&1
echo "cfg exit=$?"; grep -n "^% " $W/fwd-on.log || echo "no CLI errors"
sed -n '/show ip dns forwarding/,$p' $W/fwd-on.log | head -14
sleep 4   # dnsmasq restarts on any DNS-relay config change (TFS S1570 Limitations)
echo "### TWO responders on eth4: .9 (static, answers 10.9.9.9) and .2 (DHCP-learned, 10.2.2.2)"
sudo -n timeout 40 /usr/sbin/tcpdump -i eth4 -nn -w $S/cap/order-eth4.pcap -s 400 udp port 53 2>/dev/null &
sudo -n python3.8 dnsresp.py respond eth4 --for 192.168.48.9 --default-answer 10.9.9.9 \
  --ttl 30 --duration 32 --json $S/cap/order-r9.json > $S/cap/order-r9.out 2>$S/cap/order-r9.err &
sudo -n python3.8 dnsresp.py respond eth4 --for 192.168.48.2 --default-answer 10.2.2.2 \
  --ttl 30 --duration 32 --json $S/cap/order-r2.json > $S/cap/order-r2.out 2>$S/cap/order-r2.err &
for i in $(seq 1 25); do grep -q responder $S/cap/order-r2.err 2>/dev/null && grep -q responder $S/cap/order-r9.err 2>/dev/null && break; sleep 1; done
sleep 2
echo "--- one query from eth3 to the DUT's vlan10 SVI ---"
sudo -n python3.8 dnsresp.py query eth3 --server 192.168.10.1 --server-mac e0:1a:ea:d4:70:43 \
  --src-ip 192.168.10.50 --name ck-order.test --wait 10 --json $S/cap/order-cli.json \
  > $S/cap/order-cli.out 2>$S/cap/order-cli.err
echo "query exit=$?"
wait
sudo -n chown -R $(id -u):$(id -g) $S/cap; cp $S/cap/order-* $W/ 2>/dev/null
echo "=== WHO WAS QUERIED, and when (the discriminator) ==="
grep -E "UPSTREAM QUERIES|t=" $S/cap/order-r9.err | sed 's/^/  .9 static : /'
grep -E "UPSTREAM QUERIES|t=" $S/cap/order-r2.err | sed 's/^/  .2 dynamic: /'
echo "=== tcpdump on eth4, authoritative for the wire ==="
sudo -n /usr/sbin/tcpdump -r $S/cap/order-eth4.pcap -nn 2>/dev/null | head -8
echo "=== what came back to the querying host ==="
grep -E "QUERIES SENT|->" $S/cap/order-cli.err
