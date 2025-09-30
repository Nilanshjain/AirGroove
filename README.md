# 🎵 AirGroove DJ - Gesture-Controlled Music Mixing

AirGroove DJ is an innovative gesture-controlled DJ mixing application that transforms your webcam into a powerful music mixing interface. Using advanced computer vision and hand tracking technology, you can control audio playback and apply DJ-style effects through intuitive hand gestures - no physical equipment needed!

## ✨ Features

### Core Functionality
- **Real-time Hand Tracking**: Utilizes MediaPipe for accurate hand detection and tracking
- **Precision Gesture Recognition**: Rule-based detection using geometric analysis of hand landmarks
- **Web-based Interface**: Modern HTML5/CSS3/JavaScript frontend with real-time WebSocket communication
- **Dual-deck Audio System**: Independent track control with crossfading capabilities
- **Mode-based Controls**: Specialized FX, Loop, and Scratch modes for different DJ techniques
- **Visual Gesture Cursor**: Palm-style cursor that follows hand movement with emoji feedback
- **Gesture Smoothing**: Kalman filtering for stable and accurate gesture detection
- **Quick Gesture Actions**: Instant button activation for common controls

### Supported Gestures

1. **✋ Open Palm (Browsing)**
   - Default state for navigating the interface
   - Shows green cursor when hand is detected

2. **✊ Closed Fist (Selection/Action)**
   - Mode selection when hovering over buttons
   - Master control for system actions
   - Shows red cursor with pulsing animation

3. **👌 Pinch (Deck A Control)**
   - Play/Pause Deck A
   - Mode-specific parameter control (filter, loop length, pitch bend)
   - Shows orange cursor

4. **👉 Pointer (Deck B Control)**
   - Play/Pause Deck B
   - Mode-specific parameter control (effect mix, loop position, scratch speed)
   - Shows blue cursor

5. **✌️ Two Fingers (Stop All)**
   - Stop all decks
   - Mode-specific dual parameter control (reverb+delay, loop roll, crossfader)
   - Shows purple cursor

## 🔧 Installation

### Prerequisites
- Python 3.10 or higher
- Webcam/camera
- Modern web browser (Chrome, Firefox, Safari, Edge)
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
python main_precision.py
```
This starts the full AirGroove DJ interface with web UI.

3. **Web interface will open automatically** in your default browser at `file:///path/to/AirGroove/web/index.html`

### Control Modes

#### 🎛️ FX Mode
- **Pinch**: Filter control (Y-axis movement)
- **Pointer**: Effect mix (X-axis movement)  
- **Two Fingers**: Reverb (X) + Delay (Y) control

#### 🔄 Loop Mode
- **Pinch**: Loop length control (X-axis)
- **Pointer**: Loop position (X-axis)
- **Two Fingers**: Loop roll effect (Y-axis)

#### 🎧 Scratch Mode
- **Pinch**: Pitch bend (Y-axis, centered)
- **Pointer**: Scratch speed (X-axis, centered)
- **Two Fingers**: Crossfader control (X-axis)

### Keyboard Controls (Backup)

- **`Space`** - Play/Pause Deck A
- **`O`** - Load demo track
- **`1`** - Select FX Mode
- **`2`** - Select Loop Mode
- **`3`** - Select Scratch Mode
- **`Q`** - Quit application

### Loading Audio Files

1. Use the web interface to load tracks
2. Or press `O` to load demo tracks
3. Supported formats: MP3, WAV, OGG, FLAC

## 📁 Project Structure

