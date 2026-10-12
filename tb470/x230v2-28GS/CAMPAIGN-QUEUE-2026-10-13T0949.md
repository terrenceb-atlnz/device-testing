# Campaign queue — tb470, x230v2-28GS as the DUT, 5 AWPTCM cases (office hours), from 2026-10-13 09:49 NZDT

The ask, Test Engineer 2026-10-13 (after the 2026-10-09 campaign's NOT TESTED review):
*"yes to all, reconfigure the devices as you require, write the configs, and then start the office-hours test mode run."*
Cases: T30403, T45543, T20358, T33234, T47228.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-13 09:49 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (option text: "u0 = x230v2-28GS DUT (swi_f); u1 = AR4050S partner (swi_e). The IE520 stack (u2/u4/u5) and IE520-sa (u3) are left alone.")
PDU: 10.36.150.14, u0=1, u1=7 (option text: "Per tb470.static. Only these two outlets are written into the run's setup, so a framework post-failure power cycle touches only the x230 and 4050.")
Constraints: "Office hours, no reloads; T33234 too" (option text: "No CLI reload of any unit. T33234 runs now on a u0/u1-only setup: the tester checks its defaulting commands (polarity, speed) on both units first and stops at the first systematic failure, so at worst one x230+4050 power cycle.")

Test Engineer's rulings carried into this campaign (2026-10-13):
- T45543: steps 1-2 only; step 3 is MANUAL-ONLY (MANUAL-ONLY.md). *"'TPM is instantiated' is the same as TPM is OK."*
- T47228: *"use the API commands to enable/disable interfaces, and also add/delete VLANs"*; the API is RESTCONF
  (memory `awplus-restconf-api-reference`: enable steps, interface `enabled` path; the VLAN create/delete path is open and
  is to be settled from the x230's own ietf-yang-library, then the memory updated).
- 10 Mb/s is not supported on the copper SFPs (re the T47208 caveat).
- The x230v2-28GS is x220 hardware; x220 naming on it is expected (platforms/x230v2-28GS.md §1).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies, tightened by the constraint above: **no CLI reload of any unit**. A framework
  post-failure PDU cycle of u0/u1 is accepted (§6); a systematic failure stops the run.
- **Only u0 and u1 are touched.** The IE520 stack (u2/u4/u5) and IE520-sa (u3) are not opened, configured or probed
  beyond `bench_probe.py`'s own read.
- Case texts: Ask-CK `ck.db` table `zephyr_cases` (read-only: `sqlite3 'file:<path>/ck.db?mode=ro'`), key `AWPTCM-T<n>`.
- MANUAL-ONLY.md (repo root) is read at triage.
- Platform traps: [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md). The previous campaign's working logs are in git
  history (`git show a6fcbf5^:…`), its final logs and reviews under `*-2026-10-09T0845/`.

## Bench at queue creation (2026-10-13 09:48, before the Test Engineer's apply)

- Probe `2026-10-12T204*Z` (u0-u5): MISMATCH (1): `[portlink] swi_e-swi_f` EXTRA_IN_LIVE `port1.0.5-port1.0.8` (the new
  crossover, x230 port1.0.8 <-> 4050 port1.0.5). `bench_probe.py apply` is the Test Engineer's, requested 09:49.
- x230 (u0) boots `flash:/tb470-bench.cfg` (saved 09:28): VLAN 103/104/105/108 on port1.0.3/1.0.4/1.0.5/1.0.8, `lldp run`,
  **port1.0.7 `shutdown`** (port1.0.6 <-> port1.0.7 is a direct copper lead: a loop unless STP blocks one end).
  Pluggables: 1.0.1 AT-SPTXa, 1.0.2/1.0.3/1.0.6/1.0.7 AT-SPTX, 1.0.4 AT-SPSX, 1.0.5/1.0.8 AT-SPTXc.
- AR4050S (u1) boots `flash:/tb470-bench.cfg` (saved 09:48): port1.0.5 in VLAN 108; port1.0.2 `shutdown` (VLAN 10,
  cabled to x230 port1.0.1, straight-through); port1.0.1 = tb470 eth2.
- Links for this campaign: x230 port1.0.1 <-> 4050 port1.0.2 (straight Cat5e); x230 port1.0.8 <-> 4050 port1.0.5
  (crossover); x230 port1.0.6 <-> port1.0.7 (copper, loop lead); x230 port1.0.5 <-> tb470 eth3.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | CLI / API cases: T30403, T45543, T20358, T47228 | tb470/x230v2-28GS/cli-2026-10-13T0949/ | DONE 11:43 (T30403 UNSUPPORTED, T45543 PARTIAL, T20358 PASS, T47228 FAIL; bench restored) | manual CLI on u0 (+ u1 if needed); T30403 read-only UNSUPPORTED evidence; T45543 steps 1-2; T20358 RSTP on x230, then `no shutdown` port1.0.7, eth3 broadcast; T47228 RESTCONF from tb470 over eth3 (x230 vlan105 IP) |
| 2 | MDI/MDI-X framework: T33234 (scripts 5000.0003 straight, 5000.0004 crossover) | tb470/x230v2-28GS/mdix-2026-10-13T0949/ | DONE 12:06 (T33234 PASS: 7/7 launched TCs PASS, 0 power cycles; forced-polarity TCs 0004/0003 TC2-5 UNSUPPORTED pending the Test Engineer, TC9-10 UNSUPPORTED by ruling; bench restored) | the scripts' source: ck.db `scripts` table (`test_scripts/5000_mdi_mdix/`); dut = x230, remote = 4050; u0/u1-only setup; check defaulting commands (polarity) on both units before launch (STANDING-ORDERS §6) |

## Triage 2026-10-13 09:50-10:01 (bench-runner, TRIAGE)

**5 runnable / 0 blocked by topology / 0 blocked otherwise**; T45543 step 3 MANUAL-ONLY (already listed). Probe
`2026-10-12T205148Z` (u0,u1 only): exit 1, the only real diff the expected EXTRA `swi_e-swi_f port1.0.5-port1.0.8`
(the partial read also shows an artefact `tb-swi_f eth1-port1.0.2` and MISSING lines for the unread IE520s). The partial
bench-state.md it wrote was replaced by the sentinel from the full capture `2026-10-12T204840Z` (commit 36e1557).
- Clocks: x230 reads NZDT wall time labelled UTC (no timezone); 4050 correct. Host NICs: eth1 00:f0:4d:00:77:16 .1/27,
  eth2 00:f0:4d:00:77:17 .33/27, eth3 00:f0:4d:00:77:18 .65/27.
- Concurrent: Ask-CK IE520 validation `tb470/IE520/CAMPAIGN-QUEUE-2026-10-13T0954.md` (T33235, u2-u5, outlets 4/5/6/8 only,
  excludes u0/u1). Its power cycles can flap x230 port1.0.2-1.0.4 and 4050 sa1 (port1.0.3/1.0.4): theirs, not DUT faults.
- T47228: `service restconf` is "% Unrecognized command" on this build (guide: not required after 5.5.4-1); `service http`
  already on; vlan105 needs the in-test IP 10.38.215.90/27; client = new `tools/restconf.py` run on tb470; toggle port1.0.8.
- T33234: scripts 5000.0003/0004 + library_5000.py extracted read-only from ck.db `scripts` (sha1 match); case setup
  `tb470-mdix-u0u1.setup` (swi_a = u0 x230, swi_b = u1 4050; [misc] dutSFPCopper/linkpSFPCopper = port1.0.1/port1.0.2,
  dutSFPCopperX/linkpSFPCopperX = port1.0.8/port1.0.5). Defaulting is `speed/duplex/polarity auto` (no `no polarity`).
  Before launch: prove forced polarity takes the crossover link down; capture TC6/TC8 refusal text. Bench setup once:
  4050 port1.0.2 -> VLAN 22, x230 port1.0.1 -> an unused VID; restore once after (incl. `boot config-file
  flash:/tb470-bench.cfg` on both, delete the framework's .cfg files).

**Test Engineer's answers, 2026-10-13 ~10:2x:**
- "Proceed with all 5" (option text: "Group 1 (T30403, T45543, T20358, T47228), then group 2 (T33234: 0004 then 0003), with the pre-launch checks above.")
- TC9/TC10: "Exclude, grade UNSUPPORTED" (option text: "Run 0003 with --include-test-cases 1 2 3 4 5 6 7 8 11; TC9/TC10 recorded UNSUPPORTED under your ruling. Avoids ~2 power cycles.")
- TC6 refusal text: "Exclude TC6, note why" (option text: "Run without TC6 and record the library defect plus the captured CLI refusal as the evidence; no script change.")

## Run, group 1 (cli-2026-10-13T0949) -- bench setup and restore recipe (bench-runner, written 11:2x before the first case)

Gate 11:19-11:21: precheck u0,u1 CLEAR; peek u0 `awplus login:`, u1 `4050-5g#` (left logged in by the triage);
`/nfsHome` mounted; probe `2026-10-12T221943Z` (u0,u1, `--baud 115200`) exit 1 with only the known diffs (EXTRA
`swi_e-swi_f port1.0.5-port1.0.8`, artefact `tb-swi_f eth1-port1.0.2`, MISSING for unread IE520s). Both units:
`Current boot config: flash:/tb470-bench.cfg (file exists)`. Group baseline (running-config, show boot, show system) of
u0 and u1: `cli-2026-10-13T0949/30403/work/prerun-u0.out`, `prerun-u1.out`; every case's teardown diffs against it.
Scratch on tb470: `/tmp/x230cli-0949/` (transcripts `console-u0.log`, `console-u1.log`). **No `write` on either unit,
no reload.**

Per case, running-config only (x230 = u0 unless named):
- **T30403** read-only plus refused config commands (`ip multicast-routing`, `ip mroute ...`); nothing to restore
  beyond proving the running-config unchanged.
- **T45543** read-only (`show platform full-debug | grep tpm`, `show system tpm`). Step 3 NOT RUN (MANUAL-ONLY).
- **T20358** setup: `no lacp global-passive-mode enable`; `spanning-tree rstp enable` (mode is already rstp);
  port1.0.6 and port1.0.7 `switchport access vlan 105` (port1.0.5 = tb470 eth3 is already VLAN 105); prove no
  `channel-group` on 1.0.6/1.0.7 and both listed in `show spanning-tree brief`; only then port1.0.7 `no shutdown`;
  gate: port1.0.7 Backup/Discarding within 20 s, else `shutdown` port1.0.7 at once. Broadcast from eth3
  (`tools/linerate.py`, 10 Mb/s).
  **Restore, in this order:** `interface port1.0.7` / `shutdown` (FIRST: the lead is a loop with STP off);
  `interface port1.0.6-1.0.7` / `no switchport access vlan` (back to VLAN 1); `no spanning-tree rstp enable`;
  `lacp global-passive-mode enable`; then diff running-config against `prerun-u0.out`.
- **T47228** setup: `interface vlan105` / `ip address 10.38.215.90/27` (tb470 eth3 = .65/27); RESTCONF over HTTPS
  from tb470 with `tools/restconf.py` (manager, priv 15); toggle x230 port1.0.8 (4050 port1.0.5 side observed
  read-only on u1); create/delete a test VLAN (VID 3999, not otherwise used on the bench).
  **Restore:** port1.0.8 `no shutdown` (enabled), VLAN 3999 absent (`no vlan 3999` under `vlan database` if left),
  `interface vlan105` / `no ip address`, `no interface vlan105` if the case created it; anything else the API
  changed is reverted by running-config diff against `prerun-u0.out` (and u1's against `prerun-u1.out`).
- **If the tester dies mid-group:** on u0 apply the T20358 restore (port1.0.7 `shutdown` first), then the T47228
  restore, then diff against `prerun-u0.out`; `show boot` must still read `flash:/tb470-bench.cfg`.

- **After the group (11:38-11:43):** both units restored by running-config diff against `prerun-u0/u1.out` (rcdiff
  empty, u0 and u1, `47228/work/teardown-u*.out`); `show boot` on both `Current boot config: flash:/tb470-bench.cfg
  (file exists)`; x230 port1.0.7 `shutdown`, STP off, `lacp global-passive-mode enable` as baseline. Post-run probe
  `2026-10-12T224215Z` (u0,u1, same facts): exit 1 with the identical diff set as the pre-run probe (only the known
  EXTRA crossover + eth1 artefact). bench-state.md checked out again (the u0/u1 probes rewrite it partially). Nothing
  left running on tb470; consoles at exec. No write, no reload, no PDU cycle.

## Run, group 2 (mdix-2026-10-13T0949) -- bench setup and restore recipe (bench-runner, written 11:5x before the first TestSet)

Gate 11:44-11:47: precheck u0,u1 CLEAR; peek u0 `awplus#`, u1 `4050-5g#`; `/nfsHome` mounted; probe
`2026-10-12T224457Z` (u0,u1, same facts, `--baud 115200`) exit 1, the same known diff set as group 1 (bench-state.md
checked out again). Both units `Current boot config: flash:/tb470-bench.cfg (file exists)`. Group baseline:
`mdix-2026-10-13T0949/33234/work/prerun-u0.out`, `prerun-u1.out`. Scratch on tb470: `/tmp/mdix-0949/`. Case setup
file: `33234/work/tb470-mdix-u0u1.setup` (swi_a = u0 x230, swi_b = u1 4050, outlets 1/7 only). Framework workdirs
`/home/st-art/pytest-create/33234/0004-run1/` and `.../0003-run1/`. **No `write`, no reload.**

**Bench setup (applied 11:48, once for both TestSets):**
- u1 (4050): `interface port1.0.2` / `switchport access vlan 22` (the existing empty `flap-deadend` VLAN) / `no shutdown`.
- u0 (x230): `vlan database` / `vlan 101 name mdix-tmp`; `interface port1.0.1` / `switchport access vlan 101`.
- Straight link x230 port1.0.1 <-> 4050 port1.0.2 up at 1000/full; crossover port1.0.8 <-> port1.0.5 unchanged (VLAN 108).

**Restore (once, after both TestSets, or by a fresh tester if this one dies):**
- u0: `interface port1.0.1` / `no switchport access vlan` (back to VLAN 1); `interface port1.0.1` and
  `port1.0.8`: `speed auto`, `duplex auto`, `polarity auto`; `vlan database` / `no vlan 101`.
- u1: `interface port1.0.2` / `switchport access vlan 10` / `shutdown`; `interface port1.0.2` and `port1.0.5`:
  `speed auto`, `duplex auto`, `polarity auto`.
- Both: if `show boot` no longer reads `flash:/tb470-bench.cfg`, `boot config-file flash:/tb470-bench.cfg`; delete
  the framework's `<hostname>.cfg` (x230 `flash:/awplus.cfg`, 4050 `flash:/4050-5g.cfg`, or whatever name the run log
  shows) only if it was not there before (baseline `dir` checked first).
- Prove it: rcdiff of `show running-config` against `prerun-u0.out` / `prerun-u1.out` empty.

- **After the group (12:04-12:06):** restored as above; both boot pointers back to `flash:/tb470-bench.cfg` (the
  framework had moved them to `swi_a/b_5000_0003.cfg`); 10 framework `.cfg` files deleted on each unit; rcdiff empty u0
  and u1 (`33234/work/teardown-u*.out`). Post-run probe `2026-10-12T230610Z`: exit 1, identical diff set to the pre-run
  probe. bench-state.md checked out. Consoles at exec. No write, no reload, no PDU cycle.

**Test Engineer's answers after the campaign, 2026-10-13 ~12:2x:**
- T47228: *"yea that sounds like a fail. good catch."* (FAIL stands).
- T45543 TPM simulator: *"yes, it tries to talk to the idevid servers"* (expected; not a fault).
- x230 `lacp global-passive-mode enable`: *"write it"* -> `no lacp global-passive-mode enable` + `write` on u0, 12:16 (tb470-bench.cfg).
- `bench_probe.py apply`: *"apply"* (the Test Engineer runs it; denied to the session by his settings).
- T33234: *"what does 'SFP' stand for"* / *"thats right. So, by definition, thats *no* a fixed copper port, right"* -> re-graded
  UNSUPPORTED (his 2026-09-29 ruling, queue I-5 of tb470/IE520 port-2026-09-29: an SFP cage is not a fixed copper port for MDI/MDI-X).
  The sentinel's 10-13 re-triage that called T33234 runnable via the copper-SFP scripts 5000.0003/0004 contradicted that ruling.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T30403 | Check traffic is fowarded with static mroutes (IPv4) | cli-2026-10-13T0949 | UNSUPPORTED | x230v2-28GS has no multicast routing: ip mroute / ip multicast-routing / ip pim / show ip mroute absent from the parser (% Invalid input), no PIM licence feature; running-config unchanged | cli-2026-10-13T0949/30403/work/run1.log | tester |
| T45543 | TPM Support | cli-2026-10-13T0949 | PARTIAL | steps 1-2 PASS ("show platform full-debug \| grep tpm" lists tpm2-abrmd + tpm_server; "TPM is instantiated" = OK per ruling), step 3 idevid NOT RUN (MANUAL-ONLY); note: tpm2-abrmd uses --tcti=mssim to /usr/bin/tpm_server on localhost:2321 (a software TPM simulator), recorded ungraded | cli-2026-10-13T0949/45543/work/run1.log | tester |
| T20358 | STP loop between x230 ports | cli-2026-10-13T0949 | PASS | RSTP on, port1.0.6<->1.0.7 lead closed in VLAN 105: port1.0.7 Backup/Discarding in 5 s (Received RSTP from own bridge); 8356 broadcast frames from eth3 flooded by port1.0.6, 0 broadcast TX on port1.0.7, none back to eth3; port1.0.7 shut first in teardown, rcdiff empty (first closure aborted by ckcon --stop-on-error on "% " lines, re-closed and measured) | cli-2026-10-13T0949/20358/work/run1.log | tester |
| T47228 | API-enable/disable interface, add/delete vlans | cli-2026-10-13T0949 | FAIL | RESTCONF on the x230v2 cannot add/delete VLANs (no VLAN-database model; PUT ietf-interfaces vlan3999 answers 204 but creates nothing, DELETE of a real VLAN is 403 access-denied) and PATCH of the enabled leaf answers 204 but changes nothing; interface disable/enable works by PUT {"enabled":false\|true} on the leaf, proven at both link ends; host-meta 404 | cli-2026-10-13T0949/47228/work/run1.log | tester |
| T33234 | Port - Auto MDI/MDI-X | mdix-2026-10-13T0949 | UNSUPPORTED | no fixed copper switchport on the x230v2-28GS (all 28 ports are SFP cages); an SFP is a pluggable transceiver, not a fixed copper port, so MDI/MDI-X does not apply (Test Engineer's ruling 2026-09-29 queue I-5, reaffirmed 2026-10-13). Supporting evidence from this run: copper SFPs refuse forced polarity ("% Polarity set failed", "Polarity mode not supported on this interface"); auto MDI-X through the module links on straight and crossover leads (7 launched TCs PASS, 0 power cycles) | mdix-2026-10-13T0949/33234/work/run1.log | Test Engineer, re-graded from PASS on 2026-10-13 |

## Issues

- 11:57 sentinel-kit issue: with two campaigns on tb470, sentinel.sh reads every `/tmp/*/console-*.log`, so its narrator
  attributed the concurrent IE520 campaign's u5 console activity to this campaign's tester. The tester confirmed it never
  opened u2-u5 (scratch /tmp/mdix-0949, u0/u1 only). Fix candidate: scope CLI_GLOB to the campaign's own scratch dirs.
- 09:19 (before this queue) x230 port1.0.6 <-> 1.0.7 loop found live (~230 Mbps each way, VLAN 1, STP off); port1.0.7 shut
  by this session, then saved into tb470-bench.cfg 09:28 on the Test Engineer's "write the running config".
