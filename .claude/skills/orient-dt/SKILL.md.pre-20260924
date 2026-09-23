---
name: orient-dt
description: Orient a tb470 IE520 bench session — ground-truth the hardware, reconcile it against bench-state.md (the ONLY home for bench facts), load the platform/driver/framework traps that don't rot, then brief the user and wait. Use at the start of any session that will touch the tb470 IE520s. Pairs with /wrap-dt.
---

# Orient — tb470 IE520 bench

For sessions that run tests against the tb470 IE520s. **Nothing about what is ON the bench is
written in this file** — how many units, which console is which, stack membership and roles,
cabling, VLANs, addressing, boot source, PDU outlets, what is shut. All of that is a bench fact,
and bench facts have exactly one home: **`bench-setup/bench-state.md`, "Current state — <latest
date>"**, read against the hardware at the start of every session (§1). This file holds what does
not rot: platform facts, driver and framework mechanics, and the traps that have each cost a
session. Establish state from **reality**, load the facts that don't rot, then brief the user and
wait.

## 0. Where things live (paths as at 2026-09-11 — update HERE, nowhere else)

Repo root = `claude/device-testing/` on the NFS lab home (`/media/terrenceb/mnt/testbox_home/` from
this host, `/home/terrenceb/` as tb470 sees it). Paths below are repo-relative. **Every other
section refers to these by NAME**; when something moves, fix this table and nothing else.

| name | path | notes |
| --- | --- | --- |
| **bench-state.md** | `bench-setup/bench-state.md` | the bench source of truth; generates `tb470.setup` via `bench-setup/bench_setup.py` |
| **session handovers** | `IE520/SESSION-HANDOVER-<YYYY-MM-DD>.md` | latest first; `/wrap-dt` writes them |
| **per-case logs** | `IE520/<suite>/<case-id>.log` | e.g. `IE520/ipv4-routing/10623.log` |
| **console.py** (the maintained driver) | `IE520/stack-tests/2026-09-02-driver-test/console.py` | older copies sit in other run dirs; copy this one to tb470 `/tmp/ckorient/` and import from there (paths under the NFS home have moved mid-session before) |
| **memories** | `.claude/memory/` in this repo (after the 2026-09-11 split; until it lands, `claude/Test-cases/.claude/memory/`) | index `MEMORY.md`; Test-cases symlinks to ours |
| **skills** | `.claude/skills/orient-dt`, `.claude/skills/wrap-dt` | renamed from `orient-ie520`/`wrap-ie520` on 2026-09-11 |
| **framework** | `framework -> /home/st-art/framework` | READ-ONLY; not ours |
| **resiliency-link evidence** | `IE520/stack-tests/resiliency-link/after-action-17688.md` | |
| **TESTBOX-ACCESS.md** | `claude/Test-cases/TESTBOX-ACCESS.md` ¹ | SSH agent socket, `.setup` is declarative |
| **TB470-HOST-NETWORKING.md** | `claude/Test-cases/TB470-HOST-NETWORKING.md` ¹ | host NICs, DHCP/TFTP, return path |
| **bench_probe.py** (standalone bench source-of-truth, 2026-09-15) | `bench-setup/bench_probe.py` | sweeps `/dev/u0`–`u6` identically every run, depends on NOTHING (no `.setup`, no bench-state.md) — it FEEDS bench-state.md. Also lists EACH member's own flash (`dir awplus-N/flash:`) and maps every up host NIC→switch port (ping + filtered `show mac address-table`). **stdout-only:** JSON to stdout, summary to stderr — no `--json` flag (`python3 bench_probe.py [--consoles 0-6] > /tmp/probe.json`); the JSON is transient, read it then discard. Run it ON tb470. **This is the probe to use for bench state.** |
| **bench_probe.py** (older *framework-driver* reads — different tool, same name) | `claude/Test-cases/ask-ck/functions/test-composer/bench_probe.py` ¹ | binds devices via the `.setup`; used by the test-composer. Archived revisions in `IE520/stack-tests/bench-probe-*/` |
| **bench_topology.py** (verify-setup: probe→md, md-vs-template diff, 2026-09-15) | `bench-setup/bench_topology.py` | `generate <probe.json>` → live physical-topology `.md` (with `​```setup` fences + a `​```nic-state` block); `diff <live> <template>` → semantic `.setup`-vs-`.setup` compare (comment/order-insensitive; handles multi-stack). Exit 0 MATCH / 1 MISMATCH / 2 NEEDS-CHECK; labels MOVED/LINK_DOWN/CHECK_CABLE. Static scaffold (outlets/caps) hardcoded per-bench for now. |
| **fw_async_test.py / fw_async_chatter.py** | `claude/Test-cases/ask-ck/test-composer/` ¹ | the §3 chatter regression |
| **working style** | `claude/Test-cases/CLAUDE.md` §"How we work" ¹ | |

¹ Still in the Test-cases repo and **expected to move into this repo**. If a path is stale,
`find claude -name <file> -not -path '*/framework/*'` from the lab home, then fix this table.

**Scope: tb470 only.** Nothing here describes another bench. `tb504` is a shared testbox outside
our control — do not target it and do not propose it as a second bench; its historical results
remain valid evidence, the hardware is not ours to use.

**Design rule for this file.** Three kinds of content, kept deliberately separate:

- **§2, §3 and §4 are immutable platform, tooling and framework facts.** Each one has already cost
  hardware hours or been mistaken for a defect. Do not convert them to lookups.
- **§1, §6 and §7 describe HOW to read the bench and WHAT to plan for — never what the bench
  currently is.** Bench state, stack state, roles, addresses, boot source and flash contents are
  **always** a live lookup reconciled against bench-state.md.
- **Every claim here was verified against the hardware or the source on the date it carries.** If
  you correct one, date it and say what you measured.
