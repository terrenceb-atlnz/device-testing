---
name: ssh-path-has-no-sbin
description: "`ssh tbNNN 'command -v foo'` returns nothing for binaries in /usr/sbin or /sbin — a non-login ssh shell's PATH omits both. Never conclude a tool is absent from that; check absolute paths or dpkg."
metadata:
  node_type: memory
  type: feedback
---

Measured on tb470, 2026-09-22, and it nearly cost two test cases.

```
ssh tb470 'echo $PATH'
/usr/local/bin:/usr/bin:/bin:/usr/games        <-- no /usr/sbin, no /sbin
```

So `ssh tb470 'command -v wpa_supplicant'` printed nothing while
`/usr/sbin/wpa_supplicant` and `/sbin/wpa_supplicant` both existed
(wpa_supplicant v2.10, wired driver present). I had already written
"no wpa_supplicant" into a plan and was about to grade the 802.1X cases
UNMEASURED on the strength of it. A peer session caught it.

**How to apply — to decide a tool is ABSENT, use at least one of:**
- absolute paths: `for p in /usr/sbin/X /sbin/X /usr/bin/X; do [ -x "$p" ] && echo "$p"; done`
- the package database: `dpkg -l | grep -i X`
- a listening socket, if it is a daemon: `ss -lntu | grep <port>`

A bare `command -v` / `which` over ssh is evidence of PRESENCE only, never of
absence. The same applies to anything else that reads PATH — `type`, `hash`,
and bare invocation in a script.

Worth knowing which way each answer went on tb470: wpa_supplicant and wpa_cli
are PRESENT in /usr/sbin (false negative); TACACS+ is genuinely ABSENT,
confirmed three ways (no binary at any absolute path, nothing in dpkg, no
TCP/49 listener).

Related: [[testbox-console-access]], [[rejected-tool-calls-keep-running-remotely]].
