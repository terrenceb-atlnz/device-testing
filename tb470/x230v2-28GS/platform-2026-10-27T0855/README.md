tb470, DUT x230v2-28GS (swi_f, u1), standalone with the FULL licence, 2026-10-27 09:23-09:48 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T31863 | FactoryRunup-BIST (if supported) | [31863/31863-unsupported.log](31863/31863-unsupported.log) | **UNSUPPORTED**. `platform bist instance all`, `instance 0` and `instance all full` each answer "% BIST test not supported." `show platform bist` stays "Not run". Each `show platform bist` writes about 96 EXFX debug lines to the log. Health clean |
| T31866 | FactoryRunup-PRBS (if supported) | [31866/31866-unsupported.log](31866/31866-unsupported.log) | **UNSUPPORTED**. Every `platform prbs` form, including the case's own `all duration 20`, answers "% PRBS not supported on this platform". No PRBS test ran. Health clean |
