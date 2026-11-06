"""
Kant Compiler Toolchain - Server-Sent Events (SSE) Broker
Multiplexes real-time telemetry updates and state changes to connected browsers.
"""

import json
import queue
import threading
import time
from typing import Any, Dict, Optional, Set


class SSEBroker:
    """Thread-safe Server-Sent Events broker and client multiplexer."""

    def __init__(self, ping_interval_seconds: int = 15):
        self.ping_interval = ping_interval_seconds
        self.lock = threading.Lock()
        self.clients: Set[queue.Queue] = set()
        self._running = True

        # Start background heartbeat daemon
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="Kant-SSE-Heartbeat",
            daemon=True,
        )
        self._heartbeat_thread.start()

    def register_client(self) -> queue.Queue:
        """Register a new SSE client connection and return its message queue."""
        client_queue: queue.Queue = queue.Queue(maxsize=128)
        with self.lock:
            self.clients.add(client_queue)
        # Send initial connection confirmation
        init_msg = self.format_sse_message(
            event_type="connected",
            data={"status": "connected", "broker": "KantSSEBroker/0.1.0"},
        )
        try:
            client_queue.put_nowait(init_msg)
        except queue.Full:
            pass
        return client_queue

    def unregister_client(self, client_queue: queue.Queue) -> None:
        """Unregister a disconnected SSE client."""
        with self.lock:
            self.clients.discard(client_queue)

    def client_count(self) -> int:
        """Return the number of currently connected SSE clients."""
        with self.lock:
            return len(self.clients)

    @staticmethod
    def format_sse_message(event_type: str, data: Any) -> str:
        """Format an event and data payload according to the W3C SSE standard."""
        payload_str = json.dumps(data, ensure_ascii=False)
        return f"event: {event_type}\ndata: {payload_str}\n\n"

    def broadcast(self, event_type: str, data: Any) -> None:
        """Broadcast an event to all connected SSE clients."""
        formatted = self.format_sse_message(event_type, data)
        with self.lock:
            dead_clients = []
            for q in self.clients:
                try:
                    q.put_nowait(formatted)
                except queue.Full:
                    dead_clients.append(q)
            for dead in dead_clients:
                self.clients.discard(dead)

    def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat ping comments to keep connections alive."""
        ping_comment = ": ping\n\n"
        while self._running:
            time.sleep(self.ping_interval)
            if not self._running:
                break
            with self.lock:
                dead_clients = []
                for q in self.clients:
                    try:
                        q.put_nowait(ping_comment)
                    except queue.Full:
                        dead_clients.append(q)
                for dead in dead_clients:
                    self.clients.discard(dead)

    def shutdown(self) -> None:
        """Terminate heartbeat loop and release all client queues."""
        self._running = False
        with self.lock:
            for q in self.clients:
                try:
                    q.put_nowait(None)  # Sentinel to unblock consumers
                except Exception:
                    pass
            self.clients.clear()
