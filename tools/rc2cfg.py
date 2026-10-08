#!/usr/bin/env python3
"""rc2cfg.py <ckcon-stdout> <out.cfg> <header-line> [<header-line> ...]
Turn the FIRST `show running-config` in a saved ckcon.py stdout (the `HH:MM:SS >>> cmd`
header format rcdiff.py reads) into a loadable per-device .cfg (logged-output.md §2):
the header lines are written first, each prefixed "! " unless it already starts with "!",
then the running-config with the echoed command, prompts, pager remnants and CRs removed.
Blank lines are kept out; AW+ '!' separator lines are kept. Reads and writes files only."""
import re
import sys

if len(sys.argv) < 4 or sys.argv[1] in ("-h", "--help"):
    print("usage: rc2cfg.py <ckcon-stdout> <out.cfg> <header-line> [<header-line> ...]")
    sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
src, dst, heads = sys.argv[1], sys.argv[2], sys.argv[3:]
t = open(src, errors="replace").read().replace("\r", "")
if ">>> show running-config\n" not in t:
    print("no '>>> show running-config' block in %s" % src)
    sys.exit(1)
body = t.split(">>> show running-config\n", 1)[1]
body = re.split(r"\n\d\d:\d\d:\d\d >>> ", body)[0]
out = []
for line in body.splitlines():
    line = line.rstrip()
    if not line.strip():
        continue
    if line.strip() == "show running-config":          # echoed command
        continue
    if re.match(r"^[\w.-]+(\([^)]*\))?[#>]\s*$", line):  # a bare prompt
        continue
    if "--More--" in line:
        continue
    out.append(line)
with open(dst, "w") as f:
    for h in heads:
        f.write((h if h.startswith("!") else "! " + h) + "\n")
    f.write("\n".join(out) + "\n")
print("wrote %s: %d header + %d config lines" % (dst, len(heads), len(out)))
