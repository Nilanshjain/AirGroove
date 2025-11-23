#!/usr/bin/env python3
"""
Test Audio Generator for AirGroove DJ
Generates synthetic audio clips optimized for testing DJ effects.
"""

import numpy as np
import soundfile as sf
from pathlib import Path
import os


class TestAudioGenerator:
    """Generate test audio files for DJ effect testing."""

    def __init__(self, output_dir='audio/test_samples', sample_rate=44100):
        """
        Initialize the test audio generator.

        Args:
            output_dir: Directory to save generated audio files
            sample_rate: Audio sample rate in Hz
        """
        self.output_dir = Path(output_dir)
        self.sample_rate = sample_rate

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[TestAudio] Initialized generator")
        print(f"[TestAudio] Output directory: {self.output_dir.absolute()}")
        print(f"[TestAudio] Sample rate: {self.sample_rate} Hz")

    def generate_all_test_tracks(self):
        """Generate all test tracks."""
        print("\n[TestAudio] Generating all test tracks...")

        tracks = [
            self.generate_house_beat(),
            self.generate_frequency_sweep(),
            self.generate_pink_noise(),
            self.generate_melody_loop()
        ]

        print(f"\n[TestAudio] [OK] Generated {len(tracks)} test tracks")
        print(f"[TestAudio] Saved to: {self.output_dir.absolute()}")

        return tracks

    def generate_house_beat(self):
        """
        Generate a 120 BPM house beat with kick and hi-hats.
        Perfect for testing loops and sync.

        Returns:
            Path to generated file
        """
        print("[TestAudio] Generating 120 BPM house beat...")

        bpm = 120
        duration = 30  # seconds
        beats_per_second = bpm / 60.0
        samples_per_beat = int(self.sample_rate / beats_per_second)
        total_samples = int(duration * self.sample_rate)

        # Create stereo audio
        audio = np.zeros((total_samples, 2), dtype=np.float32)

        # Generate kick drum (every beat)
        for beat in range(int(duration * beats_per_second)):
            start = beat * samples_per_beat
            kick_duration = int(self.sample_rate * 0.15)  # 150ms kick

            if start + kick_duration < total_samples:
                # Kick: 60Hz sine with exponential decay
                t = np.linspace(0, 0.15, kick_duration)
                kick = np.sin(2 * np.pi * 60 * t) * np.exp(-20 * t)
                audio[start:start+kick_duration, 0] += kick * 0.8
                audio[start:start+kick_duration, 1] += kick * 0.8

        # Generate hi-hats (8th notes)
        for eighth in range(int(duration * beats_per_second * 2)):
            start = eighth * (samples_per_beat // 2)
            hihat_duration = int(self.sample_rate * 0.05)  # 50ms hi-hat

            if start + hihat_duration < total_samples:
                # Hi-hat: filtered white noise with quick decay
                t = np.linspace(0, 0.05, hihat_duration)
                hihat = np.random.randn(hihat_duration) * np.exp(-100 * t)
                audio[start:start+hihat_duration, 0] += hihat * 0.3
                audio[start:start+hihat_duration, 1] += hihat * 0.3

        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.9

        # Save
        output_file = self.output_dir / "test_120bpm_house.wav"
        sf.write(str(output_file), audio, self.sample_rate)

        print(f"[TestAudio] [OK] Created: {output_file.name} (30s, 120 BPM)")
        return output_file

    def generate_frequency_sweep(self):
        """
        Generate a frequency sweep from 20Hz to 20kHz.
        Perfect for testing filters.

        Returns:
            Path to generated file
        """
        print("[TestAudio] Generating frequency sweep...")

        duration = 20  # seconds
        start_freq = 20  # Hz
        end_freq = 20000  # Hz

        # Linear sweep in log scale (sounds more natural)
        t = np.linspace(0, duration, int(duration * self.sample_rate))

        # Logarithmic frequency sweep
        frequencies = np.logspace(np.log10(start_freq), np.log10(end_freq), len(t))
        phase = np.cumsum(2 * np.pi * frequencies / self.sample_rate)

        # Generate sweep
        sweep = np.sin(phase).astype(np.float32) * 0.7

        # Apply fade in/out to avoid clicks
        fade_samples = int(self.sample_rate * 0.1)  # 100ms fade
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)

        sweep[:fade_samples] *= fade_in
        sweep[-fade_samples:] *= fade_out

        # Convert to stereo
        audio = np.column_stack([sweep, sweep])

        # Save
        output_file = self.output_dir / "test_frequency_sweep.wav"
        sf.write(str(output_file), audio, self.sample_rate)

        print(f"[TestAudio] [OK] Created: {output_file.name} (20s, 20Hz-20kHz)")
        return output_file

    def generate_pink_noise(self):
        """
        Generate pink noise (equal energy per octave).
        Perfect for testing reverb and delay.

        Returns:
            Path to generated file
        """
        print("[TestAudio] Generating pink noise...")

        duration = 15  # seconds
        samples = int(duration * self.sample_rate)

        # Generate white noise
        white = np.random.randn(samples).astype(np.float32)

        # Convert white noise to pink noise using Paul Kellett's algorithm
        # This is a simplified version - good enough for testing
        b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0
        pink = np.zeros(samples, dtype=np.float32)

        for i in range(samples):
            white_sample = white[i]
            b0 = 0.99886 * b0 + white_sample * 0.0555179
            b1 = 0.99332 * b1 + white_sample * 0.0750759
            b2 = 0.96900 * b2 + white_sample * 0.1538520
            b3 = 0.86650 * b3 + white_sample * 0.3104856
            b4 = 0.55000 * b4 + white_sample * 0.5329522
            b5 = -0.7616 * b5 - white_sample * 0.0168980
            pink[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white_sample * 0.5362) * 0.11
            b6 = white_sample * 0.115926

        # Normalize
        pink = pink / np.max(np.abs(pink)) * 0.7

        # Convert to stereo
        audio = np.column_stack([pink, pink])

        # Save
        output_file = self.output_dir / "test_pink_noise.wav"
        sf.write(str(output_file), audio, self.sample_rate)

        print(f"[TestAudio] [OK] Created: {output_file.name} (15s, pink noise)")
        return output_file

    def generate_melody_loop(self):
        """
        Generate a simple melodic loop at 128 BPM.
        Perfect for musical testing.

        Returns:
            Path to generated file
        """
        print("[TestAudio] Generating melody loop...")

        bpm = 128
        beats_per_bar = 4
        num_bars = 8
        duration = (num_bars * beats_per_bar) / (bpm / 60.0)

        # Simple chord progression: C - Am - F - G (repeated 2x)
        # Using MIDI note numbers
        chords = [
            [60, 64, 67],  # C major (C, E, G)
            [69, 72, 76],  # A minor (A, C, E) - higher octave
            [65, 69, 72],  # F major (F, A, C) - higher octave
            [67, 71, 74],  # G major (G, B, D) - higher octave
        ] * 2  # Repeat progression

        total_samples = int(duration * self.sample_rate)
        audio = np.zeros(total_samples, dtype=np.float32)

        samples_per_bar = int((beats_per_bar / (bpm / 60.0)) * self.sample_rate)

        # Generate each chord
        for bar_idx, chord in enumerate(chords):
            start_sample = bar_idx * samples_per_bar
            bar_duration = samples_per_bar / self.sample_rate

            # Create chord sound (simple sine waves)
            t = np.linspace(0, bar_duration, samples_per_bar)

            # ADSR envelope for chord
            attack = int(samples_per_bar * 0.05)
            decay = int(samples_per_bar * 0.1)
            sustain_level = 0.7
            release = int(samples_per_bar * 0.2)

            envelope = np.ones(samples_per_bar)
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[attack:attack+decay] = np.linspace(1, sustain_level, decay)
            envelope[-release:] = np.linspace(sustain_level, 0, release)

            # Add each note in the chord
            chord_sound = np.zeros(samples_per_bar)
            for midi_note in chord:
                freq = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))  # A4 = 440Hz
                note = np.sin(2 * np.pi * freq * t) * envelope
                chord_sound += note

            # Normalize chord and add to audio
            chord_sound = chord_sound / len(chord) * 0.6

            if start_sample + samples_per_bar <= total_samples:
                audio[start_sample:start_sample+samples_per_bar] += chord_sound

        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.8

        # Convert to stereo
        audio_stereo = np.column_stack([audio, audio])

        # Save
        output_file = self.output_dir / "test_128bpm_melody.wav"
        sf.write(str(output_file), audio_stereo, self.sample_rate)

        print(f"[TestAudio] [OK] Created: {output_file.name} (8 bars, 128 BPM)")
        return output_file

    def check_existing_tracks(self):
        """
        Check which test tracks already exist.

        Returns:
            List of existing track paths
        """
        expected_files = [
            "test_120bpm_house.wav",
            "test_frequency_sweep.wav",
            "test_pink_noise.wav",
            "test_128bpm_melody.wav"
        ]

        existing = []
        for filename in expected_files:
            filepath = self.output_dir / filename
            if filepath.exists():
                existing.append(filepath)

        return existing


def generate_test_audio(force_regenerate=False):
    """
    Generate test audio files if they don't exist.

    Args:
        force_regenerate: If True, regenerate all files even if they exist

    Returns:
        List of paths to test audio files
    """
    generator = TestAudioGenerator()

    # Check existing files
    existing = generator.check_existing_tracks()

    if len(existing) == 4 and not force_regenerate:
        print("[TestAudio] All test tracks already exist")
        print("[TestAudio] Use force_regenerate=True to regenerate")
        return existing

    # Generate missing or all tracks
    if force_regenerate or len(existing) < 4:
        tracks = generator.generate_all_test_tracks()
        return tracks

    return existing


if __name__ == "__main__":
    # Generate test audio when run directly
    print("=" * 60)
    print("AIRGROOVE TEST AUDIO GENERATOR")
    print("=" * 60)

    tracks = generate_test_audio(force_regenerate=True)

    print("\n" + "=" * 60)
    print("Test audio generation complete!")
    print(f"Generated {len(tracks)} tracks")
    print("=" * 60)
