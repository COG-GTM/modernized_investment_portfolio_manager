import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PACKAGE_DIR.parent
DATA_DIR = PACKAGE_DIR / "data"

SCENARIO_BASELINE = "baseline"
SCENARIO_BROKEN = "broken"
SCENARIOS = (SCENARIO_BASELINE, SCENARIO_BROKEN)

FAULT_PRE_ACK_STALL = "PRE_ACK_STALL"

DEFAULT_DATABASE_URL = f"sqlite:///{BACKEND_DIR / 'portfolio.db'}"


def detect_code_revision() -> str:
    override = os.environ.get("TECHFEST_CODE_REVISION")
    if override:
        return override
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def _env_scenario() -> str:
    value = os.environ.get("TECHFEST_BATCH_SCENARIO", SCENARIO_BASELINE).strip().lower()
    return value if value in SCENARIOS else SCENARIO_BASELINE


@dataclass
class Settings:
    scenario: str = field(default_factory=_env_scenario)
    database_url: str = field(
        default_factory=lambda: os.environ.get("TECHFEST_BATCH_DATABASE_URL", DEFAULT_DATABASE_URL)
    )
    # Injected pre-acknowledgement stall, honored only in the broken scenario.
    stall_ms: int = field(default_factory=lambda: int(os.environ.get("TECHFEST_BATCH_STALL_MS", "1500")))
    # Client retry policy (bounded).
    client_timeout_s: float = field(
        default_factory=lambda: float(os.environ.get("TECHFEST_BATCH_CLIENT_TIMEOUT_S", "1.0"))
    )
    client_max_attempts: int = field(
        default_factory=lambda: int(os.environ.get("TECHFEST_BATCH_CLIENT_MAX_ATTEMPTS", "3"))
    )
    code_revision: str = field(default_factory=detect_code_revision)

    @property
    def fault_injection_enabled(self) -> bool:
        return self.scenario == SCENARIO_BROKEN


settings = Settings()
