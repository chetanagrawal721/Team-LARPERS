"""Data labels and destination classes. Labels are computed by the gateway from what it resolved, never reported by agents."""
import json
import sqlite3

from .policy_loader import LEVELS, Policy

RANK = {lvl: i for i, lvl in enumerate(LEVELS)}   # PUBLIC < INTERNAL < PII < SECRET


def max_level(labels) -> str | None:
    ranked = [lbl for lbl in labels if lbl in RANK]
    return max(ranked, key=RANK.get) if ranked else None


def label_effect(policy: Policy, rows: dict, extras: dict) -> tuple[list[str], list[str]]:
    """Return (labels, label_path) for an effect. Unlabelled columns default to INTERNAL (strict)."""
    labels: set[str] = set()
    cols = extras.get("columns") or []
    for table, col in cols:
        labels.add(policy.label_for(table, None if col == "*" else col))
    if not cols:
        for table in rows:
            labels.add(policy.label_for(table))
    labels.update(extras.get("extra_labels", []))
    if extras.get("untrusted"):
        labels.add("UNTRUSTED")
    return sorted(labels), list(extras.get("label_path", []))


def classify_address(policy: Policy, address: str) -> str:
    """Email address -> destination class (internal_email / external_email)."""
    domain = address.rsplit("@", 1)[-1].lower() if "@" in address else ""
    return "internal_email" if domain in [d.lower() for d in policy.model.internal_domains] else "external_email"


def destination_clearance(policy: Policy, dest_class: str) -> int:
    """Rank of the highest label level this destination class is cleared for; -1 if unknown (default deny)."""
    lvl = policy.destinations.get(dest_class)
    return RANK.get(lvl, -1)


def uncleared_destinations(policy: Policy, labels, destinations) -> list[str]:
    """Destinations that are not cleared for the most sensitive label in `labels`."""
    top = max_level(labels)
    if top is None:
        return []
    return sorted(d for d in destinations if destination_clearance(policy, d) < RANK[top])


def unknown_destinations(policy: Policy, destinations) -> list[str]:
    return sorted(d for d in destinations if d not in policy.destinations)


def file_labels(conn: sqlite3.Connection, path: str) -> tuple[list[str], list[str]]:
    """Labels and provenance recorded for a file object written by an agent."""
    r = conn.execute("SELECT labels, label_path FROM shared_files WHERE path=?", (path,)).fetchone()
    if not r:
        return [], []
    return json.loads(r[0] or "[]"), json.loads(r[1] or "[]")