- **A bench fact found in this file is a leftover** (Terrence, 2026-09-11: *"point any topology
  references … to bench-state.md, so we can stop having these stale leftovers"*). Move it to
  bench-state.md and leave a pointer; do not refresh it in place.

Before touching hardware, read **TESTBOX-ACCESS.md** (§0) **in full** — SSH from this host needs
an explicit `SSH_AUTH_SOCK`, and a `.setup` file is declarative and may not match the bench.
Working style is the **"How we work"** section (§0): no time pressure, verify facts yourself,
**ask about decisions**, and don't work beyond the literal ask.

---

## 1. Ground-truth the bench — recorded state is always stale

**The consoles are on tb470, not on this host.** `/dev/u2`…`/dev/u5` do not exist locally;
every command below runs *on the testbox*. This has confused a session before.

```bash
sock=/run/user/1971/keyring/ssh          # the Mac-forwarded agent is EMPTY; this one has the key
ssh -o BatchMode=yes tb470 hostname      # with SSH_AUTH_SOCK=$sock

# Is the console free?  fuser, NOT pgrep (pgrep matches its own command line)
SSH_AUTH_SOCK=$sock ssh tb470 'fuser -v /dev/u*; ls /var/lock/LCK..*; pgrep -a minicom'   # which uN exist: bench-state.md
# fuser on the DEVICE NODE is the only reliable answer. 2026-09-09: minicom held three consoles,
# then bench_probe.py held FOUR for ~45 min; and pgrep -f -- even with the [b]racket trick --
# matched its own ssh wrapper. Two readers on one port give "device reports readiness to read but
# returned no data (device disconnected or multiple access on port?)", which reads like a dead unit.
```

Then read the DUT (read-only): `show system serialnumber`, `show stack`, `show stack detail`,
`show boot`, `show version`, `show file systems`, `dir`, `show reboot history`.

Once you have read the hardware, reconcile it against **bench-state.md** (§0) — that file is the
source of truth for what is cabled to what, PDU outlets, addressing, boot source and what is shut,
and `/home/st-art/st-art/configs/tb470.setup` is generated from it. Check for drift with
`./bench_setup.py check` in `bench-setup/`. Hardware still wins: if the two disagree, the record is
stale, so fix the record (edit it and run `bench_setup.py apply`) rather than working around it.
**Never hand-edit the `.setup` on the box** and never write a `.bak` beside it.

**Don't interrogate the hardware for facts the file format already answers** (Terrence,
2026-07-30: *"this is a `.setup` input, not an interrogation"*). The letter-vs-number PDU outlet
question was settled by one grep of `Setup.py`; pinging the PDU and curling its web UI added
nothing. Probe hardware when the fact genuinely changes file content and cannot be derived —
otherwise read the format. This cuts the other way too: §3 trap 5's baud plumbing was settled by
reading `Setup.py`, after a docstring had been taken at face value and got it wrong.

### Bench identity — confirm by serial number, never by a record

Records have had units on the wrong consoles **twice** (2026-09-02: the two stack members
reversed; 2026-09-09: the whole population had moved — the pair the record called "the stack" was
standalone units, and the real stack was a different pair on consoles the record didn't list).
**The console → unit → S/N → stack-ID → PDU-outlet map is in bench-state.md** (§0) and nowhere
else; it is not repeated here on purpose. What is durable is *how* to read it:

- Identify a unit by **`show system serialnumber`**. The login banner is a *role* identifier, not a
  unit one (bare `awplus` = whichever unit is currently master; `awplus-N` = member N), so neither
  it nor the shared prompt tells you which physical unit you are on.
- **The stack ID is the load-bearing column, because it decides port naming** (`portN.0.x`), and
  **stack IDs need not start at 1** — a standalone unit that was ever member 2 keeps `port2.0.x`.
  Confirm which ID a unit holds before any step that names a port: config naming the wrong range is
  accepted **silently** (this once presented as a DHCP option-61 defect that did not exist).
- **Which member is master changes on its own and is normally not worth recording.** The exception
  is a failover test: there the master IS the question — it decides which unit you cut and which
  member your traffic must be sourced on — and because rejoining never re-elects, **it moves after
  every failover**. Read `show stack` immediately before acting, every time (§6).
- Both members' consoles reach the stack CLI once logged in, but a **backup member's console has
  its own login** (`awplus-N login:`), and `console.py`'s `login()` only handles it from a clean
  prompt — a `Password:` in the tail means the port was left mid-dialog; send a CR and retry
  (2026-09-11).

### Five things that present as something else

- **A DESTACKED UNIT KEEPS ITS OLD STACK ID — the *phantom-port* trap.** Its whole old-range
  (e.g. `port1.0.x`) goes phantom — `Provisioned`, MAC `0000.0000.0000` — while the real ports are
  the other range. Whether any unit is in that state today is a bench fact (bench-state.md);
  verify which case you are in before naming a port.
- **BOOT SOURCE IS A BENCH FACT (bench-state.md → "Boot") AND IT HAS FLIPPED BEFORE.** The units
  can boot two ways, and each way has its own traps that have been misread as faults:
  - **Flash boot** (the state Terrence set on all units from the bootloader config on 2026-09-11):
    a plain `reload` is safe. **But `show boot` must read `Current boot image : … (file exists)`
    before you reload** — the stack was running `IE520-tb470.rel` while its boot pointer named a
    deleted `tomahawk` file; `boot system flash:/<the .rel that exists>` fixes it and, on a stack,
    **syncs the 40 MB image to the other member with the console dark for ~10–12 min** (§2 SPIFlash)
    — wait it out. Memory: `tb470-ie520-flash-boot-reboots-ok`.
  - **TFTP netboot** (the 2026-09-02 → 09-10 state; bootloader autoboots from tb470
    `/tftproot/IE520-tb470.rel`, re-fetched on every reboot). Three things read as faults and are
    not: AW+'s `Autoboot status : disabled` is the AW+-level setting, not the bootloader's;
    `show boot … (file not found)` or an empty flash is NOT a unit that cannot boot; and
    `local6.alert … booted from non-default location, SW version auto synchronization cannot be
    supported` is normal. Two hazards ARE real: replacing that one file while the bench is live
    arms the version split (below), and **a member that cannot reach the TFTP server never comes
    back** — it boot-loops (`Failed to load tftp://…` → `Restarting system in 5..` → `BootROM`,
    ~5/min, indefinitely; the survivor reads `Standalone unit`, peer `Provisioned`, both stackports
    `Down` — an *absent* peer, not a split, §6). So: prefer `reload stack-member <id>` over a PDU
    cut unless the TFTP path is proven up, and **never leave the TFTP-serving host NIC pinned
    1000-only** (`advertise 0x20`) — the bootloader's ASIX dongle is 10/100-class; restore
    `advertise 0x2f`.
- **The release filename is CONSTANT BY CONVENTION and carries no date** — a build is loaded under
  the name of the testbox it came from, so on tb470 it is `IE520-tb470.rel`. `show system`'s
  `Current software : IE520-tb470.rel` is therefore **correct and expected**; it is not a
  mislabel, an oddity or something to chase. A *dated* filename in flash (the historical
  `IE520-20260825.rel`) is the deviation, not the norm. Read the build from `show system`'s
  `Software version` / `Build date`, or `show version` — **never from the filename**.
- **A NEWER BUILD DATE IS NOT DRIFT.** These units deliberately track the newest mainline build,
  so a build date that has moved since anyone last looked is the bench working as intended. Do not
  open a session by reporting it as drift, and never compare the live date against one written
  down in a file. From **2026-09-02** releases are `awplus_main` plus a coded date (first one:
  `IE520-awplus_main-20260902-1700.rel`), which supersedes the `tomahawk_ie520-continuous` builds;
  the `.info` beside a staged `/tftproot` image gives its full dated name.
- **🔥 WHAT ACTUALLY BREAKS THINGS IS A VERSION MISMATCH *BETWEEN THE TWO MEMBERS* — AND NEITHER
  THE FILENAME NOR `show boot` WILL SHOW IT.** Under netboot a member that reboots comes back on
  **whatever `/tftproot/IE520-tb470.rel` holds at that instant** while the other keeps the build it
  already had; under flash boot the same happens if the two members' flash images differ (S/W
  auto-sync normally prevents it — check `show stack detail`).
  Nothing on the DUT records the difference: the filename never changes, and `show boot` describes
  a flash image the units do not even boot from. A VCStack will not stay formed across that
  mismatch, so the stack **splits**. Observed exactly this way on 2026-09-02:
  member 1 rebooted unattended at 10:42:58, came back on `08/30/26 23:47:03` against member 2's
  `08/25/26 05:33:09`, and both units sat as masters seeing each other as `Provisioned`.
  **⇒ Compare the build date on BOTH members against EACH OTHER. `show boot` is not evidence.**
  After any unexpected reboot, compare the two before trusting the stack.
