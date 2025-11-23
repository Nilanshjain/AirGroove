#!/usr/bin/env python3
"""
SoundDevice Audio Engine for AirGroove DJ
Real-time audio playback with effects processing using sounddevice.
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import time
import math
from pathlib import Path
from typing import Dict, Optional, Callable
import librosa
from effects_processor import EffectsProcessor


class SoundDeviceDeck:
    """Individual audio deck with real-time playback."""

    def __init__(self, name: str, sample_rate: int = 44100):
        """Initialize deck."""
        self.name = name
        self.sample_rate = sample_rate

        # Audio data
        self.audio_data = None  # numpy array [samples, channels]
        self.position = 0  # Current playback position in samples
        self.playing = False
        self.volume = 1.0

        # Track metadata
        self.track_name = "No Track Loaded"
        self.artist = "Unknown Artist"
        self.bpm = 120.0
        self.duration = 0.0
        self.waveform_data = []
        self.loaded = False

        # Loading state
        self.loading = False
        self.load_progress = 0.0
        self.load_thread = None

        # Thread safety
        self.lock = threading.Lock()

        print(f"[Deck {self.name}] Initialized")

    def load_track(self, file_path: str):
        """Load an audio track asynchronously in background thread."""
        # Cancel any existing load operation
        if self.load_thread and self.load_thread.is_alive():
            print(f"[Deck {self.name}] Canceling previous load operation")
            # Note: We can't truly cancel a running thread, but we can ignore its results
            self.loading = False

        # Start loading in background thread
        self.loading = True
        self.load_progress = 0.0
        self.load_thread = threading.Thread(
            target=self._load_track_worker,
            args=(file_path,),
            daemon=True
        )
        self.load_thread.start()
        print(f"[Deck {self.name}] Started loading: {Path(file_path).name}")

    def _load_track_worker(self, file_path: str):
        """Worker thread for loading tracks (runs in background)."""
        try:
            # Step 1: Load audio file (30% of progress)
            self.load_progress = 0.1
            audio_data, sr = sf.read(file_path, always_2d=True)
            self.load_progress = 0.3

            if not self.loading:  # Check if canceled
                return

            # Step 2: Resample if needed (40% of progress)
            if sr != self.sample_rate:
                print(f"[Deck {self.name}] Resampling {sr}Hz -> {self.sample_rate}Hz")
                resampled = []
                for ch in range(audio_data.shape[1]):
                    resampled_ch = librosa.resample(
                        audio_data[:, ch],
                        orig_sr=sr,
                        target_sr=self.sample_rate
                    )
                    resampled.append(resampled_ch)
                audio_data = np.column_stack(resampled)
            self.load_progress = 0.7

            if not self.loading:  # Check if canceled
                return

            # Step 3: Generate waveform (10% of progress)
            hop_length = len(audio_data) // 1000
            if hop_length > 0:
                waveform_data = audio_data[::hop_length, 0].tolist()
            else:
                waveform_data = audio_data[:, 0].tolist()
            self.load_progress = 0.8

            # Step 4: Detect BPM (optional, 10% of progress)
            bpm = 120.0  # Default BPM
            try:
                y_mono = np.mean(audio_data, axis=1)
                tempo, _ = librosa.beat.beat_track(y=y_mono, sr=self.sample_rate)
                bpm = float(tempo)
            except:
                pass  # Use default BPM if detection fails
            self.load_progress = 0.9

            if not self.loading:  # Check if canceled
                return

            # Step 5: Atomically update deck state (thread-safe)
            with self.lock:
                self.audio_data = audio_data.astype(np.float32)
                self.duration = len(audio_data) / self.sample_rate
                self.position = 0
                self.track_name = Path(file_path).name
                self.waveform_data = waveform_data
                self.bpm = bpm
                self.loaded = True
                self.loading = False
                self.load_progress = 1.0

            print(f"[Deck {self.name}] Loaded: {self.track_name}")
            print(f"[Deck {self.name}] Duration: {self.duration:.1f}s, BPM: {self.bpm:.1f}")

        except Exception as e:
            print(f"[Deck {self.name}] Error loading track: {e}")
            with self.lock:
                self.loaded = False
                self.loading = False
                self.load_progress = 0.0

    def get_audio_chunk(self, num_frames: int) -> np.ndarray:
        """
        Get audio chunk for playback.

        Args:
            num_frames: Number of frames to get

        Returns:
            Audio chunk [num_frames, 2]
        """
        with self.lock:
            if not self.playing or self.audio_data is None or not self.loaded:
                return np.zeros((num_frames, 2), dtype=np.float32)

            end_pos = self.position + num_frames

            # Check if we've reached the end
            if end_pos >= len(self.audio_data):
                # Get remaining audio
                remaining = len(self.audio_data) - self.position
                if remaining > 0:
                    chunk = self.audio_data[self.position:self.position + remaining]
                    # Pad with zeros
                    padding = num_frames - remaining
                    chunk = np.pad(chunk, ((0, padding), (0, 0)), mode='constant')
                else:
                    chunk = np.zeros((num_frames, 2), dtype=np.float32)

                # Stop playback
                self.playing = False
                self.position = 0
            else:
                chunk = self.audio_data[self.position:end_pos]
                self.position = end_pos

            # Apply volume
            return chunk * self.volume

    def play(self):
        """Start playback."""
        with self.lock:
            if self.audio_data is not None and self.loaded:
                self.playing = True
                print(f"[Deck {self.name}] Playing")

    def pause(self):
        """Pause playback."""
        with self.lock:
            self.playing = False
            print(f"[Deck {self.name}] Paused")

    def stop(self):
        """Stop playback and reset position."""
        with self.lock:
            self.playing = False
            self.position = 0
            print(f"[Deck {self.name}] Stopped")

    def unload(self):
        """Unload track."""
        with self.lock:
            self.audio_data = None
            self.track_name = "No Track Loaded"
            self.artist = "Unknown Artist"
            self.bpm = 120.0
            self.duration = 0.0
            self.position = 0
            self.playing = False
            self.waveform_data = []
            self.loaded = False
            print(f"[Deck {self.name}] Unloaded")

    def set_volume(self, volume: float):
        """Set deck volume."""
        with self.lock:
            self.volume = np.clip(volume, 0.0, 1.0)

    def seek(self, position_seconds: float):
        """Seek to position."""
        with self.lock:
            if self.audio_data is not None:
                position_samples = int(position_seconds * self.sample_rate)
                self.position = np.clip(position_samples, 0, len(self.audio_data))

    def get_status(self) -> Dict:
        """Get deck status."""
        with self.lock:
            current_time = self.position / self.sample_rate if self.sample_rate > 0 else 0.0
            return {
                'track_name': self.track_name,
                'artist': self.artist,
                'bpm': self.bpm,
                'position': current_time,
                'duration': self.duration,
                'playing': self.playing,
                'volume': self.volume,
                'waveform': self.waveform_data,
                'loaded': self.loaded,
                'loading': self.loading,
                'load_progress': self.load_progress
            }


class SoundDeviceAudioEngine:
    """Real-time audio engine using sounddevice."""

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 1024):
        """Initialize audio engine."""
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Decks
        self.deck_a = SoundDeviceDeck('A', sample_rate)
        self.deck_b = SoundDeviceDeck('B', sample_rate)

        # Mixing
        self.crossfader_position = 0.5  # 0 = A, 1 = B
        self.master_volume = 1.0

        # Effects
        self.effects_processor = EffectsProcessor(sample_rate)

        # Audio stream
        self.stream = None
        self.stream_active = False

        # Callbacks
        self.on_status_changed = None

        # Thread safety
        self.lock = threading.Lock()

        print("[SoundDeviceAudioEngine] Initialized")
        print(f"[SoundDeviceAudioEngine] Sample rate: {sample_rate} Hz")
        print(f"[SoundDeviceAudioEngine] Buffer size: {buffer_size} frames")

    def audio_callback(self, outdata: np.ndarray, frames: int, time_info, status):
        """Audio callback for sounddevice stream."""
        try:
            # Get audio from both decks
            audio_a = self.deck_a.get_audio_chunk(frames)
            audio_b = self.deck_b.get_audio_chunk(frames)

            # Apply crossfader (constant power law)
            angle = self.crossfader_position * (math.pi / 2)
            vol_a = math.cos(angle)
            vol_b = math.sin(angle)

            # Mix
            mixed = audio_a * vol_a + audio_b * vol_b

            # Apply effects
            if self.effects_processor.filter_enabled:
                mixed = self.effects_processor.process_audio(mixed)

            # Apply master volume
            mixed = mixed * self.master_volume

            # Clip to prevent distortion
            mixed = np.clip(mixed, -1.0, 1.0)

            # Output
            outdata[:] = mixed

        except Exception as e:
            print(f"[AudioEngine] Error in callback: {e}")
            outdata.fill(0)

    def start_processing(self):
        """Start audio processing."""
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                callback=self.audio_callback,
                blocksize=self.buffer_size,
                dtype=np.float32
            )
            self.stream.start()
            self.stream_active = True
            print("[SoundDeviceAudioEngine] Stream started")

        except Exception as e:
            print(f"[SoundDeviceAudioEngine] Error starting stream: {e}")
            self.stream_active = False

    def stop_processing(self):
        """Stop audio processing."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.stream_active = False
            print("[SoundDeviceAudioEngine] Stream stopped")

    # Deck control methods
    def load_track(self, deck: str, file_path: str):
        """Load track."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.load_track(file_path)

    def play_deck(self, deck: str):
        """Play deck."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.play()

    def pause_deck(self, deck: str):
        """Pause deck."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.pause()

    def stop_deck(self, deck: str):
        """Stop deck."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.stop()

    def unload_track(self, deck: str):
        """Unload track."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.unload()

    def set_deck_volume(self, deck: str, volume: float):
        """Set deck volume."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.set_volume(volume)

    def seek_deck(self, deck: str, position: float):
        """Seek deck."""
        target_deck = self.deck_a if deck.lower() == 'a' else self.deck_b
        target_deck.seek(position)

    def set_crossfader(self, position: float):
        """Set crossfader position."""
        with self.lock:
            self.crossfader_position = np.clip(position, 0.0, 1.0)

    # Effects control
    def fx_control(self, parameter: str, value: float):
        """Control FX parameter."""
        if parameter == 'filter_type':
            # value should be 'lowpass', 'highpass', or 'bandpass'
            self.effects_processor.set_filter_type(str(value))
        elif parameter == 'cutoff':
            self.effects_processor.set_filter_cutoff(value)
        elif parameter == 'resonance':
            self.effects_processor.set_filter_resonance(value)
        elif parameter == 'wet_dry':
            self.effects_processor.set_wet_dry_mix(value)
        elif parameter == 'enable':
            self.effects_processor.enable_filter(bool(value))

    def get_fx_state(self) -> Dict:
        """Get FX state."""
        return self.effects_processor.get_state()

    # Loop control
    def loop_control(self, parameter: str, value: float):
        """Control loop parameter."""
        if parameter == 'enable':
            enabled = bool(value)
            self.deck_a.set_loop_enabled(enabled)
            print(f"[Loop Control] Loop {'enabled' if enabled else 'disabled'}")
        elif parameter == 'length':
            # value is in beats
            self.deck_a.set_loop_length(value)
            print(f"[Loop Control] Loop length: {value} beats")
        elif parameter == 'position':
            # value is normalized 0-1
            self.deck_a.set_loop_position(value)
            print(f"[Loop Control] Loop position: {value*100:.0f}%")

    def loop_action(self, action: str, parameters: Dict):
        """Handle loop actions."""
        if action == 'set_in':
            # Set loop IN point at current playback position
            position = self.deck_a.get_playback_position()
            self.deck_a.set_loop_in_point(position)
            print(f"[Loop Action] Set IN point at {position:.2f}s")
        elif action == 'set_out':
            # Set loop OUT point at current playback position
            position = self.deck_a.get_playback_position()
            self.deck_a.set_loop_out_point(position)
            print(f"[Loop Action] Set OUT point at {position:.2f}s")
        elif action == 'roll':
            # Toggle loop roll (temporary loop)
            active = parameters.get('active', False)
            self.deck_a.set_loop_roll(active)
            print(f"[Loop Action] Loop roll {'activated' if active else 'deactivated'}")

    def get_loop_state(self) -> Dict:
        """Get loop state."""
        return {
            'loop_enabled': getattr(self.deck_a, 'loop_enabled', False),
            'loop_length': getattr(self.deck_a, 'loop_length_beats', 4.0),
            'loop_in_point': getattr(self.deck_a, 'loop_in_point', None),
            'loop_out_point': getattr(self.deck_a, 'loop_out_point', None),
            'loop_position': getattr(self.deck_a, 'loop_position', 0.0),
            'is_rolling': getattr(self.deck_a, 'is_rolling', False),
            'bpm': getattr(self.deck_a, 'bpm', 120.0)
        }

    def stop(self):
        """Stop engine."""
        self.stop_processing()
        print("[SoundDeviceAudioEngine] Stopped")


# Test if run directly
if __name__ == "__main__":
    print("=" * 60)
    print("SOUNDDEVICE AUDIO ENGINE TEST")
    print("=" * 60)

    # Create engine
    engine = SoundDeviceAudioEngine()

    # Start
    engine.start_processing()

    print("\n[Test] Engine started")
    print("[Test] Press Ctrl+C to stop")

    try:
        # Keep running
        while True:
            time.sleep(1)
            status_a = engine.deck_a.get_status()
            status_b = engine.deck_b.get_status()
            print(f"\r[Test] Deck A: {status_a['playing']}, Deck B: {status_b['playing']}", end='')

    except KeyboardInterrupt:
        print("\n[Test] Stopping...")
        engine.stop()
        print("[Test] Stopped")
