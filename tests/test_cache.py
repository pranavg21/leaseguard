"""Tests for leaseguard/cache.py."""

import threading

from leaseguard.cache import LRUCache, content_key


def test_content_key_is_stable_and_length_prefixed() -> None:
    assert content_key("a", "b") == content_key("a", "b")
    assert content_key("ab", "c") != content_key("a", "bc")


def test_lru_evicts_least_recently_used() -> None:
    cache: LRUCache[int] = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0


def test_cache_is_thread_safe() -> None:
    cache: LRUCache[int] = LRUCache(50)
    threads = [threading.Thread(target=lambda i=i: cache.put(str(i), i)) for i in range(40)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(cache) == 40
