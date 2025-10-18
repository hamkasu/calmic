# StoryKeep Android Build & Deployment Guide

## Overview
StoryKeep is now fully cross-platform! This guide will help you build and deploy the Android version of your app.

## Prerequisites
- Node.js 22+ installed
- Expo CLI installed (`npm install -g expo-cli`)
- Android Studio (for emulator testing) OR physical Android device
- Expo Go app installed on your Android device (for development testing)

## Quick Start - Testing on Android

### Option 1: Test with Expo Go (Recommended for Development)
1. **Install Expo Go** on your Android device from Google Play Store
2. **Start the development server**:
   ```bash
   cd StoryKeep-iOS
   npm start
   ```
3. **Scan the QR code** with your Android device's camera
4. The app will open in Expo Go

### Option 2: Test with Android Emulator
1. **Install Android Studio** and set up an Android emulator
2. **Start the emulator** from Android Studio
3. **Run the app**:
   ```bash
   cd StoryKeep-iOS
   npm run android
   ```

## Building for Production

### Build Android APK (for testing)
```bash
cd StoryKeep-iOS
eas build --platform android --profile preview
```

### Build Android AAB (for Google Play Store)
```bash
cd StoryKeep-iOS
eas build --platform android --profile production
```

## Android-Specific Features

### ✅ What's Already Configured
- **Package Name**: `com.calmic.storykeep`
- **Version Code**: 1 (must be manually incremented for each Play Store release)
- **Permissions**:
  - Camera access
  - Microphone for voice memos
  - Storage read/write
  - Biometric authentication (fingerprint/face unlock)
- **Adaptive Icon**: Configured for Material Design
- **Splash Screen**: Android-specific splash configured
- **Status Bar**: Optimized for Android
- **Back Button**: Hardware back button handling implemented

### Platform-Specific Behaviors

#### Biometric Authentication
- **iOS**: Shows "Face ID" or "Touch ID"
- **Android**: Shows "Fingerprint" or "Face Unlock" based on device capability

#### Keyboard Handling
- **iOS**: Uses `padding` behavior
- **Android**: Uses `height` behavior
- Both handled automatically by the app

#### Status Bar
- Always shows with dark content
- White background
- Non-translucent on Android for better compatibility

#### Back Button
- On login/register screens: Shows exit confirmation
- Inside the app: Normal back navigation

## Testing Checklist

### Core Features to Test on Android
- [ ] Login with email/password
- [ ] Biometric login (fingerprint/face unlock)
- [ ] Camera/Digitizer for photo capture
- [ ] Photo gallery viewing
- [ ] Photo enhancement features
- [ ] Family Vaults creation and access
- [ ] Voice memo recording
- [ ] Photo downloads and sharing
- [ ] Profile editing with image upload
- [ ] Settings and preferences
- [ ] Logout functionality
- [ ] Back button navigation

### Android-Specific Testing
- [ ] Hardware back button works correctly
- [ ] Status bar displays properly
- [ ] Keyboard doesn't cover input fields
- [ ] Biometric prompt shows correct text (Fingerprint vs Face ID)
- [ ] Camera permissions request properly
- [ ] Storage permissions work
- [ ] App adaptive icon displays correctly
- [ ] Splash screen shows on launch

## Common Issues & Solutions

### Issue: "Network request failed" on Android
**Solution**: Make sure the API base URL is accessible from your Android device. If testing locally, use your computer's local IP address instead of `localhost`.

### Issue: Camera not working
**Solution**: 
1. Check that camera permissions are granted in app settings
2. Restart the app after granting permissions
3. Ensure you're using a physical device (emulators may have limited camera support)

### Issue: Biometric not showing
**Solution**:
1. Ensure biometric is set up on the device (Settings > Security > Fingerprint)
2. Check that the app has permission to use biometric authentication
3. Login once with email/password to enable biometric login

### Issue: Back button exits the app unexpectedly
**Solution**: This is expected behavior on login/register screens. Once logged in, the back button navigates within the app.

### Issue: Images not loading
**Solution**:
1. Check network connectivity
2. Verify the API server is running and accessible
3. Check storage permissions are granted

## Deployment to Google Play Store

### Step 1: Prepare for Release
1. Update version in `app.json` (increment versionCode for each release):
   ```json
   {
     "expo": {
       "version": "1.0.0",
       "android": {
         "versionCode": 1  // Increment to 2, 3, 4... for each new build
       }
     }
   }
   ```
   
   **Important**: Google Play requires a higher versionCode for each new release. Always increment this number before building a new version.

2. Create app icon and screenshots for Play Store listing

### Step 2: Build Release AAB
```bash
eas build --platform android --profile production
```

### Step 3: Upload to Google Play Console
1. Go to [Google Play Console](https://play.google.com/console)
2. Create a new app or select existing
3. Upload the AAB file
4. Fill in app details, screenshots, and privacy policy
5. Submit for review

### Step 4: Release Management
- **Internal Testing**: Test with a small group first
- **Closed Beta**: Expand to beta testers
- **Production**: Release to all users

## Configuration Files

### app.json - Android Configuration
```json
{
  "android": {
    "versionCode": 1,
    "package": "com.calmic.storykeep",
    "adaptiveIcon": {
      "foregroundImage": "./assets/adaptive-icon.png",
      "backgroundColor": "#ffffff"
    },
    "permissions": [
      "CAMERA",
      "RECORD_AUDIO",
      "READ_EXTERNAL_STORAGE",
      "WRITE_EXTERNAL_STORAGE",
      "USE_BIOMETRIC",
      "USE_FINGERPRINT"
    ]
  }
}
```

### Key Expo Plugins
- `expo-camera`: Camera access and photo capture
- `expo-media-library`: Photo library access
- `expo-av`: Audio recording for voice memos
- `expo-local-authentication`: Biometric authentication

## Performance Optimization

### Android-Specific Optimizations
1. **Image Caching**: Images are cached automatically by Expo
2. **Lazy Loading**: Gallery uses lazy loading for better performance
3. **Native Modules**: Using native modules for camera and biometric for speed
4. **Memory Management**: Photos are released from memory after processing

## Security Considerations

### Android Security Features
- **Biometric credentials** stored in Android Keystore (most secure)
- **Auth tokens** stored in AsyncStorage (encrypted by OS)
- **API communication** over HTTPS only
- **Camera access** requires explicit user permission
- **Storage access** sandboxed to app directory

## Support

### Minimum Android Version
- **Minimum SDK**: 21 (Android 5.0 Lollipop)
- **Target SDK**: Latest stable Android version
- **Recommended**: Android 8.0+ for best performance

### Device Compatibility
- **Phones**: All Android phones with camera
- **Tablets**: Full tablet support
- **Foldables**: Adaptive layout support
- **ChromeOS**: May work but not officially supported

## Next Steps

1. **Test thoroughly** on multiple Android devices
2. **Gather beta feedback** from Android users
3. **Fix any platform-specific bugs**
4. **Submit to Google Play Store**
5. **Monitor crash reports** and user feedback

---

## Quick Commands Reference

```bash
# Start development server
npm start

# Run on Android emulator
npm run android

# Build APK for testing
eas build --platform android --profile preview

# Build AAB for Play Store
eas build --platform android --profile production

# Clear cache and restart
npx expo start -c
```

---

**Note**: The app was originally developed for iOS but is now fully cross-platform. All features work on both iOS and Android with platform-appropriate UI/UX patterns.
