# Campaign queue — tb470, x230v2-28GS as the DUT: re-run of the cases previously UNSUPPORTED, after a FULL licence was installed (AR4050S = partner), from 2026-10-27 08:55 NZDT

The ask, Test Engineer 2026-10-27 ~08:45 (after `/orient-dt`, bench tb470): *"Ive installed a Full license on the x230v2 now,
we need to re-run any test that was previously listed as UNSUPPORTED, including 30403."* Scope agreed 08:5x (AskUserQuestion):
T30403, T31863, T31866 (always), plus **T28218 with the x230 as the AMF MASTER**; T33234 (MDI/MDI-X) left out (a hardware
ruling, not a licence one). Then `/test-mode T30403 T31863 T31866 T28218`.

Titles (ck.db `zephyr_cases`): AWPTCM-T30403 Check traffic is fowarded with static mroutes (IPv4); AWPTCM-T31863
FactoryRunup-BIST (if supported); AWPTCM-T31866 FactoryRunup-PRBS (if supported); AWPTCM-T28218 ATMF provisioning.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-27 08:55 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (u0 = AR4050S swi_e; u1 = x230v2-28GS swi_f, the DUT; both 115200) — "Yes, as stated"
PDU: "10.36.150.14 u0=3 u1=4" — "Yes, as stated"
Constraints: "Reloads allowed (Recommended)" (option text: "The x230 and the 4050 may reload as the cases need, during office hours.") + "None beyond reloads allowed". Sentinel stand-down: "When the run ends". Host: "Stay in VS Code (Recommended)" (risk accepted).

At 08:46 Terrence opened `minicom --wrap -D /dev/u1 -c off` (PID 309802) on tb470 (installing the licence). **u1 is not opened by
this campaign until that holder is gone** (precheck CLEAR); never displace it.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies (§7 scapy for traffic, §8 health reads twice per case). Startup config: nothing written unless a case requires it.
- **Only u0 and u1 are touched.**
- **First read of the campaign, before any case:** on u1 `show license`, `show license brief`, `show feature` (or the build's
  equivalents): what the FULL licence enabled. Record it in the triage. Whether a licensed feature needs a reload to take
  effect is a measurement, not an assumption (reloads are allowed).
- **Prior verdicts are method only, never the verdict.** A case that is still refused gets UNSUPPORTED again, with the
  licence read as evidence; one that now works is graded on its steps.
  - T30403 UNSUPPORTED 2026-10-13 (`cli-2026-10-13T0949/30403/30403-unsupported.log`): `ip multicast-routing`, `ip mroute`,
    `ip pim`, `show ip mroute` absent from the parser; `show license` had no multicast/PIM feature.
  - T31863 UNSUPPORTED 2026-10-09 (`platform-2026-10-09T0845/31863/`): `platform bist instance …` → `% BIST test not supported.`
  - T31866 UNSUPPORTED 2026-10-09 (`platform-2026-10-09T0845/31866/`): `platform prbs …` → `% PRBS not supported on this platform`.
  - T28218 with the x230 as master: triaged UNSUPPORTED 2026-10-09 (x230 lacked AMF-MASTER), never run. T28218 PASSED
    2026-10-21 with the **4050** as master (`atmf-2026-10-21T0835/`, queue `CAMPAIGN-QUEUE-2026-10-21T0835.md`: the
    exact steps, setup and restore). This run is the x230-as-master limb.
- Case texts: Ask-CK `ck.db` table `zephyr_cases`, key `AWPTCM-T<n>`, read-only (`tools/ckcase.py`; on the dev host the db is
  `/media/terrenceb/mnt/testbox_home/claude/Test-cases/ask-ck/db/ck.db`).
- MANUAL-ONLY.md (repo root) is read at triage.
- Platform traps: [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md) (reload ≈ 165 s; a reload drops running-only
  config incl. `lldp run`; `show reboot history` is unsorted). AMF memories: `atmf-recovery-residue-and-reboots`,
  `ie520-master-ignores-remote-backup-server`, `x230v2-atmf-campaign-2026-10-21`.

## Bench at queue creation (orient probe `2026-10-26T190212Z`, 08:02, u0/u1, **MISMATCH**; reads 08:02–08:06)

- Probe MISMATCH = the 2026-10-22 recable only (`[portlink] swi_e-swi_f` adds port1.0.3-port1.0.3; `tb-swi_f eth2-port1.0.10`
  absent from the template). `apply` not done (the Test Engineer's). No Advisories.
- u0 AR4050S swi_e S/N A10401G214000005, awplus_main-20261008-57, bootloader 5.2.8, boots `flash:/AR4050S-awplus_main-20261008-57.rel (file exists)`
  + `flash:/tb470-bench.cfg (file exists)`; flash 3.4 GB free, USB 28.6 GB free; up 11 d; newest reboot 2026-10-15.
- u1 x230v2-28GS swi_f S/N A10783G262900002, awplus_main-20261019-75, bootloader 6.2.40, boots `flash:/x230v2_28GS-awplus_main-20261019-75.rel (file exists)`
  + `flash:/tb470-bench.cfg (file exists)`; flash 60.6 MB free; **no USB stick** (`usb:` Avail N); up 6 d 20 h; newest reboot 2026-10-20.
  Admin down AND saved: port1.0.7, **port1.0.16, port1.0.26** (the self-loop legs; leave them shut — 1.0.15<->1.0.16 copper,
  1.0.25<->1.0.26 SX, all vlan1 with STP off would storm). These read before the licence install; re-read at triage.
- Links (probe): tb eth1 -> x230 port1.0.2; tb eth2 -> x230 port1.0.10; tb eth3 -> 4050 port1.0.1; 4050 port1.0.2 <-> x230
  port1.0.1 (x230 side `switchport atmf-link`); 4050 port1.0.3 (vlan10, sa1) <-> x230 port1.0.3 (vlan103).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | platform: T31863 (BIST), T31866 (PRBS) | tb470/x230v2-28GS/platform-2026-10-27T0855/ | QUEUED | u1 CLI; may need a reload if the licence only takes at boot |
| 2 | mcast: T30403 (static mroutes, IPv4) | tb470/x230v2-28GS/mcast-2026-10-27T0855/ | QUEUED | needs multicast routing on the x230; traffic by scapy from tb470 (§7) with a control flow |
| 3 | atmf: T28218 (ATMF provisioning, **x230 as master**) | tb470/x230v2-28GS/atmf-2026-10-27T0855/ | QUEUED | only if the licence carries AMF-MASTER; the x230 has no USB stick, so backup media is a triage question |

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |

## Issues

