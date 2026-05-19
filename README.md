# Xiaomi 14 locked-BL temporary root notes

目标设备：小米 14 / `houji` / Snapdragon 8 Gen 3 / HyperOS，未解锁 Bootloader。

这个项目整理的是 Mobile01 文章和其他公开讨论里的“临时 root / root-like 命令执行”链路：

1. 在 fastboot 里利用 Qualcomm ABL 参数注入，把本次启动的 SELinux 切到 `permissive`。
2. 回到系统后，通过 Xiaomi/MIUI 的 `miui.mqsas.IMQSNative` binder 服务执行 `ksud late-load`。
3. KernelSU 管理器接管后，再在手机上给 shell 授权。

这不是 Magisk，也不是持久 root。重启后通常会恢复；每次需要 root-like 命令执行时都要重新确认环境。

## 风险

- 这些是漏洞利用步骤，只适合你自己的设备和可接受数据丢失风险的测试环境。
- TUI 默认是真实执行模式；选择菜单项就表示同意执行该步骤。
- 单独运行的底层脚本仍默认 dry-run；真正执行需要显式加 `--execute`。
- 不提供写入 `abl`、`efisp`、`boot`、`init_boot` 等分区的脚本。
- 如果系统安全补丁已经修复，命令可能无效。

## 项目结构

```text
scripts/
  00_check_tools.py           检查 adb / fastboot
  01_detect_device.py         读取设备型号、补丁日期、SELinux、MQSAS 服务
  02_boot_permissive.py       fastboot 阶段注入 SELinux permissive 参数
  03_mqsas_root_command.py    通过 IMQSNative 执行单条 root 权限命令
  04_check_temp_root.py       验证 getenforce / whoami
  05_start_kernelsu.py        按 Mobile01 流程 push ksud 并 late-load
  one_click_tui.py            一键交互式 TUI 总入口
  common.py                   Python 脚本共享工具
  mqsas.py                    MQSAS service call 参数构造
bin/
  KernelSU_v3.2.4_32457-release.apk  KernelSU 管理器 APK
  ksud                         从官方 APK 提取的 arm64 ksud
  ksuinit                      KernelSU 官方 release 文件
  README.md                    外部文件来源和 SHA256
docs/
  SOURCES.md                  搜索到的资料和判断
```

## 准备

1. Windows 安装 Android Platform Tools，并确保 `adb.exe` 和 `fastboot.exe` 在 `PATH`。
2. 手机打开开发者选项：
   - USB 调试
   - USB 调试（安全设置）如果系统提供该项
3. 用 USB 连接手机，手机上允许本电脑调试。

## TUI 一键执行

推荐直接用 TUI：

```shell
python .\scripts\one_click_tui.py
```

TUI 默认是真实执行模式。你选择菜单项，就表示同意执行该步骤。

TUI 会让你选择本次要操作的 ADB 设备；即使只发现 1 台设备，也需要你确认。完整向导里只在开始选择一次设备，进入 fastboot 后会优先沿用同一个序列号；只有无法匹配时才会再次要求选择 fastboot 设备。选定后，后续命令会自动带上对应的 `-s <serial>`。如果没有发现设备，当前步骤会明显报错并停止。

如果只想预览命令，不执行，可以启动时加：

```shell
python .\scripts\one_click_tui.py --dry-run
```

真实执行模式下，脚本不会再对每条 adb/fastboot 命令逐个确认。

完整向导支持从中途继续：如果当前已经是 `Permissive`，会跳过重启 fastboot 和注入步骤，直接继续 KernelSU late-load；如果 KernelSU 管理器已经安装，也会跳过安装。Android 开机后如果 `getenforce` 不是 `Permissive`，会停止 KernelSU late-load，避免继续执行必定失败的 MQSAS 步骤；这时请在菜单里切换备用 OEM 命令后重新注入。

## 单独脚本只读检测

也可以不用 TUI，单独运行脚本：

```shell
python .\scripts\00_check_tools.py
python .\scripts\01_detect_device.py
```

重点看：

- `ro.product.device` 是否为 `houji`
- `ro.product.model` 是否为 Xiaomi 14
- `getenforce` 当前通常应为 `Enforcing`
- `service check miui.mqsas.IMQSNative` 是否能看到服务

