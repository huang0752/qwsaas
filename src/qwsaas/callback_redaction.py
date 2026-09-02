from __future__ import annotations

from typing import Any


class SafeCallbackRepr:
    """A callback model whose repr is safe for routine diagnostics."""

    def to_safe_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.to_safe_dict()!r})"
