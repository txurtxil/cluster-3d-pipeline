#!/usr/bin/env python3
# sftp_transfer.py — transferencia verificada SIN paramiko (FASE 5: scp+ssh+sha256sum).
# scp exit 0 NO basta: se exige exists + size + sha256 remoto == local.
# Uso: sftp_transfer.py get|put <host> <port> <remote> <local> [--retries N]
import sys, os, subprocess, hashlib, time


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300)


def main():
    direction, host, port, remote, local = sys.argv[1:6]
    retries = int(sys.argv[sys.argv.index("--retries")+1]) if "--retries" in sys.argv else 3
    tgt = "txurtxil@%s" % host
    last = ""
    for i in range(1, retries+1):
        if direction == "get":
            r = run(["scp", "-P", port, "%s:%s" % (tgt, remote), local])
        else:
            r = run(["scp", "-P", port, local, "%s:%s" % (tgt, remote)])
        if r.returncode != 0:
            last = "scp rc=%d: %s" % (r.returncode, (r.stderr or "").strip()[:140])
            print("SFTP_RETRY %d/%d %s" % (i, retries, last))
            time.sleep(2 * i)
            continue
        # 1) existe remotamente  2) tamano  3) sha256 remoto == local
        t = run(["ssh", "-p", port, tgt, "test -f %s && echo Y" % remote])
        if t.stdout.strip() != "Y":
            last = "remoto no existe tras scp: %s" % remote
            print("SFTP_RETRY %d/%d %s" % (i, retries, last))
            time.sleep(2 * i)
            continue
        s = run(["ssh", "-p", port, tgt, "stat -c %%s %s" % remote])
        rsize = s.stdout.strip()
        lsize = str(os.path.getsize(local))
        h = run(["ssh", "-p", port, tgt, "sha256sum %s | cut -d' ' -f1" % remote])
        rsha = h.stdout.strip()
        lsha = sha256(local)
        if rsize != lsize or rsha != lsha:
            last = "verify mismatch size %s/%s sha %s..%s" % (rsize, lsize, rsha[:10], lsha[:10])
            print("SFTP_RETRY %d/%d %s" % (i, retries, last))
            time.sleep(2 * i)
            continue
        print("SFTP_OK %s %s -> %s (%s bytes, sha256 %s...) intento %d/%d"
              % (direction, remote, local, lsize, lsha[:12], i, retries))
        return 0
    print("SFTP_FAIL %s %s: %s" % (direction, remote, last))
    return 2


if __name__ == "__main__":
    sys.exit(main())
