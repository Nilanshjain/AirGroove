import numpy as np
import sounddevice as sd
import soundfile as sf
import librosa
import threading
import queue
import time
from collections import deque
import os


class AudioEngine:
    def __init__(self, buffer_size=1024, sample_rate=44100, channels=2):
        """Initialize audio playback engine.
        
        Args:
            buffer_size: Audio buffer size
            sample_rate: Sample rate for audio playback
            channels: Number of audio channels (1=mono, 2=stereo)
        """
        self.buffer_size = buffer_size
        self.sample_rate = sample_rate
        self.channels = channels
        
        # Audio track data
        self.track = None
        self.track_name = ""
        self.track_duration = 0
        self.position = 0
        
        # Playback state
        self.playing = False
        self.stream = None
        self.audio_thread = None
        self.audio_queue = queue.Queue(maxsize=32)
        self.stop_event = threading.Event()
        
        # Audio parameters (controlled by gestures)
        self.volume = 1.0        # 0.0 - 1.0
        self.pitch_shift = 0.0   # Semitones, -12 to +12
        self.tempo = 1.0         # 0.5x - 2.0x
        self.filter_value = 0.5  # 0.0 - 1.0 (EQ balance)
        
        # Parameters smoothing
        self.param_history = {
            'volume': deque(maxlen=5),
            'pitch_shift': deque(maxlen=5),
            'tempo': deque(maxlen=5),
            'filter_value': deque(maxlen=5)
        }
        
        # Audio effects
        self.effects_active = {
            'filter': False
        }
        
        # Status callbacks
        self.on_status_changed = None
        
    def load_track(self, file_path):
        """Load an audio track from file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Success status (bool)
        """
        try:
            # Load audio file
            audio_data, file_sample_rate = sf.read(file_path, dtype='float32')
            
            # Convert to mono if needed
            if audio_data.ndim > 1 and self.channels == 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Convert to stereo if needed
            elif audio_data.ndim == 1 and self.channels == 2:
                audio_data = np.column_stack((audio_data, audio_data))
            
            # Resample if necessary
            if file_sample_rate != self.sample_rate:
                audio_data = librosa.resample(
                    audio_data.T, 
                    orig_sr=file_sample_rate, 
                    target_sr=self.sample_rate
                ).T
            
            self.track = audio_data
            self.track_name = os.path.basename(file_path)
            self.track_duration = len(self.track) / self.sample_rate
            self.position = 0
            
            # Report status
            if self.on_status_changed:
                self.on_status_changed({
                    'track_loaded': self.track_name,
                    'duration': self.track_duration,
                    'position': 0
                })
                
            return True
            
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return False
    
    def play(self):
        """Start or resume audio playback."""
        if self.track is None:
            print("No track loaded.")
            return
            
        if self.playing:
            return
            
        self.playing = True
        self.stop_event.clear()
        
        # Start audio processing thread if not running
        if self.audio_thread is None or not self.audio_thread.is_alive():
            self.audio_thread = threading.Thread(target=self._audio_processing_thread)
            self.audio_thread.daemon = True
            self.audio_thread.start()
        
        # Open audio stream if not open
        if self.stream is None or not self.stream.active:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                channels=self.channels,
                callback=self._audio_callback
            )
            self.stream.start()
        
        # Report status
        if self.on_status_changed:
            self.on_status_changed({'playing': True})
    
    def pause(self):
        """Pause audio playback."""
        if not self.playing:
            return
            
        self.playing = False
        
        # Report status
        if self.on_status_changed:
            self.on_status_changed({'playing': False})
    
    def toggle_play_pause(self):
        """Toggle between play and pause states."""
        if self.playing:
            self.pause()
        else:
            self.play()
    
    def stop(self):
        """Stop playback and reset position."""
        self.playing = False
        self.position = 0
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.stop_event.set()
        
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        # Report status
        if self.on_status_changed:
            self.on_status_changed({
                'playing': False,
                'position': 0
            })
    
    def seek(self, position_seconds):
        """Seek to a specific position in the track.
        
        Args:
            position_seconds: Position in seconds
        """
        if self.track is None:
            return
            
        # Ensure position is within bounds
        position_seconds = max(0, min(self.track_duration, position_seconds))
        
        # Convert to samples
        self.position = int(position_seconds * self.sample_rate)
        
        # Report status
        if self.on_status_changed:
            self.on_status_changed({'position': position_seconds})
    
    def set_volume(self, volume):
        """Set volume level.
        
        Args:
            volume: Volume level (0.0 - 1.0)
        """
        # Apply smoothing
        self.param_history['volume'].append(volume)
        smoothed_volume = sum(self.param_history['volume']) / len(self.param_history['volume'])
        
        self.volume = max(0.0, min(1.0, smoothed_volume))
        
        # Report status
        if self.on_status_changed:
            self.on_status_changed({'volume': self.volume})
    
    def set_pitch(self, pitch_value):
        """Set pitch shift value.
        
        Args:
            pitch_value: Pitch shift in semitones (-12 to +12)
        """
        # Convert from 0-1 range to semitones
        pitch_semitones = (pitch_value * 24) - 12
        
        # Apply smoothing
        self.param_history['pitch_shift'].append(pitch_semitones)
        smoothed_pitch = sum(self.param_history['pitch_shift']) / len(self.param_history['pitch_shift'])
        
        self.pitch_shift = smoothed_pitch
        
        # Report status
        if self.on_status_changed:
            self.on_status_changed({'pitch': self.pitch_shift})
    
    def set_tempo(self, tempo_value):
        """Set playback tempo.
        
        Args:
            tempo_value: Tempo multiplier (-1.0 to 1.0 where 0 is normal)
        """
        # Convert from -1 to 1 range to 0.5-2.0 tempo range
        tempo_rate = 1.0 + (tempo_value * 0.5)
        
        # Apply smoothing
        self.param_history['tempo'].append(tempo_rate)
        smoothed_tempo = sum(self.param_history['tempo']) / len(self.param_history['tempo'])
        
        self.tempo = max(0.5, min(2.0, smoothed_tempo))
        
        # Report status
        if self.on_status_changed:
            self.on_status_changed({'tempo': self.tempo})
    
    def set_filter(self, filter_value):
        """Set EQ filter value.
        
        Args:
            filter_value: Filter balance (0.0 = more bass, 1.0 = more treble)
        """
        # Apply smoothing
        self.param_history['filter_value'].append(filter_value)
        smoothed_filter = sum(self.param_history['filter_value']) / len(self.param_history['filter_value'])
        
        self.filter_value = max(0.0, min(1.0, smoothed_filter))
        self.effects_active['filter'] = True
        
        # Report status
        if self.on_status_changed:
            self.on_status_changed({'filter': self.filter_value})
    
    def toggle_filter(self):
        """Toggle EQ filter on/off."""
        self.effects_active['filter'] = not self.effects_active['filter']
        
        # Report status
        if self.on_status_changed:
            self.on_status_changed({'filter_active': self.effects_active['filter']})
    
    def get_current_position(self):
        """Get current playback position in seconds."""
        return self.position / self.sample_rate if self.track is not None else 0
    
    def get_status(self):
        """Get current playback status."""
        return {
            'track': self.track_name,
            'duration': self.track_duration,
            'position': self.get_current_position(),
            'playing': self.playing,
            'volume': self.volume,
            'pitch': self.pitch_shift,
            'tempo': self.tempo,
            'filter': self.filter_value,
            'filter_active': self.effects_active['filter']
        }
    
    def _audio_callback(self, outdata, frames, time_info, status):
        """Audio output stream callback.
        
        This is called by sounddevice to fill the audio output buffer.
        """
        if status:
            print(f"Audio callback status: {status}")
            
        if not self.playing or self.track is None:
            outdata.fill(0)
            return
            
        try:
            # Get audio data from queue
            audio_chunk = self.audio_queue.get_nowait()
            outdata[:] = audio_chunk
        except queue.Empty:
            # Queue empty - fill with silence
            outdata.fill(0)
            print("Audio buffer underrun!")
    
    def _audio_processing_thread(self):
        """Process audio data in a separate thread."""
        while not self.stop_event.is_set():
            if not self.playing or self.track is None:
                time.sleep(0.1)
                continue
                
            # Skip if queue is full
            if self.audio_queue.full():
                time.sleep(0.01)
                continue
                
            # Get chunk of audio data
            chunk_size = int(self.buffer_size * self.tempo)
            end_pos = min(len(self.track), self.position + chunk_size)
            
            if self.position >= len(self.track):
                # End of track
                self.position = 0
                self.playing = False
                
                # Report status
                if self.on_status_changed:
                    self.on_status_changed({
                        'playing': False,
                        'position': 0
                    })
                    
                continue
                
            # Get audio chunk
            audio_chunk = self.track[self.position:end_pos].copy()
            
            # Update position
            self.position = end_pos
            
            # Apply audio effects
            audio_chunk = self._apply_effects(audio_chunk)
            
            # Resample to correct tempo if needed
            if self.tempo != 1.0:
                # Use librosa to change tempo without affecting pitch
                audio_chunk = librosa.effects.time_stretch(audio_chunk.T, rate=self.tempo).T
            
            # Ensure chunk size matches buffer size
            if len(audio_chunk) < self.buffer_size:
                # Pad with zeros if needed
                if audio_chunk.ndim == 1:
                    padding = np.zeros(self.buffer_size - len(audio_chunk))
                else:
                    padding = np.zeros((self.buffer_size - len(audio_chunk), audio_chunk.shape[1]))
                audio_chunk = np.vstack((audio_chunk, padding))
            elif len(audio_chunk) > self.buffer_size:
                # Truncate if needed
                audio_chunk = audio_chunk[:self.buffer_size]
            
            # Add to queue
            try:
                self.audio_queue.put(audio_chunk, block=False)
            except queue.Full:
                pass
    
    def _apply_effects(self, audio_chunk):
        """Apply audio effects to the chunk.
        
        Args:
            audio_chunk: Audio data
            
        Returns:
            Processed audio data
        """
        # Apply volume
        audio_chunk = audio_chunk * self.volume
        
        # Apply pitch shift if needed
        if self.pitch_shift != 0:
            # This is a simplified pitch shifting
            # For a real implementation, use librosa.effects.pitch_shift
            # Note: This is computationally expensive and might cause latency
            if audio_chunk.ndim > 1:
                # Process each channel
                channels = []
                for ch in range(audio_chunk.shape[1]):
                    shifted = librosa.effects.pitch_shift(
                        audio_chunk[:, ch], 
                        sr=self.sample_rate, 
                        n_steps=self.pitch_shift
                    )
                    channels.append(shifted)
                audio_chunk = np.column_stack(channels)
            else:
                audio_chunk = librosa.effects.pitch_shift(
                    audio_chunk, 
                    sr=self.sample_rate, 
                    n_steps=self.pitch_shift
                )
        
        # Apply EQ filter if active
        if self.effects_active['filter']:
            # Simple EQ filter (bass/treble balance)
            # For a real implementation, use proper filter design
            # This is a naive implementation for demonstration
            if audio_chunk.ndim > 1:
                # Process each channel
                for ch in range(audio_chunk.shape[1]):
                    # Low-pass filter for bass
                    bass = librosa.effects.preemphasis(audio_chunk[:, ch], coef=0.95, return_zf=False)
                    # High-pass filter for treble
                    treble = audio_chunk[:, ch] - bass
                    # Mix based on filter value
                    audio_chunk[:, ch] = (bass * (1 - self.filter_value) + 
                                          treble * self.filter_value)
            else:
                # Low-pass filter for bass
                bass = librosa.effects.preemphasis(audio_chunk, coef=0.95, return_zf=False)
                # High-pass filter for treble
                treble = audio_chunk - bass
                # Mix based on filter value
                audio_chunk = (bass * (1 - self.filter_value) + 
                               treble * self.filter_value)
        
        return audio_chunk


