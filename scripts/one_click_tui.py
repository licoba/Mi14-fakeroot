from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from common import REPO_ROOT, print_cmd, require_tool
from mqsas import build_kernelsu_late_load_args, build_service_args


OEM_COMMANDS = ("set-gpu-preemption", "set-gpu-preemption-value", "set-hw-fence-value")
BIN_DIR = REPO_ROOT / "bin"
KSUD_LOCAL = BIN_DIR / "ksud"
KERNELSU_APK = BIN_DIR / "KernelSU_v3.2.4_32457-release.apk"
KSUD_REMOTE = "/data/local/tmp/ksud"
KSU_LOG = "/sdcard/ksulog.txt"
KERNELSU_PACKAGE = "me.weishu.kernelsu"
KSU_UI_XML = "/sdcard/ksu-ui.xml"


@dataclass
class Device:
    serial: str
    state: str
    label: str = ""


class App:
    def __init__(self, execute: bool, oem_command: str) -> None:
        self.execute = execute
        self.oem_command = oem_command
        self.adb_serial: str | None = None
        self.fastboot_serial: str | None = None

    def clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def pause(self) -> None:
        try:
            input("\n按 Enter 返回菜单...")
        except EOFError:
            pass

    def ask_yes(self, prompt: str, default: bool = False) -> bool:
        suffix = "Y/n" if default else "y/N"
        answer = input(f"{prompt} [{suffix}] ").strip().lower()
        if not answer:
            return default
        return answer in ("y", "yes", "是", "确认", "好", "执行")

    def guarded_run(self, args: list[str], label: str | None = None, force_execute: bool | None = None) -> int:
        execute = self.execute if force_execute is None else force_execute
        if label:
            print(f"\n[{label}]")
        print_cmd(args)
        if not execute:
            print("(预览模式，不执行)")
            return 0
        return subprocess.run(args, check=False).returncode

    def capture_run(self, args: list[str], label: str | None = None, force_execute: bool | None = None) -> str:
        execute = self.execute if force_execute is None else force_execute
        if label:
            print(f"\n[{label}]")
        print_cmd(args)
        if not execute:
            print("(预览模式，不执行)")
            return ""
        result = subprocess.run(args, check=False, capture_output=True, text=True)
        output = (result.stdout or "") + (result.stderr or "")
        if output.strip():
            print(output.rstrip())
        if result.returncode != 0:
            raise RuntimeError(f"命令执行失败，退出码：{result.returncode}")
        return output.strip()

    def capture_run_no_fail(self, args: list[str], label: str | None = None) -> tuple[int, str]:
        if label:
            print(f"\n[{label}]")
        print_cmd(args)
        if not self.execute:
            print("(预览模式，不执行)")
            return 0, ""
        result = subprocess.run(args, check=False, capture_output=True, text=True)
        output = (result.stdout or "") + (result.stderr or "")
        if output.strip():
            print(output.rstrip())
        return result.returncode, output.strip()

    def check_shell_output(self, command: str, label: str) -> str:
        return self.capture_run(self.adb_args(["shell", command]), label)

    def adb_args(self, rest: list[str]) -> list[str]:
        if self.adb_serial:
            return ["adb", "-s", self.adb_serial, *rest]
        return ["adb", *rest]

    def fastboot_args(self, rest: list[str]) -> list[str]:
        serial = self.fastboot_serial or self.adb_serial
        if serial:
            return ["fastboot", "-s", serial, *rest]
        return ["fastboot", *rest]

    def list_adb_devices(self) -> list[Device]:
        require_tool("adb")
        result = subprocess.run(["adb", "devices", "-l"], check=False, capture_output=True, text=True)
        devices: list[Device] = []
        for line in result.stdout.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            serial = parts[0]
            state = parts[1] if len(parts) > 1 else "unknown"
            label = " ".join(parts[2:])
            devices.append(Device(serial=serial, state=state, label=label))
        return devices

    def list_fastboot_devices(self) -> list[Device]:
        require_tool("fastboot")
        result = subprocess.run(["fastboot", "devices"], check=False, capture_output=True, text=True)
        devices: list[Device] = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if not parts:
                continue
            serial = parts[0]
            state = parts[1] if len(parts) > 1 else "fastboot"
            devices.append(Device(serial=serial, state=state))
        return devices

    def choose_adb_device(self) -> None:
        devices = self.list_adb_devices()
        if not devices:
            self.adb_serial = None
            raise RuntimeError("没有发现 ADB 设备。请确认 USB 调试已打开，并在手机上允许本电脑调试。")

        if len(devices) == 1:
            print("\n发现 1 台 ADB 设备，请确认是否操作这台设备：")
        else:
            print("\n发现多台 ADB 设备，请选择本次要操作的小米 14：")
        for idx, dev in enumerate(devices, start=1):
            current = "（当前）" if dev.serial == self.adb_serial else ""
            print(f"{idx}. {dev.serial}  {dev.state}  {dev.label} {current}".rstrip())
        choice = input("请选择设备编号，输入 0 取消：").strip()
        if choice == "0":
            raise RuntimeError("已取消选择 ADB 设备。")
        if not choice.isdigit() or not (1 <= int(choice) <= len(devices)):
            raise RuntimeError("ADB 设备选择无效。")
        self.adb_serial = devices[int(choice) - 1].serial
        print(f"已选择 ADB 设备：{self.adb_serial}")

    def choose_fastboot_device(self) -> None:
        devices = self.list_fastboot_devices()
        if not devices:
            self.fastboot_serial = None
            raise RuntimeError("没有发现 fastboot 设备。请确认手机已经进入 fastboot 画面。")

        if len(devices) == 1:
            print("\n发现 1 台 fastboot 设备，请确认是否操作这台设备：")
        else:
            print("\n发现多台 fastboot 设备，请选择本次要操作的小米 14：")
        for idx, dev in enumerate(devices, start=1):
            current = "（当前）" if dev.serial == self.fastboot_serial else ""
            print(f"{idx}. {dev.serial}  {dev.state} {current}".rstrip())
        choice = input("请选择设备编号，输入 0 取消：").strip()
        if choice == "0":
            raise RuntimeError("已取消选择 fastboot 设备。")
        if not choice.isdigit() or not (1 <= int(choice) <= len(devices)):
            raise RuntimeError("fastboot 设备选择无效。")
        self.fastboot_serial = devices[int(choice) - 1].serial
        print(f"已选择 fastboot 设备：{self.fastboot_serial}")

    def select_fastboot_after_reboot(self) -> None:
        devices = self.list_fastboot_devices()
        if not devices:
            self.fastboot_serial = None
            raise RuntimeError("没有发现 fastboot 设备。请确认手机已经进入 fastboot 画面。")

        if self.adb_serial:
            for dev in devices:
                if dev.serial == self.adb_serial:
                    self.fastboot_serial = dev.serial
                    print(f"\nfastboot 设备与已选择的 ADB 设备匹配：{self.fastboot_serial}")
                    return

        if len(devices) == 1:
            self.fastboot_serial = devices[0].serial
            print(f"\n发现 1 台 fastboot 设备，已沿用：{self.fastboot_serial}")
            return

        print("\n进入 fastboot 后无法自动匹配原设备，请选择本次要操作的小米 14：")
        for idx, dev in enumerate(devices, start=1):
            print(f"{idx}. {dev.serial}  {dev.state}".rstrip())
        choice = input("请选择设备编号，输入 0 取消：").strip()
        if choice == "0":
            raise RuntimeError("已取消选择 fastboot 设备。")
        if not choice.isdigit() or not (1 <= int(choice) <= len(devices)):
            raise RuntimeError("fastboot 设备选择无效。")
        self.fastboot_serial = devices[int(choice) - 1].serial
        print(f"已选择 fastboot 设备：{self.fastboot_serial}")

    def preflight(self) -> None:
        print("\n正在检查本机 adb / fastboot...")
        for tool in ("adb", "fastboot"):
            path = require_tool(tool)
            print(f"[正常] {tool} => {path}")
        print()
        self.guarded_run(["adb", "devices", "-l"], "查看 ADB 设备", force_execute=True)
        self.choose_adb_device()

    def detect_device(self) -> None:
        commands = [
            "getprop ro.product.manufacturer",
            "getprop ro.product.model",
            "getprop ro.product.device",
            "getprop ro.product.name",
            "getprop ro.build.version.release",
            "getprop ro.build.version.incremental",
            "getprop ro.build.version.security_patch",
            "getprop ro.boot.verifiedbootstate",
            "getprop ro.boot.flash.locked",
            "getenforce",
            "service check miui.mqsas.IMQSNative",
        ]
        print("\n正在读取手机信息。重点看 device 是否是 houji、安全补丁日期、SELinux、MQSAS 服务。")
        if not self.adb_serial:
            self.choose_adb_device()
        for command in commands:
            self.guarded_run(self.adb_args(["shell", command]), command, force_execute=True)

    def install_kernelsu_manager(self) -> None:
        if not KERNELSU_APK.exists():
            print(f"\n[缺失] {KERNELSU_APK}")
            print("仓库里没有 KernelSU 管理器 APK。")
            return
        print("\n这一步会把仓库里的 KernelSU 管理器 APK 安装到手机。")
        if not self.adb_serial:
            self.choose_adb_device()
        if self.execute and self.is_package_installed(KERNELSU_PACKAGE):
            print("KernelSU 管理器已经安装，跳过安装。")
            self.open_kernelsu_manager()
            return
        self.guarded_run(self.adb_args(["install", "-r", str(KERNELSU_APK)]), "安装 KernelSU 管理器")
        self.open_kernelsu_manager()

    def is_package_installed(self, package_name: str) -> bool:
        output = self.capture_run(
            self.adb_args(["shell", f"pm path {package_name} 2>/dev/null"]),
            f"检查 {package_name} 是否已安装",
        )
        return package_name in output

    def open_kernelsu_manager(self) -> None:
        if not self.adb_serial:
            self.choose_adb_device()
        self.guarded_run(
            self.adb_args(["shell", "monkey", "-p", KERNELSU_PACKAGE, "-c", "android.intent.category.LAUNCHER", "1"]),
            "打开 KernelSU 管理器",
        )

    def reboot_bootloader(self) -> None:
        if not self.adb_serial:
            self.choose_adb_device()
        self.guarded_run(self.adb_args(["reboot", "bootloader"]), "重启到 fastboot")
        print("\n等手机屏幕进入 fastboot 画面后，再继续后续步骤。")

    def choose_oem_command(self) -> None:
        print("\n可选 OEM 命令：")
        for idx, command in enumerate(OEM_COMMANDS, start=1):
            marker = "（当前）" if command == self.oem_command else ""
            print(f"{idx}. {command}{marker}")
        choice = input("请选择 OEM 命令 [默认 1]: ").strip()
        if not choice:
            self.oem_command = OEM_COMMANDS[0]
            return
        if not choice.isdigit() or not (1 <= int(choice) <= len(OEM_COMMANDS)):
            print("选择无效，保持当前设置。")
            return
        self.oem_command = OEM_COMMANDS[int(choice) - 1]

    def boot_permissive(self) -> None:
        print("\n这一步必须在手机已经处于 fastboot 模式时执行。")
        self.guarded_run(["fastboot", "devices"], "查看 fastboot 设备")
        if not self.fastboot_serial:
            self.choose_fastboot_device()
        self.guarded_run(
            self.fastboot_args([
                "oem",
                self.oem_command,
                "0",
                "androidboot.selinux=permissive",
            ]),
            "注入 SELinux permissive 启动参数",
        )
        self.guarded_run(self.fastboot_args(["continue"]), "继续启动系统")
        print("\n等 Android 完全开机，并在手机上重新允许 ADB 调试。")

    def wait_for_adb(self) -> None:
        self.guarded_run(self.adb_args(["wait-for-device"]), "等待 ADB 连接")
        self.ensure_selinux_permissive()

    def ensure_selinux_permissive(self) -> None:
        state = self.get_selinux_state("查看当前 SELinux 状态")
        if not self.execute:
            return
        if "Permissive" not in state:
            raise RuntimeError(
                "当前 SELinux 不是 Permissive，MQSAS/KernelSU late-load 不能继续。"
                "请重新进入 fastboot，并在菜单 12 里换一个 OEM 命令后再执行注入步骤。"
            )

    def get_selinux_state(self, label: str = "查看 SELinux") -> str:
        return self.capture_run(self.adb_args(["shell", "getenforce"]), label)

    def is_selinux_permissive(self) -> bool:
        if not self.execute:
            return False
        return "Permissive" in self.get_selinux_state("检查当前 SELinux 是否已是 Permissive")

    def start_kernelsu(self) -> None:
        if not KSUD_LOCAL.exists():
            print(f"\n[缺失] {KSUD_LOCAL}")
            print("仓库里没有 ksud，不能继续执行 KernelSU late-load。")
            return

        print("\n这一步会把 ksud 推送到 /data/local/tmp/，然后通过 MQSAS 执行 late-load。")
        if not self.adb_serial:
            self.choose_adb_device()
        self.ensure_selinux_permissive()
        self.guarded_run(self.adb_args(["push", str(KSUD_LOCAL), KSUD_REMOTE]), "推送 ksud")
        self.guarded_run(self.adb_args(["shell", "chmod", "777", KSUD_REMOTE]), "给 ksud 执行权限")
        self.guarded_run(self.adb_args(["shell", f"rm -f {KSU_LOG}"]), "清理旧 KernelSU 日志")
        self.guarded_run(
            self.adb_args(build_kernelsu_late_load_args(KSUD_REMOTE, KSU_LOG, 60)[1:]),
            "通过 MQSAS 启动 KernelSU late-load",
        )
        self.guarded_run(self.adb_args(["shell", f"cat {KSU_LOG} 2>/dev/null"]), "读取 KernelSU 日志")
        self.open_kernelsu_manager()
        print("\n我已经尝试打开 KernelSU 管理器。如果手机上弹出 Shell 授权，请允许。")

    def read_kernelsu_ui(self) -> str:
        self.open_kernelsu_manager()
        self.guarded_run(self.adb_args(["shell", f"uiautomator dump {KSU_UI_XML} >/dev/null"]), "读取 KernelSU 界面文本")
        return self.capture_run(self.adb_args(["shell", f"cat {KSU_UI_XML} 2>/dev/null"]), "分析 KernelSU 界面")

    def verify_root(self) -> None:
        print("\n开始验证 SELinux 和 root 权限。")
        if not self.adb_serial:
            self.choose_adb_device()
        state = self.get_selinux_state("查看 SELinux")
        if "Permissive" in state or not self.execute:
            self.guarded_run(
                self.adb_args(build_service_args("whoami", "", "/sdcard/mqsas-whoami.txt", 60)[1:]),
                "通过 MQSAS 执行 whoami",
            )
            self.guarded_run(self.adb_args(["shell", "cat /sdcard/mqsas-whoami.txt 2>/dev/null"]), "读取 MQSAS 输出")
        else:
            print("SELinux 当前是 Enforcing；这不等于 root 失败，继续用 KernelSU / su 多路检测。")

        checks = [
            ("检查 PATH 里的 su", "command -v su 2>/dev/null || true"),
            ("检查 KernelSU su 路径", "ls -l /data/adb/ksu/bin/su /debug_ramdisk/su /system/bin/su /system/xbin/su 2>/dev/null || true"),
            ("su -c id", "su -c id"),
            ("/data/adb/ksu/bin/su -c id", "/data/adb/ksu/bin/su -c id"),
            ("/debug_ramdisk/su -c id", "/debug_ramdisk/su -c id"),
            ("/system/bin/su -c id", "/system/bin/su -c id"),
            ("ksud --help", f"{KSUD_REMOTE} --help"),
            ("ksud version", f"{KSUD_REMOTE} --version"),
        ]

        root_ok = False
        ui_output = self.read_kernelsu_ui()
        if "工作中" in ui_output and ("LKM" in ui_output or "越狱模式" in ui_output):
            print("\nKernelSU 管理器显示：工作中 <LKM> / 越狱模式。")
            root_ok = True

        for label, command in checks:
            _, output = self.capture_run_no_fail(self.adb_args(["shell", command]), label)
            lowered = output.lower()
            if "uid=0" in lowered or lowered.strip() == "root" or "uid=0(root)" in lowered:
                root_ok = True

        if root_ok:
            print("\n验证结果：检测到 root 权限可用。")
        else:
            print("\n验证结果：没有从 ADB shell 检测到可用 root。")
            print("如果 KernelSU 管理器里已经显示 root，请确认是否给 Shell 授权；")
            print("也可能是 su 不在 PATH，需要用上面输出里的实际 su 路径执行。")

    def restore_enforcing(self) -> None:
        print("\n这一步会尝试把 SELinux 恢复为 Enforcing。需要 su 已经可用。")
        if not self.adb_serial:
            self.choose_adb_device()
        self.guarded_run(self.adb_args(["shell", "su -c setenforce 1"]), "恢复 SELinux Enforcing")
        self.guarded_run(self.adb_args(["shell", "getenforce"]), "查看当前 SELinux 状态")

    def full_flow(self) -> None:
        print("\n完整向导流程：")
        print("1. 检查 adb / fastboot 和手机信息")
        print("2. 如果 KernelSU 管理器已安装则跳过安装")
        print("3. 如果当前已是 Permissive，则跳过 fastboot 注入")
        print("4. 否则重启到 fastboot 并注入 androidboot.selinux=permissive")
        print("5. 执行 KernelSU late-load")
        print("6. 验证 root")
        print("\n不会刷写 boot、init_boot、abl、efisp 等分区。")
        if self.execute and not self.ask_yes("开始完整执行吗？"):
            return
        self.preflight()
        self.detect_device()
        self.install_kernelsu_manager()

        if self.is_selinux_permissive():
            print("\n当前已经是 Permissive，跳过重启 fastboot 和注入步骤。")
        else:
            self.reboot_bootloader()
            input("\n手机进入 fastboot 画面后，按 Enter 继续...")
            self.select_fastboot_after_reboot()
            self.boot_permissive()
            input("\nAndroid 开机并允许 ADB 后，按 Enter 继续...")
            self.wait_for_adb()

        self.start_kernelsu()
        input("\n检查手机上的 KernelSU 管理器后，按 Enter 继续验证...")
        self.verify_root()

    def resource_status(self) -> str:
        apk = "已内置" if KERNELSU_APK.exists() else "缺失"
        ksud = "已内置" if KSUD_LOCAL.exists() else "缺失"
        return f"KernelSU APK: {apk} | ksud: {ksud}"

    def menu(self) -> None:
        while True:
            self.clear()
            print("小米 14 锁 BL 临时 Root 交互工具")
            print("=" * 42)
            print(f"当前模式：{'真实执行' if self.execute else '预览模式'}")
            print(f"ADB 设备：{self.adb_serial or '未选择'}")
            print(f"fastboot 设备：{self.fastboot_serial or '未选择'}")
            print(f"OEM 命令：{self.oem_command}")
            print(self.resource_status())
            print()
            print("1. 一键完整向导")
            print("2. 检查 adb / fastboot 和设备连接")
            print("3. 选择 ADB 设备")
            print("4. 读取手机信息")
            print("5. 安装 KernelSU 管理器 APK")
            print("6. 重启到 fastboot")
            print("7. 选择 fastboot 设备")
            print("8. 注入 SELinux permissive 并继续启动")
            print("9. 启动 KernelSU late-load")
            print("10. 验证 root")
            print("11. 恢复 SELinux Enforcing")
            print("12. 选择 OEM 命令")
            print("13. 打开 KernelSU 管理器")
            print("14. 切换预览模式 / 真实执行")
            print("0. 退出")

            try:
                choice = input("\n请选择：").strip()
            except EOFError:
                return
            try:
                if choice == "1":
                    self.full_flow()
                elif choice == "2":
                    self.preflight()
                elif choice == "3":
                    self.choose_adb_device()
                elif choice == "4":
                    self.detect_device()
                elif choice == "5":
                    self.install_kernelsu_manager()
                elif choice == "6":
                    self.reboot_bootloader()
                elif choice == "7":
                    self.choose_fastboot_device()
                elif choice == "8":
                    self.boot_permissive()
                elif choice == "9":
                    self.start_kernelsu()
                elif choice == "10":
                    self.verify_root()
                elif choice == "11":
                    self.restore_enforcing()
                elif choice == "12":
                    self.choose_oem_command()
                elif choice == "13":
                    self.open_kernelsu_manager()
                elif choice == "14":
                    if not self.execute:
                        print("\n真实执行模式会直接调用 adb / fastboot。你选择菜单项就表示同意执行该步骤。")
                        self.execute = self.ask_yes("切换到真实执行模式吗？")
                    else:
                        self.execute = False
                        print("已切回预览模式。")
                elif choice == "0":
                    return
                else:
                    print("选择无效。")
            except KeyboardInterrupt:
                print("\n已中断。")
            except SystemExit as exc:
                print(f"\n已停止，退出码：{exc.code}")
            except Exception as exc:
                print(f"\n发生错误：{exc}")
            self.pause()


def main() -> int:
    parser = argparse.ArgumentParser(description="小米 14 锁 BL 临时 root 交互工具。")
    parser.add_argument("--dry-run", action="store_true", help="启动后进入预览模式，只显示命令不执行。")
    parser.add_argument("--oem-command", choices=OEM_COMMANDS, default="set-gpu-preemption")
    args = parser.parse_args()

    app = App(execute=not args.dry_run, oem_command=args.oem_command)
    app.menu()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
