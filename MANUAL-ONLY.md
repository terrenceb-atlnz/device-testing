# MANUAL-ONLY test cases — the tracked list

**What this is.** Test cases (or single steps) that an agent cannot complete on its own, because a
**person** has to do or see something: hold a magnet on a fan, watch an LED, click through a
browser, supply an account or credentials, or reach the internet. The Test Engineer asked for them
to be tracked so they are never re-triaged from scratch (Terrence, 2026-10-13: *"Mark this as a
MANUAL-ONLY test case … We will encounter many, and i want them clearly tracked (so we dont have
this issue down the road)"*).

**How it is used.**
- `/test-mode` triage reads this file. A listed case (or step) is reported as **MANUAL-ONLY** with
  the reason below, and is never scheduled into an unattended or after-hours run.
- The agent still runs the automatable part when the row says there is one. The case's verdict then
  follows logged-output.md §1: a case whose manual part did not run is PARTIAL, with the manual part
  under `NOT RUN:`, or NOT TESTED if nothing ran.
- A manual case runs when the Test Engineer books a person at the bench. The agent drives the CLI
  and the person reports what they saw, and the log quotes them.
- **Add a row** whenever triage finds a new one, with the date and who decided. **Remove a row**
  only on the Test Engineer's word, for example when a tool makes the step automatable.

The list is per case id, which is the same on every platform. Where the reason is platform-specific,
the row says so.

| case | title | manual part | why a person is needed | automatable part | added |
| --- | --- | --- | --- | --- | --- |
| T45543 | TPM Support | step 3 | needs an idevid account and internet access for the DUT | steps 1–2 (`show system tpm`; "TPM is instantiated" = "TPM is OK", Terrence 2026-10-13) | 2026-10-13, Terrence |
| T47214 | Fan Alarm: verify alarm is trigger when fan speed is interrupted | whole case | someone interrupts the fan (a magnet on it) while the alarm is watched | reading the alarm and `show system environment` once the fan is interrupted | 2026-10-13, x230 triage 2026-10-09 |
| T31854 | FactoryRunUp-LEDtesting | whole case | someone watches the LEDs; precondition is no SFP and no cable in the DUT | none | 2026-10-13, x230 triage 2026-10-09 |
| T31859 | FactoryRunUp-SystemEnvCheck | fault-LED check | someone looks at the fault LED | the CLI half | 2026-10-13, x230 triage 2026-10-09 |
| T47120 | Confim telnet cannot be enabled CLI/GUI | GUI half | someone in a browser on the DUT's GUI | the CLI half (in secure mode) | 2026-10-13, x230 triage 2026-10-09 |
