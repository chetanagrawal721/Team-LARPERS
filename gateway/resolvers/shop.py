"""E-commerce resolvers: lookup, write_file, send_email. File objects carry the labels of the rows written into them."""
import json
import re

from .. import labels as labels_mod
from ..resolver import Ctx, Resolver, ResolverError

PATH_RE = re.compile(r"^shared/[A-Za-z0-9_.\-]{1,60}$")
CUSTOMER_RE = re.compile(r"^K-\d{4}$")


class Lookup(Resolver):
    action = "lookup"
    tables = ("customers",)

    def validate(self, args):
        if not CUSTOMER_RE.match(str(args.get("customer", ""))):
            raise ResolverError("invalid customer id")

    def apply(self, conn, args, ctx):
        if not conn.execute("SELECT 1 FROM customers WHERE id=?", (args["customer"],)).fetchone():
            raise ResolverError("no such customer")
        return {"columns": [("customers", "name")]}


class WriteFile(Resolver):
    action = "write_file"
    tables = ("customers",)

    def validate(self, args):
        if not PATH_RE.match(str(args.get("path", ""))):
            raise ResolverError("invalid file path")
        if args.get("source") != "customers":
            raise ResolverError("unknown file source")

    def apply(self, conn, args, ctx: Ctx):
        path = args["path"]
        n = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        lbl = ctx.policy.label_for("customers", "email")
        prov = [f"customers.email -> {path}"]
        conn.execute("INSERT OR REPLACE INTO shared_files (path, content, labels, label_path, written_by) VALUES (?,?,?,?,?)",
                     (path, f"{n} customer rows", json.dumps([lbl]), json.dumps(prov), ctx.agent))
        return {"destinations": ["shared_drive"], "virtual_rows": {"files": {path: {}}},
                "columns": [("customers", "email")], "label_path": prov}


class SendEmail(Resolver):
    action = "send_email"
    tables = ("customers",)

    def validate(self, args):
        if not isinstance(args.get("list"), str) or not args["list"]:
            raise ResolverError("mailing list required")
        for k in ("subject", "body"):
            if not isinstance(args.get(k, ""), str) or len(args.get(k, "")) > 4000:
                raise ResolverError(f"invalid {k}")
        if args.get("file") is not None and not PATH_RE.match(str(args["file"])):
            raise ResolverError("invalid file path")

    def reduce(self, args, effect, check, env):
        if check is not None and check.offending_recipients:
            return dict(args, exclude_external=True)
        if args.get("file"):
            return {k: v for k, v in args.items() if k != "file"}
        return None

    def apply(self, conn, args, ctx: Ctx):
        rows = conn.execute("SELECT email, declared FROM mailing_lists WHERE list_name=? ORDER BY id",
                            (args["list"],)).fetchall()
        if not rows:
            raise ResolverError("unknown or empty mailing list")
        resolved = [(e, d, labels_mod.classify_address(ctx.policy, e)) for e, d in rows]
        if args.get("exclude_external"):
            resolved = [r for r in resolved if r[2] == r[1]]
        file_lbls, file_path = [], []
        if args.get("file"):
            file_lbls, file_path = labels_mod.file_labels(conn, args["file"])
            if not file_lbls:
                raise ResolverError("no such file")
            file_path = file_path + [f"{args['file']} -> {args['list']} recipients"]
        for email, _, _ in resolved:
            conn.execute("INSERT INTO outbox (kind, recipient, subject, body, payload_json, status, created_ts, decision_id)"
                         " VALUES ('email',?,?,?,?,'pending',?,?)",
                         (email, str(args.get("subject", "")), str(args.get("body", "")), "{}", ctx.now, ctx.decision_id))
        return {"recipients": [r[0] for r in resolved], "destinations": sorted({r[2] for r in resolved}),
                "virtual_rows": {"recipients": {e: {"declared": d, "dest": c} for e, d, c in resolved}},
                "columns": [("mail_body", "*")], "extra_labels": file_lbls, "label_path": file_path}


RESOLVERS = {r.action: r() for r in (Lookup, WriteFile, SendEmail)}
