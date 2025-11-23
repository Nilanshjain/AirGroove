# AirGroove - FX and Loop Mode Gesture Testing Guide

## Setup

1. **Start the application:**
   ```bash
   python main_precision.py
   ```

2. **Open web interface:**
   Navigate to `http://localhost:8000` in your browser

3. **Load a track:**
   Click "LOAD TRACK" on Deck A and select any audio file

## FX Mode Testing

### How to Enter FX Mode:
- Select "FX" from the mode selector in the web UI
- The interface will show purple/violet theme

### FX Gestures (FULLY IMPLEMENTED):

#### 1. **Filter Type Selection** - Left Hand Pointer
- **Gesture:** Point with left hand (index finger extended)
- **Control:** Y position (vertical) selects filter type
  - **Top** (Y < 0.3): Lowpass filter
  - **Middle** (0.3 < Y < 0.7): Highpass filter
  - **Bottom** (Y > 0.7): Bandpass filter
- **Result:** Filter is automatically enabled when you point
- **Visual Feedback:** Web UI filter type buttons will update

#### 2. **Cutoff Frequency & Wet/Dry Mix** - Right Hand Two Fingers
- **Gesture:** Show two fingers with right hand (peace sign)
- **Control:**
  - **X position (horizontal):** Cutoff frequency
    - Left (X=0): 20 Hz
    - Right (X=1): 20,000 Hz (20 kHz)
    - Logarithmic scale
  - **Y position (vertical):** Wet/Dry mix
    - Up (Y=0): 100% wet (full effect)
    - Down (Y=1): 0% wet (dry/bypass)
- **Result:** Real-time filter cutoff and mix adjustment
- **Visual Feedback:** Frequency graph updates in web UI

#### 3. **Resonance (Q Factor)** - Palm Rotation (Either Hand)
- **Gesture:** Rotate your palm clockwise or counter-clockwise
- **Control:** Rotation speed maps to resonance
  - **Counter-clockwise** (-180°/s): Resonance = 0.5
  - **No rotation** (0°/s): Resonance = 5.0
  - **Clockwise** (+180°/s): Resonance = 10.0
- **Threshold:** Must rotate faster than 20°/s to trigger
- **Result:** Adjusts filter sharpness/peak
- **Visual Feedback:** Resonance value updates in web UI

### FX Testing Steps:

1. **Test Filter Types:**
   - Point with left hand
   - Move hand up → Lowpass filter
   - Move hand middle → Highpass filter
   - Move hand down → Bandpass filter
   - **Expected:** Console shows `[FX MODE] Filter type: lowpass/highpass/bandpass`

2. **Test Cutoff Frequency:**
   - Show two fingers with right hand
   - Move horizontally left to right
   - **Expected:** Console shows `[FX MODE] Cutoff: 20Hz ... 20000Hz`
   - **Expected:** Audio changes pitch/brightness

3. **Test Wet/Dry Mix:**
   - Keep two fingers gesture
   - Move vertically up and down
   - **Expected:** Console shows `[FX MODE] Wet/Dry: 0% ... 100%`
   - **Expected:** Effect intensity changes

4. **Test Resonance:**
   - Rotate palm clockwise/counter-clockwise
   - **Expected:** Console shows `[FX MODE] Resonance (Q): 0.5 ... 10.0`
   - **Expected:** Filter peak becomes sharper/softer

---

## Loop Mode Testing

### How to Enter Loop Mode:
- Select "LOOP" from the mode selector in the web UI
- The interface will show green theme

### Loop Gestures (FULLY IMPLEMENTED):

#### 1. **Set Loop IN Point** - Pointer (Either Hand)
- **Gesture:** Point with index finger
- **Result:** Sets loop start point at current playback position
- **Console:** `[LOOP MODE] Left/Right pointer -> Set loop IN point`
- **Backend:** `[Loop Action] Set IN point at X.XXs`

#### 2. **Set Loop OUT Point** - Two Fingers (Either Hand)
- **Gesture:** Show two fingers (peace sign)
- **Result:** Sets loop end point at current playback position
- **Console:** `[LOOP MODE] Left/Right two_fingers -> Set loop OUT point`
- **Backend:** `[Loop Action] Set OUT point at X.XXs`

#### 3. **Adjust Loop Length** - Pinch (Either Hand)
- **Gesture:** Pinch gesture (thumb and index finger together)
- **Control:** X position (horizontal) selects loop length
  - Logarithmic scale from 0.25 to 32 beats
  - Snaps to common lengths: 0.25, 0.5, 1, 2, 4, 8, 16, 32 beats
- **Result:** Changes loop length
- **Console:** `[LOOP MODE] Loop length: X beats (X=0.XX)`
- **Backend:** `[Loop Control] Loop length: X beats`

#### 4. **Enable/Disable Loop** - Palm Rotation (Either Hand)
- **Gesture:** Rotate palm clockwise or counter-clockwise
- **Control:**
  - **Clockwise** (>30°/s): Enable loop
  - **Counter-clockwise** (<-30°/s): Disable loop
