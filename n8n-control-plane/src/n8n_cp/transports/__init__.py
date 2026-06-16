"""Transport abstraction.

The business logic does not depend on HTTP directly. A transport turns a
(method, path, query, body) into a raw response. This makes it trivial to swap
in a CLI-backed transport or a mock for offline tests.
"""
from .base import Transport, RawResponse
from .rest import RestApiTransport
from .mock import MockTransport
from .cli import N8nCliTransport

__all__ = ["Transport", "RawResponse", "RestApiTransport", "MockTransport",
           "N8nCliTransport"]
