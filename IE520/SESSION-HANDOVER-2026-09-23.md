# Session handover — tb470 IE520 — 2026-09-23 (LATE session)

> Two sessions ran on 2026-09-23. **This top part is the later session and is current.** The
> morning session's handover follows below with only its heading changed. Where they
> disagree, this part wins: the bench was rebuilt again, every IE520 moved to
> `awplus_main-20260923-20`, and `atmf cleanup` became possible on the new standalone IE520.

## TL;DR

- **The bench is PARKED mid-ATMF, not idle.** An AMF network `tb470` is up on all four
  devices, and the **AR4050S (`4050-5g`) is AMF master in RUNNING config only**. The stack's
  *startup* still says `atmf master`. **Nothing AMF-related was `write`n this session**, so a
  reboot of any node changes who is master (§3).
- **The physical bench is whole.**
  - Units: a 3-member IE520 stack (IDs 1/3/4, master = member 3), the standalone `IE520-sa`,
    the x230 and the AR4050S, joined by three static LAGs.
  - Build: every IE520 runs `awplus_main-20260923-20`.
  - `IE520-sa` is now **stack ID 1**, so its ports are `port1.0.x`.
  - The record is `bench-setup/bench-state.md` "Current state — 2026-09-23 late";
    `tb470.setup` is applied and `IN SYNC`.
- **Results:**
  - ATMF **38472 PASS**.
  - **38475 run 1 FAIL**; the run is confounded, so a repeat is required.
  - **38474 not yet run.** Its remote-backup path is built (4050 master → tb470 over SSH),
    and it is the first thing to run.
- **Terrence's rule for these logs (2026-09-23): ONE `<case-id>.log` per case**, holding the
  most recent run only: outputs and proof, no side-stories. Raw captures stay in tb470 `/tmp`.

## 1. Verify the parked state in one block

```bash
export SSH_AUTH_SOCK=/run/user/1971/keyring/ssh
ssh tb470 'for d in /dev/ttyUSB*; do printf "%s: " $d; fuser $d 2>&1 || echo free; done'
# consoles: u0 x230 (9600!) · u1 4050 · u2 stack m1 · u3 IE520-sa · u4 stack m4 · u5 stack m3 (master)
# expect u1 (4050):  show atmf -> Role : Master, Current ATMF Nodes : 4
# expect u5 (stack): show stack -> 1/3/4 Ready, m3 Active Master;  show atmf -> Role : Member
# expect u3 (SA):    show stack -> ID 1 Standalone;  show atmf links -> sa3 Uplink Full IE520-stk
ssh tb470 'for p in "eth1 10.38.215.10" "eth1 10.38.215.2" "eth2 10.38.215.40" "eth2 10.38.215.41" "eth3 10.38.215.66"; do set -- $p; echo "$1->$2 $(ping -I $1 -c2 -W2 $2 | grep -oE "[0-9]+% packet loss")"; done'
# tb470 backup-server plumbing for 38474
ssh tb470 'ip route show 10.10.10.0/27; ping -c2 -W2 10.10.10.2 | tail -1; sudo -n sshd -T -C user=terrenceb,host=ar,addr=10.10.10.2,laddr=10.38.215.1,lport=22 | grep -i ^authorizedkeysfile'
#   expect "10.10.10.0/27 via 10.38.215.10 dev eth1", ping OK, "authorizedkeysfile /etc/ssh/atmf-backup-keys/%u".
#   The route is RUNTIME-ONLY: after a tb470 reboot, re-add it (§8).
```

## 2. What was accomplished

1. **Bench rebuilt.** It is now a 3-member stack + standalone `IE520-sa` + `sa3`, and every
   IE520 moved to `awplus_main-20260923-20`. Terrence loaded the members and set the
   bootloader default to flash. Committed earlier as `fcfdbb3`.
2. **ATMF 38472 (Master) — PASS**, all five steps. That includes secure mode, which FAILED on
   the 2026-09-21 build. → `IE520/atmf-2026-09-23/38472.log`
