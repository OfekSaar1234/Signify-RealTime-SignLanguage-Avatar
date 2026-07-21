import asyncio
import websockets
import json
import threading
from utils.logger import logger

class WebSocketStreamer:
    """
    Manages a WebSocket server to broadcast 3D frame data to external clients (e.g., Unity).
    """
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.connected_ws_clients = set()
        self.ws_loop = None

    def start(self):
        threading.Thread(target=self._start_server_sync, daemon=True).start()

    def _start_server_sync(self):
        asyncio.run(self._run_ws_server())

    async def _ws_connection_handler(self, websocket, *args, **kwargs):
        self.connected_ws_clients.add(websocket)
        logger.info(f"3D Avatar connected! Total clients: {len(self.connected_ws_clients)}")
        try:
            async for _ in websocket:
                pass 
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_ws_clients.remove(websocket)
            logger.info(f"3D Avatar disconnected. Total clients: {len(self.connected_ws_clients)}")

    async def _run_ws_server(self):
        self.ws_loop = asyncio.get_running_loop()
        async with websockets.serve(self._ws_connection_handler, self.host, self.port):
            logger.info(f"WebSocket Server started on ws://{self.host}:{self.port}")
            await asyncio.Future()

    def broadcast(self, payload):
        if self.connected_ws_clients and self.ws_loop:
            if isinstance(payload, dict):
                data_to_send = json.dumps(payload, separators=(',', ':'))
            else:
                data_to_send = payload
                
            for client in list(self.connected_ws_clients):
                asyncio.run_coroutine_threadsafe(client.send(data_to_send), self.ws_loop)
