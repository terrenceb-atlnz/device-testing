# After-action — TEST 17688, Disabled-Master via resiliency link

**Bench:** tb470, AT-IE520-28GSX stack (virtual-chassis-id 3439)
**Session:** 2026-08-17 13:30 → 2026-08-18 08:20 NZST (device timestamps in logs are **UTC**)
**Software:** `IE520-tb470.rel`, `tomahawk_ie520-continuous`, built 2026-08-10, `AlliedWare Plus (TM) 0.0.0`
**Driven by:** hand, via pyserial on tb470. **Not** an ATTestSet framework run — so there are no
framework logs, and nothing reached any results DB.
**Evidence:** [`17688.log`](17688.log) (full transcript) plus 10 console captures `17688-*.log`.

---

## Headline

**17688 FAILS at step 3, and the cause is a product defect, not the bench.**

The backup stack member never enters Disabled-Master. It promotes itself to a full Active Master
and **keeps the virtual MAC**, producing two switches that are indistinguishable on the network.
The root cause is upstream of the test: **on this build, whichever member holds the backup role
receives 100 % of the master's resiliency-link healthchecks error-free and never registers them.**

| Verdict | Steps |
|---|---|
| **PASS** | 2 — steps 10, 11 |
| **FAIL** | 1 — step 3 |
| **UNMEASURED (blocked by step 3)** | 4 — steps 4, 5, 6, 7 |
| **Observed by a different route** | 1 — step 9 |
| Procedural / setup | 3 — steps 1, 2, 8 |

---

## Per-step verdicts

There is **no prior bench result for 17688** to compare against — this is its first run here. The
adjacent 2026-08-13 runs (`17041.log`, `17545.log`) touch the same subsystem and are cited below
where they establish a baseline.

| # | Step | Verdict | Evidence / prior-bench note |
|---|---|---|---|
| 1 | Configure as per setup/configs | **Setup — done, config absent from the case** | Case ships no step-1 config. Built it ourselves: `stack resiliencylink vlan4093` + `switchport resiliencylink` on both ends, per `stack_cmd/stack_resiliencylink_ag.html`. Also enabled `stack virtual-mac` (VMAC `0000.cd37.0d6f`) so steps 10/11 had a referent. **Prior bench: 17041 and 17545 both record `Resiliency link status: Not configured`** — this is the first time it has been configured on tb470. |
| 2 | Pull the stacking cables | **Procedural — done** | Terrence pulled `port1.0.27`↔`port2.0.28` and `port1.0.28`↔`port2.0.27` at 19:56:28 UTC. |
| 3 | Slave transitioned to Disabled-Master | **FAIL — product** | `VCS: Contact with the Active Master has been lost` → `Member 1 (84e3.2787.0740) has become the Active Master` → `Stack Virtual MAC is 0000.cd37.0d6f`. Both units then read `Operational Status: Standalone unit` with the **same** stack MAC and the **same** `vlan1 10.38.215.20/27`. Ports were never disabled. |
| 4 | `no shutdown` all ports on the Disabled Master | **UNMEASURED — blocked** | No Disabled-Master exists and no ports were disabled, so there is nothing to un-shut. |
| 5 | Other devices' tables show the REAL MAC | **UNMEASURED — blocked** | Requires a Disabled-Master. The promoted unit **kept the VMAC** rather than reverting to its real `84e3.2787.0740`, so the real-vs-virtual distinction the step tests never arose. |
| 6 | `show stack detail` contains the REAL MAC | **UNMEASURED — blocked** | As step 5. |
| 7 | `show mac address-table` contains the REAL MAC | **UNMEASURED — blocked** | As step 5. |
| 8 | Reconnect stacking cables | **Procedural — done** | Both pairs reconnected. |
| 9 | Disabled Master reboots and rejoins | **Observed by a different route — NOT a pass** | A unit did reboot and rejoin (member 2, 20:06:09 UTC). But it was the **original master losing a duplicate-master election** to the self-promoted member 1 (lower MAC `…0740`) — not a Disabled-Master recovering. The mechanism under test never engaged. |
| 10 | `show stack detail` has the original VMAC / chassis-id | **PASS** | `Virtual Chassis ID 3439 (0xd6f)`, `Virtual MAC address 0000.cd37.0d6f` — both original values retained after the reform. |
| 11 | `show mac address-table` has the original VMAC | **PASS** | `1  CPU  0000.cd37.0d6f  forward  static`. |

