from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "fast_sim.cli"]


def test_cli_info() -> None:
    result = subprocess.run(CLI + ["info"], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    assert data["version"] == "0.1.0"


def test_cli_run(tmp_path: Path) -> None:
    config = REPO_ROOT / "examples" / "configs" / "sir_demo.yaml"
    result = subprocess.run(
        CLI
        + [
            "run",
            "--config",
            str(config),
            "--steps",
            "5",
            "--seed",
            "123",
            "--out",
            str(tmp_path / "metrics.npz"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "fast-sim metrics" in result.stdout or "metric" in result.stdout
