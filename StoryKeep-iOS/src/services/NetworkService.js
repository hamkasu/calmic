/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 * 
 * Network Service - Monitor connectivity status
 */

import NetInfo from '@react-native-community/netinfo';

class NetworkService {
  constructor() {
    this.isConnected = true;
    this.listeners = [];
    this.unsubscribe = null;
  }

  initialize() {
    this.unsubscribe = NetInfo.addEventListener(state => {
      const wasConnected = this.isConnected;
      this.isConnected = state.isConnected;
      
      if (wasConnected !== this.isConnected) {
        this.notifyListeners(this.isConnected);
      }
    });

    NetInfo.fetch().then(state => {
      this.isConnected = state.isConnected;
    });
  }

  cleanup() {
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  }

  addListener(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(cb => cb !== callback);
    };
  }

  notifyListeners(isConnected) {
    this.listeners.forEach(callback => callback(isConnected));
  }

  getConnectionStatus() {
    return this.isConnected;
  }
}

export default new NetworkService();
