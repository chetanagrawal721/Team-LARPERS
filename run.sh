#!/bin/sh
# Start the gateway (:8000) and the frontend (:5173). Needs .env (copy .env.example) and `npm install` in frontend/.
PY=.venv/Scripts/python
[ -x "$PY" ] || PY=.venv/bin/python
$PY -m uvicorn gateway.main:app --port 8000 &
(cd frontend && npm run dev) &
wait
