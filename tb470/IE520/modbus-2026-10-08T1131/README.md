tb470, DUT IE520 VCStack stk_a (AT-IE520-28GSX, members 1/3/4, main-calanm), 2026-10-08.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T22650 | modbus - read System information | [22650/22650-fail.log](22650/22650-fail.log) | **FAIL**. 9/10 items equal the CLI at their Mapping-Version-5 addresses; Number of Alarms 0x0049 = 124 vs CLI 93 (the provisioned, absent member 2 is counted) |
| T22651 | S2166.1.10, S2166.1.11, S2166.1.12 - modbus - read Sensor information | [22651/22651.log](22651/22651.log) | **PASS**. Sensor #1/#2 type, reading, units and status registers equal show system environment on members 1, 3 and 4 |
| T22652 | modbus - read alarm information | [22652/22652.log](22652/22652.log) | **PASS**. Alarm #1 type, configuration and status equal the CLI on members 1, 3 and 4 (Mapping Version 5 block 0x3000) |
| T22653 | modbus - read port information | [22653/22653.log](22653/22653.log) | **PASS**. Port current/configured state and byte counters equal the CLI; PoE steps 3-5 UNSUPPORTED |
| T22654 | modbus - write | [22654/22654.log](22654/22654.log) | **PASS**. Alarm-config and port configured-state writes over IPv4, global and link-local IPv6 acknowledged, logged and reflected by the CLI; PoE write UNSUPPORTED |
| T22655 | modbus - dynamic changes | [22655/22655.log](22655/22655.log) | **PASS**. TCP port change, server disable/enable, API port disable/enable and CLI-to-register reflection confirmed |
