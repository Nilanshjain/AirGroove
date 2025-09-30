AirGroove DJ is an innovative gesture-controlled DJ mixing application that transforms your webcam into a powerful music mixing interface. Using advanced computer vision and hand tracking technology, you can control audio playback and apply DJ-style effects through intuitive hand gestures - no physical equipment needed!

## ✨ Features

### Core Functionality
- **Real-time Hand Tracking**: Utilizes MediaPipe for accurate hand detection and tracking.
- **Precision Gesture Recognition**: Rule-based detection using geometric analysis of hand landmarks for high accuracy.
- **Web-based Interface**: Modern and responsive HTML5/CSS3/JavaScript frontend with real-time WebSocket communication.
- **Dual-deck Audio System**: Independent track control for two audio decks, with crossfading capabilities.
- **Mode-based Controls**: Specialized FX, Loop, and Scratch modes for a variety of DJ techniques.
- **Visual Gesture Feedback**: The UI provides instant feedback on detected gestures.
- **Gesture Smoothing**: Implements a gesture smoother for stable and accurate gesture detection, preventing jitters.
- **Direct Gesture Control**: A cursor-less system that maps gestures directly to actions for a more intuitive experience.

### Supported Gestures
1.  **✋ Open Palm (Browsing & Mode Switching)**: The default state for navigating the interface. Swipe left or right to switch between control modes.
2.  **✊ Closed Fist (Play/Pause)**: Play or pause the corresponding deck (left hand for Deck A, right hand for Deck B).
3.  **👌 Pinch (Load Track)**: Load a track onto the corresponding deck.
4.  **👉 Pointer (Sync/Cue)**: Sync or cue the track on the corresponding deck.
5.  **✌️ Two Fingers (Stop)**: Stop the corresponding deck, or stop all decks if used in a two-hand combination.

## 🔧 Installation

### Prerequisites
- Python 3.10 or higher
- A webcam
- A modern web browser (Chrome, Firefox, Safari, Edge)
- Supported OS: Windows, macOS, or Linux

### Setup Instructions

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/your-username/AirGroove.git](https://github.com/your-username/AirGroove.git)
    cd AirGroove
    ```

2.  **Create and activate a virtual environment**:
    - **Windows**:
      ```bash
      python -m venv venv
      venv\Scripts\activate
      ```
    - **macOS/Linux**:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```

3.  **Install the required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage

### Quick Start

1.  **(Recommended) Test your gestures**:
    Run the gesture test script to get familiar with the hand gestures and ensure your setup is working correctly.
    ```bash
    python test_gestures.py
    ```

2.  **Run the main application**:
    This will start the backend server and open the web interface in your default browser.
    ```bash
    python main_precision.py
    ```

3.  **Start Mixing!**
    The web interface will open automatically. Use the gestures you practiced to control the music.

### Control Modes

-   **🎛️ FX Mode**: Control audio effects like filters and reverb.
-   **🔄 Loop Mode**: Create and control audio loops.
-   **🎧 Scratch Mode**: Scratch tracks and control pitch.

## 🏛️ System Architecture

The application consists of a Python backend and a JavaScript frontend, communicating in real-time via WebSockets.