/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 * Offline cache service for photos and gallery data
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system/legacy';

const CACHE_KEYS = {
  GALLERY_DATA: 'gallery_cache',
  DASHBOARD_DATA: 'dashboard_cache',
  VAULTS_DATA: 'vaults_cache',
  USER_PROFILE: 'profile_cache',
  PREFETCH_STATUS: 'prefetch_status',
};

const CACHE_EXPIRY = {
  GALLERY: 5 * 60 * 1000,  // 5 minutes
  DASHBOARD: 2 * 60 * 1000, // 2 minutes
  VAULTS: 10 * 60 * 1000,   // 10 minutes
  PROFILE: 30 * 60 * 1000,  // 30 minutes
};

const IMAGE_CACHE_DIR = FileSystem.cacheDirectory + 'image_cache/';

class CacheService {
  constructor() {
    this.memoryCache = new Map();
    this.initImageCacheDir();
  }

  async initImageCacheDir() {
    try {
      const dirInfo = await FileSystem.getInfoAsync(IMAGE_CACHE_DIR);
      if (!dirInfo.exists) {
        await FileSystem.makeDirectoryAsync(IMAGE_CACHE_DIR, { intermediates: true });
      }
    } catch (error) {
      console.error('Failed to create image cache directory:', error);
    }
  }

  async setCache(key, data, expiryMs = CACHE_EXPIRY.GALLERY) {
    try {
      const cacheData = {
        data,
        timestamp: Date.now(),
        expiry: expiryMs,
      };
      this.memoryCache.set(key, cacheData);
      await AsyncStorage.setItem(key, JSON.stringify(cacheData));
    } catch (error) {
      console.error('Cache set error:', error);
    }
  }

  async getCache(key) {
    try {
      if (this.memoryCache.has(key)) {
        const cached = this.memoryCache.get(key);
        if (Date.now() - cached.timestamp < cached.expiry) {
          return cached.data;
        }
        this.memoryCache.delete(key);
      }

      const stored = await AsyncStorage.getItem(key);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Date.now() - parsed.timestamp < parsed.expiry) {
          this.memoryCache.set(key, parsed);
          return parsed.data;
        }
        await AsyncStorage.removeItem(key);
      }
      return null;
    } catch (error) {
      console.error('Cache get error:', error);
      return null;
    }
  }

  async clearCache(key) {
    try {
      this.memoryCache.delete(key);
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error('Cache clear error:', error);
    }
  }

  async clearAllCaches() {
    try {
      this.memoryCache.clear();
      const keys = Object.values(CACHE_KEYS);
      await AsyncStorage.multiRemove(keys);
      await this.clearImageCache();
    } catch (error) {
      console.error('Clear all caches error:', error);
    }
  }

  async cacheGalleryData(photos, pagination = null) {
    await this.setCache(CACHE_KEYS.GALLERY_DATA, { photos, pagination }, CACHE_EXPIRY.GALLERY);
  }

  async getCachedGallery() {
    return await this.getCache(CACHE_KEYS.GALLERY_DATA);
  }

  async cacheDashboardData(data) {
    await this.setCache(CACHE_KEYS.DASHBOARD_DATA, data, CACHE_EXPIRY.DASHBOARD);
  }

  async getCachedDashboard() {
    return await this.getCache(CACHE_KEYS.DASHBOARD_DATA);
  }

  async cacheVaultsData(vaults) {
    await this.setCache(CACHE_KEYS.VAULTS_DATA, vaults, CACHE_EXPIRY.VAULTS);
  }

  async getCachedVaults() {
    return await this.getCache(CACHE_KEYS.VAULTS_DATA);
  }

  async cacheUserProfile(profile) {
    await this.setCache(CACHE_KEYS.USER_PROFILE, profile, CACHE_EXPIRY.PROFILE);
  }

  async getCachedProfile() {
    return await this.getCache(CACHE_KEYS.USER_PROFILE);
  }

  getImageCachePath(url) {
    const hash = this.hashUrl(url);
    const ext = url.split('.').pop()?.split('?')[0] || 'jpg';
    return IMAGE_CACHE_DIR + hash + '.' + ext;
  }

  hashUrl(url) {
    let hash = 0;
    for (let i = 0; i < url.length; i++) {
      const char = url.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
  }

  async cacheImage(url, authToken) {
    try {
      const cachePath = this.getImageCachePath(url);
      const fileInfo = await FileSystem.getInfoAsync(cachePath);
      
      if (fileInfo.exists) {
        return cachePath;
      }

      const downloadResult = await FileSystem.downloadAsync(
        url,
        cachePath,
        {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        }
      );

      return downloadResult.uri;
    } catch (error) {
      console.error('Image cache error:', error);
      return null;
    }
  }

  async getCachedImage(url) {
    try {
      const cachePath = this.getImageCachePath(url);
      const fileInfo = await FileSystem.getInfoAsync(cachePath);
      return fileInfo.exists ? cachePath : null;
    } catch (error) {
      return null;
    }
  }

  async clearImageCache() {
    try {
      const dirInfo = await FileSystem.getInfoAsync(IMAGE_CACHE_DIR);
      if (dirInfo.exists) {
        await FileSystem.deleteAsync(IMAGE_CACHE_DIR, { idempotent: true });
        await FileSystem.makeDirectoryAsync(IMAGE_CACHE_DIR, { intermediates: true });
      }
    } catch (error) {
      console.error('Clear image cache error:', error);
    }
  }

  async getImageCacheSize() {
    try {
      const dirInfo = await FileSystem.getInfoAsync(IMAGE_CACHE_DIR);
      if (!dirInfo.exists) return 0;

      const files = await FileSystem.readDirectoryAsync(IMAGE_CACHE_DIR);
      let totalSize = 0;
      
      for (const file of files) {
        const fileInfo = await FileSystem.getInfoAsync(IMAGE_CACHE_DIR + file);
        if (fileInfo.exists && fileInfo.size) {
          totalSize += fileInfo.size;
        }
      }
      
      return totalSize;
    } catch (error) {
      console.error('Get cache size error:', error);
      return 0;
    }
  }

  formatCacheSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }
}

export const cacheService = new CacheService();
export default cacheService;