- **Console rate is not fixed and not interesting** — the IE520 runs at either 9600 or 115200.
  What matters is that the `.setup`'s `[baudrates]` matches the bench, because
  `AWPConsoleCore._connect_serial()` opens the port once and never renegotiates. A mismatch looks
  like a dead console: a bare CR returns a few garbage bytes, not silence.
- **The bootloader-side link is only up DURING BOOT.** Testbox-side carrier is *not* a valid
  pre-flight check — a working TFTP path looks identical to an unplugged one until the DUT
  power-cycles.
- **UNEXPECTED REBOOTS HAPPEN ON BOTH MEMBERS, AND ACROSS THE FLEET.** Terrence, 2026-09-02:
  *"ive had word that all of our units do it"*, and *"we will be keeping an eye on BOTH members"*.
  Both carry unattended `Unexpected System reboot` entries — member 1 at 2026-08-31 22:10 and
  2026-09-02 05:35 / 10:42; member 2 at 2026-08-29 05:57 / 10:17 and 2026-08-31 10:48. So do
  **not** attribute one to a single bad unit, and do not treat a reboot as evidence of a defect in
  whatever you were testing. **Check any unexplained stack event against `show reboot history` on
  BOTH members first**, and report a change in *rate* or a new *signature* rather than the bare
  fact of a reboot.

Only `10.38.215.0/24` has an upstream return path and tb470 has **no NAT** (proof commands and
the DHCP/routing/capture detail: **TB470-HOST-NETWORKING.md**, §0). The virtual chassis ID, whether
`stack virtual-mac` is enabled, and member priorities are **bench facts → bench-state.md**. The
mechanic that does not rot (measured 2026-09-11, T10623): **with virtual-mac disabled the stack MAC
is the master's base MAC and CHANGES at failover** — the host keeps sending to the dead master's
MAC until ARP staleness expires, a **23 s** outage; **with `stack virtual-mac` the MAC is derived
from the chassis ID and HELD**, and the same failover costs **~2 s**. `stack virtual-mac` needs a
save + reboot to take effect. Log: `IE520/ipv4-routing/10623.log`.

---

## 2. IE520 platform facts — permanent, not bench gaps

Hardware and firmware characteristics. They will not change, and each has already been mistaken
for a provisioning problem or a defect once.

