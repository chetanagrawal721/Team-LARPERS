import os
import pathlib
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8000")
