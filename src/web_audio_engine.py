#!/usr/bin/env python3
"""
Web-optimized audio engine with mode-based control for AirGroove DJ interface.
Handles audio processing, effects, and real-time parameter updates.
"""

import threading
import time
import numpy as np
from typing import Dict, Optional, Callable
import os
from sounddevice_audio_engine import SoundDeviceAudioEngine
from effects_processor import EffectsProcessor

class WebAudioEngine:
    """Web-optimized audio engine with advanced DJ controls."""

    def __init__(self):
        """Initialize the web audio engine."""
        # Use sounddevice backend for real-time audio processing
        self.sd_engine = SoundDeviceAudioEngine(sample_rate=44100, buffer_size=1024)

        # Current mode - Default to NORMAL mode
        self.current_mode = 'normal'

        # Mode-specific engines
        self.fx_engine = EffectsEngine(self.sd_engine.effects_processor)
        self.loop_engine = LoopEngine()
        self.scratch_engine = ScratchEngine()

        # Status callback
        self.on_status_changed = None
        self.on_fx_state_changed = None

        # Audio processing thread for status updates
        self.processing_thread = None
        self.is_processing = False

        # Cached FX state for change detection
        self._last_fx_state = None

        print("[AudioEngine] Web audio engine initialized with sounddevice backend")

    def start_processing(self):
        """Start the audio processing."""
        # Start sounddevice audio stream
        self.sd_engine.start_processing()

        # Start status update thread
        if not self.is_processing:
            self.is_processing = True
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()

    def stop_processing(self):
        """Stop the audio processing."""
        # Stop sounddevice audio stream
        self.sd_engine.stop_processing()

        # Stop status update thread
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join()

    def _processing_loop(self):
        """Main status update loop."""
        while self.is_processing:
            # Send status updates (actual audio processing happens in sounddevice callback)
            self._send_status_update()
            time.sleep(1/60)  # 60 FPS status updates

    def set_mode(self, mode: str):
        """Set the current control mode."""
        self.current_mode = mode
        print(f"[AudioEngine] Mode set to: {mode}")

        # Reset mode-specific states
        if mode == 'fx':
            self.fx_engine.reset()
        elif mode == 'loop':
            self.loop_engine.reset()
        elif mode == 'scratch':
            self.scratch_engine.reset()

    # Deck control methods (pass through to sounddevice backend)
    def load_track(self, deck: str, file_path: str):
        """Load a track into the specified deck."""
        self.sd_engine.load_track(deck, file_path)

    def play_deck(self, deck: str):
        """Start playing the specified deck."""
        self.sd_engine.play_deck(deck)

    def pause_deck(self, deck: str):
        """Pause the specified deck."""
        self.sd_engine.pause_deck(deck)

    def stop_deck(self, deck: str):
        """Stop the specified deck."""
        self.sd_engine.stop_deck(deck)

    def unload_track(self, deck: str):
        """Unload/eject track from the specified deck."""
        self.sd_engine.unload_track(deck)

    def set_deck_volume(self, deck: str, volume: float):
        """Set volume for the specified deck."""
        self.sd_engine.set_deck_volume(deck, volume)

    def seek_deck(self, deck: str, position: float):
        """Seek to a specific position in the track (in seconds)."""
        self.sd_engine.seek_deck(deck, position)

    def set_crossfader(self, position: float):
        """Set crossfader position and apply audio mixing (0.0 = deck A, 1.0 = deck B)."""
        # Pass through to sounddevice backend (it handles constant power law)
        self.sd_engine.set_crossfader(position)

        # Send update to web interface immediately
        self._send_status_update()

    # Mode-specific control methods
    def fx_control(self, parameter: str, value: float):
        """Control FX parameters."""
        if self.current_mode == 'fx':
            self.fx_engine.set_parameter(parameter, value)
            # Pass through to sounddevice backend effects processor
            self.sd_engine.fx_control(parameter, value)

    def loop_control(self, parameter: str, value: float):
        """Control loop parameters."""
        if self.current_mode == 'loop':
            self.loop_engine.set_parameter(parameter, value)
        # Pass through to sounddevice backend
        self.sd_engine.loop_control(parameter, value)

    def loop_action(self, action: str, parameters: dict):
        """Handle loop actions."""
        # Pass through to sounddevice backend
        self.sd_engine.loop_action(action, parameters)

    def scratch_control(self, parameter: str, value: float):
        """Control scratch parameters."""
        if self.current_mode == 'scratch':
            self.scratch_engine.set_parameter(parameter, value)

    def _send_status_update(self):
        """Send status update to web interface."""
        if self.on_status_changed:
            # Get status from sounddevice backend
            deck_a_status = self.sd_engine.deck_a.get_status()
            deck_b_status = self.sd_engine.deck_b.get_status()

            # Get FX state from real effects processor
            fx_state = self.sd_engine.get_fx_state() if self.current_mode == 'fx' else self.fx_engine.get_state()

            # Only send FX state update if it changed (reduce WebSocket traffic)
            fx_state_changed = (fx_state != self._last_fx_state)
            if fx_state_changed:
                self._last_fx_state = fx_state.copy() if isinstance(fx_state, dict) else fx_state

            status = {
                'deck_a': deck_a_status,
                'deck_b': deck_b_status,
                'crossfader': self.sd_engine.crossfader_position,
                'master_volume': self.sd_engine.master_volume,
                'current_mode': self.current_mode,
                'fx_state': fx_state,
                'loop_state': self.loop_engine.get_state() if self.current_mode == 'loop' else {},
                'scratch_state': self.scratch_engine.get_state() if self.current_mode == 'scratch' else {}
            }
            self.on_status_changed(status)

            # Also send dedicated FX state update ONLY if changed and in FX mode
            if (fx_state_changed and hasattr(self, 'on_fx_state_changed') and
                self.on_fx_state_changed and self.current_mode == 'fx'):
                self.on_fx_state_changed(fx_state)

    def stop(self):
        """Stop the audio engine."""
        self.stop_processing()
        print("[AudioEngine] Stopped")


