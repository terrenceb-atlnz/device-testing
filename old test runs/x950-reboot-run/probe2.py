import sys, time, serial
CMDS = ["show running-config | include stack",
        "show running-config interface port1.0.1",
        "show running-config interface port1.0.7",
        "show interface port1.0.1 status",
        "show interface port1.0.7 status"]
def drain(s, settle=0.6):
    out=b""; end=time.time()+20
    while time.time()<end:
        c=s.read(4096)
        if not c:
            if out: break
            time.sleep(0.2); continue
        out+=c
        if b"--More--" in c: s.write(b" ")
        time.sleep(settle)
    return out.decode(errors="replace")
def cmd(s,c,settle=0.6):
    s.write((c+"\r").encode()); time.sleep(settle); return drain(s,settle)
dev=sys.argv[1]
s=serial.Serial(dev,115200,timeout=1)
s.write(b"\r"); time.sleep(0.4); drain(s,0.3)
cmd(s,"terminal length 0")
for c in CMDS:
    print(f"\n--- [{dev}] {c} ---"); print(cmd(s,c).strip())
s.close()
