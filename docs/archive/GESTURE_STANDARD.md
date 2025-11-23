# AIRGROOVE - GESTURE MAPPING STANDARD v1.0

**Status:** Production-Ready Base
**Last Updated:** November 23, 2025

---

## DESIGN PRINCIPLES

1. **Conflict-Free**: Each gesture has ONE clear purpose per mode
2. **Muscle Memory**: Common actions use same gestures across modes
3. **Safety**: Critical actions (play/pause, mode switch) require deliberate gestures
4. **Ergonomic**: Gestures are comfortable to hold for extended periods
5. **Visual Feedback**: Every mode change and gesture action has clear UI feedback

---

## CORE GESTURES (Mode-Independent)

These gestures work the SAME in ALL modes:

| Gesture | Detection | Action | Rationale |
|---------|-----------|--------|-----------|
| **Closed Fist** | All 4 fingers folded, compact hand | Play/Pause deck | Universal "stop" gesture |
| **Open Palm** | 3+ fingers extended | Ready state / Swipe detection | Neutral position |
| **Swipe UP** | Fast upward open palm | Enter FX mode | "Lift up" to effects |
| **Swipe DOWN** | Fast downward open palm | Enter LOOP mode | "Push down" to loops |
| **Swipe LEFT** | Fast leftward open palm | Previous mode (cycle) | Navigate modes |
| **Swipe RIGHT** | Fast rightward open palm | Next mode (cycle) | Navigate modes |

---

## MODE 1: NORMAL (Default)

**Purpose:** Basic DJ controls - play, mix, crossfade
**Visual Indicator:** Top bar shows "NORMAL" in white

| Hand | Gesture | Action | Notes |
|------|---------|--------|-------|
| Either | Closed Fist | Play/Pause deck | Left = Deck A, Right = Deck B |
| Either | Pinch | Crossfader control | Horizontal movement = balance |
| Either | Pointer | *Reserved for future* | Could be cue point trigger |
| Either | Two Fingers | *Reserved for future* | Could be sync/beatmatch |
| Either | Swipe UP/DOWN/LEFT/RIGHT | Mode switching | See Core Gestures |

**Crossfader Behavior:**
- Remembers last position
- Smooth tracking with 85/15 smoothing
- Works with single hand or both hands (averaged)

---

## MODE 2: FX (Effects Control)

**Purpose:** Apply and control audio effects in real-time
**Visual Indicator:** Top bar shows "FX" in cyan, effects panel visible
**Entry:** Swipe UP from any mode

| Hand | Gesture | Action | Details |
|------|---------|--------|---------|
| Either | Closed Fist | Play/Pause (inherited) | Same as NORMAL |
| Left | Pointer | Select effect (Deck A) | Point at effect in list |
| Right | Pointer | Select effect (Deck B) | Point at effect in list |
| Left | Two Fingers | Adjust effect parameter | Vertical = wet/dry, Horizontal = param |
| Right | Two Fingers | Adjust effect parameter | Vertical = wet/dry, Horizontal = param |
| Either | Palm Rotation | Effect intensity | CW = increase, CCW = decrease |
| Either | Pinch | Fine-tune selected param | More precise than two_fingers |
| Either | Swipe (any) | Mode switching | See Core Gestures |

**Available Effects:**
- Low-pass filter
- High-pass filter
- Echo/Delay
- Reverb
- Flanger
- Phaser
- Bitcrush
- Auto-filter

**Effect Parameters:**
- Wet/Dry mix (0-100%)
- Effect-specific parameter (e.g., filter cutoff, delay time)
- Feedback/Resonance (where applicable)

---

## MODE 3: LOOP (Loop Control)

**Purpose:** Create and manipulate audio loops
**Visual Indicator:** Top bar shows "LOOP" in green, loop waveform visible
**Entry:** Swipe DOWN from any mode

| Hand | Gesture | Action | Details |
|------|---------|--------|---------|
| Either | Closed Fist | Play/Pause (inherited) | Same as NORMAL |
| Left | Pointer | Set loop IN point (Deck A) | Mark start of loop |
| Right | Pointer | Set loop IN point (Deck B) | Mark start of loop |
| Left | Two Fingers | Set loop OUT point (Deck A) | Mark end of loop |
| Right | Two Fingers | Set loop OUT point (Deck B) | Mark end of loop |
| Either | Pinch | Adjust loop length | Horizontal = shrink/expand loop |
| Either | Palm Rotation | Move loop position | Shift loop forward/backward |
| Left | Swipe UP | Enable loop (Deck A) | Start looping |
| Right | Swipe UP | Enable loop (Deck B) | Start looping |
| Left | Swipe DOWN | Disable loop (Deck A) | Exit loop |
| Right | Swipe DOWN | Disable loop (Deck B) | Exit loop |
| Either | Swipe LEFT/RIGHT | Mode switching | See Core Gestures |

