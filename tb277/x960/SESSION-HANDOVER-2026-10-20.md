# tb277 / x960 — session handover, 2026-10-20

## Session facts
Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None beyond standing orders (full authority within tests; power cycles allowed).
             Unattended overnight.

## TL;DR

The 14-case x960 Management campaign is **complete and wrapped**. 12 PASS, 1 FAIL, 1 NOT TESTED.
All 13 final logs and their `.cfg` files are created and committed; every `work/` folder is gone.

**The bench is whole, and the DUT is byte-equivalent to how the campaign found it.** Nothing was
left configured, nothing was written to startup-config, and the DUT did not reboot (uptime
3 days 21:57 at wrap).

**One partner is unreachable by the probe: swi_a (u5).** It needs a password the probe does not
have. swi_b (u3) is fine — an earlier claim in this file that it refused its login was wrong, and
the cause is recorded under "The 9600 console trap" below.

## Current bench state and how to verify it

```bash
cd ~/claude/device-testing
tools/tb precheck tb277 u2,u3,u5
tools/tb probe tb277 --consoles u2,u3,u5 --no-prompt --pdu 10.36.230.212 --outlet u2=1,u3=7
tools/tb peek tb277 cksnmpmon u2 115200      # expect: awplus#
tools/tb peek tb277 cksnmpmon u3 9600        # expect: x960-28YSQ login:
tools/tb peek tb277 cksnmpmon u5 9600        # expect: awplus login:
```

Note `tools/tb probe` appends `run` itself — do not pass `run`. And tb277's `python3` is 3.6, so
`bench_probe.py` fails with `TypeError: __init__() got an unexpected keyword argument
'capture_output'` if you ssh and run it directly. `tools/tb` already maps tb277 to `python3.8`;
use the wrapper.

### Per unit, as left

| unit | console | power | state |
| --- | --- | --- | --- |
| swi_d (DUT, AT-x960-56YSQ, S/N A2WQS700B) | u2 @115200 | on | standalone, Ready, Active Master. Boot image `flash:/x960-tb277.rel` **(file exists)**, boot config `flash:/default.cfg` **(file exists)**. Software `sin_x96056-20261012-24`, build Mon Oct 12 06:38:00 UTC 2026. Console **left logged in at `awplus#`** |
| swi_b (AT-x960-28YSQ, S/N A10737A261700021) | u3 @9600 | on | **fine.** standalone, Active Master, `sin_x96056-20260921-9`, bootloader 8.24.0, boot `flash:/backup.rel`. Left logged in at `x960-28YSQ#` |
| swi_a (AT-x950 GEN2-52XSTQm) | u5 @9600 | on | **up and reachable by hand** (confirmed 2026-10-21). S/N `A10713A262600012`, software `awplus_main-20261019-73`, build Mon Oct 19 00:54:59 UTC 2026. 🔴 **`Current boot image : Not set`**; boot config `flash:/default.cfg (file exists)`. `bench_probe.py` still cannot log in — see OPEN 1 |

Host NICs: eth2 `10.38.22.1/27`, eth3 `10.38.22.33/27`, eth4 `10.38.22.65/27` — **all three
carrier=1**. The bench flash-boots, so there is no TFTP path to worry about.

🔴 **`/tmp` on tb277 is 95 % full (1.9 G of 2.0 G, 100 M free).** 1.8 G of that is
`wireshark_eth4*.pcapng` **belonging to someone else — not ours to delete.** Bound every capture.

## What was accomplished

The 14-case Management campaign, run unattended by `bench-runner` subagents in four groups under
a sentinel. Queue: `CAMPAIGN-QUEUE-2026-10-20T0825.md`.

## Results — all runs CLEAN, none confounded

Final logs **created** for every attempted case (`/create-logs`, commits `b164ceb`, `e0a2705`,
`a2b9ed1`, `768d122`). No `work/` folder remains.

| group | cases | verdicts |
| --- | --- | --- |
| [aaa-2026-10-20T0825](aaa-2026-10-20T0825/README.md) | T33407, T33408, T33409 | 3 PASS |
| [snmpmon-2026-10-20T0825](snmpmon-2026-10-20T0825/README.md) | T44308, T33413, T44301, T44309 | 4 PASS |
| [mgmt-2026-10-20T0825](mgmt-2026-10-20T0825/README.md) | T33378, T47199, T33416 | 2 PASS, 1 **FAIL** |
| [tacacs-2026-10-20T0825](tacacs-2026-10-20T0825/README.md) | T33411, T33410, T33412 | 3 PASS |
| — | T33427 Flexera Licensing | **NOT TESTED** — Test Engineer's decision, needs a licence file |

Every case carries both STANDING-ORDERS §8 health samples. No reboot, no exception-log entry and
no crash, daemon restart or kernel error in any case.

T33413 was run twice. **Run 2 is the record**; run 1's PARTIAL / "NOT MEASURABLE" was wrong and
is superseded. The final log describes run 2 alone.

