"""
Small in-memory, per-process cache for simulation results that have just
been run but not yet (or never) saved to the database.

Why not put this in the DB? Because a full path matrix can be tens of MB,
and most runs are exploratory (the user tweaks inputs repeatedly before
deciding to save one). Keeping un-saved runs purely in server memory, with
a short TTL, avoids bloating storage (constraint C3) while still letting
the results page, "Save this run", and "Export" actions work off the same
token without re-running the simulation.

This is process-local and non-persistent by design: restarting the server
clears it, and that's fine because nothing of record lives here until the
user explicitly saves.
"""
from __future__ import annotations

import threading
import time
import uuid
from typing import Optional

_LOCK = threading.Lock()
_STORE: dict[str, dict] = {}
_TTL_SECONDS = 30 * 60  # 30 minutes


def _purge_expired():
    now = time.time()
    expired = [k for k, v in _STORE.items() if now - v["_created"] > _TTL_SECONDS]
    for k in expired:
        _STORE.pop(k, None)


def put(user_id: int, payload: dict) -> str:
    with _LOCK:
        _purge_expired()
        token = uuid.uuid4().hex
        _STORE[token] = {**payload, "_user_id": user_id, "_created": time.time()}
        return token


def get(token: str, user_id: int) -> Optional[dict]:
    with _LOCK:
        _purge_expired()
        entry = _STORE.get(token)
        if not entry or entry["_user_id"] != user_id:
            return None
        return entry
