# Session handover — tb470 IE520 — 2026-09-24 (updated at the EVENING wrap, ~17:10 NZST)

## TL;DR — evening (current; the afternoon and morning TL;DRs follow)

- **The bench is whole and unchanged in config.** All four devices have running == startup
  (nothing was written). The stack is 1/3/4 Ready with member 3 the master. Two deliberate
  member reloads (3 and 4) during 38435 are the only new reboot-history entries. Host paths
  are at 0% loss. Record: bench-state.md "Evening wrap" block.
- **Terrence's instruction:** run the remaining cases autonomously, log non-test decisions as
  issues, choose blockers with the options recorded, then plan the fixes and wrap. **The
  queue, all 27 issues (I-1…I-27) and the PLAN are in
  [CAMPAIGN-QUEUE-2026-09-24.md](CAMPAIGN-QUEUE-2026-09-24.md). Read that first.**
- **Run this afternoon/evening, each reverted and diffed IDENTICAL against a pre-test copy:**

  | case(s) | verdict | log |
  | --- | --- | --- |
  | IPv6 mcast 38144 11724 11740 11722 11736 30681 20930 | 7 PASS | `ipv6-2026-09-22/` |
  | 38430 BGP4+ BFD fall-over | PASS (I-14: case premise; peer = IE520-sa, I-13) | `ipv6-2026-09-22/38430.log` |
  | QoS 13549 strict priority / 13553 WRR | 2 PASS (+ finding I-17) | `qos-2026-09-22/` |
  | 38435 tri-auth / VCS master failover | PASS (redraft, I-20) | `auth-2026-09-22/38435.log` |
  | 28126–28129 rate halves | 28129 → PASS; 28126/28127 step-1 rate PASS (step-2 FAIL stands); 28128 FAIL stands | `auth-2026-09-22/` |
  | 16452 / 16453 loop-protection | 2 PASS (I-23) | `stp-2026-09-22/` |
  | 38432 | re-labelled UNSUPPORTED (Terrence's 09-23 ruling applied) | `auth-2026-09-22/38432.log` |

- **What unblocked most of it:** `tcpreplay` on tb470 gives ~983 Mbps per NIC, which is line
  rate. The "harness peaks at ~26 Mbps" limit no longer holds. It also makes 3116 and 12067
  (ruled skip) measurable (I-19).
- **Still BLOCKED:**
  - 38474 needs tb470 root (route, `/tmp/atmfbk`) and the 4050 knownhosts fetch (I-1, I-2,
    I-21).
  - 38152/38153 remaining steps and EPSR need the SFP+ SA↔x230 link, which is faulty (I-3,
    hands).
  - MRP: the partners have no CLI.
- **Watcher:** a session-only hourly cron (`:17`) re-wakes this session if work is left. The
  queue is finished, so it has nothing to do. It dies with the session (and was deleted at
  this wrap).

## E. Evening session (2026-09-24, ~15:00–17:10) — findings

**Measured**
- **QoS, stack (I-17, possible defect):**
  - UNTAGGED traffic entering on a remote member (sa3 on members 1/4, egress on member 3)
    is sent from egress queue 0. The same CoS-0 traffic entering locally uses queue 2, as
    the map says. Under strict priority, remote traffic therefore always loses.
  - `mls qos cos 5` on a port is accepted, but that port's untagged traffic does not move
    queue.
  - Tagged PCP traffic follows the map from any member.
- **Strict priority and WRR work.** The higher queue gets 100% whichever member it enters
  on. WRR 30:10 / 10:30 / 20:20 gives received ratios 2.99 / 0.33 / 1.00.
- **The IE520 uses scheduler-sets for WRR:**
  `mls qos scheduler-set N wrr-queue group G weight W queues Q`, then
  `mls qos scheduler-set N` on the port. There is no interface `wrr-queue weight`, and
  `show mls qos scheduler-set N` is `% Invalid input`.
- **BFD on the IE520 is service-gated** (`service bfd`). The show command is `show bfd peer`.
  - BFD fall-over drops BGP within ~2 s when BFD's packets are lost.
  - A TCP-only ACL leaves BFD up, and BGP ends on its hold timer (+114 s).
  - Neither BGP nor BFD state changes are logged (I-16).
  - `no service bfd` drops the console from config to exec.
- **ACLs on the IE520:**
  - A later-added rule is appended AFTER an existing `permit any any` (I-15).
  - `ipv6 traffic-filter` is refused on static-channel members; it goes on the `saN`
    interface.
- **VCS master failover with tri-auth:** a ~2.2 s outage on every path; all dot1x, web and
  MAC sessions survive; a new 802.1X auth succeeds against the new master's local RADIUS.
  - Tri-auth also works on a static aggregator (sa3).
  - The web login is refused ("previous authentication in progress") while the port's
    802.1X attempt is Connecting.
- **Guest VLAN, CPU path** (hw-forwarding off): 100% up to 20 Mbps; 95.1% IPv4 / 98.3% IPv6
  at 100 Mbps. Hardware path: line rate, no loss.
  - The first line-rate burst after an SVI address change lost ~12 ms of traffic. Settled
    runs lose nothing.
- **Loop-protection:**
  - fast-block IS clearable: `no loop-protection loop-detect`, then re-add without
    `fast-block`.
  - link-down err-disables the port and the far end goes notconnect.
  - port-disable Blocks the port while the link stays up at both ends.
- **Static IPv6 mroute:** all downstreams must go in ONE command (I-12). `ipv6 mld
  static-group` with no interface lists the group on EVERY port of the VLAN, including the
  phantom member-2 range (I-27).

**Inferred**
- I-17 looks like the stacking path losing the ingress-assigned CoS for untagged frames. Not
  proven: a tagged-vs-untagged run from the same remote port would isolate it.

**OPEN questions:** all in the queue file's issue list (status OPEN) and its Plan §A.

**Next steps:** the queue file's Plan (A decisions → C root/38474 → B hands/SFP+ → D case
text → E tooling).

