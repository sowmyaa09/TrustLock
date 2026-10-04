import json
from typing import List, Callable, Optional
from .schema import TelemetryEvent


class TelemetryLogger:
    """Collector and audit logger for structured telemetry events."""

    def __init__(self):
        self._events: List[TelemetryEvent] = []
        self._listeners: List[Callable[[TelemetryEvent], None]] = []

    def log(self, event: TelemetryEvent) -> TelemetryEvent:
        """Record a telemetry event and notify listeners."""
        self._events.append(event)
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"[TelemetryLogger Warning] Listener error: {e}")
        return event

    def subscribe(self, listener: Callable[[TelemetryEvent], None]) -> None:
        """Register a callback for real-time event streaming."""
        self._listeners.append(listener)

    def get_events(self, session_id: Optional[str] = None) -> List[TelemetryEvent]:
        """Retrieve recorded telemetry events, optionally filtered by session."""
        if session_id:
            return [e for e in self._events if e.session_id == session_id]
        return list(self._events)

    def clear(self) -> None:
        """Clear recorded events."""
        self._events.clear()

    def export_json(self, session_id: Optional[str] = None) -> str:
        """Export telemetry events as JSON array."""
        events = self.get_events(session_id)
        return json.dumps([e.model_dump() for e in events], indent=2)