## Findings

### Measured

- **T47199 — a device still on the factory password `friend` gives NO warning, on any path.**
  0 warnings in 6 logins, with a `banner exec` marker proving the instruments see a message at
  that exact position, plus a RestCONF cross-check. Graded FAIL. `platforms/x960.md` §7F.4.
- **T33413 — the over-temperature trap works, and its enable command does not gate it.** The
  trap was produced by lowering `/sys/class/hwmon/hwmon1/temp1_max` from 61000 to 20000 against
  a real unchanged 27 °C reading, via `start-shell`. Three assert/clear cycles, six transitions,
  six traps, against a silent baseline. **The trap is still sent with `snmp-server enable trap
  hw-monitoring` removed and never re-added**, shown by two controlled 150 s captures.
- **AW+ silently swallows a chained `| exclude` after `| include`.** No error, the command
  succeeds, nothing is excluded — the output *looks* filtered. This affects the §8 health read
  directly. `platforms/x960.md` §7G and STANDING-ORDERS §8 (commit `61c9e03`).
- The DUT stores management secrets three different ways, and the **SNMP community is
  plaintext**. Queue `## Issues`.
- RADIUS, TACACS+, RMON, sFlow v5, SNMP traps and interface triggers all work as specified,
  with the per-case exceptions in each log's CAVEAT.

### 🔥 The 9600 console trap — measured 2026-10-20, and it produced a wrong diagnosis first

**`bench_probe.py`'s baud DETECTION corrupts the login dialog on a 9600 console, but only when a
login is actually required.** Measured three times in a row:

| run | consoles | u2 (115200) | u3 (9600) | u5 (9600) |
| --- | --- | --- | --- | --- |
| mixed, auto-detect, u3 at `login:` | u2,u3,u5 | ok | **login_failed** | login_failed |
| `--baud 9600` | u3,u5 | — | **ok** | login_failed |
| mixed, auto-detect, u3 already logged in | u2,u3,u5 | ok | **ok** | login_failed |

The probe's own code comments the mechanism: a CR sent at the wrong rate during detection
arrives as a garbage character and leaves the port mid-dialog. A console already at an exec
prompt needs no login dialog, so there is nothing to corrupt — which is why the 2026-10-19 run
succeeded on u3 and the first run today did not.

**How to tell this apart from a bad password, which is the part that matters.** Read the
`login:` note in the capture's `meta.json`:
- `"no prompt after login. tail=''"` — an **empty** read. Not an authentication failure. A wrong
  password makes AW+ print `Login incorrect` and a fresh `login:`, so the tail would END WITH
  `login:`. Empty means the dialog desynced. **This is the baud trap.**
- `"no prompt after login. tail='terminal no monitor\r\nPassword: '"` — the login proceeded and
  the device is asking for a password the probe does not have. **This is a real credential.**

Both consoles showed the first form on the first run, and I wrote them up as "both devices
refuse their credentials". That was wrong: two devices changing their password on the same
afternoon is a far less likely story than one driver mishandling one baud rate, and the empty
tail distinguishes them. **The Test Engineer corrected it by saying he can log in to all three.**

### swi_a (u5) — resolved by hand on 2026-10-21, and two things it taught

The Test Engineer supplied the password and cleared the account. A **hand-paced** login then
succeeded first time and read the unit:

