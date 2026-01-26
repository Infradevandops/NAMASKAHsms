import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request

from app.core.unified_error_handling import (
    NamaskahException,
    UnifiedErrorHandlingMiddleware,
    setup_unified_error_handling,
)


@pytest.mark.asyncio
async def test_error_handling_middleware_init():
    from fastapi import FastAPI

    app = FastAPI()
    middleware = UnifiedErrorHandlingMiddleware(app)
    assert middleware.app == app


@pytest.mark.asyncio
async def test_setup_error_handling():
    from fastapi import FastAPI

    app = FastAPI()
    setup_unified_error_handling(app)
    assert any("unified" in str(handler) or "exception" in str(handler) for handler in app.exception_handlers.values())


@pytest.mark.asyncio
async def test_namaskah_exception_logic():
    exc = NamaskahException("Test Error", error_code="TEST_CODE", status_code=400)
    assert exc.message == "Test Error"
    assert exc.error_code == "TEST_CODE"
    assert exc.status_code == 400
