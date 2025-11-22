### 개요
1. 홈서버에 장착된 NVIDIA RTX 3060 Ti를 가상화 환경(Proxmox VE) 환경에서 사용해야 되는 상황입니다.
2. 가상화 오버헤드로 인한 GPU 성능 저하를 방지하기 위해, VM에 GPU를 Direct로 할당하도록 GPU Passthrough 설정을 목표로 합니다.


## 1. IOMMU Group 확인
- PCI 패스스루를 위해, 해당 PCI 장치가 속한 IOMMU 그룹에 다른 장치가 포함돼있지 않아야 합니다. 다음 명령을 통해 패스스루할 장치가가 포함된 IOMMU 그룹에 GPU 외 다른 장치가 있는지 확인합니다.
```bash
$ for d in /sys/kernel/iommu_groups/*/devices/*; do 
   n=${d#*/iommu_groups/*}; n=${n%%/*}
   printf 'IOMMU Group %s ' "$n"
   lspci -nns "${d##*/}"
done

IOMMU Group 0 00:00.0 Host bridge [0600]: Intel Corporation Comet Lake-S 6c Host Bridge/DRAM Controller [8086:9b53] (rev 05)
IOMMU Group 1 00:01.0 PCI bridge [0604]: Intel Corporation 6th-10th Gen Core Processor PCIe Controller (x16) [8086:1901] (rev 05)
IOMMU Group 1 01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3060 Ti Lite Hash Rate] [10de:2489] (rev a1)
IOMMU Group 1 01:00.1 Audio device [0403]: NVIDIA Corporation GA104 High Definition Audio Controller [10de:228b] (rev a1)
IOMMU Group 2 00:08.0 System peripheral [0880]: Intel Corporation Xeon E3-1200 v5/v6 / E3-1500 v5 / 6th/7th/8th Gen Core Processor Gaussian Mixture Model [8086:1911]
IOMMU Group 3 00:14.0 USB controller [0c03]: Intel Corporation Comet Lake PCH-V USB Controller [8086:a3af]
IOMMU Group 3 00:14.2 Signal processing controller [1180]: Intel Corporation Comet Lake PCH-V Thermal Subsystem [8086:a3b1]
IOMMU Group 4 00:16.0 Communication controller [0780]: Intel Corporation Comet Lake PCH-V HECI Controller [8086:a3ba]
IOMMU Group 5 00:17.0 SATA controller [0106]: Intel Corporation 400 Series Chipset Family SATA AHCI Controller [8086:a382]
IOMMU Group 6 00:1c.0 PCI bridge [0604]: Intel Corporation Comet Lake PCI Express Root Port #05 [8086:a394] (rev f0)
IOMMU Group 6 02:00.0 Ethernet controller [0200]: Realtek Semiconductor Co., Ltd. RTL8111/8168/8411 PCI Express Gigabit Ethernet Controller [10ec:8168] (rev 0c)
IOMMU Group 7 00:1f.0 ISA bridge [0601]: Intel Corporation H410 Chipset LPC/eSPI Controller [8086:a3da]
IOMMU Group 7 00:1f.2 Memory controller [0580]: Intel Corporation Cannon Lake PCH Power Management Controller [8086:a3a1]
IOMMU Group 7 00:1f.3 Audio device [0403]: Intel Corporation Comet Lake PCH-V cAVS [8086:a3f0]
IOMMU Group 7 00:1f.4 SMBus [0c05]: Intel Corporation Comet Lake PCH-V SMBus Host Controller [8086:a3a3]
```

- GPU가 포함된 IOMMU 그룹#1 에 속해있는 디바이스 목록
    - 00:01.0 PCI bridge [0604]: Intel Corporation 6th-10th Gen Core Processor PCIe Controller (x16) [8086:1901]
        - GPU와 연결된 PCI 브릿지이므로, GPU와 함께 패스스루
    - VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3060 Ti Lite Hash Rate] [10de:2489] 
    - 01:00.1 Audio device [0403]: NVIDIA Corporation GA104 High Definition Audio Controller [10de:228b]