```
AirGroove/
├── main_precision.py       # Main application entry point
├── src/                    # Core Python modules
│   ├── precision_gestures.py    # Gesture recognition engine
│   ├── gesture_smoother.py      # Gesture smoothing algorithms
│   ├── web_audio_engine.py      # Audio processing system
│   └── websocket_enhanced.py    # Real-time communication
├── web/                    # Frontend web interface
│   ├── index.html          # Main DJ interface
│   ├── css/                # Styling and animations
│   │   ├── dj-layout.css   # Main interface layout
│   │   ├── gestures.css     # Gesture cursor styling
│   │   ├── animations.css   # UI animations
│   │   └── gesture-buttons.css # Button styling
│   └── js/                 # JavaScript functionality
│       ├── main.js         # Main application controller
│       ├── gesture-ui.js   # Gesture UI interaction
│       ├── websocket-client.js # WebSocket communication
│       └── waveform.js     # Audio visualization
├── audio/                  # Sample audio files
│   ├── Ainozama.mp3       # Demo track 1
│   └── pianos-by-jtwayne-7-174717.mp3 # Demo track 2
├── test_gestures.py        # Gesture testing utility
├── test_cursor.html        # Cursor testing tool
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

### Module Description

- **`main_precision.py`**: Main application orchestrator with WebSocket server and gesture mapping
- **`precision_gestures.py`**: Rule-based gesture recognition using MediaPipe landmarks
- **`gesture_smoother.py`**: Kalman filtering for stable gesture detection
- **`web_audio_engine.py`**: Dual-deck audio system with effects and real-time processing
- **`websocket_enhanced.py`**: Real-time communication between Python backend and web frontend
- **`test_gestures.py`**: Standalone gesture testing without audio dependencies
- **Web Interface**: Modern HTML5/CSS3/JavaScript frontend with real-time gesture feedback

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
- **OpenCV**: Video processing and debug visualization
- **Pygame**: Audio playback and real-time processing
- **WebSocket**: Real-time communication between Python and web frontend
- **Librosa**: Audio analysis and waveform generation
- **NumPy**: Numerical operations and signal processing

### Architecture
- **Backend**: Python with MediaPipe for gesture recognition, Pygame for audio
- **Frontend**: Pure HTML5/CSS3/JavaScript with WebSocket client
- **Communication**: WebSocket server for bidirectional real-time data exchange
- **Gesture Recognition**: Rule-based detection using geometric analysis of hand landmarks

### Advanced Features
- **Precision Gesture Recognition**: No machine learning models - pure mathematical calculations
- **Gesture Smoothing**: Kalman filtering for stable and accurate detection
- **Visual Gesture Cursor**: Palm-style cursor with emoji feedback that follows hand movement
- **Mode-based Control System**: Specialized FX, Loop, and Scratch modes
- **Dual-deck Audio Engine**: Independent track control with crossfading
- **Real-time WebSocket Communication**: Low-latency data synchronization
- **Quick Gesture Actions**: Instant button activation for common controls

## 🛠️ Troubleshooting

### Common Issues

**Gestures not detected?**
- Check lighting conditions - ensure hands are well-lit
- Ensure hand is clearly visible in camera frame
- Run `python test_gestures.py` to verify detection
- Check camera permissions and webcam availability

**Cursor not visible in web interface?**
- Open `test_cursor.html` in browser to test cursor styling
- Check browser console for JavaScript errors
- Ensure WebSocket connection is established (check connection status in footer)

**Audio not playing?**
- Verify audio file format is supported (MP3, WAV, OGG, FLAC)
- Check system audio settings and volume
- Ensure no other applications are using the audio device
- Try loading demo tracks with `O` key

**WebSocket connection issues?**
- Check if port 8765 is available
- Ensure firewall allows WebSocket connections
- Try refreshing the web page
- Check browser console for connection errors

**Performance issues?**
- Close other applications to free up CPU/memory
- Reduce camera resolution in `main_precision.py` if needed
- Check CPU usage and ensure adequate resources
- Ensure proper lighting for gesture detection

**False gesture detection?**
- Practice making gestures more distinct and deliberate
- Check debug output in console for gesture states
- Ensure proper hand positioning (1-2 feet from camera)
- Use `test_gestures.py` to practice gesture recognition

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

- [ ] Additional gesture types (thumbs up, peace sign, etc.)
- [ ] Multi-track mixing support (3+ tracks)
- [ ] Recording capabilities and session saving
- [ ] MIDI output support for external hardware
- [ ] Gesture customization interface
- [ ] Effects presets system
- [ ] Beat matching algorithm and BPM sync
- [ ] Enhanced waveform visualization
- [ ] Network collaboration mode for remote DJing
- [ ] Mobile companion app
- [ ] Voice command integration
- [ ] Advanced audio effects (EQ, filters, etc.)
- [ ] Gesture learning mode for custom gestures
- [ ] Performance analytics and gesture statistics

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Run `python test_gestures.py` for gesture testing
- Open `test_cursor.html` for cursor testing

## 🙏 Acknowledgments

- **MediaPipe team** for the hand tracking technology
- **OpenCV community** for computer vision tools
- **Pygame developers** for audio processing capabilities
- **Librosa team** for audio analysis and manipulation
- **WebSocket community** for real-time communication standards

## 🎯 Use Cases

- **Live DJ performances** with gesture-controlled mixing
- **Music production** with hands-free parameter control
- **Educational purposes** for learning DJ techniques
- **Accessibility** for users with mobility limitations
- **Interactive installations** and art projects
- **Remote DJing** with web-based interface

---

**Note**: This project requires a webcam and proper lighting for optimal performance. Practice gestures using the test script before attempting full DJ controls. The web interface provides real-time feedback and is essential for the full experience.

*Made with ❤️ using Python, MediaPipe, OpenCV, and modern web technologies* 