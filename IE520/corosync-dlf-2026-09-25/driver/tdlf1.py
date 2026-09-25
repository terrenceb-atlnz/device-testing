import sys, time, re, subprocess, signal, threading; sys.path.insert(0, "/tmp/ckorient")
from gate import *
from scapy.all import Ether, IP, UDP, Raw, wrpcap, sendp
Q = "/tmp/ckorient/q"
MAC = {"eth1": "00:f0:4d:00:77:16", "eth2": "00:f0:4d:00:77:17", "eth3": "00:f0:4d:00:77:18"}
DLF = "02:00:00:00:99:99"
def frame(dst, dport):
    p = Ether(src=MAC["eth3"], dst=dst)/IP(src="10.38.215.65", dst="192.0.2.1", ttl=2)/UDP(sport=5010, dport=dport)/Raw(bytes(1454))
    assert len(p) == 1496   # + 4-byte FCS = 1500 on the wire
    return p
wrpcap(Q + "/known1496.pcap", [frame(MAC["eth1"], 9)] * 500)
wrpcap(Q + "/dlf1496.pcap", [frame(DLF, 10)] * 500)

stk = session("stk"); do(stk, "stk", "end", allow_err=True)
do(stk, "stk", "show clock", allow_err=True)
do(stk, "stk", "show running-config | include storm", allow_err=True)
o = do(stk, "stk", "show mac address-table | include 0200.0000.9999", allow_err=True)
if re.search(r"(?m)^\s*\S+\s+\S+\s+0200\.0000\.9999\s", o): log("[GATE FAILED: DLF MAC is learned -- STOP]"); raise SystemExit(1)
do(stk, "stk", "show log | include corosync", allow_err=True)
o = do(stk, "stk", "terminal monitor", allow_err=True)
if "Console logging enabled" not in o: log("[GATE FAILED: terminal monitor not confirmed -- STOP]"); raise SystemExit(1)

MON = []; stop = threading.Event()
def reader():
    while not stop.is_set():
        out = stk.read_until_quiet(quiet=0.5, timeout=2, need_prompt=False)
        for l in out.splitlines():
            if l.strip(): MON.append((time.strftime("%H:%M:%S"), l.rstrip()))
def mon_on():
    stop.clear(); t = threading.Thread(target=reader, daemon=True); t.start(); return t
def mon_off(t):
    stop.set(); t.join()
def sdma3(tag):
    o = do(stk, "stk", "show platform counter sdma", allow_err=True, timeout=60)
    blk = o.split("Stack member 3:")[1].split("Stack member")[0] if "Stack member 3:" in o else ""
    rx = sum(int(v) for v in re.findall(r":\s+(\d+) : sdmaRegs\.rxDmaPcktCnt", blk))
    log("[DLF sdma m3 rx, %s] %d" % (tag, rx))
def phase(tag, pcap, rate, secs=10):
    tds = {i: subprocess.Popen(["tcpdump", "-i", i, "-nn", "-s", "64", "-B", "65536", "-w", "/dev/null",
                                "ether src %s and udp src port 5010" % MAC["eth3"]], stderr=subprocess.PIPE, text=True)
           for i in ("eth1", "eth2")}
    time.sleep(2)
    t0 = time.strftime("%H:%M:%S")
    a = ["tcpreplay", "-i", "eth3", "--duration=%d" % secs, "--loop=0"] + (["--topspeed"] if rate == "top" else ["--mbps=%s" % rate]) + [pcap]
    out = subprocess.run(a, capture_output=True, text=True).stdout
    t1 = time.strftime("%H:%M:%S"); time.sleep(2)
    got = {}
    for i, p in tds.items():
        p.send_signal(signal.SIGINT); err = p.communicate()[1]
        got[i] = "%s (kd %s)" % (re.search(r"(\d+) packets captured", err).group(1), re.search(r"(\d+) packets dropped by kernel", err).group(1))
    m = re.search(r"Actual: (\d+) packets.*?Rated: ([\d.]+) Bps, ([\d.]+) Mbps, ([\d.]+) pps", out, re.S)
    sent, bps, mbps, pps = int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    wire = pps * (1500 + 20) * 8 / 1e6   # + preamble/SFD 8 + IFG 12
    log("[DLF %s] %s-%s sent %d  tcpreplay %.1f Mbps (frame bytes)  %.0f pps  = %.1f Mbps on the wire | rx eth1 %s  eth2 %s"
        % (tag, t0, t1, sent, mbps, pps, wire, got["eth1"], got["eth2"]))

subprocess.run(["ping", "-c", "2", "-i", "0.3", "-I", "eth1", "10.38.215.10"], capture_output=True)   # keep eth1 learned
sdma3("before")
t = mon_on()
for tag, pcap, rate in (("ramp known-unicast 100M", "known1496.pcap", "100"),
                        ("ramp known-unicast 500M", "known1496.pcap", "500"),
                        ("ramp known-unicast line", "known1496.pcap", "top")):
    phase(tag, Q + "/" + pcap, rate); time.sleep(5)
mon_off(t); sdma3("after ramp"); t = mon_on()
phase("DLF line-rate, ingress master port3.0.9", Q + "/dlf1496.pcap", "top"); time.sleep(10)
mon_off(t); sdma3("after DLF")
do(stk, "stk", "terminal no monitor")
do(stk, "stk", "show clock", allow_err=True)
do(stk, "stk", "show log | include corosync", allow_err=True)
log("[DLF console lines during the run: %d]" % len(MON))
for ts, l in MON: log("  MON %s | %s" % (ts, l))
log("[DLF WARMUP DONE]")
