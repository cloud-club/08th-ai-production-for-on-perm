>[!info] Link
>- 

---

### 개요
1. 호스트 서버에서 Pass-Throungh 설정한 GPU를 할당할 VM을 생성합니다.


## 1. VM 생성 (기본 설정)
```bash
# VM ID 100으로 생성
qm create 100 \
  --name gpu-inference-vm \
  --memory 8192 \
  --cores 4 \
  --sockets 1 \
  --cpu host \
  --ostype l26 \
  --machine q35 \
  --bios ovmf \
  --scsihw virtio-scsi-single \
  --net0 virtio,bridge=vmbr0
```

## 2. EFI 디스크 추가
```bash
# EFI 디스크 생성
qm set 100 --efidisk0 local-lvm:4,efitype=4m,pre-enrolled-keys=1
```

### 3. OS 디스크 추가
```bash
# 100GB 디스크 생성
qm set 100 --scsi0 local-lvm:100,discard=on,iothread=1,ssd=1
```

### 4. ISO 이미지 연결
```bash
qm set 100 --ide2 local-hdd-1TB:iso/ubuntu-24.04.3-desktop-amd64.iso,media=cdrom
```

### 5. GPU 패스스루 추가
```bash
# RTX 3060 Ti 패스스루
qm set 100 --hostpci0 0000:01:00,pcie=1,x-vga=1

# 출력
update VM 100: -hostpci0 0000:01:00,pcie=1,x-vga=1
```
- `0000:01:00` : GPU와 Audio 모두 포함 (All Functions)
- `pcie=1` : PCI Express 모드
- `x-vga=1`
    - Primary GPU를 체크하면 부팅 화면이 GPU로 출력되므로 VNC 화면이 사라집니다. 즉, 콘솔 접근이 안됩니다.


### 6. Hugepages 설정
```bash
# Hugepages 활성화 (1024 = 1GB 단위)
$ qm set 100 --hugepages 1024

# 출력
update VM 100: -hugepages 1024
```

### 7. Memory Balloon 비활성화
```bash
# Balloon 비활성화 (Hugepages 사용 시 필수)
$ qm set 100 --balloon 0

# 출력
update VM 100: -balloon 0
```

### 8. CPU 최적화 설정
```bash
# CPU hidden 설정 (NVIDIA Code 43 방지)
qm set 100 --cpu host,hidden=1,flags=+pcid

update VM 100: -cpu host,hidden=1,flags=+pcid

# args 파라미터 추가 (kvm=off)
qm set 100 --args "-cpu 'host,+kvm_pv_unhalt,+kvm_pv_eoi,hv_vendor_id=NV43FIX,kvm=off'"

update VM 100: -args -cpu 'host,+kvm_pv_unhalt,+kvm_pv_eoi,hv_vendor_id=NV43FIX,kvm=off'
```

### 9. QEMU Guest Agent 활성화
```bash
# Guest Agent 활성화
$ qm set 100 --agent 1
update VM 100: -agent 1
```

### 10. 설정 확인
```bash
# VM 100의 전체 설정 확인
qm config 100
```

```bash
args: -cpu 'host,+kvm_pv_unhalt,+kvm_pv_eoi,hv_vendor_id=NV43FIX,kvm=off'
balloon: 0
bios: ovmf
boot: order=scsi0;ide2;net0
cores: 4
cpu: host,hidden=1,flags=+pcid
efidisk0: local-lvm:vm-100-disk-0,efitype=4m,pre-enrolled-keys=1,size=4M
hostpci0: 0000:01:00,pcie=1,x-vga=1
hugepages: 1024
ide2: local-hdd-1TB:iso/ubuntu-24.04.3-desktop-amd64.iso,media=cdrom,size=6197156K
machine: q35
memory: 8192
meta: creation-qemu=9.2.0,ctime=1763200321
name: gpu-inference-vm
net0: virtio=BC:24:11:17:14:BC,bridge=vmbr0,firewall=1
numa: 1
ostype: l26
scsi0: local-lvm:vm-100-disk-1,iothread=1,size=100G
scsihw: virtio-scsi-single
smbios1: uuid=9c77c621-46c3-4ca6-9ed7-89a52bcb10c5
sockets: 1
vmgenid: c1ef30b4-48d7-4c8a-b726-035ca64eee14
```




