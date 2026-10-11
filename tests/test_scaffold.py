import pathlib


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_cors_allows_frontend_only(client):
    ok = client.get("/health", headers={"Origin": "http://localhost:5173"})
    bad = client.get("/health", headers={"Origin": "http://evil.test"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in bad.headers


def test_agents_have_no_db_path():
    for p in pathlib.Path("agents").rglob("*.py"):
        text = p.read_text().lower()
        assert ".db" not in text and "sqlite" not in text, p