3. **ATMF 38475 (recover from USB) — run 1 FAIL**, confounded (§4).
   → `IE520/atmf-2026-09-23/38475.log`
4. **ATMF 38474 (backup to a remote file server): the backup path was found by
   elimination.**
   - Dev PC as the server: impossible, because the lab network cannot open TCP to the office
     subnet.
   - IE520 stack as master: accepts `atmf backup server` but never mounts it.
   - x230 as master: `% ATMF requires AMF-MASTER-X license`.
   - **AR4050S as master (licensed), with tb470 as the server**: built and verified up to the
     mount, which is the next step.
5. **Records.** bench-state.md has a "late" section and updated fences (swi_b → `port1.0.x`),
   applied (`backups/2026-09-23T040043Z.*`). Memories are listed in §10.

## 3. BENCH DELTAS — the landmine: running ≠ startup, plus host changes

| node | running | startup | on the device (NVS), not config |
| --- | --- | --- | --- |
| 4050-5g | **`atmf master`**, atmf-link sa1 | **no `atmf master`** | manager RSA key `SHA256:YDtOg/YU…` |
| IE520-stk | **not master**; atmf-link sa1 + sa2 + **sa3 (trunk)** | **`atmf master`**, atmf-link sa1 + sa2 | manager RSA key `SHA256:zOsTvQR8…`; knownhosts #1 = tb470 `10.38.215.1` |
| IE520-sa | sa3 **trunk + atmf-link**, **no vlink** | sa3 access + **`atmf virtual-link id 1` → 10.38.215.40** | — |
| x230-10GP | atmf-link sa2 (= startup) | same | manager RSA key `SHA256:7C40Iz3R…` (unused) |

- **After ANY reboot, re-read `show atmf` on all four.**
  - A 4050 reboot leaves the network masterless, since the stack isn't master in running.
  - A stack reboot brings it back as a second master.
  - An SA reboot returns it to its vlink and sa3 access.
- **tb470 host, root, installed by Terrence's paste:**
  - `/etc/ssh/sshd_config.d/60-atmf-backup-tb470.conf` + `/etc/ssh/atmf-backup-keys/terrenceb`:
    the 4050's key only, honoured only for `10.10.10.2/31` → `10.38.215.1`, key-only.
  - Runtime route `10.10.10.0/27 via 10.38.215.10 dev eth1`.
  - `/tmp/atmfbk`, empty.
  - **Revert:** `sudo rm -r /etc/ssh/sshd_config.d/60-atmf-backup-tb470.conf /etc/ssh/atmf-backup-keys && sudo systemctl reload ssh && sudo ip route del 10.10.10.0/27 via 10.38.215.10`.
