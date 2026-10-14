# Session handover — 2026-10-15: x230v2-28GS re-wrap (final logs created, bench verified)

Session `50f164f5` (VS Code, desktop): the same session as the 2026-10-09 and 2026-10-13 x230 campaigns. Wrapped
06:2x NZDT on `/wrap-dt`. Since the 10-13 wrap ([SESSION-HANDOVER-2026-10-13.md](SESSION-HANDOVER-2026-10-13.md)),
this session changed no device or box state. It took the Test Engineer's answers, re-graded T33234 on their word, and
ran `/create-logs`.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (option text: "u0 = x230v2-28GS DUT (swi_f); u1 = AR4050S partner (swi_e). The IE520 stack (u2/u4/u5) and IE520-sa (u3) are left alone.")
PDU: 10.36.150.14, u0=1, u1=7
Constraints: "Office hours, no reloads; T33234 too"

## TL;DR
- **Bench is whole**, read 2026-10-15 06:22 NZDT on u0/u1 only: both units up 2 d 14 h with no reboot since the 10-12
  15:58/15:59 power cycle. Both boot `flash:/tb470-bench.cfg (file exists)` with a valid image pointer. Running-config =
  startup-config on both, the exception log is None, and both consoles are at exec.
- **Campaign 2026-10-13T0949 is closed:** 1 PASS, 1 FAIL, 1 PARTIAL, 2 UNSUPPORTED. **Final logs created**: mdix
  `b7d69c0`, cli `af52dad`; no `work/` remains under `tb470/x230v2-28GS/`.
- **Committed, NOT pushed** (push is yours: `git push origin main`).

## Bench state at the wrap (read 06:22, u0/u1 only)
| unit | console | build | boot config | notes |
| --- | --- | --- | --- | --- |
| x230v2-28GS (swi_f) S/N A10783G262900002 | u0, 115200 | awplus_main-20261008-57 | `flash:/tb470-bench.cfg` saved 10-13 12:16 | port1.0.7 `shutdown` (saved; the 1.0.6<->1.0.7 lead loops otherwise); `lldp run`; `no lacp global-passive-mode enable`; VLAN 103/104/105/108 isolation |
| AR4050S (swi_e) S/N A10401G214000005 | u1, 115200 | awplus_main-20261008-57 | `flash:/tb470-bench.cfg` saved 10-13 09:48 | port1.0.2 `shutdown` (saved); port1.0.5 in VLAN 108 to x230 port1.0.8 |

- Both units are powered (PDU outlets 1 and 7). Nothing is running-only and nothing was left unrecovered.
- **Probe** `captures/2026-10-14T172342Z` (u0/u1): MISMATCH, and only from the probe's scope. Every listed item is a
  u2–u5 IE520 unit, link or outlet (`MISSING_IN_LIVE`), plus one `CHECK_CABLE` on tb-eth1 to port3.0.13; nothing is
  listed for swi_e or swi_f. The two-unit bench-state.md was restored with `git checkout`. The committed file stays
  the full u0–u5 capture `2026-10-12T204840Z`, which diffs MATCH against the template Terrence applied
  (`backups/2026-10-12T232145Z`).
- No tool process is left on tb470. Precheck CLEAR before and after. The box has no host change (no IPs, routes or
  ethtool). Scratch `/tmp/wrap1015/` is tmpfs.
- Sentinel: stood down at the 10-13 wrap. Re-checked now: no cron job and no `sentinel.sh` process.

Verify in one go (repo root):
```
tools/tb precheck tb470 0,1 && tools/tb probe tb470 --consoles 0,1 --no-prompt --pdu 10.36.150.14 --outlet u0=1,u1=7 --baud 115200
git checkout bench-setup/bench-state.md     # a u0/u1 probe writes a two-unit file; never apply from it
```

## What was accomplished since the 10-13 wrap
1. Test Engineer's answers: T47228 FAIL stands. The TPM daemon is expected (it reaches the idevid servers). LACP
   passive was removed and written (12:16). `apply` was run by Terrence (`fe119f1`).
2. **T33234 re-graded UNSUPPORTED** by the Test Engineer, because an SFP is not a fixed copper port (their
   2026-09-29 ruling, which triage had missed). New memory `sfp-is-not-a-fixed-copper-port`; platform row corrected
   (`dbded09`).
3. `/create-logs`: 5 final logs with `.cfg` files, plus the reviews.

## Results (queue `CAMPAIGN-QUEUE-2026-10-13T0949.md` `## Results`) — all runs clean; final logs created
| case | verdict | final log |
| --- | --- | --- |
| T30403 | UNSUPPORTED | `cli-2026-10-13T0949/30403/30403-unsupported.log` (`af52dad`) |
| T45543 | PARTIAL | `cli-2026-10-13T0949/45543/45543-partial.log` (`af52dad`) |
| T20358 | PASS | `cli-2026-10-13T0949/20358/20358.log` (`af52dad`) |
| T47228 | FAIL | `cli-2026-10-13T0949/47228/47228-fail.log` (`af52dad`) |
| T33234 | UNSUPPORTED (Test Engineer, re-graded from PASS 2026-10-13) | `mdix-2026-10-13T0949/33234/33234-unsupported.log` (`b7d69c0`) |

## Findings
**Measured (2026-10-15):** no reboot of either unit since 2026-10-12. The concurrent Ask-CK validations (queues
`tb470/IE520/CAMPAIGN-QUEUE-2026-10-13T1223.md` and `…T1455.md`, u2–u5) did not cycle u0 or u1.

## OPEN (Test Engineer)
1. **Review point, T47228:** its Results row says the change was "proven at both link ends", but the evidence covers
   only the disable. Should the row be reworded? The final log states only what is sourced.
2. ~~The 2026-10-12 Ask-CK run power-cycled outlets 1 and 7 although its scope excluded the x230 and 4050. Should a
   `Consoles: "all"` Ask-CK run exclude the outlets of units it does not use? (Carried from 10-13 OPEN 6.)~~
   **ANSWERED 2026-10-15 (Test Engineer): yes.** Every run binds a run `.setup` declaring only the units it uses;
   STANDING-ORDERS §6, bench-runner gate 5.
3. Proposed tools from the reviews, none built: `case_tokens --split-at-result`, `ckcon.py --error-regex`,
   `tools/ifdelta.py`, `restconf.py --plan`, `tools/tb fw --wait --summary`, `tools/fwclean.py`. Details:
   [cli REVIEW.md](cli-2026-10-13T0949/REVIEW.md), [mdix REVIEW.md](mdix-2026-10-13T0949/REVIEW.md).
4. The after-hours list, not set up: T44179 (jumbo; a `tools/tb mtu` action to build), T46810 and T28218 (ATMF,
   with the 4050 as master), T31868, and T47119/T47121/T47120-CLI (the 4050 as the reference).

## Next steps
1. Push (`git push origin main`).
2. Decide OPEN 1–3.
3. When wanted: `/test-mode` for the after-hours list (OPEN 4), with constraint "after hours" so reloads are allowed.

## Pointers
- Previous handover (full bench detail and recipes): [SESSION-HANDOVER-2026-10-13.md](SESSION-HANDOVER-2026-10-13.md)
- Bench: [../../bench-setup/bench-state.md](../../bench-setup/bench-state.md)
- Platform facts: [../../platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md)
- Manual-only list: [../../MANUAL-ONLY.md](../../MANUAL-ONLY.md)
