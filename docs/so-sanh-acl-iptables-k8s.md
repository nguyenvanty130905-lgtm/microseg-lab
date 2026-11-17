# Bang doi chieu: ACL Cisco - iptables - Kubernetes NetworkPolicy

| Tieu chi | ACL Cisco | iptables | K8s NetworkPolicy |
|---|---|---|---|
| Huong (Inbound/Outbound) | Gan vao interface theo chieu `in` hoac `out` | Chuoi INPUT, OUTPUT, FORWARD | `Ingress` (vao pod) va `Egress` (ra khoi pod) |
| Nho trang thai (stateful) | Khong (stateless); phai them `established` cho chieu tra loi | Co, qua conntrack (`ESTABLISHED,RELATED`) | Co: goi tra loi cua ket noi da duoc phep tu dong di qua (tuy CNI) |
| Chon doi tuong theo | IP, wildcard mask, giao thuc, cong | IP, cong, interface, giao thuc, ... | Nhan (label) pod, namespace, ipBlock, cong |
| Mac dinh | Interface chua gan ACL: cho phep; het ACL co `deny` ngam dinh | Policy mac dinh cua chain thuong la ACCEPT | Pod chua bi policy chon: cho phep; da bi chon: chan phan khong duoc liet ke |
| Thu tu xu ly | Tu tren xuong, khop dong dau tien | Tu tren xuong, khop luat dau tien | Khong co thu tu, cac policy cong don (hop cua cac luat cho phep) |
| Luat chan tuong minh | Co (`deny`) | Co (`DROP`, `REJECT`) | Khong (chi co allow, chan bang cach khong liet ke) |
| Pham vi | Mot router / interface | Mot may chu (host) | Ca cum nhieu node |
| Tang lop | L3 - L4 | L3 - L4 (mo rong ung dung can module) | L3 - L4 (L7 can Cilium / service mesh) |
| Dung cho Docker | - | Docker tu dong tao luat iptables; tuy chinh qua chuoi `DOCKER-USER` | - |
