#!/bin/bash
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-client-2026-10-15T1458/T43854/work
cd $S/tools || exit 1
echo "### 1. drop the DHCP client so the dynamic entry goes, leaving ONLY the static"
python3.8 cfg.py /dev/u2 115200 $S/console-u2.log "configure terminal" "interface vlan48" \
  "no ip address dhcp" "end" "show ip name-server" > $W/ns-cleared.log 2>&1
echo "cfg exit=$?"; grep -n "^% " $W/ns-cleared.log || echo "no CLI errors"
sed -n '/show ip name-server/,$p' $W/ns-cleared.log | head -8
echo "### 2. re-apply the client WITH the server running, so DHCP-learned arrives AFTER static"
python3.8 cfg.py /dev/u2 115200 $S/console-u2.log "configure terminal" "interface vlan48" \
  "ip address dhcp" "end" > $W/ns-reapply.log 2>&1
sudo -n timeout 45 /usr/sbin/tcpdump -i eth4 -nn -w $S/cap/nsorder-eth4.pcap -s 600 udp port 67 or udp port 68 2>/dev/null &
sudo -n python3.8 dhcp4.py server eth4 --server-ip 192.168.48.2 --pool-start 192.168.48.100 \
  --pool-end 192.168.48.110 --mask 255.255.255.0 --router 192.168.48.1 --dns 192.168.48.2 \
  --lease 3600 --duration 40 --json $S/cap/nsorder-srv.json > $S/cap/nsorder-srv.out 2>$S/cap/nsorder-srv.err &
for i in $(seq 1 25); do grep -q "dhcp4 server on" $S/cap/nsorder-srv.err 2>/dev/null && break; sleep 1; done
sleep 1
python3.8 cfg.py /dev/u2 115200 $S/console-u2.log "configure terminal" "interface vlan48" \
  "shutdown" "no shutdown" "end" > $S/cap/nsorder-bounce.log 2>&1
wait
sudo -n chown -R $(id -u):$(id -g) $S/cap; cp $S/cap/nsorder-* $W/ 2>/dev/null
echo "### 3. ordering now that DHCP-learned arrived AFTER the static entry"
python3.8 ckcon.py /dev/u2 115200 $S/console-u2.log "show ip name-server" "show ip interface brief" > $W/ns-order2.log 2>&1
sed -n '/show ip name-server/,/show ip interface/p' $W/ns-order2.log
grep -E "vlan48 " $W/ns-order2.log | tail -1
