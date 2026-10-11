"""Reset the demo to its initial state: re-seed every domain and clear the gateway state (`python -m gateway.reset`)."""
import importlib
import pathlib
import shutil
import sys

from . import config


def reset_all(data_dir=None) -> None:
    d = pathlib.Path(data_dir or config.DATA_DIR)
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.db*"):
        f.unlink(missing_ok=True)
    shutil.rmtree(d / "sandbox", ignore_errors=True)
    for domain in config.DOMAINS:
        importlib.import_module(f"gateway.seed.{domain}_seed").seed(d / f"{domain}.db")


if __name__ == "__main__":
    reset_all(sys.argv[1] if len(sys.argv) > 1 else None)
    print("demo reset: " + ", ".join(config.DOMAINS))
