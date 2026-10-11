import itertools
import time

from gateway import verify

_n = itertools.count(1)
KEYS = {"refund-agent": "k-refund", "refund-agent-2": "k-refund2", "refund-agent-3": "k-refund3",
        "ops-agent": "k-ops", "records-agent": "k-records", "support-agent": "k-support",
        "marketing-agent": "k-marketing"}


def make_proposal(agent="refund-agent", action="lookup", args=None, user_instruction="", on_behalf_of="",
                  intent="", ts=None, nonce=None, key=None):
    body = {"agent": agent, "action": action, "args": args if args is not None else {},
            "intent": intent, "user_instruction": user_instruction, "on_behalf_of": on_behalf_of,
            "nonce": nonce or f"n-{next(_n)}-{time.time_ns()}",
            "ts": int(time.time()) if ts is None else ts}
    body["sig"] = verify.sign(key or KEYS.get(agent, "k-unknown"), body)
    return body
