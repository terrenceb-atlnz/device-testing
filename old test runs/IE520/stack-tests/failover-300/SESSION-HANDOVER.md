# Session handover — tb470 IE520 stack bench

**Written:** 2026-08-26, end of the afternoon session.
**Next session:** Terrence, remote over VS Code SSH.
**Run directory:** `~/old test runs/IE520/stack-tests/failover-300/` on **tb470**
(the same path is `/media/terrenceb/mnt/testbox_home/old test runs/...` over NFS from the dev host).

---

## 0. The one thing that will bite you first

`/dev/u4` and `/dev/u5` **do not exist on the dev host** — they are on tb470. Everything here runs
over SSH, and a non-interactive shell needs the auth socket set explicitly:

```bash
export SSH_AUTH_SOCK=/run/user/1971/keyring/ssh
ssh tb470
```

Two more that cost time today:

* **`pkill -f witness_log.py` kills your own SSH session** — the pattern matches the remote command
  line carrying it. Use `ps -eo pid,args --no-headers | grep -E 'python3 \./(witness_log|repro_38378)'`
  and kill explicit PIDs. Same trap the orient doc records for `pgrep`.
* **Opening or closing a serial port drops DTR, and the IE520 reads that as a BREAK.** `console.py`
  works around it (`stty -hupcl`, then a bare CR to absorb the open). **minicom does not**, unless you
  leave it with **Ctrl-A then Q**. A unit that was healthy at 14:15 was found parked in the bootloader
  at 14:51, across the window minicom sessions were closed. Do not open either console while a unit
  is booting.

---

## 1. Bench state as left

Stack is **healthy, `Normal operation`, both members `Ready`, all four stackports `Learnt neighbor`.**

| | ID 1 | ID 2 |
|---|---|---|
| Serial | **264A23061** (NEW unit, fitted 2026-08-26) | 264A23052 |
| Console | `/dev/u5` | `/dev/u4` |
| PDU (10.36.150.14) | outlet 5 ("E") | outlet 4 ("D") |
| Role | **Backup Member** | **Active Master** |
| Priority | 128 | **1** (lowest wins election) |
| Boots from | flash | flash |

* Boot image (stack-wide): `flash:/IE520-20260825.rel`, 41,103,575 bytes — byte-exact with
  `/tftproot/IE520-tb470.rel`.
* Both members run **`AlliedWare Plus (TM) 0.0.0 08/19/26 02:20:43`**, build
  `IE520-tomahawk_ie520-continuous.rel`. Verified on each member separately, not inferred.
* `stack virtual-chassis-id 3439` + `stack virtual-mac` → Stack MAC `0000.cd37.0d6f`, the same
  virtual MAC the pre-swap stack used.
* Clock: **UTC**, set to within ~1 s of tb470 (it was ~68 s adrift before, and the new unit arrived
  a month fast at Sep 25). It survived a warm reboot. Timezone left at the device default UTC
  deliberately, so new logs stay directly comparable with the whole existing evidence corpus.
* Stackport pairing (unchanged across the swap): **`port1.0.27 ↔ port2.0.28`** and
  **`port1.0.28 ↔ port2.0.27`**.

### Cosmetic oddity — do not chase it
`show boot` reads `Current software : IE520-tb470.rel` while `Current boot image` is
`flash:/IE520-20260825.rel`. Those are two different files in member 2's flash (Aug 18 vs Aug 25).
`show version` on **both** members returns the same build string, so this field is stale labelling,
not a version mismatch.

---

## 2. What changed today, and why

The unit that wedged twice — **264A23066** — was **physically removed** and replaced with
**264A23061**. That ended the software investigation into whether the wedge was unit-specific: the
suspect hardware is out of the bench.

When the new unit joined it came up as master and VCStack pushed **its factory config across the
stack**, discarding the old stack's VLAN/IP setup. The old config was recovered from
`awplus-2/flash:/stack.cfg` and is reproduced in §4 — **it has not been reapplied.**

Corrections worth carrying forward:

* A **virtual-chassis-id mismatch does NOT block stack formation.** It was predicted to, and the
  stack formed anyway across mismatched IDs (3803 vs 3439). The chassis-id governs the virtual MAC
  only.
* **Cross-member flash copy works and is far faster than TFTP** — `copy awplus-2/flash:/<file>
  flash:/<file>` moved 41 MB in **3.5 minutes**, against ~12 minutes for the TFTP route, and needs
  no IP address at all. Delta was **+0 bytes**, so the recorded "+352 bytes" artefact is specific to
  TFTP writes, not to flash writes.
* **Console mode persists across serial sessions.** `rc.py` opens and closes the port per
  invocation, but the device stays in whatever CLI mode it was left in — a second
  `configure terminal` returns `% Invalid input detected`. Check where you are before assuming.