---

## The defect

**On this build, the backup stack member does not register resiliency-link healthchecks.**

The Active Master transmits 64-byte multicast healthchecks at ~2/sec. The backup's MAC receives
every one of them with zero errors, transmits no reply, and `show stack resiliencylink` reports
`Status: Failed` — documented as *"Not receiving any healthchecks from the Active Master."*

### Reproduction matrix — 4 port pairs, all identical

| # | Pair | Media | Speed | Numbering | Master TX | Backup RX | Backup TX | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | `1.0.7`↔`2.0.7` | 1000BASE-SX | 1 G | matched | 409 mcast | 424, 0 err | **0** | `Failed` |
| 2 | `1.0.25`↔`2.0.25` | 10GBASE-SR | 10 G | matched | 393 mcast | 408, 0 err | **0** | `Failed` |
| 3 | `1.0.26`↔`2.0.25` | 10GBASE-SR | 10 G | **mismatched** | 492 mcast | 1086, 0 err | **0** | `Failed` |
| 4 | `1.0.27`↔`2.0.28` | 1xCOPPER PAS | 10 G | **stacking PHYs** | 395 mcast | 409, 0 err | 17¹ | `Failed` |

¹ 17 reverse packets ≈ 4 % of the send rate — not a reply-per-healthcheck.

### Role, not unit — proven by master swap

`reboot stack-member 1` swapped the roles. The fault swapped with them:

| Unit | Bootloader | as Master | as Backup |
|---|---|---|---|
| `264A23066` (`84e3.2787.0740`) | `9.1.0` | `Configured` ✔ | **`Failed`** |
| `264A23052` (`84e3.2787.09c0`) | `pauld` | `Configured` ✔ | **`Failed`** |

Confirmed a **fourth** time when the stack reformed at step 8 with the roles swapped back.

### Excluded causes

Cabling · optics · fibre pair · pluggable modules · media type (3 distinct PHY types) · link speed ·
port number · matched-vs-mismatched numbering · ASIC port · STP blocking · VLAN choice · config
content, ordering, save and sync · stackport interference · settling time · **both physical units** ·
**both roles** · **both bootloader builds** · 4 full reboots.

### Demonstrated network consequence

Not merely a status field. With the stack split, the AR4050S neighbour saw **the same bridge ID on
two ports** and could not distinguish the two switches:

```
Root Id   8000:0000cd370d6f          <- the VMAC became STP root
port1.0.3 8000:0000cd370d6f  Alternate  Discarding
port1.0.4 8000:0000cd370d6f  Rootport   Forwarding
```

STP blackholed one unit. tb470 could ping `10.38.215.20` with no way to know which unit answered.
This is verbatim the hazard the CLI reference warns of for a non-functional resiliency link:
*"the stack will assume the master is NOT present in the network, which could cause network
conflicts if the master is still online."*

---

## Separate finding — a bench doc is now stale

**`TESTBOX-ACCESS.md` §4a is wrong for this build.** It records (2026-07-30) that on the IE520,
ports 27/28 are dedicated stackports where *"`no stackport` is accepted and saved, but the flag
returns after reboot on the real member's ports."*

It did **not** return. `no stackport` on `port1.0.27` and `port2.0.28` survived the reboot cleanly —
both came back as ordinary `switchport`s in vlan 1, and the stack ran happily on the single
remaining pair `port1.0.28`↔`port2.0.27`. Either the behaviour changed in this software, or the
July observation had another cause. **Left unedited deliberately** — correcting a bench doc is a
change to make on purpose, not as a side effect.

---

## Bench state left behind

**Healthy, stacked and re-runnable.**