- **Result:** Toggles loop on/off
- **Console:** `[LOOP MODE] Loop ENABLED/DISABLED (rotation=X.X°/s)`
- **Backend:** `[Loop Control] Loop enabled/disabled`

### Loop Testing Steps:

1. **Set Loop Points:**
   - Start playback
   - At desired start: Point finger → Sets IN point
   - At desired end: Show two fingers → Sets OUT point
   - **Expected:** Console shows IN and OUT point timestamps

2. **Test Loop Length:**
   - Pinch gesture
   - Move hand left → Shorter loops (0.25, 0.5, 1 beat)
   - Move hand right → Longer loops (8, 16, 32 beats)
   - **Expected:** Console shows loop length in beats

3. **Enable/Disable Loop:**
   - Rotate palm clockwise → Loop enabled
   - **Expected:** Track loops between IN and OUT points
   - Rotate palm counter-clockwise → Loop disabled
   - **Expected:** Track plays normally

---

## Web UI Controls (Alternative to Gestures)

Both FX and Loop modes can also be controlled via the web interface:

### FX Controls (web/js/fx-controls.js):
- Filter enable/disable button
- Filter type selector (Lowpass/Highpass/Bandpass)
- Cutoff frequency slider (20Hz - 20kHz)
- Resonance slider (0.1 - 20)
- Wet/dry mix slider (0% - 100%)
- Real-time frequency response graph

### Loop Controls (web/js/loop-controls.js):
- Loop enable/disable button
- Loop length selector (1/4, 1/2, 1, 2, 4, 8, 16, 32 beats)
- Loop position slider
- Set IN/OUT point buttons
- Loop actions: Roll, Double, Halve

---

## Troubleshooting

### Gestures Not Working:
1. Check webcam is connected
2. Ensure good lighting
3. Keep hands in frame
4. Verify console shows gesture recognition: `[Gesture] left_hand: pointer`

### FX Not Audible:
1. Verify filter is enabled (console shows `enable: 1.0`)
2. Check wet/dry mix is not 0%
3. Try extreme cutoff frequencies (20Hz or 20kHz)
4. Increase resonance for more noticeable effect

### Loop Not Working:
1. Verify loop is enabled (console shows `Loop enabled`)
2. Check IN and OUT points are set
3. Ensure track is playing
4. Try shorter loop lengths first (1-4 beats)

### WebSocket Connection Issues:
1. Check console for WebSocket errors
2. Verify server is running on port 8765
3. Refresh browser page
4. Check `[WebSocket] Client connected` message

---

## Console Output Guide

### Successful FX Mode:
```
[FX MODE] Filter type: lowpass (Y=0.15)
[FX MODE] Cutoff: 5012Hz | Wet/Dry: 75% (X=0.65, Y=0.25)
[FX MODE] Resonance (Q): 7.5 (rotation=112.3°/s)
```

### Successful Loop Mode:
```
[LOOP MODE] Left pointer -> Set loop IN point
[Loop Action] Set IN point at 12.34s
[LOOP MODE] Loop length: 4 beats (X=0.55)
[Loop Control] Loop length: 4 beats
[LOOP MODE] Loop ENABLED (rotation=45.2°/s)
[Loop Control] Loop enabled
```

---

## Implementation Status

### ✅ COMPLETED:
- FX Mode UI (HTML, CSS, JavaScript)
- FX Mode Backend (audio engine methods)
- FX Mode Gestures (filter type, cutoff, resonance, wet/dry)
- Loop Mode UI (HTML, CSS, JavaScript)
- Loop Mode Backend (audio engine methods)
- Loop Mode Gestures (IN/OUT points, length, enable/disable)
- WebSocket Communication (bidirectional)

### 🔧 PARTIALLY IMPLEMENTED:
- Loop visualization (needs deck-level loop state tracking)
- Loop roll feature (temporary loops)
- Double/Halve loop quick actions

### 📝 TODO:
- Deck-level loop state management
- Loop position tracking during playback
- BPM detection for accurate beat-synced loops

---

## Quick Test Checklist

### FX Mode:
- [ ] Point left → Filter type changes
- [ ] Two fingers right → Cutoff frequency changes
- [ ] Two fingers right (vertical) → Wet/dry mix changes
- [ ] Rotate palm → Resonance changes
- [ ] Web UI sliders update
- [ ] Frequency graph updates
- [ ] Audio sounds filtered

### Loop Mode:
- [ ] Point → Sets IN point
- [ ] Two fingers → Sets OUT point
- [ ] Pinch → Adjusts loop length
- [ ] Rotate clockwise → Enables loop
- [ ] Track loops between points
- [ ] Rotate counter-clockwise → Disables loop
- [ ] Web UI controls work

---

## Support

If you encounter issues:
1. Check console output for error messages
2. Verify all backend services are running
3. Ensure audio file is loaded
4. Test with web UI controls first
5. Then test with gestures

Enjoy testing AirGroove! 🎵🎛️
