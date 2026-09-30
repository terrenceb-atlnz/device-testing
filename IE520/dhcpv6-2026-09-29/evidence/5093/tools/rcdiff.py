import re,sys,difflib
def rc(fn):
  t=open(fn,errors="replace").read()
  r=t.split(">>> show running-config")[1]
  r=re.split(r"\n\d\d:\d\d:\d\d >>> ",r)[0]
  return [l.rstrip() for l in r.replace("\r","").splitlines()[1:] if l.strip()]
a,b=rc(sys.argv[1]),rc(sys.argv[2])
for d in difflib.unified_diff(a,b,sys.argv[1],sys.argv[2],lineterm="",n=1): print(d)
