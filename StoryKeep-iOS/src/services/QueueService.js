/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 * 
 * Queue Service - Manage offline photo uploads
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system';
import { photoAPI } from './api';

const QUEUE_KEY = '@photo_queue';
const QUEUE_PHOTOS_DIR = `${FileSystem.documentDirectory}queue_photos/`;

class QueueService {
  constructor() {
    this.queue = [];
    this.isProcessing = false;
    this.listeners = [];
  }

  async initialize() {
    try {
      await FileSystem.makeDirectoryAsync(QUEUE_PHOTOS_DIR, { intermediates: true });
    } catch (error) {
      // Directory might already exist
    }

    await this.loadQueue();
  }

  async loadQueue() {
    try {
      const queueData = await AsyncStorage.getItem(QUEUE_KEY);
      if (queueData) {
        this.queue = JSON.parse(queueData);
        this.notifyListeners();
      }
    } catch (error) {
      console.error('Error loading queue:', error);
    }
  }

  async saveQueue() {
    try {
      await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(this.queue));
      this.notifyListeners();
    } catch (error) {
      console.error('Error saving queue:', error);
    }
  }

  async addToQueue(photoUri, metadata = {}) {
    try {
      const timestamp = Date.now();
      const filename = `queued_${timestamp}.jpg`;
      const localPath = `${QUEUE_PHOTOS_DIR}${filename}`;

      await FileSystem.copyAsync({
        from: photoUri,
        to: localPath,
      });

      const queueItem = {
        id: timestamp.toString(),
        localPath,
        metadata,
        addedAt: new Date().toISOString(),
        retryCount: 0,
      };

      this.queue.push(queueItem);
      await this.saveQueue();

      return queueItem;
    } catch (error) {
      console.error('Error adding to queue:', error);
      throw error;
    }
  }

  async processQueue() {
    if (this.isProcessing || this.queue.length === 0) {
      return { processed: 0, failed: 0 };
    }

    this.isProcessing = true;
    let processed = 0;
    let failed = 0;

    const itemsToProcess = [...this.queue];

    for (const item of itemsToProcess) {
      try {
        const formData = new FormData();
        formData.append('image', {
          uri: item.localPath,
          type: 'image/jpeg',
          name: `photo_${item.id}.jpg`,
        });

        await photoAPI.detectAndExtract(formData);

        await FileSystem.deleteAsync(item.localPath, { idempotent: true });

        this.queue = this.queue.filter(q => q.id !== item.id);
        processed++;
      } catch (error) {
        console.error('Error uploading queued photo:', error);
        
        const itemIndex = this.queue.findIndex(q => q.id === item.id);
        if (itemIndex !== -1) {
          this.queue[itemIndex].retryCount++;
          
          if (this.queue[itemIndex].retryCount >= 3) {
            await FileSystem.deleteAsync(item.localPath, { idempotent: true });
            this.queue.splice(itemIndex, 1);
          }
        }
        failed++;
      }
    }

    await this.saveQueue();
    this.isProcessing = false;

    return { processed, failed };
  }

  async clearQueue() {
    try {
      for (const item of this.queue) {
        await FileSystem.deleteAsync(item.localPath, { idempotent: true });
      }

      this.queue = [];
      await this.saveQueue();
    } catch (error) {
      console.error('Error clearing queue:', error);
    }
  }

  getQueueCount() {
    return this.queue.length;
  }

  getQueue() {
    return [...this.queue];
  }

  addListener(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(cb => cb !== callback);
    };
  }

  notifyListeners() {
    this.listeners.forEach(callback => callback(this.queue.length));
  }
}

export default new QueueService();
