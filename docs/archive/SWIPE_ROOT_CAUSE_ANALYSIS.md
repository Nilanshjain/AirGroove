# SWIPE DETECTION ROOT CAUSE ANALYSIS
**Date:** November 23, 2025
**Issue:** Swipe gestures not triggering mode changes
**Status:** ✅ DEFINITIVE ROOT CAUSE FOUND

---

## COMPLETE DFS TRACE

### Level 1: User Makes Swipe Gesture
1. User extends 3+ fingers (open_palm gesture)
2. User moves hand LEFT or RIGHT across screen
3. MediaPipe detects hand landmarks

### Level 2: MediaPipe → GestureDetector (`src/precision_gestures.py`)

**File:** `src/precision_gestures.py`

**Line 138:** `gesture = self._detect_gesture(landmarks)`
- Calls gesture detection

**Line 241-265:** `_is_open_palm(landmarks)`
- **ISSUE FOUND:** Was NOT using distance normalization
- **FIX APPLIED:** Added `_calculate_hand_size()` and `_get_normalized_threshold()`
- Now detects open_palm even when hand is far from camera

**Line 152/159:** `self._track_swipe('left', hand_data['position'], gesture)`
- Passes gesture type to swipe tracker

### Level 3: Swipe Tracking (`_track_swipe`)

**Line 541-546:** Gesture filter
```python
# Only track swipes with open palm
if gesture != 'open_palm':
    swipe_data['positions'] = []
    return
```
- ✅ Correctly filters for open_palm only

**Line 590-598:** Position tracking
```python
swipe_data['positions'].append((position, current_time))
```
- ✅ Stores positions correctly

**Line 600-610:** Swipe detection
```python
if len(swipe_data['positions']) >= self.SWIPE_MINIMUM_FRAMES:
    swipe_direction = self._detect_swipe_with_threshold(swipe_data['positions'], self.SWIPE_THRESHOLD)
```
- ✅ Calls swipe direction classifier

**Line 604:** Console log
```python
print(f"[Swipe] {hand} hand swipe {swipe_direction} | Frames: {len(swipe_data['positions'])} | Direction changes: {swipe_data['direction_changes']}")
```
- ✅ Would log swipe if detected

### Level 4: Direction Classification (`_detect_swipe_with_threshold`)

**Line 616-675:** Swipe direction classifier

**Line 658-667:** Direction mapping
```python
if -22.5 <= angle < 22.5:
    return "right"  # ⚠️ LOWERCASE "right"
...
elif angle >= 157.5 or angle < -157.5:
    return "left"   # ⚠️ LOWERCASE "left"
```

**⚠️ PROBLEM:** Returns lowercase `"left"` and `"right"`

### Level 5: State Export (`_get_current_state`)

**Line 812-813:** Get swipes
```python
left_swipe = self._get_recent_swipe('left')
right_swipe = self._get_recent_swipe('right')
```

**Line 825/838:** Add to state dict
```python
'swipe': left_swipe,  # Contains "left" or "right" (lowercase)
```

**Line 848-856:** `_get_recent_swipe`
```python
if swipe_data['last_swipe'] and current_time - swipe_data['swipe_time'] < self.SWIPE_EVENT_DURATION:
    return swipe_data['last_swipe']  # Returns "left" or "right" (lowercase)
```

### Level 6: Main Loop → Mode Switching (`main_precision.py`)

**Line 327-328:** Extract swipe from state
```python
left_swipe = gesture_state.get('left_hand', {}).get('swipe')
right_swipe = gesture_state.get('right_hand', {}).get('swipe')
```
- Receives `"left"` or `"right"` (lowercase)

**Line 344:** Get direction
```python
swipe_direction = left_swipe or right_swipe
```
- `swipe_direction` = `"left"` or `"right"` (lowercase)

**Line 346:** **🔴 ROOT CAUSE - CASE MISMATCH**
```python
if swipe_direction in ['LEFT', 'RIGHT']:  # ⚠️ UPPERCASE check!
```

**DEFINITIVE ROOT CAUSE:**
The condition checks for UPPERCASE `'LEFT'` and `'RIGHT'`, but the swipe detector returns lowercase `"left"` and `"right"`.

**Result:** `swipe_direction in ['LEFT', 'RIGHT']` evaluates to `False` every time!

---

