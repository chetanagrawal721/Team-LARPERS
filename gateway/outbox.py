"""Transactional outbox delivery: messages and payments leave only after the transaction that wrote them committed."""
import threading
import time

from . import clock


def deliver_pending(engine) -> int:
    """Deliver every committed pending outbox row (a stand-in for SMTP / the payment rail). Returns the count."""
    conn = engine.real_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        rows = conn.execute("SELECT id, kind, recipient, subject, amount_minor FROM outbox "
                            "WHERE status='pending'").fetchall()
        for oid, kind, recipient, subject, amount in rows:
            conn.execute("INSERT INTO delivered_messages (outbox_id, kind, recipient, subject, amount_minor,"
                         " delivered_ts) VALUES (?,?,?,?,?,?)", (oid, kind, recipient, subject, amount, int(clock.now())))
            conn.execute("UPDATE outbox SET status='sent' WHERE id=?", (oid,))
        conn.execute("COMMIT")
        return len(rows)
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def start_worker(get_engines, interval: float = 0.5) -> threading.Thread:
    def loop():
        while True:
            time.sleep(interval)
            for eng in list(get_engines()):
                try:
                    with eng.lock:
                        deliver_pending(eng)
                except Exception:
                    pass
    t = threading.Thread(target=loop, daemon=True, name="outbox-worker")
    t.start()
    return t
