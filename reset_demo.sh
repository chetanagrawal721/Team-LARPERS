#!/bin/sh
# Restore the demo to its initial state (fresh data, empty audit log). Stop the gateway first, or use POST /demo/reset.
PY=.venv/Scripts/python
[ -x "$PY" ] || PY=.venv/bin/python
$PY -m gateway.reset
