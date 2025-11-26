/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 * 
 * Image caching utility for faster photo loading
 */

import * as FileSystem from 'expo-file-system/legacy';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_DIR = FileSystem.cacheDirectory + 'images/';
const CACHE_INDEX_KEY = 'imageCacheIndex';
const MAX_CACHE_SIZE = 100 * 1024 * 1024; // 100MB max cache
const MAX_CACHE_ITEMS = 200; // Max 200 images cached

class ImageCache {
  constructor() {
    this.cacheIndex = {};
    this.initialized = false;
    this.initPromise = null;
  }

  async init() {
    if (this.initialized) return;
    if (this.initPromise) return this.initPromise;

    this.initPromise = this._initialize();
    await this.initPromise;
  }

  async _initialize() {
    try {
      // Ensure cache directory exists
      const dirInfo = await FileSystem.getInfoAsync(CACHE_DIR);
      if (!dirInfo.exists) {
        await FileSystem.makeDirectoryAsync(CACHE_DIR, { intermediates: true });
      }

      // Load cache index
      const indexStr = await AsyncStorage.getItem(CACHE_INDEX_KEY);
      if (indexStr) {
        this.cacheIndex = JSON.parse(indexStr);
      }

      // Clean up stale entries
      await this.cleanupStaleEntries();

      this.initialized = true;
    } catch (error) {
      console.error('ImageCache init error:', error);
      this.initialized = true;
    }
  }

  async cleanupStaleEntries() {
    const validEntries = {};
    for (const [key, entry] of Object.entries(this.cacheIndex)) {
      try {
        const fileInfo = await FileSystem.getInfoAsync(entry.path);
        if (fileInfo.exists) {
          validEntries[key] = entry;
        }
      } catch {
        // Entry is stale, skip it
      }
    }
    this.cacheIndex = validEntries;
    await this.saveIndex();
  }

  getCacheKey(url) {
    // Create a unique key from the URL
    return url.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 100) + '_' + 
           url.split('/').pop()?.split('?')[0] || 'image';
  }

  async getCachedPath(url) {
    await this.init();
    
    const key = this.getCacheKey(url);
    const entry = this.cacheIndex[key];
    
    if (entry) {
      try {
        const fileInfo = await FileSystem.getInfoAsync(entry.path);
        if (fileInfo.exists) {
          // Update last accessed time
          this.cacheIndex[key].lastAccessed = Date.now();
          this.saveIndex();
          return entry.path;
        }
      } catch {
        // File doesn't exist, remove from index
        delete this.cacheIndex[key];
        this.saveIndex();
      }
    }
    
    return null;
  }

  async cacheImage(url, authToken) {
    await this.init();
    
    const key = this.getCacheKey(url);
    
    // Check if already cached
    const cachedPath = await this.getCachedPath(url);
    if (cachedPath) {
      return cachedPath;
    }

    try {
      // Download the image
      const filename = key + '.jpg';
      const filePath = CACHE_DIR + filename;
      
      const downloadResult = await FileSystem.downloadAsync(
        url,
        filePath,
        {
          headers: authToken ? {
            'Authorization': `Bearer ${authToken}`
          } : {}
        }
      );

      if (downloadResult.status === 200) {
        // Get file size
        const fileInfo = await FileSystem.getInfoAsync(filePath);
        
        // Add to cache index
        this.cacheIndex[key] = {
          path: filePath,
          url: url,
          size: fileInfo.size || 0,
          cachedAt: Date.now(),
          lastAccessed: Date.now()
        };
        
        await this.saveIndex();
        
        // Check if we need to prune cache
        await this.pruneCache();
        
        return filePath;
      }
    } catch (error) {
      console.error('Error caching image:', error);
    }
    
    return null;
  }

  async saveIndex() {
    try {
      await AsyncStorage.setItem(CACHE_INDEX_KEY, JSON.stringify(this.cacheIndex));
    } catch (error) {
      console.error('Error saving cache index:', error);
    }
  }

  async pruneCache() {
    const entries = Object.entries(this.cacheIndex);
    
    // Check number of items
    if (entries.length > MAX_CACHE_ITEMS) {
      // Sort by last accessed (oldest first)
      entries.sort((a, b) => a[1].lastAccessed - b[1].lastAccessed);
      
      // Remove oldest entries
      const toRemove = entries.slice(0, entries.length - MAX_CACHE_ITEMS);
      for (const [key, entry] of toRemove) {
        try {
          await FileSystem.deleteAsync(entry.path, { idempotent: true });
        } catch {}
        delete this.cacheIndex[key];
      }
      
      await this.saveIndex();
    }
    
    // Check total size
    let totalSize = Object.values(this.cacheIndex).reduce((sum, e) => sum + (e.size || 0), 0);
    
    if (totalSize > MAX_CACHE_SIZE) {
      const entries = Object.entries(this.cacheIndex);
      entries.sort((a, b) => a[1].lastAccessed - b[1].lastAccessed);
      
      for (const [key, entry] of entries) {
        if (totalSize <= MAX_CACHE_SIZE * 0.8) break; // Keep under 80%
        
        try {
          await FileSystem.deleteAsync(entry.path, { idempotent: true });
        } catch {}
        totalSize -= entry.size || 0;
        delete this.cacheIndex[key];
      }
      
      await this.saveIndex();
    }
  }

  async clearCache() {
    try {
      await FileSystem.deleteAsync(CACHE_DIR, { idempotent: true });
      await FileSystem.makeDirectoryAsync(CACHE_DIR, { intermediates: true });
      this.cacheIndex = {};
      await AsyncStorage.removeItem(CACHE_INDEX_KEY);
    } catch (error) {
      console.error('Error clearing cache:', error);
    }
  }

  async getCacheStats() {
    await this.init();
    
    const entries = Object.values(this.cacheIndex);
    const totalSize = entries.reduce((sum, e) => sum + (e.size || 0), 0);
    
    return {
      itemCount: entries.length,
      totalSizeMB: (totalSize / (1024 * 1024)).toFixed(2),
      maxSizeMB: (MAX_CACHE_SIZE / (1024 * 1024)).toFixed(0)
    };
  }
}

export const imageCache = new ImageCache();
export default imageCache;
