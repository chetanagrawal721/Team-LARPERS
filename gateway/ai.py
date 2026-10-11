"""Escalate-only AI client (R4, R9, R10). Calls an optional LLM behind a timeout, validates the output against a strict
schema, and returns (None, status) on any failure so the caller falls back to rules-only behaviour.

Providers (AI_PROVIDER): none | ollama | gemini | openrouter. Keys come from the environment (.env) only."""
import json
import os
import re
from typing import Literal

import httpx

from . import config  # noqa: F401  (loads .env so AI settings are available)
from pydantic import BaseModel, ConfigDict, ValidationError

TIMEOUT_SECONDS = 3.0                              # default; AI_TIMEOUT_SECONDS overrides it for slower models
TRANSPORT: httpx.BaseTransport | None = None      # tests inject httpx.MockTransport here
STATE = {"enabled": None, "force": None}           # enabled: None -> read AI_ENABLED; force: None | "garbage" | "off"

Escalation = Literal["NONE", "HOLD", "BLOCK"]


class EscalationResult(BaseModel):
    """The only shape in which an AI judgement can influence a decision: raise to HOLD or BLOCK, never lower."""
    model_config = ConfigDict(extra="forbid")
    escalation: Escalation
    reason: str = ""


def enabled() -> bool:
    if STATE["enabled"] is not None:
        return STATE["enabled"]
    return os.environ.get("AI_ENABLED", "true").lower() == "true"


def set_enabled(value: bool) -> bool:
    STATE["enabled"] = value
    return value


def provider() -> str:
    return os.environ.get("AI_PROVIDER", "none").lower()


def available() -> bool:
    if not enabled() or STATE["force"] == "off":
        return False
    return provider() != "none" or STATE["force"] == "garbage" or TRANSPORT is not None


def _call(system: str, user: str) -> str:
    """Return the model's raw text. Raises httpx.HTTPError / KeyError / ValueError on any problem."""
    prov, model, key = provider(), os.environ.get("AI_MODEL", ""), os.environ.get("AI_API_KEY", "")
    with httpx.Client(timeout=float(os.environ.get("AI_TIMEOUT_SECONDS", TIMEOUT_SECONDS)), transport=TRANSPORT) as c:
        if prov == "ollama":
            url = os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/generate"
            r = c.post(url, json={"model": model or "qwen2.5:3b", "system": system, "prompt": user,
                                  "format": "json", "stream": False})
            r.raise_for_status()
            return r.json()["response"]
        if prov == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model or 'gemini-2.0-flash'}:generateContent"
            r = c.post(url, headers={"x-goog-api-key": key},
                       json={"systemInstruction": {"parts": [{"text": system}]},
                             "contents": [{"role": "user", "parts": [{"text": user}]}],
                             "generationConfig": {"responseMimeType": "application/json", "temperature": 0,
                                                  "thinkingConfig": {"thinkingBudget": 0}}})
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        if prov == "openrouter":
            r = c.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {key}"},
                       json={"model": model or "meta-llama/llama-3.1-8b-instruct",
                             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                             "response_format": {"type": "json_object"}, "temperature": 0})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    raise ValueError("no AI provider configured")


def _extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def ask(system: str, user: str, schema: type[BaseModel]) -> tuple[BaseModel | None, str]:
    """Return (validated result, status). status in ok | off | timeout | invalid | error."""
    if not available():
        return None, "off"
    try:
        raw = "this is not json" if STATE["force"] == "garbage" else _call(system, user)
    except httpx.TimeoutException:
        return None, "timeout"
    except (httpx.HTTPError, KeyError, IndexError, ValueError, OSError, TypeError):
        return None, "error"
    try:
        return schema.model_validate(_extract_json(raw)), "ok"
    except (ValueError, ValidationError, AttributeError, TypeError):    # e.g. a null message body
        return None, "invalid"