```bash
IOMMU Group 1 00:01.0 PCI bridge [0604]: Intel Corporation 6th-10th Gen Core Processor PCIe Controller (x16) [8086:1901] (rev 05)
IOMMU Group 1 01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3060 Ti Lite Hash Rate] [10de:2489] (rev a1)
IOMMU Group 1 01:00.1 Audio device [0403]: NVIDIA Corporation GA104 High Definition Audio Controller [10de:228b] (rev a1)
```

GPU가 포함된 IOMMU 그룹#1에 GPU외에 다른 디바이스들이 포함돼있지 않으므로, 추가 작업 없이 패스스루 설정을 진행합니다.


## 2. VFIO (Virtual Function I/O) Driver 설정
1. VFIO 모듈 활성화
```bash
$ vi /etc/modules
vfio
vfio_iommu_type1
vfio_pci
vfio_vitqfd
```

2. VFIO 설정
- 다음의 config파일을 생성하고 IOMMU 그룹 확인 단계에서 확인한 장치의 ID를 입력합니다.
```bash
$ vi /etc/modprobe.d/vfio.conf
options vfio-pci ids=10de:2489,10de:228b
```


### 3. Host 상에서 NVIDIA Driver Blacklist 설정
- 패스스루를 통해 디바이스를 VM에 온전히 할당하기 위해서는, 부팅 단계에서 해당 디바이스를 호스트 서버가 선점하지 못하도록 해야합니다. 이를 위해 호스트에서 블랙리스트를 설정합니다.
```bash
vi /etc/modprobe.d/blacklist-nvidia.conf
blacklist nouveau
blacklist nvidia*
```


### 4. GRUB 설정
- 부팅 관련 옵션 설정을 위해 다음 작업을 수행합니다.
    - 파일 안에서 `GRUB_CMDLINE_LINUX` 라인을 찾습니다.
    - 초기 값인 `GRUB_CMDLINE_LINUX=""`을 수정합니다.
```bash
$ vi /etc/default/grub

# 다음과 같이 변경
GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt vfio-pci.ids=10de:2489,10de:228b default_hugepagesz=1G hugepagesz=1G hugepages=8"
```
- `intel_iommu=on` : IOMMU 활성화
- `iommu=pt`: 패스스루 모드 설정
- `vfio-pci.ids=10de:2489,10de:228b` : 패스스루할 디바이스 ID
- `hugepage` 설정의 경우, hugepage의  크기를 기본값인`Hugepagesize: 2048 kB` 에서 `1G`로 변경함으로써 GPU 패스스루 VM의 성능을 향상시키기 위한 설정입니다. 생략해도 무방합니다.

- 설정한 부트 파라미터 적용을 위한 GRUB 구성 재생성
```bash
# ubuntu/debian
$ sudo update-grub

# reboot 수행 필요 initramfs 작업까지 설정하고 reboot 해도 무방
$ sudo reboot
```

### 5. initramfs 업데이트 및 재부팅
```bash
# ubuntu/debian
$ sudo update-initramfs -u

# reboot
$ reboot
```

### 6. 설정 검증
#### 6-1. 호스트 서버 모듈 블랙리스트 적용 확인
```bash
$ lsmod | grep -e nouveau -e nvidia
# 결과 미출력이 정상
```

#### 6-2. IOMMU 활성화 확인
```bash
$ dmesg | grep -i iommu
...
[    0.058205] DMAR: IOMMU enabled
[    0.142482] DMAR-IR: IOAPIC id 2 under DRHD base  0xfed91000 IOMMU 0
[    0.376461] iommu: Default domain type: Passthrough (set via kernel command line)
...
```
- `DMAR: IOMMU enabled` : 커널이 IOMMU를 활성화함을 의미
- `iommu: Default domain type: Passthrough (set via kernel command line)` : 커널 파라미터로 인해 패스스루 기본 도메인으로 동작함을 의미

