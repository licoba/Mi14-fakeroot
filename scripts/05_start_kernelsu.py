from __future__ import annotations

import argparse
from pathlib import Path

from common import REPO_ROOT, require_tool, run
from mqsas import build_kernelsu_late_load_args


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Push ksud and start KernelSU late-load through miui.mqsas.IMQSNative."
    )
    parser.add_argument("--ksud-path", default=str(REPO_ROOT / "bin" / "ksud"))
    parser.add_argument("--remote-path", default="/data/local/tmp/ksud")
    parser.add_argument("--log-path", default="/sdcard/ksulog.txt")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--execute", action="store_true", help="Actually push ksud and call late-load.")
    args = parser.parse_args()

    require_tool("adb")

    ksud_path = Path(args.ksud_path)
    if not ksud_path.exists():
        print(f"[缺失] {ksud_path}")
        print("仓库里没有 ksud，请先确认 bin/ksud 是否存在。")
        if args.execute:
            return 1

    rc = run(["adb", "push", str(ksud_path), args.remote_path], execute=args.execute)
    if rc != 0:
        return rc

    rc = run(["adb", "shell", "chmod", "777", args.remote_path], execute=args.execute)
    if rc != 0:
        return rc

    rc = run(build_kernelsu_late_load_args(args.remote_path, args.log_path, args.timeout), execute=args.execute)
    if rc != 0:
        return rc

    rc = run(["adb", "shell", f"cat {args.log_path} 2>/dev/null"], execute=args.execute)
    if rc != 0:
        return rc

    if not args.execute:
        print("\nDry-run only. Add --execute to push ksud and call late-load.")
    else:
        print("\nReopen KernelSU Manager on the phone and grant Shell root permission if prompted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
