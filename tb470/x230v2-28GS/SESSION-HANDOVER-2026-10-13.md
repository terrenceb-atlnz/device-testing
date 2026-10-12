# Session handover — 2026-10-13: x230v2-28GS office-hours campaign (5 cases), bench config fixes

Session `50f164f5` (VS Code, desktop), the same session as the 2026-10-09 x230 campaign (its handover, with the 10-12
update, is [SESSION-HANDOVER-2026-10-09.md](SESSION-HANDOVER-2026-10-09.md)). Wrapped ~12:20 NZDT on `/wrap-dt`.

## Update 12:2x (after the wrap)
- OPEN 2 closed: T47228 FAIL stands (Terrence). OPEN 3 closed: the TPM daemon is how the unit reaches the idevid servers.
- OPEN 4 done: `no lacp global-passive-mode enable` + `write` on the x230, 12:16 (running = startup).
- OPEN 1 researched: CLI `polarity` page and the Switching Feature Overview Guide (C613-22037-00 REV E) cover copper ports
  "on the switch" only, nothing on copper SFPs; `speed` page separates tri-speed vs 1000-only copper SFPs; framework suite
  5703 (test-5000.1003) tests copper-SFP polarity as platform-dependent. Recommendation given: UNSUPPORTED. Verdict still his.
- OPEN 5: Terrence to run `apply` (bench-state.md is the full six-unit file).

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (option text: "u0 = x230v2-28GS DUT (swi_f); u1 = AR4050S partner (swi_e). The IE520 stack (u2/u4/u5) and IE520-sa (u3) are left alone.")
PDU: 10.36.150.14, u0=1, u1=7
Constraints: "Office hours, no reloads; T33234 too"

## TL;DR
- **Campaign complete: 5 cases → 2 PASS (T20358, T33234), 1 FAIL (T47228), 1 PARTIAL (T45543), 1 UNSUPPORTED (T30403).**
  Results: [CAMPAIGN-QUEUE-2026-10-13T0949.md](CAMPAIGN-QUEUE-2026-10-13T0949.md) `## Results`.
- **Final logs NOT created yet: 5 cases hold `work/`.** Run `/create-logs tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-13T0949.md` after review.
- **Bench is whole** (u0/u1 read 12:1x): both units boot `flash:/tb470-bench.cfg (file exists)`, running = startup, no
  exceptions, consoles at exec. The x230 port1.0.6/1.0.7 loop is fixed and saved. **`bench_probe.py apply` is still yours**
  (one new link, x230 port1.0.8 <-> 4050 port1.0.5).
- **Both units were power-cycled on 2026-10-12 ~15:58 by another campaign** (see Findings).
- **Committed, NOT pushed** (push is yours: `git push origin main`).

## Bench state at the wrap (read 12:1x on u0/u1 only; u2-u5 belong to a concurrent IE520 Ask-CK campaign)
- **x230 (u0, swi_f):** boot config `flash:/tb470-bench.cfg (file exists)` (default.cfg untouched, fallback); boot image
  `x230v2_28GS-awplus_main-20261008-57.rel (file exists)`; secure mode disabled; running-config = startup-config; flash
  `.cfg` files: tb470-bench.cfg, default.cfg only; exception log None. **port1.0.7 `shutdown` (saved)**: port1.0.6 <->
  port1.0.7 is a direct copper lead, a loop with STP off. Saved isolation: VLAN 103/104/105/108 on port1.0.3/1.0.4/1.0.5/1.0.8,
  `lldp run`. `lacp global-passive-mode enable` is in the saved config (see OPEN).
- **AR4050S (u1, swi_e):** boot config `flash:/tb470-bench.cfg (file exists)`; running = startup; port1.0.5 in VLAN 108
  (saved 09:48); port1.0.2 `shutdown` (VLAN 10, cabled to x230 port1.0.1); exception log None.
- **Links added today (Test Engineer):** x230 port1.0.6 <-> 1.0.7 (AT-SPTX both, copper); x230 port1.0.8 (AT-SPTXc) <->
  4050 port1.0.5 (crossover).
- **bench-state.md** = the full u0-u5 capture `2026-10-12T204840Z` (09:48 NZDT, commit 36e1557): diff vs the deployed
  setup is exactly `[portlink] swi_e-swi_f port1.0.5-port1.0.8` EXTRA. The last u0/u1-only probe (`2026-10-12T230610Z`,
  12:06) showed the same set. A full u0-u5 re-probe waits until the IE520 campaign releases u2-u5.
- No tool processes on tb470; no host change (no IPs, routes, ethtool). No reload, no `write` by any case, no PDU cycle today.
- Verify in one go (from the repo root):
  `tools/tb precheck tb470 0,1 && tools/tb probe tb470 --consoles 0,1 --no-prompt --pdu 10.36.150.14 --outlet u0=1,u1=7 --baud 115200`
  (then `git checkout bench-setup/bench-state.md`: a u0/u1 probe writes a two-unit file; never `apply` from it).

## What was accomplished (2026-10-13)
1. **Loop found and stopped 09:19:** the Test Engineer's new x230 port1.0.6 <-> 1.0.7 lead (VLAN 1, STP off) was looping
   ~230 Mbps each way. port1.0.7 shut, then saved on his "write the running config" (09:28).
2. **Crossover isolated and saved:** x230 port1.0.8 and 4050 port1.0.5 into VLAN 108, `write` on both (Test Engineer:
   "reconfigure the devices as you require, write the configs").
