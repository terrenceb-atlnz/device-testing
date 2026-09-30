#!/bin/bash
# T18302/T18303 stage-0 (feature OFF): the four case ports in a PLAIN VLAN 3979 (111=port3.0.13, 112=port1.0.2,
# 113=port1.0.13, 114=port4.0.9). No partner change: each leg's partner port already sits alone in its scratch VLAN.
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
$U5 --stop-on-error "configure terminal" "vlan database" "vlan 3979 name ck-pv-baseline" "exit" \
  "interface port3.0.13" "switchport access vlan 3979" "interface port1.0.2" "switchport access vlan 3979" \
  "interface port1.0.13" "switchport access vlan 3979" "interface port4.0.9" "switchport access vlan 3979" \
  "end" "show vlan brief | include 399|3979" || exit 2
