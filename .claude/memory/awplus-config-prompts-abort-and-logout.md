---
name: awplus-config-prompts-abort-and-logout
description: "Some AW+ config commands PROMPT (y/n) — `mls qos enable`, `no mls qos`, `atmf secure-mode enable-all`. A driver that sends the next config line instead of `y` gets '% Command aborted' AND can log the console out, wedging the run."
metadata:
  node_type: memory
  type: feedback
---

Measured on tb470, 2026-09-22, during the IE520 QoS group.

```
IE520-stk(config)# mls qos enable
Traffic will stop while configuration is applied. Continue? (y/n):
```

A `conf([...])` helper that just sends the next line fed it `end`, which
answered the prompt with garbage. Two things then went wrong at once:

1. `% Command aborted.` — QoS never enabled, so every later `policy-map` /
   `class-map` failed with `% QoS is not enabled globally!`
2. the console fell out of config mode and **logged out**, so every subsequent
   command was typed at a `login:` prompt and returned "login: timed out". The
   run produced 20 minutes of nothing and had to be killed and the console
   manually recovered.

**How to apply:**
- Send config lines through a helper that checks each reply for `(y/n)` and
  answers `y\r` before continuing ([[awplus-cli-confirmations-need-enter]]).
- Make the helper **abort on the first `%` error** rather than ploughing on. A
  bad line leaves you in the wrong mode, and the blind `exit`/`end` chain that
  follows is what actually logs the console out.
- Known prompting commands so far: `mls qos enable`, `no mls qos`,
  `atmf secure-mode enable-all`, `no atmf secure-mode enable-all`,
  `reboot stack-member N`.

**QoS specifics worth keeping:** enable is `mls qos enable`, disable is
`no mls qos` — `mls qos disable` and `no mls qos enable` are both
`% Invalid input`. Nothing in the `policy-map`/`class-map` family parses at all
until QoS is enabled globally, and the error names the real cause.
