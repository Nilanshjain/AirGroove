#!/usr/bin/env python3
"""
Simple gesture recognition test to verify the precision gesture system is working.
Shows detected gestures in real-time with confidence levels.
"""

import cv2
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from precision_gestures import PrecisionGestureRecognizer
from gesture_smoother import GestureSmoother

class GestureTest:
    def __init__(self):
        print("Initializing Gesture Test...")
        self.gesture_recognizer = PrecisionGestureRecognizer()
        self.gesture_smoother = GestureSmoother(buffer_size=5, confidence_threshold=0.6)
        self.cap = None
        self.running = False

        # FPS tracking
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0

    def start(self):
        """Start the gesture test."""
        try:
            # Initialize camera
            print("Opening camera...")
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Error: Could not open camera")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            print("Camera opened successfully")
            print("Controls: Q - Quit, SPACE - Reset")
            print("Make gestures in front of the camera...")
            print("-" * 50)

            self.running = True
            self._test_loop()

        except Exception as e:
            print(f"Error starting test: {e}")
            return False

    def _test_loop(self):
        """Main test loop."""
        while self.running:
            try:
                # Read camera frame
                success, frame = self.cap.read()
                if not success:
                    print("Error reading camera frame")
                    break

                # Flip frame for mirror effect
                frame = cv2.flip(frame, 1)

                # Process gestures
                raw_gesture_state = self.gesture_recognizer.update_hands(frame)
                smoothed_gesture_state = self.gesture_smoother.smooth_gestures(raw_gesture_state)

                # Display results
                self._display_results(frame, smoothed_gesture_state)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nQuitting gesture test...")
                    break
                elif key == ord(' '):
                    print("Resetting gesture smoother...")
                    self.gesture_smoother = GestureSmoother(buffer_size=5, confidence_threshold=0.6)

                # Update FPS
                self._update_fps()

            except KeyboardInterrupt:
                print("\nKeyboard interrupt")
                break
            except Exception as e:
                print(f"Error in test loop: {e}")

        self.stop()

    def _display_results(self, frame, gesture_state):
        """Display gesture results on frame and console."""
        # Create display frame
        display_frame = frame.copy()

        # Get gesture data
        left_hand = gesture_state.get('left_hand', {})
        right_hand = gesture_state.get('right_hand', {})
        interaction_state = gesture_state.get('interaction_state', 'browsing')

        # Add text overlays
        y_offset = 30

        # FPS
        cv2.putText(display_frame, f"FPS: {self.current_fps}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y_offset += 35

        # Left hand
        left_gesture = left_hand.get('gesture', 'none')
        left_confidence = left_hand.get('confidence', 0.0)
        left_detected = left_hand.get('detected', False)

        color = (0, 255, 0) if left_detected else (0, 0, 255)
        cv2.putText(display_frame, f"Left: {left_gesture} ({left_confidence:.2f})",
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        y_offset += 30

        # Right hand
        right_gesture = right_hand.get('gesture', 'none')
        right_confidence = right_hand.get('confidence', 0.0)
        right_detected = right_hand.get('detected', False)

        color = (0, 255, 0) if right_detected else (0, 0, 255)
        cv2.putText(display_frame, f"Right: {right_gesture} ({right_confidence:.2f})",
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        y_offset += 30

        # Interaction state
        cv2.putText(display_frame, f"State: {interaction_state}",
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        y_offset += 35

        # Hand positions if detected
        if left_detected:
            pos = left_hand.get('position', (0, 0))
            x, y = int(pos[0] * frame.shape[1]), int(pos[1] * frame.shape[0])
            cv2.circle(display_frame, (x, y), 10, (255, 0, 0), -1)
            cv2.putText(display_frame, "L", (x-10, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        if right_detected:
            pos = right_hand.get('position', (0, 0))
            x, y = int(pos[0] * frame.shape[1]), int(pos[1] * frame.shape[0])
            cv2.circle(display_frame, (x, y), 10, (0, 255, 0), -1)
            cv2.putText(display_frame, "R", (x-10, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Instructions
        instructions = [
            "Q - Quit",
            "SPACE - Reset",
            "",
            "Test these gestures:",
            "- Open palm",
            "- Closed fist",
            "- Pinch (thumb+index)",
            "- Pointer (index finger)",
            "- Two fingers (index+middle)"
        ]

        start_y = frame.shape[0] - 240
        for i, instruction in enumerate(instructions):
            cv2.putText(display_frame, instruction, (10, start_y + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Show frame
        cv2.imshow('Gesture Recognition Test', display_frame)

        # Print to console every 30 frames for debugging
        if self.fps_counter % 30 == 0:
            print(f"L: {left_gesture:12} ({left_confidence:.2f}) | R: {right_gesture:12} ({right_confidence:.2f}) | State: {interaction_state}")

    def _update_fps(self):
        """Update FPS counter."""
        self.fps_counter += 1
        current_time = time.time()

        if current_time - self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = current_time

    def stop(self):
        """Stop the test."""
        self.running = False

        if self.cap:
            self.cap.release()

        if self.gesture_recognizer:
            self.gesture_recognizer.release()

        cv2.destroyAllWindows()
        print("Gesture test stopped")


def main():
    """Main entry point."""
    test = GestureTest()
    try:
        test.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        test.stop()


if __name__ == "__main__":
    main()