**Recipes added this session** (tb470 `/tmp/ckorient` helpers as in §8):
```bash
# line-rate traffic: build a 500-frame pcap with scapy (1514 B, dst = eth1 MAC), then
sudo tcpreplay -i eth3 --topspeed --duration=10 --loop=0 /tmp/ckorient/q/eth3.pcap   # ~983 Mbps
# count per source at the receiver: exact while "0 packets dropped by kernel"
sudo tcpdump -i eth1 -nn -s 64 -B 65536 -w /dev/null ether src <mac>   # SIGINT -> counts
# DUT egress queues:  clear mls qos interface port3.0.13 queue-counters / show ... queue-counters
# tagged ingress: port3.0.9 + sa3 (both ends) + SA port1.0.2 as trunk, allowed vlan add 50;
#   egress port3.0.13 access vlan 50; eth1 sends a 1 pps learn frame
# two-link loop without the SFP+ ring: take sa2's legs out of BOTH LAGs into an empty vlan 60
#   (stack port1.0.2,1.0.9 / x230 port1.0.3,1.0.4); keep it open (x230 port1.0.4 shut)
#   except while measuring; restore: actions off, fast-block back, re-bundle, then no shut
# a master reload drops EVERY backup console's CLI session (it is remote to the master):
#   re-login (session()) after the reload before issuing the next command
```

## TL;DR — afternoon (superseded by the evening TL;DR above where they differ)

- **The bench is whole and verified.** tb470 was reset (Terrence) and came back at ~14:15. The
  bench was RE-MEASURED 14:18–14:40: no DUT changed, spanning tree is off on all four devices,
  running == startup everywhere, and there are no new reboots.
- **`tb470.setup` was re-verified line by line** against a `bench_probe.py` sweep plus LLDP on
  all six inter-device links, then applied (`backups/2026-09-24T024005Z.*`).
  - The one data change: `[boot_from_flash] swi_f = True`.
  - Comments fixed: the AMF note, the sa2 LLDP proof, the x230 boot note.
