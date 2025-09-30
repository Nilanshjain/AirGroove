#!/usr/bin/env python3
"""
Web-optimized audio engine with mode-based control for AirGroove DJ interface.
Handles audio processing, effects, and real-time parameter updates.
"""

import pygame
import threading
import time
import numpy as np
from typing import Dict, Optional, Callable
import os
import librosa

class WebAudioEngine:
    """Web-optimized audio engine with advanced DJ controls."""

    def __init__(self):
        """Initialize the web audio engine."""
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()

        # Audio state
        self.deck_a = AudioDeck('A')
        self.deck_b = AudioDeck('B')
        self.crossfader_position = 0.5  # 0 = full A, 1 = full B
        self.master_volume = 1.0

        # Current mode and effects
        self.current_mode = None
        self.fx_engine = EffectsEngine()
        self.loop_engine = LoopEngine()
        self.scratch_engine = ScratchEngine()

        # Status callback
        self.on_status_changed = None

        # Audio processing thread
        self.processing_thread = None
        self.is_processing = False

        print("[AudioEngine] Web audio engine initialized")

    def start_processing(self):
        """Start the audio processing thread."""
        if not self.is_processing:
            self.is_processing = True
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()

    def stop_processing(self):
        """Stop the audio processing thread."""
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join()

    def _processing_loop(self):
        """Main audio processing loop."""
        while self.is_processing:
            # Update deck states
            self.deck_a.update()
            self.deck_b.update()

            # Apply mode-specific processing
            if self.current_mode == 'fx':
                self.fx_engine.process(self.deck_a, self.deck_b)
            elif self.current_mode == 'loop':
                self.loop_engine.process(self.deck_a, self.deck_b)
            elif self.current_mode == 'scratch':
                self.scratch_engine.process(self.deck_a, self.deck_b)

            # Send status updates
            self._send_status_update()

            time.sleep(1/60)  # 60 FPS processing

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

    # Deck control methods
    def load_track(self, deck: str, file_path: str):
        """Load a track into the specified deck."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.load_track(file_path)

    def play_deck(self, deck: str):
        """Start playing the specified deck."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.play()

    def pause_deck(self, deck: str):
        """Pause the specified deck."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.pause()

    def stop_deck(self, deck: str):
        """Stop the specified deck."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.stop()

    def set_deck_volume(self, deck: str, volume: float):
        """Set volume for the specified deck."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.set_volume(volume)

    def set_crossfader(self, position: float):
        """Set crossfader position (0.0 = deck A, 1.0 = deck B)."""
        self.crossfader_position = max(0.0, min(1.0, position))

    # Mode-specific control methods
    def fx_control(self, parameter: str, value: float):
        """Control FX parameters."""
        if self.current_mode == 'fx':
            self.fx_engine.set_parameter(parameter, value)

    def loop_control(self, parameter: str, value: float):
        """Control loop parameters."""
        if self.current_mode == 'loop':
            self.loop_engine.set_parameter(parameter, value)

    def scratch_control(self, parameter: str, value: float):
        """Control scratch parameters."""
        if self.current_mode == 'scratch':
            self.scratch_engine.set_parameter(parameter, value)

    def _send_status_update(self):
        """Send status update to web interface."""
        if self.on_status_changed:
            status = {
                'deck_a': self.deck_a.get_status(),
                'deck_b': self.deck_b.get_status(),
                'crossfader': self.crossfader_position,
                'master_volume': self.master_volume,
                'current_mode': self.current_mode,
                'fx_state': self.fx_engine.get_state() if self.current_mode == 'fx' else {},
                'loop_state': self.loop_engine.get_state() if self.current_mode == 'loop' else {},
                'scratch_state': self.scratch_engine.get_state() if self.current_mode == 'scratch' else {}
            }
            self.on_status_changed(status)

    def stop(self):
        """Stop the audio engine."""
        self.stop_processing()
        self.deck_a.stop()
        self.deck_b.stop()
        pygame.mixer.quit()


class AudioDeck:
    """Individual audio deck with playback control."""

    def __init__(self, name: str):
        """Initialize an audio deck."""
        self.name = name
        self.sound = None
        self.channel = None
        self.file_path = None
        self.track_name = ""
        self.artist = ""
        self.bpm = 120.0
        self.position = 0.0
        self.duration = 0.0
        self.volume = 1.0
        self.playing = False
        self.waveform_data = []

    def load_track(self, file_path: str):
        """Load an audio track."""
        try:
            if os.path.exists(file_path):
                self.file_path = file_path
                self.sound = pygame.mixer.Sound(file_path)
                self.track_name = os.path.basename(file_path)
                self.artist = "Unknown Artist"

                # Load audio for analysis
                y, sr = librosa.load(file_path, sr=22050)
                self.duration = len(y) / sr

                # Generate waveform data
                hop_length = len(y) // 1000  # 1000 points max
                self.waveform_data = y[::hop_length].tolist()

                # Estimate BPM
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                self.bpm = float(tempo)

                print(f"[Deck {self.name}] Loaded: {self.track_name}")

        except Exception as e:
            print(f"[Deck {self.name}] Error loading track: {e}")

    def play(self):
        """Start playing the track."""
        if self.sound:
            self.channel = self.sound.play()
            self.playing = True
            print(f"[Deck {self.name}] Playing")

    def pause(self):
        """Pause the track."""
        if self.channel:
            pygame.mixer.pause()
            self.playing = False
            print(f"[Deck {self.name}] Paused")

    def stop(self):
        """Stop the track."""
        if self.channel:
            self.channel.stop()
            self.playing = False
            self.position = 0.0
            print(f"[Deck {self.name}] Stopped")

    def set_volume(self, volume: float):
        """Set deck volume."""
        self.volume = max(0.0, min(1.0, volume))
        if self.channel:
            self.channel.set_volume(self.volume)

    def update(self):
        """Update deck state."""
        if self.channel and self.playing:
            # Update position (simplified)
            if not self.channel.get_busy():
                self.playing = False
                self.position = 0.0

    def get_status(self) -> Dict:
        """Get current deck status."""
        return {
            'track_name': self.track_name,
            'artist': self.artist,
            'bpm': self.bpm,
            'position': self.position,
            'duration': self.duration,
            'playing': self.playing,
            'volume': self.volume,
            'waveform': self.waveform_data
        }


class EffectsEngine:
    """Audio effects processing for FX mode."""

    def __init__(self):
        """Initialize effects engine."""
        self.filter_freq = 0.5
        self.reverb_level = 0.0
        self.delay_level = 0.0
        self.mix_level = 0.5

    def set_parameter(self, parameter: str, value: float):
        """Set effect parameter."""
        value = max(0.0, min(1.0, value))

        if parameter == 'filter':
            self.filter_freq = value
        elif parameter == 'reverb':
            self.reverb_level = value
        elif parameter == 'delay':
            self.delay_level = value
        elif parameter == 'mix':
            self.mix_level = value

    def process(self, deck_a: AudioDeck, deck_b: AudioDeck):
        """Process audio with effects."""
        # Simplified effects processing
        # In a real implementation, this would apply actual DSP effects
        pass

    def reset(self):
        """Reset all effects."""
        self.filter_freq = 0.5
        self.reverb_level = 0.0
        self.delay_level = 0.0
        self.mix_level = 0.5

    def get_state(self) -> Dict:
        """Get current effects state."""
        return {
            'filter': self.filter_freq,
            'reverb': self.reverb_level,
            'delay': self.delay_level,
            'mix': self.mix_level
        }


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

    def process(self, deck_a: AudioDeck, deck_b: AudioDeck):
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

    def process(self, deck_a: AudioDeck, deck_b: AudioDeck):
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