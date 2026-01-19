import pytest
from botocore.exceptions import BotoCoreError, ClientError
from cryptography.fernet import InvalidToken
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import AuthorizationError, ExternalServiceError
from app.utils.exception_handling import (
    AWSServiceError,
    DatabaseError,
    EncryptionError,
    ValidationError,
    handle_aws_exceptions,
    handle_database_exceptions,
    handle_encryption_exceptions,
    handle_http_client_exceptions,
    safe_int_conversion,
    safe_json_parse,
)


def test_safe_int_conversion():
    assert safe_int_conversion("123") == 123
    assert safe_int_conversion("abc", default=10) == 10
    assert safe_int_conversion(None, default=5) == 5


def test_safe_json_parse():
    assert safe_json_parse('{"a":1}') == {"a": 1}
    assert safe_json_parse("invalid", default={"b": 2}) == {"b": 2}
    assert safe_json_parse(None, default={}) == {}


def test_handle_database_exceptions():
    @handle_database_exceptions
    def fail(exc):
        raise exc

    with pytest.raises(ValidationError):
        fail(IntegrityError("stmt", "params", "orig"))

    with pytest.raises(DatabaseError):
        fail(OperationalError("stmt", "params", "orig"))


def test_handle_aws_exceptions():
    @handle_aws_exceptions("s3")
    def fail(exc):
        raise exc

    # ClientError needs a response dict
    err_resp = {"Error": {"Code": "AccessDenied", "Message": "Denied"}}
    with pytest.raises(AuthorizationError):
        fail(ClientError(err_resp, "operation"))

    err_resp_not_found = {"Error": {"Code": "NoSuchKey", "Message": "Missing"}}
    with pytest.raises(ValidationError):
        fail(ClientError(err_resp_not_found, "operation"))

    err_resp_generic = {"Error": {"Code": "Other", "Message": "Fail"}}
    with pytest.raises(AWSServiceError):
        fail(ClientError(err_resp_generic, "operation"))

    with pytest.raises(AWSServiceError):
        fail(BotoCoreError())


def test_handle_encryption_exceptions():
    @handle_encryption_exceptions
    def fail(exc):
        raise exc

    with pytest.raises(EncryptionError):
        fail(InvalidToken())

    with pytest.raises(EncryptionError):
        fail(ValueError("Invalid key"))

    # Normal ValueError passes through
    with pytest.raises(ValueError):
        fail(ValueError("Other error"))


def test_handle_http_client_exceptions():
    @handle_http_client_exceptions("api")
    def fail(exc):
        raise exc

    with pytest.raises(ExternalServiceError) as exc:
        fail(ConnectionError("Fail"))
    assert "Failed to connect" in str(exc.value)

    with pytest.raises(ExternalServiceError) as exc:
        fail(TimeoutError("Time"))
    assert "Timeout" in str(exc.value)

    # General Exception with "timeout" string
    with pytest.raises(ExternalServiceError) as exc:
        fail(Exception("Read timeout occurred"))
    assert "Timeout" in str(exc.value)
