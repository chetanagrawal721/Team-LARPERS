"""Run one scripted scenario as its own process: `python -m agents.run bank-refund` or `--text "..."`."""
import argparse
import sys

import httpx

from . import scenarios


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", nargs="?")
    ap.add_argument("--text")
    ns = ap.parse_args(argv)
    name, text = ns.scenario, ns.text
    if not name and text:
        name, text = scenarios.from_text(text)
    if not name:
        print("no matching scenario", file=sys.stderr)
        return 2
    try:
        scenarios.run(name, text=text if ns.scenario is None else None)
    except httpx.HTTPError as e:
        print(f"gateway unreachable: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
