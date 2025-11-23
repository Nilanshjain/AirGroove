# AirGroove FX Mode Implementation Roadmap

## Status: Phase 1 Complete (Foundation)

### ✅ Completed Components

1. **Dependencies Installed**
   - pedalboard v0.9.19
   - pyrubberband v0.4.0
   - pydub v0.25.1

2. **Test Audio Generator** (`src/test_audio_generator.py`)
   - 4 synthetic test tracks generated
   - Located in `audio/test_samples/`
   - Ready for testing

3. **Effects Processor** (`src/effects_processor.py`)
   - Real-time DSP filters using scipy.signal
   - Lowpass, highpass, bandpass filters
   - Adjustable cutoff frequency, resonance, wet/dry mix
   - Thread-safe operation
   - Tested and working

4. **Test Mode Configuration** (`src/test_mode.py`)
   - Auto-setup for test audio
   - Instructions and deck assignments
   - Ready to integrate

---

## ⚠️ Critical Issue: pygame.mixer Limitation

**The current pygame.mixer audio backend CANNOT apply real-time effects.**

pygame.mixer is designed for game sound effects and does not provide:
- Access to audio buffers during playback
- Real-time audio processing callbacks
- Sample-accurate control

**This means you have TWO paths forward:**

---

## Path A: Quick Prototype (Simulated Effects)

**Time: 4-6 hours | Complexity: Low | Result: Visual demo**

### What You Get:
- UI shows effect parameters changing
- Gesture controls map to sliders
- NO actual audio processing
- Good for demonstrating the interface

### Implementation:
1. Update `main_precision.py` FX gesture handlers to log parameter changes
2. Send parameters via WebSocket to frontend
3. Update frontend `main.js` to display values
4. Users can SEE effects changing but not HEAR them

### Steps:
```python
# In main_precision.py _handle_fx_mode_gestures():
if left_gesture == 'pointer':
    y_pos = left_pos[1]
    if y_pos < 0.3:
        effect_type = 'lowpass'
    elif y_pos < 0.7:
        effect_type = 'highpass'
    else:
        effect_type = 'bandpass'

    print(f"[FX MODE] Selected: {effect_type}")
    # Send to WebSocket
    self.websocket_server.broadcast_json({
        'type': 'fx_update',
        'payload': {'effect_type': effect_type}
    })
```

**Pros:** Fast, demonstrates concept, no audio engine changes
**Cons:** Not functional, can't actually hear effects

---

## Path B: Full Implementation (Real Audio Processing)

**Time: 20-30 hours | Complexity: High | Result: Fully functional**

### What You Get:
- Real-time audio filtering
- Gesture-controlled effects you can hear
- Professional DJ functionality
- Complete mode system

### Architecture Changes Needed:

```
Current (pygame):
┌──────────────┐
│ pygame.mixer │ → Audio Output
│ (no access)  │
└──────────────┘

New (sounddevice):
┌────────────┐   ┌──────────────┐   ┌──────────┐
│ Audio File │ → │ Audio Buffer │ → │ Effects  │ → Audio Output
│ (loaded)   │   │ (numpy array)│   │ Processor│
└────────────┘   └──────────────┘   └──────────┘
```

### Phase 2: Sounddevice Audio Backend (8-10 hours)

**File to create:** `src/sounddevice_audio_engine.py`

**Key Classes:**
1. `SoundDeviceAudioEngine` - Main engine
2. `SoundDeviceDeck` - Individual deck with buffer
3. `AudioCallback` - Real-time processing

**Core Features:**
- Load audio files to numpy arrays (use soundfile)
- Stream audio with sounddevice.OutputStream
- Maintain playback position
- Support play/pause/stop
- Volume control per deck
- Crossfader mixing
- Effects processing hook

