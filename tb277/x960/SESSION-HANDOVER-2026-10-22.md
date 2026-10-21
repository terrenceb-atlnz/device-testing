# tb277 / x960 — session handover, 2026-10-22

Covers the campaign run on 2026-10-21 and wrapped on 2026-10-22.

## Session facts
Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None beyond standing orders. Window: partly attended.
             swi_a was treated as must-NOT-be-rebooted for the whole campaign.
             🔴 CORRECTED 2026-10-22 by the Test Engineer: the reason given was WRONG --
             swi_a NETBOOTS, so `Current boot image : Not set` is correct, not a fault.

## TL;DR

The 14-case x960 Management campaign is **complete and wrapped**: **10 PASS, 1 UNSUPPORTED,
2 NOT TESTED, 1 deferred**. All 11 final logs and their `.cfg` files are created; no `work/`
remains.

**The bench is whole.** All three units read at the wrap probe, **Advisories: none**, and
swi_d's running-config is byte-for-byte what every group handed over.

🔴 **Two things are the Test Engineer's, and one of them blocks git.** A **stash nobody in this
session made** sits on the shared working tree, so the required rebase was NOT done; and
**vlan 60 is in swi_d's startup-config** and only the Test Engineer can remove it.

## Current bench state and how to verify it

```bash
cd ~/claude/device-testing
tools/tb precheck tb277 u2,u3,u5

# 🔴 The 9600 consoles must be PINNED FIRST or their login fails — see "The baud trap" below.
printf '%s\n' '<swi_b/swi_a password>' | ssh tb277 'read -r P; export CK_PASSWORD_U3="$P" CK_PASSWORD_U5="$P"; unset P;
  cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 run \
    --consoles u3,u5 --baud 9600 --read-only --no-prompt'
printf '%s\n' '<same password>' | ssh tb277 'read -r P; export CK_PASSWORD_U3="$P" CK_PASSWORD_U5="$P"; unset P;
  cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 run \
    --consoles u2,u3,u5 --no-prompt --pdu 10.36.230.212 --outlet u2=1,u3=7'
```

The password is **not in this repo and must not be put in it**. It goes over **stdin, never a
command line** — `ps` is readable by other users on this shared box. tb277's `python3` is 3.6
and `bench_probe.py` needs 3.7+, so use `python3.8`.

### Per unit, as left

| unit | console | power | state |
| --- | --- | --- | --- |
| swi_d (DUT, AT-x960-56YSQ, S/N A2WQS700B) | u2 @115200 | on | standalone, Ready, Active Master. `sin_x96056-20261019-27`. Boot image `flash:/x960-tb277.rel` **(file exists)**, boot config `flash:/default.cfg` **(file exists)**. Uptime 15:25 at wrap |
| swi_b (AT-x960-28YSQ, S/N A10737A261700021) | u3 @9600 | on | standalone, Active Master. `awplus_main-20261020-78`, bootloader 8.24.0. Boot image `flash:/backup.rel` **(file exists)** |
| swi_a (AT-x950 GEN2-52XSTQm, S/N A10713A262600012) | u5 @9600 | on | standalone, Active Master. `awplus_main-20261019-73`, bootloader 8.24.0. **Boot image `Not set` — because it NETBOOTS**, which is correct for this unit. Its reload depends on tb277 serving TFTP; that path is healthy (below) |

Host NICs eth2, eth3, eth4 all **carrier=1**. The bench flash-boots; no TFTP path to worry about.
🔴 **`/tmp` on tb277 is 96 % full** (1.9 G of 2.0 G). 1.8 G of that is `wireshark_eth4*.pcapng`
**belonging to someone else — not ours to delete**. Bound every capture.

## What was accomplished

The 14-case Management campaign, run by `bench-runner` subagents in four groups under a sentinel.
Queue: `CAMPAIGN-QUEUE-2026-10-21T1159.md`.

## Results — all runs CLEAN, none confounded

**Final logs created**: `/create-logs` commits `3acd081` (access), `9d54134` (mgmt),
`dd7862e` (lldp), `871a23d` (ntp). No `work/` folder remains.

