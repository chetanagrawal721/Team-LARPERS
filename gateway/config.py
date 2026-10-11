"""Runtime configuration. Secrets are read from the environment / .env only."""
import os
import pathlib

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

POLICY_DIR = ROOT / "gateway" / "policy"
DATA_DIR = pathlib.Path(os.environ.get("SEALGATE_DATA_DIR", ROOT / "gateway" / "data"))
DOMAINS = ("bank", "hospital", "shop")
TS_WINDOW_SECONDS = 60


def agent_key(agent: str) -> str | None:
    return os.environ.get("AGENT_KEY_" + agent.upper().replace("-", "_"))


def user_token(user: str) -> str | None:
    return os.environ.get("USER_TOKEN_" + user.upper())


def seal_key() -> bytes:
    return os.environ.get("GATEWAY_SEAL_KEY", "").encode()
