/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';

export default function ProgressBar({ progress, message, color = '#E85D75', showPercentage = true }) {
  const animatedWidth = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(animatedWidth, {
      toValue: progress,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [progress]);

  const widthInterpolated = animatedWidth.interpolate({
    inputRange: [0, 100],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={styles.container}>
      {message && <Text style={styles.message}>{message}</Text>}
      <View style={styles.progressBarContainer}>
        <Animated.View 
          style={[
            styles.progressBarFill, 
            { 
              width: widthInterpolated,
              backgroundColor: color 
            }
          ]} 
        />
      </View>
      {showPercentage && (
        <Text style={styles.percentage}>{Math.round(progress)}%</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  message: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    textAlign: 'center',
  },
  progressBarContainer: {
    height: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  percentage: {
    fontSize: 12,
    color: '#999',
    marginTop: 6,
    textAlign: 'center',
    fontWeight: '600',
  },
});
