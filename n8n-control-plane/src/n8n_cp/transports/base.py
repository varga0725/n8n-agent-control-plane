"""Transport interface + raw response container."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol


@dataclass
class RawResponse:
    status: int
    body: Any
    headers: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


class Transport(Protocol):
    """Anything that can perform a single n8n API request.

    Implementations: RestApiTransport (default), MockTransport (tests), and a
    future N8nCliTransport. The control-plane client only sees this interface.
    """

    def request(self, method: str, path: str, *,
                query: Optional[dict] = None,
                body: Optional[Any] = None,
                timeout_ms: int = 30000) -> RawResponse:
        ...
