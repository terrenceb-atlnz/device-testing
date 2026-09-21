---
name: ie520-mac-auth-username-format
description: "IE520 MAC authentication sends the MAC to RADIUS as 00-f0-4d-00-77-17 — lowercase, HYPHEN separated. A user named 00f04d007717 never matches, and this build has no auth-mac username-format command to change it."
metadata:
  node_type: memory
  type: project
---

Measured on tb470, 2026-09-22, IE520 stack running `awplus_main-20260913-1734`.

With `auth-mac enable` on a port, the DUT authenticates the source MAC against
RADIUS using the MAC as **both username and password**, formatted as:

```
00-f0-4d-00-77-17        <- lowercase hex, hyphen separated
```

A RADIUS user named `00f04d007717` (the common no-separator form) **does not
match**; the supplicant fails with `fail:T` and the port stays Unauthorized —
which looks exactly like the feature being broken. `show auth supplicant` gives
it away: `Supplicant name:` shows the format the DUT actually sent.

There is **no `auth-mac username-format` command** on this build
(`% Unrecognized command`), so the RADIUS user must be created in the
hyphenated form. When in doubt, create the user in several formats at once —
on the DUT's own local RADIUS server this is free:
`radius-server local` / `user 00-f0-4d-00-77-17 password 00-f0-4d-00-77-17`.

**Second trap in the same feature:** default `auth host-mode` is
**single-host**, so one FAILED supplicant occupies the port and a subsequent
GOOD MAC never gets to authenticate at all. Set
`auth host-mode multi-supplicant` when testing both a good and a bad MAC on one
port, or clear the failed supplicant between attempts.

Using the DUT's **local** RADIUS server avoids editing anything on the testbox.
For a remote server, tb470 runs FreeRADIUS and the IE520 is ALREADY an
authorised client via an Ansible-managed `client 10.38.0.0/16 { secret = secret }`
block, with users `test_user/test_pass` and `user15` — also no testbox writes.
