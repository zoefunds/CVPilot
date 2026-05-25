"""
Tests for the public verify endpoint.
"""

from __future__ import annotations


def test_verify_rejects_malformed_hash(client) -> None:
    r = client.get("/api/v1/public/verify/not-a-hash")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_content_hash"


def test_verify_missing_hash_returns_404(client) -> None:
    # 64 valid hex chars but never stored on the contract.
    fake = "0" * 64
    r = client.get(f"/api/v1/public/verify/{fake}")
    # In stub-test mode the contract read raises NotImplementedError and
    # is caught as None by fetch_stored_evaluation, producing 404.
    assert r.status_code == 404
    body = r.json()
    assert body["content_hash"] == fake
    assert body["found"] is False
