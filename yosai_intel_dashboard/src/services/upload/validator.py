import base64
import json
from typing import Any, Callable, Iterable, List, Mapping

from services.upload.protocols import UploadValidatorProtocol


class ClientSideValidator(UploadValidatorProtocol):
    """Validate uploaded file name and size before processing.

    The validator mirrors the behaviour of the client side checks shipped in the
    accompanying JavaScript.  Instances can be configured with per-extension size
    limits, magic number expectations, duplicate tracking and arbitrary rule
    hooks.
    """

    def __init__(
        self,
        allowed_ext: Iterable[str] | None = None,
        *,
        max_size: int | None = None,
        size_limits: Mapping[str, int] | None = None,
        magic_numbers: Mapping[str, Iterable[bytes | str]] | None = None,
        track_duplicates: bool = True,
        hooks: Iterable[Callable[[str, bytes], Any]] | None = None,
    ) -> None:
        self.allowed_ext = {
            e.lower() for e in (allowed_ext or [".csv", ".xlsx", ".xls", ".json"])
        }
        self.max_size = max_size
        self.size_limits = {k.lower(): v for k, v in (size_limits or {}).items()}
        self.magic_numbers: dict[str, List[bytes]] = {}
        for ext, vals in (magic_numbers or {}).items():
            self.magic_numbers[ext.lower()] = [
                v if isinstance(v, bytes) else bytes.fromhex(v) for v in vals
            ]
        self.track_duplicates = track_duplicates
        self.hooks = list(hooks or [])
        self._seen: set[str] = set()

    # ------------------------------------------------------------------
    def _decode_content(self, content: str) -> bytes:
        try:
            data = content.split(",", 1)[1]
            return base64.b64decode(data)
        except Exception:
            return b""

    # ------------------------------------------------------------------
    def validate(self, filename: str, content: str) -> tuple[bool, str]:
        """Validate a single uploaded file."""

        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        issues: List[str] = []

        if self.allowed_ext and ext not in self.allowed_ext:
            issues.append("unsupported_type")

        data = self._decode_content(content)
        if not data:
            issues.append("decode_error")

        limit = self.size_limits.get(ext, self.max_size)
        if limit is not None and len(data) > limit:
            issues.append("too_large")

        magics = self.magic_numbers.get(ext)
        if magics:
            header = data[: max(len(m) for m in magics)]
            if not any(header.startswith(m) for m in magics):
                issues.append("bad_magic")

        if self.track_duplicates:
            if filename in self._seen:
                issues.append("duplicate")
            self._seen.add(filename)

        for hook in self.hooks:
            try:
                result = hook(filename, data)
                if isinstance(result, tuple):
                    valid, msg = result
                    if not valid:
                        issues.append(msg or "custom_error")
                elif result is False:
                    issues.append("custom_error")
                elif isinstance(result, str) and result:
                    issues.append(result)
            except Exception as exc:  # pragma: no cover - hook error handling
                issues.append(f"hook_error:{exc}")

        return len(issues) == 0, ", ".join(issues)

    # ------------------------------------------------------------------
    def to_json(self) -> str:
        """Return a JSON configuration for the browser validator."""

        return json.dumps(
            {
                "allowed_ext": sorted(self.allowed_ext),
                "max_size": self.max_size,
                "size_limits": self.size_limits,
                "magic_numbers": {
                    k: [m.hex() for m in v] for k, v in self.magic_numbers.items()
                },
                "track_duplicates": self.track_duplicates,
            }
        )


__all__ = ["ClientSideValidator"]
