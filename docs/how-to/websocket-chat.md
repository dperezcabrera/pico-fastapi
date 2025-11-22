# WebSocket Chat (Echo) Endpoint

This guide explains what the `/ws` WebSocket endpoint is and how to use it from a browser, Python, and the command line.

## Overview

The `/ws` endpoint provides a simple WebSocket-based chat mechanism:

- On connection, the server sends an initial greeting message.
- Any subsequent text message you send (for example, "hello" or "ping") is echoed back verbatim.

This behavior is useful for verifying connectivity and serves as a foundation for building real-time features.

Endpoint:
- Path: `/ws`
- Protocols: `ws://` (non-TLS) or `wss://` (TLS) depending on your deployment

## How to Use It

### Connect from the Browser

You can use the native WebSocket API available in modern browsers:

```html
<script>
  const ws = new WebSocket("ws://localhost:8000/ws");

  ws.addEventListener("open", () => {
    console.log("WebSocket connection opened");
  });

  ws.addEventListener("message", (event) => {
    console.log("Received:", event.data);
  });

  ws.addEventListener("close", () => {
    console.log("WebSocket connection closed");
  });

  ws.addEventListener("error", (err) => {
    console.error("WebSocket error:", err);
  });

  // Example: send messages after the socket is open
  ws.addEventListener("open", () => {
    ws.send("hello"); // server will echo "hello"
    ws.send("ping");  // server will echo "ping"
  });
</script>
```

What to expect:
- After the connection opens, the first `message` event contains the initial greeting.
- Subsequent messages are echoes of what you send.

### Connect from Python (async)

Use the `websockets` library to connect and interact with the `/ws` endpoint:

```python
import asyncio
import websockets

async def main():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Receive initial greeting
        greeting = await websocket.recv()
        print("Greeting:", greeting)

        # Echo examples
        await websocket.send("hello")
        echo1 = await websocket.recv()
        print("Echo:", echo1)  # -> "hello"

        await websocket.send("ping")
        echo2 = await websocket.recv()
        print("Echo:", echo2)  # -> "ping"

asyncio.run(main())
```

Notes:
- Replace `ws://localhost:8000/ws` with the appropriate host and protocol for your environment.
- Handle exceptions and reconnection logic as needed for production use.

### Connect from the CLI (wscat)

If you prefer the command line, `wscat` is a simple tool to interact with WebSocket endpoints:

```bash
# Install wscat if you don't have it
npm install -g wscat

# Connect to the endpoint
wscat -c ws://localhost:8000/ws
```

In the interactive session:
- You should see a greeting after connecting.
- Type `hello` or `ping` and press Enter; the server will echo the same text back.

## Verifying with Tests

A test ensures the endpoint behaves as expected: it receives the initial greeting and verifies that sent messages are echoed back.

Example pattern (using a test client with WebSocket support):

```python
def test_websocket_echo(client):
    with client.websocket_connect("/ws") as ws:
        greeting = ws.receive_text()
        assert greeting  # initial connection greeting present

        ws.send_text("hello")
        assert ws.receive_text() == "hello"

        ws.send_text("ping")
        assert ws.receive_text() == "ping"
```

## Troubleshooting

- No greeting received:
  - Verify the server is running and listening on the expected host/port.
  - Confirm you are connecting to `/ws` and using the correct protocol (`ws://` vs `wss://`).
- Connection errors:
  - Check firewall or reverse proxy settings.
  - Ensure TLS termination is correctly configured if using `wss://`.
- Messages not echoed:
  - Confirm you are sending text messages (UTF-8 strings), not binary frames.
  - Inspect server logs for errors.

## Next Steps

Once connectivity is validated, you can extend the behavior to support:
- Broadcasting messages to multiple clients
- User identification and presence
- Structured message formats (JSON)
- Authentication and access control