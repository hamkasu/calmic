/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 * 
 * Cached Image component for faster loading with blur placeholder
 */

import React, { useState, useEffect, memo } from 'react';
import { Image, View, ActivityIndicator, StyleSheet, Animated } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import imageCache from '../utils/ImageCache';

const CachedImage = memo(({ 
  source, 
  style, 
  resizeMode = 'cover',
  showPlaceholder = true,
  placeholderColor = '#f0f0f0',
  ...props 
}) => {
  const [cachedUri, setCachedUri] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const fadeAnim = useState(new Animated.Value(0))[0];

  useEffect(() => {
    loadToken();
  }, []);

  useEffect(() => {
    if (authToken && source?.uri) {
      loadCachedImage();
    }
  }, [source?.uri, authToken]);

  const loadToken = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      setAuthToken(token);
    } catch (err) {
      console.error('Error loading auth token:', err);
    }
  };

  const loadCachedImage = async () => {
    if (!source?.uri) return;

    setLoading(true);
    setError(false);

    try {
      // First, try to get from cache
      let path = await imageCache.getCachedPath(source.uri);
      
      if (path) {
        setCachedUri(path);
        setLoading(false);
        animateIn();
        return;
      }

      // Not in cache, download and cache it
      path = await imageCache.cacheImage(source.uri, authToken);
      
      if (path) {
        setCachedUri(path);
      } else {
        // Fallback to direct URL with auth header
        setCachedUri(null);
      }
    } catch (err) {
      console.error('Error loading cached image:', err);
      setCachedUri(null);
    } finally {
      setLoading(false);
    }
  };

  const animateIn = () => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 200,
      useNativeDriver: true,
    }).start();
  };

  const handleLoad = () => {
    setLoading(false);
    animateIn();
  };

  const handleError = () => {
    setError(true);
    setLoading(false);
    // If cache failed, try direct load
    if (cachedUri) {
      setCachedUri(null);
    }
  };

  const imageSource = cachedUri 
    ? { uri: cachedUri }
    : { 
        uri: source?.uri,
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {}
      };

  return (
    <View style={[styles.container, style]}>
      {showPlaceholder && loading && (
        <View style={[styles.placeholder, { backgroundColor: placeholderColor }]}>
          <ActivityIndicator size="small" color="#E85D75" />
        </View>
      )}
      
      {source?.uri && (
        <Animated.Image
          {...props}
          source={imageSource}
          style={[
            styles.image, 
            style, 
            { opacity: fadeAnim }
          ]}
          resizeMode={resizeMode}
          onLoad={handleLoad}
          onError={handleError}
        />
      )}
      
      {error && !loading && (
        <View style={[styles.placeholder, { backgroundColor: '#f8f8f8' }]}>
          <ActivityIndicator size="small" color="#ccc" />
        </View>
      )}
    </View>
  );
});

const styles = StyleSheet.create({
  container: {
    overflow: 'hidden',
    backgroundColor: '#f5f5f5',
  },
  placeholder: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    width: '100%',
    height: '100%',
  },
});

CachedImage.displayName = 'CachedImage';

export default CachedImage;