class EffectsEngine:
    """Audio effects processing for FX mode (wraps real EffectsProcessor)."""

    def __init__(self, effects_processor: EffectsProcessor):
        """Initialize effects engine with real effects processor."""
        self.effects_processor = effects_processor

    def set_parameter(self, parameter: str, value: float):
        """Set effect parameter."""
        # Map generic parameters to specific effects processor methods
        if parameter == 'filter_type':
            self.effects_processor.set_filter_type(str(value))
        elif parameter == 'cutoff':
            self.effects_processor.set_filter_cutoff(value)
        elif parameter == 'resonance':
            self.effects_processor.set_filter_resonance(value)
        elif parameter == 'wet_dry':
            self.effects_processor.set_wet_dry_mix(value)
        elif parameter == 'enable':
            self.effects_processor.enable_filter(bool(value))

    def reset(self):
        """Reset all effects."""
        self.effects_processor.reset()

    def get_state(self) -> Dict:
        """Get current effects state."""
        return self.effects_processor.get_state()


class LoopEngine:
    """Loop control engine for loop mode."""

    def __init__(self):
        """Initialize loop engine."""
        self.loop_length = 4  # beats
        self.loop_position = 0.0
        self.loop_active = False
        self.loop_in = 0.0
        self.loop_out = 4.0

    def set_parameter(self, parameter: str, value: float):
        """Set loop parameter."""
        if parameter == 'length':
            self.loop_length = max(1, int(value * 16))  # 1-16 beats
        elif parameter == 'position':
            self.loop_position = value * 10  # 0-10 seconds
        elif parameter == 'roll':
            # Trigger loop roll effect
            pass

    def process(self, deck_a, deck_b):
        """Process loop controls."""
        # Simplified loop processing
        pass

    def reset(self):
        """Reset loop state."""
        self.loop_length = 4
        self.loop_position = 0.0
        self.loop_active = False

    def get_state(self) -> Dict:
        """Get current loop state."""
        return {
            'length': self.loop_length,
            'position': self.loop_position,
            'active': self.loop_active,
            'in_point': self.loop_in,
            'out_point': self.loop_out
        }


class ScratchEngine:
    """Scratch control engine for scratch mode."""

    def __init__(self):
        """Initialize scratch engine."""
        self.scratch_speed = 0.0
        self.pitch_bend = 0.0
        self.turntable_position = 0.0

    def set_parameter(self, parameter: str, value: float):
        """Set scratch parameter."""
        if parameter == 'speed':
            self.scratch_speed = value * 2.0 - 1.0  # -1 to 1
        elif parameter == 'pitch':
            self.pitch_bend = (value - 0.5) * 2.0  # -1 to 1

    def process(self, deck_a, deck_b):
        """Process scratch controls."""
        # Update turntable position based on scratch speed
        self.turntable_position += self.scratch_speed

    def reset(self):
        """Reset scratch state."""
        self.scratch_speed = 0.0
        self.pitch_bend = 0.0
        self.turntable_position = 0.0

    def get_state(self) -> Dict:
        """Get current scratch state."""
        return {
            'speed': self.scratch_speed,
            'pitch': self.pitch_bend,
            'turntable_position': self.turntable_position % 360
        }