| group | cases | verdicts |
| --- | --- | --- |
| [access-2026-10-21T1159](access-2026-10-21T1159/README.md) | T33379, T33380, T33381 | 3 PASS |
| [mgmt-2026-10-21T1159](mgmt-2026-10-21T1159/README.md) | T33386, T47192, T33387 | 2 PASS, 1 **UNSUPPORTED** |
| [lldp-2026-10-21T1159](lldp-2026-10-21T1159/README.md) | T44296, T33398 | 2 PASS |
| [ntp-2026-10-21T1159](ntp-2026-10-21T1159/README.md) | T33399, T33400, T44298 | 3 PASS |
| — | T33388, T33389 | **NOT TESTED** (Test Engineer's decision) |
| — | T33384 | **deferred** — needs a USB stick; in `MANUAL-ONLY.md` |

🔴 **Seven reboot-persistence limbs were measured — the first in three campaigns.** Three of
them were retro-fitted to T33380, T33386 and T47192 as limb-only run 2s, after the Test Engineer
allowed `write` mid-campaign. Each cost about a fifth of a full re-run.

## Findings

### Measured

- 🔥 **A NUMBERED hardware ACL (3000-3699) holds exactly ONE rule.** Each `access-list <n> <rule>`
  **silently replaces** the previous — no error, nothing in running-config. Every management
  filter is permit-then-deny, so the numbered form **collapses to the deny and locks the
  administrator out**. The driver logs it at `err` at the instant of the loss
  (`exfx_cExt_dxch_rules_pclIdActionUpdate`), and the **named** form is unaffected — that
  contrast is what makes it reportable, and it spans two cases so it lives in the queue.
- 🔥 **`ntp rate-limit` holds exactly ONE keyword**, silently discarding the first. Same family
  as the ACL defect: **two CLI surfaces on this platform that keep only the last value.** ⚠️ This
  one has **no sourced before/after pair** and could not enter a deliverable — see OPEN 4.
- 🔴 **`switchport voice vlan` silently adds `spanning-tree portfast`**, and
  `no switchport voice vlan` leaves `switchport voice vlan priority` and `switchport voice dscp`
  behind.
- 🔴 **NTP server rate limiting is ON BY DEFAULT and invisible in running-config** (burst 8,
  interval 8 s, leak 4). A 20-packet burst gets 11 answers until `ntp rate-limit burst 64` makes
  it 20/20. Without knowing this, normal behaviour reads as a bench fault.
- **`show ntp status` / `show ntp counters` print completely empty output when NTP is not
  configured** — an empty read is a state, not a hung command.
- **The NTP client randomises both its UDP source port and its request transmit timestamp** on
  every poll. A filter on source port 123 misses every packet; that timestamp is not a clock.
- **One `ntp master` serves IPv4 and IPv6 at once**; there is no separate IPv6 enable.
- **`show ntp status` reports `Precision : 0 (1.000000000 seconds)` while the served packet
  carries `precision=-25`** (~30 ns) — 25 binary orders apart. A client acts on the packet.
- **By default LLDP advertises only the three mandatory TLVs** plus one Allied Telesis OUI TLV,
  which is why `show lldp neighbors` shows an empty Sys Name for every AW+ partner. Correct
  behaviour that reads as a defect.
- **`no lldp receive` drops the frame BEFORE the packet counter**, so `In` counts frames
  **accepted**, not **arrived**.
- **An x960-56YSQ cold-boots to its login prompt in 60 s** — `ckreload.py`'s 720 s default is
  wildly conservative here.

### Inferred, not proven

- Nothing in this campaign rests on inference. Every verdict is graded on captured frames or the
  DUT's own counters, never on a `show` alone.

## 🔴 The baud trap — read this before probing tb277 again

`bench_probe.py`'s **baud DETECTION corrupts the login dialog on a 9600 console when a login is
actually required.** It bit at the wrap: u3 and u5 both read `login_failed`, and the first
reading was that their accounts were still locked. They were not. Pinned with `--baud 9600`,
**both logged in in 4.6 s.**

**The discriminator is in the capture's `meta.json`, and it is the whole of the diagnosis:**

| `login:` note | means |
| --- | --- |
| `no prompt after login. tail=''` | an **empty** read — the dialog desynced. **The baud trap.** |
| `... tail='...Login incorrect\r\n\r\nawplus login: '` | a **wrong password** |
| `The account is locked due to N failed logins` | a genuine **lockout** |

A console already at an exec prompt needs no login dialog, so **pin the slow consoles first,
which leaves them logged in, then run the full mixed probe.** That is the recipe in the command
block above and in `orient-dt` §1.

## OPEN questions

1. 🔴 **A stash nobody in this session made is on the shared working tree**, so the git resync
   required by `/wrap-dt` §6 was **NOT done**. `orient-dt` §0a: *a stash you did not make → do
   not continue, skip or abort it; report it and stop.* Evidence:
   `stash@{0}: WIP on main: b2763a1 Merge branches 'main' and 'main' of github.com:terrenceb-atlnz/device-testing`.
   The branch is **46 ahead, 39 behind** `origin/main`. **Both `tools/README.md` and `tools/tb`
   were changed on both sides**, so the rebase will conflict there — and §0a's rule is to merge
   **both** sides' facts, never pick one. Whoever owns that stash should resolve it first.
2. ✅ **CLOSED 2026-10-22 — swi_a's `Not set` boot image is CORRECT: the unit NETBOOTS.**
   The Test Engineer supplied the reason; it was then verified end to end:
   - `/tftproot/x950GEN2-tb277.rel.info` reads **`x950GEN2-awplus_main-20261019-73.rel`**, which
     is **exactly the build swi_a is running** (`awplus_main-20261019-73`);
   - `tftpd-hpa` is **active**, `/tftpboot` is a symlink to `/tftproot`, and the image resolves
     through the served path at 57,869,727 bytes;
   - `Autoboot status : disabled` is consistent — that setting is about booting from external
     media, not about netboot.

   **The real dependency, which replaces the old wrong one:** swi_a's reload needs **tb277 to be
   serving TFTP**. That is a condition to check in seconds, not an unknown that makes the unit
   untouchable. `/orient-dt` §1's netboot rules apply — above all, never leave the TFTP-serving
   NIC pinned, or the next unit to reboot boot-loops.

   **What the wrong reading cost.** The sentinel read `Not set` as a missing pointer that could
   strand the unit, and offered the Test Engineer a "do not reboot swi_a" constraint on that
   basis. He took it, and it stood for the whole campaign — which is why group C could use swi_a
   only as a passive LLDP partner. The constraint was not wrong to accept; the reason given for
   it was.

3. 🔴 **vlan 60 is in swi_d's running-config AND startup-config** (`vlan 60 name ckMGMT-A`,
   `interface vlan60 / ip address 10.38.22.97/27`, plus port1.0.2's trunk lines). It is campaign
   infrastructure the Test Engineer approved saving. Removing it needs
   `no interface vlan60` / `no vlan 60`, which **the permission system refuses for a tester**.
4. 🔴 **`tools/awlogin.py:login()` is still unfixed.** `def login(c, tries=5, ...)` loops up to
   five times and re-sends a **full username and password on every iteration** — against AW+'s
   **five-failure** lockout threshold. It locked swi_b during this campaign. The trigger was a
   username write **truncated at 9600 baud** (`ma`, `manag`), not a wrong credential. **It will
   lock any account it ever fails once against.** Fix before the next campaign on any AW+ bench:
   an explicitly supplied password is tried **once**, and a truncated-echo username is re-sent
   only after proving the echo.
5. **The `ntp rate-limit` single-keyword finding needs a re-run with a quoted before/after
   `show running-config` pair** before it can face a developer. Measured three times, quoted
   never.
6. **T44298's health BEFORE sample has no `show log` read** — a STANDING-ORDERS §8 gap in the
   run, so that case's HEALTH line reports the after sample only.
7. **T33384 (Auto boot from external media) needs a person** to insert a FAT32 USB stick carrying
   `autoboot.txt` plus the release and config it names. The DUT has USB host hardware and **no SD
   slot**. An automatable half is available for a PARTIAL at the cost of one DUT reboot.
8. **swi_b runs `awplus_main-20261020-78`, a different build train from swi_d's
   `sin_x96056-20261019-27`.** Never confirmed as intended. Every LLDP and NTP partner result is
   against it.

## Ordered next steps

1. Resolve the foreign stash (OPEN 1), then do the §0a rebase, then `git push origin main`.
2. Fix `tools/awlogin.py:login()` (OPEN 4) — it is the highest-value fix available and it costs
   nothing on the bench.
3. Remove vlan 60 from swi_d (OPEN 3).
4. Nothing to decide for swi_a (OPEN 2 is closed); before reloading it, just confirm tb277 is serving TFTP.
5. Run T33384's automatable half, or book a person with a USB stick.

## Recipes

**Probe a mixed-baud bench** — the two-step form in the command block above. Never a single
mixed probe when a login will be required on the slow consoles.

**Give the probe a non-default password**, per console, never on a command line:
`CK_PASSWORD_U3` / `CK_PASSWORD_U5` (and `CK_USER_U<n>`), read by `bench_probe.creds_for()`.
When one is supplied it is the **only** password tried — deliberately, because every failed
attempt re-arms AW+'s five-minute lock. `tools/tb` forwards any `CK_PASSWORD*` / `CK_USER*` over
stdin for console tools, and `tools/devclient.py` takes `--password-env NAME`.

**After any reload, ping every leg to 4/4 before reading it.** A login prompt is not readiness.
This bit three times in one hour and once would have **inverted a verdict**: with
`tools/arpleg.py --tcp`, *no reply row* means **silently dropped**, which is exactly what a
working filter looks like.

## Pointers

- Topology: `bench-setup/tb277/bench-state.md` (regenerated at the wrap; all three units,
  eleven links, **Advisories: none**).
- Platform facts: `platforms/x960.md` — §5 read-back-vs-dataplane, §7E AAA, §7F management,
  §7F.10 SSH storage, §7G the silently-swallowed `| exclude`.
- The campaign: `CAMPAIGN-QUEUE-2026-10-21T1159.md`, especially its `## Issues`, which holds
  every finding and both method rules this campaign produced.
- Process reviews: each group's `REVIEW.md` and each case's `<id>-review.md`.
