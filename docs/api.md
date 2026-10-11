# SEALGATE API contract (frozen at M0.3)

Base URL `http://localhost:8000`. Schemas live in `gateway/schemas.py`. Mock responses: `gateway/mock_api.py`.
Agents authenticate with an HMAC-SHA256 signature in the body (`sig`). Humans authenticate with headers `X-User` and `X-Token` (demo-only auth).

| Endpoint | Caller | Purpose |
|---|---|---|
| `GET /health` | any | `{"status":"ok"}` |
| `POST /propose` | agent | Submit a signed `Proposal` -> `Decision` |
| `GET /status/{id}` | agent | Current `Decision` (incl. `status`, `verdict`, `drift`) |
| `GET /events` | dashboard | Server-Sent Events stream of `Event` |
| `GET /action/{id}` | dashboard | Decision + expected / sandbox / real effect + diff |
| `GET /actions` | dashboard | Recent decisions, newest first |
| `POST /approve` / `POST /reject` | human | Body `ApprovalRequest` -> `Decision` |
| `POST /execute/{id}` | human | Execute a sealed (approved) decision -> `Decision` (`DONE` or `VOID` + `drift`) |
| `POST /safe-version/{id}` | human | Accept smallest safe version -> new `Decision` |
| `GET /shadow/{sid}` | human | Shadow session: steps + cumulative diff |
| `POST /promote/{sid}` / `POST /discard/{sid}` | human | Promote or discard a Shadow session |
| `GET /audit` | dashboard | Audit entries |
| `POST /audit/verify` | dashboard | `{ok: bool, first_broken_seq: int|null}` |
| `POST /audit/replay/{seq}` | dashboard | Re-evaluate a stored decision |
| `POST /lab/run?mode=A|B|C` | dashboard | Run the paired suite |
| `POST /demo/{scenario}` | dashboard | Start a scripted agent scenario |
| `POST /demo/insert-invoices` | dashboard | Judge-clickable drift trigger (inserts 3,960 pending invoices) |
| `POST /domain/{name}` | dashboard | Switch domain (`bank`, `hospital`, `shop`) |
| `POST /ai/toggle` | dashboard | Toggle AI on/off |
| `POST /policy/reload` | admin | Reload the policy file (logged) |

## Example: `POST /propose`
```json
{"agent":"refund-agent","action":"refund","args":{"customer":"C-1042","month":"March"},
 "intent":"refund 1 customer","user_instruction":"Refund C-1042's duplicate March charges",
 "on_behalf_of":"meera","nonce":"9f1c...","ts":1760000000,"sig":"<hex hmac>"}
```
Signature: HMAC-SHA256 over `json.dumps(body_without_sig, sort_keys=True, separators=(",", ":"))` with the agent's key.

## Example: `Decision`
```json
{"id":"demo-1","verdict":"BLOCK","rule":"R06","reason":"Refund touches 61 customers; request named 1",
 "baseline_verdict":"ALLOW","decision_path":"rules+ai","status":"blocked","tier":"T2",
 "effect":{"action_type":"refund","rows":{"refunds":["RF-1"]},"amount_minor":98000000},
 "envelope":{"scope":{"customer":"C-1042","month":"March"},"max_rows":5,"source":"ai_from_instruction"},
 "safe_version":{"description":"3 refunds, Rs 6,400","args":{"customer":"C-1042","month":"March"}}}
```

Verdicts: `ALLOW | HOLD | BLOCK | VOID | DONE`. Status: `done | pending | blocked | void | rejected | shadow | allowed`.
Drift types: `args_drift | effect_drift | label_drift | policy_drift | state_drift | replay | expired | bad_signature`.
