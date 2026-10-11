"""Server-Sent Events bus: one-way gateway -> browser stream (live popups and chat)."""
import asyncio
import json
import threading
from collections import deque

from .schemas import Event


class Bus:
    def __init__(self, history: int = 500):
        self.history: deque = deque(maxlen=history)
        self.subs: set = set()
        self.lock = threading.Lock()
        self.counter = 0

    def publish(self, event: Event) -> int:
        with self.lock:
            self.counter += 1
            item = (self.counter, event)
            self.history.append(item)
            subs = list(self.subs)
        for loop, q in subs:
            try:
                loop.call_soon_threadsafe(q.put_nowait, item)
            except RuntimeError:       # the subscriber's loop has closed
                pass
        return self.counter

    def recent(self, n: int = 50) -> list:
        with self.lock:
            return list(self.history)[-n:]

    async def stream(self, replay: int = 50, last_id: int = 0):
        """Async generator of SSE frames. Replays recent history, then follows new events."""
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        sub = (loop, q)
        with self.lock:
            self.subs.add(sub)
        try:
            seen = last_id
            for i, ev in self.recent(replay):
                if i > seen:
                    seen = i
                    yield frame(i, ev)
            while True:
                try:
                    i, ev = await asyncio.wait_for(q.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if i > seen:
                    seen = i
                    yield frame(i, ev)
        finally:
            with self.lock:
                self.subs.discard(sub)


def frame(i: int, ev: Event) -> str:
    return f"id: {i}\nevent: {ev.type}\ndata: {json.dumps(ev.model_dump())}\n\n"
