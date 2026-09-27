# Session handover — 2026-09-28 (wrapped ~08:20 NZDT)

## TL;DR

- **The bench is whole and untouched.** No test ran and no DUT config was changed. Final
  `bench_probe.py run` (capture `2026-09-27T191150Z`) read **MATCH** with **all six consoles**
  read, the x230 included for the first time since 09-25.
- **`bench_probe.py` x230 login fixed.** The x230 (9600) failed `login_failed` with correct
  creds (`manager`/`friend`, Terrence confirmed). Byte-logged cause: login waited on quiet, not on
  the prompt (orient-dt §3, new paragraph). Fix: `Probe._expect()`.
- **E-11 done: `bench_probe.py apply`** (Terrence: "execute those things"). The deployed
  `/home/st-art/st-art/configs/tb470.setup` is now the generated 1166-byte fence. The old 22 KB
  commented file is in `bench-setup/backups/2026-09-27T190048Z.tb470.setup`. The framework's
  `LoadSetup` parses the new file.
- **The Test-cases 09-25 handoff is actioned** (see §2); the two 09-25 relocations are done or moot.
- Commits: see the wrap commit — **committed, NOT pushed**.

## 1. Bench state and how to verify it

Topology: [bench-setup/bench-state.md](../bench-setup/bench-state.md) (generated
2026-09-27T191150Z = 08:11 NZDT 09-28; MATCH, Advisories: only the probe's own temporary
`lldp run` on the x230).

```
stack       1/3/4 Ready, member 3 (u5) Active Master, Normal operation, Stack MAC 0000.cd37.0d6f
builds      stack + IE520-sa awplus_main-20260923-20; 4050 awplus_main-20260924-26; x230 awplus_5.5.5_2-20260918-7
boot        every device: Current boot image <platform>-tb470.rel (file exists); boot config flash:/tb470-bench.cfg (file exists)
uptime      stack/sa/4050 ~2 d 20 h (the 09-25 restore); x230 ~6 d (restored by CLI on 09-25, no reboot) — no reboot since
host        eth1/eth2/eth3 carrier 1; /nfsHome mounted; no ethtool/IP changes by this session
consoles    all free at wrap (sudo fuser: none)
```

Verify next time (ON tb470, ~2 min, once `sudo -n fuser -v /dev/u*` is empty):

```bash
cd ~/claude/device-testing/bench-setup && ./bench_probe.py run      # expect MATCH, all six consoles read
```

**Not mine, recorded:** the x230 running-config gained `line con 0` → `exec-timeout 0 0` since
the 09-25 capture — most likely from Terrence's minicom session this morning (x230 "Last login" 18:53 UTC = 07:53 NZDT). Whether it
is saved was not checked. Left alone; Terrence's call.

## 2. What was accomplished

1. **Orient** — probe NEEDS-CHECK on the x230 only; confirmed the unit was up at a clean `login:`.
2. **Test-cases handoff** (`bench-setup/handoff-from-test-cases-2026-09-25/`, README now carries
   an "Actioned" note):
   - `restore_cfg.py` → `bench-setup/restore_cfg.py`, byte-identical (md5 `4dbc0525…`); its
     `/tmp/ck33235` paths and tag→tty map are still hard-coded. `lic_install.py` stays in the
     handoff folder as reference.
   - `TESTBOX-ACCESS.md` (already this repo's file; Test-cases symlinks to it): §3 launch line
     carries `--noupdate --nodefaultcfg`, the generated-script binding text updated, new §3b "What
     the framework's default setup does to a bench".
   - bench-runner gate 7: the server path is **permitted** (flags verified at
     `Test-cases/ask-ck/CK-main/CK_server/pt_exec.py:506`), with a re-check instruction; gate 6's
     template example corrected to `<setup>.<device>.cfg` (checked against the templates dir).
3. **09-25 relocations:** TFTP-write timing (206–268 s, +0 bytes, 2026-09-23) is now a dated
   counter-observation on orient-dt §2's SPIFlash row, cross-referenced from the `+352` row. The
   4050 boot-pointer "leave it" note is **moot** — `show boot` now names
   `AR4050S-tb470.rel (file exists)` (Terrence re-pointed it 09-25) — so it was not recorded.
4. **orient-dt §0** paths fixed (TESTBOX-ACCESS.md, TB470-HOST-NETWORKING.md live at this repo's
   root; fw_async scripts are under `ask-ck/functions/test-composer/`). Snapshot
   `SKILL.md.pre-20260928` (= the committed version before today's edits).
5. **bench_probe.py login fix + apply** (TL;DR).

## 3. Findings

Measured (byte log of `Probe.login()` against u0, 2026-09-28):
- The two CRs sent at 115200 during baud detection arrive at the 9600 x230 as a garbage
  username → `Password:`.
- A bare CR at `x230-10GP login:` is taken as an empty username → `Password:`.
- `Login incorrect` arrives ~2.2 s after the rejected (empty) password — past the probe's quiet
  window, so every later send answered the wrong prompt.
- After the fix: `manager`/`friend` → `x230-10GP>` (with `% Default password needs to be
  changed.`) → `enable` → `#`.

Inferred: 09-25's successful x230 reads were timing luck under the same bug.

## 4. OPEN

- **x230 `exec-timeout 0 0`** — keep/save or remove? (Terrence.)
- **PDU 10.36.150.14** — Terrence was plugging it back in this session; not re-checked. Until it
  answers, any `powerlink` step hits the framework's silent-False path.
- **The x230's ACCESS licence retry** (from 09-25) — status not checked this session.
- **restore_cfg.py** still needs generalising (paths, tty map, file name) before Test Composer's
  "load `<setup>.<device>.cfg` onto `<device>`" can use it.

## 5. Next steps, in order

1. `bench_probe.py run` → MATCH.
2. T33235, then T33234, through the bench-runner agent (its gate list is current).
3. After Terrence's recable (an eth port to member 1), rerun the corosync DLF run 3
   (09-25 handover §7 recipe).

## 6. Recipes

Byte-log a console login with the probe's own code (scratch on tb470 tmpfs; recreate as needed —
it imports `bench_probe` from the repo and wraps `Probe.s` in a tap that logs every TX/RX with a
timestamp, then calls `detect_baud()`, `capture_banner()`, `login()`):

```python
import sys, time
sys.path.insert(0, "/home/terrenceb/claude/device-testing/bench-setup")
import bench_probe as bp
t0, log = time.time(), []
class Tap:
    def __init__(self, s): self.s = s
    def write(self, b): log.append("%6.2f TX %r" % (time.time()-t0, b)); return self.s.write(b)
    def read(self, n):
        b = self.s.read(n)
        if b: log.append("%6.2f RX %r" % (time.time()-t0, b))
        return b
    def __getattr__(self, a): return getattr(self.s, a)
orig = bp.Probe._open
def _open(self, baud): orig(self, baud); self.s = Tap(self.s)
bp.Probe._open = _open
p = bp.Probe("/dev/u0")
try:
    baud, init = p.detect_baud(); p.capture_banner(init); log.append("LOGIN %r" % (p.login(),))
finally:
    p.close(); print("\n".join(log))
```
Run it from `/tmp/ckorient/` on tb470 with the console free. It logs in and leaves the session at
`#`; send `exit` afterwards so the next reader starts from `login:`.

## 7. Pointers

- Memory updated: `.claude/memory/bench-probe-one-tool.md` (apply done; login_failed = driver
  suspect first).
- orient-dt §3: "A login dialog must wait on the PROMPT" paragraph.
