>[!info] Link
>- 

---

### 개요
- GPU 할당을 위해 생성한 VM에서 NVIDIA GPU를 인식하고 사용할 수 있도록 설정합니다.

## 1. GPU 제어 드라이버 확인
```bash
lspci -nnk | grep -i -A3 nvidia
01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3060 Ti Lite Hash Rate] [10de:2489] (rev a1)
	Subsystem: Gigabyte Technology Co., Ltd GA104 [GeForce RTX 3060 Ti Lite Hash Rate] [1458:405a]
	Kernel driver in use: nouveau
	Kernel modules: nvidiafb, nouveau
01:00.1 Audio device [0403]: NVIDIA Corporation GA104 High Definition Audio Controller [10de:228b] (rev a1)
	Subsystem: Gigabyte Technology Co., Ltd GA104 High Definition Audio Controller [1458:405a]
	Kernel driver in use: snd_hda_intel
	Kernel modules: snd_hda_intel
```
- RTX 3060 Ti를 NVIDIA가 아닌 `nouveau`가  제어 중인 상태입니다.
- 부팅 시, 오픈소스 nouveau 드라이버가 자동 로드됐고, 현재 NVIDIA 공식 드라이버는 로드되지 않은 상태입니다.
- 즉, VM이 패스스루 GPU를 단순 VGA 장치로만 인식하고 있는 상태입니다.

Ubuntu 24.04는 다음 특징이 있습니다
- 부팅 시 nouveau를 자동 로드합니다.
- NVIDIA GPU를 감지하면 nouveau가 먼저 올라갑니다.
- 패스스루 환경에서도 동일하게 nouveau가 먼저 장치를 잡아버리고, NVIDIA 드라이버가 해당 GPU를 사용하지 못합니다.
- 따라서, 이를 방지하기 위해 VM 내부에서 nouveau를 블랙리스트 처리한 뒤 NVIDIA 드라이버를 재설치해야 합니다.

## 2. nouveau 블랙리스트 처리
```bash
$ vi /etc/modprobe.d/blacklist-nouveau.conf
blacklist nouveau
options nouveau modeset=0
```

### 3. initramfs 업데이트  및 재부팅
```bash
$ sudo update-initramfs -u
$ sudo reboot
```

#### 확인
```bash
$ lspci -nnk | grep -i -A3 nvidia
01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3060 Ti Lite Hash Rate] [10de:2489] (rev a1)
	Subsystem: Gigabyte Technology Co., Ltd GA104 [GeForce RTX 3060 Ti Lite Hash Rate] [1458:405a]
	Kernel modules: nvidiafb, nouveau
```

```bash
01:00.1 Audio device [0403]: NVIDIA Corporation GA104 High Definition Audio Controller [10de:228b] (rev a1)
	Subsystem: Gigabyte Technology Co., Ltd GA104 High Definition Audio Controller [1458:405a]
	Kernel driver in use: snd_hda_intel
	Kernel modules: snd_hda_intel
```

- 블랙리스트에 의해서 `nouveau` 모듈이 3060 Ti 제어 드라이버로 설정되지 않은 것을 확인 가능합니다.

## 4. Hugepages 설정
- 확인
```bash
cat /proc/meminfo | grep -i huge
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
FileHugePages:     53248 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
Hugetlb:               0 kB
```

- hugepages 설정
```bash
$ vi /etc/default/grub

# 다음과 같이 변경
GRUB_CMDLINE_LINUX="default_hugepagesz=1G hugepagesz=1G hugepages=8"
```

```bash
$ sudo reboot
```

### 확인
```bash
$ cat /proc/cmdline
BOOT_IMAGE=/vmlinuz-6.14.0-35-generic root=UUID=84953c0e-91e7-4b00-9bf5-079396d7dcef ro default_hugepagesz=1G hugepagesz=1G hugepages=8 quiet splash vt.handoff=7
```

```bash
$ cat /proc/meminfo | grep -i huge
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
FileHugePages:         0 kB
HugePages_Total:       5
HugePages_Free:        5
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:    1048576 kB
Hugetlb:         5242880 kB
```
- 부팅 파라미터로서 hugepage는 정상적으로 반영됐으나, 전체 8GB 메모리 중에 시스텀에서 3GB 정도의 메모리를 차지하고, 남은 약 5GB 에 대해서 hugepages 가 적용된 것으로 추정됩니다.

## 5. NVIDIA 드라이버 설치
- 현재 상태 확인
```bash
$ nvidia-smi
Command 'nvidia-smi' not found, but can be installed with:
apt install nvidia-utils-470         # version 470.256.02-0ubuntu0.24.04.1, or
apt install nvidia-utils-470-server  # version 470.256.02-0ubuntu0.24.04.1
apt install nvidia-utils-535         # version 535.274.02-0ubuntu0.24.04.2
apt install nvidia-utils-535-server  # version 535.274.02-0ubuntu0.24.04.2
apt install nvidia-utils-565-server  # version 565.57.01-0ubuntu0.24.04.3
apt install nvidia-utils-570         # version 570.195.03-0ubuntu0.24.04.1
apt install nvidia-utils-570-server  # version 570.195.03-0ubuntu0.24.04.2
apt install nvidia-utils-580         # version 580.95.05-0ubuntu0.24.04.2
apt install nvidia-utils-580-server  # version 580.95.05-0ubuntu0.24.04.2
apt install nvidia-utils-525         # version 525.147.05-0ubuntu1
apt install nvidia-utils-525-server  # version 525.147.05-0ubuntu1
apt install nvidia-utils-550-server  # version 550.163.01-0ubuntu0.24.04.1
```

- 시스템에서 안내하는 드라이버  중 운영체제에 맞는 드라이버를 설치합니다.
```bash
$ apt install nvidia-utils-565-server
```

- 현재 GPU를 제어하는 드라이버가 없으므로, 재부팅함으로써 NVIDIA 드라이버가 GPU를 제어하도록 합니다.
```bash
$ reboot
```

- 재부팅 후에도 동작하지 않는 상태입니다. 드라이버가 호환되지 않는 것으로 추정됩니다.
```bash
$ nvidia-smi
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver. Make sure that the latest NVIDIA driver is installed and running.
```

### 재설치
```bash
$ sudo apt install linux-headers-$(uname -r) build-essential
```

- 최적의 버전을 자동 설치
```bash
$ sudo ubuntu-drivers autoinstall
```

- 재부팅함으로써 NVIDIA 드라이버가 GPU를 제어하도록 합니다.
```bash
$ reboot
```

### 확인
- `Driver Version: 580.95.05` 이 설치된 것을 확인할 수 있습니다. 이제 AI 추론을 위한 VM에서의 GPU 사용 환경 구축이 완료됐습니다.
```bash
$ nvidia-smi
Sat Nov 15 20:37:08 2025
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.95.05              Driver Version: 580.95.05      CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 3060 Ti     Off |   00000000:01:00.0 Off |                  N/A |
|  0%   41C    P8             14W /  220W |      15MiB /   8192MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A            1249      G   /usr/lib/xorg/Xorg                        4MiB |
+-----------------------------------------------------------------------------------------+
```




---

# References
- 