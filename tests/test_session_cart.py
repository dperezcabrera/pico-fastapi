def test_cart_session_persists_items_and_id(client):
    r1 = client.post("/cart/items/apple")
    assert r1.status_code == 200
    body1 = r1.json()
    cart_id_1 = body1["cart_id"]
    assert "apple" in body1["items"]

    r2 = client.post("/cart/items/banana")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["cart_id"] == cart_id_1
    assert "banana" in body2["items"]
    assert "apple" in body2["items"]

    r3 = client.get("/cart/items")
    assert r3.status_code == 200
    body3 = r3.json()
    assert body3["cart_id"] == cart_id_1
    assert set(body3["items"]) >= {"apple", "banana"}
