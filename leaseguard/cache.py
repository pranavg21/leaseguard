"""A small, thread-safe least-recently-used cache keyed by content hash."""

import hashlib
import threading
from collections import OrderedDict
from typing import Generic, TypeVar

V = TypeVar("V")


def content_key(*parts: str) -> str:
    """Return a SHA-256 key for the given parts.

    Args:
        *parts: Strings that together determine a result.

    Returns:
        A hex digest. Parts are length-prefixed so ("ab", "c") and ("a", "bc")
        produce different keys.
    """
    digest = hashlib.sha256()
    for part in parts:
        encoded = part.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big") + encoded)
    return digest.hexdigest()


class LRUCache(Generic[V]):
    """Bounded mapping that evicts the least recently used entry."""

    def __init__(self, max_size: int) -> None:
        """Create a cache.

        Args:
            max_size: Maximum number of entries to keep.
        """
        self._max_size = max_size
        self._items: OrderedDict[str, V] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> V | None:
        """Return a cached value and mark it as recently used.

        Args:
            key: Cache key.

        Returns:
            The value, or None if absent.
        """
        with self._lock:
            if key not in self._items:
                return None
            self._items.move_to_end(key)
            return self._items[key]

    def put(self, key: str, value: V) -> None:
        """Store a value, evicting the oldest entry if the cache is full.

        Args:
            key: Cache key.
            value: Value to store.
        """
        with self._lock:
            self._items[key] = value
            self._items.move_to_end(key)
            if len(self._items) > self._max_size:
                self._items.popitem(last=False)

    def clear(self) -> None:
        """Remove every entry."""
        with self._lock:
            self._items.clear()

    def __len__(self) -> int:
        """Return the number of cached entries."""
        return len(self._items)
