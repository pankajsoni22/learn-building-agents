"""
A tiny disk cache for Gemini API responses.

Why this exists: Google's free tier allows only ~20 requests/day PER MODEL
(we hit this limit while debugging Lesson 2). Every time you re-run a script
to fix a bug or re-read an example, you pay the same quota cost — even if
the request is byte-for-byte identical to one you already made.

This cache stores (request -> response) pairs on disk, keyed by a hash of
the exact request body. Re-running the same script with the same prompt
costs ZERO quota on the second run. It only costs quota the first time a
specific request is ever made.

This is a development aid, not a production caching strategy — a real
production cache would need invalidation, TTLs, and per-user scoping. We
don't need those: the LLM for a fixed prompt + tools is being asked the
same question, so an identical answer is fine to reuse.
"""

import hashlib
import json
import os

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".gemini_cache")


def _cache_key(request_body: dict) -> str:
    """Hash the exact request body so identical requests map to the same file.

    json.dumps with sort_keys=True guarantees the same dict always produces
    the same string, regardless of key insertion order.
    """
    serialized = json.dumps(request_body, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def get_cached(request_body: dict) -> dict | None:
    """Return a cached response for this exact request, or None if not cached."""
    key = _cache_key(request_body)
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def save_to_cache(request_body: dict, response_body: dict) -> None:
    """Save a response so the next identical request skips the API call."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = _cache_key(request_body)
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w") as f:
        json.dump(response_body, f, indent=2)
