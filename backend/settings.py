"""Runtime configuration for VASP TRACE.

Secrets are intentionally read only from environment variables.  This module
contains no credentials and is safe to commit.
"""
from dataclasses import dataclass
import os
from pathlib import Path


VALID_TRACE_MODES = {"DEMO", "LIVE", "AUTO"}


def load_local_env() -> None:
    """Load simple KEY=VALUE entries from the project-local .env file.

    Existing operating-system environment variables take priority. This avoids a
    runtime dependency while keeping secrets outside source control.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class TraceSettings:
    default_mode: str
    etherscan_api_key: str
    trongrid_api_key: str
    bitquery_api_key: str
    request_timeout_seconds: float
    max_hops: int
    max_transfers_per_wallet: int
    max_wallet_queries_per_trace: int
    max_children_per_wallet: int
    max_trace_seconds: float

    @property
    def live_sources_configured(self) -> dict[str, bool]:
        return {
            "etherscan": bool(self.etherscan_api_key),
            "trongrid": bool(self.trongrid_api_key),
            "bitquery": bool(self.bitquery_api_key),
        }


def load_settings() -> TraceSettings:
    load_local_env()
    mode = os.getenv("VASP_TRACE_MODE", "DEMO").upper()
    if mode not in VALID_TRACE_MODES:
        mode = "DEMO"
    return TraceSettings(
        default_mode=mode,
        etherscan_api_key=os.getenv("ETHERSCAN_API_KEY", ""),
        trongrid_api_key=os.getenv("TRONGRID_API_KEY", ""),
        bitquery_api_key=os.getenv("BITQUERY_API_KEY", ""),
        # A trace is interactive work.  Bound every upstream wait even when a
        # local .env contains an accidentally large value.
        request_timeout_seconds=max(2.0, min(float(os.getenv("TRACE_REQUEST_TIMEOUT_SECONDS", "5")), 10.0)),
        max_hops=max(1, min(int(os.getenv("TRACE_MAX_HOPS", "4")), 6)),
        # Provider history can be enormous for exchange and service wallets.
        # These caps keep a browser-request trace responsive and readable.
        max_transfers_per_wallet=max(1, min(int(os.getenv("TRACE_MAX_TRANSFERS_PER_WALLET", "25")), 50)),
        # Four focused paths per level allow a full 4-hop investigation without
        # turning one busy wallet into an unbounded fan-out crawl.
        max_wallet_queries_per_trace=max(1, min(int(os.getenv("TRACE_MAX_WALLET_QUERIES_PER_TRACE", "16")), 24)),
        max_children_per_wallet=max(1, min(int(os.getenv("TRACE_MAX_CHILDREN_PER_WALLET", "4")), 12)),
        max_trace_seconds=max(8.0, min(float(os.getenv("TRACE_MAX_DURATION_SECONDS", "20")), 28.0)),
    )


settings = load_settings()
