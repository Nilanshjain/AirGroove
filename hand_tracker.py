import cv2
import mediapipe as mp
import numpy as np
import time

class HandTracker:
    def __init__(self, max_hands=2, detection_confidence=0.7, tracking_confidence=0.7):
        """Initialize the hand tracking module.
        
        Args:
            max_hands: Maximum number of hands to detect
            detection_confidence: Minimum confidence value for hand detection
            tracking_confidence: Minimum confidence value for landmark tracking
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Performance metrics
        self.prev_frame_time = 0
        self.fps = 0
        
    def find_hands(self, frame, draw=True):
        """Process the frame and detect hands.
        
        Args:
            frame: Input RGB image/frame
            draw: Whether to draw landmarks on the image
            
        Returns:
            processed_frame: Frame with drawings if draw=True
            results: Raw detection results from MediaPipe
        """
        # Calculate FPS
        current_time = time.time()
        self.fps = 1 / (current_time - self.prev_frame_time) if self.prev_frame_time > 0 else 0
        self.prev_frame_time = current_time
        
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame to find hands
        results = self.hands.process(rgb_frame)
        
        if draw and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
        # Add FPS counter
        cv2.putText(frame, f"FPS: {int(self.fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return frame, results
    
    def find_landmark_positions(self, results, img_shape):
        """Extract landmark positions from the detection results.
        
        Args:
            results: Raw detection results from MediaPipe
            img_shape: Shape of the input image (height, width)
            
        Returns:
            hands_data: List of dictionaries containing hand information
                Each dict contains:
                - 'landmarks': List of (x,y,z) coordinates for each landmark
                - 'bounding_box': (xmin, ymin, xmax, ymax)
                - 'hand_type': 'Left' or 'Right'
                - 'hand_confidence': Confidence score
        """
        hands_data = []
        height, width = img_shape[:2]
        
        if not results.multi_hand_landmarks:
            return hands_data
            
        for idx, (hand_landmarks, handedness) in enumerate(
            zip(results.multi_hand_landmarks, results.multi_handedness)
        ):
            hand_data = {
                'landmarks': [],
                'bounding_box': None,
                'hand_type': handedness.classification[0].label,
                'hand_confidence': handedness.classification[0].score
            }
            
            # Extract landmark positions
            x_coordinates = []
            y_coordinates = []
            
            for landmark in hand_landmarks.landmark:
                x, y, z = landmark.x * width, landmark.y * height, landmark.z
                hand_data['landmarks'].append((x, y, z))
                x_coordinates.append(x)
                y_coordinates.append(y)
            
            # Calculate bounding box
            x_min, x_max = int(min(x_coordinates)), int(max(x_coordinates))
            y_min, y_max = int(min(y_coordinates)), int(max(y_coordinates))
            hand_data['bounding_box'] = (x_min, y_min, x_max, y_max)
            
            hands_data.append(hand_data)
            
        return hands_data
    
    def calculate_finger_distances(self, landmarks):
        """Calculate distances between finger tips and the wrist.
        
        Args:
            landmarks: List of (x,y,z) landmark coordinates
            
        Returns:
            Dictionary of distances between fingertips and wrist
        """
        # MediaPipe hand landmark indices:
        # Wrist: 0
        # Thumb tip: 4
        # Index tip: 8
        # Middle tip: 12
        # Ring tip: 16
        # Pinky tip: 20
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        distances = {
            'thumb_wrist': self._distance(thumb_tip, wrist),
            'index_wrist': self._distance(index_tip, wrist),
            'middle_wrist': self._distance(middle_tip, wrist),
            'ring_wrist': self._distance(ring_tip, wrist),
            'pinky_wrist': self._distance(pinky_tip, wrist),
            'thumb_index': self._distance(thumb_tip, index_tip),
        }
        
        return distances
    
    def _distance(self, point1, point2):
        """Calculate Euclidean distance between two points."""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def release(self):
        """Release the MediaPipe hands object."""
        self.hands.close()


def main():
    """Demo function to test the hand tracker."""
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue
            
        # Flip the image horizontally for a selfie-view display
        frame = cv2.flip(frame, 1)
        
        # Process the frame
        processed_frame, results = tracker.find_hands(frame)
        
        # Get landmark positions
        hands_data = tracker.find_landmark_positions(results, frame.shape)
        
        # Display information for each detected hand
        for i, hand in enumerate(hands_data):
            hand_type = hand['hand_type']
            confidence = hand['hand_confidence']
            
            # Calculate finger distances
            distances = tracker.calculate_finger_distances(hand['landmarks'])
            
            # Draw bounding box
            x_min, y_min, x_max, y_max = hand['bounding_box']
            cv2.rectangle(processed_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            
            # Print hand type and confidence
            cv2.putText(
                processed_frame, 
                f"{hand_type} Hand ({confidence:.2f})", 
                (x_min, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
            )
        
        cv2.imshow('MediaPipe Hands', processed_frame)
        if cv2.waitKey(5) & 0xFF == 27:  # Press ESC to exit
            break
            
    tracker.release()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()