# Repository Instructions

- All scripts in this repository must be written in Python.
- Do not add PowerShell, Bash, Batch, or shell-wrapper scripts.
- Low-level scripts that can change device state must default to dry-run and require an explicit execution flag.
- The interactive TUI is the exception: it defaults to execution mode because menu selection is the user's confirmation boundary.
- Keep device-touching commands visible in stdout before execution.
