def test_admin_requires_auth(client):
    res = client.get("/api/admin/data")
    assert res.status_code == 401
    body = res.json()
    assert "error" in body


def test_admin_forbidden_with_user_token(client):
    res = client.get("/api/admin/data", headers={"Authorization": "Bearer jwt_user_token"})
    assert res.status_code == 403
    body = res.json()
    assert "error" in body


def test_admin_allowed_with_admin_token(client):
    res = client.get("/api/admin/data", headers={"Authorization": "Bearer jwt_admin_token"})
    assert res.status_code == 200
    body = res.json()
    assert "data" in body and "user_id" in body
    assert body["user_id"] == "u-admin"
