# Handoff from the Test-cases session, 2026-09-25 (afternoon)

> **Actioned 2026-09-28 (device-testing session, Terrence: "execute those things").**
> §1: `restore_cfg.py` moved unchanged to `bench-setup/restore_cfg.py` (md5 still
> `4dbc0525…`); its `/tmp/ck33235` paths and tag→tty map are still hard-coded. `lic_install.py`
> stays here as reference. §3: both edits applied to `TESTBOX-ACCESS.md` (§3 flags + new §3b).
> §4: bench-runner gate item 7 now permits the server run path (flags verified at
> `pt_exec.py:506`); gate item 6 uses the `<setup>.<device>.cfg` naming. This file is kept as
> the dated record; §2's bench state is historical — bench-state.md is current.

Written by the Ask-CK (Test-cases) session `test-cases-2d` into this repo **at Terrence's explicit
request** ("save whatever handoff you have for device-testing IN that repo"). The
`device-testing-00` session had exited before these could be sent as messages. **Nothing here is
committed**: review it, move it to where it belongs under this repo's conventions, and commit it.
No licence key is in any file here; all four files were scanned for fragments of the three keys
before writing.

## 1. `restore_cfg.py` → `bench-setup/restore_cfg.py` (Terrence: yes)

`restore_cfg.py` in this folder is byte-identical to the copy that ran on tb470 today,
`/tmp/ck33235/restore_cfg.py` (md5 `4dbc052552cc94a1105977800ff69620`). That copy is on tmpfs. It
imports `console.py` from `/tmp/ck33235`. That file is byte-identical
(md5 `af8505812378a4001df3d324574301c9`) to this repo's
`IE520/stack-tests/2026-09-02-driver-test/console.py`.

**What it does.** It restored all four devices to 0 diff lines against the 2026-09-24 16:58 copy.

- `<tag> --check` is read-only: `show stack`, `show boot`, `show license brief`.
- `stack` / `sa` / `4050`:
  1. `start-shell` (`start-shell <id>` for each stack member).
  2. Build the file in `/tmp` one `echo '<line>' >> <tmp>` at a time, the framework's own
     `write_config_file` method, and check the md5 against the reference text (3 attempts).
  3. `sudo cp` it to `/flash/tb470-bench.cfg` and check the md5 again.
  4. `boot config-file flash:/tb470-bench.cfg`, reboot, and diff the running config against the
     reference.

  On the stack, setting the boot config on the master printed "Synchronizing file across the
  stack … [DONE]", so the per-member write is belt and braces.
- `x230`: CLI only. `copy running-config flash:/tb470-bench.cfg` + `boot config-file`, then
  `show file` diffed. It worked only because the x230's running config already matched. It ran
  before the x230 had `ACCESS`.

**Limits to adapt:**
1. `/tmp/ck33235` paths are hard-coded.
2. References come from `restore/<stk|sa|ar|x230>.running.txt`.
3. The tag → tty map is hard-coded: stack=u5, sa=u3, 4050=u1, x230=u0.
4. `FILE = 'tb470-bench.cfg'` is a constant.

Test Composer will want "load `templates/<setup>/<setup>.<device>.cfg` onto `<device>`" instead.

`lic_install.py` (reference only; bench-runner does not touch licences) is the tool that
installed the licences below. It reads the key from `/home/st-art/feature_license_keys.env` and
never prints it. The key is redacted wrap-tolerantly (`\s*` between every character, plus every
12-character slice scrubbed) in the report, in exception text and in the transcript. It answers
the `license` command's "(y/n)" with `y`, logs out and back in, and for `ACCESS` proves that
`start-shell` works.

## 2. Bench state as left, 2026-09-25 ~13:00

- **Boot config.** Every device boots `flash:/tb470-bench.cfg`: stack members 1, 3 and 4, the
  IE520-sa, the 4050 and the x230. Every running config is at 0 diff lines against 16:58,
  re-checked after the licence installs. The 10:55 `bench_probe.py run` read MATCH.
- **4050 software.** Terrence put a new `AR4050S-tb470.rel` in the 4050's flash and made it the
  boot image, in the bootloader and in config.
