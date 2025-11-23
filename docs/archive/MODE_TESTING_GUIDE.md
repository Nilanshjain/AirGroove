# MODE SYSTEM TESTING GUIDE

**Date:** November 23, 2025
**Feature:** LEFT/RIGHT Swipe Mode Switching
**Status:** Ready for Testing

---

## IMPLEMENTATION COMPLETE

✅ Mode state management (4 modes: NORMAL, FX, LOOP, SCRATCH)
✅ LEFT/RIGHT swipe detection for mode switching
✅ Prominent mode indicator (top center of camera UI)
✅ Mode-specific instruction text (bottom of camera UI)
✅ Mode-specific gesture handlers (with console logging)
✅ 500ms cooldown between mode changes
✅ WebSocket mode change broadcast

---

## CAMERA UI FEATURES

### Top Center: MODE INDICATOR
- **Large colored box** with mode name
- **Color coding**:
  - NORMAL MODE: White border
  - FX MODE: Cyan border
  - LOOP MODE: Green border
  - SCRATCH MODE: Orange border

### Bottom: MODE-SPECIFIC INSTRUCTIONS
- **Line 1**: "Q-Quit | SPACE-Play A | O/P-Demo | Swipe L/R: Change Mode"
- **Line 2**: Dynamic instructions based on current mode
  - **NORMAL**: "Fist: Play/Pause | Pinch: Crossfader"
  - **FX**: "Fist: Play/Pause | Pointer: Select FX | Two Fingers: Adjust | Rotate: Intensity"
  - **LOOP**: "Fist: Play/Pause | Pointer: IN | Two Fingers: OUT | Pinch: Length | Rotate: Move"
  - **SCRATCH**: "Fist: Play/Pause | Rotate: Scratch | Pinch: Pitch | Pointer: Cue | Two Fingers: Nudge"

---

## HOW TO TEST

### Step 1: Start Application
```bash
python -B main_precision.py
```

### Step 2: Verify Default Mode
- Camera UI should show: **"NORMAL MODE"** in white at top center
- Bottom instruction should show: **"Pinch: Crossfader"**

### Step 3: Test Mode Switching

#### Swipe RIGHT (Cycle Forward):
1. Make **open palm** gesture
2. Move hand quickly to the **RIGHT**
3. Watch console output:
   ```
   ============================================================
   [MODE SWITCH] Swipe RIGHT → FX MODE
   ============================================================
   ```
4. Camera UI should change to: **"FX MODE"** in cyan
5. Instructions should update to FX controls

#### Swipe LEFT (Cycle Backward):
1. Make **open palm** gesture
2. Move hand quickly to the **LEFT**
3. Watch console output:
   ```
   ============================================================
   [MODE SWITCH] Swipe LEFT → NORMAL MODE
   ============================================================
   ```
4. Camera UI should change back to: **"NORMAL MODE"** in white

#### Full Mode Cycle:
1. Start in NORMAL (white)
2. Swipe RIGHT → FX (cyan)
3. Swipe RIGHT → LOOP (green)
4. Swipe RIGHT → SCRATCH (orange)
5. Swipe RIGHT → NORMAL (white) [cycles back]

OR

1. Start in NORMAL (white)
2. Swipe LEFT → SCRATCH (orange)
3. Swipe LEFT → LOOP (green)
4. Swipe LEFT → FX (cyan)
5. Swipe LEFT → NORMAL (white) [cycles back]

---

## MODE-SPECIFIC GESTURE TESTING

### NORMAL MODE (White)

**Test Crossfader:**
1. Make **pinch** gesture (thumb + index together)
2. Move hand LEFT and RIGHT
3. Console should show: `[NORMAL MODE] Crossfader active`
4. Crossfader visualization should move

**Test Play/Pause:**
1. Make **closed fist** gesture with left hand
2. Hold for 0.4 seconds
3. Console should show: `[CLOSED_FIST] Left hand → PLAY Deck A`

---

### FX MODE (Cyan)

**Test Effect Selection (Pointer):**
1. Make **pointer** gesture (index only)
2. Move hand up/down
3. Console should show: `[FX MODE] Left pointer → Select effect at Y=0.XX`

**Test Parameter Adjustment (Two Fingers):**
1. Make **two fingers** gesture (index + middle)
2. Move hand around
3. Console should show: `[FX MODE] Right two_fingers → Adjust param (X=0.XX, Y=0.XX)`

**Test Intensity (Palm Rotation):**
1. Make **open palm** gesture
2. Rotate palm clockwise or counter-clockwise
3. Console should show: `[FX MODE] Left rotation → Intensity XX.X°/s`

---

### LOOP MODE (Green)

**Test Loop IN Point (Pointer):**
1. Make **pointer** gesture
2. Console should show: `[LOOP MODE] Left pointer → Set loop IN (Deck A)`

**Test Loop OUT Point (Two Fingers):**
1. Make **two fingers** gesture
2. Console should show: `[LOOP MODE] Right two_fingers → Set loop OUT (Deck B)`

**Test Loop Length (Pinch):**
1. Make **pinch** gesture
2. Move horizontally
3. Console should show: `[LOOP MODE] Left pinch → Adjust loop length (X=0.XX)`

**Test Loop Position (Palm Rotation):**
1. Make **open palm** gesture
2. Rotate palm
3. Console should show: `[LOOP MODE] Right rotation → Move loop position XX.X°/s`

---

### SCRATCH MODE (Orange)