- **USB sticks:** one in `IE520-sa` (38475's recovery-file media) and one in **stack member
  3** (Terrence, for 38475's master-side backup media).
- **The 4050's routes** `10.38.215.0/27` and `10.38.215.32/27` via `10.10.10.1` **pre-date
  this session** and are in its startup. Do NOT remove them at teardown.
- **Dev PC:** `~/.ssh/authorized_keys` was edited and then restored byte-identical. Nothing
  is left there.

## 4. Results

| case | verdict | run quality | log |
| --- | --- | --- | --- |
| 38472 ATMF Master | **PASS** (5/5) | clean. Caveat in the log: static LAG vs LACP not isolated | `IE520/atmf-2026-09-23/38472.log` |
| 38475 recover from USB | **FAIL at step 5** (run 1) | **confounded.** The DUT was a former stack member at ID 2; the NVS erase reset it to ID 1, so its recovered `port2.0.x` config landed on phantom ports. A repeat is required, and its log REPLACES this one | `IE520/atmf-2026-09-23/38475.log` |
| 38474 backup + recover via a remote server | **not run** | setup in progress (§7 A) | — |

**LED check (38474 step 5).** Terrence watched the port LEDs scroll in the recovery pattern
during 38475 run 1's recovery; they "work as advertised" (2026-09-23 late). He doesn't need to
watch again unless he says so.

## 5. Findings

**Measured**
- **An IE520 AMF master ignores `atmf backup server`.**
  - Server 1 stayed `Configured (Unmounted)`, and server-status read `No check`.
  - tb470's sshd logged ONE connection from the stack, the host-key fetch
    (`Connection closed by 10.38.215.10 … [preauth]`).
  - `atmf backup now IE520-sa` → `% No backup media found on this device`, and the 03:00 run
    logged `Scheduled backup not started because media not found`.
  - Re-adding the server and toggling `atmf backup enable` changed nothing.
  - Memory `ie520-master-ignores-remote-backup-server`.
- **The x230-10GP cannot be AMF master** (`% ATMF requires AMF-MASTER-X license`). **The
  AR4050S can**: its FULL licence carries AMF-MASTER-20…250.
- **The bench cannot open TCP to the office subnet.** From tb470, every port on 10.33.22.17
  times out, closed ports included, while ICMP passes. Memory `bench-cannot-open-tcp-to-office-pcs`.
- **The IE520 CLI differs from the wiki.**
  - `crypto key pubkey-chain knownhosts` is **Global Config** here; exec rejects
    `pubkey-chain`. It prints the whole host key, then asks
    `Are you sure you want to add this public key (yes/no)?`.
  - `crypto key generate userkey … rsa` makes **3072** bits (the wiki says 2048) on the
    IE520, the x230 and the 4050 alike.
- **`atmf cleanup` resets a standalone's stack ID to 1 and wipes its reboot history.** The
  cleanup's own reboot then reads `Unexpected System reboot`.
- **38475 run 1:**
  - Before the wipe, the DUT read `Special Link Not Present` while its vlink was Full.
  - The USB recovery file dated from the vlink's creation, not from the saves.
  - `atmffsd: Unable to remove recovery link`.
  - The recovered config had no vlink, which led to `Automatic node recovery failed`.
- **The DUT's `show atmf recovery-file` now reads `Special Link Present`** although it has
  no vlink and no recovery file anywhere. Observed, not explained.
- **A USB stick inserted into the stack** (a non-master member at the time) received an
  `atmf_recovery_file` at once (03:53:02 UTC).

**Inferred**
- The candidate root cause for 38475 run 1: the member never registered its vlink as a
  special link, so the recovery file lacked the tunnel. The clean repeat settles it by reading
  `show atmf recovery-file` on the DUT **before** the wipe.

## 6. OPEN questions (decisions for Terrence)

1. **IE520 master + remote backup server:** is it "unsupported but accepted", or a defect
   worth filing? The evidence is in §5 and the memory.
2. **Running 38474 with the AR4050S as master** (IE520 member as DUT) instead of the x230
   you approved, which lacks the AMF-MASTER-X licence: acceptable?
3. **rsync on tb470** is approved if a backup needs it, but it is NOT installed yet. Install:
   `sudo apt-get install -y --no-install-recommends rsync`; revert: `sudo apt-get purge -y rsync`.
4. **What end-state should the AMF teardown after 38474/38475 leave?** For example no AMF
   config at all, then `write` on all four. The startups have held AMF config since 38472's
   secure-mode writes.
5. **Trim `38472.log`** to the new outputs-and-proof-only format?

## 7. Ordered next steps

**A. ATMF 38474.** Master = the 4050 on u1; DUT = IE520-sa on u3. Stop on any `% ` error
(§8 helper).

1. On the 4050, run `crypto key pubkey-chain knownhosts ip 10.38.215.1`. The wiki says exec
   mode; if that gives `% Invalid input`, use config mode. Answer `yes` **only** if the printed
   `ssh-rsa` blob equals field 2 of tb470's `/etc/ssh/ssh_host_rsa_key.pub` (`SHA256:t+C9p31P…`).
2. In 4050 config mode, set `atmf backup server id 1 10.38.215.1 username terrenceb path /tmp/atmfbk`.
   Then poll `show atmf backup` until it reads `Configured (Mounted)`, and check
   `show atmf backup server-status`.
   - If it never mounts, read `sudo journalctl -u ssh --since <t>` on tb470 for `10.10.10.2`.
   - If the backup log shows rsync is missing, apply OPEN #3.
   - Root changes on tb470 go through Terrence while auto mode is on (memory
     `tb470-root-changes-go-through-terrence`).
3. On the SA, `write`, then save its `show running-config` as the baseline. The backup must
   hold the running config: sa3 trunk + atmf-link, no vlink.
4. On the 4050, run `atmf backup now`. The case text means all nodes, and they fit in tb470's
   3.8 GB `/tmp`. Wait for `Current Action … Idle`, then check that `show atmf backup` lists
   every node as `Good`, and `ls -R /tmp/atmfbk` on tb470.
5. On the stack, `shutdown` `port4.0.9`. With only one sa3 leg up, the wiped SA cannot form
   an asymmetric LAG.
6. On the SA, run `atmf cleanup` and answer `y`. Login returns at about t+196 s. `dir` should
   show only `IE520-tb470.rel`, the GUI file and `log/`. Then watch
   `show log | include atmf` for the recovery.
7. The recovered `show running-config` must equal the baseline. Also check `show atmf` on the
   SA (Member, 4 nodes) and `show atmf nodes` on the 4050.
8. On the stack, `no shutdown` `port4.0.9`. Both sa3 legs should come up and the host pings
   run 0% loss.
9. Write `IE520/atmf-2026-09-23/38474.log`: outputs and proof only.

**B. ATMF 38475 repeat.** Master = the stack, backup media = the member-3 USB; DUT = IE520-sa,
with the vlink as its only path.

1. On the stack, `atmf master`; **only once it reads `Role : Master`**, `no atmf master` on the
   4050. Then on the stack, `atmf recovery-server`, and check `show atmf backup` for media =
   USB (expected, not yet verified).
2. Add the vlinks. SA: `atmf virtual-link id 1 ip 10.38.215.41 remote-id 2 remote-ip 10.38.215.40`.
   Stack: `atmf virtual-link id 2 ip 10.38.215.40 remote-id 1 remote-ip 10.38.215.41`.
3. Once the vlink is Full, remove sa3's atmf-link at both ends: `no switchport atmf-link`, then
   `switchport mode access`.
4. On the stack, `atmf backup now IE520-sa`. On the SA, `write`.
5. **Freshness gate** (Terrence: "dont use stale configs"). On the SA:
   - `dir usb:` must show `atmf_recovery_file` dated AFTER the write and the backup;
   - `show atmf recovery-file` must read `Special Link Present` with fresh dates.

   If it reads `Not Present` while the vlink is Full, that reproduces run 1's finding; log it.
6. Shut stack `port4.0.9`, run `atmf cleanup` on the SA, let it recover, compare its config
   with the baseline, then `no shutdown` `port4.0.9`.
7. Write `38475.log`, replacing run 1.

**C. Teardown.**
- AMF config: as OPEN #4 decides.
- tb470: the revert in §3.
- `crypto key destroy userkey manager rsa` on the stack, the x230 and the 4050.
- The stack's knownhosts entry: `no crypto key pubkey-chain knownhosts 1` (config mode on the
  IE520).

**D. The queue after ATMF** (plan unchanged).
- No-reconfig cases: 38413, 942, 28126–28129 (the functional half), 6057 (fill ARP with a
  responder).
- Then the reconfig group, one case at a time:
  - 38152/38153 (the SA↔x230 SFP+ ring)
  - 16452/16453
  - EPSR 45789/45788
  - IPv6 multicast/PIM: 38144, 11722, 11724, 11736, 11740, 20930, 30681
  - 38430 BFD
  - QoS 13549/13553
  - MRP
  - 38435, redrafted as a stack-master failover with the master as auth server
    (multiple-dynamic-vlan and dhcp-relay stay off)
- Terrence's rulings: skip 38148, 24032, 3116, 12067 and 8770; 38432 is Not Supported (no
  TACACS+).

