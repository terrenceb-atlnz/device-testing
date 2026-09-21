"""QoS helper: send frames through the DUT and DECODE the egress markings."""
import sys, time, subprocess
sys.path.insert(0, "/tmp/acl")
from bench import ING_IF, EGR_IF, ING_MAC, EGR_MAC

def send_decode(pkt_expr, bpf, n=10, want="tos"):
    """Fire n frames, capture on egress with scapy, return list of decoded values."""
    cap_script = (
        "from scapy.all import *\n"
        "import json,sys\n"
        "pkts = sniff(iface=%r, filter=%r, timeout=14, count=%d)\n"
        "out=[]\n"
        "for p in pkts:\n"
        "    d={}\n"
        "    if p.haslayer('IP'):   d['tos']=p['IP'].tos; d['dscp']=p['IP'].tos>>2\n"
        "    if p.haslayer('IPv6'): d['tc']=p['IPv6'].tc; d['dscp']=p['IPv6'].tc>>2\n"
        "    if p.haslayer('Dot1Q'): d['cos']=p['Dot1Q'].prio; d['vlan']=p['Dot1Q'].vlan\n"
        "    out.append(d)\n"
        "print(json.dumps(out))\n" % (EGR_IF, bpf, n))
    cap = subprocess.Popen(["sudo", "-n", sys.executable, "-c", cap_script],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    time.sleep(4)
    snd = "from scapy.all import *\nsendp(%s, iface=%r, count=%d, inter=0.15, verbose=False)\n" % (pkt_expr, ING_IF, n)
    subprocess.run(["sudo", "-n", sys.executable, "-c", snd], capture_output=True, text=True)
    try:
        o, _ = cap.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        cap.kill(); o = "[]"
    import json
    try:
        return json.loads(o.strip().splitlines()[-1]) if o.strip() else []
    except Exception:
        return []

def summarise(rows, key):
    vals = [r.get(key) for r in rows if key in r]
    uniq = sorted(set(vals))
    return len(rows), uniq
