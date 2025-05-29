# AirGroove: Real-Time Gesture-Based Music Control

AirGroove is an AI-powered system that allows you to control music in real-time using hand gestures captured through your webcam. No external hardware required - just your laptop's built-in camera!

## Features

- Real-time hand gesture tracking using MediaPipe
- Intuitive gesture controls for music manipulation:
  - Pinch: Volume control
  - Finger spread: Pitch control
  - Palm tilt: Tempo control
  - Palm height: Filter control
  - Palm up/down: Play/Pause
  - Fist: Stop
- Real-time audio visualization
- Support for various audio formats (MP3, WAV, OGG, FLAC)
- Low-latency audio processing
- Modern, user-friendly interface

## Requirements

- Python 3.8 or higher
- Webcam
- Audio output device

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/airgroove.git
cd airgroove
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Load an audio file:
   - Press 'O' to open the file dialog
   - Select an audio file (MP3, WAV, OGG, or FLAC)

3. Control the music using hand gestures:
   - Pinch your thumb and index finger to control volume
   - Spread your fingers to adjust pitch
   - Tilt your palm left/right to change tempo
   - Move your hand up/down to control filters
   - Show your palm up/down to play/pause
   - Make a fist to stop playback

4. Additional controls:
   - Space: Toggle play/pause
   - ESC: Exit application

## Gesture Guide

- **Volume Control**: Pinch your thumb and index finger together. The closer they are, the lower the volume.
- **Pitch Control**: Spread your fingers apart. The wider the spread, the higher the pitch.
- **Tempo Control**: Tilt your palm left or right. Left tilt slows down, right tilt speeds up.
- **Filter Control**: Move your hand up or down. Higher position = more treble, lower position = more bass.
- **Play/Pause**: Show your palm facing up to play, facing down to pause.
- **Stop**: Make a fist to stop playback.

## Troubleshooting

- If the webcam doesn't start, ensure no other application is using it
- For audio issues, check your system's audio output settings
- If gestures aren't being detected, ensure good lighting and a clear view of your hands

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 