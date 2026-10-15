#!/bin/bash
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-client-2026-10-15T1458/T43854/work
cd $S/tools || exit 1
python3.8 cfg.py /dev/u2 115200 $S/console-u2.log "configure terminal" "ip dns forwarding" \
  "ip dns forwarding cache size 100 time 60" "end" "show ip dns forwarding" > $W/cache-cfg.log 2>&1
echo "cfg exit=$?"; grep -n "^% " $W/cache-cfg.log || echo "no CLI errors"
sed -n '/show ip dns forwarding/,$p' $W/cache-cfg.log | head -10
sleep 20
sudo -n timeout 60 /usr/sbin/tcpdump -i eth4 -nn -w $S/cap/cache-eth4.pcap -s 400 udp port 53 2>/dev/null &
sudo -n python3.8 dnsresp.py respond eth4 --for 192.168.48.9 --default-answer 10.9.9.9 \
  --ttl 60 --duration 52 --json $S/cap/cache-r9.json > $S/cap/cache-r9.out 2>$S/cap/cache-r9.err &
for i in $(seq 1 25); do grep -q responder $S/cap/cache-r9.err 2>/dev/null && break; sleep 1; done
sleep 2
echo "--- round 1: first ever query for ck-cache.test ---"
sudo -n python3.8 dnsresp.py query eth3 --server 192.168.10.1 --server-mac e0:1a:ea:d4:70:43 \
  --src-ip 192.168.10.50 --name ck-cache.test --base-id 0x7100 --wait 10 \
  --json $S/cap/cache-q1.json > /dev/null 2>$S/cap/cache-q1.err
grep -E "QUERIES SENT|->" $S/cap/cache-q1.err
U1=$(sudo -n /usr/sbin/tcpdump -r $S/cap/cache-eth4.pcap -nn 2>/dev/null | grep -c 'A?')
echo "  upstream queries so far: $U1"
echo "--- round 2: SAME name again, within the 60 s TTL ---"
sudo -n python3.8 dnsresp.py query eth3 --server 192.168.10.1 --server-mac e0:1a:ea:d4:70:43 \
  --src-ip 192.168.10.50 --name ck-cache.test --base-id 0x7200 --wait 10 \
  --json $S/cap/cache-q2.json > /dev/null 2>$S/cap/cache-q2.err
grep -E "QUERIES SENT|->" $S/cap/cache-q2.err
wait
sudo -n chown -R $(id -u):$(id -g) $S/cap; cp $S/cap/cache-* $W/ 2>/dev/null
echo "=== totals ==="
echo "upstream queries for ck-cache.test over BOTH rounds: $(sudo -n /usr/sbin/tcpdump -r $S/cap/cache-eth4.pcap -nn 2>/dev/null | grep -c 'A?')"
grep 'UPSTREAM QUERIES' $S/cap/cache-r9.err
sudo -n /usr/sbin/tcpdump -r $S/cap/cache-eth4.pcap -nn 2>/dev/null
