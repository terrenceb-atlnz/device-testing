# SESSION HANDOVER — tb470 IE520 bench, 2026-09-22

**Wrapped** (not paused). Bench is **whole**: 4/4 stack members `Ready`, `Normal operation`,
all three host↔bench paths 0% loss, no console or NIC held by this session.

---

## TL;DR

- The **72-case AWPTCM campaign is complete**: **39 PASS / 1 PARTIAL / 32 UNMEASURED**, across
  seven group directories, every case with its own `.log`. Every UNMEASURED is attributed to a
  named cause, not to work skipped.
- The **ATMF run (2026-09-21) is complete**: 8 of 10 cases executed, 7 PASS / 1 FAIL.
- **All running-configs are clean** — ATMF, QoS, ACLs, policy-maps, 802.1X and every routing
  protocol have been removed from all three devices, and RSTP is back to the bench's intended
  disabled baseline.
- **ONE LANDMINE, and it is the first thing to read (§3.1): the stack's and the AR4050S's
  `startup-config` still contain the ATMF campaign config — including `atmf secure-mode` on the
  4050.** Running is clean; startup is not. **Any reload brings ATMF back on two of three nodes
  and not the third.** This was left deliberately — it is a decision, not a cleanup (§6 Q1).
- `bench-setup/bench-state.md` was **deliberately not updated** (Terrence's standing instruction
  for this campaign). Bench deltas live in §3 here and in `RESUME-CAMPAIGN-2026-09-22.md` §4.
- All work is **committed locally and NOT pushed** — see §9.

---

## 1. Current bench state — measured 2026-09-22, verify it in one block

Everything below was read from the hardware at wrap time, not recalled.

```bash
sock=/run/user/1971/keyring/ssh
# 1. the authoritative bench probe (read-only; sweeps u0-u5, maps host NIC -> switch port)
SSH_AUTH_SOCK=$sock ssh tb470 \
  'cd /home/terrenceb/claude/device-testing/bench-setup && python3 bench_probe.py --consoles 0-5 > /tmp/probe.json'
# 2. the three data paths (all three MUST be 0% loss)
SSH_AUTH_SOCK=$sock ssh tb470 \
  'for ip in 10.38.215.10 10.38.215.40 10.38.215.70; do echo -n "$ip: "; ping -c4 -W2 -q $ip | grep "packet loss"; done'
# 3. nothing of ours holding a console
SSH_AUTH_SOCK=$sock ssh tb470 'fuser -v /dev/u*; ls /var/lock/LCK..* 2>/dev/null'
```

**Consoles** (baud matters — the x230 is the odd one out):

| console | device | baud | state at wrap |
| --- | --- | --- | --- |
| `/dev/u0` | **x230-10GP** | **9600** | up, `vlan100` running, uptime 8h57m. *Does not answer a 115200 sweep — `bench_probe.py` reports it `unreachable`. That is the baud, not a fault.* |
| `/dev/u1` | AR4050S-5G | 115200 | up, `awplus_main-20260918-7`, uptime 4d03h |
| `/dev/u2` | IE520 member **1** | 115200 | Ready, Backup, prio 128 |
| `/dev/u3` | IE520 member **2** | 115200 | Ready, Backup, **prio 2** |
| `/dev/u4` | IE520 member **4** | 115200 | Ready, Backup, prio 128 |
| `/dev/u5` | IE520 member **3** | 115200 | **ACTIVE MASTER**, prio 128, holds the **USB stick** (28.9 GB, 28.6 GB free) |

**Stack:** virtual MAC `0000.cd37.0d6f`, `Operational Status Normal operation`, 4/4 `Ready`.
Software **identical on all four members** — `awplus_main-20260913-1734` (no build-date drift, so
no split hazard). Bootloaders differ per member and that is expected: m1 `9.1.0`,
m2 `master-20260822-535`, m3 `9.1.0`, m4 `pauld`.

**Boot:** `show boot` on the stack reads `Current boot image : flash:/IE520-tb470.rel
(file not found)`. **This is pre-existing and already adjudicated** — bench-state.md ruled it on
2026-09-15 as *"not a usable field, bootloader-overridden, not an action item"*. It is **not** a
stale-pointer hazard: the 20-cycle pinned run on 2026-09-20/21 rebooted members 22 times and every
one came back. Read the running build from `show system`, never from `show boot`.