## 8. Recipes (self-contained: tb470's `/tmp` and this session's scratchpad are gone)

```bash
export SSH_AUTH_SOCK=/run/user/1971/keyring/ssh
ssh tb470 'mkdir -p /tmp/ckorient/work'
scp IE520/stack-tests/2026-09-02-driver-test/console.py tb470:/tmp/ckorient/   # == the linkflap-38378 copy (same md5)
# u0 (x230) is 9600; everything else 115200. console.py applies stty -hupcl itself.
```

`/tmp/ckorient/am.py`, the multi-device helper used all session. Recreate it on tb470
(tmpfs, never the lab tree):

```python
import sys, time, re; sys.path.insert(0, '/tmp/ckorient')
from console import Console, PROMPT_RE
RUN = '/tmp/ckorient/work'   # raw captures stay OUT of the repo (Terrence's one-log rule)
DEV = {'stk': ('/dev/u5', 115200), 'ar': ('/dev/u1', 115200),
       'sa': ('/dev/u3', 115200), 'x230': ('/dev/u0', 9600)}
RAW = open(RUN + '/work-raw.log', 'a', buffering=1)
YN = re.compile(r"\((y/n|yes/no)\)\s*\??\s*:?\s*$")
def log(s): RAW.write(s + '\n'); print(s, flush=True)   # log BEFORE print: a dead ssh stdout raises BrokenPipe
def session(tag):
    port, baud = DEV[tag]
    c = Console(port, '%s/console-%s.log' % (RUN, tag), baud=baud); c.login(timeout=120); return c
def do(c, tag, cmd, answer=None, timeout=120, allow_err=False):
    """One CLI line. STOP on an unexpected (y/n)/(yes/no) (answers no) and on any '% ' error."""
    out = c.send(cmd, quiet=1.5, timeout=timeout, need_prompt=False)
    t0 = time.time()
    while time.time() - t0 < timeout and not (PROMPT_RE.search(out.rstrip()[-120:]) or YN.search(out.rstrip())):
        out += c.read_until_quiet(quiet=1.5, timeout=10, need_prompt=False)
    if YN.search(out.rstrip()):
        if answer is None:
            w = 'no' if 'yes/no' in out.rstrip()[-20:] else 'n'
            out += c.send(w, quiet=2.0, timeout=30)
            log('%s> %s\n%s\n[UNEXPECTED prompt -> %s; STOP]' % (tag, cmd, out, w)); raise SystemExit(1)
        out += '\n[answered %s]\n' % answer + c.send(answer, quiet=2.0, timeout=timeout)
    log('%s> %s\n%s' % (tag, cmd, out))
    if not allow_err and re.search(r'^\s*% ', out, re.M):
        log('[CLI error -- STOP]'); raise SystemExit(1)
    return out
```

