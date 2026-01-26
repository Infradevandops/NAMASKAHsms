def test_cannot_modify_own_tier(client, freemium_user_token):
    """Users cannot modify their own tier."""
    response = client.put(
        "/api/user/tier",
        headers={"Authorization": f"Bearer {freemium_user_token}"},
        json={"tier": "custom"},
    )
    assert response.status_code in [403, 404]


def test_no_tier_info_leakage(client):
    """402 errors don't leak sensitive info without auth."""
    response = client.get("/api/keys")
    assert response.status_code == 401  # Not 402


def test_admin_only_tier_changes(client, regular_user_token, user_id):
    """Only admins can change user tiers."""
    response = client.put(
        f"/api/admin/users/{user_id}/tier",
        headers={"Authorization": f"Bearer {regular_user_token}"},
        json={"tier": "pro"},
    )
    assert response.status_code == 403


def test_tier_sql_injection(client, admin_token):
    """Tier queries are safe from SQL injection."""
    response = client.put(
        "/api/admin/users/1/tier",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"tier": "pro'; DROP TABLE users; --"},
    )
    assert response.status_code in [400, 422]


def test_rate_limiting_tier_endpoints(client, pro_user_token):
    """Tier endpoints have rate limiting."""
    for _ in range(100):
        response = client.get("/api/keys", headers={"Authorization": f"Bearer {pro_user_token}"})
    assert response.status_code == 429
