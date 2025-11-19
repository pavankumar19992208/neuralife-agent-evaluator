# Sandbox Runner (Placeholder)

This directory will contain the sandbox execution environment for uploaded agent packages.

Planned components:

- `run_agent_in_sandbox.py`: orchestrates containerized execution with resource limits.
- Profiles: network-disabled by default; optional limited proxy layer later.
- Resource enforcement: CPU, memory, wall-clock timeout watchdog.
- Event emission: stdout/stderr capture + structured tool/event trace.

Security notes:

- No outbound network by default.
- Minimal mounted volumes: `/sandbox/agent`, `/data` for artifacts.
- Future: syscall filtering (seccomp), gVisor / Firecracker exploration.