**Example Structure:**
```python
import sounddevice as sd
import soundfile as sf
import numpy as np
from effects_processor import EffectsProcessor

class SoundDeviceDeck:
    def __init__(self, name):
        self.name = name
        self.audio_data = None  # numpy array
        self.sample_rate = 44100
        self.position = 0
        self.playing = False
        self.volume = 1.0

    def load_track(self, file_path):
        self.audio_data, self.sample_rate = sf.read(file_path, always_2d=True)

    def get_audio_chunk(self, num_frames):
        if not self.playing or self.audio_data is None:
            return np.zeros((num_frames, 2))

        end_pos = min(self.position + num_frames, len(self.audio_data))
        chunk = self.audio_data[self.position:end_pos]

        # Handle end of track
        if len(chunk) < num_frames:
            chunk = np.pad(chunk, ((0, num_frames - len(chunk)), (0, 0)))
            self.playing = False
            self.position = 0
        else:
            self.position = end_pos

        return chunk * self.volume

class SoundDeviceAudioEngine:
    def __init__(self):
        self.deck_a = SoundDeviceDeck('A')
        self.deck_b = SoundDeviceDeck('B')
        self.effects_processor = EffectsProcessor()
        self.crossfader_position = 0.5
        self.stream = None

    def audio_callback(self, outdata, frames, time, status):
        # Get audio from both decks
        audio_a = self.deck_a.get_audio_chunk(frames)
        audio_b = self.deck_b.get_audio_chunk(frames)

        # Apply crossfader
        import math
        angle = self.crossfader_position * (math.pi / 2)
        vol_a = math.cos(angle)
        vol_b = math.sin(angle)

        mixed = audio_a * vol_a + audio_b * vol_b

        # Apply effects
        if self.effects_processor.filter_enabled:
            mixed = self.effects_processor.process_audio(mixed)

        outdata[:] = mixed

    def start(self):
        self.stream = sd.OutputStream(
            samplerate=44100,
            channels=2,
            callback=self.audio_callback,
            blocksize=1024
        )
        self.stream.start()
```

### Phase 3: Integration (6-8 hours)

**Files to modify:**

1. **`src/web_audio_engine.py`**
   - Replace WebAudioEngine class
   - Import SoundDeviceAudioEngine
   - Update EffectsEngine to use real effects_processor
   - Connect all existing API calls

2. **`main_precision.py`**
   - Update FX gesture handlers
   - Map gestures to effects processor methods
   - Add --test-mode flag parsing
   - Auto-load test tracks in test mode

```python
# In main_precision.py
def _handle_fx_mode_gestures(self, gesture_state):
    left_gesture = gesture_state.get('left_hand', {}).get('gesture', 'none')
    left_pos = gesture_state.get('left_hand', {}).get('position', (0.5, 0.5))
    right_gesture = gesture_state.get('right_hand', {}).get('gesture', 'none')
    right_pos = gesture_state.get('right_hand', {}).get('position', (0.5, 0.5))

    # Pointer = Select filter type
    if left_gesture == 'pointer':
        y_pos = left_pos[1]
        if y_pos < 0.3:
            self.audio_engine.fx_engine.set_filter_type('lowpass')
        elif y_pos < 0.7:
            self.audio_engine.fx_engine.set_filter_type('highpass')
        else:
            self.audio_engine.fx_engine.set_filter_type('bandpass')

    # Two fingers horizontal = Cutoff frequency
    if right_gesture == 'two_fingers':
        x_pos = right_pos[0]
        # Map 0-1 to 20-20000 Hz (logarithmic)
        import math
        cutoff = 20 * math.pow(1000, x_pos)  # 20Hz to 20kHz
        self.audio_engine.fx_engine.set_filter_cutoff(cutoff)

        # Two fingers vertical = Wet/dry mix
        y_pos = right_pos[1]
        wet_dry = 1.0 - y_pos  # Invert so up = more wet
        self.audio_engine.fx_engine.set_wet_dry_mix(wet_dry)
```

3. **Test Mode Integration**
   - Add command line argument parsing
   - Load test tracks automatically
   - Switch to FX mode
   - Display instructions

```python
# In main_precision.py __init__():
import sys
self.test_mode_enabled = '--test-mode' in sys.argv

if self.test_mode_enabled:
    from test_mode import enable_test_mode
    self.test_mode = enable_test_mode()

# In start():
if self.test_mode_enabled:
    deck_a, deck_b = self.test_mode.get_deck_tracks()
    if deck_a:
        self.audio_engine.load_track('a', str(deck_a))
    if deck_b:
        self.audio_engine.load_track('b', str(deck_b))
    self.current_mode = 'fx'  # Start in FX mode
```

