#!/usr/bin/env python3
"""Kiem thu tu dong ma tran chinh sach (Nguon x Dich x Cong).

  python tests/run_matrix.py docker   # kiem tra Docker Compose (3 network)
  python tests/run_matrix.py k8s      # kiem tra Kubernetes NetworkPolicy
  python tests/run_matrix.py l7       # kiem tra L7 (HTTP method/path) tren cum Cilium

Ma thoat 0 neu moi dong PASS, 1 neu co dong FAIL.
"""
import csv
import os
import subprocess
import sys

NETCHECK = "microseg/netcheck:1"

# (id, nguon, dich, cong, ky_vong_docker, ky_vong_k8s, ghi_chu)
MATRIX = [
    ("M1", "client", "web", 80, "ALLOW", "ALLOW", "Nguoi dung vao web"),
    ("M2", "client", "api", 8000, "DENY", "DENY", "Nguoi dung khong goi thang api"),
    ("M3", "client", "db", 5432, "DENY", "DENY", "Nguoi dung khong goi thang db"),
    ("M4", "web", "api", 8000, "ALLOW", "ALLOW", "web goi api"),
    ("M5", "web", "db", 5432, "DENY", "DENY", "web khong goi thang db"),
    ("M6", "api", "db", 5432, "ALLOW", "ALLOW", "api goi db"),
    ("M7", "api", "web", 80, "ALLOW", "DENY", "Chieu nguoc: Docker khong chan duoc (cung network)"),
    ("M8", "db", "api", 8000, "ALLOW", "DENY", "db chu dong goi api: Docker khong chan duoc"),
    ("M9", "db", "example.com", 80, "DENY", "DENY", "db khong ra Internet"),
    ("M10", "untrusted", "web", 80, "N/A", "DENY", "Namespace khong duoc phep"),
]

K8S_SRC = {
    "client": ("external", "tester"),
    "untrusted": ("untrusted", "tester"),
    "web": ("microseg", "tester-web"),
    "api": ("microseg", "tester-api"),
    "db": ("microseg", "tester-db"),
}

# (id, method, path, ma_http_ky_vong, ghi_chu)   nguon: pod tester-web
L7 = [
    ("L1", "GET", "/health", "200", "Duoc phep"),
    ("L2", "GET", "/notes", "200", "Duoc phep"),
    ("L3", "POST", "/notes", "200", "Duoc phep"),
    ("L4", "DELETE", "/notes/1", "403", "Cilium chan theo method"),
]


def run(cmd, timeout=40):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except subprocess.TimeoutExpired:
        return 124, ""


def docker_cmd(src, dst, port):
    net = "microseg_frontend" if src == "client" else f"container:{src}"
    return ["docker", "run", "--rm", "--network", net, NETCHECK,
            "nc", "-z", "-w", "3", dst, str(port)]


def k8s_cmd(src, dst, port):
    ns, pod = K8S_SRC[src]
    host = dst
    if ns != "microseg" and dst in ("web", "api", "db"):
        host = f"{dst}.microseg.svc.cluster.local"
    return ["kubectl", "-n", ns, "exec", pod, "--",
            "nc", "-z", "-w", "3", host, str(port)]


def l7_cmd(method, path):
    cmd = ["kubectl", "-n", "microseg", "exec", "tester-web", "--",
           "curl", "-s", "-o", "/dev/null", "-m", "5", "-w", "%{http_code}",
           "-X", method, f"http://api:8000{path}"]
    if method == "POST":
        cmd += ["-H", "Content-Type: application/json", "-d", '{"text":"l7-test"}']
    return cmd


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("docker", "k8s", "l7"):
        print(__doc__)
        return 2
    os.makedirs("results", exist_ok=True)
    rows, fails = [], 0

    if mode == "l7":
        print(f"{'ID':4} {'REQUEST':22} {'KY VONG':8} {'THUC TE':8} KET QUA")
        for rid, method, path, expect, note in L7:
            _, out = run(l7_cmd(method, path))
            actual = out[-3:] if out else "000"
            ok = actual == expect
            fails += 0 if ok else 1
            print(f"{rid:4} {method + ' ' + path:22} {expect:8} {actual:8} {'PASS' if ok else 'FAIL'}")
            rows.append([rid, method, path, expect, actual, "PASS" if ok else "FAIL", note])
        header = ["id", "method", "path", "expected_http", "actual_http", "result", "note"]
    else:
        print(f"{'ID':4} {'NGUON':10} {'DICH':12} {'CONG':5} {'KY VONG':8} {'THUC TE':8} KET QUA")
        for rid, src, dst, port, exp_d, exp_k, note in MATRIX:
            expect = exp_d if mode == "docker" else exp_k
            if expect == "N/A":
                continue
            cmd = docker_cmd(src, dst, port) if mode == "docker" else k8s_cmd(src, dst, port)
            code, _ = run(cmd)
            actual = "ALLOW" if code == 0 else "DENY"
            ok = actual == expect
            fails += 0 if ok else 1
            print(f"{rid:4} {src:10} {dst:12} {port:<5} {expect:8} {actual:8} {'PASS' if ok else 'FAIL'}")
            rows.append([rid, src, dst, port, expect, actual, "PASS" if ok else "FAIL", note])
        header = ["id", "source", "destination", "port", "expected", "actual", "result", "note"]

    path = os.path.join("results", f"matrix-{mode}.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    total = len(rows)
    print(f"\nTong: {total} | PASS: {total - fails} | FAIL: {fails} | Da luu: {path}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
