---
name: console-driver-retries-are-lockout-generators
description: "A console driver that retries a login, or types any word at a credential prompt, is an account-lockout generator on AW+ — awlogin.py's tries=5 against a 5-failure threshold locked a partner switch mid-campaign. Supply a password ONCE; at a credential prompt the only safe keystroke is the protocol escape"
metadata:
  node_type: memory
  type: feedback
---

**AW+ locks an account at five failed logins, and every further failure RE-ARMS the five-minute
timer.** So a lock cannot expire while anything is still trying — waiting is useless until every
retry stops. Measured on tb277, 2026-10-20/21.

**Two of our own tools locked accounts in one campaign, by two different mechanisms.** Neither
was a wrong password.

**1. A retry loop whose count equals the threshold.** `tools/awlogin.py`:

```python
def login(c, tries=5, username=None, password=None):   # :30
    for _ in range(tries):                              # :35  up to 5 iterations
        if p == LOGIN:
            c.s.write(user + b"\r"); c.s.write(pw + b"\r")   # :42, :44
            if p3 in (None, BAD): continue              # :46  -> another FULL attempt
```

One call made **five attempts in forty seconds** and locked swi_b. **The driver's retry count
was exactly the platform's lockout threshold**, so it locks any account it ever fails once
against.

**What triggered the first failure was the transport, not the credential.** At 9600 baud a
single fast `write(b"manager\r")` is **truncated on the wire** — the device echoed `ma`, then
`manag`, and went straight to `Password:`. `bench_probe.py` had logged into that same console
with that same password fourteen minutes earlier, which is the control. The loop then re-sent a
**correct** credential four more times into a desynced dialog.

**2. Error recovery that types a word at a credential prompt.** A different driver's recovery
path typed `exit` at a `Password:` prompt — **which the device reads as another password
guess.** It got there because `subprocess.run(input=...)` **REPLACES** stdin rather than
prepending to it, so a forwarded secret swallowed the password being piped behind it and an
**empty** password went out. One bug produced four attempts.

**The rules, both now in the tooling:**

- **An explicitly supplied password is tried ONCE.** Never loop a credential. `bench_probe.py`'s
  `creds_for()` does this: when a per-console `CK_PASSWORD_U<n>` is set it is the **only**
  password tried, deliberately, so a unit with a non-default password costs no failed attempt on
  any other console. Omitting the variable is worse than useless — the fallback tries three
  defaults, so **forgetting an environment variable triples the lockout exposure.**
- **At a login or password prompt the only safe keystroke is the protocol escape.** Any recovery
  that sends text there is silently making authentication attempts.
- **Re-send a truncated-echo username only after proving the echo**, never by restarting the
  credential dialog. At 9600, verify the echo before sending the password.
- **A failed login that you did not intend: stop and report it. Never retry in a loop.**
- ✅ **`tools/awlogin.py` was FIXED on 2026-10-22** (commit `fdaded7`). `login()` now takes
  `cred_attempts=1`: a username+password is **submitted once**, `Login incorrect` returns
  False immediately, and a desync *after* submitting also returns False, because you cannot
  know whether the attempt landed. `tries` now bounds **prompt navigation only** — bare CRs,
  `enable`, an already-open session — none of which costs an authentication attempt. The
  username is also typed per character below 19200 baud and its echo verified before the
  password is sent, so the baud truncation that started all this cannot repeat. Verified on
  hardware: a bad credential now produces **exactly one** `Login incorrect` where the old
  loop produced five.

**How to tell the three cases apart** — the probe's `meta.json` `login:` note is the whole
diagnosis, and getting this wrong cost a session:

| note | means |
| --- | --- |
| `no prompt after login. tail=''` | an **empty** read: the dialog desynced. Usually the baud trap, NOT a credential |
| `tail='...Login incorrect\r\n\r\n<host> login: '` | a genuinely **wrong password** |
| `The account is locked due to N failed logins` | a real **lockout** |

An empty tail was twice read as "the device is refusing our credentials". It was not: pinning
the console with `--baud 9600` logged in first time. See [[cli-surface-is-not-the-device-surface]]
for the sibling lesson about reading a surface and inferring too much from it.

**Recovering a locked account needs an interactive human login** — a successful login resets the
counter, and nothing automated can do it without spending attempts that re-arm the timer.

Related: [[tb277-x960-management-campaign-2026-10-21]], [[testbox-console-access]],
[[bench-probe-one-tool]], [[awplus-cli-confirmations-need-enter]].