## 进入临时 SELinux permissive

先重启到 fastboot：

```shell
adb reboot bootloader
```

先 dry-run 看命令：

```shell
python .\scripts\02_boot_permissive.py
```

确认后执行：

```shell
python .\scripts\02_boot_permissive.py --execute
```

脚本默认使用公开资料里针对 Xiaomi 14/SM8650 常见的：

```text
fastboot oem set-gpu-preemption 0 androidboot.selinux=permissive
fastboot continue
```

如果你的 fastboot 报 unknown command，可以试备用 OEM 命令名：

```shell
python .\scripts\02_boot_permissive.py --oem-command set-gpu-preemption-value --execute
python .\scripts\02_boot_permissive.py --oem-command set-hw-fence-value --execute
```

## 按 Mobile01 流程启动 KernelSU 临时 root

仓库已经内置 KernelSU 管理器 APK 和 `bin/ksud`。TUI 里可以直接选择“安装 KernelSU 管理器 APK”和“启动 KernelSU late-load”。安装和 late-load 后，TUI 会尝试自动打开 KernelSU 管理器。

先 dry-run：

```shell
python .\scripts\05_start_kernelsu.py
```

确认后执行：

```shell
python .\scripts\05_start_kernelsu.py --execute
```

成功后重新打开 KernelSU 管理器，给 Shell root 权限。按原文思路，拿到 root 后可恢复 SELinux enforcing：

```shell
adb shell su -c setenforce 1
```

## 验证临时 root-like 命令执行

手机开机并重新授权 ADB 后，先 dry-run：

```shell
python .\scripts\04_check_temp_root.py
```

确认后执行：

```shell
python .\scripts\04_check_temp_root.py --execute
```

它会检查：

- `adb shell getenforce`
- 通过 `miui.mqsas.IMQSNative` 执行 `whoami`
- 读取 `/sdcard/mqsas-whoami.txt`
- 多路检查 `su` / KernelSU 常见路径，例如 `/data/adb/ksu/bin/su`
- 读取 KernelSU 管理器界面；如果显示“工作中 <LKM> / 越狱模式”，也判定 KernelSU 已加载成功

如果任一路输出包含 `uid=0` 或 `root`，说明 root 可用。`getenforce` 回到 `Enforcing` 不一定代表 root 失败，因为 KernelSU late-load 后可能已经接管 root，再恢复 SELinux 状态。

## 执行自定义 root 命令

示例：读取 root 身份：

```shell
python .\scripts\03_mqsas_root_command.py --command whoami --output /sdcard/mqsas-whoami.txt --execute
```

示例：执行带参数命令：

```shell
python .\scripts\03_mqsas_root_command.py --command id --output /sdcard/mqsas-id.txt --execute
```

命令模板来自公开资料：

```text
adb shell service call miui.mqsas.IMQSNative 21 i32 1 s16 "<命令>" i32 1 s16 "<参数列表>" s16 "<输出路径>" i32 <超时秒数>
```

## 失败排查

- `miui.mqsas.IMQSNative doesn't exist`：可能该机型/版本没有服务，或者 USB 调试授权不完整，或者系统已修复。
- `getenforce` 仍是 `Enforcing`：fastboot 注入没有生效，试备用 OEM 命令名，或说明补丁已修。
- `service: unknown option /sdcard/...`：旧版本脚本的 MQSAS 空参数引用问题；现在已改成单条远端 shell 命令。更新后重新执行即可。
- `whoami` 输出不是 `root`：MQSAS 链路不可用或 SELinux 没有 permissive；如果 KernelSU 已生效，以 TUI 的多路 root 检测结果为准。
- `su: inaccessible or not found`：`su` 可能不在 PATH，TUI 会继续尝试 `/data/adb/ksu/bin/su`、`/debug_ramdisk/su` 等常见路径。
- 执行后没有输出文件：检查输出路径是否可写，先用 `/sdcard/...`。

## 恢复

通常重启即可恢复 SELinux enforcing：

```shell
adb reboot
```

重启后再运行：

```shell
adb shell getenforce
```
