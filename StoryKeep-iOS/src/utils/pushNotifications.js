/**
 * Push Notification Utility for Expo Notifications
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import { authAPI } from '../services/api';

// Configure how notifications are handled when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

/**
 * Register for push notifications and get Expo push token
 */
export async function registerForPushNotifications() {
  let token;

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#E85D75',
    });
  }

  if (Device.isDevice) {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    if (finalStatus !== 'granted') {
      console.log('Push notification permission denied');
      return null;
    }
    
    // Get Expo push token
    try {
      token = (await Notifications.getExpoPushTokenAsync({
        projectId: 'd2nwcbs-anonymous', // Your Expo project ID
      })).data;
      console.log('📱 Expo Push Token:', token);
      
      // Register token with backend
      await authAPI.registerPushToken(token);
      
    } catch (error) {
      console.error('Error getting push token:', error);
      return null;
    }
  } else {
    console.log('Must use physical device for push notifications');
  }

  return token;
}

/**
 * Setup notification listeners
 * @param {Function} onNotificationReceived - Callback when notification received in foreground
 * @param {Function} onNotificationTapped - Callback when notification is tapped
 * @returns {Object} Subscription objects to cleanup on unmount
 */
export function setupNotificationListeners(onNotificationReceived, onNotificationTapped) {
  // Listener for notifications received while app is in foreground
  const notificationListener = Notifications.addNotificationReceivedListener(notification => {
    console.log('📬 Notification received:', notification);
    if (onNotificationReceived) {
      onNotificationReceived(notification);
    }
  });

  // Listener for when user taps on notification
  const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
    console.log('👆 Notification tapped:', response);
    if (onNotificationTapped) {
      const data = response.notification.request.content.data;
      onNotificationTapped(data);
    }
  });

  return {
    notificationListener,
    responseListener,
  };
}

/**
 * Handle navigation based on notification data
 * @param {Object} navigation - React Navigation object
 * @param {Object} notificationData - Data from notification
 */
export function handleNotificationNavigation(navigation, notificationData) {
  const { type, vault_id, photo_id } = notificationData;

  if (type === 'vault_update' && vault_id) {
    // Navigate to vault detail screen
    navigation.navigate('VaultDetail', { vaultId: vault_id });
  } else if (photo_id) {
    // Navigate to photo detail screen
    navigation.navigate('PhotoDetail', { photoId: photo_id });
  }
}
