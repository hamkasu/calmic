/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 * Skeleton loading component for smooth loading placeholders
 */

import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');

const SkeletonPulse = ({ style, children }) => {
  const shimmerAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const shimmer = Animated.loop(
      Animated.timing(shimmerAnim, {
        toValue: 1,
        duration: 1200,
        useNativeDriver: true,
      })
    );
    shimmer.start();
    return () => shimmer.stop();
  }, []);

  const translateX = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-width, width],
  });

  return (
    <View style={[styles.skeletonBase, style]}>
      <Animated.View
        style={[
          styles.shimmer,
          { transform: [{ translateX }] },
        ]}
      >
        <LinearGradient
          colors={['transparent', 'rgba(255,255,255,0.3)', 'transparent']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={StyleSheet.absoluteFill}
        />
      </Animated.View>
      {children}
    </View>
  );
};

export const PhotoGridSkeleton = ({ columns = 3, count = 12 }) => {
  const itemWidth = (width - 6) / columns;
  
  return (
    <View style={styles.gridContainer}>
      {Array(count).fill(0).map((_, index) => (
        <SkeletonPulse 
          key={index} 
          style={[styles.gridItem, { width: itemWidth, height: itemWidth }]} 
        />
      ))}
    </View>
  );
};

export const PhotoDetailSkeleton = () => (
  <View style={styles.detailContainer}>
    <SkeletonPulse style={styles.detailImage} />
    <View style={styles.detailMeta}>
      <SkeletonPulse style={styles.detailTitle} />
      <SkeletonPulse style={styles.detailDate} />
      <View style={styles.detailActions}>
        <SkeletonPulse style={styles.actionButton} />
        <SkeletonPulse style={styles.actionButton} />
        <SkeletonPulse style={styles.actionButton} />
      </View>
    </View>
  </View>
);

export const DashboardSkeleton = () => (
  <View style={styles.dashboardContainer}>
    <SkeletonPulse style={styles.dashboardAvatar} />
    <SkeletonPulse style={styles.dashboardName} />
    <SkeletonPulse style={styles.dashboardPlan} />
    <View style={styles.statsRow}>
      <SkeletonPulse style={styles.statCard} />
      <SkeletonPulse style={styles.statCard} />
      <SkeletonPulse style={styles.statCard} />
    </View>
    <View style={styles.statsRow}>
      <SkeletonPulse style={styles.statCard} />
      <SkeletonPulse style={styles.statCard} />
      <SkeletonPulse style={styles.statCard} />
    </View>
    <SkeletonPulse style={styles.recentSection} />
  </View>
);

export const VaultListSkeleton = ({ count = 4 }) => (
  <View style={styles.vaultListContainer}>
    {Array(count).fill(0).map((_, index) => (
      <SkeletonPulse key={index} style={styles.vaultCard} />
    ))}
  </View>
);

export const ImageSkeleton = ({ style }) => (
  <SkeletonPulse style={[styles.imageSkeleton, style]} />
);

export default SkeletonPulse;

const styles = StyleSheet.create({
  skeletonBase: {
    backgroundColor: '#E1E9EE',
    overflow: 'hidden',
    borderRadius: 4,
  },
  shimmer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    width: '100%',
  },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 1,
  },
  gridItem: {
    margin: 1,
    borderRadius: 8,
  },
  detailContainer: {
    padding: 16,
  },
  detailImage: {
    width: '100%',
    height: width - 32,
    borderRadius: 12,
    marginBottom: 16,
  },
  detailMeta: {
    gap: 12,
  },
  detailTitle: {
    height: 24,
    width: '60%',
    borderRadius: 4,
  },
  detailDate: {
    height: 16,
    width: '40%',
    borderRadius: 4,
  },
  detailActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  actionButton: {
    height: 44,
    width: 80,
    borderRadius: 8,
  },
  dashboardContainer: {
    padding: 20,
    alignItems: 'center',
  },
  dashboardAvatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    marginBottom: 16,
  },
  dashboardName: {
    height: 24,
    width: 150,
    borderRadius: 4,
    marginBottom: 8,
  },
  dashboardPlan: {
    height: 20,
    width: 100,
    borderRadius: 10,
    marginBottom: 24,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
    width: '100%',
  },
  statCard: {
    flex: 1,
    height: 80,
    borderRadius: 12,
  },
  recentSection: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    marginTop: 16,
  },
  vaultListContainer: {
    padding: 16,
    gap: 12,
  },
  vaultCard: {
    height: 100,
    width: '100%',
    borderRadius: 12,
  },
  imageSkeleton: {
    backgroundColor: '#E1E9EE',
  },
});
