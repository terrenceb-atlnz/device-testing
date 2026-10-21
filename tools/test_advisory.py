#!/usr/bin/env python3
"""test_advisory.py -- regression test for console.ADVISORY / console.is_advisory().

Run it anywhere with python3 (no bench, no console, no arguments):

    python3 tools/test_advisory.py        # prints a table; exit 0 = pass, 1 = fail

WHY THIS EXISTS. The drivers (cfg.py, qmark.py) stop a batch at the first "% " line, because on
AW+ that normally means the command was refused. A few "% " lines are ADVISORIES printed
alongside a command that SUCCEEDED, and treating those as errors aborts the batch and silently
skips every command after it -- which has now cost two runs on tb277 (2026-10-08 cfg.py during
T44992, 2026-10-09 qmark.py during T44973).

The hazard this file guards is the opposite one, and it is worse: **two of the strings differ by
a single word and mean opposite things.**

    ADVISORY   % This access-list is attached to an interface. The modified configuration
               will be applied to the interface automatically after exiting ...
               -> named hardware ACL sub-mode. The edit SUCCEEDS, applied on exit/end.

    REJECTION  % This access-list is currently attached to an interface so cannot be edited.
               -> numbered hardware ACL. The edit is REFUSED and does not happen.

If the advisory pattern is ever loosened to "access-list ... attached to an interface", the
rejection matches too, every driver silently swallows a refused edit, and the run grades a
configuration that was never applied. Keep the patterns tight and keep this test passing.

Add a case here whenever a new advisory is allow-listed, together with the nearest rejection you
can find, so the pair is pinned.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console

# (line, is_advisory, what it is, where it was seen)
CASES = [
    ("% This access-list is attached to an interface. The modified configuration will be applied"
     " to the interface automatically after exiting this configuration mode  by entering \"exit\""
     " or \"end\" command.",
     True,  "ADVISORY  named hw ACL sub-mode, edit succeeds", "tb277 T44992 2026-10-08"),

    ("% This access-list is currently attached to an interface so cannot be edited.",
     False, "REJECTION numbered hw ACL, edit refused",        "tb277 T44987 2026-10-09"),

    ("% port1.0.10 is currently configured as a mirror-port. Use caution when altering its config",
     True,  "ADVISORY  mirror destination port",              "tb277 T44967 2026-10-09"),

    ('% Comparing "show running-config" on node 1 and node 2',
     True,  "ADVISORY  remote-diff pair header (a read)",     "tb101 T17509 2026-10-22"),
    ("% Results are identical",
     True,  "ADVISORY  remote-diff result (a read)",          "tb101 T17509 2026-10-22"),

    # Real errors that must always stop a batch.
    ("% Incomplete command.",                                 False, "REJECTION", "tb277 T44973"),
    ("% Invalid input detected at '^' marker.",               False, "REJECTION", "tb277 no mls qos enable"),
    ("% Unrecognized command",                                False, "REJECTION", "tb277 access-group on vlan1"),
    ("% Cannot overwrite flash:/default.cfg as it is the default config file",
                                                              False, "REJECTION", "tb277 T44992 restore"),
    ("% Translation configuration of hardware failed",        False, "REJECTION", "IE520 2026-10-07"),
    ("% Interface port1.0.48 is already mirrored",            False, "REJECTION", "tb277 T44967"),
    ("% QoS is not enabled globally!",                        False, "informational on a show", "tb277 group 2"),
]


def main():
    bad = 0
    for line, want, what, seen in CASES:
        got = console.is_advisory(line)
        ok = (got == want)
        bad += (not ok)
        print("%s advisory=%-5s expected=%-5s  %-46s %-28s %s"
              % ("ok " if ok else "BAD", got, want, what, seen, line[:58]))
    print()
    if bad:
        print("FAIL: %d case(s) wrong. A driver would %s."
              % (bad, "swallow a real rejection" if any(
                  console.is_advisory(l) and not w for l, w, _, _ in CASES)
                 else "abort on an advisory and silently skip the rest of its batch"))
    else:
        print("PASS: %d cases, advisories allowed through and every rejection still stops a batch."
              % len(CASES))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
