tb470, DUT x230v2-28GS (u0, S/N A10783G262900002) on bootloader 6.2.40, AWPTCM 5700 bootloader suite, 2026-10-06.

| case | title | log | verdict |
| --- | --- | --- | --- |
| 5700.2001 | Boot System CLI rules (11 TestCases) | [5700.2001/5700.2001.log](5700.2001/5700.2001.log) | **PASS**. 11/11 TestCases PASS, framework rc 0 |
| 5700.2002 | default/one-off boot, filenames, foreign release, bootloader version (26 TestCases) | [5700.2002/5700.2002-partial.log](5700.2002/5700.2002-partial.log) | **PARTIAL**. 18 PASS / 7 UNSUPPORTED (SD, no slot); 2002.110 stopped by the script's own NameError (library_5700.py:227) |
| 5700.2003 | stage-1/2 diagnostics menus (15 TestCases) | [5700.2003/5700.2003-partial.log](5700.2003/5700.2003-partial.log) | **PARTIAL**. 11 PASS / 2 UNSUPPORTED (NVS, SD); 2003.11's erase passed on the device but the framework's post-erase boot-config reset failed it and skipped 2003.10 |
| 5700.2004 | U-Boot access; date reset/set (2 TestCases) | [5700.2004/5700.2004.log](5700.2004/5700.2004.log) | **PASS**. 2/2 TestCases PASS, framework rc 0 |
| 5700.2005 | security levels 2/3, passwords, factory restore (8 TestCases) | [5700.2005/5700.2005-fail.log](5700.2005/5700.2005-fail.log) | **FAIL**. 2005.2's erase gate expects `Erasing flash`; the device printed `Erasing nand0:` (the erase and level-1 reset happened); 2005.3–.8 skipped by the framework; 2005.1 PASS |
