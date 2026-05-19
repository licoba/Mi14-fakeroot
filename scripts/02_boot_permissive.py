from __future__ import annotations

import argparse

from common import require_tool, run


OEM_COMMANDS = ("set-gpu-preemption", "set-gpu-preemption-value", "set-hw-fence-value")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject androidboot.selinux=permissive through fastboot OEM command."
    )
    parser.add_argument("--oem-command", choices=OEM_COMMANDS, default="set-gpu-preemption")
    parser.add_argument("--execute", action="store_true", help="Actually run fastboot commands.")
    args = parser.parse_args()

    require_tool("fastboot")

    print("This step must be run while the phone is in fastboot mode.\n")

    rc = run(["fastboot", "devices"], execute=args.execute)
    if rc != 0:
        return rc

    command = [
        "fastboot",
        "oem",
        args.oem_command,
        "0",
        "androidboot.selinux=permissive",
    ]
    rc = run(command, execute=args.execute)
    if rc != 0:
        return rc

    rc = run(["fastboot", "continue"], execute=args.execute)
    if rc != 0:
        return rc

    if not args.execute:
        print("\nDry-run only. Add --execute to run the commands.")
    else:
        print("\nAfter Android boots, run scripts/04_check_temp_root.py --execute.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

