tb470, DUT x230v2-28GS (swi_f, u1), fibre self-loop port1.0.25 <-> port1.0.26, 2026-10-22 13:45-14:22 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T47209 | Fibre pluggable with supported speeds | [47209/47209-fail.log](47209/47209-fail.log) | **FAIL**. The AT-SPSX (1000BASE-SX) accepts `speed 100` and `speed auto 100`, reads "connected" at 100 and passes 0 of 100 frames. Speeds 10, 2500, 10000 and half duplex are refused. Auto, 1000, and 1000 full on both ends pass 100 of 100. Health clean |
| T44179 | Jumbo Frames | — | **NOT TESTED**. `platform jumboframe` needs a write and 2 x230 reloads, which the session's "no reboots" constraint excluded. It also needs MTU 9216 on tb470 eth1 and eth2 (a root change for the Test Engineer). Test Engineer 2026-10-22: proceed with the other 3 cases only |
