# AirGroove - Actual Gesture Mappings (Verified from Code)

This document contains the **actual** gesture mappings as implemented in the code, verified by reading `main_precision.py`.

## Mode Switching

**Swipe LEFT/RIGHT** → Switch between modes:
- Modes: NORMAL → FX → LOOP → SCRATCH (cycles)
- Cooldown: 500ms between mode switches

## All Modes: Play/Pause

**Closed Fist Gesture:**
- **Left hand closed fist** → Toggle play/pause Deck A
- **Right hand closed fist** → Toggle play/pause Deck B
- Uses edge detection (triggers once per fist gesture)
- Cooldown: 500ms between triggers

---

## FX Mode Gestures

### 1. Filter Type Selection - Left Hand Pointer
**Gesture:** Point with left hand index finger (only index extended)
**Control:** Y position (vertical) selects filter type
- **Top** (Y < 0.3): **Lowpass** filter
- **Middle** (0.3 ≤ Y < 0.7): **Highpass** filter
- **Bottom** (Y ≥ 0.7): **Bandpass** filter

**Effect:** Filter is automatically enabled when you point

### 2. Cutoff Frequency & Wet/Dry Mix - Right Hand Two Fingers
**Gesture:** Show two fingers with right hand (peace sign - index and middle extended)
**Control:**
- **X position (horizontal):** Cutoff frequency
  - Left (X=0): 20 Hz
  - Right (X=1): 20,000 Hz (20 kHz)
  - **Logarithmic scale** for musical response
- **Y position (vertical):** Wet/Dry mix
  - Up (Y=0): 100% wet (full effect)
  - Down (Y=1): 0% wet (dry/bypass)

### 3. Resonance (Q Factor) - Palm Rotation
**Gesture:** Rotate your palm clockwise or counter-clockwise (either hand)
**Control:** Rotation velocity maps to resonance
- **Counter-clockwise** (-180°/s): Resonance = 0.5 (minimal peak)
- **No rotation** (0°/s): Resonance = 5.0 (moderate peak)
- **Clockwise** (+180°/s): Resonance = 10.0 (sharp peak)

**Threshold:** Must rotate faster than 20°/s to trigger

---

## NORMAL Mode Gestures

### Crossfader Control - Pinch Gesture
**Gesture:** Pinch with thumb and index finger (either hand)
**Control:** X position controls crossfader
- Left (X=0): 100% Deck A
- Center (X=0.5): 50/50 mix
- Right (X=1): 100% Deck B

---

## LOOP Mode Gestures

**IMPORTANT: Loop mode gestures are currently NOT fully implemented.**
They print console messages but don't actually control the audio loop system.

### Intended Gestures (Not Working):
1. **Pointer** → Set loop IN point (only prints)
2. **Two fingers** → Set loop OUT point (only prints)
3. **Pinch** → Adjust loop length (only prints)
4. **Palm rotation** → Move loop position (only prints)

---

## SCRATCH Mode Gestures

### Palm Rotation - Vinyl Control
**Gesture:** Rotate your palm like scratching a vinyl record (either hand)
**Control:** Rotation velocity controls playback speed
- **Clockwise**: Forward playback
- **Counter-clockwise**: Reverse playback
- **Speed**: Proportional to rotation velocity

---

## Technical Notes

### Gesture Recognition Thresholds
- **Pinch threshold**: 0.04 (distance between thumb and index tip)
- **Finger fold threshold**: 0.10 (vertical distance for finger detection)
- **Swipe threshold**: 0.15 (horizontal distance for mode switching)
- **Rotation velocity threshold**: 30°/s (for scratch detection)

### Mode System
- **Current mode stored in**: `main_precision.py:current_mode`
- **Mode guard in FX control**: `web_audio_engine.py:126` checks `if self.current_mode == 'fx'`
- **Audio engine mode sync**: Mode must be set in both main app and audio engine

### Effects Processing Pipeline
1. Gesture detected → `main_precision.py:_handle_fx_mode_gestures()`
2. Calls → `audio_engine.fx_control(parameter, value)`
3. Checks → `if self.current_mode == 'fx'` (web_audio_engine.py:126)
4. Passes to → `self.sd_engine.fx_control(parameter, value)` (sounddevice_audio_engine.py:378)
5. Updates → `effects_processor.set_filter_*(value)` (effects_processor.py)
6. Applied in audio callback → `effects_processor.process_audio(mixed)` (sounddevice_audio_engine.py:294)
7. **Critical check**: `if self.effects_processor.filter_enabled:` (line 293)

### Why FX Might Not Work
1. **Mode mismatch**: Main app mode != audio engine mode
2. **Filter not enabled**: `filter_enabled` flag is False (default)
3. **No mode switch**: User didn't switch to FX mode via swipe or UI

---

## How to Test FX Mode

1. **Load a track** on Deck A (press 'o' key or use UI)
2. **Start playback** (left hand closed fist or spacebar)
3. **Switch to FX mode** (swipe right with right hand, or select in UI)
4. **Point with left hand**:
   - Move hand up → Lowpass (muffled sound)
   - Move hand middle → Highpass (tinny sound)
   - Move hand down → Bandpass (telephone sound)
5. **Show two fingers with right hand**:
   - Move horizontally → Adjust cutoff frequency (pitch/brightness)
   - Move vertically → Adjust wet/dry mix (effect intensity)
6. **Rotate palm** → Adjust resonance (peak sharpness)

### Expected Console Output
```
[FX MODE] Filter type: lowpass (Y=0.15)
[TRACE-FX] BEFORE fx_control('filter_type', lowpass)
[TRACE-FX] AFTER fx_control('filter_type', lowpass)
[TRACE-FX] BEFORE fx_control('enable', 1.0)
[EffectsProcessor] Filter enabled: lowpass @ 1000Hz
[TRACE-FX] AFTER fx_control('enable', 1.0)
[FX MODE] Cutoff: 5012Hz | Wet/Dry: 75% (X=0.65, Y=0.25)
```

---

## Accessibility Notes

### For Users with Limited Hand Mobility
- **Large gesture tolerance**: Finger fold thresholds are relaxed (0.10)
- **Distance normalization**: Gestures work at any distance from camera
- **Smoothing**: All gesture positions are smoothed over 3 frames
- **Hold-free control**: Most controls are continuous (no need to hold gestures)

### For Users with One Hand
- **Either hand works**: Most gestures can be performed with either hand
- **No simultaneous gestures required**: Each gesture is independent
- **Mode switching**: Single swipe gesture switches modes

### Alternative Control Methods
- **Web UI controls**: All FX and Loop parameters can be controlled via sliders and buttons
- **Keyboard shortcuts**:
  - Spacebar: Play/pause Deck A
  - 'o': Load track to Deck A
  - 'p': Load track to Deck B
  - 'q': Quit application

---

Generated: 2025-01-XX (verified from codebase)