**Loop Lengths:**
- Auto-quantized to beat grid (1, 2, 4, 8, 16, 32 beats)
- Manual mode allows free-form loops
- Visual feedback shows loop region on waveform

---

## MODE 4: SCRATCH (Turntable Control)

**Purpose:** Vinyl-style scratching and pitch control
**Visual Indicator:** Top bar shows "SCRATCH" in orange, turntable platter visible
**Entry:** Swipe LEFT/RIGHT to cycle from LOOP mode

| Hand | Gesture | Action | Details |
|------|---------|--------|---------|
| Either | Closed Fist | Play/Pause (inherited) | Same as NORMAL |
| Left | Palm Rotation | Scratch/Spin (Deck A) | CW = forward, CCW = reverse |
| Right | Palm Rotation | Scratch/Spin (Deck B) | CW = forward, CCW = reverse |
| Left | Pinch | Pitch bend (Deck A) | Up = faster, Down = slower |
| Right | Pinch | Pitch bend (Deck B) | Up = faster, Down = slower |
| Left | Pointer | Cue point (Deck A) | Hold to pause at cue |
| Right | Pointer | Cue point (Deck B) | Hold to pause at cue |
| Left | Two Fingers | Nudge tempo up (Deck A) | Small BPM increase |
| Right | Two Fingers | Nudge tempo up (Deck B) | Small BPM increase |
| Either | Swipe (any) | Mode switching | See Core Gestures |

**Scratch Sensitivity:**
- Rotation velocity mapped to playback speed
- Dead zone at low velocities (< 10°/s)
- Max speed: 2x forward, 2x reverse
- Smooth acceleration/deceleration curves

---

## GESTURE DETECTION PARAMETERS

### Current Thresholds (Proven Working):

```python
# Finger Extension/Fold Detection
FINGER_EXTEND_THRESHOLD = 0.10
FINGER_FOLD_THRESHOLD = 0.10

# Distance Normalization (for far detection)
REFERENCE_SIZE = 0.25  # Optimal hand size
NORMALIZATION_RANGE = (0.25, 1.5)  # 4x dynamic range

# Pinch Detection
PINCH_THRESHOLD = 0.10

# Closed Fist Detection
FIST_COMPACTNESS_THRESHOLD = 0.12  # Hand width
FIST_FOLDED_FINGERS_REQUIRED = 4  # All non-thumb

# Swipe Detection
SWIPE_DISTANCE_THRESHOLD = 0.30
SWIPE_TIME_WINDOW = 0.5
SWIPE_MINIMUM_FRAMES = 5
SWIPE_VELOCITY_MIN = 0.4
SWIPE_COOLDOWN = 0.3

# Crossfader Smoothing
CROSSFADER_SMOOTHING = (0.85, 0.15)  # (old, new)
```

### Gesture Priority Order:
```
1. Closed Fist (most specific, checked first)
2. Pinch (thumb-index proximity)
3. Pointer (index extended, middle folded)
4. Two Fingers (index+middle extended, ring+pinky folded)
5. Open Palm (3+ fingers extended)
6. None (no clear gesture)
```

---

## MODE SWITCHING FLOW

```
User Action:          System Response:
────────────────────────────────────────────────
Swipe UP       →      Mode = FX
                      Show effects panel
                      Visual feedback: "FX MODE"
                      Audio feedback: Short beep (optional)

Swipe DOWN     →      Mode = LOOP
                      Show loop controls
                      Visual feedback: "LOOP MODE"
                      Audio feedback: Short beep (optional)

Swipe LEFT     →      Mode = Previous in cycle
                      Update UI accordingly
                      Visual feedback: Mode name

Swipe RIGHT    →      Mode = Next in cycle
                      Update UI accordingly
                      Visual feedback: Mode name

Double Tap     →      Mode = NORMAL (quick return)
(optional)            Reset to default state
                      Visual feedback: "NORMAL MODE"
```

