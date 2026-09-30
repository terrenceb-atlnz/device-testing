#!/bin/bash
# 8770-fill.sh <first-batch> <last-batch> [hw]   (on tb470, cwd /tmp/ck11)
# Per batch k: replay p/f<k>.pcap (1000 new destinations) from eth2 at 300 pps,
# settle 5 s, record the responder's counters and the count of 2001:db8:8770:1::
# rows in `show ipv6 neighbors`; with "hw", also count /128 rows per stack member
# in `show platform table ipv6`. Raw outputs -> $E/8770-fill-k<k>-*.out.
E=/home/terrenceb/claude/device-testing/IE520/ipv6-bgp-2026-09-29/evidence/8770
cd /tmp/ck11 || exit 1
for k in $(seq "$1" "$2"); do
  t0=$(date +%T)
  sudo -n tcpreplay -i eth2 --pps=${PPS:-300} p/f$k.pcap 2>&1 | grep -E "Actual" > /tmp/ck11/tr.out
  sleep 5
  cp resp.json $E/8770-fill-k$k-resp.json
  CKTO=400 python3 ckcon.py /dev/u5 115200 /tmp/ck11/console-u5.log "show ipv6 neighbors" > $E/8770-fill-k$k-nbr.out 2>&1
  n=$(grep -c '2001:db8:8770:1::1:' $E/8770-fill-k$k-nbr.out)
  echo "$t0 batch $k sent=$((k*1000)) $(cat /tmp/ck11/tr.out) | neighbours=$n | resp: $(python3 -c 'import json;d=json.load(open("resp.json"));print("ns_mcast=%d ns_ucast=%d na=%d targets=%d"%(d["ns_mcast"],d["ns_ucast"],d["na_sent"],d["targets"]))')"
  if [ "$3" = hw ]; then
    CKTO=600 python3 ckcon.py /dev/u5 115200 /tmp/ck11/console-u5.log "show platform table ipv6" > $E/8770-fill-k$k-hw.out 2>&1
    awk '/^Stack member/{m=$3} /2001:db8:8770:1::1:[0-9a-f]+\/128/{c[m]++} END{for(k in c) printf "  hw member %s /128 rows=%d\n",k,c[k]}' $E/8770-fill-k$k-hw.out
  fi
done