| Fact | Consequence |
|---|---|
| **No SD card slot at all** | Any case needing SD media can never produce a verdict on this platform. Mark it `testCaseExcl`; don't chase it, and don't propose fitting a card — there is nowhere to fit one. |
| **No battery-backed RAM / NVS** | Any case depending on it is permanently unsupported. Also: the clock does not survive a power cycle without NTP. |
| **No onboard management ethernet** (`show interface eth0` → `% Can't find interface eth0`) | The `eth0` a `.setup` names for TFTP boot is an **ASIX USB-to-Ethernet dongle** in the switch's USB port, visible **only to the bootloader**. Cabling a front-panel port gives it no download path. |
| **No SSH and no telnet** on these units | They answer on 80/443, but **the console is the only CLI path**. Enabling `ssh server` would itself need CLI access. |
| **Flash is SPIFlash and is extraordinarily slow** | A 41 MB flash-to-flash copy is **~12 minutes**, and during it the unit answers **nothing** — console silent even to a bare CR, ping and ARP failing. This looks exactly like a crash. **Never power-cycle mid-write.** Also: `cmd()` returns on `Copying...` without verifying the file landed. |
| **Cross-member flash copy beats TFTP** | `copy awplus-2/flash:/<f> flash:/<f>` moved 41 MB in **3.5 min** vs ~12 min for TFTP, and needs no IP address. |
| **Opening or closing a serial port drops DTR, and the IE520 reads that as a BREAK** | It can park a unit in the bootloader. Drive these consoles with a tool that does `stty -hupcl` first; leave minicom with `Ctrl-A Q`, never by closing the window. A `sysrq: HELP` banner on open means a BREAK was just sent. |
| **USB dongle and stick share one rear port through a hub** | u4's stick has dropped off the bus unprompted with nobody touching it. If a USB case fails oddly, **suspect the hub before the product.** |
| **Every TFTP-written release is `+352` bytes** vs source | Deterministic across transfers and devices, so it is an AW+ write artefact, not corruption. Images boot. Not a finding. **Flash-to-flash copies are +0 bytes** — the artefact is TFTP-specific. |
| **The CLI is media-blind** | On fibre, `speed`/`duplex`/`polarity` are all still offered and nothing errors, so a speed matrix pointed at fibre records a false *"DUT failed to set speed"*. Media is knowable only from the `Type` column of `show interface <port> status`. |
| **1000BASE-T copper SFPs (AT-SPTX / -SPTXa / -SPTXc) facing a host NIC only link when FORCED** (2026-09-09) | Autoneg on both ends left every such edge `notconnect` while the host (Intel igc) reported `Link detected: yes` — a half-link that reads exactly like a wiring error. The recipe that linked 3 of 3 good ports: switch `speed 1000` + `duplex full` + shut/no-shut, host `ethtool -s ethN autoneg on advertise 0x20`, allow ~20 s. Switch-to-switch copper SFP links never needed this. Mind the TFTP-NIC caveat in §1 before pinning. |
| **A dead SFP cage still reads the module's EEPROM** (2026-09-09) | `show system pluggable` lists the SFP; the port never links. Stack `port1.0.1` and u4 `port1.0.1` each defeated 2 SFPs × 2 cables × 2 NICs that all linked one cage over. Isolate by swapping the cable at the **switch** end — if the fault stays with the port, it is the cage. Route around it to a free cage; don't debug it. |
| **Map host NIC → switch port by shutting the port and watching `/sys/class/net/ethN/carrier`** | Definitive even when the switch reads `notconnect`, and non-destructive. It disproved a cabling assumption twice on 2026-09-09 in under a minute each. |
| **No `show mac address-table count` / `summary` / `interface <port>` on this build** | Every form is `% Invalid input` (the `interface <port>` form too, 2026-09-11). Filter client-side with `\| include <port>` or `\| include <mac>` — ~9,500 matching lines take ~25 s at 115200 and read cleanly. **Non-destructive host-NIC → switch-port mapping (2026-09-11):** `ping -c1 -I ethN <any address in its /27>` on tb470 forces one ARP broadcast out that NIC, then `show mac address-table \| include <that NIC's MAC>` on every switch — the switch that learned it on a *physical* port (not a trunk or `saN`) is the cabled one; the others show the trunk it arrived through. Mapped all three tb470 NICs in under a minute. (Host-side LLDP capture with `tcpdump` needs root and returned nothing unprivileged.) |
| **A 2-member VCStack shows ~HALF the MACs a standalone learns from the same flood** (observed 2026-09-09, cause inferred) | 4,750 vs 9,348 of 9,500 broadcast sources — consistent with the hardware FDB being split across members, not proven. For an FDB-scale claim count on a standalone node, or treat the stack's figure as a per-member view. |
| **Unpaced broadcast floods lose about half to storm-control** | 200 sent → 100 learned. Paced (chunks of 500, ~0.8 ms between frames) the same 9,500 landed 9,497. Pace anything you expect the FDB to hold. |
| **Absence from `ck.db`'s CLI reference means UNKNOWN, not unsupported** | `polarity` is undocumented for `ie520` and both units support it. Verify on the device. |

---

## 3. Driving a device — two drivers, with a MEASURED boundary

**Default to the framework's own console driver, bound from the `.setup`** — and read the
boundary below before a campaign that needs `terminal monitor`. Do not write a *third* driver.
`framework/ATDrivers/AWPConsoleCore.py` and `ATSwitch.py` already handle login, `enable`, the
`--More--` pager, baud and prompt matching, and `Setup.LoadSetup` binds devices straight from the
`.setup` — so what you observe is what a generated test will meet.

| Use | Driver |
|---|---|
| Bench state, media, anything a generated test will also meet; any run with a **quiet** console | **framework driver** (`bench_probe.py`) — flawless in this mode: 24/24 commands at 0.41 s |
| Anything needing **`terminal monitor` ON** — witness logging, wedge reproducers, long campaigns that must capture the device's own log stream; and any ad-hoc driving from tb470 itself | **`console.py`** (§0 — the `2026-09-02-driver-test` copy is the maintained one) — the framework **times out on ~17% of commands** in this mode |