**Mode Cycle:**
```
NORMAL ←→ FX ←→ LOOP ←→ SCRATCH ←→ NORMAL
   ↑                                    ↓
   └────────────────────────────────────┘
```

---

## HAND ASSIGNMENT LOGIC

### Current Implementation:
- **Left Hand = Deck A (default)**
- **Right Hand = Deck B (default)**
- **Both Hands = Averaged (for crossfader)**

### Proposed Enhancement:
- **Dominant hand preference** (user configurable)
- **Hand swap gesture** (both hands crossed = swap assignments)
- **Independent deck control** (each hand can control either deck)

---

## VISUAL FEEDBACK REQUIREMENTS

### Mode Indicators:
- **Top bar**: Current mode name (NORMAL/FX/LOOP/SCRATCH)
- **Color coding**: White/Cyan/Green/Orange
- **Icon**: Visual symbol for each mode

### Gesture Feedback:
- **Hand outline**: Shows detected landmarks
- **Gesture label**: Text showing current gesture (pointer, pinch, etc.)
- **Action indicator**: Shows what action will trigger (e.g., "CROSSFADER ACTIVE")

### Parameter Feedback:
- **Crossfader**: Slider position + percentage
- **Effect params**: Knob visualization + value
- **Loop region**: Highlighted waveform section
- **Scratch speed**: Turntable rotation visualization

---

## FUTURE ENHANCEMENTS

### Possible Additions:
1. **Tap Detection**: Quick finger tap for hot cues
2. **Hold Duration**: Different actions based on hold time
3. **Gesture Combos**: Simultaneous gestures for advanced controls
4. **Voice Commands**: Supplement gestures with speech (mode names, effects)
5. **Eye Tracking**: Look at effect/control to select it (with pointer to activate)

### Refinement Areas:
1. **Sensitivity Tuning**: Per-user calibration for gesture thresholds
2. **Latency Optimization**: Reduce detection-to-action delay
3. **False Positive Reduction**: Improve gesture distinction
4. **Fatigue Management**: Alternative gestures for long sessions

---

## TESTING & VALIDATION

### Test Cases for Each Mode:

**NORMAL Mode:**
- [ ] Closed fist plays/pauses deck A (left hand)
- [ ] Closed fist plays/pauses deck B (right hand)
- [ ] Pinch controls crossfader smoothly
- [ ] Crossfader remembers position after release
- [ ] Swipe UP switches to FX mode

**FX Mode:**
- [ ] Pointer selects effect from list
- [ ] Two fingers adjusts effect parameter
- [ ] Palm rotation controls intensity
- [ ] Pinch fine-tunes parameter
- [ ] Swipe DOWN returns to LOOP mode

**LOOP Mode:**
- [ ] Pointer sets loop IN point
- [ ] Two fingers sets loop OUT point
- [ ] Pinch adjusts loop length
- [ ] Palm rotation moves loop position
- [ ] Swipe UP enables/disables loop

**SCRATCH Mode:**
- [ ] Palm rotation scratches deck
- [ ] Pinch bends pitch
- [ ] Pointer triggers cue point
- [ ] Two fingers nudges tempo
- [ ] Swipe RIGHT cycles to NORMAL mode

---

## VERSION HISTORY

**v1.0 (Current)**
- Swipe-based mode switching (Option A)
- 4 modes: NORMAL, FX, LOOP, SCRATCH
- Standardized gesture mappings
- Distance normalization for all gestures
- Crossfader position memory

**Future v1.1 (Planned)**
- Implement FX mode controls
- Implement LOOP mode controls
- Implement SCRATCH mode controls
- Add visual mode indicators
- Add audio feedback for mode changes

**Future v2.0 (Planned)**
- User calibration system
- Custom gesture macros
- Multi-user profiles
- Advanced effects routing
- MIDI output support

---

## CONCLUSION

This standard provides:
✅ **Clear gesture definitions** with specific detection criteria
✅ **Mode-based control** for complex DJ operations
✅ **Swipe-based mode switching** (proven reliable)
✅ **Conflict-free mappings** to prevent accidental triggers
✅ **Extensible framework** for future enhancements

**Next Steps:**
1. Implement swipe → mode switching logic
2. Build FX mode UI and controls
3. Build LOOP mode UI and controls
4. Build SCRATCH mode UI and controls
5. Add visual mode indicators
6. Test full workflow with real music

**Ready to implement?** Let's start with the mode switching system!
