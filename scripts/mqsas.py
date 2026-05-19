from __future__ import annotations


def shell_quote(value: str) -> str:
    if value == "":
        return "''"
    return "'" + value.replace("'", "'\\''") + "'"


def build_service_shell_command(command: str, arguments: str, output: str, timeout: int) -> str:
    parts = [
        "service",
        "call",
        "miui.mqsas.IMQSNative",
        "21",
        "i32",
        "1",
        "s16",
        shell_quote(command),
        "i32",
        "1",
        "s16",
        shell_quote(arguments),
        "s16",
        shell_quote(output),
        "i32",
        str(timeout),
    ]
    return " ".join(parts)


def build_service_args(command: str, arguments: str, output: str, timeout: int) -> list[str]:
    return [
        "adb",
        "shell",
        build_service_shell_command(command, arguments, output, timeout),
    ]


def build_kernelsu_late_load_args(remote_path: str, log_path: str, timeout: int) -> list[str]:
    return build_service_args(
        command=remote_path,
        arguments="late-load",
        output=log_path,
        timeout=timeout,
    )
