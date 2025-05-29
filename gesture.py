import numpy as np
import math

class GestureRecognizer:
    def __init__(self, sensitivity=1.0):
        """Initialize the gesture recognizer.
        
        Args:
            sensitivity: Sensitivity multiplier for gesture detection thresholds
        """
        self.sensitivity = sensitivity
        self.gestures = {
            'pinch': False,            # Volume control
            'finger_spread': 0.0,      # Pitch control (0.0 - 1.0)
            'palm_tilt': 0.0,          # Tempo control (-1.0 to 1.0)
            'palm_height': 0.0,        # Filter control (0.0 - 1.0)
            'play_pause': False,       # Play/pause toggle
            'fist': False,             # Stop/silence
            'pointing': False,         # Track selection
            'circular': False,         # Loop control
        }
        self.prev_palm_center = None
        self.palm_movement = (0, 0)
        self.smooth_factor = 0.5       # Smoothing factor for continuous controls
        
        # Gesture history for smoothing
        self.history = {gesture: [] for gesture in self.gestures}
        self.history_size = 5
        
    def update_gestures(self, hands_data):
        """Update gesture states based on the hand landmark data.
        
        Args:
            hands_data: List of hand data dictionaries from HandTracker
            
        Returns:
            Dictionary of detected gestures and their values
        """
        if not hands_data:
            # Gradually reset gestures when no hands are detected
            for gesture in self.gestures:
                if isinstance(self.gestures[gesture], bool):
                    self.gestures[gesture] = False
                else:
                    # Smoothly return continuous gestures to neutral
                    current = self.gestures[gesture]
                    if gesture == 'palm_tilt':
                        neutral = 0.0
                    else:
                        neutral = 0.0
                    self.gestures[gesture] = current * 0.9 + neutral * 0.1
            return self.gestures
        
        # Use the first detected hand for gestures
        hand = hands_data[0]
        landmarks = hand['landmarks']
        
        # Process each gesture type
        self._detect_pinch(landmarks)
        self._detect_finger_spread(landmarks)
        self._detect_palm_tilt(landmarks)
        self._detect_palm_height(landmarks, hand['bounding_box'])
        self._detect_play_pause(landmarks)
        self._detect_fist(landmarks)
        self._detect_pointing(landmarks)
        self._detect_circular_motion(landmarks)
        
        # Apply smoothing to continuous gestures
        self._apply_smoothing()
        
        return self.gestures
    
    def _detect_pinch(self, landmarks):
        """Detect pinch gesture (thumb tip to index tip).
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
        """
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        # Calculate distance between thumb and index fingertips
        distance = math.sqrt(
            (thumb_tip[0] - index_tip[0])**2 + 
            (thumb_tip[1] - index_tip[1])**2
        )
        
        # Get average hand size for normalization
        hand_size = self._get_hand_size(landmarks)
        normalized_distance = distance / hand_size
        
        # Pinch threshold (lower values = more sensitive)
        threshold = 0.1 * (1 / self.sensitivity)
        
        # Update pinch state
        self.gestures['pinch'] = normalized_distance < threshold
    
    def _detect_finger_spread(self, landmarks):
        """Detect finger spread for pitch control.
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
        """
        # Get fingertip landmarks
        fingertips = [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        
        # Calculate average distance between adjacent fingertips
        total_distance = 0
        pairs = [(fingertips[i], fingertips[i+1]) for i in range(len(fingertips)-1)]
        
        for p1, p2 in pairs:
            distance = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
            total_distance += distance
        
        avg_distance = total_distance / len(pairs) if pairs else 0
        
        # Normalize by hand size
        hand_size = self._get_hand_size(landmarks)
        normalized_spread = min(1.0, avg_distance / (hand_size * 0.7))
        
        # Update finger spread value (smooth transition)
        self.gestures['finger_spread'] = normalized_spread
    
    def _detect_palm_tilt(self, landmarks):
        """Detect palm tilt for tempo control.
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
        """
        # Calculate palm normal vector using wrist and middle finger MCP
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        
        # Calculate vectors representing the palm plane
        v1 = np.array([landmarks[5][0] - wrist[0], landmarks[5][1] - wrist[1], landmarks[5][2] - wrist[2]])
        v2 = np.array([landmarks[17][0] - wrist[0], landmarks[17][1] - wrist[1], landmarks[17][2] - wrist[2]])
        
        # Calculate normal vector of palm plane
        normal = np.cross(v1, v2)
        normal = normal / np.linalg.norm(normal) if np.linalg.norm(normal) > 0 else np.array([0, 0, 1])
        
        # Calculate tilt by comparing to vertical axis
        vertical = np.array([0, 0, 1])
        tilt_angle = np.arccos(np.dot(normal, vertical) / (np.linalg.norm(normal) * np.linalg.norm(vertical)))
        
        # Convert to range -1.0 to 1.0 based on left-right tilt
        # Determine left-right tilt direction using the normal's x component
        direction = 1 if normal[0] > 0 else -1
        tilt_value = direction * min(1.0, tilt_angle / (np.pi/2))
        
        # Update palm tilt value
        self.gestures['palm_tilt'] = tilt_value
    
    def _detect_palm_height(self, landmarks, bounding_box):
        """Detect vertical palm position for filter control.
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
            bounding_box: (xmin, ymin, xmax, ymax) of the hand
        """
        # Calculate center of palm
        palm_center_y = (landmarks[0][1] + landmarks[9][1]) / 2
        
        # Normalize height based on camera frame height (assuming height = 1.0)
        # Higher values = lower position, so invert
        normalized_height = 1.0 - min(1.0, max(0.0, palm_center_y))
        
        # Update palm height value
        self.gestures['palm_height'] = normalized_height
    
    def _detect_play_pause(self, landmarks):
        """Detect palm up/down for play/pause control.
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
        """
        # Use palm facing direction
        palm_facing_up = landmarks[9][1] < landmarks[0][1]  # Middle MCP above wrist
        
        # Check if palm is clearly facing up/down (z value of landmarks)
        palm_facing_camera = landmarks[9][2] < -0.01  # Negative z value points toward camera
        
        # Update play/pause state
        self.gestures['play_pause'] = palm_facing_up and palm_facing_camera
    
    def _detect_fist(self, landmarks):
        """Detect closed fist gesture.
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
        """
        # Check if all fingertips are close to the palm
        palm_center = np.mean([landmarks[0], landmarks[5], landmarks[9], landmarks[13], landmarks[17]], axis=0)
        fingertips = [landmarks[4], landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        
        distances = [
            math.sqrt((tip[0] - palm_center[0])**2 + (tip[1] - palm_center[1])**2)
            for tip in fingertips
        ]
        
        hand_size = self._get_hand_size(landmarks)
        normalized_distances = [d / hand_size for d in distances]
        
        # Fist threshold
        threshold = 0.2 * (1 / self.sensitivity)
        
        # Update fist state
        self.gestures['fist'] = all(d < threshold for d in normalized_distances)
    
    def _detect_pointing(self, landmarks):
        """Detect pointing gesture (index finger extended, others closed).
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
        """
        # Check if index finger is extended
        index_extended = landmarks[8][1] < landmarks[6][1]  # Tip above PIP
        
        # Check if other fingers are not extended
        middle_closed = landmarks[12][1] > landmarks[10][1]
        ring_closed = landmarks[16][1] > landmarks[14][1]
        pinky_closed = landmarks[20][1] > landmarks[18][1]
        
        # Update pointing state
        self.gestures['pointing'] = index_extended and middle_closed and ring_closed and pinky_closed
    
    def _detect_circular_motion(self, landmarks):
        """Detect circular motion of the hand.
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
        """
        # Calculate center of palm
        palm_center = np.mean([landmarks[0], landmarks[5], landmarks[9], landmarks[13], landmarks[17]], axis=0)
        
        # Track palm movement
        if self.prev_palm_center is not None:
            dx = palm_center[0] - self.prev_palm_center[0]
            dy = palm_center[1] - self.prev_palm_center[1]
            self.palm_movement = (dx, dy)
        
        self.prev_palm_center = palm_center
        
        # Detect circular motion (simplified implementation)
        # A more robust implementation would track multiple positions and analyze the path
        motion_magnitude = math.sqrt(self.palm_movement[0]**2 + self.palm_movement[1]**2)
        
        # Threshold for significant movement
        if motion_magnitude > 10:
            # Here we'd need a more complex algorithm to detect actual circular motion
            # This is a placeholder that randomly triggers circular gesture
            # In a real implementation, you'd track points over time and fit to a circle
            self.gestures['circular'] = np.random.random() < 0.05
        else:
            self.gestures['circular'] = False
    
    def _get_hand_size(self, landmarks):
        """Calculate approximate hand size for normalization.
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
            
        Returns:
            Estimated hand size (distance from wrist to middle fingertip)
        """
        wrist = landmarks[0]
        middle_tip = landmarks[12]
        
        return math.sqrt(
            (wrist[0] - middle_tip[0])**2 + 
            (wrist[1] - middle_tip[1])**2
        )
    
    def _apply_smoothing(self):
        """Apply smoothing to continuous gesture values."""
        for gesture, value in self.gestures.items():
            if not isinstance(value, bool):
                # Add current value to history
                self.history[gesture].append(value)
                
                # Keep history at fixed size
                if len(self.history[gesture]) > self.history_size:
                    self.history[gesture].pop(0)
                
                # Apply exponential smoothing
                if self.history[gesture]:
                    smoothed_value = sum(self.history[gesture]) / len(self.history[gesture])
                    self.gestures[gesture] = (
                        self.smooth_factor * value + 
                        (1 - self.smooth_factor) * smoothed_value
                    )


def main():
    """Demo function to test the gesture recognizer with mock data."""
    # Create mock hand landmarks data
    mock_landmarks = [(i * 10, i * 10, 0) for i in range(21)]
    mock_bbox = (0, 0, 200, 200)
    mock_hand_data = {
        'landmarks': mock_landmarks,
        'bounding_box': mock_bbox,
        'hand_type': 'Right',
        'hand_confidence': 0.95
    }
    
    recognizer = GestureRecognizer()
    gestures = recognizer.update_gestures([mock_hand_data])
    
    print("Detected gestures:")
    for gesture, value in gestures.items():
        print(f"  {gesture}: {value}")


if __name__ == "__main__":
    main()