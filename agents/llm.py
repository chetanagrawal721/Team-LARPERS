"""Chat client for the agent's language model. The agent process holds its own model credentials and its signing key,
and nothing else: it still cannot reach any data or credential of the organisation.

Reliability: each provider is retried with backoff on rate limits, server errors and timeouts; if a hosted provider keeps
failing, the next one in AI_FALLBACK (default: ollama, when it is running locally) is used. Every attempt is reported."""
import json
import os
import re
import time

import httpx

TRANSPORT: httpx.BaseTransport | None = None      # tests inject httpx.MockTransport here
SLEEP = time.sleep                                 # tests replace this so retries do not wait
PROVIDERS = ("openrouter", "gemini", "ollama")
RETRYABLE = {408, 425, 429, 500, 502, 503, 504}
BACKOFF = (1.5, 4.0)                               # waits before retry 2 and 3


class LLMError(Exception):
    pass


def primary() -> str:
    return os.environ.get("AI_PROVIDER", "none").lower()


def chain() -> list[str]:
    """Providers to try, in order: the configured one, then AI_FALLBACK (default ollama), without duplicates."""
    out = [primary()] if primary() in PROVIDERS else []
    for p in (os.environ.get("AI_FALLBACK", "ollama") or "").lower().replace(" ", "").split(","):
        if p in PROVIDERS and p not in out and (p != "ollama" or ollama_up()):
            out.append(p)
    return out


def configured() -> bool:
    return bool(chain())


def ollama_up() -> bool:
    try:
        with httpx.Client(timeout=1.5, transport=TRANSPORT) as c:
            return c.get(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/tags").status_code == 200
    except httpx.HTTPError:
        return False


def model_for(provider: str) -> str:
    if provider == primary():
        return os.environ.get("AI_MODEL", "")
    return os.environ.get("OLLAMA_MODEL", "llama3:8b") if provider == "ollama" else ""


def _call(provider: str, messages: list[dict], timeout: float) -> str:
    model, key = model_for(provider), os.environ.get("AI_API_KEY", "")
    with httpx.Client(timeout=timeout, transport=TRANSPORT) as c:
        if provider == "openrouter":
            r = c.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {key}"},
                       json={"model": model or "meta-llama/llama-3.1-8b-instruct", "messages": messages, "temperature": 0})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        if provider == "gemini":
            system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
            contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                        for m in messages if m["role"] != "system"]
            r = c.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model or 'gemini-3.5-flash-lite'}:generateContent",
                       headers={"x-goog-api-key": key},
                       json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
                             "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}})
            r.raise_for_status()
            cand = r.json()["candidates"][0]
            text = "".join(part.get("text", "") for part in cand.get("content", {}).get("parts", []))
            if not text.strip():
                raise ValueError(f"no text in the reply (finishReason {cand.get('finishReason')})")
            return text
        r = c.post(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/chat",
                   json={"model": model or "llama3:8b", "messages": messages, "stream": False, "format": "json",
                         "options": {"temperature": 0, "num_ctx": 8192}})
        r.raise_for_status()
        return r.json()["message"]["content"]


def chat_ex(messages: list[dict], timeout: float | None = None, report=None) -> tuple[str, dict]:
    """Return (raw text, meta). `report(text, **data)` is called for every retry or fallback so the UI can show it."""
    report = report or (lambda *a, **k: None)
    providers = chain()
    if not providers:
        raise LLMError("no language model is configured (set AI_PROVIDER, AI_MODEL and AI_API_KEY, or start Ollama)")
    base = timeout or float(os.environ.get("AGENT_LLM_TIMEOUT") or os.environ.get("AI_TIMEOUT_SECONDS", "60"))
    errors: list[str] = []
    for provider in providers:
        t_out = max(base, 180.0) if provider == "ollama" else base          # a local model may need time to load
        for attempt in range(1, len(BACKOFF) + 2):
            try:
                text = _call(provider, messages, t_out)
                if not isinstance(text, str) or not text.strip():
                    raise ValueError("empty answer")
                return text, {"provider": provider, "model": model_for(provider) or provider, "attempt": attempt,
                              "fell_back": provider != providers[0], "errors": errors}
            except httpx.TimeoutException:
                why, retry = "timed out", True
            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                why, retry = f"HTTP {code}", code in RETRYABLE
            except (KeyError, IndexError, ValueError, TypeError) as e:
                why, retry = f"unusable reply ({type(e).__name__})", False       # retrying the same call gives the same shape
            except httpx.HTTPError as e:
                why, retry = f"{type(e).__name__}", True
            errors.append(f"{provider}: {why} (attempt {attempt})")
            last = attempt > len(BACKOFF)
            if retry and not last:
                report(f"{provider} failed ({why}); retrying in {BACKOFF[attempt - 1]:g}s", provider=provider, attempt=attempt)
                SLEEP(BACKOFF[attempt - 1])
                continue
            nxt = providers[providers.index(provider) + 1] if provider != providers[-1] else None
            report(f"{provider} is not working ({why})" + (f"; switching to {nxt}" if nxt else ""), provider=provider)
            break
    raise LLMError("every language model provider failed: " + "; ".join(errors[-4:]))


def chat(messages: list[dict], timeout: float | None = None) -> str:
    return chat_ex(messages, timeout)[0]


def parse_json(text: str) -> dict:
    """Pull the first JSON object out of a model reply (models sometimes wrap it in prose or code fences)."""
    m = re.search(r"\{.*\}", text, re.S)
    obj = json.loads(m.group(0) if m else text)
    if not isinstance(obj, dict):
        raise ValueError("not an object")
    return obj