**Host (tb470):** `eth1 10.38.215.1/27`, `eth2 10.38.215.33/27`, `eth3 10.38.215.65/27`, all
`carrier=1`, **all three autoneg on advertising 10/100/1000/2500** — no `ethtool` pinning left
behind. No stray routes or ARP entries. Paths verified 0% loss to `.10` (via the x230), `.40`
(direct) and `.70` (the 4050).

**Host NIC → switch port** (from the probe's MAC-table mapping): `eth1 → port1.0.2` (member 1),
`eth2 → port2.0.2` (member 2), `eth3 → port1.0.1` (member 1). Note `port1.0.1` reads
`admin up / protocol down` in `show interface brief` — treat the `eth3` mapping as **inferred from
a MAC-table entry, not confirmed**; the `.70` ping proves the path works, not which port it uses.

---

## 2. What was accomplished

1. **Member-1 pinned hang hunt** — 20/20 cycles PASS, no reproduction.
   `member1-pinned-2026-09-21/result-member1-pinned.md`. Combined member-1 rate **1/45 = 2.22%**
   (Clopper-Pearson 95% CI 0.06–11.77%). Console evidence for the 38377 hang is **exhausted**;
   the bootloader lead was **ruled out**, not merely deprioritised (`stack-tests/member-38377-2026-09-18/after-action-38377-partial.md` §8.2).
2. **ATMF group, 2026-09-21** — 8 of 10 cases, 7 PASS / 1 FAIL (`atmf-2026-09-21/`).
3. **The 72-case AWPTCM campaign** — all seven groups, in the screenshot's group order
   (§4 for results).
4. The **x230 was integrated as a third AMF node by configuration only**, with no recabling, per
   Terrence's instruction.

---

## 3. BENCH DELTAS — not in bench-state.md, read before touching anything

bench-state.md was **deliberately not updated** this campaign. These are the differences between
what it says and what is actually on the bench.

### 3.1 THE LANDMINE — running-config ≠ startup-config

| device | running-config | startup-config | consequence of a reload |
| --- | --- | --- | --- |
| **IE520 stack** | ATMF fully removed | still has `atmf network-name tb470`, `service atmf-application-proxy`, `atmf virtual-link id 1 ip 10.10.10.1 remote-id 2 remote-ip 10.10.10.2`, `switchport atmf-link`, `switchport trunk native vlan 10` | ATMF returns |
| **AR4050S** | ATMF fully removed | still has `atmf network-name tb470` **and `atmf secure-mode`** | ATMF **and secure mode** return |
| **x230** | clean | **clean** | stays clean |

So a reload produces a **half-ATMF network with secure mode on one node only** — the exact split
condition that cost time on 2026-09-21. Verify before/after any reload with:

```
show startup-config | include atmf
```

**Nothing was written**, because choosing between "the campaign's clean state" and "the saved
ATMF-era state" is Terrence's call, not a wrap-time tidy (§6 Q1).

### 3.2 The triangle is broken ON PURPOSE

- AR4050S `port1.0.2` is **`admin down` (shutdown)** and removed from `channel-group 1`. It was
  taken down at 08:57 on 09-22 to break a loop before ATMF was stripped, and never restored
  because MRP turned out unrunnable.
- **RSTP is disabled on all three devices** — `spanning-tree mode rstp` plus
  `no spanning-tree rstp enable`, confirmed in running-config on all three at wrap.
  **Closing that leg without a working loop protocol will storm the bench.**
- `po1` is therefore a **single link** on both ends: stack `port4.0.2` ↔ 4050 `port1.0.4`.
  bench-state.md still describes a two-link LAG.

### 3.3 Other deltas

- **Master moved**: bench-state.md records member 2 as master (2026-09-18, post-reboot election).
  It is now **member 3**. Roles move on every failover and never pre-empt — not a health signal.
- **Member 3's flash carries campaign artefacts** from the ATMF node-provisioning work:
  `x230-tb470.rel` (25,785,296 B) and `x230-default.cfg` (1342 B). Member 3 is therefore at
  **40.5 MB free** against ~64 MB on the other three. Not urgent; see §6 Q2.
- **`no lacp global-passive-mode enable`** on the stack, left off deliberately since 2026-09-21 —
  passive mode auto-enrols freed ports into new aggregations and fights explicit port config.
- **QoS is off** (`no mls qos`). `mls qos disable` and `no mls qos enable` are both invalid.
- The x230 runs its own restored `default.cfg`: ports in vlan 100, SVI `10.38.215.2/27`,
  console **9600**.
- `vlan10` (`10.10.10.1/27`) on the stack is **baseline, not debris** — it predates this campaign
  (bench-state.md, 2026-09-18).

---

## 4. Results

All runs below are **clean** unless labelled. A run is *confounded* when something other than the
DUT could explain the number; those are called out in the per-case log and are not graded.

| group | cases | result | README |
| --- | --- | --- | --- |
| ACL | 13 | **11 PASS / 2 UNMEASURED** | [acl-2026-09-22/](acl-2026-09-22/README.md) |
| Authentication | 7 | **1 PASS / 6 UNMEASURED** | [auth-2026-09-22/](auth-2026-09-22/README.md) |
| MRP | 5 | **0 PASS / 5 UNMEASURED** | [mrp-2026-09-22/](mrp-2026-09-22/README.md) |
| QoS | 12 | **9 PASS / 3 UNMEASURED** | [qos-2026-09-22/](qos-2026-09-22/README.md) |
| STP & storm control | 8 | **6 PASS / 2 UNMEASURED** | [stp-2026-09-22/](stp-2026-09-22/README.md) |
| switching | 11 | **6 PASS / 1 PARTIAL / 4 UNMEASURED** | [switching-2026-09-22/](switching-2026-09-22/README.md) |
| IPv6 routing & protocol | 16 | **6 PASS / 10 UNMEASURED** | [ipv6-2026-09-22/](ipv6-2026-09-22/README.md) |
| **total** | **72** | **39 PASS / 1 PARTIAL / 32 UNMEASURED** | |
| ATMF (09-21) | 10 | **7 PASS / 1 FAIL / 2 not executed** | [atmf-2026-09-21/](atmf-2026-09-21/README.md) |

**Read the UNMEASURED count with its reasons before reading it as a score.** The 32 break down as:

| cause | cases |
| --- | --- |
| no line-rate generator (ixia) on this bench | 9 |
| only one cabled copper port per stack member | 14 |
| the case's partner device does not exist here (MRP switches, TACACS+, a BFD-capable peer) | 6 |
| the case has **no steps defined in `ck.db`** (`num_steps = 0`) | 3 |
| the feature's subject is absent (no SFP fitted, etc.) | 4 |

Authentication is the group most likely to be misread: **MAC-auth, web-auth and 802.1X were each
driven end to end and passed.** Those six UNMEASURED are TACACS+ (absent) and cases needing two
simultaneous supplicants — not a failure of the feature.

---

## 5. Findings

### Measured

1. **Member-1 hang does not reproduce under pinning** — 20/20 clean cycles. Rate over all runs
   1/45. The 38377 signature remains a single observation.
2. **The IE520 console prints nothing between `Starting kernel ...` and userspace.** A hang
   anywhere in that window is indistinguishable from a healthy boot **on the console**. This is
   why console evidence is exhausted, and why a more verbose bootloader would not help — the gap
   is after the bootloader has handed off.
3. **`atmf cleanup` is refused on a VCStack.**
4. **A `spanning-tree mode` change silently re-enables spanning tree** and drops a prior
   `no spanning-tree <mode> enable`. Caught during 38487. Re-assert and re-verify forwarding after
   any mode change — a wrong STP baseline would have invalidated every later STP, switching and
   storm-control result without looking like an error.
5. **LACP passive mode hides a live link from STP**: it auto-enrols freed ports into a
   channel-group, and STP then runs on the *aggregator*, so a member link can forward where STP
   has nothing to block.
6. **MAC-auth usernames reach RADIUS as `00-f0-4d-00-77-17`** — lowercase, hyphenated. There is no
   `auth-mac username-format` command on this build.
7. **Default auth host-mode is single-host**: one *failed* supplicant occupies the port, so a good
   supplicant behind it never authenticates.
8. **`mls qos enable` and `no mls qos` both prompt `(y/n)`**, and a driver that feeds the prompt
   the next config line gets `% Command aborted.` **and is logged out of the console.**
9. **`policy-map` / `class-map` do not parse until QoS is enabled globally.**

### Inferred (stated as inference — what would prove it is named)

- **`eth3 → port1.0.1`** comes from one MAC-table entry against a port that reads
  `protocol down`. *Proof:* LLDP on both ends, or a `show mac address-table` taken while traffic
  is actually flowing on `eth3`.
- **The stale `IE520-tb470.rel` boot pointer is harmless** because AW+ falls back to the current
  software. *Observed:* 22 successful reboots on 09-20/21. *Not proven:* that the fallback holds
  for a cold power-cycle as well as a `reload`.

---

## 6. OPEN questions — decisions, not tasks

**Q1. Do the clean running-configs get written to startup, or does the ATMF-era startup stand?**
Writing bakes in the campaign's torn-down state *and* the single-link `po1` and the shut
`port1.0.2` on the 4050. Not writing leaves the §3.1 landmine. Neither is obviously "the bench's
intended state", so nothing was written. *Evidence path:* `show startup-config | include atmf` on
`/dev/u5` and `/dev/u1`.

**Q2. Delete the ATMF provisioning artefacts from member 3's flash?** `x230-tb470.rel` (25.8 MB)
and `x230-default.cfg`. They are this campaign's debris, but a DUT's flash is outside the three
repos, so nothing was deleted without consent. No urgency — 40.5 MB still free.

**Q3. Should a sentinel session be MANDATORY for long autonomous runs?** Terrence, 2026-09-22:
*"It seems that having a sentinel watch over the process is really really valuable, and can help
save and unstick sessions. might need to make it mandatory."* Recorded with its evidence in
`.claude/memory/sentinel-session-keeps-long-runs-moving.md`; **deliberately not implemented**,
because making it mandatory is a process/config change (a hook, or a step in `/orient-dt`).
Recommended home if yes: a step in `/orient-dt`, not a hook — it is a process rule, not a
file-write rule.

**Q4. Where do the harness `.py` files live?** `IE520/test-harness/` holds the **design README
only**. The `.py` files were removed after the `no-stray-py` hook refused them in the lab tree;
the guard points at `ask-ck/functions/test-composer/`, which is a *different repo*. Unresolved.

**Q5. Should bench-state.md now be updated?** It was held back all campaign on instruction. It now
disagrees with the bench on: master member, `po1` link count, the shut 4050 port, and the x230's
existence. **The next `/orient-dt` will orient against a stale source of truth unless this is
folded in.**

---

## 7. Ordered next steps

1. **Answer Q1** and, if writing, `write` on `/dev/u5` and `/dev/u1`, then re-read
   `show startup-config | include atmf` on both to confirm.
2. **Fold §3 into bench-state.md** (Q5) and run `./bench_setup.py apply` in `bench-setup/` — but
   only rewrite the ` ```setup ` fences from a whole, cleanly measured bench. The bench *is* whole
   right now, so this is a good moment.
3. **The standing bench asks**, in order of cases unblocked:
   - **one recable** — a second cabled copper port, ideally straddling two stack members →
     unblocks ~14 cases (ACL 881/885/889/890, QoS 13604's straddling half, the four guest-VLAN
     cases, 38435's failover half, the mirror-destination checks in 943 and 830);
   - **a line-rate source (ixia)** → unblocks 9;
   - **two MRP-capable switches** → unblocks the whole MRP group (5);
   - **steps defined for the three `num_steps = 0` cases** (38435, 38148, and 6005/38151/38487
     were interpreted from their titles — those interpretations are recorded in their logs and
     should be reviewed).
4. **Review the interpretations and judgement calls** recorded in the per-case logs — Terrence
   asked for them to be recorded rather than blocked on.

---

## 8. Recipes — self-contained, this session's scratch is gone

The tb470 scratch (`/tmp/acl/`, tmpfs) will not survive a reboot of tb470. Rebuild what you need:

**Drive a console.** The maintained driver is in the repo at
`IE520/stack-tests/linkflap-38378-2026-09-18/console.py`. From tb470:

```python
import sys
sys.path.insert(0, "/home/terrenceb/claude/device-testing/IE520/stack-tests/linkflap-38378-2026-09-18")
from console import Console
c = Console("/dev/u5", "/tmp/my.log")          # add baud=9600 for the x230 on /dev/u0
c.login(monitor=False)
c.send("terminal length 0", timeout=30)
print(c.send("show stack", timeout=90))
c.send("end", timeout=20); c.s.close()
```

**Rules that were paid for in hardware time:**

- **Abort a config batch on the first `%` error.** A bad line leaves the console in the wrong
  mode, and a blind `exit` chain then logs it out entirely.
- **Never send `<cmd> ?` through a driver that appends CR** — if `<cr>` is a valid completion the
  command *executes*. This enabled ATMF secure mode on a live bench. Probe without the CR.
- **Always `end` before leaving a console.** One left in `configure terminal` answers every `show`
  with `% Invalid input detected at '^' marker` and reads as a dead unit.
- **`ssh tbNNN 'command -v X'` misses `/usr/sbin` and `/sbin`** — it proves presence, never
  absence. This nearly graded two 802.1X cases UNMEASURED wrongly.
- **`ssh tb470 'pgrep -f X'` matches its own `bash -c` wrapper**, so a wait loop never exits. Use
  a sentinel file, or grep a full remote `ps` locally.
- **A rejected or interrupted tool call does not kill an already-dispatched ssh command.** It
  keeps running, keeps changing device state and keeps holding consoles. Re-read device state
  after any interrupt.
- **Run the harness as your own user.** Running it under `sudo` put root-owned logs on the NFS
  share; keep `sudo` inside the subprocesses that need it.

**Measurement discipline** (the two rules that decide whether a result grades at all):
baseline the feature **off** first, and make the traffic **transit** the DUT — inject on one host
NIC, capture on another. And ask what else is in the path: the **x230 is a switch, not a wire**,
and it silently pruned an early set of snooping measurements.

---

## 9. Git — committed, NOT pushed

Working tree is **clean**. This campaign's commits are local only; **Claude cannot push in this
environment** (company-set permissions deny it every time). **The push is Terrence's:**

```bash
cd /media/terrenceb/mnt/testbox_home/claude/device-testing && git push origin main
```

Most recent commits:

```
3aba98e  memory: fold the 72-case campaign's findings into the store
442f9e5  IPv6 routing & protocol group complete: 6 PASS / 10 UNMEASURED
d0df31b  IPv6 routing: BGP4+ 3111, 3112, 3114 all PASS
52ffd67  IPv6 routing: 10874 PASS -- OSPFv3 adjacency syncs across 5 flap cycles
1827cf0  IPv6 routing: 8734 PASS -- Neighbor Advertisement responses
27313de  switching group complete: 6 PASS / 1 PARTIAL / 4 UNMEASURED
a07d4d4  STP & storm control group complete: 6 PASS / 2 UNMEASURED
```

No large or binary artefacts were produced — all 213 files written today are text and committed.

---

## 10. Pointers

- **Topology and bench facts** → `bench-setup/bench-state.md` (**stale in the four ways listed in
  §3 — read §3 first**).
- **Mid-campaign continuity record** → `IE520/RESUME-CAMPAIGN-2026-09-22.md` (written at the
  42/72 mark; §4 holds the same bench deltas).
- **Per-case deliverables** → `IE520/<group>-2026-09-22/<case-id>.log`. The `.log` **is** the
  deliverable; the group README carries the verdict table and the UNMEASURED reasons.
- **Campaign pointer memory** → `.claude/memory/ie520-awptcm-campaign-2026-09-22.md`.
- **The AW+ CLI wiki** → `claude/github-copilot-awplus-wiki/awplus_cli_wiki/commands/`, 3437
  command pages with syntax, mode and platform tables. **Look a command up there before probing
  the CLI** — a `?` probe only completes the prefix you guessed, so guessing wrong returns a
  confident-looking "that option doesn't exist". That is how OSPFv3 interface attachment was
  wrongly declared impossible when `ipv6 router ospf area 0` was one page away. The platform
  tables are a guide, not a gate: the IE520 is missing from tables for commands that work on it.
