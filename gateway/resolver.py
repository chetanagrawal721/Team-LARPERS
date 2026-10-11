"""Effect resolution: run an action on a sandbox copy and measure exactly what it changes (C1)."""
import hashlib
import json
import pathlib
import sqlite3
import tempfile
from dataclasses import dataclass, field

from . import labels as labels_mod
from . import sandbox
from .policy_loader import Policy
from .schemas import Effect
from .seed.common import connect


class ResolverError(Exception):
    """Invalid arguments or unknown action: the caller must BLOCK."""


@dataclass
class Ctx:
    policy: Policy
    agent: str = ""
    human: str = ""
    now: int = 0
    decision_id: str = ""


@dataclass
class Measured:
    effect: Effect
    state_ver: str
    extras: dict = field(default_factory=dict)


class Resolver:
    """Base class. `tables` is a fixed whitelist of business tables to diff (never agent input)."""
    action = ""
    tables: tuple = ()
    meta_cols: dict = {}

    def validate(self, args: dict) -> None:
        pass

    def apply(self, conn: sqlite3.Connection, args: dict, ctx: Ctx) -> dict:
        raise NotImplementedError


def snapshot(conn: sqlite3.Connection, table: str) -> dict:
    cur = conn.execute(f"SELECT * FROM {table}")      # table comes from a resolver's fixed whitelist
    cols = [d[0] for d in cur.description]
    return {str(r[0]): dict(zip(cols, r)) for r in cur}


def table_diff(before: dict, after: dict) -> tuple[list, list, list]:
    added = after.keys() - before.keys()
    removed = before.keys() - after.keys()
    modified = {k for k in before.keys() & after.keys() if before[k] != after[k]}
    return sorted(added), sorted(removed), sorted(modified)


def _h(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def canonical_effect(e: Effect) -> dict:
    return {"action_type": e.action_type,
            "rows": {t: sorted(v) for t, v in sorted(e.rows.items())},
            "recipients": sorted(e.recipients), "amount_minor": e.amount_minor, "currency": e.currency,
            "destinations": sorted(e.destinations), "reversible": e.reversible, "labels": sorted(e.labels)}


def effect_hash(e: Effect) -> str:
    return _h(canonical_effect(e))


def label_path_hash(e: Effect) -> str:
    return _h(list(e.label_path))


def measure(resolver: Resolver, conn: sqlite3.Connection, args: dict, ctx: Ctx) -> Measured:
    """Apply the action on `conn` (caller owns the transaction) and diff the watched tables."""
    resolver.validate(args)
    before = {t: snapshot(conn, t) for t in resolver.tables}
    extras = resolver.apply(conn, args, ctx) or {}
    after = {t: snapshot(conn, t) for t in resolver.tables}
    rows, meta, sizes, pre = {}, {}, {}, {}
    for t in resolver.tables:
        added, removed, modified = table_diff(before[t], after[t])
        if not (added or removed or modified):
            continue
        rows[t] = sorted(added + removed + modified)
        sizes[t] = len(before[t])
        cols = resolver.meta_cols.get(t, [])
        meta[t] = {}
        for ops, pks in (("added", added), ("removed", removed), ("modified", modified)):
            for pk in pks:
                src = after[t].get(pk) or before[t].get(pk) or {}
                meta[t][pk] = {"op": ops, **{c: src.get(c) for c in cols}}
        pre[t] = {pk: before[t].get(pk) for pk in rows[t]}
    policy = ctx.policy
    lbls, path = labels_mod.label_effect(policy, rows, extras)
    dests = sorted(set(extras.get("destinations", [])))
    effect = Effect(action_type=resolver.action, rows=rows, row_meta=meta, table_sizes=sizes,
                    recipients=sorted(set(extras.get("recipients", []))), amount_minor=int(extras.get("amount_minor", 0)),
                    currency=policy.model.currency, destinations=dests,
                    reversible=policy.action_def(resolver.action).get("reversible", "snapshot"),
                    labels=lbls, label_path=path, label_catalog_ver=policy.label_catalog_ver)
    return Measured(effect=effect, state_ver=_h(pre), extras=extras)


def resolve(resolver: Resolver, real_db, args: dict, ctx: Ctx, scratch_dir=None) -> Measured:
    """Practice run on a sandbox copy. The real database is never opened for writing."""
    scratch = pathlib.Path(scratch_dir) if scratch_dir else pathlib.Path(tempfile.mkdtemp(prefix="sealgate-sbx-"))
    copy = sandbox.copy(real_db, scratch)
    conn = connect(copy)
    try:
        conn.execute("BEGIN")
        return measure(resolver, conn, args, ctx)
    finally:
        conn.close()
        sandbox.cleanup(copy)
