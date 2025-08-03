"""Key derivation and rotation utilities.

This module provides a small HKDF implementation and a :class:`KeyManager`
that can rotate the root key and derive context specific keys.  The
implementation is intentionally lightweight so it can be used in tests without
external dependencies.
"""

from __future__ import annotations

from typing import Callable, Iterable

import hashlib
import hmac


def hkdf(key_material: bytes, *, context: bytes, length: int = 32) -> bytes:
    """Derive key material using a simplified HKDF construction.

    The function uses HMAC-SHA256 as the underlying hash.  Only the ``info``
    parameter (called ``context`` here) is exposed since that's all the
    library currently needs.  ``length`` specifies the number of bytes to
    return.

    Args:
        key_material: Initial key material.
        context: Context specific information (``info`` in the HKDF spec).
        length: Desired number of bytes to return. Defaults to ``32``.

    Returns:
        Derived key bytes of ``length`` size.
    """

    # Extract step with an empty salt.  This keeps the function deterministic
    # which is useful for tests.
    hash_len = hashlib.sha256().digest_size
    prk = hmac.new(b"\x00" * hash_len, key_material, hashlib.sha256).digest()

    # Expand step
    t = b""
    okm = b""
    counter = 1
    while len(okm) < length:
        t = hmac.new(prk, t + context + bytes([counter]), hashlib.sha256).digest()
        okm += t
        counter += 1

    return okm[:length]


class KeyManager:
    """Manage a root key and derive sub keys for different purposes."""

    def __init__(self, root_key: bytes, writers: Iterable[Callable[[bytes], None]] | None = None):
        self._root_key = root_key
        self._writers = list(writers or [])

    def derive(self, purpose: str, *, length: int = 32) -> bytes:
        """Deterministically derive a key for the given ``purpose``."""

        return hkdf(self._root_key, context=purpose.encode("utf-8"), length=length)

    def rotate(self, new_root_key: bytes) -> None:
        """Rotate the stored root key and persist it using the provided writers."""

        self._root_key = new_root_key
        for writer in self._writers:
            writer(new_root_key)

