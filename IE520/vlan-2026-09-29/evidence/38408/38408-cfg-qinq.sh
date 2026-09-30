#!/bin/bash
# T38408 steps 1+2: port3.0.13 customer-edge-port (S-VLAN 3995), port1.0.13 + port1.0.2 provider-port.
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
$U5 --stop-on-error "configure terminal" \
  "interface port3.0.13" "switchport vlan-stacking customer-edge-port" \
  "interface port1.0.13" "switchport vlan-stacking provider-port" \
  "interface port1.0.2" "switchport vlan-stacking provider-port" \
  "end" "show running-config interface port3.0.13" "show running-config interface port1.0.13" "show running-config interface port1.0.2" \
  "show interface status | include port1.0.2 |port1.0.9 |port1.0.13 |port3.0.13 " || exit 2
