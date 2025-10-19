import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { useLoading } from '../contexts/LoadingContext';

const LoadingOverlay = () => {
  const { isLoading, loadingCount, currentMessage } = useLoading();

  if (!isLoading) return null;

  return (
    <View style={styles.overlay}>
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#fff" />
        <Text style={styles.message}>{currentMessage}</Text>
        {loadingCount > 1 && (
          <View style={styles.counterBadge}>
            <Text style={styles.counterText}>{loadingCount}</Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
  },
  container: {
    backgroundColor: '#333',
    borderRadius: 15,
    padding: 30,
    alignItems: 'center',
    minWidth: 150,
    position: 'relative',
  },
  message: {
    color: '#fff',
    fontSize: 16,
    marginTop: 15,
    textAlign: 'center',
  },
  counterBadge: {
    position: 'absolute',
    top: -10,
    right: -10,
    backgroundColor: '#FF6B6B',
    borderRadius: 15,
    width: 30,
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#333',
  },
  counterText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default LoadingOverlay;
