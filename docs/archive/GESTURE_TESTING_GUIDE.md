# AIRGROOVE - GESTURE TESTING GUIDE

**Last Updated:** November 23, 2025

---

## CROSSFADER IMPROVEMENTS

### What Changed:
1. **Position Memory**: Crossfader now remembers last position instead of resetting to center (0.5)
2. **Better Sensitivity**: Reduced smoothing from 0.7/0.3 to 0.85/0.15 for more accurate control
3. **Initialization**: First pinch starts from audio engine's current position (not default 0.5)

### How to Test Crossfader:
1. Make a **pinch gesture** (thumb + index finger together)
2. Move your hand LEFT and RIGHT slowly
3. Watch the crossfader position in the web UI
4. Release the pinch (open your hand)
5. Make pinch again - should resume from last position, NOT center

**Expected Behavior:**
- Smooth, responsive movement following your hand
- No jumps or resets to center
- Position persists between pinch sessions

---

## GESTURE RECOGNITION FIXES

### What Changed:
1. **Closed Fist**: Stricter detection (all 4 fingers must be folded, hand width < 0.12)
2. **Pointer**: Middle finger MUST be folded (prevents confusion with two_fingers)
3. **Two Fingers**: Ring and pinky MUST be folded (prevents confusion with open palm)

### Current Gesture Mappings:

| Gesture | Hand Position | Action | Status |
|---------|---------------|--------|--------|
| **Closed Fist** | All fingers folded tightly | Play/Pause deck | ✅ WORKING |
| **Pinch** | Thumb + index together | Crossfader control | ✅ WORKING |
| **Pointer** | Index up, middle/ring/pinky down | Precision control mode | ✅ WORKING |
| **Two Fingers** | Index + middle up, ring/pinky down | Precision control mode | ✅ WORKING |
| **Open Palm** | 3+ fingers extended | Gesture ready state | ✅ WORKING |
| **Swipe** | Quick open palm movement | Mode switching (planned) | ⏳ IMPLEMENTED |
| **Palm Rotation** | Rotate open palm | Mode effects (planned) | ⏳ IMPLEMENTED |

---

## TESTING EACH GESTURE

### 1. Closed Fist (Play/Pause)
**How to perform:**
- Make a tight fist with all fingers curled in
- Keep hand compact (fingers close together)

**What to check:**
- Console shows: `[CLOSED_FIST] Left/Right hand -> PLAY Deck A/B`
- Track starts/stops playing
- NOT triggered by pointer or two_fingers

**Troubleshooting:**
- If not detected: Make fist tighter, bring fingers closer together
- If pointer triggers it: Make sure index finger is completely folded

---

### 2. Pinch (Crossfader)
**How to perform:**
- Touch thumb tip to index finger tip
- Move hand left/right horizontally
- Keep other fingers relaxed (not extended)

**What to check:**
- Crossfader slider moves smoothly
- Position follows your hand movement
- Release pinch, then pinch again - should NOT reset to center

**Troubleshooting:**
- If too sensitive: Move hand more slowly
- If not responding: Make sure thumb and index are clearly touching
- If jumpy: Keep hand steady while moving

---

### 3. Pointer (Index Only)
**How to perform:**
- Extend ONLY index finger pointing up
- Fold middle, ring, pinky down into palm
- Thumb can be relaxed or folded

**What to check:**
- Console shows: `[DEBUG] Right: pointer` (or Left)
- NOT detected as closed_fist
- NOT detected as two_fingers

**Troubleshooting:**
- If detected as two_fingers: Make sure middle finger is folded
- If detected as closed_fist: Extend index finger more clearly
- If not detected: Hold gesture for >0.5 seconds

---

### 4. Two Fingers (Index + Middle)
**How to perform:**
- Extend index AND middle fingers together
- Fold ring and pinky down into palm
- Keep index and middle separated (V shape)

**What to check:**
- Console shows: `[DEBUG] Right: two_fingers` (or Left)
- NOT detected as pointer
- NOT detected as open_palm

**Troubleshooting:**
- If detected as pointer: Make sure middle is clearly extended
- If detected as open_palm: Fold ring and pinky more
- If not detected: Separate index and middle more clearly

---

### 5. Open Palm
**How to perform:**
- Extend all 5 fingers outward
- Keep hand flat and open

**What to check:**
- Console shows: `[DEBUG] Right: open_palm` (or Left)
- Used for swipe and rotation tracking

**Troubleshooting:**
- If not detected: Extend all fingers more clearly
- Should be easiest gesture to detect

---

## SWIPE DETECTION TESTING

### Current Implementation:
- **8-directional swipes**: up, down, left, right, up-left, up-right, down-left, down-right
- **Requirements**: Open palm, minimum 5 frames, velocity > 0.4, distance > 0.30

### How to Test Swipes:
1. Start with **open palm** gesture
2. Move hand quickly in one direction (left/right/up/down/diagonal)
3. Keep palm open during the entire movement
4. Watch console for: `[Swipe] left/right hand swipe LEFT/RIGHT/UP/DOWN/...`

**Expected Output Examples:**
```
[Swipe] right hand swipe RIGHT | Frames: 8 | Direction changes: 0
[Swipe] left hand swipe UP | Frames: 6 | Direction changes: 1
[Swipe] right hand swipe DOWN-RIGHT | Frames: 7 | Direction changes: 0
```

