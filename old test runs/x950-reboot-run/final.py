import sys, time, serial
def drain(s,settle=0.7,budget=30):
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
def cmd(s,c,settle=0.7,budget=30):
    s.write((c+"\r").encode()); time.sleep(settle); return drain(s,settle,budget)
dev=sys.argv[1]
s=serial.Serial(dev,115200,timeout=1)
s.write(b"\r"); time.sleep(0.5); drain(s,0.3,8)
cmd(s,"enable"); cmd(s,"terminal length 0")
print(f"\n===== {dev}")
for c in ("show running-config | include stack",
          "show running-config interface port1.0.27",
          "show interface brief | include 1.0.27|1.0.28|1.0.1 |1.0.7 "):
    print(f"\n--- {c}")
    print("\n".join(l.rstrip() for l in cmd(s,c).splitlines() if l.strip() and l.strip()!=c))
s.close()