**Test Scratching (Palm Rotation):**
1. Make **open palm** gesture
2. Rotate palm clockwise (forward) or counter-clockwise (reverse)
3. Console should show: `[SCRATCH MODE] Left rotation → Scratch FORWARD/REVERSE XX.X°/s (Deck A)`

**Test Pitch Bend (Pinch):**
1. Make **pinch** gesture
2. Move hand up (faster) or down (slower)
3. Console should show: `[SCRATCH MODE] Right pinch → Pitch bend FASTER/SLOWER (Deck B)`

**Test Cue Point (Pointer):**
1. Make **pointer** gesture
2. Console should show: `[SCRATCH MODE] Left pointer → CUE (Deck A)`

**Test Tempo Nudge (Two Fingers):**
1. Make **two fingers** gesture
2. Console should show: `[SCRATCH MODE] Right two_fingers → Nudge tempo UP (Deck B)`

---

## EXPECTED CONSOLE OUTPUT

### Successful Mode Switch:
```
[DEBUG] Right: open_palm | Pos: (0.65, 0.42) | Swipe: RIGHT | Tap: False | Rot: 0.0°/s

============================================================
[MODE SWITCH] Swipe RIGHT → FX MODE
============================================================
```

### FX Mode Gesture:
```
[DEBUG] Left: pointer | Pos: (0.32, 0.28) | Swipe: None | Tap: False | Rot: 0.0°/s
[FX MODE] Left pointer → Select effect at Y=0.28
```

### LOOP Mode Gesture:
```
[DEBUG] Right: two_fingers | Pos: (0.58, 0.71) | Swipe: None | Tap: False | Rot: 0.0°/s
[LOOP MODE] Right two_fingers → Set loop OUT (Deck B)
```

### SCRATCH Mode Gesture:
```
[DEBUG] Left: open_palm | Pos: (0.41, 0.49) | Swipe: None | Tap: False | Rot: -67.3°/s
[SCRATCH MODE] Left rotation → Scratch FORWARD 67.3°/s (Deck A)
```

---

## TROUBLESHOOTING

### Mode Not Switching:
- **Check swipe detection**: Make sure you see `Swipe: LEFT` or `Swipe: RIGHT` in debug output
- **Check cooldown**: Wait 500ms between mode changes
- **Make open palm**: Swipes only detected with open palm gesture

### Console Not Showing Mode Gestures:
- **Verify mode indicator**: Check camera UI shows correct mode
- **Hold gesture longer**: Some gestures need to be held for recognition
- **Check gesture detection**: Make sure gesture shows correctly in debug output

### UI Not Updating:
- **Check mode color**: Border should change with each mode
- **Check instructions**: Bottom text should change with each mode
- **Restart application**: Clear Python cache and restart

---

## TESTING CHECKLIST

### Mode Switching:
- [ ] Swipe RIGHT changes mode (NORMAL → FX → LOOP → SCRATCH → NORMAL)
- [ ] Swipe LEFT changes mode (NORMAL → SCRATCH → LOOP → FX → NORMAL)
- [ ] Mode indicator updates correctly (color + text)
- [ ] Instructions update correctly (mode-specific)
- [ ] Cooldown prevents rapid mode changes (500ms)
- [ ] Either hand can trigger mode switch

### NORMAL Mode:
- [ ] Pinch controls crossfader
- [ ] Closed fist plays/pauses deck
- [ ] UI shows "NORMAL MODE" in white

### FX Mode:
- [ ] Pointer gesture logs effect selection
- [ ] Two fingers gesture logs parameter adjustment
- [ ] Palm rotation logs intensity change
- [ ] UI shows "FX MODE" in cyan

### LOOP Mode:
- [ ] Pointer gesture logs loop IN point
- [ ] Two fingers gesture logs loop OUT point
- [ ] Pinch gesture logs loop length adjustment
- [ ] Palm rotation logs loop position move
- [ ] UI shows "LOOP MODE" in green

### SCRATCH Mode:
- [ ] Palm rotation logs scratching (forward/reverse)
- [ ] Pinch gesture logs pitch bend (faster/slower)
- [ ] Pointer gesture logs cue point
- [ ] Two fingers gesture logs tempo nudge
- [ ] UI shows "SCRATCH MODE" in orange

### Closed Fist (All Modes):
- [ ] Closed fist works in NORMAL mode
- [ ] Closed fist works in FX mode
- [ ] Closed fist works in LOOP mode
- [ ] Closed fist works in SCRATCH mode
- [ ] Left hand controls Deck A
- [ ] Right hand controls Deck B

---

## NEXT STEPS AFTER TESTING

Once mode switching is confirmed working:
1. **Implement FX mode controls** (effect selection, parameter adjustment)
2. **Implement LOOP mode controls** (loop point setting, length adjustment)
3. **Implement SCRATCH mode controls** (turntable scratch, pitch bend)
4. **Add visual feedback** for mode-specific actions
5. **Integrate with audio engine** (actual effect/loop/scratch processing)

---

## NOTES

- **Current Implementation**: Mode switching and gesture detection COMPLETE
- **Gesture Handlers**: Logging to console (no audio processing yet)
- **WebSocket**: Mode changes broadcast to web UI
- **Performance**: Mode switching has 500ms cooldown (adjustable)
- **Flexibility**: Easy to add new modes or change swipe directions

**Ready to test?** Run: `python -B main_precision.py`

**See issues?** Check console output for debug info and error messages!
