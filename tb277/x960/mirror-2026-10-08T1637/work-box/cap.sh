#!/bin/bash
# cap.sh <label> -- capture ICMP on eth3 (mirror destination) while pinging .70 from .65
lbl="$1"
sudo -n timeout 14 tcpdump -i eth3 -n -Q in 'icmp' > cap-$lbl.txt 2>cap-$lbl.err &
tp=$!
sleep 3
ping -c 6 -i 0.5 -I 10.38.22.65 -W 2 10.38.22.70 > ping-$lbl.txt 2>&1
wait $tp 2>/dev/null
req=$(command grep -c '10.38.22.65 > 10.38.22.70: ICMP echo request' cap-$lbl.txt)
rep=$(command grep -c '10.38.22.70 > 10.38.22.65: ICMP echo reply'   cap-$lbl.txt)
loss=$(command grep -oE '[0-9]+% packet loss' ping-$lbl.txt)
printf '  %-10s eth3 saw: echo REQUESTS(ingress on 1.0.48)=%s  echo REPLIES(egress on 1.0.48)=%s   ping: %s\n' "$lbl" "$req" "$rep" "$loss"
