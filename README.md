# Microsegmentation: ung dung 3 tang + kiem thu tu dong

Ung dung: web (nginx) -> api (FastAPI, cong 8000) -> db (PostgreSQL, cong 5432).
Luu y: bo ma nay chua duoc chay thu tren may cua ban. Neu co loi, chup man hinh gui lai.

Cac lenh duoi day chay trong PowerShell, tu thu muc microseg-app.
Can cai Python mot lan: `winget install Python.Python.3.12` (roi mo cua so PowerShell moi).

## A. Docker Compose (3 network)

```
docker build -t microseg/netcheck:1 tests/netcheck
docker compose up -d --build
```
Mo http://localhost:8080 (them/xem ghi chu). Kiem tra API qua web:
```
curl.exe http://localhost:8080/api/health
docker network ls
docker network inspect microseg_data
```
Chay ma tran kiem thu:
```
python tests\run_matrix.py docker
```
Don dep: `docker compose down -v`

## B. Kubernetes + Calico (NetworkPolicy)

```
kind create cluster --name microseg --config k8s\kind-config.yaml
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml
kubectl wait --for=condition=Ready nodes --all --timeout=300s

docker build -t microseg/api:1 api
docker build -t microseg/web:1 web
kind load docker-image microseg/netcheck:1 microseg/api:1 microseg/web:1 --name microseg

kubectl apply -f k8s\00-namespaces.yaml
kubectl apply -f k8s\01-app.yaml
kubectl apply -f k8s\02-tests.yaml
kubectl -n microseg get pods
```
Cho cac pod Running, roi TRUOC khi chan, chay thu de co anh "truoc":
```
python tests\run_matrix.py k8s
```
(luc nay nhieu dong se FAIL vi chua co policy - day la bang chung "truoc khi chan")

Ap dung chinh sach, chay lai:
```
kubectl apply -f k8s\03-default-deny.yaml
kubectl apply -f k8s\04-allow-dns.yaml
kubectl apply -f k8s\05-tier-policies.yaml
python tests\run_matrix.py k8s
```
Don dep: `kind delete cluster --name microseg`

## C. Nang cao: L7 bang Cilium (nhom 4-5 SV)

Calico ban mien phi KHONG loc duoc theo HTTP method/path. Dung Cilium tren mot cum rieng
(xoa cum Calico truoc de tiet kiem RAM):
```
kind create cluster --name microseg-cilium --config k8s\kind-cilium.yaml
cilium install
cilium status --wait
```
(Cilium CLI: xem huong dan cai dat tren docs.cilium.io, muc "Cilium Quick Installation".)
Sau do load image, deploy ung dung nhu muc B, roi:
```
kubectl apply -f k8s\10-cilium-l7.yaml
python tests\run_matrix.py l7
```
Ky vong: GET /health, GET /notes, POST /notes tra 200; DELETE /notes/1 tra 403.

## D. CI (GitHub Actions)

Day thu muc nay len mot repo GitHub. Workflow `.github/workflows/netpol-ci.yml` tu dong
dung Docker Compose va cum kind + Calico roi chay `tests/run_matrix.py`; ket qua CSV
duoc luu o muc Artifacts cua lan chay.
