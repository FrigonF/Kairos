"""
KAIROS AI Structured Response Schema.

Provides clean dataclasses for formatted router outputs.
"""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, Optional

DEFAULT_UNSUPPORTED_MESSAGE = "I can only help with KAIROS investigation commands."


@dataclass
class RouterResponse:
    """
    Structured output returned by the KAIROS AI intent router.
    """
    intent: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None
    raw_llm_output: Optional[str] = None

    def to_dict(self, include_metadata: bool = False) -> Dict[str, Any]:
        """Convert response to standard dictionary format."""
        data: Dict[str, Any] = {
            "intent": self.intent,
            "arguments": self.arguments,
        }
        if self.message is not None:
            data["message"] = self.message
        if include_metadata and self.raw_llm_output is not None:
            data["raw_llm_output"] = self.raw_llm_output
        return data

    def to_json(self, indent: int = 2, include_metadata: bool = False) -> str:
        """Serialize to formatted JSON string."""
        return json.dumps(self.to_dict(include_metadata=include_metadata), indent=indent)

    @classmethod
    def unsupported(cls, message: str = DEFAULT_UNSUPPORTED_MESSAGE, raw_llm_output: Optional[str] = None) -> "RouterResponse":
        """Factory for unsupported / invalid queries."""
        return cls(
            intent="unsupported",
            arguments={},
            message=message,
            raw_llm_output=raw_llm_output,
        )
