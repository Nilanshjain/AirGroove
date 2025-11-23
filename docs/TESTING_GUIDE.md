# AirGroove Manual Testing Guide

## Table of Contents
1. [Setup and Prerequisites](#setup-and-prerequisites)
2. [Gesture System Testing](#gesture-system-testing)
3. [DJ Interface Testing](#dj-interface-testing)
4. [Library and Playlist Testing](#library-and-playlist-testing)
5. [Profile System Testing](#profile-system-testing)
6. [Known Limitations](#known-limitations)

---

## Setup and Prerequisites

### Required Hardware
- Webcam (for hand gesture recognition)
- Speakers or headphones

### Required Software
- Python 3.8+ with dependencies:
  - mediapipe
  - opencv-python (cv2)
  - pygame
  - librosa
  - websockets
  - asyncio
- Modern web browser (Chrome, Firefox, or Edge recommended)

### Starting the Application
1. Open terminal in the AirGroove directory
2. Run: `python main_precision.py` or `python -B main_precision.py`
3. Wait for "WebSocket server started" message
4. Open `web/index.html` in your browser
5. Allow webcam access when prompted

### Expected Initial State
- ✅ WebSocket connection indicator should be green
- ✅ Both hand gesture indicators should show "none"
- ✅ Current mode should display "NORMAL"
- ✅ Both decks should show "No Track Loaded"

---

## Gesture System Testing

### Hand Detection Test

**Test 1: Single Hand Detection**
- **Action**: Place your dominant hand in view of the webcam
- **Expected**:
  - Corresponding hand status (LEFT or RIGHT) updates from "none"
  - Console shows "[Gesture] [LEFT/RIGHT] hand detected"
- **Pass/Fail**: ___

**Test 2: Two-Hand Detection**
- **Action**: Place both hands in view
- **Expected**:
  - Both LEFT and RIGHT status indicators update
  - Console shows detection for both hands
- **Pass/Fail**: ___

**Test 3: Hand Loss Detection**
- **Action**: Remove hand(s) from view
- **Expected**:
  - Status returns to "none" for removed hand(s)
  - Console shows hand lost message
- **Pass/Fail**: ___

### Gesture Recognition Test

#### Basic Gestures

**Test 4: Open Palm**
- **Action**: Show open palm to camera
- **Expected**: Gesture indicator shows "open_palm"
- **Notes**: All fingers extended
- **Pass/Fail**: ___

**Test 5: Closed Fist**
- **Action**: Make a fist
- **Expected**: Gesture indicator shows "closed_fist"
- **Notes**: All fingers curled
- **Pass/Fail**: ___

**Test 6: Pointing**
- **Action**: Point with index finger
- **Expected**: Gesture indicator shows "pointing"
- **Notes**: Only index finger extended
- **Pass/Fail**: ___

**Test 7: Peace Sign**
- **Action**: Show peace sign (index + middle fingers)
- **Expected**: Gesture indicator shows "peace"
- **Notes**: Index and middle fingers extended
- **Pass/Fail**: ___

**Test 8: Thumbs Up**
- **Action**: Show thumbs up
- **Expected**: Gesture indicator shows "thumbs_up"
- **Notes**: Only thumb extended upward
- **Pass/Fail**: ___

**Test 9: Thumbs Down**
- **Action**: Show thumbs down
- **Expected**: Gesture indicator shows "thumbs_down"
- **Notes**: Only thumb extended downward
- **Pass/Fail**: ___

**Test 10: Tap Gesture**
- **Action**: Pinch thumb and index finger together
- **Expected**: Gesture indicator shows "tap"
- **Notes**: Forms an "OK" sign shape
- **Pass/Fail**: ___

#### Precision Gestures

**Test 11: Swipe Left**
- **Action**: Move hand from right to left across camera view
- **Expected**:
  - Gesture shows "swipe_left"
  - Mode changes (NORMAL → FX → LOOP → SCRATCH → NORMAL)
- **Pass/Fail**: ___

**Test 12: Swipe Right**
- **Action**: Move hand from left to right
- **Expected**:
  - Gesture shows "swipe_right"
  - Mode changes in reverse order
- **Pass/Fail**: ___

**Test 13: Vertical Movement (Volume Control)**
- **Action**: Move open palm up and down in NORMAL mode
- **Expected**:
  - Up movement increases volume
  - Down movement decreases volume
  - Volume meter reflects changes
- **Pass/Fail**: ___

**Test 14: Horizontal Movement (Crossfader)**
- **Action**: Move closed fist left and right in NORMAL mode
- **Expected**:
  - Crossfader knob moves
  - Position percentage updates
  - Color changes (purple ← center → green)
- **Pass/Fail**: ___

---

## DJ Interface Testing

### Mode Switching

**Test 15: Normal Mode**
- **Action**: Swipe to NORMAL mode
- **Expected**:
  - Mode selector highlights NORMAL
  - Current mode name shows "NORMAL"
  - Mode-specific controls appear in mixer section
- **Pass/Fail**: ___

**Test 16: FX Mode**
- **Action**: Swipe to FX mode
- **Expected**:
  - Mode selector highlights FX
  - Current mode name shows "FX"
  - FX controls appear
- **Pass/Fail**: ___

**Test 17: Loop Mode**
- **Action**: Swipe to LOOP mode
- **Expected**:
  - Mode selector highlights LOOP
  - Current mode name shows "LOOP"
  - Loop controls appear
- **Pass/Fail**: ___

**Test 18: Scratch Mode**
- **Action**: Swipe to SCRATCH mode
- **Expected**:
  - Mode selector highlights SCRATCH
  - Current mode name shows "SCRATCH"
  - Scratch controls appear
- **Pass/Fail**: ___

### Deck Controls

**Test 19: Load Track to Deck A**
- **Action**: Click "LOAD TRACK" button on Deck A
- **Expected**:
  - File dialog opens
  - After selecting audio file:
    - Track name and artist display
    - Waveform renders
    - BPM shows (if detected)
    - Duration shows
- **Pass/Fail**: ___

**Test 20: Load Track to Deck B**
- **Action**: Click "LOAD TRACK" button on Deck B
- **Expected**: Same as Test 19 for Deck B
- **Pass/Fail**: ___

**Test 21: Play/Pause Deck A**
- **Action**:
  - Load track on Deck A
  - Use TAP gesture or click PLAY button
- **Expected**:
  - Audio plays
  - Deck border glows purple and pulses
  - Volume meter glows and animates
  - Play button shows pause icon
  - Waveform position marker moves
  - Time updates
- **Pass/Fail**: ___

**Test 22: Play/Pause Deck B**
- **Action**: Same as Test 21 for Deck B
- **Expected**: Same as Test 21 but with green glow
- **Pass/Fail**: ___

**Test 23: Stop Deck**
- **Action**: Use THUMBS_DOWN gesture or click STOP button while deck is playing
- **Expected**:
  - Audio stops
  - Deck glow animation stops
  - Position resets to 0:00
  - Play button shows play icon
- **Pass/Fail**: ___

**Test 24: Sync Decks**
- **Action**:
  - Load different tempo tracks on both decks
  - Click SYNC button on one deck
- **Expected**:
  - BPM of clicked deck matches other deck
  - Sync button briefly highlights
  - Notification appears
- **Pass/Fail**: ___

**Test 25: Waveform Click-to-Seek**
- **Action**:
  - Load and play track
  - Click anywhere on waveform
- **Expected**:
  - Playback jumps to clicked position
  - Position marker updates
  - Time updates
- **Pass/Fail**: ___

**Test 26: Waveform Hover Preview**
- **Action**: Hover mouse over waveform
- **Expected**:
  - Vertical line appears at hover position
  - Time preview tooltip shows
- **Pass/Fail**: ___

### Crossfader and Volume

**Test 27: Manual Crossfader Control**
- **Action**: Use closed fist gesture to move crossfader
- **Expected**:
  - Crossfader knob follows hand movement
  - Trail shows path
  - Position percentage updates
  - Audio balance shifts between decks
- **Pass/Fail**: ___

**Test 28: Volume Control with Gesture**
- **Action**: Use open palm vertical movement
- **Expected**:
  - Volume meter fills/empties
  - Volume percentage updates
  - Audio volume changes
- **Pass/Fail**: ___

---

## Library and Playlist Testing

### Library Navigation

**Test 29: Access Library Page**
- **Action**: Click "Library" in navbar
- **Expected**:
  - Library page loads
  - "All Songs" view shows by default
  - Sidebar shows navigation options
- **Pass/Fail**: ___

**Test 30: Add Songs to Library**
- **Action**: Click "Add Songs" button
- **Expected**:
  - File dialog opens
  - After selecting files:
    - Songs appear in "All Songs" list
    - Count updates
    - Songs persist after page reload
- **Pass/Fail**: ___

**Test 31: View Playlists**
- **Action**: Click "Playlists" in sidebar
- **Expected**:
  - Playlists view shows
  - Displays all created playlists
  - Shows playlist count
- **Pass/Fail**: ___

**Test 32: View Liked Songs**
- **Action**: Click "Liked Songs" in sidebar
- **Expected**:
  - Liked songs view shows
  - Displays all liked tracks
  - Shows liked count
- **Pass/Fail**: ___

### Playlist Management

**Test 33: Create Playlist**
- **Action**:
  - Click "Create Playlist" button
  - Enter name and description
  - Click "Create Playlist"
- **Expected**:
  - Modal closes
  - Playlist appears in playlists view
  - Playlist count increases
- **Pass/Fail**: ___

**Test 34: Add Songs to Playlist**
- **Action**:
  - Open playlist detail view
  - Click "Add Songs"
  - Select songs from list
  - Click "Add Selected"
- **Expected**:
  - Songs added to playlist
  - Playlist song count updates
  - Changes persist after reload
- **Pass/Fail**: ___

**Test 35: Load Playlist to Deck**
- **Action**: Click deck button (A or B) on a playlist
- **Expected**:
  - First track from playlist loads to selected deck
  - Queue shows in library panel
  - Prev/Next buttons work
- **Pass/Fail**: ___

**Test 36: Navigate Playlist with Prev/Next**
- **Action**:
  - Load playlist to deck
  - Click NEXT button
- **Expected**:
  - Next track in playlist loads
  - Queue indicator updates
  - Works across page reloads
- **Pass/Fail**: ___

**Test 37: Like/Unlike Songs**
- **Action**: Click heart icon on a track
- **Expected**:
  - Heart fills/unfills
  - Track appears/disappears in Liked Songs
  - Liked count updates
- **Pass/Fail**: ___

### Search and Filtering

**Test 38: Search Songs**
- **Action**: Type in search box on All Songs view
- **Expected**:
  - Song list filters in real-time
  - Matching songs show
  - Search is case-insensitive
- **Pass/Fail**: ___

---

## Profile System Testing

### Profile Access

**Test 39: Access Profile Page**
- **Action**: Click profile avatar in navbar
- **Expected**:
  - Profile page loads
  - Shows username and avatar
  - Displays stats
  - Shows genre preferences
- **Pass/Fail**: ___

**Test 40: Edit Profile**
- **Action**:
  - Click "Edit Profile" button
  - Change username
  - Add bio
  - Click "Save Changes"
- **Expected**:
  - Modal closes
  - Profile updates
  - Changes persist after reload
  - Avatar letter updates if username changed
- **Pass/Fail**: ___

### Genre Preferences

**Test 41: Select Genres**
- **Action**: Click various genre tags
- **Expected**:
  - Tags highlight when selected
  - Selected count updates
  - Genre appears in selected list
- **Pass/Fail**: ___

**Test 42: Remove Selected Genres**
- **Action**: Click X on selected genre tag
- **Expected**:
  - Genre deselected
  - Removed from selected list
  - Count decreases
- **Pass/Fail**: ___

**Test 43: Save Genre Preferences**
- **Action**:
  - Select multiple genres
  - Click "Save Preferences"
- **Expected**:
  - Success notification appears
  - Preferences persist after reload
  - Saved to localStorage
- **Pass/Fail**: ___

**Test 44: Browse Genre Categories**
- **Action**: Scroll through genre categories
- **Expected**:
  - 12 main categories display
  - Each shows color indicator
  - Shows selection count (X / Total)
  - Sub-genres listed for each
- **Pass/Fail**: ___

### Statistics

**Test 45: View Stats**
- **Action**: Check stats section on profile
- **Expected**:
  - Shows track count from library
  - Shows playlist count
  - Shows liked songs count
  - Shows mix time (placeholder)
- **Pass/Fail**: ___

---

## Known Limitations

### Gesture System
- Hand must be within webcam view (centered works best)
- Lighting conditions affect detection (well-lit environments work best)
- Distance from camera: 30-100cm optimal
- Background should be relatively clear
- Gesture latency: ~100-300ms
- Some gestures may require practice for consistent recognition

### Audio System
- pygame.mixer seek functionality is limited (may restart from beginning)
- BPM detection accuracy varies by audio file quality
- Waveform generation can be slow for long audio files
- Volume changes may have slight delay

### Browser Compatibility
- localStorage required for persistence
- WebSocket support required
- Canvas API support required
- File API support required for track loading

### Performance
- CPU usage increases with both decks playing
- Waveform rendering can be resource-intensive
- Multiple background processes may affect gesture recognition

---

## Test Summary Template

```
Date: ___________
Tester: _________
Environment: _________

Tests Passed: ___ / 45
Tests Failed: ___
Tests Skipped: ___

Critical Issues:
1.
2.
3.

Minor Issues:
1.
2.
3.

Notes:


```

---

## Troubleshooting Common Issues

### Webcam Not Working
1. Check browser permissions
2. Ensure no other application is using webcam
3. Try refreshing the page
4. Check console for error messages

### WebSocket Connection Fails
1. Verify Python server is running
2. Check that port 8765 is available
3. Look for firewall blocking
4. Check console for connection errors

### Gestures Not Recognized
1. Improve lighting
2. Move closer/farther from camera
3. Try exaggerating gestures
4. Check hand is fully in frame
5. Ensure hand is clearly visible against background

### Audio Not Playing
1. Check system volume
2. Verify audio file format is supported
3. Check browser audio permissions
4. Try loading a different audio file
5. Check console for playback errors

### Tracks Not Persisting
1. Check localStorage is enabled in browser
2. Verify browser isn't in private/incognito mode
3. Check console for storage quota errors
4. Clear and re-add tracks if corruption suspected

---

## Reporting Issues

When reporting issues, include:
1. Test number that failed
2. Browser and version
3. Operating system
4. Steps to reproduce
5. Expected vs actual behavior
6. Console errors (if any)
7. Screenshots/video (if applicable)

---

**End of Testing Guide**
