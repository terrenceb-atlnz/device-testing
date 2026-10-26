#!/usr/bin/env python3
"""atmf_provision.py <tty> <baud> <transcript> --node NAME [--device TYPE] [--rel FILE]
                    [--cfg FILE] [--set-master] [--keep | --restore-only]
Provision a future AMF node on the AMF master at <tty>, then undo it, in ONE call. It runs the
AWPTCM-T28218 sequence that the 2026-10-21 and 2026-10-27 campaigns each built by hand
(review atmf-2026-10-27T0855/28218/28218-review.md):
  pre      show atmf, show atmf provision nodes, and `show file` of any existing
           <media>/atmf/<net>/info/backup_<NAME>.info (provisioning REWRITES that file; its
           old content is printed here so it is not lost unseen)
  steps    atmf provision node NAME [device TYPE] / create / locate /
           copy flash:/REL ./REL / configure boot system REL /
           copy flash:/CFG ./CFG / configure boot config CFG / exit /
           show atmf provision nodes / show atmf backup / dir recursive <the node's directory>
  restore  atmf provision node NAME / delete (answers y if asked) / exit /
           rmdir <the node's directory> (`delete` leaves it behind, and the node stays listed
           as Provisioned until it goes) / show atmf provision nodes
Each command is printed as `HH:MM:SS >>> cmd` with its output (ckcon's format; save stdout into
the case's work/). It stops at the first "% " line (exit 3) and, if the steps had started,
still runs the restore.
  --set-master    configure `atmf master` first if the unit is not master, and `no atmf master`
                  at the end (only if this run set it). After `no atmf master`, "Restricted
                  login" stays Disabled until a reload: this tool does not reload; it says so.
  --keep          run pre + steps only (leave the node provisioned)
  --restore-only  run the restore only (for a node a cut-short run left behind)
Exit: 0 ok, 3 a CLI error, 4 precondition (not master, no backup media), 7 no privileged
prompt, 2 usage. Env CKTO = per-command timeout s (default 90; copies get max(CKTO, 600));
CK_USER / CK_PASSWORD = credentials (default manager / friend)."""
import os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
USAGE = ("usage: atmf_provision.py <tty> <baud> <transcript> --node NAME [--device TYPE] [--rel FILE] "
         "[--cfg FILE] [--set-master] [--keep | --restore-only]")
if len(sys.argv) < 4 or sys.argv[1] in ("-h", "--help"):
    print(__doc__ if sys.argv[1:2] in (["-h"], ["--help"]) else USAGE)
    sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
try:
    tty, baud, transcript = sys.argv[1], int(sys.argv[2]), sys.argv[3]
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
opts = {"node": None, "device": None, "rel": None, "cfg": None,
        "set-master": False, "keep": False, "restore-only": False}
a = sys.argv[4:]
while a:
    k = a.pop(0)
    if k[2:] in ("set-master", "keep", "restore-only"):
        opts[k[2:]] = True; continue
    if k.startswith("--") and k[2:] in opts and a:
        opts[k[2:]] = a.pop(0); continue
    print(USAGE); print("bad argument: %r" % k); sys.exit(2)
SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
for k in ("node", "device", "rel", "cfg"):
    if opts[k] is not None and not SAFE.match(opts[k]):
        print(USAGE); print("--%s must be a plain name (letters, digits, . _ -): %r" % (k, opts[k])); sys.exit(2)
if not opts["node"] or (opts["keep"] and opts["restore-only"]):
    print(USAGE); print("--node is required; --keep and --restore-only exclude each other"); sys.exit(2)
NODE = opts["node"]
CKTO = float(os.environ.get("CKTO", "90"))

import console, awlogin as L

ESC = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[78()=>]|\x1b\][^\x07]*\x07")
c = console.Console(tty, transcript, baud=baud)


class CliError(Exception):
    pass


def clean(s):
    return ESC.sub("", s.replace("\r", ""))


def run(cmd, timeout=None, check=True):
    out = clean(c.cmd(cmd, timeout=timeout or CKTO))
    print("%s >>> %s" % (time.strftime("%H:%M:%S"), cmd))
    if out:
        print(out)
    if check and any(l.lstrip().startswith("%") and not console.is_advisory(l) for l in out.splitlines()):
        raise CliError(cmd)
    return out


def run_yn(cmd):
    """A command that MAY ask (y/n): answer y + Enter if it does (memory awplus-cli-confirmations-need-enter)."""
    out = clean(c.send(cmd, quiet=1.5, timeout=30.0, need_prompt=False))
    print("%s >>> %s" % (time.strftime("%H:%M:%S"), cmd))
    if re.search(r"\(y/n\)", out):
        print(out.strip())
        out = clean(c.send("y", quiet=1.5, timeout=60.0))
        print("%s >>> y   (answer to the (y/n) above)" % time.strftime("%H:%M:%S"))
    if out.strip():
        print(out.strip())
    if any(l.lstrip().startswith("%") and not console.is_advisory(l) for l in out.splitlines()):
        raise CliError(cmd)
    return out


