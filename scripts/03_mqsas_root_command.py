from __future__ import annotations

import argparse

from common import require_tool, run
from mqsas import build_service_args


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one root-like command through miui.mqsas.IMQSNative."
    )
    parser.add_argument("--command", default="whoami")
    parser.add_argument("--arguments", default="")
    parser.add_argument("--output", default="/sdcard/mqsas-root.txt")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--execute", action="store_true", help="Actually call adb service.")
    args = parser.parse_args()

    require_tool("adb")

    service_args = build_service_args(args.command, args.arguments, args.output, args.timeout)
    rc = run(service_args, execute=args.execute)
    if rc != 0:
        return rc

    rc = run(["adb", "shell", f"cat {args.output} 2>/dev/null"], execute=args.execute)
    if rc != 0:
        return rc

    if not args.execute:
        print("\nDry-run only. Add --execute to run the service call.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
