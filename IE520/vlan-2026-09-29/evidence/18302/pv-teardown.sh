#!/bin/bash
# T18302/T18303 teardown -> group-setup state (legs back in 3991/3993/3994, port3.0.13 access VLAN 1).
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
$U5 --stop-on-error "configure terminal" \
  "no arp 192.168.100.1" "no arp 192.168.100.2" "no arp 192.168.100.3" "no arp 192.168.100.4" \
  "interface vlan3980" "no ip address" \
  "interface port1.0.2" "no switchport private-vlan host-association" "no switchport mode private-vlan host" "switchport access vlan 3991" \
  "interface port1.0.13" "no switchport private-vlan host-association" "no switchport mode private-vlan host" "switchport access vlan 3993" \
  "interface port4.0.9" "no switchport private-vlan host-association" "no switchport mode private-vlan host" "switchport access vlan 3994" \
  "interface port3.0.13" "no switchport private-vlan mapping" "no switchport mode private-vlan promiscuous" "no switchport access vlan" \
  "exit" "vlan database" "private-vlan 3980 association remove 3981" "no private-vlan 3981 isolated" "no private-vlan 3980 primary" \
  "no vlan 3981" "no vlan 3980" "end" \
  "show vlan private-vlan" "show vlan brief | include 399|398" "show arp" "show mac address-table | include 0000.0000.01" \
  "show running-config interface port3.0.13" "show running-config interface port1.0.2" "show running-config interface port1.0.13" "show running-config interface port4.0.9" || exit 2
# Try 1 (16:53) stopped at port1.0.2 "no switchport mode private-vlan" (% Incomplete command; the form needs
# host|promiscuous). Everything before it had applied. pv-teardown-2.sh resumes from that line with the fixed form.