Run scripts as `ssh tb470 'cd /tmp/ckorient && python3 - <<"EOF" … EOF'`, a heredoc: never
a `.py` in the lab tree.

**A knownhosts add that actually checks the key.** The prompt is `(yes/no)?` and it prints the
key, not a fingerprint. Run it on tb470, so it can read tb470's own host key:

```python
HK = open('/etc/ssh/ssh_host_rsa_key.pub').read().split()[1]
a = c.send('crypto key pubkey-chain knownhosts ip 10.38.215.1', quiet=4.0, timeout=90, need_prompt=False)
m = re.search(r'ssh-rsa (AAAA[A-Za-z0-9+/=]+)', a.replace('\r', ''))
c.send('yes' if ('(yes/no)' in a and m and m.group(1) == HK) else 'no', quiet=3.0, timeout=60)
```

**The tb470 return route after a reboot** (root, so it goes through Terrence while auto mode is
on): `sudo ip route add 10.10.10.0/27 via 10.38.215.10 dev eth1`.

## 9. Git — committed, NOT pushed

Committed locally on `main` together with this handover; the hash is in the session brief and
in `git log -1`. **NOT pushed:** Claude cannot push here, so Terrence runs `git push origin main`.

## 10. Pointers

- Topology, addressing, consoles, PDU and the parked AMF state: `bench-setup/bench-state.md`
  "Current state — 2026-09-23 late".