- **Found:** after the reset, `/nfsHome` was not mounted, so the canonical `.setup` path
  dangled. Terrence mounted it. The ATMF route `10.10.10.0/27` and `/tmp/atmfbk` were lost in
  the reset (§A).
- **No tests were run this afternoon** (Terrence: "do not continue tests yet"). The next step
  is still 38152 phase 1 (§7 below).

## A. Afternoon session (2026-09-24, 14:15–14:45)

1. **tb470 reset.** `uptime -s` reads 11:57:54, but the box was unreachable (ARP FAILED from
   tb105 on the same `bootnet`) until ~14:15. **After it came back,
   `/home/st-art/st-art/configs/tb470.setup` did not resolve:**
   - `/home/st-art/st-art` is a symlink to `/nfsHome/st-art/`, and fstab mounts
     `10.36.250.11:/home` on BOTH `/home` and `/nfsHome`. Only `/home` came up.
   - The file was intact: the same sha1 `7630ccf0…` at `/home/st-art/configs/tb470.setup`.
   - Fix (root, so Terrence ran it): `sudo mount /nfsHome`.
   - **Any framework run bound to the canonical path fails until this is done.**
     Memory: `tb470-reboot-nfshome-unmounted`.
2. **Probe plus reconciliation.** `bench_probe.py` (u0 read by hand at 9600, the known probe
   defect).
   - `bench_topology.py generate` produced 21 FALSE mismatches: it models the standalone
     `IE520-sa` as a second stack and uses a stale 09-15 scaffold. Its output was not used.
   - Instead every `.setup` line was checked against the raw probe output: consoles/serials,
     stack 1/3/4, baud, host edges, `[portlink]`, boot.
   - sa2's per-port pairing was proven with a temporary `lldp run` on the x230, removed again
     afterwards (running == startup re-checked).
3. **`.setup` applied and IN SYNC** at `273ade07…`. A strict configparser load passes. The PDU
   outlets are unchanged and still unverified for SA (H/8). The two held-shut links stay
   undeclared.
4. **Before resuming 38474:** Terrence re-adds
   `sudo ip route add 10.10.10.0/27 via 10.38.215.10 dev eth1`, and `/tmp/atmfbk` is recreated
   (`mkdir /tmp/atmfbk`).

---

# Morning session (SUPERSEDED where it conflicts with the afternoon above)


## TL;DR

- **The bench is whole, AMF-free and written — but it was NOT re-read at wrap.** The test
  network (tb470 itself) went unreachable at ~10:15 NZST, mid-session. Everything below is
  the last measured state (~10:05–10:10 NZST).