#### 6-3. VFIO 확인
```bash
$ dmesg | grep -i vfio
[    0.000000] Command line: BOOT_IMAGE=/boot/vmlinuz-6.8.12-16-pve root=/dev/mapper/pve-root ro intel_iommu=on iommu=pt vfio-pci.ids=10de:2489,10de:228b hugepagesz=1G hugepages=8 quiet
[    0.058151] Kernel command line: BOOT_IMAGE=/boot/vmlinuz-6.8.12-16-pve root=/dev/mapper/pve-root ro intel_iommu=on iommu=pt vfio-pci.ids=10de:2489,10de:228b hugepagesz=1G hugepages=8 quiet
[    2.452042] VFIO - User Level meta-driver version: 0.3
[    2.460867] vfio-pci 0000:01:00.0: vgaarb: deactivate vga console
[    2.460871] vfio-pci 0000:01:00.0: vgaarb: VGA decodes changed: olddecodes=io+mem,decodes=io+mem:owns=io+mem
[    2.461011] vfio_pci: add [10de:2489[ffffffff:ffffffff]] class 0x000000/00000000
[    2.508878] vfio_pci: add [10de:228b[ffffffff:ffffffff]] class 0x000000/00000000
```
- `BOOT_IMAGE=/boot/vmlinuz-6.8.12-16-pve root=/dev/mapper/pve-root ro intel_iommu=on iommu=pt vfio-pci.ids=10de:2489,10de:228b hugepagesz=1G hugepages=8 quiet`
    - 부트 커맨드라인 출력
        - `intel_iommu=on` : Intel IOMMU 활성화
        - `iommu=pt` : 패스스루 모드로 동작
        - `vfio-pci.ids=10de:2489,10de:228` : 해당 디바이스 IO 목록을 VFIO 드라이버에 바인딩하도록 지정
        - `hugesize=1G hugepages=8` : 1GiB 크기 hugepage 8개를 예약
- `VFIO - User Level meta-driver version: 0.3` : VFIO 드라이버 로드 확인
- `vfio-pci 0000:01:00.0: vgaarb: deactivate vga console` : 해당 VGA 디바이스를 비활성화
- `vfio-pci 0000:01:00.0: vgaarb: VGA decodes changed: olddecodes=io+mem,decodes=io+mem:owns=io+mem` : VGA 디바이스를 VFIO 드라이버에 할당됨
- `vfio_pci: add [10de:2489[ffffffff:ffffffff]] class 0x000000/00000000` : PCI ID를 기반으로 해당 장치들을 VFIO 드라이버에 바인딩됨
- `vfio_pci: add [10de:228b[ffffffff:ffffffff]] class 0x000000/00000000` : PCI ID를 기반으로 해당 장치들을 VFIO 드라이버에 바인딩됨

#### 6-4. vfio_pci 드라이버 바인딩 확인
```bash
$ lspci -nnk -d 10de:2489
01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3060 Ti Lite Hash Rate] [10de:2489] (rev a1)
        Subsystem: Gigabyte Technology Co., Ltd GA104 [GeForce RTX 3060 Ti Lite Hash Rate] [1458:405a]
        Kernel driver in use: vfio-pci
        Kernel modules: nvidiafb, nouveau

$ lspci -nnk -d 10de:228b
01:00.1 Audio device [0403]: NVIDIA Corporation GA104 High Definition Audio Controller [10de:228b] (rev a1)
        Subsystem: Gigabyte Technology Co., Ltd GA104 High Definition Audio Controller [1458:405a]
        Kernel driver in use: vfio-pci
        Kernel modules: snd_hda_intel
```
- `Kernel driver in use: vfio-pci`
    - vfio 드라이버가 GPU를 제어하고 있음을 의미
- `Kernel modules: nvidiafb, nouveau`
    - 사용 가능한 모듈 목록을 단순 출력
```

#### 6-5. hugepages 확인
- 현재 커널에 어떤 부트 파라미터가 전달됐는지 확인
```bash
$ cat /proc/cmdline
BOOT_IMAGE=/boot/vmlinuz-6.8.12-16-pve root=/dev/mapper/pve-root ro intel_iommu=on iommu=pt vfio-pci.ids=10de:2489,10de:228b default_hugepagesz=1G hugepagesz=1G hugepages=8 quiet
```

- hugepages 확인
```bash
$ cat /proc/meminfo | grep -i huge
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
FileHugePages:         0 kB
HugePages_Total:       8
HugePages_Free:        8
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:    1048576 kB
Hugetlb:         8388608 kB
```


---

References
- https://colorscale.notion.site/colorscale-gaming-ai-pc
- https://pve.proxmox.com/wiki/PCI_Passthrough
- https://docs.redhat.com/ko/documentation/red_hat_enterprise_linux/7/html/virtualization_deployment_and_administration_guide/sect-iommu-deep-dive