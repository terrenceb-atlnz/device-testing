tb470, DUT x230v2-28GS (u0, S/N A10783G262900002) on bootloader 6.2.40, AWPTCM 5700 bootloader suite, 2026-10-06 to 2026-10-08.

| case | title | log | verdict |
| --- | --- | --- | --- |
| 5700.2001 | Boot System CLI rules (11 TestCases) | [5700.2001/5700.2001.log](5700.2001/5700.2001.log) | **PASS**. 11/11 TestCases PASS, framework rc 0 |
| 5700.2002 | default/one-off boot, filenames, foreign release, bootloader version (26 TestCases) | [5700.2002/5700.2002.log](5700.2002/5700.2002.log) | **PASS**. 19 PASS / 7 UNSUPPORTED (SD, no slot); 2002.110 one-off boots of main, backup and TFTP copy each booted and reverted, 13/13 |
| 5700.2003 | stage-1/2 diagnostics menus (15 TestCases) | [5700.2003/5700.2003.log](5700.2003/5700.2003.log) | **PASS**. 13 PASS / 2 UNSUPPORTED (NVS, SD); 2003.11 erase + reboot PASS on the device (framework post-erase reset = harness, c1e7679); 2003.10 Filesystem FLASH test 2/2 |
| 5700.2004 | U-Boot access; date reset/set (2 TestCases) | [5700.2004/5700.2004.log](5700.2004/5700.2004.log) | **PASS**. 2/2 TestCases PASS, framework rc 0 |
| 5700.2005 | security levels 2/3, passwords, factory restore (8 TestCases) | [5700.2005/5700.2005.log](5700.2005/5700.2005.log) | **PASS**. 8/8: levels 2/3 set and enforced, length limits, all character classes, `show boot` level, prompt timeout, start-shell refused at level 3; 2005.2 PASS per the Test Engineer (`Erasing nand0:` wording) |
