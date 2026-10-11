"""Bank resolvers: lookup, update_contact, refund, transfer, payee_change, grant_role. All SQL is parameterised."""
import re

from ..resolver import Ctx, Resolver, ResolverError

CUSTOMER_RE = re.compile(r"^C-\d{4}$")
VENDOR_RE = re.compile(r"^V-\d{2}$")
MONTHS = {"January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"}


def _only(args):
    only = args.get("only")
    if only is not None and (not isinstance(only, list) or not all(isinstance(x, str) and len(x) < 40 for x in only)):
        raise ResolverError("invalid 'only' list")


def _customer(args, key="customer"):
    c = args.get(key, "")
    if not isinstance(c, str) or not CUSTOMER_RE.match(c):
        raise ResolverError(f"invalid customer id {c!r}")
    return c


class Lookup(Resolver):
    action = "lookup"
    tables = ("customers",)

    def validate(self, args):
        _customer(args)

    def apply(self, conn, args, ctx):
        r = conn.execute("SELECT id FROM customers WHERE id=?", (args["customer"],)).fetchone()
        if not r:
            raise ResolverError("no such customer")
        return {"columns": [("customers", "name"), ("customers", "city")]}


class UpdateContact(Resolver):
    action = "update_contact"
    tables = ("customers",)
    meta_cols = {"customers": ["id"]}

    def validate(self, args):
        _customer(args)
        if not (args.get("phone") or args.get("email")):
            raise ResolverError("phone or email required")

    def apply(self, conn, args, ctx):
        cols = []
        for field in ("phone", "email"):
            if args.get(field):
                cur = conn.execute(f"UPDATE customers SET {field}=? WHERE id=?", (str(args[field]), args["customer"]))
                if cur.rowcount == 0:
                    raise ResolverError("no such customer")
                cols.append(("customers", field))
        return {"columns": cols}


class Refund(Resolver):
    action = "refund"
    tables = ("refunds",)
    meta_cols = {"refunds": ["customer_id", "amount_minor"]}

    def validate(self, args):
        _customer(args)
        if args.get("month") not in MONTHS:
            raise ResolverError("invalid month")
        if args.get("match", "customer") not in ("customer", "batch"):
            raise ResolverError("invalid match mode")
        _only(args)

    def reduce(self, args, effect, check, env):
        meta = effect.row_meta.get("refunds", {})
        want = env.scope.get("customer", args.get("customer"))
        keep, total = [], 0
        for pk in sorted(meta):
            if meta[pk].get("customer_id") != want:
                continue
            amt = meta[pk].get("amount_minor") or 0
            if (env.max_rows is not None and len(keep) >= env.max_rows) or (
                    env.max_amount_minor is not None and total + amt > env.max_amount_minor):
                break
            keep.append(pk)
            total += amt
        return dict(args, match="customer", only=keep) if keep else None

    def apply(self, conn, args, ctx: Ctx):
        month, cust = args["month"], args["customer"]
        if args.get("match", "customer") == "batch":
            batches = [r[0] for r in conn.execute(
                "SELECT DISTINCT batch FROM transactions WHERE customer_id=? AND month=? AND is_duplicate=1",
                (cust, month))]
            if not batches:
                rows = []
            else:
                marks = ",".join("?" * len(batches))
                rows = conn.execute(
                    "SELECT id, customer_id, amount_minor FROM transactions WHERE is_duplicate=1 AND month=? "
                    f"AND batch IN ({marks}) AND id NOT IN (SELECT txn_id FROM refunds) ORDER BY id",
                    (month, *batches)).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, customer_id, amount_minor FROM transactions WHERE customer_id=? AND month=? "
                "AND is_duplicate=1 AND id NOT IN (SELECT txn_id FROM refunds) ORDER BY id", (cust, month)).fetchall()
        only = args.get("only")
        if only is not None:
            rows = [r for r in rows if "RF-" + r[0] in set(only)]
        names = {cid: n for cid, n in conn.execute("SELECT id, name FROM customers")}
        row_names = {"refunds": {"RF-" + tid: names.get(cid, "") for tid, cid, _ in rows}}
        total = 0
        for tid, cid, amt in rows:
            conn.execute("INSERT INTO refunds (id, txn_id, customer_id, amount_minor, ts) VALUES (?,?,?,?,?)",
                         ("RF-" + tid, tid, cid, amt, ctx.now))
            total += amt
        return {"amount_minor": total, "destinations": ["payment_rail"] if rows else [],
                "columns": [("refunds", "*")], "row_names": row_names}


