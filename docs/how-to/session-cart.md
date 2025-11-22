# Session-backed Shopping Cart

This guide explains how the session-backed shopping cart works and how to use it from clients and tests.

Overview:
- The application maintains a single cart_id per session.
- Items you add (for example, "apple" then "banana") accumulate in the cart across multiple HTTP requests as long as the same session is used.
- This behavior is verified by the test named test_cart_session_persists_items_and_id, which ensures both the cart_id and the accumulated items persist across requests.

What is this?
- A session-based shopping cart stores a cart identifier and the list of items in the server-side session (or a session cookie/store).
- For a given browser session or API client that preserves cookies, the cart_id remains stable, and items added over time appear together when you fetch the cart.

How do I use it?
- Use the same browser session or HTTP client instance across requests so that cookies (and thus the session) are reused.
- Add items via your API’s "add to cart" endpoint. Subsequent adds in the same session will accumulate items.
- Retrieve the cart to see the current cart_id and list of items.

Example: Using an HTTP client that preserves cookies
- The simplest way to ensure persistence is to use a client that stores cookies between requests. In Python, requests.Session does this for you.

```python
import requests

# Replace with your actual base URL and endpoint paths
BASE_URL = "http://localhost:8000"

with requests.Session() as s:
    # Add the first item (e.g., "apple")
    r1 = s.post(f"{BASE_URL}/cart/items", json={"sku": "apple"})
    r1.raise_for_status()
    data1 = r1.json()
    cart_id1 = data1["cart_id"]
    print("Cart after first add:", data1)

    # Add the second item (e.g., "banana") using the same session
    r2 = s.post(f"{BASE_URL}/cart/items", json={"sku": "banana"})
    r2.raise_for_status()
    data2 = r2.json()
    cart_id2 = data2["cart_id"]
    print("Cart after second add:", data2)

    # The cart_id should be the same across requests
    assert cart_id1 == cart_id2

    # Fetch the cart to see accumulated items
    r3 = s.get(f"{BASE_URL}/cart")
    r3.raise_for_status()
    cart = r3.json()
    print("Final cart:", cart)
    assert {item["sku"] for item in cart["items"]} == {"apple", "banana"}
```

Example: Testing with a framework’s test client
- When writing tests, reuse the same client instance between requests so the session persists. The test below mirrors the intent of test_cart_session_persists_items_and_id:

```python
def test_cart_session_persists_items_and_id(client):
    # Add "apple"
    r1 = client.post("/cart/items", json={"sku": "apple"})
    assert r1.status_code == 200
    cart_id_1 = r1.json["cart_id"]

    # Add "banana" using the same client (same session)
    r2 = client.post("/cart/items", json={"sku": "banana"})
    assert r2.status_code == 200
    cart_id_2 = r2.json["cart_id"]

    # The cart_id is stable across requests from the same session
    assert cart_id_1 == cart_id_2

    # The cart contains both items
    r3 = client.get("/cart")
    assert r3.status_code == 200
    items = {item["sku"] for item in r3.json["items"]}
    assert items == {"apple", "banana"}
```

Backend expectations (high level)
- On the first cart interaction in a session, generate and persist a cart_id in the session if one does not exist.
- Store items in a session-backed list or data structure and write it back to the session on each modification.
- Return the current cart_id and items in responses so clients and tests can assert on them.

Common pitfalls and troubleshooting
- Seeing a new cart_id on every request:
  - Ensure your client preserves cookies (e.g., use a single requests.Session or the same test client instance).
  - Verify session middleware/storage is configured correctly in your framework.
- Items not accumulating:
  - Check that you read-modify-write the session’s item list rather than overwriting it each request.
  - Confirm that you are not clearing or rotating the session between requests.
- Session reset:
  - Clearing cookies or session storage will reset the cart and assign a new cart_id on the next interaction.

By ensuring that your client preserves the session across requests, you will observe a stable cart_id and an accumulating set of cart items, as validated by the test for cart session persistence.