- Case logs: `IE520/atmf-2026-09-23/` (`38472.log`, `38475.log`). Earlier ATMF work:
  `IE520/atmf-2026-09-21/`.
- Memories written or updated this session:
  - `bench-cannot-open-tcp-to-office-pcs`
  - `ie520-master-ignores-remote-backup-server`
  - `bench-scripts-stop-on-cli-errors`
  - `tb470-root-changes-go-through-terrence`
  - `log-is-the-deliverable` (the one-log rule)
  - `awplus-cli-wiki-on-the-share` (no IE520 pages; x230 is the closest documented cousin;
    IE560, IE360, x230v2 and IE340 are the relatives Terrence named)
  - `awplus-cli-confirmations-need-enter` (`(yes/no)` prompts)
  - `rejected-tool-calls-keep-running-remotely` (incidents 3 and 4)

---

# Earlier the same day — morning session handover (SUPERSEDED where it conflicts with the late session above)

## TL;DR

**Bench is WHOLE and re-runnable.** The 72-case IE520 campaign is **complete** (39 PASS ·
1 PARTIAL · 32 UNMEASURED). Afterwards Terrence recabled and the bench was reconfigured
into **two static LAGs**, with all three TB NICs now landing **directly on the stack**.
Everything is **saved to startup-config** and recorded in `bench-setup/bench-state.md`
("Current state — 2026-09-23"); `tb470.setup` regenerated and applied.

Nothing is parked, nothing is powered off, nothing is left `shutdown` except one
deliberate link (below).

## Verify the bench in one block

```bash
ssh tb470
# stack whole, master (moves after any failover -- read it, never assume)
#   expect: 4/4 Ready, "Normal operation", Stack MAC 0000.cd37.0d6f
minicom --wrap -D /dev/u5     # or drive with pyserial; see Recipes
#   show stack ; show static-channel-group ; show interface status
#   show boot        -> "flash:/IE520-tb470.rel (file not found)" is EXPECTED
#                       (bootloader overrides it; read the real build from show system)
#   show system      -> awplus_main-20260913-1734 on ALL FOUR members

# host edges -- all three must be 0% loss
for s in "eth1 10.38.215.10" "eth2 10.38.215.40" "eth3 10.38.215.66"; do set -- $s
  echo "$1 -> $2: $(ping -I $1 -c2 -W2 $2 | grep -oE '[0-9]+% packet loss')"; done
# vlan10 transit across sa1
#   from the stack CLI: ping 10.10.10.2 repeat 3
```

## Current bench state

**Topology (measured 2026-09-23 — LLDP both ends, host-MAC learning, ping):**

| link | |
| --- | --- |
| **`sa1`** stack `port3.0.2` + `port4.0.2` ↔ 4050 `port1.0.3` + `port1.0.4` | static LAG, vlan 10. **Straddles stack units 3 and 4.** |
| **`sa2`** stack `port1.0.2` + `port1.0.9` ↔ x230 `port1.0.3` + `port1.0.4` | static LAG, vlan 1 (x230 side vlan 100) |
| tb `eth1` → stack `port3.0.13` · `eth2` → `port2.0.2` · `eth3` → `port3.0.9` | all three hosts direct on the stack |
| 4050 `port1.0.2` ↔ x230 `port1.0.2` | **deliberately `shutdown`** — see hazard below |

**Addressing:** stack vlan1 `10.38.215.10/27` + `.40/27` + `.66/27` secondary; stack
vlan10 `10.10.10.1/27` on `sa1`; 4050 vlan10 `10.10.10.2/27` on `sa1`; 4050 vlan1
`10.38.215.70/27` (**no TB edge any more**); x230 all ports vlan 100, SVI `10.38.215.2/27`.

**Third device:** x230-10GP on `/dev/u0` — **console is 9600 baud**, every other console
here is 115200. At 115200 it returns NUL bytes and reads as a dead device.

**RSTP is disabled on all three devices** (bench design). Saved to startup on the stack.

## !! The one standing hazard

