

from unittest.mock import AsyncMock, MagicMock, patch
from app.models.user import User

@patch("app.api.core.auth.get_notification_service")
@patch("app.services.textverified_service.TextVerifiedService")
def test_complete_user_journey(MockTVService, mock_get_notify, client, db_session):

    """
    Test the complete user journey:
    1. Register
    2. Login (get token)
    3. Add Credits (simulated)
    4. Create Verification
    5. Check Status
    """

    # 1. Setup Mocks
    # Mock TextVerified Service to avoid external API calls
    mock_instance = MockTVService.return_value
    mock_instance.enabled = True
    mock_instance.buy_number = AsyncMock(
        return_value={
            "cost": 0.50,
            "phone_number": "+1555123456",
            "activation_id": "mock_activation_id",
        }
    )

    # Mock Notification Service to avoid SMTP errors/calls
    mock_notify = MagicMock()
    mock_notify.send_email = AsyncMock(return_value=True)
    mock_get_notify.return_value = mock_notify

    # 2. Register
    reg_data = {
        "email": "journey_user@example.com",
        "password": "SecurePassword123!",
        "referral_code": None,
    }
    # Note: Using /api/v1/auth/register
    response = client.post("/api/v1/auth/register", json=reg_data)
    assert response.status_code == 201, f"Registration failed: {response.text}"

    user_id = response.json()["user"]["id"]

    # Verify User created in DB
    user = db_session.query(User).filter(User.id == user_id).first()
    assert user is not None
    assert user.email == "journey_user@example.com"

    # Manually verify email in DB (Simulate clicking verification link)
    user.email_verified = True
    db_session.commit()

    # 3. Login
    login_data = {"email": "journey_user@example.com", "password": "SecurePassword123!"}
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Add Credits (Simulate Payment via DB)
    # We directly update the user credits since we can't easily mock the full payment webhook flow here
    user.credits = 10.0
    user.free_verifications = 0
    db_session.commit()
    db_session.refresh(user)

    # Check Balance via API
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["credits"] == 10.0

    # 5. Create Verification
    verify_data = {"service_name": "whatsapp", "country": "us"}
    # Endpoint: /api/v1/verify/create
    response = client.post("/api/v1/verify/create", json=verify_data, headers=headers)
    assert response.status_code == 201, f"Verification creation failed: {response.text}"

    verify_id = response.json()["id"]
    assert response.json()["status"] == "pending"
    assert response.json()["phone_number"] == "+1555123456"
    assert response.json()["cost"] == 0.50

    # Verify Cost Deduction
    db_session.refresh(user)
    assert user.credits == 9.50  # 10.0 - 0.50

    # 6. Check Status
    response = client.get(f"/api/v1/verify/{verify_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == verify_id
    assert response.json()["status"] == "pending"