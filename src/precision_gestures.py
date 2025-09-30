#!/usr/bin/env python3
"""
Ultra-precise gesture recognition using MediaPipe landmarks and geometric analysis.
No trained models - pure rule-based detection for maximum accuracy and customization.
"""

import cv2
import numpy as np
import mediapipe as mp
import time
import math
from typing import Dict, List, Optional, Tuple

class PrecisionGestureRecognizer:
    """Ultra-precise gesture recognition using geometric analysis of hand landmarks."""

    def __init__(self):
        """Initialize the precision gesture recognizer."""
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

        # Initialize MediaPipe Hands with optimized settings for better detection
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,  # Track both hands
            model_complexity=1,
            min_detection_confidence=0.7,  # Lowered for better single hand detection
            min_tracking_confidence=0.5    # Lowered for smoother tracking
        )

        # Gesture detection thresholds (fine-tuned for accuracy)
        self.PINCH_THRESHOLD = 0.04  # Distance for pinch detection
        self.FINGER_FOLD_THRESHOLD = 0.03  # How far below MCP to consider folded
        self.FINGER_EXTEND_THRESHOLD = 0.02  # How far above PIP to consider extended

        # Current hand states
        self.left_hand = None
        self.right_hand = None
        self.left_gesture = "none"
        self.right_gesture = "none"

        # Swipe detection
        self.swipe_history = {
            'left': {'positions': [], 'last_time': 0, 'last_swipe': None, 'swipe_time': 0},
            'right': {'positions': [], 'last_time': 0, 'last_swipe': None, 'swipe_time': 0}
        }
        self.SWIPE_THRESHOLD = 0.2  # Base threshold for swipe (good for single hand)
        self.SWIPE_TIME_WINDOW = 0.4  # Time window for swipe detection
        self.SWIPE_EVENT_DURATION = 0.3  # How long swipe event is active

        # Hand swap correction (toggle if hands appear reversed)
        self.SWAP_HANDS = False  # Set to True if hands appear reversed

        # Gesture timing for quick actions
        self.gesture_history = {
            'left': {'gesture': 'none', 'start_time': 0, 'duration': 0, 'last_quick_gesture': 0},
            'right': {'gesture': 'none', 'start_time': 0, 'duration': 0, 'last_quick_gesture': 0}
        }
        self.QUICK_GESTURE_THRESHOLD = 0.5  # seconds
        self.GESTURE_COOLDOWN = 0.3  # seconds between quick gestures

    def update_hands(self, frame) -> Dict:
        """Process frame and return hand states and gestures."""
        # Convert frame for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.hands.process(frame_rgb)
        frame_rgb.flags.writeable = True

        # Reset hand states
        self.left_hand = None
        self.right_hand = None
        self.left_gesture = "none"
        self.right_gesture = "none"

        if results.multi_hand_landmarks:
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Determine hand side
                hand_side = "unknown"
                if i < len(results.multi_handedness):
                    label = results.multi_handedness[i].classification[0].label

                    if self.SWAP_HANDS:
                        # Swap: MediaPipe's "Left" is user's right hand (camera perspective)
                        hand_side = "right" if label == "Left" else "left"
                    else:
                        # Use MediaPipe's labels directly
                        hand_side = "left" if label == "Left" else "right"

                    # Debug output occasionally
                    if np.random.random() < 0.02:  # 2% chance
                        print(f"[Hand Detection] MediaPipe: {label} → User: {hand_side}")

                # Extract normalized landmarks
                landmarks = self._extract_landmarks(hand_landmarks)

                # Detect gesture for this hand
                gesture = self._detect_gesture(landmarks)

                # Store hand data
                hand_data = {
                    'landmarks': landmarks,
                    'gesture': gesture,
                    'confidence': self._calculate_gesture_confidence(landmarks, gesture),
                    'position': self._get_hand_center(landmarks)
                }

                if hand_side == "left":
                    self.left_hand = hand_data
                    self.left_gesture = gesture
                    self._update_gesture_timing('left', gesture)
                    self._track_swipe('left', hand_data['position'], gesture)
                elif hand_side == "right":
                    self.right_hand = hand_data
                    self.right_gesture = gesture
                    self._update_gesture_timing('right', gesture)
                    self._track_swipe('right', hand_data['position'], gesture)

        return self._get_current_state()

    def _extract_landmarks(self, hand_landmarks) -> List[Tuple[float, float]]:
        """Extract normalized landmark coordinates."""
        landmarks = []
        for landmark in hand_landmarks.landmark:
            landmarks.append((landmark.x, landmark.y))
        return landmarks

    def _detect_gesture(self, landmarks) -> str:
        """Detect gesture using geometric analysis of landmarks."""
        if len(landmarks) < 21:
            return "none"

        # Check each gesture in order of specificity
        if self._is_pinch(landmarks):
            return "pinch"
        elif self._is_pointer(landmarks):
            return "pointer"
        elif self._is_two_fingers(landmarks):
            return "two_fingers"
        elif self._is_closed_fist(landmarks):
            return "closed_fist"
        elif self._is_open_palm(landmarks):
            return "open_palm"
        else:
            return "unknown"

    def _is_open_palm(self, landmarks) -> bool:
        """Detect open palm - all fingers extended."""
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        finger_pips = [3, 6, 10, 14, 18]  # PIP joints

        extended_count = 0

        # Check thumb (special case - use x-axis)
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        if abs(thumb_tip[0] - thumb_mcp[0]) > self.FINGER_EXTEND_THRESHOLD:
            extended_count += 1

        # Check other fingers (use y-axis)
        for i in range(1, 5):
            tip = landmarks[finger_tips[i]]
            pip = landmarks[finger_pips[i]]
            if tip[1] < pip[1] - self.FINGER_EXTEND_THRESHOLD:
                extended_count += 1

        return extended_count >= 4  # At least 4 fingers extended

    def _is_closed_fist(self, landmarks) -> bool:
        """Detect closed fist - all fingers folded."""
        finger_tips = [4, 8, 12, 16, 20]
        finger_mcps = [2, 5, 9, 13, 17]

        folded_count = 0

        # Check all fingers are folded (tips below MCPs)
        for i in range(5):
            tip = landmarks[finger_tips[i]]
            mcp = landmarks[finger_mcps[i]]

            if i == 0:  # Thumb - check x-axis
                if abs(tip[0] - mcp[0]) < self.FINGER_FOLD_THRESHOLD:
                    folded_count += 1
            else:  # Other fingers - check y-axis
                if tip[1] > mcp[1] + self.FINGER_FOLD_THRESHOLD:
                    folded_count += 1

        return folded_count >= 4  # At least 4 fingers folded

    def _is_pinch(self, landmarks) -> bool:
        """Detect pinch - thumb tip close to index tip."""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]

        # Calculate distance between thumb and index tips
        distance = math.sqrt(
            (thumb_tip[0] - index_tip[0])**2 +
            (thumb_tip[1] - index_tip[1])**2
        )

        # Check if other fingers are not interfering
        middle_tip = landmarks[12]
        middle_distance = math.sqrt(
            (thumb_tip[0] - middle_tip[0])**2 +
            (thumb_tip[1] - middle_tip[1])**2
        )

        return distance < self.PINCH_THRESHOLD and middle_distance > distance * 1.5

    def _is_pointer(self, landmarks) -> bool:
        """Detect pointer - only index finger extended."""
        # Check index finger is extended
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        index_extended = index_tip[1] < index_pip[1] - self.FINGER_EXTEND_THRESHOLD

        if not index_extended:
            return False

        # Check other fingers are folded
        finger_tips = [4, 12, 16, 20]  # Thumb, Middle, Ring, Pinky
        finger_mcps = [2, 9, 13, 17]

        folded_count = 0
        for i, (tip_idx, mcp_idx) in enumerate(zip(finger_tips, finger_mcps)):
            tip = landmarks[tip_idx]
            mcp = landmarks[mcp_idx]

            if i == 0:  # Thumb
                if abs(tip[0] - mcp[0]) < self.FINGER_FOLD_THRESHOLD:
                    folded_count += 1
            else:  # Other fingers
                if tip[1] > mcp[1] + self.FINGER_FOLD_THRESHOLD:
                    folded_count += 1

        return folded_count >= 3  # Thumb, middle, ring, pinky folded

    def _is_two_fingers(self, landmarks) -> bool:
        """Detect two fingers - index and middle extended."""
        # Check index and middle fingers are extended
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]

        index_extended = index_tip[1] < index_pip[1] - self.FINGER_EXTEND_THRESHOLD
        middle_extended = middle_tip[1] < middle_pip[1] - self.FINGER_EXTEND_THRESHOLD

        if not (index_extended and middle_extended):
            return False

        # Check ring and pinky are folded (less strict on thumb)
        ring_tip = landmarks[16]
        ring_mcp = landmarks[13]
        pinky_tip = landmarks[20]
        pinky_mcp = landmarks[17]

        ring_folded = ring_tip[1] > ring_mcp[1] + (self.FINGER_FOLD_THRESHOLD * 0.7)
        pinky_folded = pinky_tip[1] > pinky_mcp[1] + (self.FINGER_FOLD_THRESHOLD * 0.7)

        # Check that index and middle are clearly separated from ring and pinky
        finger_separation = abs(middle_tip[1] - ring_tip[1]) > self.FINGER_EXTEND_THRESHOLD

        return ring_folded and pinky_folded and finger_separation

    def _calculate_gesture_confidence(self, landmarks, gesture) -> float:
        """Calculate confidence score for detected gesture."""
        if gesture == "none" or gesture == "unknown":
            return 0.0

        # Base confidence on how well landmarks match gesture criteria
        # This is a simplified version - can be made more sophisticated
        confidence = 0.8

        # Add stability bonus if gesture is clear
        if gesture in ["open_palm", "closed_fist"]:
            confidence += 0.1
        elif gesture in ["pinch", "pointer", "two_fingers"]:
            confidence += 0.05

        return min(1.0, confidence)

    def _get_hand_center(self, landmarks) -> Tuple[float, float]:
        """Get center point of hand for UI positioning."""
        # Use wrist as center point
        return landmarks[0]

    def _track_swipe(self, hand: str, position: Tuple[float, float], gesture: str):
        """Track hand position for swipe detection."""
        current_time = time.time()
        swipe_data = self.swipe_history[hand]

        # Only track swipes with open palm
        if gesture != 'open_palm':
            swipe_data['positions'] = []
            swipe_data['last_time'] = current_time
            return

        # Clear old positions if too much time has passed
        if current_time - swipe_data['last_time'] > self.SWIPE_TIME_WINDOW:
            swipe_data['positions'] = []

        # Add current position
        swipe_data['positions'].append((position[0], current_time))
        swipe_data['last_time'] = current_time

        # Keep only recent positions
        swipe_data['positions'] = [
            (x, t) for x, t in swipe_data['positions']
            if current_time - t < self.SWIPE_TIME_WINDOW
        ]

        # Detect swipe if we have enough positions
        if len(swipe_data['positions']) >= 3:
            # Check if both hands are detected for sensitivity adjustment
            both_hands_detected = self.left_hand is not None and self.right_hand is not None

            # Use different threshold based on hand count
            # Single hand: easier swipe (lower threshold)
            # Two hands: harder swipe (higher threshold) to avoid accidental triggers
            threshold = self.SWIPE_THRESHOLD * 2.0 if both_hands_detected else self.SWIPE_THRESHOLD

            swipe_direction = self._detect_swipe_with_threshold(swipe_data['positions'], threshold)
            if swipe_direction:
                print(f"[Swipe] {hand} hand swipe {swipe_direction} (threshold: {threshold:.2f})")
                # Store swipe event
                swipe_data['last_swipe'] = swipe_direction
                swipe_data['swipe_time'] = current_time
                # Clear positions after successful swipe
                swipe_data['positions'] = []

    def _detect_swipe(self, positions: List[Tuple[float, float]]) -> Optional[str]:
        """Detect swipe direction from position history (uses default threshold)."""
        return self._detect_swipe_with_threshold(positions, self.SWIPE_THRESHOLD)

    def _detect_swipe_with_threshold(self, positions: List[Tuple[float, float]], threshold: float) -> Optional[str]:
        """Detect swipe direction with custom threshold."""
        if len(positions) < 3:
            return None

        # Calculate total horizontal movement
        start_x = positions[0][0]
        end_x = positions[-1][0]
        distance = end_x - start_x

        # Also check for consistency in direction (reduce false positives)
        mid_x = positions[len(positions)//2][0]
        consistent_direction = (
            (mid_x > start_x and end_x > mid_x) or  # Consistently moving right
            (mid_x < start_x and end_x < mid_x)     # Consistently moving left
        )

        # Check if movement is significant and consistent
        if abs(distance) > threshold and consistent_direction:
            return "right" if distance > 0 else "left"

        return None

    def _get_current_state(self) -> Dict:
        """Get current state of both hands and gestures."""
        timing_info = self.get_gesture_timing_info()

        # Check for recent swipes
        left_swipe = self._get_recent_swipe('left')
        right_swipe = self._get_recent_swipe('right')

        return {
            'left_hand': {
                'detected': self.left_hand is not None,
                'gesture': self.left_gesture,
                'position': self.left_hand['position'] if self.left_hand else (0, 0),
                'confidence': self.left_hand['confidence'] if self.left_hand else 0.0,
                'duration': timing_info['left']['duration'],
                'is_quick': timing_info['left']['is_quick'],
                'swipe': left_swipe
            },
            'right_hand': {
                'detected': self.right_hand is not None,
                'gesture': self.right_gesture,
                'position': self.right_hand['position'] if self.right_hand else (0, 0),
                'confidence': self.right_hand['confidence'] if self.right_hand else 0.0,
                'duration': timing_info['right']['duration'],
                'is_quick': timing_info['right']['is_quick'],
                'swipe': right_swipe
            },
            'interaction_state': self._determine_interaction_state(),
            'timing_info': timing_info
        }

    def _get_recent_swipe(self, hand: str) -> Optional[str]:
        """Check if a swipe was detected recently."""
        swipe_data = self.swipe_history[hand]
        current_time = time.time()

        # Check if swipe is still active (within event duration)
        if swipe_data['last_swipe'] and current_time - swipe_data['swipe_time'] < self.SWIPE_EVENT_DURATION:
            return swipe_data['last_swipe']

        return None

    def _determine_interaction_state(self) -> str:
        """Determine the current interaction state based on both hands."""
        left_gesture = self.left_gesture
        right_gesture = self.right_gesture

        # Both hands open = browsing mode
        if left_gesture == "open_palm" and right_gesture == "open_palm":
            return "browsing"

        # One hand fist = mode selection
        if left_gesture == "closed_fist" and right_gesture == "open_palm":
            return "selecting_with_left"
        elif right_gesture == "closed_fist" and left_gesture == "open_palm":
            return "selecting_with_right"

        # One fist + special gesture = audio control
        if left_gesture == "closed_fist" and right_gesture in ["pinch", "pointer", "two_fingers"]:
            return f"controlling_with_right_{right_gesture}"
        elif right_gesture == "closed_fist" and left_gesture in ["pinch", "pointer", "two_fingers"]:
            return f"controlling_with_left_{left_gesture}"

        return "unknown"

    def get_screen_coordinates(self, hand_position: Tuple[float, float],
                             screen_width: int, screen_height: int) -> Tuple[int, int]:
        """Convert normalized hand position to screen coordinates."""
        x = int(hand_position[0] * screen_width)
        y = int(hand_position[1] * screen_height)
        return (x, y)

    def release(self):
        """Release resources."""
        if self.hands:
            try:
                self.hands.close()
            except ValueError:
                # Already closed, ignore
                pass

    def _update_gesture_timing(self, hand_side: str, current_gesture: str):
        """Update gesture timing for quick gesture detection."""
        current_time = time.time()
        history = self.gesture_history[hand_side]

        # If gesture changed
        if history['gesture'] != current_gesture:
            # If previous gesture was not 'none', calculate its duration
            if history['gesture'] != 'none':
                history['duration'] = current_time - history['start_time']

                # Check if it was a quick gesture
                if history['duration'] <= self.QUICK_GESTURE_THRESHOLD:
                    # Check cooldown period
                    if current_time - history['last_quick_gesture'] >= self.GESTURE_COOLDOWN:
                        history['last_quick_gesture'] = current_time
                        # Trigger quick gesture event
                        self._trigger_quick_gesture(hand_side, history['gesture'])

            # Start tracking new gesture
            history['gesture'] = current_gesture
            history['start_time'] = current_time
            history['duration'] = 0
        else:
            # Update duration of current gesture
            history['duration'] = current_time - history['start_time']

    def _trigger_quick_gesture(self, hand_side: str, gesture: str):
        """Handle quick gesture events for button actions."""
        # This will be used by the main application for button triggering
        print(f"[QuickGesture] {hand_side} {gesture} - Duration: {self.gesture_history[hand_side]['duration']:.2f}s")

    def get_gesture_timing_info(self) -> Dict:
        """Get current gesture timing information."""
        return {
            'left': {
                'gesture': self.gesture_history['left']['gesture'],
                'duration': self.gesture_history['left']['duration'],
                'is_quick': self.gesture_history['left']['duration'] <= self.QUICK_GESTURE_THRESHOLD,
                'last_quick': self.gesture_history['left']['last_quick_gesture']
            },
            'right': {
                'gesture': self.gesture_history['right']['gesture'],
                'duration': self.gesture_history['right']['duration'],
                'is_quick': self.gesture_history['right']['duration'] <= self.QUICK_GESTURE_THRESHOLD,
                'last_quick': self.gesture_history['right']['last_quick_gesture']
            }
        }