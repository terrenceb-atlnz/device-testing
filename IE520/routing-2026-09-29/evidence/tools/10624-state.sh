#!/bin/bash
# 10624-state.sh <tag>: stack (u5) OSPF neighbour, RIB summary, O-route count and per-member
# silicon count of the 10.124.0.0-10.125.243.0 prefixes (show platform table ip).
E=/home/terrenceb/claude/device-testing/IE520/routing-2026-09-29/evidence/10624; cd /tmp/ck12
f=$E/10624-$1-u5.out
python3 ckcon.py /dev/u5 115200 console-u5.log "show ip ospf neighbor" "show ip route summary" "show ip route ospf" "show platform table ip" > $f 2>&1
python3 - $f <<'PY'
import sys, re
t = open(sys.argv[1], errors="replace").read().replace("\r", "").replace("\x00", "")
def blk(c):
    p = t.split(">>> " + c)
    return re.split(r"\n\d\d:\d\d:\d\d >>> ", p[1])[0] if len(p) > 1 else ""
nb = [l.strip() for l in blk("show ip ospf neighbor").splitlines() if "10.106" in l]
print("neighbour:", nb or "none")
print("summary:", " | ".join(l.strip() for l in blk("show ip route summary").splitlines() if re.match(r"\s*(connected|ospf|static|Total|FIB)", l)))
o = re.findall(r"^O\S*\s+\S*\s*(10\.12[45]\.\d+\.0/24)", blk("show ip route ospf"), re.M)
print("RIB O routes in 10.124-125: %d distinct %d" % (len(o), len(set(o))))
cur = None; cnt = {}
for l in blk("show platform table ip").splitlines():
    m = re.match(r"Stack member (\d+)", l)
    if m: cur = m.group(1); cnt[cur] = 0; continue
    if cur and re.match(r"10\.12[45]\.\d+\.0\s+24\s", l): cnt[cur] += 1
print("silicon /24 entries in 10.124-125 per member:", cnt)
PY
