"""ACL group harness -- tb470 scratch. Traffic TRANSITS the stack:
   ingress tb470 eth2 -> stack port2.0.2   (vlan 1)
   egress  stack port1.0.2 -> x230 -> tb470 eth1
A frame seen on eth1 proves forwarding THROUGH the DUT."""
import sys, time, subprocess, os
sys.path.insert(0, "/home/terrenceb/claude/device-testing/IE520/stack-tests/linkflap-38378-2026-09-18")
from console import Console

RUN = "/home/terrenceb/claude/device-testing/IE520/acl-2026-09-22"
ING_IF, EGR_IF = "eth2", "eth1"
ING_MAC, EGR_MAC = "00:f0:4d:00:77:17", "00:f0:4d:00:77:16"
ING_PORT = "port2.0.2"
EGR_PORT = "port1.0.2"

class DUT:
    def __init__(self, tag):
        self.c = Console("/dev/u5", os.path.join(RUN, "console-%s.log" % tag))
        self.c.login(monitor=False)
        self.c.send("terminal length 0", timeout=30)
    def cmd(self, c, t=90):
        return self.c.send(c, timeout=t)
    def conf(self, lines, t=90):
        """Stop on the first error: a bad line leaves us in the wrong mode and a
        blind `exit` chain then logs the console out entirely."""
        o = self.cmd("configure terminal", 30)
        for l in lines:
            r = self.cmd(l, t)
            o += r
            if [x for x in r.splitlines() if x.strip().startswith("%")]:
                o += "\n<<< aborted: previous line errored >>>\n"
                break
        o += self.cmd("end", 30)
        return o
    @staticmethod
    def errs(out):
        return [l.strip() for l in out.splitlines() if l.strip().startswith("%")]
    def close(self):
        try:
            self.c.s.close()
        except Exception:
            pass

def send_capture(pkt_expr, bpf, n=10, marker=None, iface_in=None, iface_out=None):
    """Fire n frames into the DUT ingress, count how many exit. Returns int."""
    iface_in = iface_in or ING_IF
    iface_out = iface_out or EGR_IF
    script = "from scapy.all import *\npkt = %s\nsendp(pkt, iface=%r, count=%d, inter=0.15, verbose=False)\n" % (
        pkt_expr, iface_in, n)
    cap = subprocess.Popen(["sudo", "-n", "tcpdump", "-i", iface_out, "-nn", "-c", str(n), "-l", bpf],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    time.sleep(3)
    r = subprocess.run(["sudo", "-n", sys.executable, "-c", script], capture_output=True, text=True)
    if r.returncode != 0:
        cap.terminate()
        raise RuntimeError("scapy send failed: %s" % r.stderr.strip()[:300])
    time.sleep(4)
    subprocess.run(["sudo","-n","pkill","-f","tcpdump -i "+iface_out], capture_output=True)
    cap.terminate()
    lines = [l for l in cap.stdout if l.strip()]
    if marker:
        lines = [l for l in lines if marker in l]
    return len(lines)

def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")
