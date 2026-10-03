from typing import Any

class ValidationError(ValueError):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category

class UnsupportedVersion(ValidationError):
    def __init__(self, value: Any) -> None:
        super().__init__("unsupported_spec_version", f"unsupported spec version: {value!r}")
