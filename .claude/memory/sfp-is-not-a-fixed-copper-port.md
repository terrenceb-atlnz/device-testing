---
name: sfp-is-not-a-fixed-copper-port
description: Terrence's ruling: an SFP cage is NOT a fixed copper port for MDI/MDI-X, whatever module it holds; MDI/MDI-X cases (T33234) on an all-SFP DUT are UNSUPPORTED; a copper SFP keeps its copper identity for speed/duplex/media
metadata:
  type: feedback
---

**The ruling.** An SFP (Small Form-factor Pluggable) is a removable transceiver. The switchport is the cage, so a copper SFP is **not a fixed copper port**.
- For MDI/MDI-X and polarity, a cage counts as a fibre port, whatever module it holds.
- A DUT with no fixed RJ45 switchport therefore makes the MDI/MDI-X cases (T33234 "Port - Auto MDI/MDI-X") **UNSUPPORTED**. Examples: the IE520-28GSX and the x230v2-28GS.
- **Scope: MDI/MDI-X only.** In every other test (speed, duplex, media) a copper SFP keeps its copper identity.

**Why:** Terrence ruled this on 2026-09-29 (IE520 campaign, queue I-5, `IE520/port-2026-09-29/33234-unsupported.log`), citing the
AW+ `polarity` usage note: "applies to copper 10/100/1000BASE-T switch ports; does not apply to fiber ports". The Test-cases
script changed to match (`d9a08dd`: gate on `has_fixed_copper_port`, pluggable cases stripped).
- On 2026-10-12/13 the ruling was NOT in memory. The sentinel re-triaged the x230's T33234 as "runnable via the copper-SFP
  scripts 5000.0003/0004", and the run graded it PASS.
- Terrence then: *"what does SFP stand for … So, by definition, thats *no* a fixed copper port, right"*. It was re-graded UNSUPPORTED.
- That run's measurements stay as supporting evidence: copper SFPs refuse forced polarity (`% Polarity set failed`, "Polarity mode
  not supported on this interface"), and auto MDI-X through the module links.

**How to apply:** at triage, the MDI/MDI-X case on a DUT with no fixed copper switchport is UNSUPPORTED before anything runs.
- Never propose the legacy copper-SFP polarity scripts (5000.0003/0004, the 5703 copper-SFP TestCases) as a way to run it.
- Read a platform's prior verdicts and rulings (`platforms/<FAMILY>.md`, earlier logs of the same case id) before re-triaging a case.
- Related: [[awplus-speed-duplex-constraint]], [[ie520-first-copper-port-is-x-0-2]].
