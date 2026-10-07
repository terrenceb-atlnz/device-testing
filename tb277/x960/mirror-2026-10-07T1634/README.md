# mirror-2026-10-07T1634 — tb277, AT-x960-56YSQ (swi_c, S/N A2WQS7004), 2026-10-07

| case | title | log | verdict |
| --- | --- | --- | --- |
| T44967 | CLI show mirror interface direction set to transmit | [T44967/44967.log](T44967/44967.log) | **PASS**. A transmit-direction mirror was accepted, stored and reported correctly (Enabled, direction transmit, destination port1.0.11, monitored port1.0.10). Configuration and reporting only — both ports are empty SFP cages, so no frames were mirrored. |
| T44968 | CLI show mirror interface direction set to receive | [T44968/44968.log](T44968/44968.log) | **PASS**. As above with direction `receive`. |
| T44969 | CLI show mirror interface direction set to both | [T44969/44969.log](T44969/44969.log) | **PASS**. As above with direction `both`. |
| T44973 | CLI Remove mirror interface | [T44973/44973.log](T44973/44973.log) | **PASS**. A configured mirror was removed with `no mirror interface port1.0.10`; `show mirror` empty afterwards and no residue in running-config. The drafted bare `no mirror interface` is invalid on this platform (`% Incomplete command.`). |
| T44974 | Mirror set to interface none | [T44974/44974.log](T44974/44974.log) | **PASS**. `mirror interface none` exists, is accepted and is reported — but it does **not** deactivate the mirror; it adds an independent ACL-sourced destination-only mirror (`Monitored Port Name: none (via ACL)`). Verdict turns on a judgement call: see the log. |
