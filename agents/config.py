"""Agent-side configuration. Agents know only the gateway URL and their own signing key."""
import os

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8000")
