#!/usr/bin/env python3
"""
Enhanced WebSocket server for AirGroove DJ interface.
Handles real-time communication between gesture recognition and web frontend.
"""

import asyncio
import websockets
import json
import threading
import time
from typing import Dict, Set, Optional, Any

class EnhancedWebSocketServer:
    """Enhanced WebSocket server with message routing and state management."""

    def __init__(self, host='localhost', port=8765):
        """Initialize the enhanced WebSocket server."""
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.is_running = False

        # Message queues for different data types
        self.gesture_queue = asyncio.Queue()
        self.audio_queue = asyncio.Queue()
        self.system_queue = asyncio.Queue()

        # Current state cache
        self.current_state = {
            'gestures': {},
            'audio': {},
            'system': {}
        }

        # Statistics
        self.message_count = 0
        self.client_count = 0
        self.last_fps_time = time.time()

        print(f"[WebSocket] Enhanced server initialized on {host}:{port}")

    async def start_server(self):
        """Start the WebSocket server."""
        try:
            async def connection_handler(websocket):
                path = getattr(websocket, 'path', '/')
                await self.handle_client(websocket, path)

            self.server = await websockets.serve(
                connection_handler,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10
            )
            self.is_running = True

            print(f"[WebSocket] Server started on ws://{self.host}:{self.port}")

            # Start message processing task
            asyncio.create_task(self.process_messages())

            # Keep server running
            await self.server.wait_closed()

        except Exception as e:
            print(f"[WebSocket] Error starting server: {e}")

    async def handle_client(self, websocket, path):
        """Handle new WebSocket client connection."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        print(f"[WebSocket] Client connected: {client_id}")

        self.clients.add(websocket)
        self.client_count += 1

        try:
            # Send current state to new client
            await self.send_initial_state(websocket)

            # Handle incoming messages
            async for message in websocket:
                await self.handle_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            print(f"[WebSocket] Client disconnected: {client_id}")
        except Exception as e:
            print(f"[WebSocket] Error handling client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
            self.client_count -= 1

    async def send_initial_state(self, websocket):
        """Send current state to newly connected client."""
        try:
            # Send gesture state
            if self.current_state['gestures']:
                await websocket.send(json.dumps({
                    'type': 'gesture_update',
                    'payload': self.current_state['gestures'],
                    'timestamp': time.time()
                }))

            # Send audio state
            if self.current_state['audio']:
                await websocket.send(json.dumps({
                    'type': 'audio_update',
                    'payload': self.current_state['audio'],
                    'timestamp': time.time()
                }))

            # Send system state
            if self.current_state['system']:
                await websocket.send(json.dumps({
                    'type': 'system_update',
                    'payload': self.current_state['system'],
                    'timestamp': time.time()
                }))

        except Exception as e:
            print(f"[WebSocket] Error sending initial state: {e}")

    async def handle_message(self, websocket, message):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            payload = data.get('payload', {})

            print(f"[WebSocket] Received: {message_type}")

            # Route message to appropriate handler
            if hasattr(self, f'handle_{message_type}'):
                handler = getattr(self, f'handle_{message_type}')
                await handler(websocket, payload)
            else:
                print(f"[WebSocket] Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            print(f"[WebSocket] Invalid JSON received: {e}")
        except Exception as e:
            print(f"[WebSocket] Error handling message: {e}")

    async def handle_mode_select(self, websocket, payload):
        """Handle mode selection from client."""
        mode = payload.get('mode')
        if mode:
            # Forward to gesture system (would be set up in main app)
            if hasattr(self, 'mode_selection_callback'):
                self.mode_selection_callback(mode)

    async def handle_audio_control(self, websocket, payload):
        """Handle audio control commands from client."""
        action = payload.get('action')
        parameters = payload.get('parameters', {})

        if hasattr(self, 'audio_control_callback'):
            self.audio_control_callback(action, parameters)

    async def handle_ui_interaction(self, websocket, payload):
        """Handle UI interaction events from client."""
        element = payload.get('element')
        action = payload.get('action')
        position = payload.get('position')

        if hasattr(self, 'ui_interaction_callback'):
            self.ui_interaction_callback(element, action, position)

    async def process_messages(self):
        """Process queued messages and broadcast to clients."""
        while self.is_running:
            try:
                # Process gesture updates
                if not self.gesture_queue.empty():
                    gesture_data = await self.gesture_queue.get()
                    await self.broadcast_gesture_update(gesture_data)

                # Process audio updates
                if not self.audio_queue.empty():
                    audio_data = await self.audio_queue.get()
                    await self.broadcast_audio_update(audio_data)

                # Process system updates
                if not self.system_queue.empty():
                    system_data = await self.system_queue.get()
                    await self.broadcast_system_update(system_data)

                await asyncio.sleep(1/60)  # 60 FPS processing

            except Exception as e:
                print(f"[WebSocket] Error processing messages: {e}")

    async def broadcast_gesture_update(self, gesture_data):
        """Broadcast gesture update to all clients."""
        if not self.clients:
            return

        message = {
            'type': 'gesture_update',
            'payload': gesture_data,
            'timestamp': time.time()
        }

        # Update state cache
        self.current_state['gestures'] = gesture_data

        await self.broadcast_message(message)

    async def broadcast_audio_update(self, audio_data):
        """Broadcast audio update to all clients."""
        if not self.clients:
            return

        message = {
            'type': 'audio_update',
            'payload': audio_data,
            'timestamp': time.time()
        }

        # Update state cache
        self.current_state['audio'] = audio_data

        await self.broadcast_message(message)

    async def broadcast_system_update(self, system_data):
        """Broadcast system update to all clients."""
        if not self.clients:
            return

        message = {
            'type': 'system_update',
            'payload': system_data,
            'timestamp': time.time()
        }

        # Update state cache
        self.current_state['system'] = system_data

        await self.broadcast_message(message)

    async def broadcast_message(self, message):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return

        message_json = json.dumps(message)
        disconnected_clients = set()

        for client in self.clients.copy():
            try:
                await client.send(message_json)
                self.message_count += 1
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.clients -= disconnected_clients

    # Public methods for updating data from backend
    def update_gesture_data(self, gesture_data):
        """Update gesture data (called from main application)."""
        if self.is_running:
            try:
                self.gesture_queue.put_nowait(gesture_data)
            except asyncio.QueueFull:
                # Drop oldest message if queue is full
                try:
                    self.gesture_queue.get_nowait()
                    self.gesture_queue.put_nowait(gesture_data)
                except asyncio.QueueEmpty:
                    pass

    def update_audio_data(self, audio_data):
        """Update audio data (called from main application)."""
        if self.is_running:
            try:
                self.audio_queue.put_nowait(audio_data)
            except asyncio.QueueFull:
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.put_nowait(audio_data)
                except asyncio.QueueEmpty:
                    pass

    def update_system_data(self, system_data):
        """Update system data (called from main application)."""
        if self.is_running:
            try:
                self.system_queue.put_nowait(system_data)
            except asyncio.QueueFull:
                try:
                    self.system_queue.get_nowait()
                    self.system_queue.put_nowait(system_data)
                except asyncio.QueueEmpty:
                    pass

    def set_mode_selection_callback(self, callback):
        """Set callback for mode selection events."""
        self.mode_selection_callback = callback

    def set_audio_control_callback(self, callback):
        """Set callback for audio control events."""
        self.audio_control_callback = callback

    def set_ui_interaction_callback(self, callback):
        """Set callback for UI interaction events."""
        self.ui_interaction_callback = callback

    def get_stats(self) -> Dict:
        """Get server statistics."""
        current_time = time.time()
        fps = self.message_count / (current_time - self.last_fps_time + 0.001)

        stats = {
            'connected_clients': len(self.clients),
            'total_messages': self.message_count,
            'messages_per_second': fps,
            'queue_sizes': {
                'gesture': self.gesture_queue.qsize(),
                'audio': self.audio_queue.qsize(),
                'system': self.system_queue.qsize()
            }
        }

        return stats

    async def stop_server(self):
        """Stop the WebSocket server."""
        self.is_running = False

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Close all client connections
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )

        print("[WebSocket] Server stopped")


def start_websocket_server(host='localhost', port=8765):
    """Start the WebSocket server in a separate thread."""
    server = EnhancedWebSocketServer(host, port)

    def run_server():
        asyncio.run(server.start_server())

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    return server