---

## 3. Open items

1. **38376 and 38377 have not been run** — reboot the master 300×, and reboot a backup member 300×.
   These were deferred to the weekend. Both are dominated by reboot time; flash boot is now in place,
   and a boot measured **~3 minutes** today versus considerably longer on netboot, so the earlier
   15–25 h estimates should be re-derived rather than reused.
2. **No IP connectivity on the stack.** Nothing reaches the TFTP server. Not needed for the stack
   tests, but it does mean **NTP cannot run**, so the clock is manual-only. Given the IE520 has no
   battery-backed RAM, expect to reset it after any power cycle.
3. **Restoring the old config would recreate a known L2 loop.** `stack.cfg` has `po1` and `po2` both
   reaching the 4050 (directly, and via the x230). Measured previously at **86.7 % loss / 2.6 s RTT**;
   shutting `po1` took it to **0 % loss**. If you reapply §4, shut `po1` in the same change.
4. **The cycle-293 consolidated evidence window assumes an exact +12 h offset** between device UTC and
   tb470 NZST. Real skew at the time was ~68 s on top of that. The window is still usable; the
   sub-minute alignment is not exact.

---

## 4. Recovered pre-swap config (NOT applied — see open item 3)

```
vlan database
 vlan 393 name fdb-test-38393
 vlan 393 state enable
!
interface port1.0.1
 switchport mode access
 switchport access vlan 393
 channel-group 1 mode active
interface port1.0.9
 switchport access vlan 393
 channel-group 2 mode active
interface port2.0.1
 switchport access vlan 393
 channel-group 2 mode active
interface port2.0.9
 switchport access vlan 393
 channel-group 1 mode active
!
interface po1-2
 switchport mode access
 switchport access vlan 393
!
interface vlan1
 ip address 10.38.215.20/27
interface vlan393
 ip address 10.38.215.34/27
 ip address 10.38.215.66/27 secondary
!
line con 0
 exec-timeout 0 0
```

TFTP server is **10.38.215.65**, reached via the `10.38.215.66/27` secondary. Only `10.38.215.0/24`
has an upstream return path and tb470 has **no NAT**.

---

## 5. Tooling in this directory

| Script | Purpose |
|---|---|
| `console.py` | AW+ console driver. Tolerates async log output; completes on **prompt-after-echo**, never on silence. |
| `rc.py` | `rc.py /dev/uN "cmd" ...` — quick commands, monitor off. **120 s cap per command**, so not for slow operations. |
| `flash_copy.py` | Copy into flash from any source path incl. `awplus-2/flash:/...`. Verifies the landed byte count. 30 min ceiling. |
| `tftp_copy.py` | The TFTP variant of the same. |
| `reboot_unit.py` | Reboot + `y`+CR confirmation + boot capture. |
| `witness_log.py` | Read-only **timestamped** peer-console logger. Logs in once, enables `terminal monitor`, then never writes again. |
| `repro_38378.py` | The tight reproducer — see §6. |
| `test_38378.py` | The full 300-cycle test 38378. |
| `build_window.sh` | Builds the annotated cycle-293 evidence window. |

Two driver behaviours that are load-bearing, please do not "simplify" them:

* `read_until_quiet` has **no silence escape hatch**. An IE520 writing 41 MB to SPIFlash answers
  nothing for ~12 minutes; an earlier version returned after 20 s and reported a healthy transfer as
  a failure. *Silence is not an outcome — only the prompt or the timeout is.*
* `PROMPT_ANYWHERE_RE` is anchored at line start and requires **nothing** after the `#`. With
  `terminal monitor` on, the device splices a log line straight onto the prompt
  (`awplus(config-if)#00:55:19 awplus NSM[742]: ...`). Requiring newline-or-end after `#` made every
  such command run to its full timeout — that bug alone consumed **~8.3 hours** of the original
  17.8-hour 38378 run.

---

## 6. Log layout

| Path | Contents |
|---|---|
| `archive-preswap-control/` | The pre-swap control run: 2000 iterations hammering member 2, **clean**. |
| `*.wedge-run` | The run where **264A23066 wedged at iteration 1550/2000**. |
| `evidence-cycle293/` | Cycle-293 forensics, 18 files. |
| `evidence-repro-iter1550/` | Wedge window, witness log, verdicts. |
| `postswap-runA-*/` | Post-swap Run A — see §7. |
| `postswap-runB-*/` | Post-swap Run B — see §7. |

`repro_38378.py` **appends** to `repro-38378.log` and `repro-38378-console.log` and **overwrites**
`repro-progress.txt`. Move them aside between runs or the campaigns merge.

