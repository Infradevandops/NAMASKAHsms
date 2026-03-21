"""Unit tests for SecurityHeadersMiddleware CSP output."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security import SecurityHeadersMiddleware


@pytest.fixture(scope="module")
def secured_client():
    test_app = FastAPI()

    @test_app.get("/ping")
    def ping():
        return {"ok": True}

    test_app.add_middleware(SecurityHeadersMiddleware)
    return TestClient(test_app, raise_server_exceptions=True)


def _csp(client) -> str:
    resp = client.get("/ping")
    return resp.headers["content-security-policy"]


def test_csp_header_present(secured_client):
    resp = secured_client.get("/ping")
    assert "content-security-policy" in resp.headers


def test_csp_header_contains_script_src_attr_unsafe_inline(secured_client):
    assert "script-src-attr 'unsafe-inline'" in _csp(secured_client)


def test_csp_header_still_contains_nonce_for_script_src(secured_client):
    csp = _csp(secured_client)
    assert "script-src" in csp
    assert "'nonce-" in csp


def test_csp_nonce_changes_per_request(secured_client):
    """Each request must get a fresh nonce — reusing nonces defeats the purpose."""
    def extract_nonce(csp: str) -> str:
        for part in csp.split(";"):
            part = part.strip()
            if part.startswith("script-src "):
                for token in part.split():
                    if token.startswith("'nonce-"):
                        return token
        return ""

    nonce1 = extract_nonce(_csp(secured_client))
    nonce2 = extract_nonce(_csp(secured_client))
    assert nonce1 != "" and nonce2 != ""
    assert nonce1 != nonce2


def test_csp_blocks_object_src(secured_client):
    assert "object-src 'none'" in _csp(secured_client)


def test_x_frame_options_deny(secured_client):
    resp = secured_client.get("/ping")
    assert resp.headers["x-frame-options"] == "DENY"


def test_x_content_type_options_nosniff(secured_client):
    resp = secured_client.get("/ping")
    assert resp.headers["x-content-type-options"] == "nosniff"
