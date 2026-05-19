from __future__ import annotations

import subprocess

from common import adb_shell, print_cmd, require_tool


PROPS = [
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


def main() -> int:
    require_tool("adb")

    print_cmd(["adb", "devices"])
    subprocess.run(["adb", "devices"], check=False)

    for command in PROPS:
        print()
        adb_shell(command, execute=True)

    print("\nExpected for Xiaomi 14: ro.product.device is usually 'houji'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