- **Licences, from the framework's key file:**
  - x230: `ACCESS` (uppercase, the framework's keep-list spelling). `start-shell` works again.
  - IE520-sa, 4050, and all three stack members: `FULL`. One install on the master reported
    "3 licenses installed".
  - Terrence: **`NZ` is `FULL` under another title**, so no licence is missing.
  - Still installed from the framework's 07:50 run: `ACCESS` + `AT-IE520-FL01` on the IE520s,
    and `ACCESS`, `LICD-Dev`, `No-License-Lock`, `AMF-APP-PROXY` and `AT-FL-AR4-AM20` on the 4050.
    Terrence has not asked for these to be removed.
- **Key leak.** The x230's `ACCESS` key leaked into the Test-cases session output on the first
  attempt: the console wrapped the echoed command past a plain `str.replace`. The tb470 files are
  scrubbed. The Test-cases memory `console-secret-redaction-wraps` records the fix.
- **`tracelog_control`** never existed on any device. The framework's `mv` of it answered "No such
  file".
- **PDU 10.36.150.14:** unplugged since yesterday's network upgrade. Terrence plugs it in next
  session.

## 3. Proposed edits to `TESTBOX-ACCESS.md` §3 and a new §3b

The Test-cases session drafted these and the edit tool refused them, correctly, because
`TESTBOX-ACCESS.md` is this repo's file. The draft text is below, as the Test-cases session
wrote it, including Test-cases-relative paths (`ask-ck/…`, `pt_exec`). Adapt the wording to this
repo's voice. Apply each edit as OLD → NEW.

````text
PROPOSED EDITS to device-testing/TESTBOX-ACCESS.md (drafted by test-cases session 2026-09-25;
refused because the file is device-testing's). Apply as old -> new.

===== edit 1 : OLD =====
SSH_AUTH_SOCK=$sock ssh "$BOX" "
  cd $WORK && ln -sfn /home/st-art/framework framework &&
  sudo -n PYTHONPATH=/home/st-art python3 ./<script>.py -s <topology>.setup -v
"
```

- The `-s <…>.setup` argument names the topology file (`SETUP-FILE-REFERENCE.md`); the
  script never hardcodes a port. A generated script (since 2026-09-21) binds the `swi_a` slot and
  discovers its cables through `get_all_port_links()`, reading media from the DUT; legacy scripts
  bind with `init_portlink(...)`, which returns `(None, None)` silently for an undeclared link.
===== edit 1 : NEW =====
SSH_AUTH_SOCK=$sock ssh "$BOX" "
  cd $WORK && ln -sfn /home/st-art/framework framework &&
  sudo -n PYTHONPATH=/home/st-art python3 ./<script>.py -s <topology>.setup -v --noupdate --nodefaultcfg
"
```

- **`--noupdate --nodefaultcfg` are not optional** (Terrence, 2026-09-25) — §3b says what the
  framework does to every bound device without them. `pt_exec.FRAMEWORK_RUN_FLAGS` carries them
  for the server path. On tb470, runs go through device-testing's **`bench-runner`** agent
  (`.claude/agents/bench-runner.agent.md`), which gates the bench before and after.
- The `-s <…>.setup` argument names the topology file (`SETUP-FILE-REFERENCE.md`); the
  script never hardcodes a port. A generated script (since 2026-09-25) initialises every device
  the `.setup` declares with `setup.init_all_devices(powerOn=False)`, takes `swi_a` from that
  table, and discovers its cables through `get_all_port_links()` — which returns only
  INITIALISED links, so binding `swi_a` alone discovered nothing — reading media from the DUT.
  Legacy scripts bind with `init_portlink(...)`, which returns `(None, None)` silently for an
  undeclared link.

===== edit 2 : OLD =====
---

## 4. Running a LEGACY corpus script on hardware ✅
===== edit 2 : NEW =====
### 3b. What the framework's default setup does to a bench — and why every run skips it ✅

Verified 2026-09-25 on tb470 by the first framework run of a generated script (T33235), which
reset all four bench devices, and by reading `/home/st-art/framework` (read-only).

**Without `--nodefaultcfg`, ATTestSet's setup resets every device the script initialises**
(`__pre_configure` → `_DefaultConfigThread`), in this order:
1. builds a `default.cfg` in Python (`ATSwitch.generate_default_config`: hostname
   `<dev>_<suite>_<set>`, every port `shutdown`, stacking lines) and echoes it into flash through
   **`start-shell`** — there is no template file on disk to replace;
2. `no boot conf` / `boot conf default.cfg`;
3. loads and unloads licences — **only when the script's `FEATURES` is non-empty** (framework
   default `[]`; the Ask-CK frame uses `['ALL']`, the corpus idiom 291/306). It removes every
   licence not in `/home/st-art/feature_license_keys.env` for that platform except the keep-list
   `ACCESS, VCSPLUS, AT-FL-CF9-VCSPL, No-License-Lock`, compared **case-sensitively** — the x230's
   lowercase `access` was removed that way, which took its `start-shell` with it; `NZ` and `FULL`
   were stripped from the IE520s, `FULL` from the 4050. Nothing ever re-adds a removed licence;
4. reboots each device into `default.cfg`;
5. **without `--noupdate`**: TFTP-copies `<platform>-<hostname>.rel` into flash and sets it as the
   boot image. tb470's `/tftproot` is a **tmpfs** (emptied by every tb470 reboot), so the copy
   failed ("% Source file not found"), the failure path deleted crash files from the stack's flash
   to "free space", and the run hung until killed.

`--nodefaultcfg` skips 1–5 and the power cycle; the framework still runs `configure()`, saves the
running config as `<hostname>.cfg` through the CLI (`copy run` + `boot conf`, no shell needed) and
tears down to it. `-n/--noconf` would also skip `configure()` and tear-down — not what a run wants.

**What the bench expects instead:** each device boots its topology's own config —
`flash:/tb470-bench.cfg` for the standing tb470 bench (all four devices since 2026-09-25), and
`ask-ck/functions/test-composer/templates/<setup>/<setup>.<device>.cfg` for a composed topology
(one per device, one shared by a whole stack). A config file is written onto a device the
framework's way — `start-shell`, one `echo '<line>' >> <tmp>` per line, md5 against the source,
`sudo cp` into `/flash/`, `boot config-file`, reboot, diff the running config — which needs the
`ACCESS` (or `FULL`) feature; without it only CLI `copy running-config` works.

**Other traps the same day:**
- **A killed run leaves a console in a root shell** (`[root@… ~]#`). The next run's `show`
  commands then answer `ash: show: not found` and discovery reads every link as `absent`. Send a
  bare CR to every console before a run and `exit` any shell.
- **Two tools on one console fail** with `SerialException: device reports readiness to read but
  returned no data`. `fuser -v /dev/u*` first — another session's `bench_probe.py run` held the
  stack consoles once that afternoon.
- **A licence key sent down a console comes back in the echo, wrapped mid-token** — redact
  wrap-tolerantly (memory `console-secret-redaction-wraps`); `license <name> <key>` then asks
  "(y/n)" and wants `y` + Enter. One install on the stack master installs on every member.

---

## 4. Running a LEGACY corpus script on hardware ✅
````

## 4. What changed on the Test-cases side (all on its `main`, merged)

| Commit | What it did |
|---|---|
| `1cb72db` | The frame initialises every device the `.setup` declares: `setup.init_all_devices(powerOn=False)`, then `tb = _devs['tb']`, `dut = _devs['swi_a']`, `dut_stack = dut.get_stack()`. |
| `db1e02f` | `pt_preflight` reads that table. Until this, it found NO devices in new-frame scripts, so bench-runner's gate item 5 was vacuous. |
| `57d2021` | The server run path (`run/{key}` → `pt_exec.run_command`) launches with `--noupdate --nodefaultcfg`. **bench-runner's gate item 7 ("never launch via run/{key}") can be relaxed.** |
| `088745e` | `genpop` → `test-composer`, and the `bench-runner` symlink in `Test-cases/.claude/agents/`. |
| `69bdd83` | Template naming: `templates/<setup>/<setup>.setup` plus one `<setup>.<device>.cfg` per device in the `.setup`, one per stack (`a.swi_b.cfg`, `a.stk_a.cfg`). |

**Next for the bench:** T33235, then T33234, through bench-runner. T33235 has not run a
TestCase yet.
