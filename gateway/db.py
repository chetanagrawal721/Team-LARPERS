"""Gateway control-plane state (one SQLite file per domain engine). Business data lives in the domain DB."""
import sqlite3

STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS nonces (nonce TEXT PRIMARY KEY, agent TEXT, ts INTEGER);
CREATE TABLE IF NOT EXISTS audit_log (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, prev_hash TEXT NOT NULL, ts INTEGER NOT NULL,
  agent TEXT, action TEXT, payload_json TEXT NOT NULL, decision TEXT, rule TEXT,
  decision_path TEXT, policy_hash TEXT, entry_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY, created_ts INTEGER, agent TEXT, action TEXT, requester TEXT,
  proposal_json TEXT, decision_json TEXT, status TEXT, parent_id TEXT, meta_json TEXT);
CREATE TABLE IF NOT EXISTS seals (
  decision_id TEXT PRIMARY KEY, token_json TEXT NOT NULL, nonce TEXT UNIQUE, used INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT, decision_id TEXT, user TEXT, action TEXT, ts INTEGER, note TEXT);
CREATE TABLE IF NOT EXISTS policy_versions (hash TEXT PRIMARY KEY, policy_json TEXT, ts INTEGER);
CREATE TABLE IF NOT EXISTS frozen_agents (agent TEXT PRIMARY KEY, reason TEXT, ts INTEGER);
CREATE TABLE IF NOT EXISTS agent_touched (agent TEXT, label TEXT, ts INTEGER, PRIMARY KEY (agent, label));
CREATE TABLE IF NOT EXISTS shadow_sessions (
  id TEXT PRIMARY KEY, agent TEXT, requester TEXT, status TEXT, reason TEXT, db_path TEXT,
  trigger_decision TEXT, created_ts INTEGER, base_hash TEXT);
CREATE TABLE IF NOT EXISTS shadow_steps (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, seq INTEGER, action TEXT,
  args_json TEXT, effect_json TEXT, ts INTEGER);
"""


def connect(path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_state(path) -> sqlite3.Connection:
    conn = connect(path)
    conn.executescript(STATE_SCHEMA)
    return conn
