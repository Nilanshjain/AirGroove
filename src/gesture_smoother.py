#!/usr/bin/env python3
"""
Multi-frame gesture smoothing and validation for ultra-stable gesture recognition.
Prevents false triggers and provides confidence-based gesture filtering.
"""

from collections import deque
from typing import Dict, List, Optional
import time

class GestureSmoother:
    """Smooths gesture detection across multiple frames for stability."""

    def __init__(self, buffer_size: int = 10, confidence_threshold: float = 0.7):
        """
        Initialize gesture smoother.

        Args:
            buffer_size: Number of frames to buffer for smoothing
            confidence_threshold: Minimum confidence for gesture acceptance
        """
        self.buffer_size = buffer_size
        self.confidence_threshold = confidence_threshold

        # Buffers for each hand
        self.left_gesture_buffer = deque(maxlen=buffer_size)
        self.right_gesture_buffer = deque(maxlen=buffer_size)
        self.left_confidence_buffer = deque(maxlen=buffer_size)
        self.right_confidence_buffer = deque(maxlen=buffer_size)

        # Current stable states
        self.stable_left_gesture = "none"
        self.stable_right_gesture = "none"
        self.stable_interaction_state = "browsing"

        # Transition detection
        self.last_stable_state = "browsing"
        self.state_change_time = time.time()
        self.min_state_duration = 0.3  # Minimum time in state before allowing change

    def smooth_gestures(self, gesture_state: Dict) -> Dict:
        """
        Apply smoothing to gesture detection results.

        Args:
            gesture_state: Raw gesture state from PrecisionGestureRecognizer

        Returns:
            Smoothed gesture state with stable detections
        """
        # Extract current frame data
        left_gesture = gesture_state['left_hand']['gesture']
        right_gesture = gesture_state['right_hand']['gesture']
        left_confidence = gesture_state['left_hand']['confidence']
        right_confidence = gesture_state['right_hand']['confidence']

        # Add to buffers
        self.left_gesture_buffer.append(left_gesture)
        self.right_gesture_buffer.append(right_gesture)
        self.left_confidence_buffer.append(left_confidence)
        self.right_confidence_buffer.append(right_confidence)

        # Calculate stable gestures
        stable_left = self._get_stable_gesture(
            self.left_gesture_buffer,
            self.left_confidence_buffer
        )
        stable_right = self._get_stable_gesture(
            self.right_gesture_buffer,
            self.right_confidence_buffer
        )

        # Update stable states if they've changed
        if stable_left != self.stable_left_gesture:
            self.stable_left_gesture = stable_left

        if stable_right != self.stable_right_gesture:
            self.stable_right_gesture = stable_right

        # Determine stable interaction state
        stable_interaction = self._determine_stable_interaction_state(
            stable_left, stable_right
        )

        # Apply state change timing rules
        current_time = time.time()
        if stable_interaction != self.last_stable_state:
            if current_time - self.state_change_time > self.min_state_duration:
                self.stable_interaction_state = stable_interaction
                self.last_stable_state = stable_interaction
                self.state_change_time = current_time
        else:
            self.stable_interaction_state = stable_interaction

        # Build smoothed state
        smoothed_state = gesture_state.copy()
        smoothed_state['left_hand']['gesture'] = stable_left
        smoothed_state['right_hand']['gesture'] = stable_right
        smoothed_state['interaction_state'] = self.stable_interaction_state

        # Add smoothing metadata
        smoothed_state['smoothing'] = {
            'left_stability': self._calculate_stability(self.left_gesture_buffer),
            'right_stability': self._calculate_stability(self.right_gesture_buffer),
            'state_confidence': self._calculate_state_confidence(stable_left, stable_right),
            'frames_in_buffer': len(self.left_gesture_buffer)
        }

        return smoothed_state

    def _get_stable_gesture(self, gesture_buffer: deque,
                           confidence_buffer: deque) -> str:
        """Get the most stable gesture from the buffer."""
        if not gesture_buffer:
            return "none"

        # Count occurrences of each gesture
        gesture_counts = {}
        total_confidence = {}

        for i, gesture in enumerate(gesture_buffer):
            confidence = confidence_buffer[i] if i < len(confidence_buffer) else 0.0

            # Only consider gestures above confidence threshold
            if confidence >= self.confidence_threshold:
                if gesture not in gesture_counts:
                    gesture_counts[gesture] = 0
                    total_confidence[gesture] = 0.0

                gesture_counts[gesture] += 1
                total_confidence[gesture] += confidence

        if not gesture_counts:
            return "none"

        # Find gesture with highest count and confidence
        best_gesture = None
        best_score = 0.0

        for gesture, count in gesture_counts.items():
            avg_confidence = total_confidence[gesture] / count
            # Score combines count and average confidence
            score = count * avg_confidence

            if score > best_score:
                best_score = score
                best_gesture = gesture

        # Require minimum agreement (60% of frames)
        required_count = max(1, int(len(gesture_buffer) * 0.6))
        if gesture_counts.get(best_gesture, 0) >= required_count:
            return best_gesture
        else:
            return "none"

    def _determine_stable_interaction_state(self, left_gesture: str,
                                          right_gesture: str) -> str:
        """Determine interaction state from stable gestures."""
        # Both hands open = browsing mode
        if left_gesture == "open_palm" and right_gesture == "open_palm":
            return "browsing"

        # One hand fist = mode selection
        if left_gesture == "closed_fist" and right_gesture == "open_palm":
            return "selecting_with_left"
        elif right_gesture == "closed_fist" and left_gesture == "open_palm":
            return "selecting_with_right"

        # One fist + special gesture = audio control
        control_gestures = ["pinch", "pointer", "two_fingers"]

        if left_gesture == "closed_fist" and right_gesture in control_gestures:
            return f"controlling_with_right_{right_gesture}"
        elif right_gesture == "closed_fist" and left_gesture in control_gestures:
            return f"controlling_with_left_{left_gesture}"

        # Default to browsing if unclear
        return "browsing"

    def _calculate_stability(self, gesture_buffer: deque) -> float:
        """Calculate stability score for a gesture buffer."""
        if not gesture_buffer:
            return 0.0

        # Count most common gesture
        gesture_counts = {}
        for gesture in gesture_buffer:
            gesture_counts[gesture] = gesture_counts.get(gesture, 0) + 1

        if not gesture_counts:
            return 0.0

        max_count = max(gesture_counts.values())
        stability = max_count / len(gesture_buffer)
        return stability

    def _calculate_state_confidence(self, left_gesture: str, right_gesture: str) -> float:
        """Calculate confidence in the current interaction state."""
        # Higher confidence for clear, intentional states
        if left_gesture == "open_palm" and right_gesture == "open_palm":
            return 0.9  # Clear browsing state

        if (left_gesture == "closed_fist" and right_gesture == "open_palm") or \
           (right_gesture == "closed_fist" and left_gesture == "open_palm"):
            return 0.85  # Clear selection state

        control_gestures = ["pinch", "pointer", "two_fingers"]
        if (left_gesture == "closed_fist" and right_gesture in control_gestures) or \
           (right_gesture == "closed_fist" and left_gesture in control_gestures):
            return 0.8  # Clear control state

        return 0.5  # Uncertain state

    def reset(self):
        """Reset all buffers and states."""
        self.left_gesture_buffer.clear()
        self.right_gesture_buffer.clear()
        self.left_confidence_buffer.clear()
        self.right_confidence_buffer.clear()

        self.stable_left_gesture = "none"
        self.stable_right_gesture = "none"
        self.stable_interaction_state = "browsing"
        self.last_stable_state = "browsing"
        self.state_change_time = time.time()

    def get_debug_info(self) -> Dict:
        """Get debug information about current smoothing state."""
        return {
            'buffer_sizes': {
                'left_gestures': len(self.left_gesture_buffer),
                'right_gestures': len(self.right_gesture_buffer),
                'left_confidences': len(self.left_confidence_buffer),
                'right_confidences': len(self.right_confidence_buffer)
            },
            'current_buffers': {
                'left_gestures': list(self.left_gesture_buffer),
                'right_gestures': list(self.right_gesture_buffer),
                'left_confidences': list(self.left_confidence_buffer),
                'right_confidences': list(self.right_confidence_buffer)
            },
            'stable_states': {
                'left_gesture': self.stable_left_gesture,
                'right_gesture': self.stable_right_gesture,
                'interaction_state': self.stable_interaction_state
            },
            'timing': {
                'last_state_change': self.state_change_time,
                'min_state_duration': self.min_state_duration
            }
        }