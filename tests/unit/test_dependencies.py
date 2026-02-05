

from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException, Request
from app.core.dependencies import (
from app.utils.security import create_access_token

    get_current_user,
    get_current_user_id,
    get_optional_user_id,
    get_token_from_request,
)


@pytest.mark.asyncio
async def test_get_token_from_request():
    # 1. Test Authorization header
    mock_req = MagicMock(spec=Request)
    mock_cred = MagicMock()
    mock_cred.credentials = "test_token"
    assert get_token_from_request(mock_req, mock_cred) == "test_token"

    # 2. Test Cookie
    mock_req.cookies = {"access_token": "cookie_token"}
    assert get_token_from_request(mock_req, None) == "cookie_token"

    # 3. Test Missing
    mock_req.cookies = {}
with pytest.raises(HTTPException):
        get_token_from_request(mock_req, None)


@pytest.mark.asyncio
async def test_get_current_user_id(regular_user):

    token = create_access_token({"user_id": str(regular_user.id), "email": regular_user.email})
    assert get_current_user_id(token) == str(regular_user.id)


@pytest.mark.asyncio
async def test_get_current_user(regular_user, db_session):
    user = get_current_user(str(regular_user.id), db_session)
    assert user.id == regular_user.id


@pytest.mark.asyncio
async def test_get_optional_user_id():
    mock_cred = MagicMock()
    mock_cred.credentials = "test_token"
    # This will fail decode but return None if mocked properly or if jwt is real
    assert get_optional_user_id(None) is None
