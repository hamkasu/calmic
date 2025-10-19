# Adding a Gentle Chime to Splash Screen

The splash screen is ready to play a gentle chime sound, but needs an audio file to be added.

## Steps to Add the Chime Sound:

### 1. Download a Free Chime Sound
Visit [Pixabay Sound Effects - Chime](https://pixabay.com/sound-effects/search/chime/) and download one of these recommended options:

**Recommended Chimes:**
- **"Chime sound"** (1 second) - Quick, gentle notification chime
- **"Silver chime"** (2 seconds) - Soft, metallic chime  
- **"Melancholy UI Chime"** (1 second) - Pleasant UI chime

All sounds are **royalty-free** and **no attribution required**.

### 2. Save the Sound File
1. Download the `.mp3` file from Pixabay
2. Rename it to `chime.mp3`
3. Save it in: `StoryKeep-iOS/src/assets/sounds/chime.mp3`

### 3. Enable the Chime in Code
Open `StoryKeep-iOS/src/screens/SplashScreen.js` and:

1. **Find these commented lines** (around line 42):
```javascript
// const { sound: chimeSound } = await Audio.Sound.createAsync(
//   require('../assets/sounds/chime.mp3'),
//   { shouldPlay: true, volume: 0.5 }
// );
// sound = chimeSound;
```

2. **Uncomment them** (remove the `//`):
```javascript
const { sound: chimeSound } = await Audio.Sound.createAsync(
  require('../assets/sounds/chime.mp3'),
  { shouldPlay: true, volume: 0.5 }
);
sound = chimeSound;
```

3. **Find this commented line** (around line 58):
```javascript
// playChimeSound();
```

4. **Uncomment it**:
```javascript
playChimeSound();
```

### 4. Test the Splash Screen
1. Restart the Expo Server
2. Open the app on your phone
3. You should hear the gentle chime when the splash screen appears!

## Technical Details

- **Volume:** Set to 50% for a pleasant, non-jarring experience
- **Timing:** Plays immediately when the logo appears
- **Error Handling:** Won't crash if the sound fails to load
- **Cleanup:** Properly unloads the sound when the splash screen closes
- **iOS Silent Mode:** Configured to play even when phone is on silent
- **Performance:** Bundled locally for instant playback, no network delay

## Customization

Want to adjust the volume or timing?

**Volume:** Change `volume: 0.5` to a value between 0.0 (silent) and 1.0 (full volume)

**Delay the sound:** Wrap `playChimeSound()` in a setTimeout:
```javascript
setTimeout(() => playChimeSound(), 300); // Delay 300ms
```

---

*Note: The expo-av package is already installed and the splash screen code is ready to use.*