- **ATMF:**
  - **38475 PASS.** The DUT recovered byte-identical config from USB plus the master backup.
    This replaces run 1's FAIL.
  - **38474 PARKED** until the end of the queue (Terrence: "the juice isn't worth the
    squeeze"). The 4050 cannot fetch tb470's host key.
  - **AMF has been torn down on all four devices** and the result written.
- **Re-runs of the no-reconfig queue:**
  - 38413 and 942: **UNSUPPORTED** (Terrence's ruling).
  - 6057: **PASS + finding**. The ARP table caps at 2045 entries, and while it is full a new
    neighbour cannot be resolved.
  - 28126, 28127 and 28128: **FAIL**.
  - 28129: **PASS** (functional).
- **Next:** the reconfig group, starting with **38152/38153** (the RSTP/STP ring). The plan is
  in §7 and nothing of it was applied. **First confirm RSTP is still off** (§1).

## 1. When tb470 is back: verify the bench in one block

```bash
export SSH_AUTH_SOCK=/run/user/1971/keyring/ssh
ssh tb470 'uptime; for d in /dev/u0 /dev/u1 /dev/u2 /dev/u3 /dev/u4 /dev/u5; do printf "%s: " $d; fuser $d 2>&1 || echo free; done'
#   uptime < time since 10:15 NZST 2026-09-24  =>  tb470 rebooted: its /tmp (all helpers) and the
#   runtime route 10.10.10.0/27 are gone. Route (root -> Terrence pastes): sudo ip route add 10.10.10.0/27 via 10.38.215.10 dev eth1
ssh tb470 'for p in "eth1 10.38.215.10" "eth1 10.38.215.2" "eth2 10.38.215.40" "eth2 10.38.215.41" "eth3 10.38.215.66"; do set -- $p; echo "$1->$2 $(ping -I $1 -c2 -W2 $2 | grep -oE "[0-9]+% packet loss")"; done'
# consoles: u0 x230 (9600!) · u1 4050 · u2 stack m1 · u3 IE520-sa · u4 stack m4 · u5 stack m3 (master)
# ON EVERY DEVICE (stack u5, SA u3, x230 u0):
#   show running-config | include spanning   -> must still read "no spanning-tree rstp enable" and
#                                               NO "spanning-tree priority" line (see §3)
#   show atmf                                -> Network Name : Not Set, 1 node
#   show stack (IE520s), show reboot history -> any new entry since 2026-09-23 21:06 UTC?
cd bench-setup && ./bench_setup.py apply     # SKIPPED at wrap (needs tb470): archives the superseded record
```

## 2. What was accomplished

1. **Orientation.** The bench matched the 09-23 late record exactly. New observation: the
   4050's `show boot` names `AR4050S-5.5.1-2.1.rel` while it runs `AR4050S-tb470.rel`.
   Terrence: fine, leave it.
2. **38472.log trimmed** to the one-log format: the side-story sections went, and the
   static-vs-LACP caveat moved under the verdict.
3. **ATMF 38474 attempted, then parked.**
   - `crypto key pubkey-chain knownhosts ip 10.38.215.1` on the 4050 fails with
     `% Cannot retrieve public key`.
   - TCP to tb470:22 from the 4050 works: `telnet 10.38.215.1 22` gets the OpenSSH banner, and
     tcpdump shows a clean handshake.
   - tb470's sshd journal logs nothing from 10.10.10.2 for the fetch attempts.
   - The auto-mode classifier also blocked Claude from running the knownhosts add
     ("Unauthorized Persistence"), so Terrence typed it.
4. **ATMF 38475 — PASS** (repeat): `IE520/atmf-2026-09-23/38475.log`.
5. **AMF teardown** on all four devices, then `write` (bench-state.md "2026-09-24" §1).
6. **Re-runs:**
   - 38413 and 942 (UNSUPPORTED): `IE520/acl-2026-09-22/`.
   - 6057: `IE520/switching-2026-09-22/`.
   - 28126–28129, now four per-case logs: `IE520/auth-2026-09-22/`. The combined
     `guest-vlan-28126-28129.log` was removed, and the group READMEs were updated.

## 3. BENCH DELTAS / what is not verified

- **AMF removed, written.** Everything that got AMF trunks is back to access on its
  original VLAN.
  - **4050 `port1.0.2`** (shut) is now access vlan 10. This is **inferred**: no pre-AMF
    capture of that port exists.
- **Keys:**
  - The stack and x230 userkeys are destroyed, and the stack's knownhosts list is empty.
  - **The 4050 userkey is kept** for 38474.
- **tb470 host, kept for 38474:**
  - the sshd drop-in and `/etc/ssh/atmf-backup-keys/`;
  - the runtime route (gone if tb470 rebooted);
  - `/tmp/atmfbk`.

  Revert when 38474 is done or dropped:
  `sudo rm -r /etc/ssh/sshd_config.d/60-atmf-backup-tb470.conf /etc/ssh/atmf-backup-keys && sudo systemctl reload ssh && sudo ip route del 10.10.10.0/27 via 10.38.215.10`.
- **RSTP: VERIFIED OFF at the afternoon wrap** (§A). The 38152 phase-1 call never ran; all four
  devices read `no spanning-tree rstp enable` with no priority lines, and x230 `port1.0.10`
  stays shut.
- **USB:** stack member 3's stick holds an `atmf/tb470/` backup tree from 38475 (data).
- **tb470 `/tmp/ckorient/`** holds this session's raw captures (`t38474/`, `t38475/`,
  `teardown/`, `t6057/`, `tguest/`, …). They are lost if tb470 rebooted. The logs already
  carry the proof.

## 4. Results

| case | verdict | run quality | log |
| --- | --- | --- | --- |
| 38475 ATMF recover from USB | **PASS** | clean. A reload before the case cleared run-1 residue (see findings) | `IE520/atmf-2026-09-23/38475.log` |
| 38474 ATMF remote backup | **PARKED** | not run past step 1 | — |
| 38413 standard IPv6 ACL | **UNSUPPORTED** | clean; not configurable | `IE520/acl-2026-09-22/38413.log` |
| 942 send-to-mirror IPv6 | **UNSUPPORTED** | clean; the action does not exist | `IE520/acl-2026-09-22/942.log` |
| 6057 ARP full tables | **PASS + finding** | clean | `IE520/switching-2026-09-22/6057.log` |
| 28126 guest VLAN IPv4, hw-fwd off | **FAIL** (step 2) | clean; the step-2 meaning is interpreted (see log) | `IE520/auth-2026-09-22/28126.log` |
| 28127 guest VLAN IPv4, hw-fwd on | **FAIL** (step 2) | clean; same interpretation | `IE520/auth-2026-09-22/28127.log` |
| 28128 guest VLAN IPv6, hw-fwd off | **FAIL** | clean | `IE520/auth-2026-09-22/28128.log` |
| 28129 guest VLAN IPv6, hw-fwd on | **PASS** (functional) | clean; rate UNMEASURED | `IE520/auth-2026-09-22/28129.log` |

In all four guest-VLAN cases the rate half (loss vs line rate) is UNMEASURED; it needs an ixia.

## 5. Findings

**Measured**

- **AMF failed-recovery residue persists until a reboot** (38475).
  - Run 1's DUT had not rebooted since its failed recovery.
  - Until it did, it read `Special Link Not Present` with its vlink Full, and wrote no USB
    recovery file.
  - The master refused to back it up:
    `Aborted backup for node IE520-sa due to the node being in safe mode`.
  - The DUT itself said `Recovery State : None`.
  - One `reload` cleared all three. Run 1's candidate root cause was therefore this residue,
    not a vlink defect (n=1).
- **A successful AMF recovery reboots the node a second time.** It logs `File recovery from
  master node succeeded. Node will now reboot`, about 15 min after `atmf cleanup`.
  `Unable to remove recovery link` (user.err) is logged even though recovery succeeds.
- **ARP table cap about 2045 entries** (6057).
  - Past the cap, the DUT sends no ARP requests at all.
  - A new neighbour gets `ping: sendmsg: No buffer space available`.
  - Existing entries keep working, and nothing is logged.
  - Removing an IP secondary flushes the **whole** VLAN's neighbour table.
- **Guest VLAN:**
  - `auth guest-vlan hw-forwarding` defaults to off, so traffic is CPU-forwarded. Proven like
    for like: member 3's sdma counters were +621 rx / +625 tx for 600 frames with it off vs on.
  - Unknown unicast floods to the other guest-VLAN port in both modes.
  - With it off, IPv6 between supplicants is dropped unless the guest VLAN has an IPv6 address
    in the traffic's subnet.
- **IE520 CLI:**
  - `no interface vlan200` is refused (`% Removal of interface not allowed`). Remove the
    address, then `no vlan` in the vlan database.
  - `crypto key destroy userkey manager rsa` is **Global Config** (exec gives `% Invalid input`).
- **The 4050's knownhosts fetch** fails with `Cannot retrieve public key` while the TCP path
  and sshd are proven good; sshd logs nothing (38474).

**Inferred**

- The 2045 cap looks like a kernel neighbour-table limit (the error is ENOBUFS). Not proven.

## 6. OPEN questions (for Terrence)

1. **38474:** when we return to it, do we debug the 4050 knownhosts fetch (e.g. try the `rsa`
   / `ecdsa` keyword, or read the 4050's `debug`), or drop the case?
2. **28126/28127 step 2:** the case repeats step 1's wording and expects "completely blocked".
   It was read as unknown-unicast suppression (from the folder title). Is that right?
3. **6057:** is refusing new neighbours at a full table, rather than evicting stale ones, the
   intended policy? Worth raising?
4. **28128:** worth raising as a defect? The evidence is in its log.

## 7. Ordered next steps

**A. 38152 RSTP / 38153 STP on the new single-domain ring.** None of this has been applied.

- **Topology mapping.**
  - DUT = the stack; its host is eth1 on `port3.0.13`.
  - sw1 = `IE520-sa` (sa3 to the DUT); its host is eth2 on `port1.0.2`.
  - sw2 = x230 (sa2 to the DUT; SFP+ `port1.0.10` ↔ SA `port1.0.25`).
  - All links are untagged, so this is one L2 domain.
- **Priorities.** DUT 4096, SA 8192, x230 default. Step 9 needs a sw1 priority *lower* than the
  DUT, and step 6 expects sw1 to win.

1. On the stack, SA and x230, set `spanning-tree rstp enable`; set the priorities.
   **Before closing the ring,** confirm every ring port (stack sa2/sa3, SA sa3/port1.0.25,
   x230 sa2/port1.0.10) shows in `show spanning-tree brief` with a real state.
2. Close the ring: x230 `no shutdown` on `port1.0.10`. **If no ring port reaches
   Discarding within 15 s, shut it again at once.** Expect SA `port1.0.25` = Alternate.
3. Run the steps as the case orders them:
   1. Root: all three see the DUT.
   2. Bidirectional eth1↔eth2 timestamped streams while `sa3` is shut on the DUT (the
      alternate path).
   3. Portfast on `port3.0.13`.
   4. BPDU filter on sa3 plus shutting sa2. Mirror sa3's members to `port3.0.9` and capture
      BPDUs on eth3.
   5. Root guard on sa3, then SA priority 0. Note: superior BPDUs can also reach the DUT via
      sa2; report literally, then isolate if needed.
   6. Loop guard on a host port.
4. 38153: the same in `spanning-tree mode stp`. **The mode change re-enables STP**
   (memory `stp-mode-change-reenables-spanning-tree`).
5. Teardown: disable RSTP on all three, restore the default priorities, shut x230 `port1.0.10`,
   and verify the pings.

**B.** Then 16452/16453 (loop protection on the same ring), EPSR 45789/45788, IPv6 mcast/PIM,
38430 BFD, QoS 13549/13553, MRP, and 38435 (the plan is unchanged from the 09-23 handover).

**C.** 38474 last (OPEN #1), then revert tb470's host additions (§3).

## 8. Recipes (tb470 tmpfs dies on reboot: recreate from here)

```bash
export SSH_AUTH_SOCK=/run/user/1971/keyring/ssh
ssh tb470 'mkdir -p /tmp/ckorient'
scp IE520/stack-tests/2026-09-02-driver-test/console.py tb470:/tmp/ckorient/
```

`/tmp/ckorient/am2.py`: the 09-23 `am.py`, with `RUN` taken from the environment and
`terminal length 0` sent after login.

```python
import sys, time, re, os; sys.path.insert(0, "/tmp/ckorient")
from console import Console, PROMPT_RE
RUN = os.environ.get("RUN", "/tmp/ckorient/work")
DEV = {"stk": ("/dev/u5", 115200), "ar": ("/dev/u1", 115200), "sa": ("/dev/u3", 115200), "x230": ("/dev/u0", 9600)}
RAW = open(RUN + "/work-raw.log", "a", buffering=1)
YN = re.compile(r"\((y/n|yes/no)\)\s*\??\s*:?\s*$")
def log(s): RAW.write(s + "\n"); print(s, flush=True)
def session(tag):
    port, baud = DEV[tag]
    c = Console(port, "%s/console-%s.log" % (RUN, tag), baud=baud); c.login(timeout=120)
    c.send("terminal length 0", quiet=1.0, timeout=20); return c
def do(c, tag, cmd, answer=None, timeout=120, allow_err=False):
    out = c.send(cmd, quiet=1.5, timeout=timeout, need_prompt=False)
    t0 = time.time()
    while time.time() - t0 < timeout and not (PROMPT_RE.search(out.rstrip()[-120:]) or YN.search(out.rstrip())):
        out += c.read_until_quiet(quiet=1.5, timeout=10, need_prompt=False)
    if YN.search(out.rstrip()):
        if answer is None:
            w = "no" if "yes/no" in out.rstrip()[-20:] else "n"
            out += c.send(w, quiet=2.0, timeout=30)
            log("%s> %s\n%s\n[UNEXPECTED prompt -> %s; STOP]" % (tag, cmd, out, w)); raise SystemExit(1)
        out += "\n[answered %s]\n" % answer + c.send(answer, quiet=2.0, timeout=timeout)
    log("%s> %s\n%s" % (tag, cmd, out))
    if not allow_err and re.search(r"^\s*% ", out, re.M):
        log("[CLI error -- STOP]"); raise SystemExit(1)
    return out
```

`/tmp/ckorient/gate.py`:

```python
from am2 import *
def poll(c, tag, cmd, pat, secs=120, every=5):
    t0 = time.time()
    while time.time() - t0 < secs:
        o = do(c, tag, cmd, allow_err=True)
        if re.search(pat, o): return o
        time.sleep(every)
    log("[GATE FAILED: %s !~ %s -- STOP]" % (cmd, pat)); raise SystemExit(1)
def conf(c, tag, lines):
    do(c, tag, "configure terminal")
    for l in lines: do(c, tag, l)
    do(c, tag, "end")
```

`/tmp/ckorient/tx.py`: inject labelled frames on one NIC and count arrivals per label on the
others. Run it as `sudo -n python3 tx.py spec.py`; only the packet I/O is root.

```python
import sys, json, time
from scapy.all import sendp, AsyncSniffer, UDP, conf
conf.verb = 0
spec = {}; exec(open(sys.argv[1]).read(), spec)
ING, EGR, PKTS = spec["ING"], spec["EGR"], spec["PKTS"]      # PKTS = [(label, pkt, n)]
ports = {40000 + i: lab for i, (lab, _, _) in enumerate(PKTS)}
sn = {e: AsyncSniffer(iface=e, filter="udp and portrange 40000-40999", store=True) for e in EGR}
for s in sn.values(): s.start()
time.sleep(1.5)
for i, (lab, p, n) in enumerate(PKTS):
    p[UDP].dport = 40000 + i; sendp(p, iface=ING, count=n, inter=0.02)
time.sleep(2.0)
res = {lab: {e: 0 for e in EGR} for (lab, _, _) in PKTS}
for e, s in sn.items():
    for q in s.stop():
        if UDP in q and q[UDP].dport in ports: res[ports[q[UDP].dport]][e] += 1
print(json.dumps(res))
```

Host MACs: eth1 `00:f0:4d:00:77:16`, eth2 `…:17`, eth3 `…:18`. Stack router MAC
`00:00:cd:37:0d:6f`.

Gotchas that cost time this session:
- A vlink row in `show atmf links` has **no Link Status column**, so match
  `vlink1\s+Uplink\s+Full`, not `Up`.
- The master's `show atmf nodes` keeps a departed node for a while. It is **not** a rejoin
  signal; watch the node's own `atmffsd` log.
- A recovery reboots the node a second time.

## 9. Git — committed, NOT pushed

Committed locally on `main` together with this handover; the hash is in the session brief and
in `git log -1`. **NOT pushed:** Claude cannot push here, so Terrence runs `git push origin main`.

## 10. Pointers

- Bench record: `bench-setup/bench-state.md` "Current state — 2026-09-24".
- Previous handover (ATMF background, 38474 plumbing): `IE520/SESSION-HANDOVER-2026-09-23.md`.
- Memories written or updated this session: `atmf-recovery-residue-and-reboots` (new),
  `tb470-root-changes-go-through-terrence` (device trust changes are blocked too),
  `tb470-reboot-nfshome-unmounted` (new, afternoon).
