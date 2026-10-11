"""Agent-side tools. An agent's only capability is a signed POST to the gateway; it holds its signing key and nothing else."""
import hashlib
import hmac
import json
import os
import re
import time
import uuid

import httpx

from . import config


def sign(key: str, body: dict) -> str:
    canon = json.dumps({k: v for k, v in body.items() if k != "sig"}, sort_keys=True, separators=(",", ":"))
    return hmac.new(key.encode(), canon.encode(), hashlib.sha256).hexdigest()


class Agent:
    def __init__(self, name: str, client: httpx.Client | None = None, key: str | None = None, wait_seconds: float = 120.0,
                 poll: float = 0.5):
        self.name = name
        self.key = key or os.environ.get("AGENT_KEY_" + name.upper().replace("-", "_"), "")
        self.client = client or httpx.Client(base_url=config.GATEWAY_URL, timeout=10.0)
        self.wait_seconds = wait_seconds
        self.poll = poll

    # ---- transport ------------------------------------------------------------------
    def propose(self, action: str, args: dict, intent: str = "", user_instruction: str = "",
                on_behalf_of: str = "", run: str = "") -> dict:
        body = {"agent": self.name, "action": action, "args": args, "intent": intent,
                "user_instruction": user_instruction, "on_behalf_of": on_behalf_of,
                "nonce": uuid.uuid4().hex, "ts": int(time.time())}
        body["sig"] = sign(self.key, body)
        r = self.client.post("/propose", json=body, headers={"X-Run": run} if run else None)
        r.raise_for_status()
        return r.json()

    def status(self, decision_id: str) -> dict:
        r = self.client.get(f"/status/{decision_id}")
        r.raise_for_status()
        return r.json()

    def wait(self, decision: dict, until=("done", "void", "rejected", "blocked", "shadow")) -> dict:
        """Poll a held decision until a human resolves it (or the wait budget runs out)."""
        deadline = time.time() + self.wait_seconds
        d = decision
        while d["status"] in ("pending", "approved") and time.time() < deadline:
            time.sleep(self.poll)
            d = self.status(d["id"])
            m = re.search(r"replaced by safe version (D-[0-9a-f]+)", d.get("reason", ""))
            if m:
                d = self.status(m.group(1))
        return d

    def say(self, text: str, kind: str = "agent") -> None:
        try:
            self.client.post("/chat", json={"from": kind, "agent": self.name, "text": text})
        except httpx.HTTPError:
            pass

    # ---- one tool per action (each is just a signed request) -------------------------------
    def lookup(self, **a): return self.propose("lookup", a)
    def update_contact(self, **a): return self.propose("update_contact", a)
    def refund(self, **a): return self.propose("refund", a)
    def transfer(self, **a): return self.propose("transfer", a)
    def payee_change(self, **a): return self.propose("payee_change", a)
    def grant_role(self, **a): return self.propose("grant_role", a)
    def send_report(self, **a): return self.propose("send_report", a)
    def delete_record(self, **a): return self.propose("delete_record", a)
    def write_file(self, **a): return self.propose("write_file", a)
    def send_email(self, **a): return self.propose("send_email", a)