3. **Records:** [MANUAL-ONLY.md](../../MANUAL-ONLY.md) (new tracked list + memory `manual-only-cases-tracked`, test-mode
   triage reads it); memory `awplus-restconf-api-reference` (guide tracked by LOCATION; measured x230 facts added by the
   tester); [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md) (x220 lineage, polarity, duplex refusal, RESTCONF, TPM).
4. **Campaign** (`/test-mode`, this session = sentinel): triage 09:50-10:01, group 1 11:18-11:43, group 2 11:44-12:07.
5. **New tool:** [tools/restconf.py](../../tools/restconf.py) (stdlib RESTCONF client, README entry).

## Results — all runs clean; final logs NOT created
| case | verdict | one line |
| --- | --- | --- |
| T30403 | UNSUPPORTED | no multicast routing: `ip mroute`/`ip multicast-routing`/`ip pim`/`show ip mroute` not in the parser |
| T45543 | PARTIAL | steps 1-2 PASS ("TPM is instantiated" = OK, ruling); step 3 idevid MANUAL-ONLY, NOT RUN |
| T20358 | PASS | port1.0.7 Backup/Discarding in 5 s; 8356 eth3 broadcasts, 0 broadcast TX on port1.0.7, none back to eth3 |
| T47228 | FAIL | RESTCONF: interface disable/enable by PUT works; VLAN create 204 with no effect, delete 403; PATCH 204 no-op |
| T33234 | PASS | auto MDI-X up on crossover and straight copper-SFP leads; 7/7 launched TCs PASS, 0 power cycles; TC9/10 UNSUPPORTED (10 Mb/s ruling); 8 forced-polarity TCs UNSUPPORTED **pending the Test Engineer** |

Clean: no reload, no PDU cycle, every running-config diff empty after its case; the concurrent IE520 campaign did not
cycle u0/u1 during the run (its outlets are 4/5/6/8).

## Findings
**Measured:**
- **2026-10-12 power cycle of the x230 and 4050 by another campaign.** `show reboot history`: x230 `2026-10-12 15:59:33
  Unexpected System reboot`, 4050 `2026-10-12 15:58:59 Unexpected System reboot`. That matches the framework's
  `power-group-20261012.log` 15:57:57 "Power outlets have been successfully turned off" / 15:58:20 "!! ERROR: power outlets
  have not been successfully turned on in 3 attempts", in the Ask-CK run `tb470/IE520/CAMPAIGN-QUEUE-2026-10-12T1537.md`
  (`Consoles: "all"`, T33235 run 1 failed its exception-log check). Its queue says "Nothing on the x230 (u0) … 4050 (u1)",
  but the post-failure power cycle covered every outlet. Both units came back on `tb470-bench.cfg`.
- x230 copper SFPs refuse forced polarity ("Polarity mode not supported on this interface"); auto MDI-X works.
- x230 RESTCONF behaviour (T47228 row; memory `awplus-restconf-api-reference`).
- The x230's TPM daemon talks to `tpm_server` on localhost:2321 (`--tcti=mssim`).
**Inferred:** the TPM is a software simulator on this dev build (not proven: a hardware-TPM build or the TPM owner would
settle it).

## Process notes
- **u0/u1-only probes rewrite bench-state.md with two units** and the result looks like a template that has lost the IE520s.
  The triage tester caught it before any apply; the full file was regenerated from capture `204840Z` (36e1557). With a
  concurrent campaign on the other consoles, only `git checkout` the partial file; never apply from it.
- **Sentinel narrator cross-attributes campaigns:** `sentinel.sh` reads every `/tmp/*/console-*.log` on the box, so with
  two campaigns it narrated the IE520 campaign's u5 activity as this tester's (11:57; the tester never opened u2-u5). Fix
  candidate: scope `CLI_GLOB` to the campaign's own scratch dirs (queue Issues).
- `ckcon --stop-on-error` stops on `% `-prefixed lines in `show spanning-tree interface` output (T20358's first closure).

## OPEN (Test Engineer)
1. T33234: are the 8 forced-polarity TestCases UNSUPPORTED? (Otherwise the case verdict changes.)
2. T47228: FAIL as graded, or UNSUPPORTED for the VLAN half?
3. T45543: is a software TPM simulator expected on this build?
4. `lacp global-passive-mode enable` in the x230's `tb470-bench.cfg`: remove and `write`? (memory
   `lacp-passive-hides-links-from-stp`)
5. `bench_probe.py apply` for `swi_e-swi_f port1.0.5-port1.0.8` (bench-state.md is the full one; safe now).
6. The 2026-10-12 Ask-CK run power-cycled outlets 1 and 7 although its scope said "nothing on the x230/4050": should an
   Ask-CK run with `Consoles: "all"` exclude outlets of units it does not use?
7. Tonight's after-hours list (not set up): T44179 (jumbo; `tools/tb mtu` action to build), T46810 and T28218 (ATMF, 4050
   master), T31868, T47119/T47121/T47120-CLI (4050 as the reference).

## Next steps
1. Review the Results; answer OPEN 1-3; then `/create-logs tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-13T0949.md`.
2. `apply` (OPEN 5) and decide OPEN 4.
3. Set up the after-hours run (OPEN 7).

## Pointers
- Queue and results: [CAMPAIGN-QUEUE-2026-10-13T0949.md](CAMPAIGN-QUEUE-2026-10-13T0949.md)
- Bench: [../../bench-setup/bench-state.md](../../bench-setup/bench-state.md)
- Platform facts: [../../platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md)
- Manual-only list: [../../MANUAL-ONLY.md](../../MANUAL-ONLY.md)
- Concurrent IE520 campaign: [../IE520/CAMPAIGN-QUEUE-2026-10-13T0954.md](../IE520/CAMPAIGN-QUEUE-2026-10-13T0954.md)
