Testbox tb277, DUT AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261012-24`), 2026-10-20.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T44308 | (296) Management - RMON | [T44308/T44308.log](T44308/T44308.log) | **PASS**. Statistics, history, event and alarm all measured against counted traffic; four SNMPv2c traps caught and decoded; a control alarm stayed silent then fired at exactly 50. |
| T33413 | (280) Management_Trap - Temperature | [T33413/T33413.log](T33413/T33413.log) | **PASS**. The over-temperature trap was produced and caught on the wire, three assert/clear cycles against a silent baseline. One finding: the trap is still sent after its trap group is removed. |
| T44301 | (281) Management_Trap - Per-port link trap | [T44301/T44301.log](T44301/T44301.log) | **PASS**. linkDown and linkUp were emitted for the armed port only; a sibling port flapped in the same window produced no trap. |
| T44309 | (297) Management_SFlow - SFlow Agent | [T44309/T44309.log](T44309/T44309.log) | **PASS**. 2000 frames at 1-in-50 gave exactly 40 flow samples, each decoding to the frame sent. Two intermittent defects are recorded in the log and in its CAVEAT. |
