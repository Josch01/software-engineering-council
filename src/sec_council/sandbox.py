"""Docker-only execution of untrusted Python with hard CPU/RAM/time/output bounds.

Requires locally installed approved Docker image; no code is run on host Python.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .budgets import ResourceBudget
from .contracts import CheckResult, GateStatus
from .memory import sha256_file


@dataclass(frozen=True)
class SandboxConfig:
    image: str = "python:3.12-slim"


def run_python_docker(source: Path, relative_script: str, logs_dir: Path,
                      *, approved: bool = False, budget: ResourceBudget | None = None,
                      config: SandboxConfig | None = None) -> CheckResult:
    if not approved:
        return CheckResult("sandbox", GateStatus.BLOCKED, "Explicit execution approval missing")
    if shutil.which("docker") is None:
        return CheckResult("sandbox", GateStatus.BLOCKED, "Docker unavailable: fail closed")
    budget = budget or ResourceBudget()
    config = config or SandboxConfig()
    source = Path(source).resolve(strict=True)
    script = (source / relative_script).resolve(strict=True)
    if not script.is_relative_to(source) or not script.is_file() or script.suffix != ".py":
        return CheckResult("sandbox", GateStatus.BLOCKED, "Script must be a .py file inside source")
    logs_dir = Path(logs_dir).resolve()
    logs_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sec-docker-") as tmp:
        cid = Path(tmp) / "container.cid"
        log = logs_dir / f"run-{int(time.time() * 1000)}.log"
        args = [
            "docker", "run", "--rm", "--pull=never", "--cidfile", str(cid),
            "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--pids-limit=128",
            f"--cpus={budget.max_cpu}", f"--memory={budget.max_ram_mb}m",
            f"--memory-swap={budget.max_ram_mb}m",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
            "--user=65534:65534", "--workdir=/work",
            "--mount", f"type=bind,src={source},dst=/work,readonly",
            config.image, "python", "-B", relative_script,
        ]
        start = time.monotonic()
        status, explanation, returncode = GateStatus.BLOCKED, "Not started", None
        with log.open("wb") as output:
            try:
                proc = subprocess.Popen(args, stdout=output, stderr=subprocess.STDOUT)
                while True:
                    returncode = proc.poll()
                    if returncode is not None:
                        status = GateStatus.PASS if returncode == 0 else GateStatus.FAIL
                        explanation = f"Process exit code {returncode}"
                        break
                    if time.monotonic() - start > budget.timeout_seconds:
                        status, explanation = GateStatus.FAIL, "Execution timeout"
                        break
                    output.flush()
                    if log.stat().st_size > budget.max_log_bytes:
                        status, explanation = GateStatus.FAIL, "Output budget exceeded"
                        break
                    time.sleep(0.2)
                if proc.poll() is None:
                    # Kill container, not just docker client; Docker itself controls descendants.
                    if cid.exists():
                        subprocess.run(["docker", "rm", "-f", cid.read_text().strip()],
                                       capture_output=True, timeout=10, check=False)
                    proc.kill()
                proc.wait(timeout=10)
            except (OSError, subprocess.TimeoutExpired) as exc:
                status, explanation = GateStatus.BLOCKED, f"Sandbox infrastructure failure: {exc}"
                if "proc" in locals() and proc.poll() is None:
                    if cid.exists():
                        try:
                            subprocess.run(["docker", "rm", "-f", cid.read_text().strip()],
                                           capture_output=True, timeout=10, check=False)
                        except (OSError, subprocess.TimeoutExpired):
                            pass
                    proc.kill()
                    proc.wait(timeout=5)
        # Retain only budgeted logs; file size cannot drive the agent's context usage.
        if log.stat().st_size > budget.max_log_bytes:
            with log.open("rb+") as f:
                f.truncate(budget.max_log_bytes)
        return CheckResult(
            "sandbox", status, explanation, (str(log),),
            metadata={"duration_seconds": round(time.monotonic() - start, 3),
                      "script_sha256": sha256_file(script), "container_image": config.image,
                      "exit_code": returncode, "network": "disabled",
                      "cpu_limit": budget.max_cpu, "ram_limit_mb": budget.max_ram_mb},
        )
