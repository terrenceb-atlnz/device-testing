---
name: never-send-cli-help-through-a-cr-driver
description: "Never probe AW+ syntax with `<command> ?` through a driver that appends CR — if `<cr>` is a valid completion the trailing CR EXECUTES the command. It silently enabled ATMF secure mode on a live bench."
metadata:
  node_type: memory
  type: feedback
---

Measured the hard way on tb470, 2026-09-21, during the ATMF case run.

`console.py`'s `send()` does `self.s.write((line + '\r').encode())`. So sending
`"atmf secure-mode ?"` puts `?` on the wire (AW+ prints the help immediately, with no
Enter needed) **and then sends the CR**. AW+ had listed:

```
atmf secure-mode ?
  certificate  Certificate expiry time
  <cr>                      <-- bare command is VALID
```

so the trailing CR executed `atmf secure-mode` in configure mode. That **enabled ATMF
secure mode on the master node only**, which split a live two-node AMF network. It was
caught only because the next command answered `ATMF Secure-mode is already enabled`
when `show atmf` had said `Disabled` minutes earlier.

**Why:** `?` is not a normal character to AW+ — it triggers completion mid-line and
leaves the partial line in the edit buffer. Whatever follows it is applied to that
buffer, and CR means "run it."

**How to apply:**
- To read syntax, send the `?` **without** a trailing CR — write the bytes directly
  (`c.s.write(b"atmf secure-mode ?")`) and read, then send a `Ctrl-C`/`\x03` or a line
  of backspaces to clear the buffer. Never `send()`.
- Safer still on a live bench: read syntax from a **`show` command that cannot change
  state**, or from the docs, and confirm by running the real command deliberately.
- Treat any `?` probe as a **write**, not a read, when the command has a bare-`<cr>` form.

The blast radius is set by what the partial command does on its own. `atmf secure-mode`,
`shutdown`, `reload`, `no ...` are all valid bare commands. See
[[awplus-cli-confirmations-need-enter]] for the related trap (CLI `(y/n)` needs `y\r`,
only the BOOTLOADER menu takes a bare keypress) and [[read-the-whole-function-before-judging]].
