#!/bin/bash
# T18302/T18303 setup (case step 1, "Create vlan10 and set as a private vlan"; vlan 10 is the live sa1 transit
# on tb470, so the private VLAN is primary 3980 + isolated secondary 3981):
#   uplink 111 = port3.0.13 promiscuous; private 112/113/114 = port1.0.2 / port1.0.13 / port4.0.9 isolated hosts.
#   Case static ARP entries: interface vlan3980 192.168.100.254/24 + arp 192.168.100.1-4 -> 0000.0000.01{1,2,3,4}0.
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
$U5 --stop-on-error "configure terminal" \
  "interface port3.0.13" "no switchport access vlan" "interface port1.0.2" "no switchport access vlan" \
  "interface port1.0.13" "no switchport access vlan" "interface port4.0.9" "no switchport access vlan" \
  "exit" "vlan database" "no vlan 3979" "vlan 3980 name ck-pv-primary" "vlan 3981 name ck-pv-isolated" \
  "private-vlan 3980 primary" "private-vlan 3981 isolated" "private-vlan 3980 association add 3981" "exit" \
  "interface port3.0.13" "switchport mode private-vlan promiscuous" "switchport private-vlan mapping 3980 add 3981" \
  "interface port1.0.2" "switchport mode private-vlan host" "switchport private-vlan host-association 3980 add 3981" \
  "interface port1.0.13" "switchport mode private-vlan host" "switchport private-vlan host-association 3980 add 3981" \
  "interface port4.0.9" "switchport mode private-vlan host" "switchport private-vlan host-association 3980 add 3981" \
  "interface vlan3980" "ip address 192.168.100.254/24" "exit" \
  "arp 192.168.100.1 0000.0000.0110 port3.0.13" "arp 192.168.100.2 0000.0000.0120 port1.0.2" \
  "arp 192.168.100.3 0000.0000.0130 port1.0.13" "arp 192.168.100.4 0000.0000.0140 port4.0.9" \
  "end" "show vlan private-vlan" "show vlan brief | include 399|398" \
  "show running-config interface port3.0.13" "show running-config interface port1.0.2" "show running-config interface port1.0.13" "show running-config interface port4.0.9" \
  "show arp" "show mac address-table | include 0000.0000.01" || exit 2
