def test_websocket_echo(client):
    with client.websocket_connect("/ws") as ws:
        greeting = ws.receive_text()
        assert "Connected to WS Manager" in greeting
        ws.send_text("hello")
        msg1 = ws.receive_text()
        assert "hello" in msg1
        ws.send_text("ping")
        msg2 = ws.receive_text()
        assert "ping" in msg2