def field(out, name):
    m = re.search(r"^\s*%s\s*[.:]+\s*(.+?)\s*$" % re.escape(name), out, re.M)
    return m.group(1) if m else ""


def node_dir(prov_out):
    """'usb:/atmf/Net/nodes/<node>/flash/' -> 'usb:/atmf/Net/nodes/<node>'."""
    path = field(prov_out, "Provision Path")
    return re.sub(r"/flash/?$", "", path) if path else ""


rc = 0; ok = False; set_master = False; started = False
try:
    ok = L.login(c)
    if not ok:
        print("no privileged prompt on %s" % tty); rc = 7
        raise SystemExit(rc)
    run("terminal length 0", check=False)
    atmf = run("show atmf", check=False)
    role, net = field(atmf, "Role"), field(atmf, "Network Name")
    if role != "Master" and not opts["set-master"]:
        print("!!! %s is not the AMF master (Role %r); use --set-master or make it master first" % (tty, role))
        rc = 4
    elif role != "Master":
        run("configure terminal"); run("atmf master"); run("end")
        set_master = True
        time.sleep(20)                       # the 2026-10-27 run settled 20 s before reading
        role = field(run("show atmf", check=False), "Role")
        if role != "Master":
            print("!!! still not master after `atmf master` (Role %r)" % role); rc = 4
    prov = run("show atmf provision nodes", check=False)
    media = field(prov, "Backup Media")
    if rc == 0 and (not media or media.upper().startswith("NONE")):
        print("!!! no backup media (Backup Media %r): plug a USB stick or set a backup server" % media); rc = 4
    if rc == 0 and net and media:
        root = "usb:" if media.upper().startswith("USB") else ("card:" if media.upper().startswith("SD") else "")
        if root:
            info = "%s/atmf/%s/info/backup_%s.info" % (root, net, NODE)
            run("show file %s" % info, check=False)    # "% ... not found" is fine: there is none yet

    if rc == 0 and not opts["restore-only"]:
        started = True
        run("atmf provision node %s%s" % (NODE, (" device %s" % opts["device"]) if opts["device"] else ""), timeout=max(CKTO, 120))
        run("create")
        run("locate")
        if opts["rel"]:
            run("copy flash:/%s ./%s" % (opts["rel"], opts["rel"]), timeout=max(CKTO, 600))
            run("configure boot system %s" % opts["rel"])
        if opts["cfg"]:
            run("copy flash:/%s ./%s" % (opts["cfg"], opts["cfg"]), timeout=max(CKTO, 600))
            run("configure boot config %s" % opts["cfg"])
        run("exit")
        prov = run("show atmf provision nodes", check=False)
        run("show atmf backup", check=False)
        nd = node_dir(prov)
        if nd:
            run("dir recursive %s" % nd, check=False)
except CliError as e:
    print("!!! CLI error on %r -- stopping%s" % (e.args[0], " (restore follows)" if started else ""))
    rc = 3
    try:
        c.to_exec()
    except Exception:
        pass
except SystemExit:
    pass                                     # no login: rc is 7; fall through to close the port

try:
    if ok and rc in (0, 3) and (started or opts["restore-only"]) and not opts["keep"]:
        print("--- restore ---")
        try:
            prov = run("show atmf provision nodes", check=False)
            nd = node_dir(prov) if NODE in prov else ""
            if NODE in prov:
                run("atmf provision node %s" % NODE, timeout=max(CKTO, 120))
                run_yn("delete")
                run("exit")
            if nd:
                run_yn("rmdir %s" % nd)
            after = run("show atmf provision nodes", check=False)
            print("restore: node %s %s" % (NODE, "STILL LISTED" if NODE in after else "gone"))
            if NODE in after and rc == 0:
                rc = 3
        except CliError as e:
            print("!!! CLI error during restore on %r" % e.args[0]); rc = 3
    if ok and set_master:
        try:
            c.to_exec()
            run("configure terminal"); run("no atmf master"); run("end")
            print("note: `no atmf master` done; \"Restricted login\" stays Disabled until a reload "
                  "(memory atmf-recovery-residue-and-reboots). Reload with tools/tb ckreload if the case needs it.")
        except CliError as e:
            print("!!! CLI error on %r" % e.args[0]); rc = 3
finally:
    if ok:
        try:
            if not c.monitor_off():
                print("cleanup: console busy or not at exec -- sent nothing")
        except Exception as e:
            print("cleanup: %s" % e)
    c.close()
sys.exit(rc)