Canonical framework-driver tool: **bench_probe.py** (§0; the copies in
`IE520/stack-tests/bench-probe-*/` are older revisions kept as those campaigns' evidence). The shape
that works:

```python
from framework.Setup import LoadSetup            # PYTHONPATH=/home/st-art, framework symlinked
setup = LoadSetup('/home/st-art/st-art/configs/tb470.setup')
stk   = setup.init_stk('stk_a', powerOn=False)   # a stack binds as ONE device
```

Six traps, each of which cost a run:

1. **`init_swi()` / `init_stk()` do NOT establish the console session.** Call `.cmd()` on a
   console that has timed out to `login:` and every command is typed **as a login attempt** —
   the reply is `Login incorrect` and it reads exactly like a dead device. **Call
   `dev.console.mode('#')` first.**
2. **Credentials are the framework's, not the `.setup`'s.** `tb470.setup` declares
   `username: None, password: None` and that is fine: the default user is `manager` and the
   password list is `['friend', 'P@ssw0rd', 'awplus']`. Do not add credentials to a `.setup` to
   "fix" a login failure — see trap 1 for the real cause.
3. **`powerOn` defaults to `True`, and it switches the PDU outlet on.** Pass `powerOn=False` for
   anything read-only on this shared bench.
4. **`Stack.members` is a `set`** — unordered. "Drive any member" is nondeterministic and can hand
   you the console another process is holding. **Pin the member by tty.**
5. **Baud comes from the `.setup`'s `[baudrates]`**, plumbed `Setup.py:822→858→1262` into
   `Switch(baudRate=...)` (default 115200). A device constructed as bare `Switch(devicePath)`
   *bypasses the `.setup`* and forfeits its baud — that, not a driver limitation, is why a 9600
   console ever needed a hand-rolled tool.
6. **A factory-defaulted AW+ device FORCES a password change at first login.** It accepts
   `manager`/`friend`, then demands `Enter new password:` before granting a prompt. Automation
   that only knows `login:`/`Password:` feeds its next command straight into that dialog (one
   run typed `enable` as the new password). Any procedure starting from factory default needs an
   explicit step for it. `console.py` refuses to guess here and raises instead — copy that.
7. **`LoadSetup` writes `setup.log` into cwd**, so run from a writable directory — and if an
   earlier run was `sudo`, the file is root-owned and the next non-sudo run dies with
   `PermissionError`. Serial access itself needs **no sudo** (the nodes are world-writable).

### Async log chatter DOES break the framework driver — measured 2026-09-02

`console.py` exists on the premise that the framework decides completion by testing whether the
*last* line of drained output ends in `#`, so unsolicited log messages make a healthy session look
hung. **Measured on a formed stack with `terminal monitor` on and genuine external chatter, that
premise HOLDS:**

| Phase | median | max | failures |
|---|---|---|---|
| A — `terminal no monitor` (quiet) | 0.41 s | 0.42 s | **0 of 24** |
| B — `terminal monitor` + external chatter | 0.42 s | **45.18 s** | **4 of 24 — `Infinite Loop Detected`** |

Four commands ran the **full 45 s `maxWait`** and raised. The `kickInterval = 10.0` recovery
(hardcoded, `AWPConsoleCore.py:819` — on 10 s of silence the framework writes `' \n'` to kick a
fresh prompt) fires ~4 times inside that window and **does not rescue it**. Note what the failure
is called: `Infinite Loop Detected` is only the flat wall-clock timeout (§4), never a diagnosis.

⇒ **`console.py`'s prompt-after-echo completion is load-bearing, not an optimisation.** Its
`cmd_fast` returns as soon as a prompt appears *after* the echoed command, which is immune to this.
The failover-300 handover's "please do not simplify these driver behaviours" is correct.

**⚠️ THIS RESULT REVERSED AN EARLIER ONE, AND THE REASON MATTERS MORE THAN THE RESULT.** An
earlier run the same day reported the exact opposite — zero failures, "the framework survives".
That run was **invalid**: the bench had split into two standalone units ~20 min beforehand, so the
load generator on the other console could not log to the unit under test, and the 26 "chatter" log
lines counted were the DUT's own `IMISH[…]: [manager@ttyS0]<cmd>` keystroke echoes. Self-echo
arrives *before* the prompt and the framework copes with it fine; genuine external output arrives
at arbitrary times, including after the prompt, and that is what breaks completion. **A raw log-line
count cannot tell the two apart** — `fw_async_test.py` now counts them separately and reports
`PARTIAL` rather than a pass when the external count is zero. Re-verify on a **formed** stack, and
confirm the generator is actually contributing before believing either verdict.

Regression test: **fw_async_test.py** + **fw_async_chatter.py** (§0). Re-run it after a framework
upgrade; this table is what it defends.

⇒ **`rc.py` / `rc9600.py` / `probe.py` remain superseded** for ordinary reads — use
`bench_probe.py`. But **`console.py` itself is not retired.** Note also `rc.py`'s `login()` can
abort on a healthy device: it returns from the post-password read after 1.2 s of quiet, before the
prompt prints, then sends a redundant `enable` and gives up, reporting `no privileged prompt` —
which reads exactly like dead hardware.

**Read the source and the prior logs before driving anything by hand.** Before sending a
keystroke, read the framework function that already automates it and the prior `swi_a_*.log` for
the same case — they give the exact sends and expects. See
[[read-the-transcripts-before-driving-hardware]]. Three mechanics: **a prompt already on screen will
never re-appear**, so prime with the known answer rather than waiting for text printed before you
connected; **never let two processes touch one port** — that produces `device disconnected or
multiple access on port?`, which reads exactly like a hardware fault while `dmesg` shows zero USB
events (2026-09-09: my driver against Terrence's minicom, then against `bench_probe.py` holding
u4/u5 for 45 min — `fuser` first, always); and **a console left in `configure terminal` answers
every plain `show` with `% Invalid input detected at '^' marker`, caret at column 1** — which reads
like a dead or odd unit (u5 was declared "dead" for an hour on 2026-09-09, until Terrence asked
*"how is u5 dead"*). `login()` does not drain it: send raw `end` / `disable` / `enable` before the
first command, or use `do show …`.

**IE520 Boot Menu keypresses differ from the CLI's.** Menu options and Y/N take a **bare
keypress** (a trailing `\r` answers the NEXT prompt); only file selection takes Enter. But AW+ CLI
`(y/n)` confirmations want `y\r` — a bare `y` left `reload` unanswered, silently. Stop ticking
`Ctrl+B` the moment the menu appears (continuing re-prints the menu forever, so a wait-for-quiet
read loop never settles and the unit is left parked at the bootloader, offline to the whole
shared bench), and always drive `0`/`0`/`9` out in a `finally:` — **unconditionally**, never
contingent on some other recovery path existing. Cancelling with `0` persists nothing: the
bootloader only writes on `Saving settings... Complete`, after a *completed* file selection.
Verify recovery by re-reading `show boot` against the pre-test capture. (Terrence caught a script
parked in this menu on tb470 u5, 2026-08-10.)

---

## 4. Framework traps that have each cost hours

| Trap | What it looks like | Reality |
|---|---|---|
| **Runs must be root** (`launch.sh` does this) | `tb eth port eth1 not found`, `sys.exit(2)` — while eth1 is up the whole time | `ATTestBox.Eth` reads a `0600 root:root` nmconnection file. `ConfigParser.read()` **ignores an unreadable file without raising**, so it finds no `[ipv4]` section but still skips the `ip addr show` fallback that would have worked. Note a read-only *probe* needs no sudo. |
| **The framework OVERWRITES its logs in CWD** | A second run of the same suite silently destroys the first run's evidence | It opens the TestSet log without `-a` and renames `swi_a.log` → `swi_a_<suite>.log` at the end. **Always use a dated run directory per campaign.** |
| **`INFINITE LOOP DETECTED` / `WAITED TOO LONG`** | Sounds like a diagnosis | A flat wall-clock timeout, never a race and never a slow device. **There are two different defaults:** `AWPConsoleCore.DEFAULT_COMMAND_WAIT = 1800` and `ATSwitch.DEFAULT_CMD_TIMEOUT = 3600`. Pass a task-appropriate `maxWait`/`timeOut` instead of inheriting either. |
| **`sys.exit()` inside a library helper** | An abandoned run that exits **0** and looks like a clean pass | `SystemExit` is not an `Exception`, so `ATTestCase`'s handlers cannot catch it. **The framework ships a supported opt-out: `swi.exception_on_exit()` / `no_exception_on_exit()`** (`ATSwitch.py:2797/2805`) — every exit site consults `get_exception_on_exit_state()` and `raise`s instead. Use that for probes and reproducers; inside a TestCase use `self.failed(..., forceAbort=True)`. |
| **`confCheck=False` + the abort path manufactures failures** | One real defect reported as three | `_post_tear_down()` is gated by `doConfCheck` in `__run`, but `__handle_exception_in_test_run()` calls it **unconditionally**. So a case built `confCheck=False` never saved a TestSet config, yet still tries to restore and compare one. |
| **Three framework copies on the bench** | "I read the source" | `framework`, `framework2` and `framework.pre_noswitchport` all exist. `/home/st-art/framework` is **read-only** — never write under it, never point a run at a different one by accident. Keep `*.orig` beside every patched file and record its md5. |
| **`ATPublisher` only fires if `.atpylib_publisher.json` exists in CWD** | Assuming results are recorded | It is absent (`Setup.py` is its only referrer), so **nothing reaches the shared results DB.** Local logs are the only record. |
| **`init_portlink()` returns `(None, None)` SILENTLY** | A missing cable grades as a script defect | Check with `tool/pt_preflight.py` **before** booking bench time. Never invent a `[portlink]`. |
| **A pass predicated on absence-of-evidence** | Green | e.g. `if 'Incorrect password' not in output`, or a check matching a *field label* present regardless of its value. A 20 s timeout returning empty output passes both. Any such assertion needs positive evidence attached — and a probe that finds none must report **inconclusive**, not pass. |
| **Fixing one bug exposes the next** | Per-cause case counts understate the work | A defect downstream of an earlier one stays invisible for a whole campaign, because execution never reaches it. |
| **Framework logs read as BINARY** | `grep -c` returns `0` — indistinguishable from a real absence | Console logs carry control bytes and embedded NULs. Always `grep -a`, or `tr -d '\000'` first. This produced a false "0 occurrences" once. |
| **Python buffers stdout when redirected** | A detached run's `.stdout` stays empty and looks dead | Read the script's own log file for live progress. And **never `pkill -f <script>` over SSH** — the pattern matches the remote `bash -c` carrying it and kills your own session (done again 2026-09-09; `pgrep -f` with the `[b]racket` trick *also* matched its own wrapper — trust `fuser` on the device node, never a process name). |
| **`ATPower.PduPower` raised `OSError(40) Too many levels of symbolic links`** on construct (2026-09-09) | "Framework power control is broken" — again | It isn't, and it is thin: three HTTP POSTs with the lab default creds. `status.xml` → outlet states are `text.split('<pot0>')[1].split(',')[10:35]`, index = outlet−1; `offs.cgi?led=<24 chars, '1' at outlet−1>`; `ons.cgi?led=…`. Doing exactly that with `requests` worked first time (outlet 8 off → `Success!`, verified by the console going silent). Do **not** probe it with a multi-credential `curl` loop — the auto-mode classifier reads that as credential guessing and blocks it; use the one known cred. See [[read-the-whole-function-before-judging]]. |

---

## 5. Timing discipline

**Operations on this platform run LONGER than linear.** Do not size a budget by extrapolating
from an `n/50` progress counter on a run that timed out — that is exactly how too-small budgets
get set, and it produces false failures on operations that were working correctly. Measure end
to end, or budget well past your estimate.

`waitTime` is a **ceiling** — `send()` returns as soon as `strList` matches — so a generous value
costs nothing on a healthy run. There is no reason to be stingy.

---

## 6. The DUT stack — plan accordingly

Re-read `show stack` every session. **Which units form the DUT stack, what the other units are, how
they are cabled, what ring/aggregation (if any) runs, and what is powered off or shut are bench
facts — bench-state.md (§0).** What follows is what a 2-member AW+ VCStack *implies* for any test,
whatever the current cabling.

**Do not bind two members of one stack as DUT + link partner — that measures one device against
itself.** On a formed AW+ VCStack every member's console reaches the *same* master CLI, so
`init_swi()` on either `[switch]` entry reaches one device. They stay in `[switch]` only because
`Setup.py`'s `__checkMember` requires it.

Consequences, all of them live while the units are stacked:

- **Concurrency across the two members is GONE.** Guidance to run two suites simultaneously for a
  two-DUT campaign applied when they were two standalone switches.
- **Power-cycling a member cycles one member of a live stack** — a failover event, not a standalone
  reboot. A test written for a standalone DUT will not measure what it thinks it is.
- **A link partner needs cabling, not an edit.** A generated script finds its cables through the
  framework (`get_all_port_links()`); nothing in `[misc]` declares them (the `ck_profile` contract
  was retired 2026-09-21). A partner must be a separate DEVICE — a link between two members of one
  stack sits inside one L2 device — and a testbox link needs a direct testbox↔DUT cable. Whether
  one exists today is in bench-state.md.
- **The "never cable 27/28" hazard is scoped to two _standalone_ units** both claiming ID 1 under
  one chassis-id; it does **not** apply to a properly formed stack. `no stackport` on 27/28 *does*
  stick across a reboot, needs `write` + reboot, and `switchport resiliencylink` is rejected while a
  port is still a stackport.
- **Quirks of the OTHER bench units** (the AR4050S's passive-LACP bonding that never shows in its
  running-config, SFP loopback plugs that read `connected` with no neighbour) are recorded in
  bench-state.md's prose beside the cabling they affect — read them there before trusting a
  `connected` or a second link to anything.
- **Redundant inter-switch links loop unless something blocks them.** An EPSR ring with *no master*
  (all nodes `transit`) never converges — each transit blocks a port and the data VLAN partitions
  (2026-09-11). Removing a ring: shut the third edge FIRST while EPSR still blocks, then
  `epsr <ring> state disabled` → `no epsr <ring> datavlan <vid>` → `no epsr <ring>` → `no service
  epsr` (reboot to complete). An **asymmetric LAG** (aggregated on one end only) forwards but
  duplicates broadcast/multicast (DUP pings) — reduce to one link or aggregate both ends.

### Failover tests — what the 2026-09-09 T5648/T5649 runs taught (mechanics, durable)

- **Source the traffic on the member that SURVIVES.** Kill the master → the stack-side edge must
  sit on the backup's ports; kill the backup → on the master's. Sourcing on the failing member
  measures that member's port dying and says nothing about continuity — the first T5649 run was
  invalid for exactly this. Because roles swap and never pre-empt, "the surviving member" changes
  every run: `show stack` first.
- **Cut with `reload stack-member <id>`, not the PDU** (under netboot a power-cut member boot-loops
  if it can't reach TFTP, §1; under flash boot a reload is simply faster and cleaner). Priorities
  and `virtual-mac` state are in bench-state.md. Mechanics: **the LOWEST priority value wins an
  election, and only an election** — a running master is never pre-empted, so to make a specific
  member master you set its priority low and reboot (or reload the current master). With
  `virtual-mac` off the bridge MAC changes at failover (§1).
- **Measured 2026-09-11 (T10623, `reload stack-member <master>`, host on the survivor):** traffic
  gap **2.05–2.08 s** with virtual-mac; an OSPF neighbour on a survivor-homed uplink never lost the
  adjacency — a ~5 s `ExStart` dip about 21 s after the failover, `Full` again at +26 s, no
  dead-timer expiry. The failing master must not carry the host port or the uplink you measure.
- **Measured 2026-09-11 (T11427, same trigger, PIM-SM multicast through the stack + 300 OSPF
  routes):** the multicast stream was **loss-free** across the master failover (max inter-arrival
  gap = normal cadence, two runs) and the 300-route FIB stayed intact — because multicast has no
  host-ARP-to-gateway dependency, so with the forwarding path + virtual-mac held on the survivor
  the data plane never drops. Method + host-RX gotchas: [[ie520-mcast-l3-test-method]];
  `IE520/ipv4-routing/11427.log`.
- **Don't measure continuity with a unidirectional unicast flow.** Unicast across the ring was
  direction-dependent (eth2→eth1 died at u5 while broadcast passed both ways) and the working
  direction can flip at failover. Use broadcast/flood traffic or measure both directions; persist
  per-frame timestamps to a file; pace with a raw `AF_PACKET` socket — scapy `sendp` per frame
  managed ~26 pps, and a summary-only harness could not report the cut timing afterwards.
- **A cut member that is OFF or boot-looping is an ABSENT peer, not a split:** survivor
  `Operational Status: Standalone unit`, peer `Role: Provisioned`, both survivor stackports `Down`.
  Read the peer's console for the boot-loop signature before reaching for the split recovery below.
- **CLOSED-BY-REMOVAL (2026-09-11), was OPEN 2026-09-09:** "does EPSR reconverge on the surviving
  member after a master power-cut?" was never cleanly answered — the 09-09 run was confounded by the
  cut member boot-looping, and on 09-11 the ring turned out to have **no master at all** (every node
  `transit`), so it could not have converged. Terrence had the ring removed rather than re-tested.
  Evidence: `IE520/SESSION-HANDOVER-2026-09-09.md`, `IE520/SESSION-HANDOVER-2026-09-11.md`,
  `IE520/ipv4-routing/10623.log` Part 2b. Re-open only if a ring with a master is rebuilt.

### When the stack SPLITS — diagnose it before touching anything

Read `show stack detail` on **BOTH** consoles. A split stack is not a config fault and no amount
of interface config on the healthy unit can fix a dead far end. The signature:

| | Healthy | **Split** |
|---|---|---|
| Operational Status | `Normal operation` | `Standalone unit` on one, `Operating in failover mode` on the other |
| The other member | `Ready` | **`Provisioned`** — each unit sees the other as merely provisioned |
| Role | Master + Backup | **two masters**, one of them `Disabled Master` |
| Front-panel ports | up | **all 26 `err-disable`** on the `Disabled Master` |
| Stack MAC | one VMAC | the demoted unit reverts to **its own** MAC |

Observed exactly this way 2026-09-02 after member 1 rebooted unattended and came back on a
different release. **`port1.0.27`/`1.0.28` both read `connected` throughout** — so *link is not
the test*; do not go hunting for a cable.

**Two causes, and they need opposite fixes:**

1. **Release mismatch** (see §1) — align the software and let it rejoin. Check `show version` on
   both members *first*; this is the likely cause after any unexpected reboot.
2. **Stackports genuinely down / units provisioned into one chassis with 27/28 uncabled** — the
   2026-07-30 case. Recovery that worked: `no stackport` on both 27/28 ranges, `no stack
   virtual-mac`, **`stack 2 renumber 1`** on the demoted unit (`show stack` then shows a
   `Pending ID`), `write`, reboot. Afterwards both read `Operational Status: Standalone unit`
   with their own MAC.

**⛔ NEVER use `no stack <id> enable` to unpick this.** Per the CLI reference it *"will act as a
stand-alone master and **disable all of its ports**… can then only be accessed via its console
port"* — it **creates** the state you are trying to escape. Also: `stack virtual-chassis-id` has
**no `no` form at all** (`no stack ?` offers only `<1-8>`, `all`,
`disabled-master-monitoring`, `management`, `resiliencylink`, `virtual-mac`).

**Rejoining does not re-elect**, so roles will not match what the priorities imply: priority
decides an *election*, and there is no pre-emption when a member rejoins a running stack.
Measured 2026-09-02, after the split healed, member 1 held master at priority 128 while member 2
sat backup at priority 1. **This is normal and does not need correcting** — which unit is master
is not a bench-health signal. What matters after a rejoin is that both members read `Ready` under
`Operational Status: Normal operation`.

---

## 7. Bench hygiene — leave it re-runnable

The measure of a finished run is that the next person can start one. Verify and record final state.

- **Leave the boot source the next reboot will actually use in a good state** — which source that
  is (flash `.rel` named by `show boot`, or `/tftproot/IE520-tb470.rel` on tb470 under netboot) is
  in bench-state.md "Boot" (§1). Under flash boot confirm `show boot` reads `(file exists)`; under
  netboot leave the served file holding the intended build.
- **Watch free flash.** 106.3 MB total per member; two 41 MB `.rel` files leave ~20–26 MB — **not
  enough for another release** (measured 2026-09-02; current figures are a `dir` away). Clear large
  leftovers; a stray 41 MB `.rel` has filled a unit's flash and caused a silent failure. `dir`
  reads the master's flash only (`dir stack-member N` is rejected).
- **A case that destroys state must restore it in a `finally:` inside `main()`, not in
  `tear_down()`** — `tear_down()` does not run when `main()` raises, which once caused a
  five-case cascade.
- **Restore session-scoped settings you changed** (`terminal monitor`, CLI mode). Console mode
  *persists across serial sessions*: the device stays in whatever mode it was left in, so a
  second `configure terminal` returns `% Invalid input detected`. The inverse bites too: a console
  left in config mode makes every plain `show` fail for the next session (§3). `end` before you close.
- **Restore host-NIC settings you changed** — `ethtool` speed/advertise pinnings especially, and
  above all on the NIC that serves TFTP boot (§1): leaving it 1000-only strands the next member that
  reboots. `ethtool -s ethN autoneg on advertise 0x2f`.
- **If you power a member OFF deliberately (e.g. to stop a boot-loop), record it** — in
  bench-state.md "Current state" and in the session handover. A powered-off member reads as a dead
  one to whoever comes next.
- If a run leaves the DUT locked out of its own boot menu, say so explicitly — the framework has
  no bootloader-password handling, so the next run is locked out too.

---

## 8. Load the memories

```bash
ls <memories>/*.md      # the directory IS the list — path in §0 ("memories")
```

Read `MEMORY.md` (the index) and then the files whose hooks match today's work. The memory
directory is symlinked from `~/.claude/projects/<slug>/memory` for both the repo path and the lab
home, so the same set loads from either. **Any memory name written down — including here — is a
hint, not a guarantee.** A memory reflects what was true when written; if it names a file, flag or
unit, confirm it still exists.

Bootloader- and suite-specific history (the 5700 campaign, the two IE520 bootloader builds, the
known output divergences) is deliberately **not** in this file. It lives in the memories and in
each campaign's own after-action. Load it only when the work is that work. The open
resiliency-link defect's evidence is the **resiliency-link evidence** file (§0). **Always read the
latest session handover** (§0, `IE520/SESSION-HANDOVER-<date>.md`, newest date) — it says whether
the bench was left whole or *parked*, what is still shut or unsaved, and what was mid-flight.

---

## 9. Brief the user, then stop

Dense and skimmable, with clickable relative paths.

- **(a) Live bench state** — per DUT: console, S/N, **stack ID** (not role — see §1), boot pointers, what is
  in flash and how much is free, and whether it is usable *now*; for failover work, **which member
  is currently master** and whether the TFTP boot path is up. From §1 lookups, not from this
  file.
- **(b) What today's run needs first**, if anything, with its time cost.
- **(c) Relevant platform limits** (§2) that bear on the work in scope, so an expected
  unsupported result is never read as a failure.
- **(d) Today's task** — only if the user has stated one. Otherwise say "awaiting direction" and
  do **not** invent an agenda.

Then wait. **Deliverables:** for an individual lab test case the per-case `<case-id>.log` **is**
the deliverable — do not write an after-action for every case. For a whole **campaign**, the
convention is `after-action-<suite>.md` in that run's directory, written **from that run's own
logs**: headline counts, a full per-case verdict table with a prior-bench comparison column, each
failure classified *product / tooling / unmeasured*, bench state left behind, and caveats.
