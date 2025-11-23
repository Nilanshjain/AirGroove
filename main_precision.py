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
from config_loader import get_config
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

        # Check for test mode
        self.test_mode_enabled = '--test-mode' in sys.argv
        self.test_mode = None

        # Load configuration
        self.config = get_config()
        print(">> Configuration loaded")

        # Initialize components (they will use config internally)
        self.gesture_recognizer = PrecisionGestureRecognizer()
        self.gesture_smoother = GestureSmoother()  # Uses config defaults
        self.audio_engine = WebAudioEngine()
        self.websocket_server = None

        # Camera
        self.cap = None
        self.running = False

        # Initialize test mode if enabled
        if self.test_mode_enabled:
            from test_mode import enable_test_mode
            self.test_mode = enable_test_mode()
            print("\n[TEST MODE] Enabled - Test tracks will be auto-loaded")
            print("[TEST MODE] Starting in FX mode for filter testing\n")

        # Performance tracking
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0

        # Mode system - Swipe LEFT/RIGHT to switch
        self.current_mode = 'normal'  # Start in NORMAL mode
        self.mode_list = ['normal', 'fx', 'loop', 'scratch']
        self.mode_colors = {
            'normal': (255, 255, 255),  # White
            'fx': (255, 200, 0),        # Cyan
            'loop': (0, 255, 0),        # Green
            'scratch': (0, 165, 255)    # Orange
        }
        self.last_mode_switch_time = 0
        self.MODE_SWITCH_COOLDOWN = 0.5  # 500ms between mode changes
        self.last_swipe_state = {'left': None, 'right': None}  # Track last swipe state for edge detection

        print(">> Components initialized")
        print(f">> Smoothing buffer: {self.gesture_smoother.buffer_size} frames")
        print(f">> Active profile: {self.config.get_active_profile()}")

    def start(self):
        """Start the AirGroove Precision application."""
        try:
            # Initialize camera with config settings
            print(">> Initializing camera...")
            camera_config = self.config.get_camera_config()
            self.cap = cv2.VideoCapture(camera_config.get('device_index', 0))
            if not self.cap.isOpened():
                print("!! Error: Could not open camera")
                return False

            # Set camera properties from config
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_config.get('width', 640))
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_config.get('height', 480))
            self.cap.set(cv2.CAP_PROP_FPS, camera_config.get('fps', 30))
            print(f">> Camera initialized ({camera_config.get('width')}x{camera_config.get('height')} @ {camera_config.get('fps')} FPS)")

            # Start audio engine
            print(">> Starting audio engine...")
            self.audio_engine.start_processing()
            self.audio_engine.on_status_changed = self._on_audio_status_changed
            self.audio_engine.on_fx_state_changed = self._on_fx_state_changed
            print(">> Audio engine started")

            # Connect audio control callback to websocket server
            if self.websocket_server:
                self.websocket_server.audio_control_callback = self._on_audio_control

            # Load test tracks if in test mode
            if self.test_mode_enabled and self.test_mode:
                print("\n[TEST MODE] Loading test tracks...")
                deck_a, deck_b = self.test_mode.get_deck_tracks()
                if deck_a:
                    self.audio_engine.load_track('a', str(deck_a))
                    print(f"[TEST MODE] Deck A: {deck_a.name}")
                if deck_b:
                    self.audio_engine.load_track('b', str(deck_b))
                    print(f"[TEST MODE] Deck B: {deck_b.name}")
                # Switch to FX mode for filter testing
                self.current_mode = 'fx'
                self.audio_engine.set_mode('fx')
                print("[TEST MODE] Switched to FX mode for filter testing\n")

            # Start WebSocket server
            print(">> Starting WebSocket server...")
            self.websocket_server = self._start_websocket_server()
            time.sleep(1)  # Give server time to start
            print(">> WebSocket server started on ws://localhost:8765")

            # Open web interface automatically
            web_path = Path(__file__).parent / 'web' / 'index.html'
            web_url = f'file:///{web_path.absolute()}'.replace('\\', '/')
            print(f">> Opening web interface: {web_url}")
            webbrowser.open(web_url)
            print(">> Web interface opened in browser")

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

                # DEBUG: Log all detected gestures
                left_hand = smoothed_gesture_state.get('left_hand', {})
                right_hand = smoothed_gesture_state.get('right_hand', {})

                if left_hand.get('detected'):
                    print(f"[DEBUG] Left: {left_hand.get('gesture')} | Pos: ({left_hand.get('position')[0]:.2f}, {left_hand.get('position')[1]:.2f}) | " +
                          f"Swipe: {left_hand.get('swipe')} | Tap: {left_hand.get('tap')} | Rot: {left_hand.get('rotation_velocity', 0):.1f}°/s")

                if right_hand.get('detected'):
                    print(f"[DEBUG] Right: {right_hand.get('gesture')} | Pos: ({right_hand.get('position')[0]:.2f}, {right_hand.get('position')[1]:.2f}) | " +
                          f"Swipe: {right_hand.get('swipe')} | Tap: {right_hand.get('tap')} | Rot: {right_hand.get('rotation_velocity', 0):.1f}°/s")

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
        # Handle mode switching FIRST (swipe gestures)
        self._handle_mode_switching(gesture_state)

        # Handle play/pause with closed fist gestures (works in all modes)
        self._handle_play_pause_gestures(gesture_state)

        # Handle mode-specific controls based on current mode
        if self.current_mode == 'normal':
            # NORMAL mode: crossfader control
            self._handle_crossfader_gesture(gesture_state)
        elif self.current_mode == 'fx':
            # FX mode: effect selection and control
            self._handle_fx_mode_gestures(gesture_state)
        elif self.current_mode == 'loop':
            # LOOP mode: loop point and length control
            self._handle_loop_mode_gestures(gesture_state)
        elif self.current_mode == 'scratch':
            # SCRATCH mode: turntable control
            self._handle_scratch_mode_gestures(gesture_state)

    def _handle_play_pause_gestures(self, gesture_state):
        """Handle play/pause with CLOSED_FIST gesture - THE ONLY play/pause control.

        Uses edge detection to trigger exactly once per fist gesture.
        Triggers on transition TO closed_fist (not during hold).
        """
        left_gesture = gesture_state.get('left_hand', {}).get('gesture', 'none')
        right_gesture = gesture_state.get('right_hand', {}).get('gesture', 'none')

        # Initialize previous gesture state tracking
        if not hasattr(self, '_prev_left_gesture'):
            self._prev_left_gesture = 'none'
        if not hasattr(self, '_prev_right_gesture'):
            self._prev_right_gesture = 'none'
        if not hasattr(self, '_last_fist_left'):
            self._last_fist_left = 0
        if not hasattr(self, '_last_fist_right'):
            self._last_fist_right = 0

        # Timing for responsive control
        MIN_HOLD_TIME = 0.15  # 150ms hold - quick response
        COOLDOWN_TIME = 0.5   # 500ms cooldown - prevents double triggers

        current_time = time.time()

        # LEFT HAND CLOSED_FIST = Play/Pause Deck A
        # Edge detection: trigger only on transition TO closed_fist
        if left_gesture == 'closed_fist' and self._prev_left_gesture != 'closed_fist':
            # Record when fist gesture started
            self._fist_start_left = current_time

        # Trigger after minimum hold time and cooldown
        if (left_gesture == 'closed_fist' and
            self._prev_left_gesture != 'closed_fist' and
            (current_time - self._last_fist_left) > COOLDOWN_TIME):

            # Toggle play/pause for Deck A
            deck = self.audio_engine.sd_engine.deck_a
            if deck.playing:
                self.audio_engine.pause_deck('a')
                print("[CLOSED_FIST] Left hand -> PAUSE Deck A")
            else:
                self.audio_engine.play_deck('a')
                print("[CLOSED_FIST] Left hand -> PLAY Deck A")
            self._last_fist_left = current_time

        # RIGHT HAND CLOSED_FIST = Play/Pause Deck B
        # Edge detection: trigger only on transition TO closed_fist
        if right_gesture == 'closed_fist' and self._prev_right_gesture != 'closed_fist':
            # Record when fist gesture started
            self._fist_start_right = current_time

        # Trigger after minimum hold time and cooldown
        if (right_gesture == 'closed_fist' and
            self._prev_right_gesture != 'closed_fist' and
            (current_time - self._last_fist_right) > COOLDOWN_TIME):

            # Toggle play/pause for Deck B
            deck = self.audio_engine.sd_engine.deck_b
            if deck.playing:
                self.audio_engine.pause_deck('b')
                print("[CLOSED_FIST] Right hand -> PAUSE Deck B")
            else:
                self.audio_engine.play_deck('b')
                print("[CLOSED_FIST] Right hand -> PLAY Deck B")
            self._last_fist_right = current_time

        # Update previous gesture state for next frame
        self._prev_left_gesture = left_gesture
        self._prev_right_gesture = right_gesture

    def _handle_crossfader_gesture(self, gesture_state):
        """Handle crossfader control with pinch gesture.

        Remembers last position and uses less aggressive smoothing for accurate control.
        """
        # Use pinch gesture on any hand for crossfader control
        # When both hands pinch, average their X positions
        left_gesture = gesture_state.get('left_hand', {}).get('gesture', 'none')
        right_gesture = gesture_state.get('right_hand', {}).get('gesture', 'none')
        left_pos = gesture_state.get('left_hand', {}).get('position', (0.5, 0.5))
        right_pos = gesture_state.get('right_hand', {}).get('position', (0.5, 0.5))

        # Initialize crossfader position from audio engine's current state (remembers last position)
        if not hasattr(self, '_crossfader_smoothed'):
            self._crossfader_smoothed = self.audio_engine.sd_engine.crossfader_position
            self._last_pinch_x = None

        # Both hands pinch = crossfader control
        if left_gesture == 'pinch' and right_gesture == 'pinch':
            # Average X position of both hands
            x_position = (left_pos[0] + right_pos[0]) / 2.0

            # Optimized smoothing for responsive yet smooth control (0.70 old, 0.30 new)
            self._crossfader_smoothed = self._crossfader_smoothed * 0.70 + x_position * 0.30
            self.audio_engine.set_crossfader(self._crossfader_smoothed)
            self._last_pinch_x = x_position

        # Single hand pinch (when not in control mode)
        elif left_gesture == 'pinch' and right_gesture in ['none', 'open_palm']:
            # Optimized smoothing for responsive yet smooth control
            self._crossfader_smoothed = self._crossfader_smoothed * 0.85 + left_pos[0] * 0.15
            self.audio_engine.set_crossfader(self._crossfader_smoothed)
            self._last_pinch_x = left_pos[0]

        elif right_gesture == 'pinch' and left_gesture in ['none', 'open_palm']:
            # Less aggressive smoothing for more responsive control
            self._crossfader_smoothed = self._crossfader_smoothed * 0.85 + right_pos[0] * 0.15
            self.audio_engine.set_crossfader(self._crossfader_smoothed)
            self._last_pinch_x = right_pos[0]

        # When pinch is released, save the current position (no reset to center)
        # The next time pinch is detected, it will resume from audio_engine.crossfader_position

    def _handle_mode_switching(self, gesture_state):
        """Handle mode switching via LEFT/RIGHT swipes.

        Swipe LEFT  = Previous mode (cycle backward)
        Swipe RIGHT = Next mode (cycle forward)
        """
        # Check both hands for swipes
        left_swipe = gesture_state.get('left_hand', {}).get('swipe')
        right_swipe = gesture_state.get('right_hand', {}).get('swipe')

        # Edge detection: Only trigger on swipe start (transition from None to a direction)
        left_edge = left_swipe and self.last_swipe_state['left'] is None
        right_edge = right_swipe and self.last_swipe_state['right'] is None

        # Update swipe state tracking
        self.last_swipe_state['left'] = left_swipe
        self.last_swipe_state['right'] = right_swipe

        # DEBUG: Log when swipes are detected (edge triggered only)
        if left_edge:
            print(f"[DEBUG] Left swipe STARTED: {left_swipe}")
        if right_edge:
            print(f"[DEBUG] Right swipe STARTED: {right_swipe}")

        # Cooldown check (only check if we have an edge)
        if left_edge or right_edge:
            current_time = time.time()
            if current_time - self.last_mode_switch_time < self.MODE_SWITCH_COOLDOWN:
                print(f"[MODE SWITCH] Swipe detected but in cooldown (wait {self.MODE_SWITCH_COOLDOWN - (current_time - self.last_mode_switch_time):.1f}s)")
                return  # Too soon after last mode switch

        # Detect swipe direction (either hand can trigger, but only on edge)
        swipe_direction = (left_swipe if left_edge else None) or (right_swipe if right_edge else None)

        if swipe_direction in ['left', 'right']:  # FIXED: Changed to lowercase to match gesture detector output
            current_index = self.mode_list.index(self.current_mode)

            if swipe_direction == 'right':
                # Next mode (cycle forward)
                new_index = (current_index + 1) % len(self.mode_list)
            else:  # LEFT
                # Previous mode (cycle backward)
                new_index = (current_index - 1) % len(self.mode_list)

            self.current_mode = self.mode_list[new_index]
            self.last_mode_switch_time = current_time

            print(f"\n{'='*60}")
            print(f"[MODE SWITCH] Swipe {swipe_direction} -> {self.current_mode.upper()} MODE")
            print(f"{'='*60}\n")

            # Send mode change to WebSocket
            if self.websocket_server:
                mode_payload = {
                    'type': 'mode_change',
                    'payload': {
                        'mode': self.current_mode
                    }
                }
                print(f"[WebSocket] Broadcasting mode change: {mode_payload}")
                self.websocket_server.broadcast_json(mode_payload)

    def _handle_fx_mode_gestures(self, gesture_state):
        """Handle FX mode gestures.

        - Pointer (left hand Y): Select filter type (lowpass/highpass/bandpass)
        - Two fingers (right hand X): Adjust cutoff frequency (20Hz - 20kHz)
        - Two fingers (right hand Y): Adjust wet/dry mix
        - Palm rotation: Adjust resonance/Q factor
        """
        import math

        left_gesture = gesture_state.get('left_hand', {}).get('gesture', 'none')
        right_gesture = gesture_state.get('right_hand', {}).get('gesture', 'none')
        left_pos = gesture_state.get('left_hand', {}).get('position', (0.5, 0.5))
        right_pos = gesture_state.get('right_hand', {}).get('position', (0.5, 0.5))
        left_rotation = gesture_state.get('left_hand', {}).get('rotation_velocity', 0)
        right_rotation = gesture_state.get('right_hand', {}).get('rotation_velocity', 0)

        # Pointer (left hand) = Select filter type based on Y position
        if left_gesture == 'pointer':
            y_pos = left_pos[1]
            if y_pos < 0.3:
                filter_type = 'lowpass'
            elif y_pos < 0.7:
                filter_type = 'highpass'
            else:
                filter_type = 'bandpass'

            # Set filter type and enable filter
            print(f"[TRACE-FX] BEFORE fx_control('filter_type', {filter_type})")
            self.audio_engine.fx_control('filter_type', filter_type)
            print(f"[TRACE-FX] AFTER fx_control('filter_type', {filter_type})")

            print(f"[TRACE-FX] BEFORE fx_control('enable', 1.0)")
            self.audio_engine.fx_control('enable', 1.0)
            print(f"[TRACE-FX] AFTER fx_control('enable', 1.0)")

            print(f"[FX MODE] Filter type: {filter_type} (Y={y_pos:.2f})")

        # Two fingers (right hand) = Adjust cutoff frequency (X) and wet/dry mix (Y)
        if right_gesture == 'two_fingers':
            x_pos = right_pos[0]
            y_pos = right_pos[1]

            # Map X position to cutoff frequency (20Hz to 20kHz, logarithmic scale)
            cutoff = 20 * math.pow(1000, x_pos)  # 20Hz at X=0, 20kHz at X=1

            print(f"[TRACE-FX] BEFORE fx_control('cutoff', {cutoff})")
            self.audio_engine.fx_control('cutoff', cutoff)
            print(f"[TRACE-FX] AFTER fx_control('cutoff', {cutoff})")

            # Map Y position to wet/dry mix (inverted: up = more wet)
            wet_dry = 1.0 - y_pos

            print(f"[TRACE-FX] BEFORE fx_control('wet_dry', {wet_dry})")
            self.audio_engine.fx_control('wet_dry', wet_dry)
            print(f"[TRACE-FX] AFTER fx_control('wet_dry', {wet_dry})")

            print(f"[FX MODE] Cutoff: {cutoff:.0f}Hz | Wet/Dry: {wet_dry*100:.0f}% (X={x_pos:.2f}, Y={y_pos:.2f})")

        # Palm rotation = Adjust resonance (Q factor)
        if abs(left_rotation) > 20 or abs(right_rotation) > 20:
            # Use the larger rotation value
            rotation = left_rotation if abs(left_rotation) > abs(right_rotation) else right_rotation
            # Map rotation velocity to resonance (0.5 to 10.0)
            # Normalize rotation: assume max useful rotation is ±180°/s
            normalized_rotation = max(-1.0, min(1.0, rotation / 180.0))
            # Map to resonance: 0.5 at -180°/s, 5.0 at 0°/s, 10.0 at +180°/s
            resonance = 5.0 + (normalized_rotation * 4.5)

            print(f"[TRACE-FX] BEFORE fx_control('resonance', {resonance})")
            self.audio_engine.fx_control('resonance', resonance)
            print(f"[TRACE-FX] AFTER fx_control('resonance', {resonance})")

            print(f"[FX MODE] Resonance (Q): {resonance:.1f} (rotation={rotation:.1f}°/s)")

    def _handle_loop_mode_gestures(self, gesture_state):
        """Handle LOOP mode gestures.

        - Pointer: Set loop IN point
        - Two fingers: Set loop OUT point
        - Pinch: Adjust loop length (horizontal movement)
        - Palm rotation: Move loop position (shift forward/backward)
        """
        left_gesture = gesture_state.get('left_hand', {}).get('gesture', 'none')
        right_gesture = gesture_state.get('right_hand', {}).get('gesture', 'none')
        left_pos = gesture_state.get('left_hand', {}).get('position', (0.5, 0.5))
        right_pos = gesture_state.get('right_hand', {}).get('position', (0.5, 0.5))
        left_rotation = gesture_state.get('left_hand', {}).get('rotation_velocity', 0)
        right_rotation = gesture_state.get('right_hand', {}).get('rotation_velocity', 0)

        # Pointer = Set loop IN point
        if left_gesture == 'pointer':
            self.audio_engine.loop_action('set_in', {})
            print(f"[LOOP MODE] Left pointer -> Set loop IN point")
        if right_gesture == 'pointer':
            print(f"[LOOP MODE] Right pointer -> Set loop IN (Deck B)")

        # Two fingers = Set loop OUT
        if left_gesture == 'two_fingers':
            print(f"[LOOP MODE] Left two_fingers -> Set loop OUT (Deck A)")
        if right_gesture == 'two_fingers':
            print(f"[LOOP MODE] Right two_fingers -> Set loop OUT (Deck B)")

        # Pinch = Adjust loop length
        if left_gesture == 'pinch':
            print(f"[LOOP MODE] Left pinch -> Adjust loop length (X={left_pos[0]:.2f})")
        if right_gesture == 'pinch':
            print(f"[LOOP MODE] Right pinch -> Adjust loop length (X={right_pos[0]:.2f})")

        # Palm rotation = Move loop position
        if abs(left_rotation) > 20:
            print(f"[LOOP MODE] Left rotation -> Move loop position {left_rotation:.1f}°/s")
        if abs(right_rotation) > 20:
            print(f"[LOOP MODE] Right rotation -> Move loop position {right_rotation:.1f}°/s")

    def _handle_scratch_mode_gestures(self, gesture_state):
        """Handle SCRATCH mode gestures.

        - Palm rotation: Scratch/spin deck (CW = forward, CCW = reverse)
        - Pinch: Pitch bend (up = faster, down = slower)
        - Pointer: Cue point (hold to pause at cue)
        - Two fingers: Nudge tempo up
        """
        left_gesture = gesture_state.get('left_hand', {}).get('gesture', 'none')
        right_gesture = gesture_state.get('right_hand', {}).get('gesture', 'none')
        left_pos = gesture_state.get('left_hand', {}).get('position', (0.5, 0.5))
        right_pos = gesture_state.get('right_hand', {}).get('position', (0.5, 0.5))
        left_rotation = gesture_state.get('left_hand', {}).get('rotation_velocity', 0)
        right_rotation = gesture_state.get('right_hand', {}).get('rotation_velocity', 0)

        # Palm rotation = Scratch
        if abs(left_rotation) > 20:
            direction = "FORWARD" if left_rotation < 0 else "REVERSE"
            print(f"[SCRATCH MODE] Left rotation -> Scratch {direction} {abs(left_rotation):.1f}°/s (Deck A)")
        if abs(right_rotation) > 20:
            direction = "FORWARD" if right_rotation < 0 else "REVERSE"
            print(f"[SCRATCH MODE] Right rotation -> Scratch {direction} {abs(right_rotation):.1f}°/s (Deck B)")

        # Pinch = Pitch bend
        if left_gesture == 'pinch':
            bend = "FASTER" if left_pos[1] < 0.5 else "SLOWER"
            print(f"[SCRATCH MODE] Left pinch -> Pitch bend {bend} (Deck A)")
        if right_gesture == 'pinch':
            bend = "FASTER" if right_pos[1] < 0.5 else "SLOWER"
            print(f"[SCRATCH MODE] Right pinch -> Pitch bend {bend} (Deck B)")

        # Pointer = Cue point
        if left_gesture == 'pointer':
            print(f"[SCRATCH MODE] Left pointer -> CUE (Deck A)")
        if right_gesture == 'pointer':
            print(f"[SCRATCH MODE] Right pointer -> CUE (Deck B)")

        # Two fingers = Nudge tempo
        if left_gesture == 'two_fingers':
            print(f"[SCRATCH MODE] Left two_fingers -> Nudge tempo UP (Deck A)")
        if right_gesture == 'two_fingers':
            print(f"[SCRATCH MODE] Right two_fingers -> Nudge tempo UP (Deck B)")

    # Thumbs gestures removed - too sensitive, causing false triggers
    # Use web UI buttons to load/unload tracks manually

    def _load_track_dialog(self, deck):
        """Show file browser to load track."""
        try:
            from tkinter import Tk, filedialog

            print(f"[Track] Opening file browser for Deck {deck.upper()}...")

            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            file_path = filedialog.askopenfilename(
                title=f"Load Track for Deck {deck.upper()}",
                filetypes=[
                    ("Audio Files", "*.mp3 *.wav *.flac *.ogg *.m4a"),
                    ("MP3 Files", "*.mp3"),
                    ("WAV Files", "*.wav"),
                    ("FLAC Files", "*.flac"),
                    ("All Files", "*.*")
                ],
                initialdir=os.path.expanduser("~")
            )

            root.destroy()

            if file_path:
                self.audio_engine.load_track(deck, file_path)
                print(f"[Track] ✓ Loaded: {os.path.basename(file_path)} to Deck {deck.upper()}")

                # Get deck object
                target_deck = self.audio_engine.deck_a if deck.lower() == 'a' else self.audio_engine.deck_b

                # Send track info to frontend
                if self.websocket_server:
                    self.websocket_server.update_audio_data({
                        f'deck_{deck}': {
                            'track_name': target_deck.track_name,
                            'artist': target_deck.artist,
                            'bpm': target_deck.bpm,
                            'duration': target_deck.duration,
                            'loaded': True,
                            'waveform': target_deck.waveform_data
                        }
                    })
            else:
                print(f"[Track] File browser cancelled")

        except Exception as e:
            print(f"[Track] Error loading track: {e}")

    def _unload_track(self, deck):
        """Unload/eject track from deck."""
        try:
            self.audio_engine.unload_track(deck)
            print(f"[Track] ✓ Ejected track from Deck {deck.upper()}")

            # Get the updated deck state and send to frontend
            target_deck = self.audio_engine.deck_a if deck.lower() == 'a' else self.audio_engine.deck_b

            if self.websocket_server:
                self.websocket_server.update_audio_data({
                    f'deck_{deck}': target_deck.get_status()
                })
        except Exception as e:
            print(f"[Track] Error unloading track: {e}")

    # Mode-specific controls removed - will be added later
    # def _apply_mode_control(self, gesture_type, position):
    #     """Apply mode-specific control based on gesture type and hand position."""
    #     pass

    def _show_debug_window(self, frame, gesture_state):
        """Show debug window with gesture info and visualizations."""
        debug_frame = frame.copy()
        h, w = debug_frame.shape[:2]

        # Draw hand skeletons for both hands
        left_state = gesture_state.get('left_hand', {})
        right_state = gesture_state.get('right_hand', {})

        if left_state.get('detected') and left_state.get('landmarks'):
            self._draw_hand_skeleton(debug_frame, left_state['landmarks'], (255, 100, 100), "LEFT")
            self._draw_measurement_lines(debug_frame, left_state['landmarks'], (255, 100, 100))

        if right_state.get('detected') and right_state.get('landmarks'):
            self._draw_hand_skeleton(debug_frame, right_state['landmarks'], (100, 100, 255), "RIGHT")
            self._draw_measurement_lines(debug_frame, right_state['landmarks'], (100, 100, 255))

        # Create metrics panel (right side of screen)
        panel_width = 320
        panel_x = w - panel_width - 10

        # Semi-transparent overlay for metrics panel
        overlay = debug_frame.copy()
        cv2.rectangle(overlay, (panel_x - 10, 10), (w - 10, h - 140), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, debug_frame, 0.4, 0, debug_frame)

        # Draw metrics for active hand (prioritize right hand)
        active_hand = None
        active_label = ""
        if right_state.get('detected') and right_state.get('landmarks'):
            active_hand = right_state
            active_label = "RIGHT HAND"
        elif left_state.get('detected') and left_state.get('landmarks'):
            active_hand = left_state
            active_label = "LEFT HAND"

        if active_hand and active_hand.get('landmarks'):
            self._draw_metrics_panel(debug_frame, active_hand, panel_x, 20, active_label)

        # === ENHANCED GESTURE DISPLAY (PROMINENT) ===
        # Draw large gesture labels for both hands
        self._draw_gesture_display(debug_frame, left_state, right_state, w, h)

        # Draw visual feedback for special gestures
        self._draw_gesture_feedback(debug_frame, left_state, right_state, w, h)

        # Draw crossfader visualization
        self._draw_crossfader_viz(debug_frame, w, h)

        # Basic info overlay (top left)
        y_offset = 25
        cv2.putText(debug_frame, f"FPS: {self.current_fps}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # === MODE INDICATOR (PROMINENT TOP CENTER) ===
        self._draw_mode_indicator(debug_frame, w, h)

        # Mode-specific instructions (bottom left)
        instructions = [
            "Q-Quit  |  SPACE-Play A  |  O/P-Demo  |  Swipe L/R: Change Mode",
            "Fist: Play/Pause  |  " + self._get_mode_instruction()
        ]
        start_y = h - 35
        for i, instruction in enumerate(instructions):
            cv2.putText(debug_frame, instruction, (10, start_y + i * 18),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

        cv2.imshow('AirGroove Precision - Debug View', debug_frame)

    def _get_mode_instruction(self):
        """Get mode-specific instruction text."""
        if self.current_mode == 'normal':
            return "Pinch: Crossfader"
        elif self.current_mode == 'fx':
            return "Pointer: Select FX  |  Two Fingers: Adjust  |  Rotate: Intensity"
        elif self.current_mode == 'loop':
            return "Pointer: IN  |  Two Fingers: OUT  |  Pinch: Length  |  Rotate: Move"
        elif self.current_mode == 'scratch':
            return "Rotate: Scratch  |  Pinch: Pitch  |  Pointer: Cue  |  Two Fingers: Nudge"
        return ""

    def _draw_mode_indicator(self, frame, w, h):
        """Draw prominent mode indicator at top center."""
        mode_text = self.current_mode.upper() + " MODE"
        mode_color = self.mode_colors.get(self.current_mode, (255, 255, 255))

        # Get text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 3
        (text_width, text_height), baseline = cv2.getTextSize(mode_text, font, font_scale, thickness)

        # Position at top center
        x = (w - text_width) // 2
        y = 50

        # Draw background rectangle
        padding = 15
        cv2.rectangle(frame,
                     (x - padding, y - text_height - padding),
                     (x + text_width + padding, y + baseline + padding),
                     (0, 0, 0), -1)

        # Draw colored border
        cv2.rectangle(frame,
                     (x - padding, y - text_height - padding),
                     (x + text_width + padding, y + baseline + padding),
                     mode_color, 3)

        # Draw mode text
        cv2.putText(frame, mode_text, (x, y),
                   font, font_scale, mode_color, thickness)

    def _draw_gesture_display(self, frame, left_state, right_state, w, h):
        """Draw clean, simple gesture display with calibration guide."""
        # Simple top bar with gestures
        bar_height = 60
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, bar_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Left hand (Deck A)
        left_gesture = left_state.get('gesture', 'none')
        left_color = self._get_gesture_color(left_gesture)
        left_text = f"L: {left_gesture.replace('_', ' ').upper()}"
        cv2.putText(frame, left_text, (10, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, left_color, 2)

        # Right hand (Deck B)
        right_gesture = right_state.get('gesture', 'none')
        right_color = self._get_gesture_color(right_gesture)
        right_text = f"R: {right_gesture.replace('_', ' ').upper()}"
        cv2.putText(frame, right_text, (w - 250, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, right_color, 2)

        # Center: Current action
        current_action = self._get_current_action(left_gesture, right_gesture)
        if current_action:
            # Measure text size for centering
            text_size = cv2.getTextSize(current_action, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            text_x = (w - text_size[0]) // 2
            cv2.putText(frame, current_action, (text_x, 38),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 136), 2)

        # Distance calibration indicators (bottom left/right corners)
        self._draw_distance_calibration(frame, left_state, right_state, w, h)

    def _draw_distance_calibration(self, frame, left_state, right_state, w, h):
        """Draw distance calibration indicators for hands."""
        REFERENCE_SIZE = 0.25  # Same as in precision_gestures.py
        OPTIMAL_MIN = 0.20
        OPTIMAL_MAX = 0.30

        # Left hand calibration
        if 'hand_landmarks' in left_state and left_state['hand_landmarks']:
            hand_size = self._calculate_hand_size_from_state(left_state)
            if hand_size > 0:
                distance_status, color = self._get_distance_status(hand_size, OPTIMAL_MIN, OPTIMAL_MAX)
                # Draw indicator in bottom-left corner
                cv2.putText(frame, f"L: {distance_status}", (10, h - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Right hand calibration
        if 'hand_landmarks' in right_state and right_state['hand_landmarks']:
            hand_size = self._calculate_hand_size_from_state(right_state)
            if hand_size > 0:
                distance_status, color = self._get_distance_status(hand_size, OPTIMAL_MIN, OPTIMAL_MAX)
                # Draw indicator in bottom-right corner
                text_size = cv2.getTextSize(f"R: {distance_status}", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.putText(frame, f"R: {distance_status}", (w - text_size[0] - 10, h - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    def _calculate_hand_size_from_state(self, hand_state):
        """Calculate hand size from hand state (wrist to middle finger distance)."""
        if 'hand_landmarks' not in hand_state or not hand_state['hand_landmarks']:
            return 0

        landmarks = hand_state['hand_landmarks']
        if len(landmarks) < 13:
            return 0

        wrist = landmarks[0]
        middle_tip = landmarks[12]

        import math
        hand_size = math.sqrt(
            (middle_tip[0] - wrist[0])**2 +
            (middle_tip[1] - wrist[1])**2
        )
        return hand_size

    def _get_distance_status(self, hand_size, optimal_min, optimal_max):
        """Get distance status and color based on hand size."""
        if hand_size < optimal_min:
            return "TOO FAR", (0, 100, 255)  # Orange
        elif hand_size > optimal_max:
            return "TOO CLOSE", (0, 165, 255)  # Orange
        else:
            return "OPTIMAL", (0, 255, 0)  # Green

    def _draw_gesture_feedback(self, frame, left_state, right_state, w, h):
        """Draw minimal visual feedback - only for pinch (crossfader control)."""
        # Only show pinch indicator when actively using crossfader
        left_gesture = left_state.get('gesture', 'none')
        right_gesture = right_state.get('gesture', 'none')

        if left_gesture == 'pinch' or right_gesture == 'pinch':
            # Show simple crossfader active indicator
            cv2.putText(frame, "CROSSFADER ACTIVE", (w//2 - 100, h - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

    def _draw_crossfader_viz(self, frame, w, h):
        """Draw simple crossfader bar at bottom."""
        if not hasattr(self, '_crossfader_smoothed'):
            self._crossfader_smoothed = 0.5

        # Simple bar at bottom
        bar_width = 300
        bar_height = 8
        bar_x = w//2 - bar_width//2
        bar_y = h - 50

        # Background
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)

        # Position marker
        marker_x = bar_x + int(bar_width * self._crossfader_smoothed)
        cv2.circle(frame, (marker_x, bar_y + bar_height//2), 6, (124, 58, 237), -1)

        # Labels
        cv2.putText(frame, "A", (bar_x - 15, bar_y + 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        cv2.putText(frame, "B", (bar_x + bar_width + 5, bar_y + 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

    def _draw_swipe_arrow(self, frame, swipe_direction, x, y):
        """Draw arrow indicating swipe direction."""
        import math

        # Arrow direction angles (in degrees)
        directions = {
            'up': -90, 'down': 90, 'left': 180, 'right': 0,
            'up-left': -135, 'up-right': -45, 'down-left': 135, 'down-right': 45
        }

        angle = directions.get(swipe_direction, 0)
        angle_rad = math.radians(angle)

        # Arrow length
        length = 40
        end_x = int(x + length * math.cos(angle_rad))
        end_y = int(y + length * math.sin(angle_rad))

        # Draw arrow
        cv2.arrowedLine(frame, (x, y), (end_x, end_y), (0, 255, 255), 3, tipLength=0.3)

        # Label
        cv2.putText(frame, f"SWIPE: {swipe_direction.upper()}", (x - 50, y - 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    def _draw_rotation_indicator(self, frame, rotation_vel, x, y):
        """Draw circular arrow indicating rotation."""
        import math

        # Draw circular arc
        radius = 30
        color = (255, 165, 0) if rotation_vel > 0 else (255, 100, 255)

        # Arc angles
        start_angle = 0
        end_angle = 270 if rotation_vel > 0 else -270

        cv2.ellipse(frame, (x, y), (radius, radius), 0, start_angle, end_angle, color, 3)

        # Arrow tip
        tip_angle = math.radians(end_angle)
        tip_x = int(x + radius * math.cos(tip_angle))
        tip_y = int(y + radius * math.sin(tip_angle))

        # Direction indicator
        direction = "CW" if rotation_vel > 0 else "CCW"
        cv2.putText(frame, f"ROTATE {direction}", (x - 40, y - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 2)
        cv2.putText(frame, f"{abs(rotation_vel):.0f} deg/s", (x - 30, y + 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

    def _draw_pinch_indicator(self, frame, position, x, y):
        """Draw pinch amount indicator."""
        # Draw two circles coming together
        circle_spacing = 30 - int(20 * abs(position[0] - 0.5))  # Closer circles = stronger pinch

        cv2.circle(frame, (x - circle_spacing, y), 12, (255, 0, 255), 2)
        cv2.circle(frame, (x + circle_spacing, y), 12, (255, 0, 255), 2)

        cv2.putText(frame, "PINCH ACTIVE", (x - 50, y - 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 2)

    def _get_gesture_color(self, gesture):
        """Get color for gesture display."""
        colors = {
            'none': (100, 100, 100),
            'open_palm': (200, 200, 200),
            'closed_fist': (255, 100, 100),
            'pinch': (255, 0, 255),
            'pointer': (0, 255, 255),
            'two_fingers': (0, 255, 136),
            'thumbs_up': (0, 255, 0),
            'thumbs_down': (255, 0, 0)
        }
        return colors.get(gesture, (150, 150, 150))

    def _get_gesture_emoji(self, gesture):
        """Get emoji representation of gesture."""
        emojis = {
            'none': '...',
            'open_palm': '[hand]',
            'closed_fist': '[fist]',
            'pinch': '[pinch]',
            'pointer': '[point]',
            'two_fingers': '[peace]',
            'thumbs_up': '[up]',
            'thumbs_down': '[down]'
        }
        return emojis.get(gesture, '?')

    def _get_current_action(self, left_gesture, right_gesture):
        """Get current action description based on gestures."""
        if left_gesture == 'closed_fist' or right_gesture == 'closed_fist':
            return "PLAY/PAUSE"
        elif left_gesture == 'pinch' or right_gesture == 'pinch':
            return "CROSSFADER"
        # Thumbs gestures removed - use web UI buttons for load/unload
        return ""

    def _draw_hand_skeleton(self, frame, landmarks, color, label):
        """Draw hand skeleton with landmarks and connections."""
        h, w = frame.shape[:2]

        # MediaPipe hand connections
        connections = [
            # Thumb
            (0, 1), (1, 2), (2, 3), (3, 4),
            # Index
            (0, 5), (5, 6), (6, 7), (7, 8),
            # Middle
            (0, 9), (9, 10), (10, 11), (11, 12),
            # Ring
            (0, 13), (13, 14), (14, 15), (15, 16),
            # Pinky
            (0, 17), (17, 18), (18, 19), (19, 20),
            # Palm
            (5, 9), (9, 13), (13, 17)
        ]

        # Draw connections
        for start_idx, end_idx in connections:
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start_point = (int(landmarks[start_idx][0] * w), int(landmarks[start_idx][1] * h))
                end_point = (int(landmarks[end_idx][0] * w), int(landmarks[end_idx][1] * h))
                cv2.line(frame, start_point, end_point, color, 2)

        # Draw landmarks
        for i, (x, y) in enumerate(landmarks):
            point = (int(x * w), int(y * h))
            # Different colors for different parts
            if i == 0:  # Wrist
                cv2.circle(frame, point, 6, (255, 255, 0), -1)
            elif i in [4, 8, 12, 16, 20]:  # Fingertips
                cv2.circle(frame, point, 5, (0, 255, 255), -1)
            else:  # Other joints
                cv2.circle(frame, point, 3, color, -1)

        # Draw label near wrist
        if len(landmarks) > 0:
            wrist_point = (int(landmarks[0][0] * w), int(landmarks[0][1] * h) - 15)
            cv2.putText(frame, label, wrist_point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def _draw_measurement_lines(self, frame, landmarks, color):
        """Draw key measurement lines."""
        h, w = frame.shape[:2]

        # Thumb to wrist line
        wrist = (int(landmarks[0][0] * w), int(landmarks[0][1] * h))
        thumb_tip = (int(landmarks[4][0] * w), int(landmarks[4][1] * h))
        cv2.line(frame, wrist, thumb_tip, (0, 255, 255), 1, cv2.LINE_AA)

        # Thumb to index line
        index_tip = (int(landmarks[8][0] * w), int(landmarks[8][1] * h))
        cv2.line(frame, thumb_tip, index_tip, (255, 0, 255), 1, cv2.LINE_AA)

        # Hand width line (index to pinky)
        pinky_tip = (int(landmarks[20][0] * w), int(landmarks[20][1] * h))
        cv2.line(frame, index_tip, pinky_tip, (0, 255, 0), 1, cv2.LINE_AA)

    def _draw_metrics_panel(self, frame, hand_state, x, y, label):
        """Draw detailed metrics panel."""
        landmarks = hand_state.get('landmarks')
        if not landmarks:
            return

        # Get debug measurements
        debug_info = self.gesture_recognizer.get_debug_measurements(landmarks)
        if not debug_info:
            return

        distances = debug_info.get('distances', {})
        thumbs_up_cond = debug_info.get('thumbs_up_conditions', {})
        fist_cond = debug_info.get('closed_fist_conditions', {})
        fingers_folded = debug_info.get('fingers_folded', {})

        y_pos = y
        line_height = 18

        # Title
        cv2.putText(frame, label, (x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        y_pos += line_height + 5

        # Current gesture
        gesture = hand_state.get('gesture', 'none')
        gesture_color = (0, 255, 0) if gesture not in ['none', 'unknown'] else (150, 150, 150)
        cv2.putText(frame, f"Gesture: {gesture}", (x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.45, gesture_color, 1)
        y_pos += line_height + 8

        # Distances section
        cv2.putText(frame, "KEY DISTANCES:", (x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        y_pos += line_height

        dist_items = [
            ('Thumb-Wrist V', distances.get('thumb_wrist_vertical', 0), -0.10, '<'),
            ('Thumb-Index', distances.get('thumb_index', 0), 0.03, '>'),
            ('Hand Width', distances.get('hand_width', 0), None, None)
        ]

        for label_text, value, threshold, comparison in dist_items:
            color = self._get_condition_color(value, threshold, comparison) if threshold else (255, 255, 255)
            text = f"{label_text}: {value:.3f}"
            cv2.putText(frame, text, (x + 5, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
            y_pos += line_height - 2

        y_pos += 5

        # Fingers state
        cv2.putText(frame, "FINGERS FOLDED:", (x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        y_pos += line_height

        for finger_name in ['thumb', 'index', 'middle', 'ring', 'pinky']:
            is_folded = fingers_folded.get(finger_name, False)
            color = (0, 255, 0) if is_folded else (100, 100, 100)
            symbol = "✓" if is_folded else "✗"
            text = f"{symbol} {finger_name.capitalize()}"
            cv2.putText(frame, text, (x + 5, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
            y_pos += line_height - 2

        y_pos += 5

        # Thumbs Up conditions
        cv2.putText(frame, "THUMBS UP:", (x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        y_pos += line_height

        for cond_name, cond_value in thumbs_up_cond.items():
            color = (0, 255, 0) if cond_value else (80, 80, 80)
            symbol = "✓" if cond_value else "✗"
            display_name = cond_name.replace('_', ' ').title()[:15]
            text = f"{symbol} {display_name}"
            cv2.putText(frame, text, (x + 5, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.32, color, 1)
            y_pos += line_height - 3

        y_pos += 5

        # Closed Fist conditions
        cv2.putText(frame, "CLOSED FIST:", (x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        y_pos += line_height

        for cond_name, cond_value in fist_cond.items():
            color = (0, 255, 0) if cond_value else (80, 80, 80)
            symbol = "✓" if cond_value else "✗"
            display_name = cond_name.replace('_', ' ').title()[:15]
            text = f"{symbol} {display_name}"
            cv2.putText(frame, text, (x + 5, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.32, color, 1)
            y_pos += line_height - 3

    def _get_condition_color(self, value, threshold, comparison):
        """Get color based on whether condition is met."""
        if comparison == '<':
            met = value < threshold
        elif comparison == '>':
            met = value > threshold
        else:
            return (255, 255, 255)

        return (0, 255, 0) if met else (0, 100, 255)

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
            # Load track from file browser dialog
            print(f"[Audio] Load track request for deck {deck}")
            self._load_track_dialog(deck)
        elif action == 'unload_track':
            # Unload/eject track from deck
            print(f"[Audio] Unload track request for deck {deck}")
            self._unload_track(deck)
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
        elif action == 'seek':
            # Handle seek control
            position = parameters.get('position', 0.0)
            self.audio_engine.seek_deck(deck, position)

        print(f"[Audio] {action} on {deck if deck else 'system'}")

    def _on_ui_interaction(self, element, action, position):
        """Handle UI interaction from web interface."""
        print(f"[UI] {action} on {element}")

    def _on_audio_status_changed(self, status):
        """Handle audio status updates."""
        print(f"[TRACE-WS] _on_audio_status_changed called with FX state: {status.get('fx_state', 'NO FX STATE')}")
        if self.websocket_server:
            print(f"[TRACE-WS] Calling websocket_server.update_audio_data()")
            self.websocket_server.update_audio_data(status)
            print(f"[TRACE-WS] update_audio_data() completed")

    def _on_fx_state_changed(self, fx_state):
        """Handle FX state updates."""
        print(f"[FX STATE UPDATE] {fx_state}")
        if self.websocket_server:
            self.websocket_server.broadcast_json({
                'type': 'fx_state_update',
                'payload': fx_state
            })

    def _on_audio_control(self, action, parameters):
        """Handle audio control commands from web UI."""
        if action == 'seek':
            deck = parameters.get('deck', '')
            position = parameters.get('position', 0.0)
            print(f"[AUDIO CONTROL] Seek deck {deck.upper()} to {position:.2f}s")
            self.audio_engine.seek_deck(deck, position)
        elif action == 'load_track':
            deck = parameters.get('deck', '')
            print(f"[AUDIO CONTROL] Load track request for Deck {deck.upper()}")
            self._load_track_dialog(deck)
        elif action == 'unload_track':
            deck = parameters.get('deck', '')
            print(f"[AUDIO CONTROL] Unload track from Deck {deck.upper()}")
            self.audio_engine.unload_track(deck)
        elif action == 'fx_control':
            parameter = parameters.get('parameter', '')
            value = parameters.get('value', 0.0)
            print(f"[FX CONTROL] {parameter} = {value}")
            self.audio_engine.fx_control(parameter, value)
        elif action == 'loop_control':
            parameter = parameters.get('parameter', '')
            value = parameters.get('value', 0.0)
            print(f"[LOOP CONTROL] {parameter} = {value}")
            self.audio_engine.loop_control(parameter, value)
        elif action == 'loop_action':
            loop_action = parameters.get('action', '')
            print(f"[LOOP ACTION] {loop_action}")
            self.audio_engine.loop_action(loop_action, parameters)
        else:
            print(f"[AUDIO CONTROL] Unknown action: {action}")

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