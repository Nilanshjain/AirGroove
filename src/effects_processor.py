#!/usr/bin/env python3
"""
Audio Effects Processor for AirGroove DJ
Real-time DSP effects using scipy and pedalboard.
"""

import numpy as np
from scipy import signal
from typing import Dict, Optional
import threading


class EffectsProcessor:
    """
    Real-time audio effects processor.
    Handles filters, reverb, delay, and other DJ effects.
    """

    def __init__(self, sample_rate=44100):
        """
        Initialize the effects processor.

        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate

        # Filter state (target values)
        self.filter_type = 'lowpass'  # lowpass, highpass, bandpass
        self.filter_cutoff = 1000.0  # Hz
        self.filter_resonance = 1.0  # Q factor (1.0 = no resonance)
        self.filter_enabled = False

        # Smoothed parameters (actual values used in processing)
        self._smooth_cutoff = 1000.0
        self._smooth_resonance = 1.0
        self._smooth_wet_dry = 0.5

        # Wet/dry mix (0.0 = dry, 1.0 = wet)
        self.wet_dry_mix = 0.5

        # Double-buffered filter coefficients
        self._filter_b = None
        self._filter_a = None
        self._filter_b_next = None
        self._filter_a_next = None
        self._coefficients_ready = False

        # Filter state for continuous processing
        self._filter_zi_left = None
        self._filter_zi_right = None

        # Thread safety
        self.lock = threading.Lock()
        self.coeff_lock = threading.Lock()

        print("[EffectsProcessor] Initialized")
        print(f"[EffectsProcessor] Sample rate: {sample_rate} Hz")

    def set_filter_type(self, filter_type: str):
        """
        Set the filter type.

        Args:
            filter_type: 'lowpass', 'highpass', or 'bandpass'
        """
        with self.lock:
            if filter_type in ['lowpass', 'highpass', 'bandpass']:
                self.filter_type = filter_type
                self._update_filter_coefficients()
                print(f"[EffectsProcessor] Filter type: {filter_type}")

    def set_filter_cutoff(self, cutoff_hz: float):
        """
        Set the filter cutoff frequency.

        Args:
            cutoff_hz: Cutoff frequency in Hz (20-20000)
        """
        with self.lock:
            self.filter_cutoff = np.clip(cutoff_hz, 20.0, 20000.0)
            self._update_filter_coefficients()

    def set_filter_resonance(self, resonance: float):
        """
        Set the filter resonance (Q factor).

        Args:
            resonance: Q factor (0.5-10.0)
        """
        with self.lock:
            self.filter_resonance = np.clip(resonance, 0.5, 10.0)
            self._update_filter_coefficients()

    def set_wet_dry_mix(self, mix: float):
        """
        Set the wet/dry mix.

        Args:
            mix: Mix level (0.0 = dry, 1.0 = wet)
        """
        with self.lock:
            self.wet_dry_mix = np.clip(mix, 0.0, 1.0)

    def enable_filter(self, enabled: bool = True):
        """
        Enable or disable the filter.

        Args:
            enabled: True to enable, False to disable
        """
        with self.lock:
            self.filter_enabled = enabled
            if enabled:
                self._update_filter_coefficients()
                print(f"[EffectsProcessor] Filter enabled: {self.filter_type} @ {self.filter_cutoff:.0f}Hz")
            else:
                print("[EffectsProcessor] Filter disabled")

    def _update_filter_coefficients(self):
        """
        Update filter coefficients based on current settings.
        Uses Butterworth filter design with double-buffering for thread safety.
        """
        try:
            # Normalize cutoff frequency (0-1, where 1 is Nyquist)
            nyquist = self.sample_rate / 2.0
            normalized_cutoff = self.filter_cutoff / nyquist

            # Ensure cutoff is in valid range
            normalized_cutoff = np.clip(normalized_cutoff, 0.001, 0.999)

            # Design filter based on type - compute to "next" buffer
            if self.filter_type == 'lowpass':
                b_new, a_new = signal.butter(
                    N=2,  # 2nd order filter
                    Wn=normalized_cutoff,
                    btype='low',
                    analog=False
                )
            elif self.filter_type == 'highpass':
                b_new, a_new = signal.butter(
                    N=2,
                    Wn=normalized_cutoff,
                    btype='high',
                    analog=False
                )
            elif self.filter_type == 'bandpass':
                # For bandpass, use cutoff as center frequency
                # Bandwidth is controlled by resonance
                bandwidth = self.filter_cutoff / self.filter_resonance
                low_cutoff = max(20.0, self.filter_cutoff - bandwidth / 2) / nyquist
                high_cutoff = min(nyquist * 0.99, self.filter_cutoff + bandwidth / 2) / nyquist

                b_new, a_new = signal.butter(
                    N=2,
                    Wn=[low_cutoff, high_cutoff],
                    btype='band',
                    analog=False
                )

            # Store in "next" buffer (thread-safe)
            with self.coeff_lock:
                self._filter_b_next = b_new
                self._filter_a_next = a_new
                self._coefficients_ready = True

        except Exception as e:
            print(f"[EffectsProcessor] Error updating filter: {e}")
            with self.coeff_lock:
                self._filter_b_next = None
                self._filter_a_next = None
                self._coefficients_ready = False

    def process_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Process audio with current effects.
        Uses double-buffering and parameter smoothing for click-free changes.

        Args:
            audio: Input audio array (stereo, shape: [samples, 2])

        Returns:
            Processed audio array
        """
        # Quick bypass if filter is disabled
        if not self.filter_enabled:
            return audio

        try:
            # Swap coefficients if new ones are ready (thread-safe)
            with self.coeff_lock:
                if self._coefficients_ready and self._filter_b_next is not None:
                    self._filter_b = self._filter_b_next
                    self._filter_a = self._filter_a_next
                    self._coefficients_ready = False

                    # Re-initialize filter state to prevent clicks
                    if self._filter_b is not None:
                        self._filter_zi_left = signal.lfilter_zi(self._filter_b, self._filter_a)
                        self._filter_zi_right = self._filter_zi_left.copy()

            # Bypass if no coefficients available yet
            if self._filter_b is None:
                return audio

            # Apply parameter smoothing (EMA) for click-free changes
            # Smoothing factor: 95% old, 5% new (very smooth)
            self._smooth_cutoff = self._smooth_cutoff * 0.95 + self.filter_cutoff * 0.05
            self._smooth_resonance = self._smooth_resonance * 0.95 + self.filter_resonance * 0.05
            self._smooth_wet_dry = self._smooth_wet_dry * 0.95 + self.wet_dry_mix * 0.05

            with self.lock:
                # Make a copy to avoid modifying input
                processed = audio.copy()

                # Apply filter to each channel
                if len(processed.shape) == 2 and processed.shape[1] == 2:
                    # Stereo
                    left_channel = processed[:, 0]
                    right_channel = processed[:, 1]

                    # Apply filter with state continuity
                    filtered_left, self._filter_zi_left = signal.lfilter(
                        self._filter_b, self._filter_a, left_channel,
                        zi=self._filter_zi_left
                    )
                    filtered_right, self._filter_zi_right = signal.lfilter(
                        self._filter_b, self._filter_a, right_channel,
                        zi=self._filter_zi_right
                    )

                    # Apply smoothed wet/dry mix
                    processed[:, 0] = (1 - self._smooth_wet_dry) * left_channel + self._smooth_wet_dry * filtered_left
                    processed[:, 1] = (1 - self._smooth_wet_dry) * right_channel + self._smooth_wet_dry * filtered_right

                elif len(processed.shape) == 1:
                    # Mono
                    filtered, self._filter_zi_left = signal.lfilter(
                        self._filter_b, self._filter_a, processed,
                        zi=self._filter_zi_left
                    )
                    processed = (1 - self._smooth_wet_dry) * processed + self._smooth_wet_dry * filtered

                return processed

        except Exception as e:
            print(f"[EffectsProcessor] Error processing audio: {e}")
            return audio

    def get_state(self) -> Dict:
        """
        Get current effects state.

        Returns:
            Dictionary with current effect settings
        """
        with self.lock:
            return {
                'filter_type': self.filter_type,
                'filter_cutoff': self.filter_cutoff,
                'filter_resonance': self.filter_resonance,
                'filter_enabled': self.filter_enabled,
                'wet_dry_mix': self.wet_dry_mix
            }

    def reset(self):
        """Reset all effects to default state."""
        with self.lock:
            self.filter_type = 'lowpass'
            self.filter_cutoff = 1000.0
            self.filter_resonance = 1.0
            self.filter_enabled = False
            self.wet_dry_mix = 0.5
            self._filter_b = None
            self._filter_a = None
            print("[EffectsProcessor] Reset to default state")


