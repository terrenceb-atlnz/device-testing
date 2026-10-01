---
name: stack-refused-command-lands-on-backups
description: IE520 stack — a config command the master REFUSES can still land in the backup members' running-config; after stack work check `remote-diff all show running-config`, not the master's view
metadata:
  type: project
---

Observed 2026-10-02 on tb470 (T12067, row 6 of CAMPAIGN-QUEUE-2026-09-29): `flowcontrol receive on` /
`send on` was refused on the stack master (`% Error setting flow control`, DUT log `exfx_port_flowControlSet
… not supported on this product`), yet the backup members' running-config afterwards carried
`flowcontrol both`. The stack members were out of sync and nothing on the master's console showed it.
The probe and a master-side `show running-config` diff both read clean. The next framework TestCase
then failed its own "Stack members have differing running-config … 120 seconds after configure" check,
and the framework's power cycle cleared it. A possible product defect (O-1 in
`IE520/epsr-l2-2026-09-29/12067-unsupported.log`); not yet raised.

**Why:** a refused command looks like "nothing changed", so the after-check skips the members, and the
leftover becomes the next case's variable (STANDING-ORDERS §1, "keep configs tidy").

**How to apply:** after any config work on a stack, especially a refused command, run
`remote-diff all show running-config` (or read each member) before declaring the configs IDENTICAL.
Related: [[bench-probe-one-tool]], [[bench-scripts-stop-on-cli-errors]].