class Transfer(Resolver):
    """Pay pending vendor invoices. Moves money out, so it is irreversible; payments leave via the outbox."""
    action = "transfer"
    tables = ("invoices", "transactions")
    meta_cols = {"invoices": ["vendor_id", "amount_minor", "status"], "transactions": ["amount_minor"]}

    def validate(self, args):
        if args.get("batch", "pending") != "pending":
            raise ResolverError("only the 'pending' batch can be paid")
        v = args.get("vendor")
        if v is not None and (not isinstance(v, str) or not VENDOR_RE.match(v)):
            raise ResolverError("invalid vendor id")
        _only(args)

    def reduce(self, args, effect, check, env):
        meta = effect.row_meta.get("invoices", {})
        keep, total = [], 0
        for pk in sorted(meta):
            amt = meta[pk].get("amount_minor") or 0
            if len(keep) >= 10 or (env.max_amount_minor is not None and total + amt > env.max_amount_minor):
                break
            keep.append(pk)
            total += amt
        return dict(args, only=keep) if keep and len(keep) < len(meta) else None

    def apply(self, conn, args, ctx: Ctx):
        if args.get("vendor"):
            rows = conn.execute(
                "SELECT i.id, i.vendor_id, i.amount_minor, v.account FROM invoices i JOIN vendors v ON v.id=i.vendor_id "
                "WHERE i.status='pending' AND i.vendor_id=? ORDER BY i.id", (args["vendor"],)).fetchall()
        else:
            rows = conn.execute(
                "SELECT i.id, i.vendor_id, i.amount_minor, v.account FROM invoices i JOIN vendors v ON v.id=i.vendor_id "
                "WHERE i.status='pending' ORDER BY i.id").fetchall()
        if args.get("only") is not None:
            rows = [r for r in rows if r[0] in set(args["only"])]
        vnames = {vid: n for vid, n in conn.execute("SELECT id, name FROM vendors")}
        row_names = {"invoices": {r[0]: vnames.get(r[1], "") for r in rows}}
        total, recipients = 0, set()
        for iid, vid, amt, account in rows:
            conn.execute("UPDATE invoices SET status='paid', paid_ts=? WHERE id=?", (ctx.now, iid))
            conn.execute("INSERT INTO transactions (id, customer_id, amount_minor, kind, merchant, month, batch,"
                         " is_duplicate, ts) VALUES (?,NULL,?,?,?,?,NULL,0,?)",
                         ("PAY-" + iid, amt, "payment", vid, "n/a", ctx.now))
            conn.execute("INSERT INTO outbox (kind, recipient, subject, amount_minor, payload_json, status,"
                         " created_ts, decision_id) VALUES ('pay',?,?,?,?,'pending',?,?)",
                         (account, f"Invoice {iid}", amt, "{}", ctx.now, ctx.decision_id))
            total += amt
            recipients.add(account)
        return {"amount_minor": total, "recipients": sorted(recipients),
                "destinations": ["payment_rail"] if rows else [],
                "columns": [("invoices", "*"), ("transactions", "*")], "row_names": row_names}


class PayeeChange(Resolver):
    action = "payee_change"
    tables = ("vendors",)
    meta_cols = {"vendors": ["account"]}

    def validate(self, args):
        if not VENDOR_RE.match(str(args.get("vendor", ""))):
            raise ResolverError("invalid vendor id")
        if not args.get("new_account"):
            raise ResolverError("new_account required")

    def apply(self, conn, args, ctx):
        vendor, acct, source = args["vendor"], str(args["new_account"]), str(args.get("source", ""))
        untrusted, path = True, []
        kind, _, ref = source.partition(":")
        if kind == "form":
            f = conn.execute("SELECT vendor_id, account, verified FROM forms WHERE id=?", (ref,)).fetchone()
            if f and f[2] == 1 and f[0] == vendor and f[1] == acct:
                untrusted = False
                path.append(f"forms.{ref} -> vendors.{vendor}.account")
        elif kind == "inbox":
            path.append(f"inbox.{ref} -> vendors.{vendor}.account")
        if untrusted and not path:
            path.append(f"unverified source {source or 'none'} -> vendors.{vendor}.account")
        cur = conn.execute("UPDATE vendors SET account=? WHERE id=?", (acct, vendor))
        if cur.rowcount == 0:
            raise ResolverError("no such vendor")
        return {"recipients": [acct], "destinations": ["payment_rail"], "untrusted": untrusted,
                "label_path": path, "columns": [("vendors", "account")]}


class GrantRole(Resolver):
    action = "grant_role"
    tables = ("grants",)
    meta_cols = {"grants": ["subject", "role"]}

    def validate(self, args):
        if not args.get("target") or not args.get("role"):
            raise ResolverError("target and role required")

    def apply(self, conn, args, ctx):
        n = conn.execute("SELECT COUNT(*) FROM grants").fetchone()[0]
        conn.execute("INSERT INTO grants (id, subject, role, ts) VALUES (?,?,?,?)",
                     (f"G-{n + 1:04d}", str(args["target"]), str(args["role"]), ctx.now))
        return {"columns": [("grants", "*")]}


RESOLVERS = {r.action: r() for r in (Lookup, UpdateContact, Refund, Transfer, PayeeChange, GrantRole)}
