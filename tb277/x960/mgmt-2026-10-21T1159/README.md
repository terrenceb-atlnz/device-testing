Testbox tb277, DUT AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261019-27`), 2026-10-21.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33386 | (237) EnhancedOperationManagement - Management ACL | [T33386/T33386.log](T33386/T33386.log) | **PASS**. Both halves of TPS 6.1.1 proven in the dataplane — the specified host admitted, the non-specified host silently dropped with an ICMP control answered in the same leg — and the filter still discriminates after a restart. |
| T47192 | (243) Config_File - A dynamic configuration while operating (Change, Delete) | [T47192/T47192.log](T47192/T47192.log) | **PASS**. All three operations TPS line 894 names — addition, change and deletion — take effect dynamically across two unrelated subsystems, nine operations with zero restarts, and a change survives a cold boot. |
| T33387 | (238) EnhancedOperationManagement - Management Stacking | [T33387/T33387-unsupported.log](T33387/T33387-unsupported.log) | **UNSUPPORTED**. X960 TPS row 236 states the platform does not implement it — *"not necessary as these units support VCS"* — and the DUT agrees. The case changed no device state. |
| T33384 | (235) EnhancedOperationManagement - Auto boot from external media | — | **NOT TESTED**. Needs a person to insert a FAT32 USB stick carrying `autoboot.txt` plus the release and config it names. Deferred by the Test Engineer; listed in MANUAL-ONLY.md. |
| T33388 | (239) EnhancedOperationManagement - Hardware Watchdog | — | **NOT TESTED**. No user-facing watchdog CLI exists and TPS 5.3.6 states that is deliberate. Dropped by the Test Engineer on 2026-10-21. |
| T33389 | (240) EnhancedOperationManagement - Software Watchdog | — | **NOT TESTED**. Same reason as T33388. Dropped by the Test Engineer on 2026-10-21. |