def main():
    """Demo function to test the audio engine."""
    import os
    
    # Create audio engine
    engine = AudioEngine()
    
    # Define status callback
    def on_status_changed(status):
        print(f"Status changed: {status}")
    
    engine.on_status_changed = on_status_changed
    
    # Load a test audio file
    test_file = input("Enter path to test audio file: ")
    if os.path.exists(test_file):
        engine.load_track(test_file)
        
        # Start playback
        engine.play()
        
        # Test controls
        print("\nControls:")
        print("  p - play/pause")
        print("  s - stop")
        print("  + - increase volume")
        print("  - - decrease volume")
        print("  f - toggle filter")
        print("  q - quit")
        
        try:
            while True:
                cmd = input("> ")
                if cmd == "p":
                    engine.toggle_play_pause()
                elif cmd == "s":
                    engine.stop()
                elif cmd == "+":
                    engine.set_volume(min(1.0, engine.volume + 0.1))
                elif cmd == "-":
                    engine.set_volume(max(0.0, engine.volume - 0.1))
                elif cmd == "f":
                    engine.toggle_filter()
                elif cmd == "q":
                    engine.stop()
                    break
        except KeyboardInterrupt:
            pass
        
        # Clean up
        engine.stop()
    else:
        print(f"File not found: {test_file}")


if __name__ == "__main__":
    main()