---
---
---


## 7. GPU VM 생성 (Web UI)

CLI 대신 Web UI를 선호하는 경우:

### 7.1 기본 VM 생성

1. **Proxmox Web UI 접속** ([https://proxmox-ip:8006](https://proxmox-ip:8006))
2. **Create VM** 버튼 클릭
3. **General 탭:**

```
   Node: (현재 노드 선택)
   VM ID: 100
   Name: gpu-inference-vm
```

**Next** 클릭

4. **OS 탭:**

```
   Use CD/DVD disc image file (iso)
   Storage: local
   ISO image: ubuntu-22.04.3-live-server-amd64.iso
   Guest OS:
     Type: Linux
     Version: 6.x - 2.6 Kernel
```

**Next** 클릭

5. **System 탭:**

```
   Graphic card: Default
   Machine: q35
   BIOS: OVMF (UEFI)
   ✅ Add EFI Disk
   EFI Storage: local-lvm
   SCSI Controller: VirtIO SCSI single
   ✅ Qemu Agent
```

**Next** 클릭

6. **Disks 탭:**

```
   Bus/Device: SCSI 0
   Storage: local-lvm
   Disk size (GiB): 100
   ✅ Discard
   ✅ SSD emulation (SSD인 경우만)
   ✅ IO thread
```

**Next** 클릭

7. **CPU 탭:**

```
   Sockets: 1
   Cores: 4
   Type: host
```

**Next** 클릭

8. **Memory 탭:**

```
   Memory (MiB): 8192
   Minimum memory (MiB): 8192
```

**Next** 클릭

9. **Network 탭:**

```
   Bridge: vmbr0
   Model: VirtIO (paravirtualized)
```

**Next** 클릭

10. **Confirm 탭:**
    - ❌ **Start after created 체크 해제** (아직 시작하지 말 것) **Finish** 클릭

### 7.2 GPU 패스스루 추가

1. **VM 100 선택** → **Hardware 탭**
2. **Add** → **PCI Device**

```
   Raw Device: 0000:01:00.0 (NVIDIA GeForce RTX 3060 Ti)
   ✅ All Functions (오디오 포함)
   ✅ Primary GPU (선택사항)
   ✅ PCI-Express
   ✅ ROM-Bar
```

**Add** 클릭

### 7.3 설정 파일 수동 편집

Web UI에서는 hugepages와 일부 고급 설정 불가하므로 SSH 사용:

bash

```bash
# SSH 접속
ssh root@<PROXMOX_IP>

# VM 설정 파일 편집
nano /etc/pve/qemu-server/100.conf
```

**다음 라인들을 추가/수정:**

conf

```conf
# Balloon 비활성화
balloon: 0

# CPU 설정 수정
cpu: host,hidden=1,flags=+pcid

# Args 추가 (새 라인으로)
args: -cpu 'host,+kvm_pv_unhalt,+kvm_pv_eoi,hv_vendor_id=NV43FIX,kvm=off'

# Hugepages 추가 (새 라인으로)
hugepages: 1024

# NUMA 추가 (새 라인으로)
numa: 1
```

**저장 및 종료:**

- `Ctrl + X` → `Y` → `Enter`

**최종 설정 파일 예시:**

conf

```conf
agent: 1
args: -cpu 'host,+kvm_pv_unhalt,+kvm_pv_eoi,hv_vendor_id=NV43FIX,kvm=off'
balloon: 0
bios: ovmf
boot: order=scsi0;ide2;net0
cores: 4
cpu: host,hidden=1,flags=+pcid
efidisk0: local-lvm:vm-100-disk-0,efitype=4m,pre-enrolled-keys=1,size=4M
hostpci0: 0000:01:00,pcie=1,x-vga=1
hugepages: 1024
ide2: local:iso/ubuntu-22.04.3-live-server-amd64.iso,media=cdrom,size=1938M
machine: q35
memory: 8192
name: gpu-inference-vm
net0: virtio=BC:24:11:XX:XX:XX,bridge=vmbr0
numa: 1
ostype: l26
scsi0: local-lvm:vm-100-disk-1,discard=on,iothread=1,size=100G,ssd=1
scsihw: virtio-scsi-single
sockets: 1
vmgenid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```




---

# References
- 