**Swipe Parameters (from config):**
- Distance threshold: 0.30 (30% of screen)
- Time window: 0.5 seconds
- Minimum frames: 5
- Velocity threshold: 0.4
- Cooldown: 0.3 seconds between swipes

**Troubleshooting:**
- If not detected: Move hand faster and farther
- If too many false triggers: Increase SWIPE_THRESHOLD in config
- If direction changes prevent detection: Move in straighter line

---

## PALM ROTATION TESTING

### Current Implementation:
- Tracks angular velocity of palm rotation (degrees/second)
- Uses wrist → middle finger vector to detect rotation

### How to Test Rotation:
1. Start with **open palm** gesture
2. Rotate your palm clockwise or counter-clockwise
3. Keep palm open and flat during rotation
4. Watch console for rotation velocity

**Expected Output:**
```
[DEBUG] Right: open_palm | Pos: (0.52, 0.48) | Swipe: None | Tap: False | Rot: -45.2°/s
[DEBUG] Left: open_palm | Pos: (0.31, 0.45) | Swipe: None | Tap: False | Rot: 32.8°/s
```

**Rotation Values:**
- Positive rotation: Counter-clockwise
- Negative rotation: Clockwise
- Typical range: -180°/s to +180°/s

**Troubleshooting:**
- If not detected: Rotate palm more clearly
- If erratic: Keep palm flatter and steadier

---

## MODE SWITCHING IMPLEMENTATION (PLANNED)

### Concept:
Use gestures to switch between DJ control modes while music is playing.

### Proposed Modes:

**1. NORMAL MODE (Default)**
- Closed fist: Play/Pause
- Pinch: Crossfader
- Open palm: Ready state

**2. FX MODE**
- Pointer: Select effect
- Two fingers: Adjust effect parameter
- Palm rotation: Effect wet/dry mix
- Swipe left/right: Cycle through effects

**3. LOOP MODE**
- Pointer: Set loop in point
- Two fingers: Set loop out point
- Pinch: Adjust loop length
- Swipe up: Enable loop
- Swipe down: Disable loop

**4. SCRATCH MODE**
- Open palm rotation: Scratch/spin deck
- Pinch: Pitch bend
- Swipe up/down: Nudge tempo

### Mode Switching Options:

**Option A: Swipe-Based**
- Swipe UP: Enter FX mode
- Swipe DOWN: Enter Loop mode
- Swipe LEFT/RIGHT: Cycle through modes

**Option B: Gesture Combo**
- Both hands pointer: Enter FX mode
- Both hands two_fingers: Enter Loop mode
- Both hands open palm + swipe: Return to Normal mode

**Option C: Hold Gesture**
- Hold pointer for 2 seconds: Enter FX mode
- Hold two_fingers for 2 seconds: Enter Loop mode
- Any closed fist: Return to Normal mode

### Questions for User:
1. Which mode switching method do you prefer? (A, B, C, or other?)
2. Should mode persist when hands leave frame?
3. Should there be visual/audio feedback when mode changes?
4. Should certain modes be limited to specific decks (left hand = Deck A, right = Deck B)?

---

## TESTING PROCEDURE

### Quick Test Sequence:
```
1. Start application: python -B main_precision.py
2. Test closed fist play/pause (both hands)
3. Test pinch crossfader (left hand, then right hand)
4. Test pointer detection (make sure middle is folded)
5. Test two_fingers detection (make sure ring/pinky are folded)
6. Test swipe (open palm, quick movement left/right)
7. Test rotation (open palm, rotate clockwise/counter-clockwise)
8. Test crossfader position memory (pinch, release, pinch again)
```

### What to Watch:
- **Console output**: Shows detected gestures, swipes, rotation
- **Web UI**: Crossfader slider, deck status
- **Video feed**: Hand landmarks, gesture labels

### Common Issues:
1. **Gesture misdetection**: Check finger positions match description exactly
2. **No detection at far distance**: Move hands closer to camera
3. **Erratic crossfader**: Reduce hand movement speed
4. **Swipes not detected**: Increase movement speed and distance

---

## CURRENT STATUS SUMMARY

✅ **WORKING:**
- Closed fist detection (strict, accurate)
- Pointer detection (middle must be folded)
- Two fingers detection (ring/pinky must be folded)
- Pinch crossfader (remembers position, better sensitivity)
- Play/pause control
- Swipe detection (8 directions)
- Palm rotation tracking

⏳ **IMPLEMENTED BUT NOT MAPPED:**
- Swipe → Mode switching
- Rotation → Effect control
- Mode system architecture

❌ **NOT IMPLEMENTED:**
- FX mode controls
- Loop mode controls
- Scratch mode controls
- Visual mode indicators

---

## NEXT STEPS

1. **Test current gestures** to ensure accuracy
2. **Decide mode switching method** (swipe/combo/hold)
3. **Implement mode switching logic**
4. **Map gestures to mode-specific actions**
5. **Add visual feedback** for mode changes
6. **Test mode transitions** while music is playing

---

**Ready to test?** Run: `python -B main_precision.py`

**Questions?** Let me know which mode switching method you prefer and we'll implement it!