- **S/N `A10713A262600012` — this MATCHES `tb277.static`'s `A10713A262600012 = swi_a, 3,
  10.36.230.35`.** The `swi_a = u5` mapping had never been confirmed by a serial read before;
  it is now.
- Software `awplus_main-20261019-73` (a **different build train** from the x960s'
  `sin_x96056-*`). `enable` needs **no** password.
- 🔴 **`Current boot image : Not set`.** swi_d reads `flash:/x960-tb277.rel (file exists)`.
  swi_a has no boot image pointer at all, so **a reload may not bring it back**. Nobody should
  reload swi_a until this is understood. Not investigated further.
- The console **logs itself out on `exec-timeout`**, so a login does not persist between
  sessions.

**What made the login work, after ~15 automated attempts had failed:** wait for the COMPLETE
`Password:` prompt before writing the password, instead of firing on first output. The echo on
this console reads `maPassword:` — the username echo is still in flight when the prompt
arrives. That truncated echo is cosmetic; the username itself arrives intact. An earlier claim
in this file that the username was being mangled was **wrong**.

**🔴 The lockout, and the warning.** `manager` on swi_a was already at **7 failed logins** before
this session touched it, which fits the aaa group's RADIUS work that morning. Each
`ckcon.py` invocation makes about **four** login attempts, and each one **re-arms** the
five-minute lock — so the counter climbed 7 -> 8 -> 10 -> 11 under repeated "single" retries and
the lock never expired. **Waiting cannot clear a lock while anything is still retrying.** Only a
successful login resets the counter, and on a locked account that has to be done by hand.

## OPEN questions

1. **How should `bench_probe.py` get swi_a's password?** Confirmed 2026-10-21: the probe reaches
   a login prompt and fails with `Login incorrect`, because its `PASSWORDS` list is **hardcoded**
   (`["friend", "P@ssw0rd", "awplus"]`, line 163) and it reads no environment variable. swi_a's
   password is none of those. A credential must never be committed to this repo, so the probe
   needs to read one from the environment, as `tools/console.py` already does (`CK_USER` /
   `CK_PASSWORD`). **Two designs, and the choice has a lockout consequence:**
   - **One global `CK_PASSWORD`, tried first.** Simple. But on swi_d and swi_b, whose password
     IS a default, it adds one failed login each per probe run.
   - **Per-console (e.g. `CK_PASSWORD_U5`).** No wasted attempts anywhere. More code.
   Given that this bench has already locked an account out to 11 failures, the per-console form
   is the safer one. **Until this is decided, swi_a stays `login_failed` in `bench-state.md`** —
   its measured facts are in the unit table above instead. swi_d and swi_b are unaffected.
2. **May the layer 3 underlay be written to startup-config?** `vlan10 10.38.22.34/27` and
   `vlan48 10.38.22.66/27` exist in running-config only and predate this campaign. One decision
   unblocks reboot persistence for every case in the campaign **and** settles whether the
   hw-monitoring trap finding is missing gating or only a delay in applying the removal. A
   reload today would destroy the path to the trap receiver.
3. **Enable authentication via TACACS+ (S1599.1.011-016)** was never measured. It needs a
   recoverability plan before anyone attempts it.
4. **The pre-existing RADIUS secret is in git history.** `show radius` prints a global key that
   was on the DUT before this campaign; no case set it. The final logs and `.cfg` files are
   clean, and `work/` is deleted — but `work/` was committed per case, so the key is in the
   history of the unpushed commits. **Decide before pushing.**
5. **`show cpu` on the x960 never prints an idle percentage**, but the `HEALTH:` template in
   `logged-output.md` §4 asks for one. All 13 cases recorded load instead and said so. The
   template needs a one-line change.
6. **Three partner `.cfg` files were never captured**: `T47199/swi_b.cfg`, `T33416/swi_b.cfg`,
   `T44301/swi_b.cfg`. swi_b is in all three topologies. Not a check failure — no `Configs:`
   line names a missing file — but a gap against `logged-output.md` §2.

## Ordered next steps

1. Push: `git push origin main` (after deciding OPEN 4). **53 commits pending.**
2. Decide OPEN 1 so the probe can reach swi_a; `bench-state.md` already describes swi_d and
   swi_b. **When probing a bench with mixed baud rates, pin the slow consoles first**:
   `tools/tb probe tb277 --consoles u3,u5 --baud 9600 --no-prompt`, which leaves them logged in,
   then run the full mixed probe.
3. Answer OPEN 2, then re-run the persistence limb of the affected cases.
4. Stop the TACACS+ server when it is no longer wanted: `ssh tb277 "sudo systemctl stop tacacs_plus"`.

## Recipes

**Drive an AW+ root shell** (new this session — no existing driver could, because
`console.PROMPT_RE` cannot match `[root@awplus flash]#`, the character before `#` being `]`):

```bash
tools/tb awshell tb277 <scratch> u2 115200 --timeout 60 \
  "cat /sys/class/hwmon/hwmon1/temp1_max" "echo 20000 > /sys/class/hwmon/hwmon1/temp1_max"
```

It always returns the console to exec, exit 5 if it cannot.

**Force a temperature alarm on the x960-56YSQ.** `Temp: Front Right` is **hwmon1/temp1**
(adt7476 at i2c-1 0x2d), *not* hwmon0 — hwmon0 is an MDIO PHY and appears in no CLI output.
There are no label files, so join hwmon to the 14 CLI sensors on reading + low limit + high
limit together. PSU sensors take their CLI limit from `tempN_rated_max`, not `tempN_max`. Lower
`temp1_max` below the current reading, wait one poll (the alarm is **not** immediate on write,
in either direction), then restore 61000 and verify with `od -c` → `6 1 0 0 0 \n`, 6 bytes.
`rcdiff` cannot see a sysfs write, so that read-back is the only real proof of restoration.

## Pointers

- Topology: `bench-setup/tb277/bench-state.md` (regenerated **2026-10-20T050132Z**: swi_d and
  swi_b with all four links; swi_a `login_failed`, see OPEN 1).
- Platform facts: `platforms/x960.md`, §7E (AAA/RADIUS), §7F (management), §7G (the filter defect).
- The campaign: `CAMPAIGN-QUEUE-2026-10-20T0825.md`, including its `## Issues`.
- Process reviews: each group's `REVIEW.md` and each case's `<id>-review.md`.
