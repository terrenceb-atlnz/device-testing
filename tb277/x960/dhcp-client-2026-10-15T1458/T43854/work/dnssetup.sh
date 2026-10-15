#!/bin/bash
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-client-2026-10-15T1458/T43854/work
mkdir -p $W $S/cap; cd $S/tools || exit 1
cp $HOME/claude/device-testing/tools/dnsresp.py $S/tools/ 2>/dev/null
echo "### BEFORE the lease: a STATIC name-server, so S1570.1.12 ordering is testable"
python3.8 cfg.py /dev/u2 115200 $S/console-u2.log "configure terminal" \
  "ip name-server 192.168.48.9" "end" "show ip name-server" > $W/static-ns.log 2>&1
echo "cfg exit=$?"; grep -n "^% " $W/static-ns.log || echo "no CLI errors"
sed -n '/show ip name-server/,$p' $W/static-ns.log | head -10
echo "### now re-lease so the client LEARNS a DNS server (option 6 = 192.168.48.2)"
bash $S/runlegC.sh dnslease 2>&1 | grep -E "server received|leased|DISCOVER"
echo "### ordering after the lease -- DHCP-learned must be added LAST (S1570.1.12)"
python3.8 ckcon.py /dev/u2 115200 $S/console-u2.log "show ip name-server" "show ip interface brief" > $W/ns-order.log 2>&1
sed -n '/show ip name-server/,/show ip interface/p' $W/ns-order.log
grep -E "vlan48" $W/ns-order.log | tail -1
