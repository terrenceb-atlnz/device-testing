#!/usr/bin/env python3
"""Strip VCStack identity from an IE520 so it becomes a plain standalone switch.

Does NOT reboot - config is applied and saved, then verified. Reboot is a separate step.
Never uses `no stack <id> enable` (that err-disables every port and strands the unit on
its console); clears the stackport flags and the chassis identity instead.
"""
import re, sys, time, serial

ERR = re.compile(r"%|Unrecognized|Invalid|Unknown command|Ambiguous", re.I)

def drain(s, settle=0.8, budget=45):
    out = b""; end = time.time() + budget
    while time.time() < end:
        c = s.read(4096)
        if not c:
            if out: break
            time.sleep(0.2); continue
        out += c
        if b"--More--" in c:
            s.write(b" ")
        if re.search(rb"\(y/n\)", c, re.I) or b"[yes/no]" in c:
            s.write(b"y\r")                      # confirm renumber / overwrite prompts
        time.sleep(settle)
    return out.decode(errors="replace")

def cmd(s, c, settle=0.8, budget=45):
    s.write((c + "\r").encode()); time.sleep(settle)
    out = drain(s, settle, budget)
    body = "\n".join(l for l in out.splitlines() if l.strip() and l.strip() != c)
    flag = "  <-- CHECK" if ERR.search(body) else ""
    print(f"  $ {c}{flag}")
    for l in body.splitlines():
        if l.strip().rstrip("#").strip() and not l.strip().endswith("#"):
            print(f"      {l.rstrip()}")
    return body

dev, renumber_from = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
print(f"\n{'='*70}\n=== {dev}   (renumber {renumber_from}->1)" if renumber_from
      else f"\n{'='*70}\n=== {dev}   (already stack ID 1)")
print("=" * 70)
s = serial.Serial(dev, 115200, timeout=1)
try:
    s.write(b"\r"); time.sleep(0.4); drain(s, 0.3, 8)
    cmd(s, "terminal length 0")
    cmd(s, "configure terminal")
    for rng in ("port1.0.27-1.0.28", "port2.0.27-2.0.28"):
        cmd(s, f"interface {rng}")
        cmd(s, "no stackport")
        cmd(s, "exit")
    cmd(s, "no stack virtual-mac")
    out = cmd(s, "no stack virtual-chassis-id 3039")
    if ERR.search(out):
        cmd(s, "no stack virtual-chassis-id")          # fallback form
    if renumber_from:
        cmd(s, f"stack {renumber_from} renumber 1", settle=1.5, budget=60)
    cmd(s, "exit")
    print("\n  -- saving --")
    cmd(s, "write", settle=2.0, budget=60)
    print("\n  -- verify: stack lines remaining in running-config --")
    cmd(s, "show running-config | include stack")
    print("\n  -- verify: show stack --")
    cmd(s, "show stack", settle=1.0)
finally:
    s.close()
