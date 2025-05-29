import cv2
import time
import threading
from hand_tracker import HandTracker
from gesture import GestureRecognizer
from audio_engine import AudioEngine
from ui_manager import UIManager

class AirGroove:
    def __init__(self):
        """Initialize the AirGroove application."""
        # Initialize components
        self.hand_tracker = HandTracker()
        self.gesture_recognizer = GestureRecognizer()
        self.audio_engine = AudioEngine()
        self.ui_manager = UIManager()
        
        # Set up callbacks
        self.audio_engine.on_status_changed = self._on_audio_status_changed
        self.ui_manager.on_control_changed = self._on_ui_control_changed
        self.ui_manager.on_file_selected = self._on_file_selected
        
        # Application state
        self.running = False
        self.cap = None
        
    def start(self):
        """Start the AirGroove application."""
        if self.running:
            return
            
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam")
            return
            
        # Start UI
        self.ui_manager.start()
        
        # Start main loop
        self.running = True
        self._main_loop()
        
    def stop(self):
        """Stop the AirGroove application."""
        self.running = False
        
        # Release resources
        if self.cap:
            self.cap.release()
            
        # Stop components
        self.hand_tracker.release()
        self.audio_engine.stop()
        self.ui_manager.stop()
        
    def _main_loop(self):
        """Main application loop."""
        while self.running:
            # Read webcam frame
            success, frame = self.cap.read()
            if not success:
                print("Error: Could not read frame")
                break
                
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Process frame with hand tracker
            processed_frame, results = self.hand_tracker.find_hands(frame)
            
            # Get hand landmark positions
            hands_data = self.hand_tracker.find_landmark_positions(results, frame.shape)
            
            # Update gesture recognition
            gestures = self.gesture_recognizer.update_gestures(hands_data)
            
            # Map gestures to audio controls
            self._map_gestures_to_audio(gestures)
            
            # Update UI
            self.ui_manager.update_frame(processed_frame)
            self.ui_manager.update_gestures(gestures)
            
            # Render UI
            if not self.ui_manager.render():
                break
                
            # Control frame rate
            time.sleep(1/30)  # Target 30 FPS
            
    def _map_gestures_to_audio(self, gestures):
        """Map detected gestures to audio controls."""
        # Volume control (pinch gesture)
        if gestures['pinch']:
            # Calculate pinch intensity based on distance
            pinch_intensity = 1.0 - min(1.0, gestures.get('pinch_intensity', 0.5))
            self.audio_engine.set_volume(pinch_intensity)
            
        # Pitch control (finger spread)
        if gestures['finger_spread'] > 0:
            self.audio_engine.set_pitch(gestures['finger_spread'])
            
        # Tempo control (palm tilt)
        if abs(gestures['palm_tilt']) > 0.1:
            self.audio_engine.set_tempo(gestures['palm_tilt'])
            
        # Filter control (palm height)
        if gestures['palm_height'] > 0:
            self.audio_engine.set_filter(gestures['palm_height'])
            
        # Play/Pause control
        if gestures['play_pause']:
            self.audio_engine.toggle_play_pause()
            
        # Stop control (fist)
        if gestures['fist']:
            self.audio_engine.stop()
            
    def _on_audio_status_changed(self, status):
        """Handle audio status updates."""
        self.ui_manager.update_audio_status(status)
        
    def _on_ui_control_changed(self, control):
        """Handle UI control events."""
        if 'play_pause' in control:
            self.audio_engine.toggle_play_pause()
            
    def _on_file_selected(self, file_path):
        """Handle audio file selection."""
        self.audio_engine.load_track(file_path)
        self.audio_engine.play()

def main():
    """Main entry point."""
    app = AirGroove()
    try:
        app.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        app.stop()

if __name__ == "__main__":
    main()
