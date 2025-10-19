import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  Animated,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Audio } from 'expo-av';

const { width, height } = Dimensions.get('window');

export default function SplashScreen({ onFinish }) {
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoScale = useRef(new Animated.Value(0.8)).current;
  const taglineOpacity = useRef(new Animated.Value(0)).current;
  const taglineTranslateY = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    let sound = null;

    const playChimeSound = async () => {
      try {
        // Set audio mode for playback
        await Audio.setAudioModeAsync({
          playsInSilentModeIOS: true,
          staysActiveInBackground: false,
        });

        // TODO: Add a custom chime sound
        // To add a gentle chime:
        // 1. Download a free chime from https://pixabay.com/sound-effects/search/chime/
        //    Recommended: "Chime sound" (1 second) or "Silver chime" (2 seconds)
        // 2. Save the .mp3 file as 'chime.mp3' in: StoryBox-iOS/src/assets/sounds/
        // 3. Uncomment the lines below:
        
        const { sound: chimeSound } = await Audio.Sound.createAsync(
           require('../assets/sounds/chime.mp3'),
           { shouldPlay: true, volume: 0.5 }
         );
         sound = chimeSound;
        
        // For now, splash screen runs without sound to avoid errors
        // Uncomment the above code once you add the sound file
        
      } catch (error) {
        // Silently fail if audio can't play - don't block the splash screen
        console.log('Audio playback failed:', error);
      }
    };

    // Play chime when splash screen appears (currently disabled until sound file added)
    playChimeSound();

    // Start animations
    Animated.sequence([
      // Logo fade-in and scale
      Animated.parallel([
        Animated.timing(logoOpacity, {
          toValue: 1,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.spring(logoScale, {
          toValue: 1,
          friction: 8,
          tension: 40,
          useNativeDriver: true,
        }),
      ]),
      // Wait a bit
      Animated.delay(300),
      // Tagline slide-up and fade-in
      Animated.parallel([
        Animated.timing(taglineOpacity, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.timing(taglineTranslateY, {
          toValue: 0,
          duration: 600,
          useNativeDriver: true,
        }),
      ]),
      // Wait before transitioning
      Animated.delay(1500),
    ]).start(() => {
      // Animation complete, trigger transition
      if (onFinish) {
        onFinish();
      }
    });

    // Cleanup: unload sound when component unmounts
    return () => {
      if (sound) {
        sound.unloadAsync();
      }
    };
  }, []);

  return (
    <LinearGradient
      colors={['#FF6B9D', '#FFA07A', '#FFB6C1']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.container}
    >
      <View style={styles.content}>
        {/* Logo Animation */}
        <Animated.View
          style={[
            styles.logoContainer,
            {
              opacity: logoOpacity,
              transform: [{ scale: logoScale }],
            },
          ]}
        >
          <Image
            source={require('../assets/logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />
        </Animated.View>

        {/* App Name */}
        <Animated.Text
          style={[
            styles.appName,
            {
              opacity: logoOpacity,
            },
          ]}
        >
          StoryBox
        </Animated.Text>

        {/* Tagline Animation */}
        <Animated.View
          style={[
            styles.taglineContainer,
            {
              opacity: taglineOpacity,
              transform: [{ translateY: taglineTranslateY }],
            },
          ]}
        >
          <Text style={styles.tagline}>Preserving Memories, Forever</Text>
        </Animated.View>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoContainer: {
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  logo: {
    width: 120,
    height: 120,
  },
  appName: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 40,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  taglineContainer: {
    paddingHorizontal: 40,
  },
  tagline: {
    fontSize: 18,
    color: '#FFFFFF',
    textAlign: 'center',
    fontWeight: '500',
    letterSpacing: 0.5,
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
});
