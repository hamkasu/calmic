import React, { useEffect, useRef, useState } from 'react';
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

// Floating particle component
const Particle = ({ delay, leftPosition }) => {
  const translateY = useRef(new Animated.Value(height + 50)).current;
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.delay(delay),
        Animated.parallel([
          Animated.timing(opacity, {
            toValue: 0.7,
            duration: 600,
            useNativeDriver: true,
          }),
          Animated.timing(translateY, {
            toValue: -100,
            duration: 4500,
            useNativeDriver: true,
          }),
        ]),
        Animated.timing(opacity, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
        // Reset for loop
        Animated.timing(translateY, {
          toValue: height + 50,
          duration: 0,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.particle,
        {
          left: leftPosition,
          opacity,
          transform: [{ translateY }],
        },
      ]}
    />
  );
};

// Camera aperture blade component
const ApertureBlade = ({ index, rotation, scale }) => {
  const angle = (index * 360) / 8;
  
  return (
    <Animated.View
      style={[
        styles.apertureBlade,
        {
          transform: [
            { rotate: `${angle}deg` },
            { 
              rotate: rotation.interpolate({
                inputRange: [0, 1],
                outputRange: ['0deg', '45deg'],
              }),
            },
            { 
              scale: scale.interpolate({
                inputRange: [0, 1],
                outputRange: [1, 0.05],
              }),
            },
          ],
        },
      ]}
    />
  );
};