---

## 7. Post-swap runs

Both are 2000 iterations of the redundant `shutdown`, driven from the master (`/dev/u4`), with a
timestamped read-only witness on the peer console (`/dev/u5`). Carrier pair
`port1.0.28,port2.0.27` stays up throughout; the run stops immediately if it degrades, because
shutting a pair while the survivor is down would split the stack.

```bash
# Run A — hammers member 1 (the NEW unit), the position 264A23066 wedged in
./witness_log.py /dev/u5 witness-runA-member1.log &
./repro_38378.py --master /dev/u4 --carrier port1.0.28,port2.0.27 \
    --shut-first port2.0.28 --target port1.0.27 --iterations 2000 --check-every 50

# Run B — hammers member 2
./witness_log.py /dev/u5 witness-runB-member2.log &
./repro_38378.py --master /dev/u4 --carrier port1.0.28,port2.0.27 \
    --shut-first port1.0.27 --target port2.0.28 --iterations 2000 --check-every 50
```

**Results: see §8 — filled in at the end of the session.**

### Reading the output
* `state=DEGRADED` is **expected and correct** — one pair is deliberately down. The failure signals
  are `carrier_ok=False` or a wedge.
* A wedge is detected by **no prompt returning** after `shutdown`. On a wedge the script deliberately
  **stops sending and just listens for 300 s**, and it **skips the restore** — so a wedge always needs
  a manual stackport restore afterwards.
* Rate is ~0.63 s/iter, so 2000 iterations ≈ **21 minutes**.

### Statistical caveat — this matters for how you report it
A clean 2000-iteration run is **not** strong evidence on its own. 264A23066 wedged once in 1550
hammer events, so if a unit were equally susceptible the chance of a clean 2000 is
`exp(-2000/1550)` ≈ **27 %**. Reaching 95 % confidence against that rate needs roughly **4650**
iterations (~49 min); 99 % needs about **7500** (~79 min). The higher rate seen in the 300-cycle run
(1 in 293) would make a clean 2000 far more meaningful (~0.1 %), but the two loops are not the same
shape and there is no basis for picking between them. Say "suggestive", not "proven".

---

## 8. Post-swap run results

Both runs completed **2026-08-26**, back to back, on the rebuilt stack.

| | Run A | Run B |
|---|---|---|
| Hammered port | `port1.0.27` | `port2.0.28` |
| Unit under stress | **ID 1 — 264A23061 (NEW)** | **ID 2 — 264A23052** |
| Position | Backup Member, target-owner — **the exact position 264A23066 wedged in** | Active Master, its own port |
| Iterations | **2000 / 2000** | **2000 / 2000** |
| Wall clock | 1245 s | 1247 s |
| Rate | 0.61 s/iter | 0.62 s/iter |
| Carrier pair | `carrier_ok=True` at every 50-iteration check | same |
| Wedge | **none** | **none** |
| Final state | `FULL`, all four ports `Learnt neighbor` | same |

Evidence from both sides of each run, scanned for
`reset|crash|core|panic|exception|watchdog|FAT|mount|Standalone|Disabled Master|failover`:

| Capture | Size | Anomaly matches |
|---|---|---|
| Run A master console (`terminal monitor` on) | 657 KB | **0** |
| Run A witness, peer console, timestamped | 202 KB | **0** |
| Run B master console | 659 KB | **0** |
| Run B witness | 203 KB | **0** |

The only stack-layer log lines in either witness were 9 routine
`VCS[667]: STK TRACE: Ignoring TIPC BC message 8` traces. **No TIPC probe timeouts** — which is the
signature that preceded the failover in the cycle-293 event — and no silence gaps.

### What this does and does not establish

**Establishes:** the rebuilt stack survives 4000 redundant-`shutdown` events across both members with
no wedge, no crash artefact and no stack disturbance. The bench is sound for the weekend campaign.

**Does not establish:** that 264A23066 was faulty. Read §7's caveat before writing this up. Three
clean 2000-iteration runs now exist (one pre-swap on 264A23052, two post-swap), against a single
wedge at 1550/2000 on 264A23066. That pattern points at the removed unit, but each clean 2000 only
carries ~73 % confidence against the observed rate, and **the suspect unit was never re-tested before
it was pulled** — so the unit-specific conclusion rests on the absence of a repeat, not on a positive
control. If a defect report is going to be filed or withdrawn on this, 264A23066 needs bench time of
its own.

### Final bench state at handover
`Normal operation` · ID 1 Backup Member / ID 2 Active Master · both `Ready` · all four stackports
`Learnt neighbor` · Stack MAC `0000.cd37.0d6f` · clock within ~2 s of tb470 · both consoles free ·
no processes left running.
