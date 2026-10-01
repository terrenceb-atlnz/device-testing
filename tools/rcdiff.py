"""rcdiff.py <before.log> <after.log>: unified diff (1 line of context) of the FIRST
`show running-config` in each of two ckcon-style transcripts (stdout of ckcon.py:
`HH:MM:SS >>> <cmd>` header lines, each followed by that command's output). Blank
lines and CRs are dropped. Reads files only; prints to stdout. Runs anywhere."""
import re,sys,difflib
if len(sys.argv)!=3 or sys.argv[1] in ("-h","--help"):
  print("usage: rcdiff.py <before.log> <after.log>"); sys.exit(0 if sys.argv[1:2] in (["-h"],["--help"]) else 2)
def rc(fn):
  t=open(fn,errors="replace").read()
  r=t.split(">>> show running-config")[1]
  r=re.split(r"\n\d\d:\d\d:\d\d >>> ",r)[0]
  return [l.rstrip() for l in r.replace("\r","").splitlines()[1:] if l.strip()]
a,b=rc(sys.argv[1]),rc(sys.argv[2])
for d in difflib.unified_diff(a,b,sys.argv[1],sys.argv[2],lineterm="",n=1): print(d)
