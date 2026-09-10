# IE520 4-device stack — flash-prep HANDOFF

**Written 2026-09-04 (~12:3x).** Session context filled up; continuing in a fresh session.
Start the new session with `/orient-ie520`, then read this file. This is a *temporary*
experimental topology — the two-unit tb470 bench described by orient §1 is NOT the current state.

---

## The task

Prove/enable a **4-device IE520 VCStack** (u2, u3, u4, u5 — all IE520-28GSX). This has never
been proven; **the existing commands may not allow a 4-way stack to form** — that's the thing
under test.

The bootloader netboots each member over TFTP from tb470, but **only 2 of the 4 can netboot
concurrently** (2 usable TFTP links). To escape that, the plan (user's 3-step ask):

1. Put a flash copy of the current `IE520-tb470.rel` into **each** unit's local flash.
2. **User** switches each unit's bootloader default to flash-boot (they do the bootloader side;
   we do getting the `.rel` into flash). Then TFTP-netboot is irrelevant.
3. Then a single **strip + renumber** pass so a real 4-way stack can form.

u0 and u1 are powered off / disconnected and out of scope.

Standing permissions from user: *"you have permission to de-configure and re-configure all
devices"* and *"configs stripped as much as possible to ensure no further defects in function."*
Caveat: **do NOT reboot an IE520 while its data eth is disconnected** and, more precisely, only
reboot a unit once it is on **flash-boot with a valid flash `.rel`** (otherwise it drops into a
bootloader netboot it can't satisfy — the constraint we're escaping).

---

## Status of the four units

| Unit | S/N | `IE520-tb470.rel` in flash | Bootloader → flash (user) | Current stack role |
|---|---|---|---|---|
| **u5** | 264A23066 | ✓ (TFTP, eth3/10.0.40.1) | ✓ done | ID1 Backup, in a 2-stack w/ u4 |
| **u2** | 264A23068 | ✓ (TFTP, eth2/10.0.41.1) | ✓ done | flashed standalone |
| **u4** | 264A23052 | ✓ (**cross-member** from u5, 206s) | ✓ done | ID2 Active Master, 2-stack w/ u5 |
| **u3** | 264A23061 | ✓ (TFTP, eth2/10.0.41.1) — verified 41107895 B, 63.6M free | ✗ **pending (user)** | ID2 Master; ID1 partner stuck "Discovering" |

