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

# Handle imports for both direct run and module import
try:
    from config_loader import get_config
except ImportError:
    from src.config_loader import get_config

class PrecisionGestureRecognizer:
    """Ultra-precise gesture recognition using geometric analysis of hand landmarks."""

    def __init__(self):
        """Initialize the precision gesture recognizer."""
        # Load configuration
        self.config = get_config()

        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

        # Get MediaPipe config
        mp_config = self.config.get('gestures', 'mediapipe', default={})

        # Initialize MediaPipe Hands with config settings
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=mp_config.get('max_num_hands', 2),
            model_complexity=mp_config.get('model_complexity', 1),
            min_detection_confidence=mp_config.get('min_detection_confidence', 0.7),
            min_tracking_confidence=mp_config.get('min_tracking_confidence', 0.5)
        )

        # Get gesture detection thresholds from config
        thresholds = self.config.get('gestures', 'thresholds', default={})
        self.PINCH_THRESHOLD = thresholds.get('pinch_threshold', 0.04)
        self.FINGER_FOLD_THRESHOLD = thresholds.get('finger_fold_threshold', 0.10)
        self.FINGER_EXTEND_THRESHOLD = thresholds.get('finger_fold_threshold', 0.10)

        # Current hand states
        self.left_hand = None
        self.right_hand = None
        self.left_gesture = "none"
        self.right_gesture = "none"

        # Get swipe detection settings from config
        swipe_config = thresholds.get('swipe', {})
        self.swipe_history = {
            'left': {'positions': [], 'last_time': 0, 'last_swipe': None, 'swipe_time': 0, 'direction_changes': 0},
            'right': {'positions': [], 'last_time': 0, 'last_swipe': None, 'swipe_time': 0, 'direction_changes': 0}
        }
        self.SWIPE_THRESHOLD = swipe_config.get('distance_threshold', 0.15)  # More lenient: 15% of screen
        self.SWIPE_TIME_WINDOW = swipe_config.get('time_window', 0.8)  # Longer time window
        self.SWIPE_EVENT_DURATION = 0.3
        self.SWIPE_MINIMUM_FRAMES = swipe_config.get('min_frames', 3)  # Fewer frames needed
        self.SWIPE_VELOCITY_MIN = swipe_config.get('velocity_threshold', 0.25)  # Lower velocity required
        self.SWIPE_DEAD_ZONE_CENTER = 0.5
        self.SWIPE_DEAD_ZONE_RADIUS = swipe_config.get('dead_zone_radius', 0.05)
        self.SWIPE_COOLDOWN = swipe_config.get('cooldown', 0.3)

        # Hand swap correction from config
        self.SWAP_HANDS = self.config.get('gestures', 'swap_hands', default=True)

        # Gesture timing for quick actions
        self.gesture_history = {
            'left': {'gesture': 'none', 'start_time': 0, 'duration': 0, 'last_quick_gesture': 0},
            'right': {'gesture': 'none', 'start_time': 0, 'duration': 0, 'last_quick_gesture': 0}
        }
        self.QUICK_GESTURE_THRESHOLD = 0.5
        self.GESTURE_COOLDOWN = 0.3

        # Tap gesture detection (for instant play/pause)
        tap_config = thresholds.get('tap', {})
        self.tap_history = {
            'left': {'positions': [], 'velocities': [], 'last_tap_time': 0},
            'right': {'positions': [], 'velocities': [], 'last_tap_time': 0}
        }
        self.TAP_VELOCITY_THRESHOLD = tap_config.get('velocity_threshold', 0.5)
        self.TAP_DISTANCE_MIN = tap_config.get('distance_min', 0.10)
        self.TAP_DISTANCE_MAX = tap_config.get('distance_max', 0.25)
        self.TAP_TIME_WINDOW = tap_config.get('time_window', 0.2)
        self.TAP_COOLDOWN = tap_config.get('cooldown', 0.2)
        self.TAP_HISTORY_SIZE = 5  # frames to track for velocity calculation

        # Palm rotation detection (for scratching)
        self.rotation_history = {
            'left': {'angles': [], 'last_rotation_time': 0, 'rotation_velocity': 0},
            'right': {'angles': [], 'last_rotation_time': 0, 'rotation_velocity': 0}
        }
        self.ROTATION_HISTORY_SIZE = 8  # frames to track for smooth rotation
        self.ROTATION_VELOCITY_THRESHOLD = 30  # degrees per second for scratch detection

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
                        print(f"[Hand Detection] MediaPipe: {label} -> User: {hand_side}")

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
                    self._track_tap('left', hand_data['position'])
                    self._track_palm_rotation('left', landmarks)
                elif hand_side == "right":
                    self.right_hand = hand_data
                    self.right_gesture = gesture
                    self._update_gesture_timing('right', gesture)
                    self._track_swipe('right', hand_data['position'], gesture)
                    self._track_tap('right', hand_data['position'])
                    self._track_palm_rotation('right', landmarks)

        return self._get_current_state()

    def _extract_landmarks(self, hand_landmarks) -> List[Tuple[float, float]]:
        """Extract normalized landmark coordinates."""
        landmarks = []
        for landmark in hand_landmarks.landmark:
            landmarks.append((landmark.x, landmark.y))
        return landmarks

    def _calculate_hand_size(self, landmarks) -> float:
        """Calculate hand size for distance normalization.
        Uses wrist to middle finger distance as reference.
        """
        wrist = landmarks[0]
        middle_tip = landmarks[12]

        # Calculate Euclidean distance
        hand_size = math.sqrt(
            (middle_tip[0] - wrist[0])**2 +
            (middle_tip[1] - wrist[1])**2
        )
        return hand_size

    def _get_normalized_threshold(self, base_threshold: float, hand_size: float) -> float:
        """Normalize threshold based on hand distance from camera.
        Smaller hand_size = farther from camera = need smaller thresholds.

        Args:
            base_threshold: The default threshold value
            hand_size: Current hand size (0.1 to 0.4 typical range)

        Returns:
            Adjusted threshold that works at any distance
        """
        # Reference hand size when at optimal distance
        REFERENCE_SIZE = 0.25

        # Calculate normalization factor
        # If hand is smaller (farther), reduce threshold
        # If hand is larger (closer), increase threshold
        normalization_factor = hand_size / REFERENCE_SIZE

        # Apply MORE aggressive normalization for far distances (0.25x to 1.5x)
        # When hand is far (small size), we need much smaller thresholds
        normalized = base_threshold * max(0.25, min(1.5, normalization_factor))

        return normalized

    def _detect_gesture(self, landmarks) -> str:
        """Detect gesture using geometric analysis of landmarks."""
        if len(landmarks) < 21:
            return "none"

        # Check gestures in order: most SPECIFIC -> most GENERAL
        # This ensures specific gestures (pinch, pointer) are detected before generic (open_palm)

        # 1. Closed fist FIRST (easy to detect, very distinct)
        if self._is_closed_fist(landmarks):
            return "closed_fist"

        # 2. THUMBS GESTURES DISABLED - too sensitive, caused false triggers
        # Removed: thumbs_up and thumbs_down detection

        # 3. Precision control gestures (specific finger positions)
        if self._is_pinch(landmarks):
            return "pinch"
        if self._is_pointer(landmarks):
            return "pointer"
        if self._is_two_fingers(landmarks):
            return "two_fingers"

        # 4. Open palm LAST (default for extended fingers)
        if self._is_open_palm(landmarks):
            return "open_palm"

        # 5. If nothing matches, return "none" (hand detected but no clear gesture)
        return "none"

    def _is_open_palm(self, landmarks) -> bool:
        """Detect open palm - most fingers extended (relaxed detection with distance normalization)."""
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        finger_pips = [3, 6, 10, 14, 18]  # PIP joints

        # Apply distance normalization
        hand_size = self._calculate_hand_size(landmarks)
        extend_threshold = self._get_normalized_threshold(self.FINGER_EXTEND_THRESHOLD * 0.5, hand_size)

        extended_count = 0

        # Check thumb (special case - use x-axis)
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        if abs(thumb_tip[0] - thumb_mcp[0]) > extend_threshold:
            extended_count += 1

        # Check other fingers (use y-axis)
        for i in range(1, 5):
            tip = landmarks[finger_tips[i]]
            pip = landmarks[finger_pips[i]]
            if tip[1] < pip[1] - extend_threshold:
                extended_count += 1

        return extended_count >= 3  # At least 3 fingers extended (more forgiving)

    def _is_closed_fist(self, landmarks) -> bool:
        """Detect closed fist - all fingers folded into a compact shape.

        STRICT detection: ALL fingers must be clearly folded.
        """
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky (exclude thumb)
        finger_mcps = [5, 9, 13, 17]

        folded_count = 0

        # Check all 4 fingers are folded (strict: tip below MCP)
        for tip_idx, mcp_idx in zip(finger_tips, finger_mcps):
            tip = landmarks[tip_idx]
            mcp = landmarks[mcp_idx]

            # Finger is folded if tip is at or below MCP knuckle
            if tip[1] >= mcp[1] - 0.01:  # Strict threshold
                folded_count += 1

        # Check hand compactness - fist should have fingers close together
        index_tip = landmarks[8]
        pinky_tip = landmarks[20]
        hand_width = abs(index_tip[0] - pinky_tip[0])

        # Stricter compactness check
        is_compact = hand_width < 0.12

        # Require ALL 4 fingers folded AND very compact shape
        return folded_count >= 4 and is_compact

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
        """Detect pointer - ONLY index finger extended, middle MUST be folded (with distance normalization)."""
        # Calculate hand size for distance normalization
        hand_size = self._calculate_hand_size(landmarks)

        # Normalize thresholds based on distance - MORE LENIENT for far detection
        extend_threshold = self._get_normalized_threshold(self.FINGER_EXTEND_THRESHOLD * 0.5, hand_size)  # 50% more lenient
        fold_threshold = self._get_normalized_threshold(self.FINGER_FOLD_THRESHOLD * 0.7, hand_size)  # 30% more lenient

        # Check index finger is extended
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        index_extended = index_tip[1] < index_pip[1] - extend_threshold

        if not index_extended:
            return False

        # CRITICAL: Middle finger MUST be folded (to distinguish from two_fingers)
        middle_tip = landmarks[12]
        middle_mcp = landmarks[9]
        middle_folded = middle_tip[1] > middle_mcp[1] - extend_threshold * 0.5

        if not middle_folded:
            return False  # If middle is extended, this is two_fingers, not pointer

        # Check ring and pinky are folded
        ring_tip = landmarks[16]
        ring_mcp = landmarks[13]
        pinky_tip = landmarks[20]
        pinky_mcp = landmarks[17]

        ring_folded = ring_tip[1] > ring_mcp[1] - extend_threshold * 0.5
        pinky_folded = pinky_tip[1] > pinky_mcp[1] - extend_threshold * 0.5

        # Require at least 2 of the 3 non-index fingers to be folded
        folded_count = sum([middle_folded, ring_folded, pinky_folded])
        return folded_count >= 2

    def _is_two_fingers(self, landmarks) -> bool:
        """Detect two fingers - BOTH index and middle extended, ring/pinky folded (with distance normalization)."""
        # Calculate hand size for distance normalization
        hand_size = self._calculate_hand_size(landmarks)

        # Normalize thresholds based on distance - MORE LENIENT for far detection
        extend_threshold = self._get_normalized_threshold(self.FINGER_EXTEND_THRESHOLD * 0.5, hand_size)  # 50% more lenient
        fold_threshold = self._get_normalized_threshold(self.FINGER_FOLD_THRESHOLD * 0.5, hand_size)  # 50% more lenient

        # CRITICAL: Check BOTH index and middle fingers are extended
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]

        index_extended = index_tip[1] < index_pip[1] - extend_threshold
        middle_extended = middle_tip[1] < middle_pip[1] - extend_threshold

        if not (index_extended and middle_extended):
            return False

        # CRITICAL: Ring and pinky MUST be folded (to distinguish from open palm)
        ring_tip = landmarks[16]
        ring_mcp = landmarks[13]
        pinky_tip = landmarks[20]
        pinky_mcp = landmarks[17]

        ring_folded = ring_tip[1] > ring_mcp[1] - extend_threshold * 0.3
        pinky_folded = pinky_tip[1] > pinky_mcp[1] - extend_threshold * 0.3

        # Check finger separation (middle should be higher than ring)
        finger_separation = middle_tip[1] < ring_tip[1] - extend_threshold * 0.5

        # Require BOTH ring and pinky folded AND good separation
        return ring_folded and pinky_folded and finger_separation

    def _is_thumbs_up(self, landmarks) -> bool:
        """Detect thumbs up - thumb extended upward and separated from fist, fingers folded.

        Key distinguishing feature from closed_fist:
        - Thumb is WAY above wrist AND far from other fingers
        - Primary discriminator is vertical position + separation distance

        STRICTNESS: Increased thresholds to prevent false positives from relaxed fist
        """
        # Get thresholds from config - NOW STRICTER: 0.15 extension, 0.10 separation
        thumbs_up_config = self.config.get('gestures', 'thresholds', 'thumbs_up', default={})
        thumb_ext_min = thumbs_up_config.get('thumb_extension_min', 0.15)  # Default increased
        thumb_sep_min = thumbs_up_config.get('thumb_separation_min', 0.10)  # New stricter separation
        other_fingers_max = thumbs_up_config.get('other_fingers_folded_max', 0.08)

        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]
        index_tip = landmarks[8]
        index_mcp = landmarks[5]

        # CRITICAL: Thumb must be WAY above wrist (STRICTER: 0.15 vs old 0.12)
        thumb_wrist_vertical = wrist[1] - thumb_tip[1]  # Positive = thumb above wrist
        thumb_clearly_extended = thumb_wrist_vertical > thumb_ext_min

        # CRITICAL: Thumb must be pointing UP (not sideways)
        # Check thumb tip is above thumb MCP by significant amount
        thumb_pointing_up = (thumb_mcp[1] - thumb_tip[1]) > 0.06

        # CRITICAL: Thumb must be SEPARATED from index finger (STRICTER: 0.10 vs old 0.08)
        thumb_index_distance = math.sqrt(
            (thumb_tip[0] - index_tip[0])**2 +
            (thumb_tip[1] - index_tip[1])**2
        )
        # This is the KEY discriminator - in a fist, thumb is close to fingers
        # In thumbs up, thumb must be at least 10cm away from index finger (+25% stricter)
        thumb_separated = thumb_index_distance > thumb_sep_min

        # Additional check: thumb should be higher than index finger
        thumb_above_index = thumb_tip[1] < index_tip[1] - 0.05

        # Check other fingers are folded (all 4 fingers must be clearly folded)
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        finger_mcps = [5, 9, 13, 17]

        folded_count = 0
        for i in range(4):
            tip = landmarks[finger_tips[i]]
            mcp = landmarks[finger_mcps[i]]
            # Finger is folded if tip is not much higher than MCP
            if tip[1] >= mcp[1] - other_fingers_max:
                folded_count += 1

        # Require ALL 4 fingers folded (stricter than before)
        fingers_folded = folded_count == 4

        # ALL conditions must be met to avoid false positives
        return (thumb_clearly_extended and
                thumb_pointing_up and
                thumb_separated and
                thumb_above_index and
                fingers_folded)

    def _is_thumbs_down(self, landmarks) -> bool:
        """Detect thumbs down - thumb extended downward, other fingers folded.

        STRICTNESS: Increased thresholds to prevent false positives from relaxed fist
        """
        # Get thresholds from config - NOW STRICTER: 0.15 extension, 0.10 separation
        thumbs_down_config = self.config.get('gestures', 'thresholds', 'thumbs_down', default={})
        thumb_ext_min = thumbs_down_config.get('thumb_extension_min', 0.15)  # Default increased
        thumb_sep_min = thumbs_down_config.get('thumb_separation_min', 0.10)  # New stricter separation
        other_fingers_max = thumbs_down_config.get('other_fingers_folded_max', 0.08)

        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]
        index_tip = landmarks[8]

        # CRITICAL: Thumb must be clearly BELOW wrist (STRICTER: 0.15 vs old 0.12)
        thumb_wrist_vertical = thumb_tip[1] - wrist[1]  # Positive = thumb below wrist
        thumb_clearly_extended = thumb_wrist_vertical > thumb_ext_min

        # CRITICAL: Thumb must be pointing DOWN (not sideways)
        # Check thumb tip is below thumb MCP by significant amount
        thumb_pointing_down = (thumb_tip[1] - thumb_mcp[1]) > 0.06

        # CRITICAL: Thumb must be SEPARATED from index finger (STRICTER: 0.10 vs old 0.08)
        thumb_index_distance = math.sqrt(
            (thumb_tip[0] - index_tip[0])**2 +
            (thumb_tip[1] - index_tip[1])**2
        )
        # In thumbs down, thumb must be at least 10cm away from index finger (+25% stricter)
        thumb_separated = thumb_index_distance > thumb_sep_min

        # Additional check: thumb should be lower than index finger
        thumb_below_index = thumb_tip[1] > index_tip[1] + 0.05

        # Check other fingers are folded (all 4 fingers must be clearly folded)
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        finger_mcps = [5, 9, 13, 17]

        folded_count = 0
        for i in range(4):
            tip = landmarks[finger_tips[i]]
            mcp = landmarks[finger_mcps[i]]
            # Finger is folded if tip is not much higher than MCP
            if tip[1] >= mcp[1] - other_fingers_max:
                folded_count += 1

        # Require ALL 4 fingers folded (stricter than before)
        fingers_folded = folded_count == 4

        # ALL conditions must be met to avoid false positives
        return (thumb_clearly_extended and
                thumb_pointing_down and
                thumb_separated and
                thumb_below_index and
                fingers_folded)

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
        elif gesture in ["thumbs_up", "thumbs_down"]:
            confidence += 0.08  # High confidence for thumb gestures
        elif gesture in ["pinch", "pointer", "two_fingers"]:
            confidence += 0.05

        return min(1.0, confidence)

    def _get_hand_center(self, landmarks) -> Tuple[float, float]:
        """Get center point of hand for UI positioning."""
        # Use wrist as center point
        return landmarks[0]

    def _track_swipe(self, hand: str, position: Tuple[float, float], gesture: str):
        """Track hand position for swipe detection with strict validation."""
        current_time = time.time()
        swipe_data = self.swipe_history[hand]

        # DEBUG: Log open_palm detection
        if gesture == 'open_palm' and np.random.random() < 0.1:  # 10% sampling
            print(f"[Swipe Debug] {hand} hand: open_palm detected at pos {position[0]:.2f}")

        # Only track swipes with open palm
        if gesture != 'open_palm':
            swipe_data['positions'] = []
            swipe_data['last_time'] = current_time
            swipe_data['direction_changes'] = 0
            return

        # Check if we're in cooldown period
        if swipe_data['last_swipe'] and current_time - swipe_data['swipe_time'] < self.SWIPE_COOLDOWN:
            return  # Still in cooldown, don't track new swipes

        # Check if hand is in dead zone (center of screen)
        x_pos = position[0]
        if abs(x_pos - self.SWIPE_DEAD_ZONE_CENTER) < self.SWIPE_DEAD_ZONE_RADIUS:
            # In dead zone, don't start tracking
            if len(swipe_data['positions']) == 0:
                return

        # Clear old positions if too much time has passed
        if current_time - swipe_data['last_time'] > self.SWIPE_TIME_WINDOW:
            swipe_data['positions'] = []
            swipe_data['direction_changes'] = 0

        # Track direction changes to prevent jitter from triggering swipes
        if len(swipe_data['positions']) >= 2:
            try:
                # Extract previous X position - positions are stored as ((x, y), time) tuples
                prev_entry = swipe_data['positions'][-1]
                prev_prev_entry = swipe_data['positions'][-2]

                # Each entry is ((x, y), time), so extract (x, y) first, then x
                prev_pos_tuple = prev_entry[0]  # This is (x, y)
                prev_prev_pos_tuple = prev_prev_entry[0]  # This is (x, y)

                prev_x = prev_pos_tuple[0]  # Extract x from (x, y)
                prev_prev_x = prev_prev_pos_tuple[0]  # Extract x from (x, y)
            except Exception as e:
                print(f"[SWIPE BUG DEBUG] Error extracting x positions: {e}")
                print(f"[SWIPE BUG DEBUG] prev_entry type: {type(prev_entry)}, value: {prev_entry}")
                print(f"[SWIPE BUG DEBUG] prev_prev_entry type: {type(prev_prev_entry)}, value: {prev_prev_entry}")
                print(f"[SWIPE BUG DEBUG] Clearing positions and aborting")
                swipe_data['positions'] = []
                return

            # Check if direction changed
            prev_direction = 1 if prev_x > prev_prev_x else -1
            current_direction = 1 if x_pos > prev_x else -1

            if prev_direction != current_direction:
                swipe_data['direction_changes'] += 1
                # Too many direction changes = abort this swipe attempt
                # INCREASED from 2 to 3 for more tolerance
                if swipe_data['direction_changes'] > 3:
                    swipe_data['positions'] = []
                    swipe_data['direction_changes'] = 0
                    return

        # Add current position (NEW FORMAT: store both x and y)
        # DEBUG: Verify data structure
        if np.random.random() < 0.05:  # 5% sampling
            print(f"[APPEND DEBUG] Appending: position={position} (type={type(position)}), time={current_time} (type={type(current_time)})")
        swipe_data['positions'].append((position, current_time))  # position is (x, y) tuple
        swipe_data['last_time'] = current_time

        # Keep only recent positions
        # Each entry is ((x, y), time)
        swipe_data['positions'] = [
            entry for entry in swipe_data['positions']
            if current_time - entry[1] < self.SWIPE_TIME_WINDOW
        ]

        # Detect swipe if we have enough frames
        if len(swipe_data['positions']) >= self.SWIPE_MINIMUM_FRAMES:
            swipe_direction = self._detect_swipe_with_threshold(swipe_data['positions'], self.SWIPE_THRESHOLD)
            if swipe_direction:
                print(f"[Swipe] {hand} hand swipe {swipe_direction} | Frames: {len(swipe_data['positions'])} | Direction changes: {swipe_data['direction_changes']}")
                # Store swipe event
                swipe_data['last_swipe'] = swipe_direction
                swipe_data['swipe_time'] = current_time
                # Clear positions after successful swipe
                swipe_data['positions'] = []
                swipe_data['direction_changes'] = 0

    def _detect_swipe(self, positions: List[Tuple[float, float]]) -> Optional[str]:
        """Detect swipe direction from position history (uses default threshold)."""
        return self._detect_swipe_with_threshold(positions, self.SWIPE_THRESHOLD)

    def _detect_swipe_with_threshold(self, positions: List[Tuple[float, float]], threshold: float) -> Optional[str]:
        """Detect swipe direction with 8-directional support (4 cardinal + 4 diagonal)."""
        import math

        if len(positions) < self.SWIPE_MINIMUM_FRAMES:
            return None

        # Extract start and end positions
        # Check if first element is a tuple (new format) or float (old format)
        if isinstance(positions[0][0], tuple):
            # New format: ((x, y), time)
            (start_x, start_y), start_time = positions[0]
            (end_x, end_y), end_time = positions[-1]
        else:
            # Old format: (x, time) - horizontal only
            start_x, start_time = positions[0]
            end_x, end_time = positions[-1]
            start_y = end_y = 0.5  # Assume neutral Y for old format

        # Calculate movement vector
        dx = end_x - start_x
        dy = end_y - start_y  # Note: positive dy = moving DOWN (screen coords)
        time_elapsed = end_time - start_time

        # Calculate total distance and velocity
        distance = math.sqrt(dx**2 + dy**2)

        if time_elapsed > 0:
            velocity = distance / time_elapsed
            if velocity < self.SWIPE_VELOCITY_MIN:
                return None  # Too slow, not a deliberate swipe

        # Check if movement distance is significant
        if distance < threshold:
            return None  # Movement too small

        # Calculate angle of movement (-180 to 180 degrees)
        # 0° = right, 90° = down, -90° = up, ±180° = left
        angle = math.degrees(math.atan2(dy, dx))

        # Classify into 8 directions (45° sectors)
        # Allow 22.5° tolerance on each side for more forgiving detection
        if -22.5 <= angle < 22.5:
            return "right"
        elif 22.5 <= angle < 67.5:
            return "down-right"
        elif 67.5 <= angle < 112.5:
            return "down"
        elif 112.5 <= angle < 157.5:
            return "down-left"
        elif angle >= 157.5 or angle < -157.5:
            return "left"
        elif -157.5 <= angle < -112.5:
            return "up-left"
        elif -112.5 <= angle < -67.5:
            return "up"
        elif -67.5 <= angle < -22.5:
            return "up-right"

        return None

    def _track_tap(self, hand: str, position: Tuple[float, float]):
        """
        Track hand vertical movement to detect tap gestures (quick downward motion).
        Tap = instant play/pause trigger.
        """
        current_time = time.time()
        tap_data = self.tap_history[hand]

        # Check if in cooldown period
        if current_time - tap_data['last_tap_time'] < self.TAP_COOLDOWN:
            return

        # Add current position with timestamp
        y_pos = position[1]  # Vertical position (0 = top, 1 = bottom)
        tap_data['positions'].append((y_pos, current_time))

        # Keep only recent positions
        tap_data['positions'] = [
            (y, t) for y, t in tap_data['positions']
            if current_time - t < self.TAP_TIME_WINDOW
        ]

        # Need at least 3 frames to detect tap
        if len(tap_data['positions']) < 3:
            return

        # Calculate movement and velocity
        start_y, start_time = tap_data['positions'][0]
        end_y, end_time = tap_data['positions'][-1]

        # Movement distance (positive = downward)
        distance = end_y - start_y
        time_elapsed = end_time - start_time

        # Calculate velocity (downward motion)
        if time_elapsed > 0:
            velocity = distance / time_elapsed  # Positive = downward

            # Check if this is a tap gesture
            if (velocity >= self.TAP_VELOCITY_THRESHOLD and
                self.TAP_DISTANCE_MIN <= distance <= self.TAP_DISTANCE_MAX and
                time_elapsed <= self.TAP_TIME_WINDOW):

                # Detected a tap!
                print(f"[TAP] {hand} hand tap detected! Velocity: {velocity:.2f}, Distance: {distance:.2f}")

                # Record tap event
                tap_data['last_tap_time'] = current_time

                # Clear position history
                tap_data['positions'] = []

    def _get_recent_tap(self, hand: str) -> bool:
        """Check if a tap was detected very recently (within a small window)."""
        tap_data = self.tap_history[hand]
        current_time = time.time()

        # Tap is considered "active" for a brief moment after detection
        tap_active_window = 0.1  # 100ms window

        if current_time - tap_data['last_tap_time'] < tap_active_window:
            return True

        return False

    def _track_palm_rotation(self, hand: str, landmarks) -> None:
        """Track palm rotation angle for scratch control.

        Calculates rotation based on wrist-to-middle-finger-base vector.
        """
        import math

        current_time = time.time()
        rotation_data = self.rotation_history[hand]

        # Calculate palm angle using wrist (0) and middle finger MCP (9)
        wrist = landmarks[0]
        middle_mcp = landmarks[9]

        # Vector from wrist to middle finger base
        dx = middle_mcp[0] - wrist[0]
        dy = middle_mcp[1] - wrist[1]

        # Calculate angle in degrees (-180 to 180)
        # 0° = palm pointing right, 90° = pointing down, -90° = pointing up
        angle = math.degrees(math.atan2(dy, dx))

        # Add to history with timestamp
        rotation_data['angles'].append((angle, current_time))

        # Keep only recent angles
        rotation_data['angles'] = [
            (a, t) for a, t in rotation_data['angles']
            if current_time - t < 0.5  # 500ms history
        ]

        # Keep max size
        if len(rotation_data['angles']) > self.ROTATION_HISTORY_SIZE:
            rotation_data['angles'] = rotation_data['angles'][-self.ROTATION_HISTORY_SIZE:]

        # Calculate rotation velocity (degrees per second)
        if len(rotation_data['angles']) >= 3:
            start_angle, start_time = rotation_data['angles'][0]
            end_angle, end_time = rotation_data['angles'][-1]

            time_diff = end_time - start_time
            if time_diff > 0:
                # Handle angle wrapping (-180 to 180)
                angle_diff = end_angle - start_angle
                if angle_diff > 180:
                    angle_diff -= 360
                elif angle_diff < -180:
                    angle_diff += 360

                rotation_velocity = angle_diff / time_diff
                rotation_data['rotation_velocity'] = rotation_velocity
        else:
            rotation_data['rotation_velocity'] = 0

    def _get_palm_rotation_velocity(self, hand: str) -> float:
        """Get current palm rotation velocity in degrees per second."""
        return self.rotation_history[hand]['rotation_velocity']

    def _get_palm_angle(self, hand: str) -> float:
        """Get current palm angle in degrees."""
        rotation_data = self.rotation_history[hand]
        if rotation_data['angles']:
            return rotation_data['angles'][-1][0]
        return 0.0

    def _get_current_state(self) -> Dict:
        """Get current state of both hands and gestures."""
        timing_info = self.get_gesture_timing_info()

        # Check for recent swipes and taps
        left_swipe = self._get_recent_swipe('left')
        right_swipe = self._get_recent_swipe('right')
        left_tap = self._get_recent_tap('left')
        right_tap = self._get_recent_tap('right')

        return {
            'left_hand': {
                'detected': self.left_hand is not None,
                'gesture': self.left_gesture,
                'position': self.left_hand['position'] if self.left_hand else (0, 0),
                'confidence': self.left_hand['confidence'] if self.left_hand else 0.0,
                'duration': timing_info['left']['duration'],
                'is_quick': timing_info['left']['is_quick'],
                'swipe': left_swipe,
                'tap': left_tap,
                'rotation_velocity': self._get_palm_rotation_velocity('left'),
                'palm_angle': self._get_palm_angle('left'),
                'landmarks': self.left_hand['landmarks'] if self.left_hand else None
            },
            'right_hand': {
                'detected': self.right_hand is not None,
                'gesture': self.right_gesture,
                'position': self.right_hand['position'] if self.right_hand else (0, 0),
                'confidence': self.right_hand['confidence'] if self.right_hand else 0.0,
                'duration': timing_info['right']['duration'],
                'is_quick': timing_info['right']['is_quick'],
                'swipe': right_swipe,
                'tap': right_tap,
                'rotation_velocity': self._get_palm_rotation_velocity('right'),
                'palm_angle': self._get_palm_angle('right'),
                'landmarks': self.right_hand['landmarks'] if self.right_hand else None
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

    def get_debug_measurements(self, landmarks) -> Dict:
        """Get detailed measurements for debugging gesture detection."""
        if not landmarks or len(landmarks) < 21:
            return {}

        # Key landmark positions
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        index_tip = landmarks[8]
        index_mcp = landmarks[5]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]

        # Calculate key distances
        thumb_wrist_dist = math.sqrt(
            (thumb_tip[0] - wrist[0])**2 + (thumb_tip[1] - wrist[1])**2
        )
        thumb_wrist_vertical = thumb_tip[1] - wrist[1]  # Negative = thumb above wrist

        thumb_index_dist = math.sqrt(
            (thumb_tip[0] - index_tip[0])**2 + (thumb_tip[1] - index_tip[1])**2
        )

        thumb_horizontal = abs(thumb_tip[0] - thumb_mcp[0])
        hand_width = abs(index_tip[0] - pinky_tip[0])

        # Per-finger states
        fingers_extended = {
            'thumb': abs(thumb_tip[0] - thumb_mcp[0]) > self.FINGER_EXTEND_THRESHOLD,
            'index': index_tip[1] < index_mcp[1] - self.FINGER_EXTEND_THRESHOLD,
            'middle': middle_tip[1] < landmarks[9][1] - self.FINGER_EXTEND_THRESHOLD,
            'ring': ring_tip[1] < landmarks[13][1] - self.FINGER_EXTEND_THRESHOLD,
            'pinky': pinky_tip[1] < landmarks[17][1] - self.FINGER_EXTEND_THRESHOLD
        }

        fingers_folded = {
            'thumb': abs(thumb_tip[0] - thumb_mcp[0]) < 0.06 and thumb_tip[1] > wrist[1] - 0.05,
            'index': index_tip[1] > index_mcp[1],
            'middle': middle_tip[1] > landmarks[9][1],
            'ring': ring_tip[1] > landmarks[13][1],
            'pinky': pinky_tip[1] > landmarks[17][1]
        }

        # Gesture-specific conditions (updated to match new thresholds)
        thumbs_up_conditions = {
            'thumb_above_wrist': thumb_wrist_vertical < -0.10,  # Updated from -0.08
            'thumb_extended_up': thumb_tip[1] < thumb_mcp[1] - 0.05,
            'thumb_vertical': thumb_horizontal < 0.07,
            'thumb_separated': thumb_index_dist > 0.03,  # Updated from 0.07
            'fingers_folded': sum([fingers_folded[f] for f in ['index', 'middle', 'ring', 'pinky']]) >= 3
        }

        closed_fist_conditions = {
            'NOT_thumbs_up_pose': thumb_wrist_vertical >= -0.10,  # Updated from -0.08
            'NOT_too_separated': thumb_index_dist <= 0.10,        # Updated from 0.12
            'thumb_close': abs(thumb_tip[0] - thumb_mcp[0]) < 0.07,
            'thumb_not_up': thumb_tip[1] > wrist[1] - 0.04,
            'fingers_folded': sum([fingers_folded[f] for f in ['index', 'middle', 'ring', 'pinky']]) >= 3,
            'compact': hand_width < 0.15
        }

        return {
            'distances': {
                'thumb_wrist': thumb_wrist_dist,
                'thumb_wrist_vertical': thumb_wrist_vertical,
                'thumb_index': thumb_index_dist,
                'thumb_horizontal': thumb_horizontal,
                'hand_width': hand_width
            },
            'fingers_extended': fingers_extended,
            'fingers_folded': fingers_folded,
            'thumbs_up_conditions': thumbs_up_conditions,
            'closed_fist_conditions': closed_fist_conditions,
            'thresholds': {
                'thumb_above_wrist_threshold': -0.10,  # Updated from -0.08
                'thumb_separated_threshold': 0.03,     # Updated from 0.07
                'fist_reject_thumb_up_threshold': -0.10,  # Updated from -0.08
                'fist_reject_separated_threshold': 0.10,  # Updated from 0.12
                'hand_compact_threshold': 0.15
            }
        }