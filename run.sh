#!/bin/sh
.venv/Scripts/python -m uvicorn gateway.main:app --reload --port 8000 &
(cd frontend && npm run dev) &
wait