# Test the effects processor
if __name__ == "__main__":
    print("=" * 60)
    print("EFFECTS PROCESSOR TEST")
    print("=" * 60)

    # Create processor
    processor = EffectsProcessor(sample_rate=44100)

    # Generate test tone (440Hz sine wave, 1 second)
    duration = 1.0
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    test_audio = np.sin(2 * np.pi * 440 * t)

    # Convert to stereo
    test_audio_stereo = np.column_stack([test_audio, test_audio]).astype(np.float32)

    print("\n[Test] Generated 440Hz sine wave (1 second)")
    print(f"[Test] Audio shape: {test_audio_stereo.shape}")

    # Test lowpass filter
    print("\n[Test] Testing lowpass filter @ 500Hz...")
    processor.set_filter_type('lowpass')
    processor.set_filter_cutoff(500.0)
    processor.set_wet_dry_mix(1.0)  # 100% wet
    processor.enable_filter(True)

    filtered = processor.process_audio(test_audio_stereo)
    print(f"[Test] Filtered audio shape: {filtered.shape}")
    print(f"[Test] Filter state: {processor.get_state()}")

    # Test highpass filter
    print("\n[Test] Testing highpass filter @ 2000Hz...")
    processor.set_filter_type('highpass')
    processor.set_filter_cutoff(2000.0)

    filtered = processor.process_audio(test_audio_stereo)
    print(f"[Test] Filtered audio shape: {filtered.shape}")

    # Test bandpass filter
    print("\n[Test] Testing bandpass filter @ 440Hz...")
    processor.set_filter_type('bandpass')
    processor.set_filter_cutoff(440.0)
    processor.set_filter_resonance(5.0)

    filtered = processor.process_audio(test_audio_stereo)
    print(f"[Test] Filtered audio shape: {filtered.shape}")

    print("\n" + "=" * 60)
    print("Effects processor test complete!")
    print("=" * 60)
