from __future__ import annotations

import subprocess
import sys

from common import require_tool


def main() -> int:
    ok = True
    for tool in ("adb", "fastboot"):
        try:
            path = require_tool(tool)
            print(f"[ok] {tool} => {path}")
        except SystemExit:
            ok = False

    if not ok:
        print("\nInstall Android Platform Tools, then add it to PATH.")
        return 1

    print("\nadb version:")
    subprocess.run(["adb", "version"], check=False)

    print("\nfastboot version:")
    subprocess.run(["fastboot", "--version"], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

