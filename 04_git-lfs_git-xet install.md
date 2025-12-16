---
index: 
tags: 
created: 2025-05-26 09:20
status: 
source_url:
---
>[!info] Link
>- 

---

공식문서
- https://github.com/git-lfs/git-lfs/blob/main/INSTALLING.md

```bash
$ curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
Detected operating system as Ubuntu/noble.
Checking for curl...
Detected curl...
Checking for gpg...
Detected gpg...
Detected apt version as 2.8.3
Running apt-get update... done.
Installing apt-transport-https... done.
Installing /etc/apt/sources.list.d/github_git-lfs.list...done.
Importing packagecloud gpg key... Packagecloud gpg key imported to /etc/apt/keyrings/github_git-lfs-archive-keyring.gpg
done.
Running apt-get update... done.

The repository is setup! You can now install packages.
```

```bash
$ apt-get install git-lfs
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following package was automatically installed and is no longer required:
  libllvm19
Use 'apt autoremove' to remove it.
The following packages will be upgraded:
  git-lfs
1 upgraded, 0 newly installed, 0 to remove and 153 not upgraded.
Need to get 8,927 kB of archives.
After this operation, 7,527 kB of additional disk space will be used.
Get:1 https://packagecloud.io/github/git-lfs/ubuntu noble/main amd64 git-lfs amd64 3.7.1 [8,927 kB]
Fetched 8,927 kB in 1s (6,161 kB/s)  
(Reading database ... 204428 files and directories currently installed.)
Preparing to unpack .../git-lfs_3.7.1_amd64.deb ...
Unpacking git-lfs (3.7.1) over (3.4.1-1ubuntu0.3) ...
Setting up git-lfs (3.7.1) ...
Git LFS initialized.
Processing triggers for man-db (2.12.0-4build2) ...
```


#### 확인
```bash
$ cat .gitconfig
[lfs]
        concurrenttransfers = 3
[lfs "customtransfer.xet"]
        path = git-xet
        args = transfer
        concurrent = true
```

## git-xet
- [xet tools v0.14.4 release notes](https://github.com/xetdata/xet-tools/releases)

```bash
$ wget https://github.com/xetdata/xet-tools/releases/download/v0.14.4/xet-linux-x86_64.deb

$ dpkg -i xet-linux-x86_64.deb 

$ git-xet --version
git-xet 0.14.4-febbf02
```


---

# References
- 