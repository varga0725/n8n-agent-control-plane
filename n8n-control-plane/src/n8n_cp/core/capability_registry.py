"""Capability registry (spec section 3: capability-registry).

Bridges discovered instance capabilities (``core/capabilities.py``) with the tool
registry (``endpoints.py``): given a Capabilities object, it answers which named
tools are currently usable, and explains why a tool is not. The tool dispatcher
consults this before any call so we never invoke an unsupported/disabled feature.
"""
from __future__ import annotations

from typing import Optional

from .capabilities import Capabilities, fetch_capabilities
from ..endpoints import REGISTRY, ToolSpec


class CapabilityRegistry:
    def __init__(self, capabilities: Capabilities):
        self.caps = capabilities

    @classmethod
    def discover(cls, client) -> "CapabilityRegistry":
        return cls(fetch_capabilities(client))

    def is_tool_available(self, tool_name: str) -> bool:
        spec = REGISTRY.get(tool_name)
        if spec is None:
            return False
        if not self.caps.is_available(spec.domain):
            return False
        if spec.beta and spec.domain not in self.caps.available_domains:
            return False
        return True

    def reason_unavailable(self, tool_name: str) -> Optional[str]:
        spec = REGISTRY.get(tool_name)
        if spec is None:
            return f"Unknown tool '{tool_name}'."
        if spec.beta and spec.domain not in self.caps.available_domains:
            return (f"Beta feature '{spec.domain}' is not enabled on this instance "
                    f"(requires the relevant feature flag + /discover support).")
        return self.caps.reason_unavailable(spec.domain)

    def available_tools(self) -> list[str]:
        return [name for name in REGISTRY if self.is_tool_available(name)]

    def unavailable_tools(self) -> dict[str, str]:
        out = {}
        for name in REGISTRY:
            if not self.is_tool_available(name):
                out[name] = self.reason_unavailable(name) or "unavailable"
        return out
