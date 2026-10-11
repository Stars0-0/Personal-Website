"""Run: pip install pytest httpx && pytest -q
To run the same checks against Postgres: DATABASE_URL=postgresql://... pytest -q"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/test.db")
os.environ["ADMIN_TOKEN"] = "secret"
os.environ["ALLOWED_ORIGINS"] = "https://stars0-0.github.io"

import pytest
from fastapi.testclient import TestClient

import main

H = {"Authorization": "Bearer secret"}


@pytest.fixture(scope="module")
def c():
    with TestClient(main.app) as client:
        yield client


@pytest.fixture(autouse=True)
def fresh_bucket():
    main.POSTS.clear()


def test_message_is_validated_and_private(c):
    assert c.post("/api/messages", json={"body": "hello there", "email": "a@b.co"}).status_code == 201
    assert c.post("/api/messages", json={"body": "   "}).status_code == 422
    assert c.post("/api/messages", json={"body": "x", "email": "nope"}).status_code == 422
    assert c.post("/api/messages", json={"body": "x\u0000y"}).status_code == 422
    assert c.post("/api/messages", json={"body": "x" * 2001}).status_code == 422
    assert "hello there" not in c.get("/api/guestbook").text
    assert any(m["body"] == "hello there" for m in c.get("/api/admin/inbox", headers=H).json()["messages"])


def test_guestbook_is_moderated(c):
    assert c.post("/api/guestbook", json={"name": "Ada\nLovelace", "body": "hello   world"}).status_code == 201
    shown = lambda: [e for e in c.get("/api/guestbook").json() if e["name"] == "Ada Lovelace"]
    assert not shown()  # pending, so invisible to visitors
    pending = [e for e in c.get("/api/admin/inbox", headers=H).json()["pending"] if e["name"] == "Ada Lovelace"][0]
    assert pending["body"] == "hello world"  # whitespace collapsed to one line
    url = f"/api/admin/guestbook/{pending['id']}"
    assert c.post(url + "/approve").status_code == 401
    assert c.post(url + "/approve", headers=H).status_code == 200
    assert shown()
    assert c.delete(url, headers=H).status_code == 204
    assert not shown()
    assert c.delete(url, headers=H).status_code == 404


def test_admin_needs_the_right_token(c, monkeypatch):
    assert c.get("/api/admin/inbox").status_code == 401
    assert c.get("/api/admin/inbox", headers={"Authorization": "Bearer wrong"}).status_code == 401
    monkeypatch.setenv("ADMIN_TOKEN", "")
    assert c.get("/api/admin/inbox", headers=H).status_code == 404  # disabled when no token is set


def test_global_rate_limit(c, monkeypatch):
    monkeypatch.setattr(main, "LIMIT", 2)
    assert [c.post("/api/messages", json={"body": "x"}).status_code for _ in range(3)] == [201, 201, 429]


def test_visit_counter(c):
    a = c.post("/api/visit").json()["visits"]
    b = c.post("/api/visit").json()["visits"]
    assert b == a + 1 and c.get("/api/stats").json()["visits"] == b


def test_cors_only_allows_my_site(c):
    def preflight(origin):
        return c.options("/api/guestbook", headers={"Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    assert preflight("https://stars0-0.github.io").headers["access-control-allow-origin"] == "https://stars0-0.github.io"
    assert "access-control-allow-origin" not in preflight("https://evil.example").headers
