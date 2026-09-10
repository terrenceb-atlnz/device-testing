#!/usr/bin/env python3
"""Wait for an IE520 to finish booting, log in if needed, then verify the unstacked state."""
import re, sys, time, serial

CHECKS = ["show stack", "show running-config | include stack",
          "show system pluggable", "show interface port1.0.1 status",
          "show interface port1.0.7 status", "show interface brief"]

def drain(s, settle=0.7, budget=35):
    out=b""; end=time.time()+budget
    while time.time()<end:
        c=s.read(4096)
        if not c:
            if out: break
            time.sleep(0.2); continue
        out+=c
        if b"--More--" in c: s.write(b" ")
        time.sleep(settle)
    return out.decode(errors="replace")

def cmd(s,c,settle=0.7,budget=35):
    s.write((c+"\r").encode()); time.sleep(settle); return drain(s,settle,budget)

dev=sys.argv[1]; deadline=time.time()+600
s=serial.Serial(dev,115200,timeout=1)
ready=False
while time.time()<deadline:
    s.write(b"\r"); time.sleep(1.0)
    out=drain(s,0.4,10)
    if re.search(r"login:", out, re.I):
        cmd(s,"manager"); out=cmd(s,"friend")
    if "#" in out or ">" in out:
        ready=True; break
    time.sleep(10)
print(f"\n{'='*70}\n=== {dev}   booted={ready}  waited={int(time.time()-(deadline-600))}s\n{'='*70}")
if ready:
    cmd(s,"terminal length 0")
    for c in CHECKS:
        print(f"\n--- {c} ---")
        print("\n".join(l.rstrip() for l in cmd(s,c).splitlines() if l.strip() and l.strip()!=c))
s.close()
