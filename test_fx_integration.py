#!/usr/bin/env python3
"""
Quick integration test for FX mode
Tests the sounddevice audio engine with effects processor
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from sounddevice_audio_engine import SoundDeviceAudioEngine
from web_audio_engine import WebAudioEngine

print("=" * 60)
print("FX MODE INTEGRATION TEST")
print("=" * 60)
print()

# Test 1: Create WebAudioEngine (which uses SoundDeviceAudioEngine)
print("[Test 1] Creating WebAudioEngine...")
try:
    audio_engine = WebAudioEngine()
    print("[Test 1] [OK] WebAudioEngine created successfully")
except Exception as e:
    print(f"[Test 1] [ERROR] {e}")
    sys.exit(1)

# Test 2: Start audio processing
print("\n[Test 2] Starting audio processing...")
try:
    audio_engine.start_processing()
    print("[Test 2] [OK] Audio processing started")
except Exception as e:
    print(f"[Test 2] [ERROR] {e}")
    sys.exit(1)

# Test 3: Load test tracks
print("\n[Test 3] Loading test tracks...")
try:
    test_track_a = "audio/test_samples/test_120bpm_house.wav"
    test_track_b = "audio/test_samples/test_frequency_sweep.wav"

    audio_engine.load_track('a', test_track_a)
    print(f"[Test 3] [OK] Deck A loaded: {test_track_a}")

    audio_engine.load_track('b', test_track_b)
    print(f"[Test 3] [OK] Deck B loaded: {test_track_b}")
except Exception as e:
    print(f"[Test 3] [ERROR] {e}")
    audio_engine.stop()
    sys.exit(1)

# Test 4: Test FX controls
print("\n[Test 4] Testing FX controls...")
try:
    # Set mode to FX
    audio_engine.set_mode('fx')
    print("[Test 4] [OK] Switched to FX mode")

    # Test filter type
    audio_engine.fx_control('filter_type', 'lowpass')
    print("[Test 4] [OK] Set filter type: lowpass")

    # Test cutoff frequency
    audio_engine.fx_control('cutoff', 1000.0)
    print("[Test 4] [OK] Set cutoff: 1000 Hz")

    # Test wet/dry mix
    audio_engine.fx_control('wet_dry', 0.7)
    print("[Test 4] [OK] Set wet/dry: 70%")

    # Enable filter
    audio_engine.fx_control('enable', 1.0)
    print("[Test 4] [OK] Filter enabled")

    # Get FX state
    fx_state = audio_engine.sd_engine.get_fx_state()
    print(f"[Test 4] FX State: {fx_state}")

except Exception as e:
    print(f"[Test 4] [ERROR] {e}")
    import traceback
    traceback.print_exc()
    audio_engine.stop()
    sys.exit(1)

# Test 5: Play audio
print("\n[Test 5] Playing audio with effects...")
try:
    audio_engine.play_deck('b')  # Play frequency sweep to hear filter
    print("[Test 5] [OK] Deck B playing")
    print("[Test 5] You should hear a frequency sweep with lowpass filter applied")
    print("[Test 5] Letting it play for 5 seconds...")
    time.sleep(5)
except Exception as e:
    print(f"[Test 5] [ERROR] {e}")
    audio_engine.stop()
    sys.exit(1)

# Test 6: Change filter parameters
print("\n[Test 6] Changing filter parameters...")
try:
    # Change to highpass
    audio_engine.fx_control('filter_type', 'highpass')
    audio_engine.fx_control('cutoff', 2000.0)
    print("[Test 6] [OK] Changed to highpass @ 2000Hz")
    print("[Test 6] Letting it play for 3 seconds...")
    time.sleep(3)
except Exception as e:
    print(f"[Test 6] [ERROR] {e}")

# Cleanup
print("\n[Cleanup] Stopping audio engine...")
try:
    audio_engine.stop()
    print("[Cleanup] [OK] Audio engine stopped")
except Exception as e:
    print(f"[Cleanup] [ERROR] {e}")

print("\n" + "=" * 60)
print("FX MODE INTEGRATION TEST COMPLETE")
print("=" * 60)
