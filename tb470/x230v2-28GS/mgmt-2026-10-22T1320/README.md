tb470, DUT x230v2-28GS (swi_f, u1) with an AR4050S link partner (swi_e, u0, read only), 2026-10-22 14:24-14:40 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T47228 | API-enable/disable  interafce, add/delete vlans | [47228/47228-fail.log](47228/47228-fail.log) | **FAIL**. RESTCONF PUT disables and enables port1.0.3 in both the OpenConfig and IETF models, and the CLI, log and partner agree. No RESTCONF request can add a VLAN (403, 404, or a 204 that creates nothing) or delete one (403 for a privilege 15 user). PATCH answers 204 and does not change the port. Health clean |
| T45543 | TPM Support | [45543/45543-partial.log](45543/45543-partial.log) | **PARTIAL**. Steps 1-2 PASS: tpm2-abrmd and tpm_server are running and connected, and `show system tpm` reads "TPM is instantiated". Step 3 (idevid registration) NOT RUN: it needs an idevid server account and internet access for the DUT. Health clean |
