#!/bin/bash
# T18252 teardown: DUT back to the group's idle isolation state, x230 and SA back to theirs.
cd /tmp/ckvlan
set -o pipefail
echo "### $(date +%T) DUT (u5) teardown"
python3 ckcon.py /dev/u5 115200 /tmp/ckvlan/console-u5.log --stop-on-error "configure terminal" \
 "interface port3.0.13" "no vlan classifier activate 1" \
 "interface port1.0.2" "no vlan classifier activate 1" "switchport mode access" "switchport access vlan 3991" \
 "interface port1.0.9" "switchport access vlan 3992" \
 "interface port1.0.13" "switchport access vlan 3993" \
 "interface port4.0.9" "switchport mode access" "switchport access vlan 3994" "exit" \
 "no vlan classifier group 1" "no vlan classifier rule 1" "no vlan classifier rule 2" "no vlan classifier rule 3" "no vlan classifier rule 4" \
 "vlan database" "no vlan 210" "no vlan 220" "end" \
 "show vlan classifier rule" "show vlan classifier group" "show vlan classifier interface group" "show vlan brief | include 210|220|399" \
 "show interface status | include 1.0.2 |1.0.9 |1.0.13 |4.0.9 |3.0.13 " || { echo DUT-TEARDOWN-FAILED; exit 2; }
echo "### $(date +%T) x230 (u0) teardown"
python3 ckcon.py /dev/u0 9600 /tmp/ckvlan/console-u0.log --stop-on-error "configure terminal" \
 "interface port1.0.3" "switchport mode access" "switchport access vlan 3991" \
 "interface port1.0.1" "switchport mode access" "switchport access vlan 100" "exit" \
 "vlan database" "no vlan 210" "no vlan 220" "end" "show vlan brief" || { echo X230-TEARDOWN-FAILED; exit 2; }
echo "### $(date +%T) SA (u3) teardown"
python3 ckcon.py /dev/u3 115200 /tmp/ckvlan/console-u3.log --stop-on-error "configure terminal" \
 "interface port1.0.2" "no switchport access vlan" "end" "show vlan brief | include 399|^1 " || { echo SA-TEARDOWN-FAILED; exit 2; }
echo "### $(date +%T) post-case running-configs"
python3 ckcon.py /dev/u5 115200 /tmp/ckvlan/console-u5.log "show running-config" | sed 1d > post-18252-u5.runcfg
python3 ckcon.py /dev/u0 9600 /tmp/ckvlan/console-u0.log "show running-config" | sed 1d > post-18252-u0.runcfg
python3 ckcon.py /dev/u3 115200 /tmp/ckvlan/console-u3.log "show running-config" | sed 1d > post-18252-u3.runcfg
wc -l post-18252-*.runcfg
