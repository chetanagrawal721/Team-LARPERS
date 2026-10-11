import os

import pytest
from fastapi.testclient import TestClient

TEST_ENV = {
    "AGENT_KEY_REFUND_AGENT": "k-refund", "AGENT_KEY_REFUND_AGENT_2": "k-refund2",
    "AGENT_KEY_REFUND_AGENT_3": "k-refund3", "AGENT_KEY_OPS_AGENT": "k-ops",
    "AGENT_KEY_RECORDS_AGENT": "k-records", "AGENT_KEY_SUPPORT_AGENT": "k-support",
    "AGENT_KEY_MARKETING_AGENT": "k-marketing", "GATEWAY_SEAL_KEY": "k-seal",
    "USER_TOKEN_PRIYA": "t-priya", "USER_TOKEN_RAHUL": "t-rahul", "USER_TOKEN_MEERA": "t-meera",
    "USER_TOKEN_ANITA": "t-anita", "AI_PROVIDER": "none", "AI_ENABLED": "true",
}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for k, v in TEST_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def client(tmp_path):
    from gateway import main
    from gateway.engine import Engine
    main.ENGINES.clear()
    main.CURRENT["domain"] = "bank"
    main.ENGINES["bank"] = Engine("bank", data_dir=tmp_path)
    return TestClient(main.app)


@pytest.fixture
def engine(tmp_path):
    from gateway.engine import Engine
    return Engine("bank", data_dir=tmp_path)
