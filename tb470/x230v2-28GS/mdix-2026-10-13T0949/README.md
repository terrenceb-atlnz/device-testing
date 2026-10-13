tb470, DUT x230v2-28GS swi_f on u0 (AT-x230-28GS V2, standalone, awplus_main-20261008-57; link partner AR4050S-5G swi_e on u1), 2026-10-13.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33234 | Port - Auto MDI/MDI-X | [33234/33234-unsupported.log](33234/33234-unsupported.log) | **UNSUPPORTED**. No fixed copper (RJ45) switchport on the x230v2-28GS: its ports are SFP cages and a copper SFP is a pluggable transceiver, not a fixed copper port. Forced `polarity mdi\|mdix` is refused on both copper SFPs ("Polarity mode not supported on this interface"); auto MDI-X and speed/duplex through the modules linked (7 framework TestCases PASS), which does not make the case PASS |
