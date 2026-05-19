from __future__ import annotations

import argparse

from common import require_tool, run
from mqsas import build_service_args


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SELinux and MQSAS root-like execution.")
    parser.add_argument("--execute", action="store_true", help="Actually run adb commands.")
    args = parser.parse_args()

    require_tool("adb")

    rc = run(["adb", "shell", "getenforce"], execute=args.execute)
    if rc != 0:
        return rc

    print("\nChecking root-like command execution through miui.mqsas.IMQSNative...")
    service_args = build_service_args(
        command="whoami",
        arguments="",
        output="/sdcard/mqsas-whoami.txt",
        timeout=60,
    )
    rc = run(service_args, execute=args.execute)
    if rc != 0:
        return rc

    rc = run(["adb", "shell", "cat /sdcard/mqsas-whoami.txt 2>/dev/null"], execute=args.execute)
    if rc != 0:
        return rc

    if not args.execute:
        print("\nDry-run only. Add --execute to run the checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
