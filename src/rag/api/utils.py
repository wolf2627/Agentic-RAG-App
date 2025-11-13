"""Utility functions for API operations."""

import json


def serialize_event(event_name: str, payload: dict) -> bytes:
    """Serialize an event for streaming response."""
    return (json.dumps({"event": event_name, "data": payload}) + "\n").encode("utf-8")
