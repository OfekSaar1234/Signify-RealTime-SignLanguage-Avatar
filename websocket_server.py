import asyncio
import websockets
import json

connected_ws_clients = set()
ws_loop = None

async def ws_connection_handler(websocket, *args, **kwargs):
    """Handles new WebSocket connections from Unity/JS Frontend."""
    connected_ws_clients.add(websocket)
    print(f"\n[NETWORK] 3D Avatar connected! Total clients: {len(connected_ws_clients)}")
    try:
        # Keep the connection open to continuously send data
        async for message in websocket:
            pass 
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_ws_clients.remove(websocket)
        print(f"\n[NETWORK] 3D Avatar disconnected. Total clients: {len(connected_ws_clients)}")

async def run_ws_server(host, port):
    global ws_loop
    ws_loop = asyncio.get_running_loop()
    async with websockets.serve(ws_connection_handler, host, port):
        print(f"[NETWORK] WebSocket Server started on ws://{host}:{port}")
        await asyncio.Future()  # Keeps the server running forever

def start_websocket_server(host="localhost", port=8765):
    asyncio.run(run_ws_server(host, port))

def broadcast_frame(frame_data: dict):
    """Broadcasts frame data to all connected WebSocket clients in real-time."""
    if connected_ws_clients and ws_loop:
        json_string = json.dumps(frame_data, separators=(',', ':'))
        for client in list(connected_ws_clients):
            asyncio.run_coroutine_threadsafe(client.send(json_string), ws_loop)