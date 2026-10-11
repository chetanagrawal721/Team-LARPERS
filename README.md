# SEALGATE

Effect-sealed authorization for AI agents (VORTEXA 3.0, C-01 ActionGate).
Every agent action is first run on a sandbox copy to measure its real effect, compared with what the user asked for, decided by deterministic rules, and approved only as a seal bound to that exact effect.

See `docs/` for the design, build playbook and project journal. Setup and run instructions are at the bottom.

## Setup (Windows, Git Bash)
```bash
python -m venv .venv && source .venv/Scripts/activate
pip install -r gateway/requirements.txt
cp .env.example .env            # then fill placeholders (keys are demo-only)
(cd frontend && npm install)
git config core.hooksPath .githooks
```

## Run
```bash
./run.sh            # gateway on :8000, frontend on :5173
pytest -q           # tests
```
