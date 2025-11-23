#!/usr/bin/env python3
"""
Test script for FX mode functionality.
Loads an audio file and tests filter effects.
"""

import sys
import os
import time
import glob

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sounddevice_audio_engine import SoundDeviceAudioEngine
from web_audio_engine import WebAudioEngine

def find_audio_file():
    """Find an audio file in the audio folder or project."""
    # Check common audio locations
    audio_dirs = [
        'audio',
        'Audio',
        'tracks',
        'Tracks',
        'music',
        'Music',
        '.'
    ]

    audio_extensions = ['*.mp3', '*.wav', '*.flac', '*.ogg', '*.m4a']

    for audio_dir in audio_dirs:
        if os.path.exists(audio_dir):
            for ext in audio_extensions:
                files = glob.glob(os.path.join(audio_dir, ext))
                if files:
                    return files[0]

    return None

def test_fx_mode():
    """Test FX mode with audio file."""
    print("=" * 60)
    print("FX MODE TEST")
    print("=" * 60)

    # Find audio file
    audio_file = find_audio_file()
    if not audio_file:
        print("[ERROR] No audio file found!")
        print("[INFO] Please place an audio file (mp3, wav, etc.) in the 'audio' folder")
        return False

    print(f"[INFO] Using audio file: {audio_file}")

    # Create audio engine
    print("\n[TEST] Creating audio engine...")
    engine = WebAudioEngine()

    # Start processing
    print("[TEST] Starting audio processing...")
    engine.start_processing()
    time.sleep(0.5)

    # Load track into Deck A
    print(f"\n[TEST] Loading track into Deck A: {os.path.basename(audio_file)}")
    engine.load_track('a', audio_file)

    # Wait for track to load with polling
    print("[TEST] Waiting for track to load...")
    max_wait_time = 10  # seconds
    poll_interval = 0.5  # seconds
    elapsed = 0

    while elapsed < max_wait_time:
        deck_a_status = engine.sd_engine.deck_a.get_status()
        if deck_a_status['loaded']:
            break

        if deck_a_status['loading']:
            progress = deck_a_status.get('load_progress', 0.0) * 100
            print(f"  Loading... {progress:.0f}%")

        time.sleep(poll_interval)
        elapsed += poll_interval

    # Final check if loaded
    deck_a_status = engine.sd_engine.deck_a.get_status()
    if not deck_a_status['loaded']:
        print("[ERROR] Track failed to load after {max_wait_time}s timeout!")
        engine.stop_processing()
        return False

    print(f"[SUCCESS] Track loaded: {deck_a_status['track_name']}")
    print(f"[INFO] Duration: {deck_a_status['duration']:.1f}s, BPM: {deck_a_status['bpm']:.1f}")

    # Start playback
    print("\n[TEST] Starting playback...")
    engine.play_deck('a')
    time.sleep(1)

    # Set mode to FX
    print("\n[TEST] Switching to FX mode...")
    engine.set_mode('fx')
    time.sleep(0.5)

    # Test 1: Enable filter
    print("\n[TEST 1] Enabling lowpass filter...")
    engine.fx_control('enable', 1.0)
    time.sleep(2)

    fx_state = engine.sd_engine.get_fx_state()
    print(f"[INFO] Filter enabled: {fx_state['filter_enabled']}")
    print(f"[INFO] Filter type: {fx_state['filter_type']}")
    print(f"[INFO] Cutoff: {fx_state['filter_cutoff']:.1f} Hz")

    # Test 2: Sweep cutoff frequency (lowpass)
    print("\n[TEST 2] Sweeping cutoff frequency (500Hz -> 5000Hz)...")
    for cutoff in [500, 1000, 2000, 3000, 4000, 5000]:
        print(f"  -> Cutoff: {cutoff} Hz")
        engine.fx_control('cutoff', cutoff)
        time.sleep(1.5)

    # Test 3: Change to highpass filter
    print("\n[TEST 3] Switching to highpass filter...")
    engine.fx_control('filter_type', 'highpass')
    engine.fx_control('cutoff', 1000)
    time.sleep(2)

    fx_state = engine.sd_engine.get_fx_state()
    print(f"[INFO] Filter type: {fx_state['filter_type']}")

    # Test 4: Sweep cutoff frequency (highpass)
    print("\n[TEST 4] Sweeping cutoff frequency (5000Hz -> 500Hz)...")
    for cutoff in [5000, 4000, 3000, 2000, 1000, 500]:
        print(f"  -> Cutoff: {cutoff} Hz")
        engine.fx_control('cutoff', cutoff)
        time.sleep(1.5)

    # Test 5: Change to bandpass filter
    print("\n[TEST 5] Switching to bandpass filter...")
    engine.fx_control('filter_type', 'bandpass')
    engine.fx_control('cutoff', 2000)
    time.sleep(2)

    # Test 6: Adjust resonance
    print("\n[TEST 6] Testing resonance (Q factor)...")
    for resonance in [1.0, 2.0, 5.0, 10.0, 5.0, 1.0]:
        print(f"  -> Resonance: {resonance}")
        engine.fx_control('resonance', resonance)
        time.sleep(1.5)

    # Test 7: Wet/Dry mix
    print("\n[TEST 7] Testing wet/dry mix...")
    for wet_dry in [0.0, 0.25, 0.5, 0.75, 1.0, 0.5]:
        print(f"  -> Wet/Dry: {wet_dry * 100:.0f}%")
        engine.fx_control('wet_dry', wet_dry)
        time.sleep(1.5)

    # Test 8: Disable filter
    print("\n[TEST 8] Disabling filter...")
    engine.fx_control('enable', 0.0)
    time.sleep(2)

    fx_state = engine.sd_engine.get_fx_state()
    print(f"[INFO] Filter enabled: {fx_state['filter_enabled']}")

    # Stop playback
    print("\n[TEST] Stopping playback...")
    engine.pause_deck('a')
    time.sleep(0.5)

    # Stop engine
    print("[TEST] Stopping audio engine...")
    engine.stop_processing()

    print("\n" + "=" * 60)
    print("FX MODE TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)

    return True

if __name__ == "__main__":
    print("\n[INFO] Starting FX Mode Test...")
    print("[INFO] Press Ctrl+C to stop at any time\n")

    try:
        success = test_fx_mode()

        if success:
            print("\n[SUCCESS] All tests passed!")
            sys.exit(0)
        else:
            print("\n[FAILED] Tests failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(0)

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
