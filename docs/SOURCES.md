# Sources and notes

检索日期：2026-05-19

## 关键资料

- Mobile01: `[分享] 小米系列高通新的漏洞 不解鎖BL鎖 獲取臨時ROOT權限`
  - URL: https://www.mobile01.com/topicdetail.php?f=634&t=7237169
  - 关键信息：条件写明安全补丁在 `2026/02/01` 之前；手动流程是安装 KernelSU 管理器，fastboot 执行 `fastboot oem set-gpu-preemption 0 androidboot.selinux=permissive` 和 `fastboot continue`，开机后 push `ksud` 到 `/data/local/tmp/`，通过 `miui.mqsas.IMQSNative` 调用 `/data/local/tmp/ksud late-load`。

- HackMD: `近期被利用之「免解鎖 Bootloader 取得 Root」漏洞列表`
  - URL: https://hackmd.io/GXONfu7DR4iFzQ2RHpINcw
  - 关键信息：`houji | Xiaomi 14 | Snapdragon 8 Gen 3 | Android 14 | ABL Cmdline Injection | 已测试`；并记录 `miui.mqsas.IMQSNative` 服务调用模板。

- DroidWin: `Get Root Privileges on Xiaomi Without Bootloader Unlocking!`
  - URL: https://droidwin.com/get-root-privileges-on-xiaomi-without-bootloader-unlocking/
  - 关键信息：称该漏洞支持 Xiaomi 14/15 和 SM8650/SM8750，并给出 `fastboot oem set-gpu-preemption-value 0 androidboot.selinux=permissive`。

- Android Authority: `New Qualcomm GBL exploit brings bootloader unlocking to flagship Androids`
  - URL: https://www.androidauthority.com/qualcomm-snapdragon-8-elite-gbl-exploit-bootloader-unlock-3648651/
  - 关键信息：说明 fastboot OEM 参数注入可追加 `androidboot.selinux=permissive`，也提到 Qualcomm 已开始修补相关检查。

- Android Headlines: `Qualcomm GBL Exploit Reportedly Enables Bootloader Unlocking on Flagships`
  - URL: https://www.androidheadlines.com/2026/03/qualcomm-gbl-exploit-reportedly-enables-bootloader-unlocking-on-flagships.html
  - 关键信息：描述 ABL `set-gpu-preemption` 参数检查不严，导致 SELinux permissive 参数注入。

- MIUI Türkiye forum: `Xiaomi Cihazlarda Bootloader Açmadan Root`
  - URL: https://forum.miuiturkiye.net/konu/xiaomi-cihazlarda-bootloader-acmadan-root-adim-adim-rehber.160721/
  - 关键信息：给出 `miui.mqsas.IMQSNative` 执行 `whoami` 并把输出写入 `/sdcard/log.txt` 的验证方法。

- Mix Vale: `Critical flaw in HyperOS exposes 160 Xiaomi POCO and Redmi devices to malware invasion`
  - URL: https://www.mixvale.com.br/2026/03/16/critical-flaw-in-hyperos-exposes-160-xiaomi-poco-and-redmi-devices-to-malware-invasion-en/
  - 关键信息：报道 HyperOS 内部诊断服务 `miui.mqsas.IMQSNative` 可被 ADB 命令触发，造成 root-like 权限。

- GitHub: `kasnria001/qualcomm_gbl_exploit_poc`
  - URL: https://github.com/kasnria001/qualcomm_gbl_exploit_poc
  - 关键信息：这是 Xiaomi 17 / Snapdragon 8 Elite Gen 5 一类 GBL/EFISP Bootloader 解锁 PoC。它涉及写入 EFISP 分区，和 Xiaomi 14 临时 root 验证目标不同，本项目未引入该二进制和写分区流程。

## 当前判断

- Xiaomi 14 锁 BL 的公开路线不是刷 Magisk，而是 Mobile01 文中这类流程：
  1. ABL cmdline injection 让本次启动 SELinux permissive。
  2. MQSAS/IMQSNative 服务调用以 root 身份执行 `ksud late-load`。
  3. KernelSU 管理器接管后再授权 Shell。
- 该链路高度依赖系统版本和安全补丁日期。
- 对用户目标“等我来执行”，项目脚本全部默认 dry-run，只有传 `--execute` 才会调用 adb/fastboot。
