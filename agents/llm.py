"""Chat client for the agent's language model. The agent process holds its own model credentials and its signing key,
and nothing else: it still cannot reach any data or credential of the organisation."""
import json
import os
import re

import httpx

TRANSPORT: httpx.BaseTransport | None = None      # tests inject httpx.MockTransport here


class LLMError(Exception):
    pass


def configured() -> bool:
    return os.environ.get("AI_PROVIDER", "none").lower() in ("openrouter", "gemini", "ollama")


def chat(messages: list[dict], timeout: float | None = None) -> str:
    """messages: [{role: system|user|assistant, content}]. Returns the model's raw text."""
    prov, model, key = os.environ.get("AI_PROVIDER", "none").lower(), os.environ.get("AI_MODEL", ""), os.environ.get("AI_API_KEY", "")
    timeout = timeout or float(os.environ.get("AI_TIMEOUT_SECONDS", "30"))
    if prov not in ("openrouter", "gemini", "ollama"):
        raise LLMError("no language model is configured (set AI_PROVIDER, AI_MODEL and AI_API_KEY)")
    try:
        with httpx.Client(timeout=timeout, transport=TRANSPORT) as c:
            if prov == "openrouter":
                r = c.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {key}"},
                           json={"model": model or "meta-llama/llama-3.1-8b-instruct", "messages": messages, "temperature": 0})
                r.raise_for_status()
                text = r.json()["choices"][0]["message"]["content"]
            elif prov == "gemini":
                system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
                contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                            for m in messages if m["role"] != "system"]
                r = c.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model or 'gemini-3.8-flash'}:generateContent",
                           headers={"x-goog-api-key": key},
                           json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
                                 "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}}})
                r.raise_for_status()
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                r = c.post(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/chat",
                           json={"model": model or "qwen2.5:3b", "messages": messages, "stream": False, "options": {"temperature": 0}})
                r.raise_for_status()
                text = r.json()["message"]["content"]
    except httpx.TimeoutException as e:
        raise LLMError("the language model did not answer in time") from e
    except httpx.HTTPStatusError as e:
        raise LLMError(f"the language model returned HTTP {e.response.status_code}") from e
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError) as e:
        raise LLMError(f"the language model could not be reached ({type(e).__name__})") from e
    if not isinstance(text, str) or not text.strip():
        raise LLMError("the language model returned an empty answer")
    return text


def parse_json(text: str) -> dict:
    """Pull the first JSON object out of a model reply (models sometimes wrap it in prose or code fences)."""
    m = re.search(r"\{.*\}", text, re.S)
    obj = json.loads(m.group(0) if m else text)
    if not isinstance(obj, dict):
        raise ValueError("not an object")
    return obj