## VERIFICATION

### Console Output Analysis
From logs, we see:
- `[DEBUG] Right: none` - Hand detected as "none" gesture
- `Swipe: None` - No swipe detected

**Why?**
1. `_is_open_palm()` was not using distance normalization → hand too far, detected as "none"
2. Even if open_palm was detected, the uppercase/lowercase mismatch would prevent mode switch

### Code Flow Simulation

**Scenario:** User swipes RIGHT with open palm

```
1. MediaPipe detects hand
2. _is_open_palm() → False (no distance norm) → gesture = "none"
3. _track_swipe('right', position, "none")
4. Line 542: gesture != 'open_palm' → return (ABORT)
5. No swipe tracked
6. Result: Swipe: None
```

**After fix #1 (distance normalization):**
```
1. MediaPipe detects hand
2. _is_open_palm() → True (with distance norm) → gesture = "open_palm"
3. _track_swipe('right', position, "open_palm")
4. Line 542: gesture == 'open_palm' → continue
5. Positions tracked...
6. Line 602: swipe_direction = "right" (lowercase)
7. _get_recent_swipe() → returns "right"
8. main_precision.py line 344: swipe_direction = "right"
9. Line 346: "right" in ['LEFT', 'RIGHT'] → False (CASE MISMATCH)
10. Mode does NOT switch
```

**After fix #2 (case correction):**
```
9. Line 346: "right" in ['left', 'right'] → True ✅
10. Mode switches successfully ✅
```

---

## DEFINITIVE FIXES REQUIRED

### Fix #1: Distance Normalization for open_palm ✅ APPLIED
**File:** `src/precision_gestures.py`
**Line:** 241-265

**Before:**
```python
def _is_open_palm(self, landmarks) -> bool:
    # No distance normalization
    if abs(thumb_tip[0] - thumb_mcp[0]) > self.FINGER_EXTEND_THRESHOLD:
```

**After:**
```python
def _is_open_palm(self, landmarks) -> bool:
    hand_size = self._calculate_hand_size(landmarks)
    extend_threshold = self._get_normalized_threshold(self.FINGER_EXTEND_THRESHOLD * 0.5, hand_size)
    if abs(thumb_tip[0] - thumb_mcp[0]) > extend_threshold:
```

### Fix #2: Case Mismatch ⚠️ NOT YET APPLIED
**File:** `main_precision.py`
**Line:** 346

**Option A: Change main_precision.py to lowercase**
```python
if swipe_direction in ['left', 'right']:  # Use lowercase
```

**Option B: Change precision_gestures.py to uppercase**
```python
return "RIGHT"  # Line 659
return "LEFT"   # Line 667
```

**RECOMMENDATION:** Option A - Change main_precision.py to lowercase
- Less invasive (1 line change vs multiple)
- Lowercase is more pythonic for string values
- Uppercase typically reserved for constants

### Fix #3: More Lenient Swipe Thresholds ✅ APPLIED
**File:** `src/precision_gestures.py`
**Lines:** 61-65

**Changes:**
- Distance: 0.30 → 0.15 (only need 15% screen width)
- Velocity: 0.4 → 0.25 (slower movement ok)
- Min frames: 5 → 3 (faster detection)
- Time window: 0.5 → 0.8 (more time)

---

## TESTING PLAN

### Test Case 1: Open Palm Detection
**Action:** Extend hand with 3+ fingers at varying distances
**Expected:** Gesture shows "open_palm" even when hand far from camera
**Verify:** `[DEBUG] Right: open_palm` in console

### Test Case 2: Swipe Tracking
**Action:** Make open palm, move RIGHT slowly
**Expected:** `[Swipe] right hand swipe right | Frames: 3-10` in console
**Verify:** Swipe log appears

### Test Case 3: Mode Switching
**Action:** Swipe RIGHT with open palm
**Expected:**
```
============================================================
[MODE SWITCH] Swipe right → FX MODE
============================================================
```
**Verify:** Mode indicator changes in camera UI

---

## STATUS

✅ Fix #1 APPLIED: Distance normalization for open_palm
✅ Fix #3 APPLIED: Lenient swipe thresholds
⚠️ Fix #2 PENDING: Case mismatch correction

**Next Step:** Apply Fix #2 to resolve case mismatch between swipe detector and mode switcher.