export default function SplashScreen({ onFinish }) {
  // Generate random positions for particles
  const [particles] = useState(
    Array.from({ length: 20 }, (_, i) => ({
      delay: i * 200,
      left: Math.random() * width,
    }))
  );

  // Aperture animation
  const apertureRotation = useRef(new Animated.Value(0)).current;
  const apertureScale = useRef(new Animated.Value(0)).current;
  
  // Logo animations
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoScale = useRef(new Animated.Value(0.3)).current;
  const logoGlow = useRef(new Animated.Value(0)).current;
  
  // Text animations
  const appNameOpacity = useRef(new Animated.Value(0)).current;
  const appNameScale = useRef(new Animated.Value(0.95)).current;
  
  // Tagline animations
  const taglineOpacity = useRef(new Animated.Value(0)).current;
  const taglineTranslateY = useRef(new Animated.Value(20)).current;
  const taglineGlow = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let sound = null;

    const playChimeSound = async () => {
      try {
        await Audio.setAudioModeAsync({
          playsInSilentModeIOS: true,
          staysActiveInBackground: false,
        });

        const { sound: chimeSound } = await Audio.Sound.createAsync(
          require('../assets/sounds/chime.mp3'),
          { shouldPlay: true, volume: 0.5 }
        );
        sound = chimeSound;
      } catch (error) {
        console.log('Audio playback failed:', error);
      }
    };

    playChimeSound();

    // Optimized animation sequence - total ~2.5s
    Animated.sequence([
      // 1. Camera aperture opens (0-700ms)
      Animated.parallel([
        Animated.timing(apertureRotation, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(apertureScale, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        // Logo starts fading in during aperture opening (400ms delay, 600ms duration)
        Animated.sequence([
          Animated.delay(400),
          Animated.parallel([
            Animated.timing(logoOpacity, {
              toValue: 1,
              duration: 600,
              useNativeDriver: true,
            }),
            Animated.spring(logoScale, {
              toValue: 1,
              friction: 6,
              tension: 40,
              useNativeDriver: true,
            }),
            // Logo glow
            Animated.timing(logoGlow, {
              toValue: 1,
              duration: 500,
              useNativeDriver: true,
            }),
          ]),
        ]),
      ]),
      
      // 2. App name fades in with logo (starts at 1000ms)
      Animated.parallel([
        Animated.timing(appNameOpacity, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
        Animated.spring(appNameScale, {
          toValue: 1,
          friction: 8,
          tension: 50,
          useNativeDriver: true,
        }),
        // Tagline starts after small delay (200ms into this phase)
        Animated.sequence([
          Animated.delay(200),
          Animated.parallel([
            Animated.timing(taglineOpacity, {
              toValue: 1,
              duration: 500,
              useNativeDriver: true,
            }),
            Animated.timing(taglineTranslateY, {
              toValue: 0,
              duration: 500,
              useNativeDriver: true,
            }),
            Animated.timing(taglineGlow, {
              toValue: 1,
              duration: 500,
              useNativeDriver: true,
            }),
          ]),
        ]),
      ]),
      
      // Hold before transition (total: 700 + 500 + 200 + 500 + 600 = 2500ms)
      Animated.delay(600),
      
    ]).start(() => {
      if (onFinish) {
        onFinish();
      }
    });

    return () => {
      if (sound) {
        sound.unloadAsync();
      }
    };
  }, []);

  return (
    <LinearGradient
      colors={['#1a1a2e', '#16213e', '#533483']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.container}
    >
      {/* Floating particles - behind everything */}
      <View style={styles.particlesLayer}>
        {particles.map((particle, i) => (
          <Particle key={i} delay={particle.delay} leftPosition={particle.left} />
        ))}
      </View>

      {/* Content - logo and text */}
      <View style={styles.content}>
        {/* Logo with glow effect */}
        <Animated.View
          style={[
            styles.logoContainer,
            {
              opacity: logoOpacity,
              transform: [{ scale: logoScale }],
            },
          ]}
        >
          <Animated.View
            style={[
              styles.logoGlow,
              {
                opacity: logoGlow.interpolate({
                  inputRange: [0, 1],
                  outputRange: [0, 0.4],
                }),
              },
            ]}
          />
          <Image
            source={require('../assets/logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />
        </Animated.View>

        {/* App Name with elegant reveal */}
        <Animated.Text
          style={[
            styles.appName,
            {
              opacity: appNameOpacity,
              transform: [{ scale: appNameScale }],
            },
          ]}
        >
          StoryKeep
        </Animated.Text>

        {/* Tagline with glow */}
        <Animated.View
          style={[
            styles.taglineContainer,
            {
              opacity: taglineOpacity,
              transform: [{ translateY: taglineTranslateY }],
            },
          ]}
        >
          <Animated.View
            style={[
              styles.taglineGlow,
              {
                opacity: taglineGlow.interpolate({
                  inputRange: [0, 1],
                  outputRange: [0, 0.3],
                }),
              },
            ]}
          />
          <Text style={styles.tagline}>Preserving Memories, Forever</Text>
        </Animated.View>
      </View>

      {/* Camera aperture overlay - ABOVE everything to reveal content */}
      <Animated.View
        style={[
          styles.apertureContainer,
          {
            opacity: apertureScale.interpolate({
              inputRange: [0, 0.5, 1],
              outputRange: [1, 1, 0],
            }),
          },
        ]}
        pointerEvents="none"
      >
        {Array.from({ length: 8 }, (_, i) => (
          <ApertureBlade
            key={i}
            index={i}
            rotation={apertureRotation}
            scale={apertureScale}
          />
        ))}
      </Animated.View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  
  // Particles layer
  particlesLayer: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    zIndex: 1,
  },
  particle: {
    position: 'absolute',
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: '#d4af37',
    bottom: 0,
  },
  
  // Content layer
  content: {
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  
  // Camera Aperture - above content to reveal it
  apertureContainer: {
    position: 'absolute',
    width: 350,
    height: 350,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 100,
  },
  apertureBlade: {
    position: 'absolute',
    width: 175,
    height: 350,
    backgroundColor: '#0a0a14',
  },
  
  // Logo
  logoContainer: {
    marginBottom: 24,
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
  },
  logo: {
    width: 130,
    height: 130,
  },
  logoGlow: {
    position: 'absolute',
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: '#d4af37',
    shadowColor: '#d4af37',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 30,
  },
  
  // App Name
  appName: {
    fontSize: 42,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 50,
    letterSpacing: 3,
    textShadowColor: '#d4af37',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 15,
  },
  
  // Tagline
  taglineContainer: {
    paddingHorizontal: 50,
    position: 'relative',
    alignItems: 'center',
  },
  tagline: {
    fontSize: 17,
    color: '#FFFFFF',
    textAlign: 'center',
    fontWeight: '400',
    letterSpacing: 1.5,
    opacity: 0.95,
    textShadowColor: 'rgba(212, 175, 55, 0.3)',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 8,
  },
  taglineGlow: {
    position: 'absolute',
    width: '120%',
    height: 40,
    backgroundColor: '#d4af37',
    borderRadius: 20,
    shadowColor: '#d4af37',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 15,
  },
});
