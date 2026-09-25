import sys, time, re, subprocess, signal, threading; sys.path.insert(0, "/tmp/ckorient")
from gate import *
from scapy.all import Ether, IP, UDP, Raw, wrpcap
Q = "/tmp/ckorient/q"
MAC = {"eth1": "00:f0:4d:00:77:16", "eth2": "00:f0:4d:00:77:17", "eth3": "00:f0:4d:00:77:18"}
IP4 = {"eth2": "10.38.215.33", "eth3": "10.38.215.65"}
DLF = "02:00:00:00:99:99"
def frame(nic):
    p = Ether(src=MAC[nic], dst=DLF)/IP(src=IP4[nic], dst="192.0.2.1", ttl=2)/UDP(sport=5010, dport=10)/Raw(bytes(1454))
    assert len(p) == 1496
    return p
wrpcap(Q + "/dlf1496-eth2.pcap", [frame("eth2")] * 500)
wrpcap(Q + "/dlf1496-eth3.pcap", [frame("eth3")] * 500)

stk = session("stk"); do(stk, "stk", "end", allow_err=True)
do(stk, "stk", "show clock", allow_err=True)
o = do(stk, "stk", "show mac address-table | include 0200.0000.9999", allow_err=True, timeout=30)
if re.search(r"(?m)^\s*\S+\s+\S+\s+0200\.0000\.9999\s", o): log("[GATE FAILED: DLF MAC is learned -- STOP]"); raise SystemExit(1)
do(stk, "stk", "show stack", allow_err=True)
o = do(stk, "stk", "terminal monitor", allow_err=True)
if "Console logging enabled" not in o: log("[GATE FAILED: terminal monitor not confirmed -- STOP]"); raise SystemExit(1)

stop = threading.Event(); NMON = [0]
def reader():
    while not stop.is_set():
        out = stk.read_until_quiet(quiet=0.5, timeout=2, need_prompt=False)
        for l in out.splitlines():
            if l.strip(): NMON[0] += 1; log("  MON %s | %s" % (time.strftime("%H:%M:%S"), l.rstrip()))
def mon_on():
    stop.clear(); t = threading.Thread(target=reader, daemon=True); t.start(); return t
def mon_off(t):
    stop.set(); t.join()
def sdma(tag):
    o = do(stk, "stk", "show platform counter sdma", allow_err=True, timeout=60)
    out = {}
    for m in re.finditer(r"Stack member (\d+):(.*?)(?=Stack member \d+:|\Z)", o, re.S):
        out[int(m.group(1))] = sum(int(v) for v in re.findall(r":\s+(\d+) : sdmaRegs\.rxDmaPcktCnt", m.group(2)))
    log("[DLF2 sdma rx per member, %s] %s" % (tag, out))
def phase(tag, senders, receivers, secs=10):
    tds = {}
    for rx, src in receivers:   # (nic, sender nic whose frames we count)
        tds[(rx, src)] = subprocess.Popen(["tcpdump", "-i", rx, "-nn", "-s", "64", "-B", "65536", "-w", "/dev/null",
                                           "ether src %s and udp src port 5010" % MAC[src]], stderr=subprocess.PIPE, text=True)
    time.sleep(2); t0 = time.strftime("%H:%M:%S")
    procs = {s: subprocess.Popen(["tcpreplay", "-i", s, "--duration=%d" % secs, "--loop=0", "--topspeed", Q + "/dlf1496-%s.pcap" % s],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) for s in senders}
    sent = {}
    for s, p in procs.items():
        out = p.communicate()[0]
        m = re.search(r"Actual: (\d+) packets.*?Rated: ([\d.]+) Bps, ([\d.]+) Mbps, ([\d.]+) pps", out, re.S)
        sent[s] = "%d @ %.1f Mbps %.0f pps" % (int(m.group(1)), float(m.group(3)), float(m.group(4))) if m else "?? " + out[-200:]
    t1 = time.strftime("%H:%M:%S"); time.sleep(2)
    got = {}
    for k, p in tds.items():
        p.send_signal(signal.SIGINT); err = p.communicate()[1]
        got["%s<-%s" % k] = "%s (kd %s)" % (re.search(r"(\d+) packets captured", err).group(1), re.search(r"(\d+) packets dropped by kernel", err).group(1))
    log("[DLF2 %s] %s-%s sent %s | rx %s" % (tag, t0, t1, sent, got))

subprocess.run(["ping", "-c", "2", "-i", "0.3", "-I", "eth1", "10.38.215.10"], capture_output=True)
sdma("before run 2")
t = mon_on()
phase("run 2: DLF from eth2 -> IE520-sa -> sa3 (members 1+4), line rate", ["eth2"], [("eth1", "eth2"), ("eth3", "eth2")])
time.sleep(10); mon_off(t); sdma("after run 2")
do(stk, "stk", "show log | include flow control", allow_err=True, timeout=30)
time.sleep(5)
t = mon_on()
phase("run 3: DLF from eth3 (master) AND eth2 (via sa3 -> members 1+4) at once, line rate", ["eth3", "eth2"],
      [("eth1", "eth2"), ("eth1", "eth3"), ("eth2", "eth3"), ("eth3", "eth2")])
time.sleep(10); mon_off(t); sdma("after run 3")
do(stk, "stk", "terminal no monitor", allow_err=True)
do(stk, "stk", "show clock", allow_err=True)
do(stk, "stk", "show log | include corosync", allow_err=True, timeout=30)
do(stk, "stk", "show log | include flow control", allow_err=True, timeout=30)
log("[DLF2 console lines seen during the runs: %d]" % NMON[0])
log("[DLF2 DONE]")
