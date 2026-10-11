tb470, DUT x230v2-28GS swi_f (AT-x230-28GS V2) on u0, awplus_main-20261008-57, 2026-10-09.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T47114 | crypto secure mode: Confirm DUT can boot into secure mode | [47114/47114.log](47114/47114.log) | **PASS**. `crypto secure-mode` + write + reload (265 s): the boot created the secure-mode host key and logged "crypto secure-mode enabled", `show secure-mode` = enabled, SSH algorithm sets narrowed, no exception; the boot also logged a release-verification warning (not part of the case) |
| T47115 | crypto secure mode: Set password requirements for users Confirm this applies to all users | [47115/47115.log](47115/47115.log) | **PASS**. In secure mode with minimum-length 12 / minimum-categories 3, short and 1-category passwords were rejected for new privilege-1 and privilege-15 users and for existing users including manager (hashes unchanged); compliant passwords accepted |
| T47120 | Confim telnet cannot be enabled CLI/GUI | — | **NOT TESTED**. CLI half runnable in secure mode, but the GUI half needs a person at a browser (x230 vlan1 IP via eth1); not in the 18:00 scope |
| T47119 | confirm secure mode algorithm sets for SSH match other devices that support secure mode | — | **NOT TESTED**. Needs a reference device named by the Test Engineer (the AR4050S supports secure mode = 2 more 4050 reloads); not in the 18:00 scope |
| T47121 | confirm the TLS algorithms match other devices with crypto secure-mode | — | **NOT TESTED**. Needs a reference device named by the Test Engineer (the AR4050S supports secure mode = 2 more 4050 reloads); not in the 18:00 scope |
