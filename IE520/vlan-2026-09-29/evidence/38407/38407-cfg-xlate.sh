#!/bin/bash
# T38407 step 1: ingress-side rule on port3.0.13 (wire 3996 <-> internal 3995) and an egress-side rule on
# port1.0.2 (internal 3995 <-> wire 3997). port1.0.13 has NO rule, so it shows the result of the ingress rule.
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
$U5 --stop-on-error "configure terminal" \
  "interface port3.0.13" "switchport vlan translation vlan 3996 vlan 3995" \
  "interface port1.0.2" "switchport vlan translation vlan 3997 vlan 3995" \
  "end" "show interface switchport vlan translation" "show running-config interface port3.0.13" "show running-config interface port1.0.2" || exit 2