**Do not un-bundle `sa2`, and do not bring up 4050 `port1.0.2`.** The two stack↔x230
links are parallel; with RSTP off the *only* thing making them safe is that they are
aggregated. Bringing up the 4050↔x230 leg additionally closes a stack/4050/x230 triangle.
Both were verified inert at wrap time.

This was demonstrated the hard way on 2026-09-22: closing that triangle produced a ring
with **no port anywhere in Discarding**, because `lacp global-passive-mode` had silently
enrolled the 4050 port into a channel-group, and **STP runs on the aggregator** — which
was down. Rule: before closing any redundant leg, confirm the port appears in
`show spanning-tree brief` **as a port with a real state**. "Spanning Tree Enabled" is not
the check.

## What was accomplished

1. **72-case IE520 campaign, all seven groups** — ACL, Authentication, MRP, QoS,
   STP & storm control, switching, IPv6 routing & protocol. Per-case `<case-id>.log` in
   dated group directories under `IE520/`, each with a README carrying the group verdict.
2. **Bench rebuild** after Terrence's recable — two static LAGs, hosts moved onto the
   stack, config saved, records updated. See `IE520/bench-rebuild-2026-09-23/`.

## Results

| group | verdict | directory |
| --- | --- | --- |
| ACL (13) | 11 PASS · 2 UNMEASURED | `IE520/acl-2026-09-22/` |
| Authentication (7) | 1 PASS · 6 UNMEASURED | `IE520/auth-2026-09-22/` |
| MRP (5) | 5 UNMEASURED | `IE520/mrp-2026-09-22/` |
| QoS (12) | 9 PASS · 3 UNMEASURED | `IE520/qos-2026-09-22/` |
| STP & storm (8) | 6 PASS · 2 UNMEASURED | `IE520/stp-2026-09-22/` |
| switching (11) | 6 PASS · 1 PARTIAL · 4 UNMEASURED | `IE520/switching-2026-09-22/` |
| IPv6 routing (16) | 6 PASS · 10 UNMEASURED | `IE520/ipv6-2026-09-22/` |

**All runs are CLEAN unless the log says otherwise.** Every measurement is on traffic that
**transits** the DUT (inject on one TB NIC, capture on another) with a **baseline taken
first with the feature off**, so a drop is provably the feature.

**Runs that were CONFOUNDED and are labelled as such in their logs:**
- The first IGMP/MLD snooping pass — the observation path ran **through the x230**, which
  has its own snooping on by default and was pruning the DUT's flood downstream. Re-run
  with x230 snooping off. *(This is now structurally fixed: eth1 is direct on the stack.)*
- T3111 (BGP default route) — filtered by **T3112's own prefix-list**, still bound to the
  same neighbour, containing `deny ::/0 le 128`. Two cases sharing one live session.
- T16453 (loop-protection link-down) — the ring never actually closed, so **no loop
  protection action was an incomplete stimulus, not a failure**.

