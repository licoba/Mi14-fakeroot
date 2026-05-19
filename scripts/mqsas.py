from __future__ import annotations


def build_service_args(command: str, arguments: str, output: str, timeout: int) -> list[str]:
    return [
        "adb",
        "shell",
        "service",
        "call",
        "miui.mqsas.IMQSNative",
        "21",
        "i32",
        "1",
        "s16",
        command,
        "i32",
        "1",
        "s16",
        arguments,
        "s16",
        output,
        "i32",
        str(timeout),
    ]


def build_kernelsu_late_load_args(remote_path: str, log_path: str, timeout: int) -> list[str]:
    return build_service_args(
        command=remote_path,
        arguments="late-load",
        output=log_path,
        timeout=timeout,
    )

