# 🎵 AirGroove DJ - Gesture-Controlled Music Mixing

AirGroove DJ is an innovative gesture-controlled DJ mixing application that transforms your webcam into a powerful music mixing interface. Using advanced computer vision and hand tracking technology, you can control audio playback and apply DJ-style effects through intuitive hand gestures - no physical equipment needed!

## ✨ Features

### Core Functionality
- **Real-time Hand Tracking**: Utilizes MediaPipe for accurate hand detection and tracking
- **Multi-gesture Recognition**: Supports various hand gestures for different controls
- **Audio Processing**: Real-time audio manipulation with effects and controls
- **Visual Feedback**: Interactive UI showing gesture states and audio status
- **Dual-hand Support**: Use both hands for advanced controls like crossfading
- **Kalman Filtering**: Advanced smoothing for stable gesture detection
- **Gesture Priority System**: Prevents conflicts between different gestures

### Supported Gestures

1. **✊ Fist (Pause/Resume)**
   - Make a fist to pause/resume playback
   - Highest priority gesture that blocks all others

2. **🤏 Pinch (Volume Control)**
   - Pinch thumb and index finger together
   - Move hand left/right to control volume
   - Visual feedback shows volume level in real-time

3. **☝️ Scratch (DJ Scratching)**
   - Extend index finger while curling others
   - Make circular motions for scratch effects
   - Intensity varies with motion speed

4. **🤌 Three-Finger Pinch (EQ Control)**
   - Bring thumb, index, and middle fingers together
   - Move hand up/down to adjust bass/treble balance
   - Low position = more bass, high position = more treble

5. **🙌 Two-Hand Separation (Crossfader)**
   - Use both hands to control crossfading between tracks
   - Separation distance controls the mix

## 🔧 Installation

### Prerequisites
- Python 3.10 or higher
- Webcam/camera
- Windows/macOS/Linux

### Setup Instructions

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/AirGroove.git
cd AirGroove
```

2. **Create a virtual environment**:
```bash
python -m venv venv
```

3. **Activate the virtual environment**:
- Windows:
  ```bash
  venv\Scripts\activate
  ```
- macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

4. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Quick Start

1. **Test gestures first** (recommended):
```bash
python test_gestures.py
```
This opens a gesture testing interface without audio to practice the hand gestures.

2. **Run the main application**:
```bash
python main.py
```

### Keyboard Controls

- **`Space`** - Play/Pause
- **`O`** - Open audio file
- **`B`** - Load second track for crossfading
- **`I`** - Set loop in point
- **`U`** - Set loop out point
- **`L`** - Toggle looping
- **`Q`** - Quit application

### Loading Audio Files

1. Press `O` to open file dialog
2. Select an audio file (MP3, WAV, OGG, FLAC)
3. Use gestures to control playback

## 📁 Project Structure

```
AirGroove/
├── main.py                 # Main application entry point
├── gesture.py              # Gesture recognition system with Kalman filtering
├── audio_engine.py         # Audio processing and effects engine
├── ui_manager.py           # User interface and visualization
├── test_gestures.py        # Gesture testing utility
├── requirements.txt        # Python dependencies
├── GESTURE_TESTING_GUIDE.md # Detailed gesture instructions
└── README.md              # This file
```

### Module Description

- **`main.py`**: Orchestrates all components, handles main application loop
- **`gesture.py`**: Implements advanced gesture recognition with Kalman filtering for smooth tracking
- **`audio_engine.py`**: Manages audio playback, effects, and real-time processing
- **`ui_manager.py`**: Renders visual feedback and gesture control zones
- **`test_gestures.py`**: Standalone gesture testing without audio dependencies

## 🎯 Gesture Tips

### For Best Results:
- **Good lighting** - Ensure hands are well-lit
- **Clear background** - Avoid cluttered backgrounds
- **Proper distance** - Keep hands 1-2 feet from camera
- **Deliberate gestures** - Make clear, intentional movements
- **Test first** - Use `test_gestures.py` to practice

### Gesture Priority System:
1. **Fist** - Highest priority, blocks all other gestures
2. **Pinch** - Blocks scratch and EQ gestures
3. **Scratch** - Blocks EQ gesture
4. **EQ** - Only active when no other gestures are detected

## 🔬 Technical Details

### Core Technologies
- **MediaPipe**: Hand detection and landmark tracking
- **OpenCV**: Video processing and UI rendering
- **NumPy**: Numerical operations and signal processing
- **Librosa**: Audio analysis and manipulation
- **SoundDevice/SoundFile**: Audio I/O and playback

### Advanced Features
- **Kalman Filtering**: Smooths hand tracking for stable gesture detection
- **Real-time DSP**: Low-latency audio processing
- **Gesture State Management**: Prevents false positives and conflicts
- **Multi-threading**: Separate threads for video and audio processing
- **Velocity-based Activation**: Uses hand velocity for more accurate gesture triggering

## 🛠️ Troubleshooting

### Common Issues

**Gestures not detected?**
- Check lighting conditions
- Ensure hand is clearly visible
- Review gesture instructions in GESTURE_TESTING_GUIDE.md
- Run `test_gestures.py` to verify detection

**Audio not playing?**
- Verify audio file format is supported
- Check system audio settings
- Ensure no other applications are using the audio device

**Performance issues?**
- Close other applications
- Reduce camera resolution if needed
- Check CPU usage
- Ensure Python is using hardware acceleration

**False gesture detection?**
- Practice making gestures more distinct
- Check debug output for gesture states
- Ensure proper hand positioning

## 📊 Performance Requirements

### Minimum Requirements
- **CPU**: Dual-core processor
- **RAM**: 4GB
- **Camera**: 720p resolution
- **OS**: Windows 10, macOS 10.14, Ubuntu 18.04

### Recommended Requirements
- **CPU**: Quad-core processor
- **RAM**: 8GB or more
- **Camera**: 1080p resolution
- **OS**: Latest versions

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests with `python test_gestures.py`
5. Submit a pull request

## 📝 License

This project is open source and available under the MIT License.

## 🎓 Educational Purpose

AirGroove DJ is designed for educational and entertainment purposes, demonstrating:
- Computer vision applications in music
- Real-time gesture recognition
- Audio signal processing
- Human-computer interaction design
- Machine learning in creative applications

## 🚧 Future Enhancements

- [ ] Additional gesture types
- [ ] Multi-track mixing support (3+ tracks)
- [ ] Recording capabilities
- [ ] MIDI output support
- [ ] Gesture customization interface
- [ ] Effects presets system
- [ ] Beat matching algorithm
- [ ] Waveform visualization
- [ ] BPM detection and sync
- [ ] Save/load mix sessions
- [ ] Network collaboration mode
- [ ] Mobile companion app

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Refer to GESTURE_TESTING_GUIDE.md for detailed troubleshooting
- Check existing issues for solutions

## 🙏 Acknowledgments

- MediaPipe team for the hand tracking technology
- OpenCV community for computer vision tools
- Librosa developers for audio processing capabilities

---

**Note**: This project requires a webcam and proper lighting for optimal performance. Practice gestures using the test script before attempting full DJ controls.

*Made with ❤️ using Python, MediaPipe, and OpenCV* 