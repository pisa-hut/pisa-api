"""Validation shared by wrapper-facing service entry points."""

from typing import Any


def validate_identity(value: Any, field_name: str) -> str:
    """Return an explicitly supplied, non-blank identity value unchanged."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty or whitespace")
    return value


__all__ = ["validate_identity"]