| | |
|---|---|
| Operational Status | `Normal operation` |
| Stack | ID 1 `84e3.2787.0740` Active Master (`awplus`, `/dev/u5`) · ID 2 `84e3.2787.09c0` Backup (`awplus-2`, `/dev/u4`), both `Ready` |
| Virtual chassis / MAC | `3439 (0xd6f)` / `0000.cd37.0d6f` — **`stack virtual-mac` was enabled by this session** |
| Stacking link | `port1.0.28`↔`port2.0.27` (single pair) |
| Resiliency link | `vlan4093`, `port1.0.27`↔`port2.0.28` |
| Boot | both members **netboot via TFTP** from tb470 (`IE520-tb470.rel`); boot config `flash:/stack.cfg`, exists |
| Consoles | both free, 115200 |

### Config this session added — remove if you want the bench as it was

- `stack virtual-mac` (needs a reboot to take effect either way)
- `stack resiliencylink vlan4093` + `switchport resiliencylink` on `port1.0.27` / `port2.0.28`
- `no stackport` on `port1.0.25`, `port1.0.26`, `port1.0.27`, `port2.0.28`
- **`interface vlan1 / ip address 10.38.215.20/27`** — ⚠️ **recommend removing.** It was added so
  steps 5/7 had traffic to learn from. While the stack is intact it is harmless, but **any future
  split puts two units on that address again**, on the only segment with an upstream return path.

---

## Retest on a newer build — 2026-08-18 — **defect NOT fixed**

The image was replaced (`tb470:/tftproot/IE520-tb470.rel`, written 2026-08-18 08:44 — both units
netboot, so that file is what they run). It is a genuinely different build, but note its **own
build date is `Fri Aug 14 02:40:47 UTC 2026`**, not same-day — worth confirming it is the intended
image before drawing conclusions about "the latest build".

| | Aug 10 build | **Aug 14 build** |
|---|---|---|
| Master TX | 395 mcast | **464 mcast** |
| Backup RX | 409, 0 err | **399, 0 err** |
| Backup TX | 17 | **0** |
| Backup `Status` | `Failed` | **`Failed`** |

Config survived the update (chassis-id 3439, VMAC `0000.cd37.0d6f`, resiliency link on
`port1.0.27`↔`port2.0.28`). Roles flipped during the update — member 1 is now the backup, and the
failure **moved with it**, giving a fifth role permutation:

| Roles | Which member reports `Failed` |
|---|---|
| m1 master / m2 backup | m2 |
| m2 master / m1 backup (deliberate swap) | m1 |
| m1 master / m2 backup (after step-8 reform) | m2 |
| m2 master / m1 backup (after build update) | m1 |

**The defect is unchanged across two builds.** Everything in this report still stands.

---

## Caveats

1. **Dev builds only, no release-build comparison.** `AlliedWare Plus (TM) 0.0.0`,
   `tomahawk_ie520-continuous`, builds dated 2026-08-10 and 2026-08-14. Someone should confirm the
   defect against a **release** build before it goes to the build owner.
2. **Step 1 config was authored by us**, because the case ships none. The method follows the CLI
   reference exactly, but the case's intended topology is unknown and may differ.
3. **`stack virtual-mac` was off** when the session started; steps 10/11 would have had no literal
   referent without enabling it. Their PASS is therefore against a VMAC this session introduced.
4. **Steps 4–7 are UNMEASURED, not passes.** No positive evidence was gathered for them and none
   should be inferred.
5. **Nothing was published to any results DB** — this was a manual console run. `17688.log` and the
   console captures are the only record.
6. The two units run **different bootloader builds** (`9.1.0` and `pauld`). Irrelevant to this
   defect — proven by the master swap — but relevant to anything bootloader-shaped.
7. `Not all stack ports are up` appeared throughout the early session as a **pre-existing** artefact
   of `port1.0.25`/`1.0.26` being configured stackports with no cable. Cleared mid-session; readings
   after that point are against a clean `Normal operation` baseline.

---

## Recommended follow-ups

1. **Raise the resiliency-link defect** with the build owner, with the 4-pair matrix and the
   master-swap result. It is reproducible in minutes and the network consequence is demonstrable.
2. **Re-test on a release build** to establish whether this is a regression in the continuous branch.
3. **Re-run 17688 once the resiliency link works** — steps 4–7 have never been exercised on this
   platform and remain genuinely unknown, not passing.
4. **Decide on `TESTBOX-ACCESS.md` §4a** (stackport persistence) and on removing `vlan1 10.38.215.20/27`.
