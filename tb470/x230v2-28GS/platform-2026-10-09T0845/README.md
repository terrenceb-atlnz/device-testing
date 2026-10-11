tb470, DUT x230v2-28GS swi_f (AT-x230-28GS V2, standalone, console u0, awplus_main-20261008-57), 2026-10-09.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T47226 | check for sh version | [47226/47226.log](47226/47226.log) | **PASS**. show version answers in full (AlliedWare Plus 0.0.0, build 10/08/26 00:10:09); its Build name line reads x220-awplus_main-20261008-57.rel, noted for re-grade |
| T47227 | check for sh license | [47227/47227.log](47227/47227.log) | **PASS**. show license lists Base License (Full) and ACCESS (Full) with issue dates and features |
| T47215 | sh sys environment | [47215/47215.log](47215/47215.log) | **PASS**. Overall Status Normal; fan 3691 rpm and all 8 voltage/temperature sensors Ok within limits |
| T31852 | FactoryRunUp-FeatureLicenceCheck | [31852/31852.log](31852/31852.log) | **PASS**. sh lic: Base License and ACCESS both Full, no error |
| T31853 | FactoryRunUp-FileSystemCheck | [31853/31853.log](31853/31853.log) | **PASS**. dir all lists .configs/ ./ .home/ .rnd .certs/ log/ ../; gui-userdata/ absent (no GUI file on this used unit), noted for re-grade |
| T31855 | FactoryRunUp-MACaddress | [31855/31855.log](31855/31855.log) | **PASS**. system MAC = vlan1 MAC = 00c2.8f3f.0f5d, a valid unicast; step 3 UNSUPPORTED (no eth0 on the x230v2) |
| T31856 | FactoryRunUp-NoExceptionsGenerated | [31856/31856.log](31856/31856.log) | **PASS**. show exception log: None |
| T31861 | FactoryRunUp-ShowSystem | [31861/31861.log](31861/31861.log) | **PASS**. show system carries all 15 listed fields with reasonable values |
| T31858 | FactoryRunUp-SettingClock | [31858/31858.log](31858/31858.log) | **PASS**. clock set 05:05:52 9 Oct 2026 accepted; after a 163 s reload the clock read 05:09:01 at tb470 18:09:02 (kept within 1 s) |
| T31863 | FactoryRunup-BIST (if supported) | [31863/31863-unsupported.log](31863/31863-unsupported.log) | **UNSUPPORTED**. `platform bist instance all` / `0` / `all full` each answer "% BIST test not supported."; show platform bist: Instance 0 Not run |
| T31866 | FactoryRunup-PRBS (if supported) | [31866/31866-unsupported.log](31866/31866-unsupported.log) | **UNSUPPORTED**. `platform prbs all-fabric duration 20` (the case's "all"), `internal-fabric duration 20` and `all-fabric` each answer "% PRBS not supported on this platform"; no results file |
| T47214 | Fan Alarm: verify alarm is trigger when fan speed is interrupted | — | **NOT TESTED**. needs a person at the bench to interrupt the fan (magnet on the fan); not in the 18:00 scope |
| T45543 | TPM Support | — | **NOT TESTED**. Test Engineer's: steps 1-2 runnable (`show system tpm` answers `TPM is instantiated`, expected `TPM is OK`), step 3 needs an idevid account and x230 internet via eth1; not in the 18:00 scope |
| T31868 | FactoryRunUp-Autoboot | — | **NOT TESTED**. 3+ reloads with a 2nd .rel on USB (x230-2.rel on the 28.8G stick; no SD slot); kept out of the 18:00 scope by the Test Engineer |
| T31854 | FactoryRunUp-LEDtesting | — | **NOT TESTED**. needs a person to watch the LEDs; precondition no SFP and no cable, but the x230 carries bench SFPs and cables |
| T31859 | FactoryRunUp-SystemEnvCheck | — | **NOT TESTED**. CLI half runnable, but the fault-LED check needs a person at the bench; not in the 18:00 scope |