Target file size on success: **41107895 bytes** (this build already lands at exactly that; it's
the netboot image, not a fresh TFTP write, so the usual +352-byte artefact doesn't apply here).

### u3 copy — DONE ✓ (verified after the handoff was first written)
- Task `bh3ckhyo7` completed: `Successful operation`, elapsed 402s. `verify swi_f` confirms
  `IE520-tb470.rel` at **41107895 bytes**, flash **63.6M free**. **All four units are flashed.**
- Leftover temp config still on u3 from the copy: SVI `vlan1 = 10.0.41.3/24`, and `port2.0.1` /
  `port2.0.5` left `shutdown` were **not** applied (that edit was rejected — user unplugged
  instead). These get wiped in the strip pass anyway.
- **Only remaining flash-prep item: user switches u3's bootloader to flash-boot.**

---

## Remaining work

1. **u3 copy verified ✓.** Just waiting on the user to set **u3's bootloader to flash-boot** →
   that completes *all four flashed + flash-boot*.
2. **Config phase — one strip + renumber pass.** BLOCKED ON A USER DECISION:
   - **ID → unit mapping** for the 4-stack (which physical unit is ID 1 / master?).
   - Root cause of the 4-way failure: **all four share Virtual Chassis ID `0x a66`
     (`0000.cd37.0a66`) with duplicate stack IDs** — two ID-1s and two ID-2s — so they form
     broken 2+2 sub-stacks that reject each other as **"Neighbor incompatible" / duplicate-master**
     (this is also why u4 was earlier "Disabled Master / err-disabled" — config-driven leftover,
     **not** hardware). Fix = renumber to **unique IDs 1–4 under one chassis-id**.
   - **Renumber reloads the unit** → only renumber-reload a unit that is already flashed + on
     flash-boot. So do this *after* step 1 for all four.
3. **User's cleanup instruction** (fold into the same pass, per stack/master, once all flashed):
   *"clean the dirs of anything that isn't Gui, log, or the recent .rel, then put a fresh config
   that only has stacking."*
   - **Keep:** `gui-userdata/`, `awplus-gui_999_99.gui`, `log/`, `IE520-tb470.rel`.
   - **Delete:** `debug-*.tgz`, `exception.log`, `kernel-*.txt`, `tech-support*.gz`, old dated
     `*.rel`, `test*.txt`; and `default.cfg` / `stack.cfg` are replaced by the fresh
     stacking-only config.
   - NB: for units already stacked (u4+u5) the running-config is **unified on the master** — a
     config strip is a per-*stack* action, not per-unit.

---

## Tooling & access (all commands run ON tb470)

- **SSH:** `sock=/run/user/1971/keyring/ssh; SSH_AUTH_SOCK=$sock ssh tb470 …`
  (the Mac-forwarded agent is empty; this sock holds the key). Read `TESTBOX-ACCESS.md` first.
- **`flash_prep.py`** — staged in this session's scratchpad and on tb470 at **`/tmp/flash_prep.py`**;
  run from **`/tmp/flashprep-recon`**. Ops: `setip｜copy｜verify｜port｜openport｜rmfile`.
  Needs `FLASH_SETUP=…` and `PYTHONPATH=/home/st-art`. `REL=IE520-tb470.rel`.
  `copy <dev> <server-ip>` = `copy tftp://<server>/IE520-tb470.rel flash:/…` (maxWait 1500).
- **`/tmp/flash4.setup`** on tb470 — copy of the live `tb470.setup` with `swi_e=/dev/u2` and
  `swi_f=/dev/u3` added to `[switch]` and `[baudrates]=115200` (u2/u3 aren't in the live setup).
- **Console/setup names:**
  - `swi_e` = **u2**, `swi_f` = **u3** (via `flash4.setup`).
  - `swi_b` = the **u4+u5 STACK**, *not a single unit*. `flash:` = current **master's** flash;
    address members as `awplus-1/flash:` (ID1=u5) and `awplus-2/flash:` (ID2=u4).
  - base `tb470.setup` `swi_a..swi_d` = the original tb470 units.
- **Cross-member copy** (no IP, ~3.5 min, +0 bytes): from the stack master's console,
  `copy awplus-<memberID>/flash:/IE520-tb470.rel flash:/IE520-tb470.rel`. Used to flash u4 from u5.

## Bench cabling NOW (verified by carrier test this session)

- **tb470 eth2 (`10.0.41.1/24`) ↔ u3 `port2.0.3`** — the live flash path (only eth up now).
- eth1 (`10.38.215.1/27`) and eth3 (`10.0.40.1/24`) were mapped to u3 `port2.0.5` / `port2.0.1`
  but the **user unplugged both** (kept only port3 to kill the vlan-1 loop). eth1 had earlier
  been on the u4+u5 stack.
- **u3 is stack ID2** → real ports are `port2.0.x`; `port1.0.x` are phantom/`Provisioned`.
  Front port N = `port2.0.N`. (This trap is silent — naming the wrong range is accepted.)

## Gotchas learned this session

- **Stack ID decides port naming** — always confirm the ID before naming a port.
- **swi_b `flash:` is the master's flash**, and the master can change under you (priority 1 wins;
  u4 became master over u5). The first "u5 flash" is on u5's local flash = now `awplus-1/flash:`.
- **`0xa66` duplicate chassis-id / duplicate IDs = the whole 4-way problem.** Stripping stack
  identity + unique renumber is the fix.
- **Framework driver hangs on async log chatter** (Pluggable/VCS lines) — long elapsed ≠ failed
  write. Verify with `dir`.
- **Delete old dated `.rel`s for space before a TFTP copy** (u2 and u3 both needed it; a full
  flash gives `% Destination file system out of space`).
- **Pluggable reseat:** a loose SFP logs `Pluggable[415]: … inserted into portX` (local6.crit)
  then `NSM[620]: Port up …`. That's the "hotplug" path — not HSL/IMISH. (u3's port-1 SFP was
  loose; user has since swapped it out.)
- **`show log tail -20`** works (no pipe); `show log | tail` is invalid; `show log | include <re>` works.

## Side quest (DONE — do not redo)
`~/.claude/settings.json` had `claude-opus-4-8[1m]` added to `model`+`availableModels`. User has
since set the model to `claude-fable-5-1[1m]` themselves — **do not revert it.**
