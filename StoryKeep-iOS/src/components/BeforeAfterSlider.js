/**
 * Before/After Slider Component
 * Interactive comparison slider for original vs enhanced photos
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React, { useState } from 'react';
import { View, Image, StyleSheet, Dimensions, Text } from 'react-native';
import { PanGestureHandler } from 'react-native-gesture-handler';
import { LinearGradient } from 'expo-linear-gradient';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function BeforeAfterSlider({ beforeImage, afterImage, height = 400 }) {
  const [sliderPosition, setSliderPosition] = useState(SCREEN_WIDTH / 2);

  const handleGesture = (event) => {
    const { translationX } = event.nativeEvent;
    const newPosition = Math.max(0, Math.min(SCREEN_WIDTH, sliderPosition + translationX));
    setSliderPosition(newPosition);
  };

  const handleGestureEnd = (event) => {
    const { translationX } = event.nativeEvent;
    const finalPosition = Math.max(0, Math.min(SCREEN_WIDTH, sliderPosition + translationX));
    setSliderPosition(finalPosition);
  };

  return (
    <View style={[styles.container, { height }]}>
      {/* After image (full width) */}
      <Image
        source={{ uri: afterImage }}
        style={styles.fullImage}
        resizeMode="cover"
      />

      {/* Before image (clipped by slider) */}
      <View style={[styles.beforeContainer, { width: sliderPosition }]}>
        <Image
          source={{ uri: beforeImage }}
          style={[styles.fullImage, { width: SCREEN_WIDTH }]}
          resizeMode="cover"
        />
      </View>

      {/* Labels */}
      <View style={styles.labelContainer}>
        <View style={styles.label}>
          <Text style={styles.labelText}>ORIGINAL</Text>
        </View>
        <View style={styles.label}>
          <Text style={styles.labelText}>ENHANCED</Text>
        </View>
      </View>

      {/* Draggable slider handle */}
      <PanGestureHandler
        onGestureEvent={handleGesture}
        onEnded={handleGestureEnd}
      >
        <View style={[styles.sliderContainer, { left: sliderPosition - 2 }]}>
          {/* Vertical line */}
          <View style={styles.sliderLine} />
          
          {/* Handle */}
          <View style={styles.sliderHandle}>
            <LinearGradient
              colors={['#E85D75', '#FF8BA0']}
              style={styles.handleGradient}
            >
              <View style={styles.handleArrowLeft}>
                <Text style={styles.handleArrowText}>◀</Text>
              </View>
              <View style={styles.handleArrowRight}>
                <Text style={styles.handleArrowText}>▶</Text>
              </View>
            </LinearGradient>
          </View>
        </View>
      </PanGestureHandler>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: SCREEN_WIDTH,
    position: 'relative',
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  fullImage: {
    width: SCREEN_WIDTH,
    height: '100%',
  },
  beforeContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    height: '100%',
    overflow: 'hidden',
  },
  labelContainer: {
    position: 'absolute',
    top: 20,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    pointerEvents: 'none',
  },
  label: {
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
  },
  labelText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 1,
  },
  sliderContainer: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: 4,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sliderLine: {
    width: 4,
    height: '100%',
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 4,
    elevation: 5,
  },
  sliderHandle: {
    position: 'absolute',
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 5,
  },
  handleGradient: {
    width: 54,
    height: 54,
    borderRadius: 27,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  handleArrowLeft: {
    width: 18,
    height: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  handleArrowRight: {
    width: 18,
    height: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  handleArrowText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
});
