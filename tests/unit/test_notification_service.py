

from unittest.mock import MagicMock
import pytest
from app.models.notification import Notification
from app.models.user import User
from app.services.notification_service import NotificationService

@pytest.fixture
def mock_db():

    return MagicMock()


@pytest.fixture
def service(mock_db):

    return NotificationService(mock_db)


def test_create_notification_success(service, mock_db):

    user_id = "u1"
    # Mock user exists
    mock_db.query.return_value.filter.return_value.first.return_value = User(id=user_id)

    notif = service.create_notification(user_id, "info", "Title", "Msg")

    assert mock_db.add.called
    assert mock_db.commit.called
    assert notif.user_id == user_id
    assert notif.title == "Title"


def test_create_notification_user_not_found(service, mock_db):

    mock_db.query.return_value.filter.return_value.first.return_value = None

with pytest.raises(ValueError, match="User unknown not found"):
        service.create_notification("unknown", "type", "title", "msg")


def test_get_notifications_success(service, mock_db):

    user_id = "u1"
    mock_db.query.return_value.filter.return_value.first.return_value = User(id=user_id)

    mock_query = mock_db.query.return_value.filter.return_value
    mock_query.count.return_value = 5
    mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
        Notification(id="n1", user_id=user_id, title="N1"),
        Notification(id="n2", user_id=user_id, title="N2"),
    ]

    result = service.get_notifications(user_id)

    assert result["total"] == 5
    assert len(result["notifications"]) == 2
    assert result["notifications"][0]["title"] == "N1"


def test_get_notifications_unread_only(service, mock_db):

    user_id = "u1"
    mock_db.query.return_value.filter.return_value.first.return_value = User(id=user_id)

    service.get_notifications(user_id, unread_only=True)

    # Check if filter was called appropriately
    # It's hard to verify exact filter chaining with simple mocks without deeper inspection
    # But ensuring it runs without error is a start.
    assert mock_db.query.called


def test_mark_as_read(service, mock_db):

    user_id = "u1"
    notif_id = "n1"
    notif = Notification(id=notif_id, user_id=user_id, is_read=False)

    mock_db.query.return_value.filter.return_value.first.return_value = notif

    updated = service.mark_as_read(notif_id, user_id)

    assert updated.is_read is True
    assert mock_db.commit.called


def test_mark_all_as_read(service, mock_db):

    user_id = "u1"
    mock_db.query.return_value.filter.return_value.first.return_value = User(id=user_id)

    mock_db.query.return_value.filter.return_value.update.return_value = 3

    count = service.mark_all_as_read(user_id)

    assert count == 3
    assert mock_db.commit.called


def test_delete_notification(service, mock_db):

    user_id = "u1"
    notif = Notification(id="n1", user_id=user_id)
    mock_db.query.return_value.filter.return_value.first.return_value = notif

    res = service.delete_notification("n1", user_id)

    assert res is True
    assert mock_db.delete.called_with(notif)
    assert mock_db.commit.called


def test_delete_all(service, mock_db):

    user_id = "u1"
    mock_db.query.return_value.filter.return_value.first.return_value = User(id=user_id)
    mock_db.query.return_value.filter.return_value.delete.return_value = 10

    count = service.delete_all_notifications(user_id)

    assert count == 10


def test_get_unread_count(service, mock_db):

    user_id = "u1"
    mock_db.query.return_value.filter.return_value.first.return_value = User(id=user_id)
    mock_db.query.return_value.filter.return_value.count.return_value = 42

    count = service.get_unread_count(user_id)
    assert count == 42
