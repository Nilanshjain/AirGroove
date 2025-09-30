#!/usr/bin/env python3
"""
AirGroove Precision - Ultra-accurate gesture-controlled DJ interface
Complete rebuild with precision gesture recognition and modern web UI.
"""

import cv2
import time
import threading
import webbrowser
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from precision_gestures import PrecisionGestureRecognizer
from gesture_smoother import GestureSmoother
from web_audio_engine import WebAudioEngine
from websocket_enhanced import EnhancedWebSocketServer
import asyncio

# Quick gestures removed - all interaction through cursor hovering


class AirGroovePrecision:
    """Ultra-precise gesture-controlled DJ application."""

    def __init__(self):
        """Initialize AirGroove Precision."""
        print("=" * 60)
        print("AIRGROOVE PRECISION - GESTURE DJ INTERFACE")
        print("=" * 60)
        print()

        # Initialize components
        self.gesture_recognizer = PrecisionGestureRecognizer()
        self.gesture_smoother = GestureSmoother(buffer_size=10, confidence_threshold=0.7)
        self.audio_engine = WebAudioEngine()
        self.websocket_server = None

        # Camera
        self.cap = None
        self.running = False

        # Performance tracking
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0

        # Current mode
        self.current_mode = None

        print(">> Components initialized")

    def start(self):
        """Start the AirGroove Precision application."""
        try:
            # Initialize camera
            print(">> Initializing camera...")
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("!! Error: Could not open camera")
                return False

            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            print(">> Camera initialized")

            # Start audio engine
            print(">> Starting audio engine...")
            self.audio_engine.start_processing()
            self.audio_engine.on_status_changed = self._on_audio_status_changed
            print(">> Audio engine started")

            # Start WebSocket server
            print(">> Starting WebSocket server...")
            self.websocket_server = self._start_websocket_server()
            time.sleep(1)  # Give server time to start
            print(">> WebSocket server started on ws://localhost:8765")

            # Open web interface
            print(">> Opening web interface...")
            web_path = Path(__file__).parent / 'web' / 'index.html'
            webbrowser.open(f'file://{web_path.absolute()}')
            print(">> Web interface opened")

            # Load demo tracks automatically
            print(">> Loading demo tracks...")
            self._load_demo_track('a')
            self._load_demo_track('b')

            # Start main processing loop
            print(">> Starting gesture recognition...")
            print()
            print("Controls:")
            print("- Move hand: Control cursor")
            print("- Fist on element: Select/activate")
            print("- Q: Quit application")
            print("- SPACE: Play/Pause Deck A")
            print("- O: Load demo track")
            print()
            print("Ready! Make gestures in front of the camera.")
            print("=" * 60)

            self.running = True
            self._main_loop()

        except Exception as e:
            print(f"!! Error starting application: {e}")
            return False

    def _start_websocket_server(self):
        """Start the WebSocket server."""
        server = EnhancedWebSocketServer('localhost', 8765)

        # Set up callbacks
        server.set_mode_selection_callback(self._on_mode_selected)
        server.set_audio_control_callback(self._on_audio_control)
        server.set_ui_interaction_callback(self._on_ui_interaction)

        def run_server():
            asyncio.run(server.start_server())

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()

        return server

    def _main_loop(self):
        """Main application processing loop."""
        while self.running:
            loop_start = time.time()

            try:
                # Read camera frame
                success, frame = self.cap.read()
                if not success:
                    print("Error: Could not read camera frame")
                    break

                # Flip frame for mirror effect
                frame = cv2.flip(frame, 1)

                # Process gestures
                raw_gesture_state = self.gesture_recognizer.update_hands(frame)
                smoothed_gesture_state = self.gesture_smoother.smooth_gestures(raw_gesture_state)

                # Send gesture data to web interface
                if self.websocket_server:
                    self.websocket_server.update_gesture_data(smoothed_gesture_state)

                # Handle gesture-based audio control
                self._handle_gesture_audio_control(smoothed_gesture_state)

                # Show debug window
                self._show_debug_window(frame, smoothed_gesture_state)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n[App] Quit requested")
                    break
                elif key == ord(' '):
                    print("[App] Space - Play/Pause deck A")
                    if hasattr(self.audio_engine.deck_a, 'playing') and self.audio_engine.deck_a.playing:
                        self.audio_engine.pause_deck('a')
                    else:
                        self.audio_engine.play_deck('a')
                elif key == ord('o'):
                    self._load_demo_track('a')
                elif key == ord('p'):
                    self._load_demo_track('b')

                # Update FPS
                self._update_fps()

                # Control frame rate (60 FPS target)
                loop_time = time.time() - loop_start
                target_time = 1.0 / 60.0
                if loop_time < target_time:
                    time.sleep(target_time - loop_time)

            except KeyboardInterrupt:
                print("\n[App] Keyboard interrupt")
                break
            except Exception as e:
                print(f"[App] Error in main loop: {e}")

        self.stop()

    def _handle_gesture_audio_control(self, gesture_state):
        """Handle gesture-based audio control."""
        interaction_state = gesture_state.get('interaction_state', 'browsing')

        # Handle mode-specific controls
        if interaction_state.startswith('controlling_'):
            parts = interaction_state.split('_')
            if len(parts) >= 4:
                hand = parts[2]  # left or right
                gesture_type = parts[3]  # pinch, pointer, two_fingers

                # Get hand position
                hand_key = f'{hand}_hand'
                if hand_key in gesture_state and gesture_state[hand_key]['detected']:
                    position = gesture_state[hand_key]['position']
                    self._apply_mode_control(gesture_type, position)

    def _apply_mode_control(self, gesture_type, position):
        """Apply mode-specific control based on gesture type and hand position."""
        if not self.current_mode:
            return

        x, y = position

        if self.current_mode == 'fx':
            if gesture_type == 'pinch':
                # Filter control (Y-axis)
                self.audio_engine.fx_control('filter', 1.0 - y)
            elif gesture_type == 'pointer':
                # Effect mix (X-axis)
                self.audio_engine.fx_control('mix', x)
            elif gesture_type == 'two_fingers':
                # Reverb (X) + Delay (Y)
                self.audio_engine.fx_control('reverb', x)
                self.audio_engine.fx_control('delay', 1.0 - y)

        elif self.current_mode == 'loop':
            if gesture_type == 'pinch':
                # Loop length (X-axis)
                self.audio_engine.loop_control('length', x)
            elif gesture_type == 'pointer':
                # Loop position (X-axis)
                self.audio_engine.loop_control('position', x)
            elif gesture_type == 'two_fingers':
                # Loop roll (Y-axis)
                self.audio_engine.loop_control('roll', 1.0 - y)

        elif self.current_mode == 'scratch':
            if gesture_type == 'pinch':
                # Pitch bend (Y-axis, centered)
                self.audio_engine.scratch_control('pitch', y)
            elif gesture_type == 'pointer':
                # Scratch speed (X-axis, centered)
                self.audio_engine.scratch_control('speed', x)
            elif gesture_type == 'two_fingers':
                # Crossfader (X-axis)
                self.audio_engine.set_crossfader(x)

    def _show_debug_window(self, frame, gesture_state):
        """Show debug window with gesture info."""
        debug_frame = frame.copy()

        # Add text overlays
        y_offset = 30

        # FPS
        cv2.putText(debug_frame, f"FPS: {self.current_fps}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y_offset += 30

        # Gesture states
        left_state = gesture_state.get('left_hand', {})
        right_state = gesture_state.get('right_hand', {})

        cv2.putText(debug_frame, f"Left: {left_state.get('gesture', 'none')}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        y_offset += 25

        cv2.putText(debug_frame, f"Right: {right_state.get('gesture', 'none')}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        y_offset += 25

        # Interaction state
        interaction = gesture_state.get('interaction_state', 'browsing')
        cv2.putText(debug_frame, f"State: {interaction}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        y_offset += 25

        # Current mode
        cv2.putText(debug_frame, f"Mode: {self.current_mode or 'None'}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 128, 0), 1)

        # Instructions
        instructions = [
            "Controls:",
            "Q - Quit",
            "SPACE - Play/Pause",
            "O - Load demo track"
        ]

        start_y = debug_frame.shape[0] - 120
        for i, instruction in enumerate(instructions):
            cv2.putText(debug_frame, instruction, (10, start_y + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow('AirGroove Precision - Debug View', debug_frame)

    def _update_fps(self):
        """Update FPS counter."""
        self.fps_counter += 1
        current_time = time.time()

        if current_time - self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = current_time

            # Send system status to web interface
            if self.websocket_server:
                self.websocket_server.update_system_data({
                    'fps': self.current_fps,
                    'camera_active': True,
                    'gesture_engine': 'precision',
                    'current_mode': self.current_mode
                })

    def _load_demo_track(self, deck='a'):
        """Load a demo track for testing."""
        demo_files = [
            'audio/Ainozama.mp3',
            'audio/pianos-by-jtwayne-7-174717.mp3',
            'C:/Windows/Media/Alarm01.wav',  # Windows system sound
            'C:/Windows/Media/Ring01.wav'
        ]

        for demo_file in demo_files:
            if os.path.exists(demo_file):
                self.audio_engine.load_track(deck, demo_file)
                print(f"[Demo] Loaded: {demo_file} to deck {deck}")

                # Send track info to frontend
                if self.websocket_server:
                    track_name = os.path.basename(demo_file)
                    self.websocket_server.update_audio_data({
                        f'deck_{deck}': {
                            'track_name': track_name,
                            'artist': 'Demo Track',
                            'loaded': True
                        }
                    })
                return

        print(f"[Demo] No demo files found for deck {deck}")

    # WebSocket event handlers
    def _on_mode_selected(self, mode):
        """Handle mode selection from web interface."""
        self.current_mode = mode
        self.audio_engine.set_mode(mode)
        print(f"[Mode] Selected: {mode}")

    def _on_audio_control(self, action, parameters):
        """Handle audio control from web interface."""
        deck = parameters.get('deck', 'a')

        if action == 'play':
            self.audio_engine.play_deck(deck)
        elif action == 'pause':
            self.audio_engine.pause_deck(deck)
        elif action == 'stop':
            self.audio_engine.stop_deck(deck)
        elif action == 'play_pause':
            # Toggle play/pause
            if deck == 'a':
                if hasattr(self.audio_engine.deck_a, 'playing') and self.audio_engine.deck_a.playing:
                    self.audio_engine.pause_deck(deck)
                else:
                    self.audio_engine.play_deck(deck)
            elif deck == 'b':
                if hasattr(self.audio_engine.deck_b, 'playing') and self.audio_engine.deck_b.playing:
                    self.audio_engine.pause_deck(deck)
                else:
                    self.audio_engine.play_deck(deck)
        elif action == 'sync':
            # Sync deck to other deck's BPM
            print(f"[Audio] Sync requested for deck {deck}")
            # Note: Implement BPM sync in audio engine if needed
            self.audio_engine.sync_deck(deck) if hasattr(self.audio_engine, 'sync_deck') else None
        elif action == 'load_track':
            # Load track from file path
            file_path = parameters.get('file_path', '')
            file_name = parameters.get('file_name', '')
            print(f"[Audio] Load track request for deck {deck}: {file_name}")

            # For now, show that load was received
            # In production, you'd handle file upload or local file selection
            if file_path and os.path.exists(file_path):
                self.audio_engine.load_track(deck, file_path)
            else:
                print(f"[Audio] File not found: {file_path}")
        elif action == 'fx_control':
            # Handle FX parameter control
            parameter = parameters.get('parameter')
            value = parameters.get('value', 0.0)
            self.audio_engine.fx_control(parameter, value)
        elif action == 'loop_control':
            # Handle loop parameter control
            parameter = parameters.get('parameter')
            value = parameters.get('value', 0.0)
            self.audio_engine.loop_control(parameter, value)
        elif action == 'scratch_control':
            # Handle scratch parameter control
            parameter = parameters.get('parameter')
            value = parameters.get('value', 0.0)
            self.audio_engine.scratch_control(parameter, value)
        elif action == 'crossfader':
            # Handle crossfader control
            position = parameters.get('position', 0.5)
            self.audio_engine.set_crossfader(position)

        print(f"[Audio] {action} on {deck if deck else 'system'}")

    def _on_ui_interaction(self, element, action, position):
        """Handle UI interaction from web interface."""
        print(f"[UI] {action} on {element}")

    def _on_audio_status_changed(self, status):
        """Handle audio status updates."""
        if self.websocket_server:
            self.websocket_server.update_audio_data(status)

    def stop(self):
        """Stop the application."""
        print("\n[App] Stopping AirGroove Precision...")

        self.running = False

        # Stop components
        if self.audio_engine:
            self.audio_engine.stop()

        if self.cap:
            self.cap.release()

        if self.gesture_recognizer:
            self.gesture_recognizer.release()

        cv2.destroyAllWindows()

        print(">> AirGroove Precision stopped")


def main():
    """Main entry point."""
    app = AirGroovePrecision()
    try:
        app.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        app.stop()


if __name__ == "__main__":
    main()