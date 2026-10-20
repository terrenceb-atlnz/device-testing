# atmf-2026-10-21T0835 — tb470, DUT x230v2-28GS (swi_f, S/N A10783G262900002) with the AR4050S as AMF master, 2026-10-21

| case | title | log | verdict |
| --- | --- | --- | --- |
| T46810 | ATMF Backup | [46810/46810.log](46810/46810.log) | **PASS**. Under the assumed reading (the case has no steps): the 4050 master backed up the x230 member to its USB media in 32 s, status Good, the .rel and tb470-bench.cfg on the media at their flash sizes |
| T28218 | ATMF provisioning | [28218/28218.log](28218/28218.log) | **PASS**. All 5 steps on the 4050 master: future_node created on usb:, the x230's .rel and tb470-bench.cfg copied from its backup and set as boot system and config, `show atmf provision nodes` matches the expected block field for field |