### Phase 4: Frontend Updates (4-6 hours)

**Files to modify:**

1. **`web/js/main.js`** (lines 578-621, FX mode UI)
   - Add real-time parameter displays
   - Show filter cutoff in Hz
   - Show wet/dry percentage
   - Add color coding for filter types

```javascript
// Update handleFXGesture() to show real values
handleFXGesture(gesture, action, value, deck) {
    switch (action) {
        case 'set_filter_type':
            const typeEl = document.getElementById('current-effect-type');
            if (typeEl) {
                typeEl.textContent = value.charAt(0).toUpperCase() + value.slice(1);
                // Color code
                typeEl.style.color = {
                    'lowpass': '#3b82f6',  // blue
                    'highpass': '#ef4444', // red
                    'bandpass': '#8b5cf6'  // purple
                }[value] || '#fff';
            }
            break;
        case 'set_cutoff':
            const cutoffEl = document.getElementById('effect-param');
            if (cutoffEl) {
                cutoffEl.textContent = `${Math.round(value)}Hz`;
            }
            break;
        case 'set_wet_dry':
            const wetDryEl = document.getElementById('effect-wet-dry');
            if (wetDryEl) {
                wetDryEl.textContent = `${Math.round(value * 100)}%`;
            }
            break;
    }
}
```

2. **`src/websocket_enhanced.py`**
   - Add FX state update messages
   - Increase update rate to 60 Hz for smooth parameter changes

### Phase 5: Testing (2-4 hours)

**Test Checklist:**

1. **Audio Playback**
   - [ ] Test tracks load successfully
   - [ ] Playback is smooth without glitches
   - [ ] Volume controls work
   - [ ] Crossfader mixes smoothly

2. **Filter Effects**
   - [ ] Lowpass: Cuts high frequencies when cutoff is low
   - [ ] Highpass: Cuts bass when cutoff is high
   - [ ] Bandpass: Isolates frequency band
   - [ ] Wet/dry mix transitions smoothly
   - [ ] No audio clicks or pops

3. **Gesture Control**
   - [ ] Pointer selects filter type
   - [ ] Two fingers adjusts cutoff
   - [ ] Two fingers adjusts wet/dry
   - [ ] UI updates in real-time

4. **Test Mode**
   - [ ] `--test-mode` flag works
   - [ ] Tracks auto-load
   - [ ] Starts in FX mode
   - [ ] Instructions display

---

## Recommended Approach

### Week 1: Foundation (DONE ✅)
- Dependencies
- Test audio
- Effects processor
- Test mode config

### Week 2: Core Audio
- Implement sounddevice backend
- Test basic playback
- Verify no audio glitches

### Week 3: Integration
- Connect effects processor
- Update gesture handlers
- Test mode integration
- Basic testing

### Week 4: Polish
- Frontend updates
- Full testing
- Documentation
- Bug fixes

---

## Quick Start for Testing Current State

Even without real-time effects, you can test what's been built:

```bash
# 1. Generate test audio
python src/test_audio_generator.py

# 2. Test effects processor
python src/effects_processor.py

# 3. Test test mode
python src/test_mode.py

# 4. Run the app (effects won't work yet, but gestures will be detected)
python main_precision.py
```

---

## Next Steps

**If you want to continue now:**
1. Start with Phase 2 (sounddevice backend)
2. Create `src/sounddevice_audio_engine.py`
3. Test it standalone before integration

**If you want to pause:**
1. The foundation is complete
2. Come back to implement Phase 2-5
3. Use this roadmap as your guide

---

## Resources

- **sounddevice docs:** https://python-sounddevice.readthedocs.io/
- **scipy.signal filters:** https://docs.scipy.org/doc/scipy/reference/signal.html
- **Current config:** `config.yaml` line 126 already specifies sounddevice backend

---

## Estimated Total Time

| Phase | Time |
|-------|------|
| Phase 1 (Done) | 4 hours |
| Phase 2 (Backend) | 10 hours |
| Phase 3 (Integration) | 8 hours |
| Phase 4 (Frontend) | 6 hours |
| Phase 5 (Testing) | 4 hours |
| **TOTAL** | **32 hours** |

This is a significant but achievable implementation. The foundation is solid, and the path forward is clear.
