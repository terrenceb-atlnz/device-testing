tb470, DUT x230v2-28GS swi_f on u0 (AT-x230-28GS V2, awplus_main-20261008-57; AR4050S swi_e on u1 as T47228's link partner), 2026-10-13.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T30403 | Check traffic is fowarded with static mroutes (IPv4) | [30403/30403-unsupported.log](30403/30403-unsupported.log) | **UNSUPPORTED**. No IPv4 multicast routing on the x230v2-28GS: `ip mroute`, `ip multicast-routing`, `ip pim` and `show ip mroute` are absent from the parser (% Invalid input), and no licence offers them |
| T45543 | TPM Support | [45543/45543-partial.log](45543/45543-partial.log) | **PARTIAL**. Steps 1-2 PASS (`show platform full-debug \| grep tpm` lists tpm2-abrmd and tpm_server; `show system tpm` "TPM is instantiated" = OK by ruling); step 3 idevid registration NOT RUN (manual-only: needs an idevid account and internet access for the DUT) |
| T20358 | Loopback between two ports on same switch | [20358/20358.log](20358/20358.log) | **PASS**. With RSTP on and the port1.0.6<->1.0.7 lead closed, port1.0.7 goes Backup/Discarding in 5 s (receives its own bridge's RSTP BPDUs) and transmits 0 of 8356 broadcast frames from tb470 eth3 |
| T47228 | API-enable/disable interafce, add/delete vlans | [47228/47228-fail.log](47228/47228-fail.log) | **FAIL**. RESTCONF cannot add or delete VLANs (a create answers 204 and creates nothing; a delete of a real VLAN is 403 access-denied) and PATCH of the `enabled` leaf answers 204 with no effect; interface disable/enable by PUT on the leaf works |
