#!/usr/bin/env python3
"""
Test Mode Configuration for AirGroove DJ
Auto-loads test tracks and configures optimal settings for testing.
"""

from pathlib import Path
from test_audio_generator import generate_test_audio


class TestMode:
    """Test mode configuration and utilities."""

    def __init__(self):
        """Initialize test mode."""
        self.test_tracks_dir = Path('audio/test_samples')
        self.test_tracks = []

        print("[TestMode] Initialized")

    def setup(self):
        """
        Set up test mode by ensuring test audio exists.

        Returns:
            List of test track paths
        """
        print("\n[TestMode] Setting up test environment...")

        # Generate test audio if needed
        self.test_tracks = generate_test_audio(force_regenerate=False)

        print(f"[TestMode] Found {len(self.test_tracks)} test tracks")
        for track in self.test_tracks:
            print(f"[TestMode]   - {track.name}")

        return self.test_tracks

    def get_deck_tracks(self):
        """
        Get recommended tracks for each deck.

        Returns:
            Tuple of (deck_a_track, deck_b_track)
        """
        if len(self.test_tracks) < 2:
            return None, None

        # Deck A: House beat (good for rhythm testing)
        deck_a = next((t for t in self.test_tracks if '120bpm_house' in t.name), None)

        # Deck B: Frequency sweep (good for filter testing)
        deck_b = next((t for t in self.test_tracks if 'frequency_sweep' in t.name), None)

        return deck_a, deck_b

    def get_instructions(self):
        """
        Get test mode instructions.

        Returns:
            List of instruction strings
        """
        return [
            "=== TEST MODE ACTIVE ===",
            "",
            "Deck A: 120 BPM House Beat (rhythm testing)",
            "Deck B: Frequency Sweep (filter testing)",
            "",
            "FX Mode Testing:",
            "1. Swipe RIGHT to enter FX mode",
            "2. Use POINTER gesture (Y axis) to select filter type:",
            "   - Top (Y < 0.3): Lowpass filter",
            "   - Middle (0.3-0.7): Highpass filter",
            "   - Bottom (Y > 0.7): Bandpass filter",
            "3. Use TWO FINGERS horizontal to adjust cutoff frequency",
            "4. Use TWO FINGERS vertical to adjust wet/dry mix",
            "5. Rotate palm to adjust resonance",
            "",
            "Keyboard Shortcuts:",
            "- SPACE: Play/Pause Deck A",
            "- O: Load Deck A",
            "- P: Load Deck B",
            "- Q: Quit",
            "",
            "Press any key to continue..."
        ]

    def print_instructions(self):
        """Print test mode instructions to console."""
        for line in self.get_instructions():
            print(line)


def enable_test_mode():
    """
    Enable test mode.

    Returns:
        TestMode instance
    """
    test_mode = TestMode()
    test_mode.setup()
    test_mode.print_instructions()
    return test_mode


if __name__ == "__main__":
    # Test the test mode setup
    print("Testing Test Mode...")
    test_mode = enable_test_mode()

    deck_a, deck_b = test_mode.get_deck_tracks()
    print(f"\nDeck A: {deck_a}")
    print(f"Deck B: {deck_b}")