**The 32 UNMEASURED are almost entirely bench limits, not product results**: needs a
line-rate generator (9) · needs more cabled ports or hosts (14, several now unblocked by
today's recable) · needs a peer device the bench lacks (6) · case has no steps in `ck.db`
(3) · the feature's subject does not exist on this platform (4).

## Findings

**Measured:**
- No implicit deny on a hardware IPv6 ACL via `ipv6 traffic-filter` — unmatched traffic
  forwards 10/10; `deny ipv6 any any` must be written explicitly.
- MAC-auth sends the MAC to RADIUS as **`00-f0-4d-00-77-17`** (lowercase, hyphenated);
  no `auth-mac username-format` command exists on this build.
- Default auth `host-mode` is single-host: one **failed** supplicant occupies the port so a
  good MAC behind it never authenticates.
- Changing `spanning-tree mode` **silently re-enables spanning tree**, discarding a prior
  `no spanning-tree <mode> enable`.
- `lacp global-passive-mode` silently enrols freed ports into aggregations — hit on **all
  three devices**; now disabled on all three.
- A static LAG refuses members whose properties differ; align VLAN/mode **before**
  `static-channel-group`.
- The DUT does not learn ARP from unsolicited/gratuitous ARP (6000 → 0 entries), while a
  single ping creates an entry immediately.
- `atmf cleanup` is **refused on a VCStack** (`% This command cannot be run when another
  stack member is present`) — this blocks AWPTCM-T38474 and T38475 entirely.
- Each IE520-28GSX member has **three** copper ports (`portN.0.2/.9/.13`), not one.
  **Correcting an earlier record**; the campaign logs that cite "one copper port per
  member" as a blocker overstate it — the real limits were uncabled ports and host count.

**Inferred (not proven):**
- ATMF secure mode not re-forming a 2-node network (T38472) is scoped to **"over an LACP
  aggregate"** — a single-physical-link control was never run. Cause unknown.
- The 2026-09-18 member-1 boot hang (`Starting kernel …` then silence) remains **n=1, no
  root cause**; a 20-cycle pinned re-run did not reproduce it.

## OPEN questions

1. **Is ATMF secure mode broken, or only over an aggregate?** Evidence path: remove
   `atmf-link` from `po1`/`sa1`, put `switchport atmf-link` on ONE physical port with the
   other member shut, re-run `atmf secure-mode enable-all`. → `IE520/atmf-2026-09-21/38472.log`
2. **Should T38474/T38475 be run by destacking to a single IE520?** That changes the DUT
   from a VCStack to a standalone switch. Terrence's call.
3. **Three cases have no steps in `ck.db`** (`38435`, `38148`, and `6005`/`38151`/`38487`
   which I interpreted from their titles and said so). Do they need defining?
4. **The AR4050S lists MRP as a licensed feature but exposes no MRP CLI.** A licence entry
   is not a capability — worth raising.
5. **`show arp counter` and `show platform table ipv6route` do not exist on this build**
   though they appear in case methods.

## Ordered next steps

1. **Re-run the cases the recable unblocked** — now buildable and not previously possible:
   ACL `881/885/890/889` and QoS `13604` against **`sa1`, which now straddles stack units
   3 and 4**; the mirror-delivery half of ACL `943`/`830` using `eth3`; the IPv6
   multicast/PIM set with three hosts direct on the stack.
2. **STP `38152`/`38153` alternate-path half** — `sa2` gives a redundant stack↔x230 path.
3. Answer OPEN #1 (one physical atmf-link) — cheap and settles a real finding.
4. Anything needing line rate waits for the ixia.

## Recipes

```bash
# drive a console (pyserial, NOT minicom -- minicom needs a TTY)
#   maintained driver: IE520/stack-tests/linkflap-38378-2026-09-18/console.py
#   x230 on /dev/u0 is 9600; everything else 115200
#   ALWAYS stty -F $(readlink -f /dev/uN) -hupcl first, or closing the port BREAKs the DUT

# campaign harness (recreate in tmpfs; it is NOT in the repo -- no-stray-py hook)
#   design + rebuild instructions: IE520/test-harness/README.md
mkdir -p /tmp/acl && scp bench.py qosbench.py peer.py tb470:/tmp/acl/
ssh tb470 'cd /tmp/acl && CAMPAIGN_RUN=<group-dir> python3 -u <case>.py'

# look up CLI syntax WITHOUT probing a live box (avoids the "? plus CR executes it" trap)
command grep -rl "<command>" \
  claude/github-copilot-awplus-wiki/awplus_cli_wiki/commands/   # 3437 pages

# regenerate and apply the .setup after editing bench-state.md
cd bench-setup && ./bench_setup.py check && ./bench_setup.py apply
```

## Pointers

- Topology, addressing, consoles, PDU: **`bench-setup/bench-state.md`** — do not duplicate.
- Rebuild detail: `IE520/bench-rebuild-2026-09-23/README.md`
- Campaign resume record (superseded by this handover): `IE520/RESUME-CAMPAIGN-2026-09-22.md`
- Earlier ATMF work and the secure-mode finding: `IE520/atmf-2026-09-21/`
- Harness design: `IE520/test-harness/README.md`
