/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 * Data prefetching service for faster app loading
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { cacheService } from './CacheService';
import { BASE_URL } from './api';

class PrefetchService {
  constructor() {
    this.isPrefetching = false;
    this.prefetchPromise = null;
  }

  async startPrefetch() {
    if (this.isPrefetching) {
      return this.prefetchPromise;
    }

    this.isPrefetching = true;
    this.prefetchPromise = this._doPrefetch();

    try {
      await this.prefetchPromise;
    } finally {
      this.isPrefetching = false;
      this.prefetchPromise = null;
    }
  }

  async _doPrefetch() {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        console.log('No auth token, skipping prefetch');
        return;
      }

      console.log('Starting data prefetch...');

      await Promise.all([
        this.prefetchDashboard(token),
        this.prefetchGallery(token),
        this.prefetchVaults(token),
        this.prefetchProfile(token),
      ]);

      console.log('Prefetch complete');
    } catch (error) {
      console.error('Prefetch error:', error);
    }
  }

  async prefetchDashboard(token) {
    try {
      const response = await fetch(`${BASE_URL}/api/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        await cacheService.cacheDashboardData(data);
        console.log('Dashboard prefetched');
      }
    } catch (error) {
      console.error('Dashboard prefetch error:', error);
    }
  }

  async prefetchGallery(token) {
    try {
      const response = await fetch(`${BASE_URL}/api/photos?page=1&per_page=30&filter=all`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.photos) {
          await cacheService.cacheGalleryData(data.photos, data.pagination);
          console.log('Gallery prefetched:', data.photos.length, 'photos');
          
          this.prefetchThumbnails(data.photos.slice(0, 12), token);
        }
      }
    } catch (error) {
      console.error('Gallery prefetch error:', error);
    }
  }

  async prefetchVaults(token) {
    try {
      const response = await fetch(`${BASE_URL}/api/family/vaults`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        await cacheService.cacheVaultsData(data.vaults || []);
        console.log('Vaults prefetched');
      }
    } catch (error) {
      console.error('Vaults prefetch error:', error);
    }
  }

  async prefetchProfile(token) {
    try {
      const response = await fetch(`${BASE_URL}/api/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        await cacheService.cacheUserProfile(data);
        console.log('Profile prefetched');
      }
    } catch (error) {
      console.error('Profile prefetch error:', error);
    }
  }

  async prefetchThumbnails(photos, token) {
    try {
      for (const photo of photos) {
        const thumbnailUrl = photo.grid_thumbnail_url || photo.thumbnail_url;
        if (thumbnailUrl) {
          const fullUrl = thumbnailUrl.startsWith('http') 
            ? thumbnailUrl 
            : `${BASE_URL}${thumbnailUrl}`;
          
          await cacheService.cacheImage(fullUrl, token);
        }
      }
      console.log('Thumbnails prefetched:', photos.length);
    } catch (error) {
      console.error('Thumbnail prefetch error:', error);
    }
  }

  async clearPrefetchedData() {
    await cacheService.clearAllCaches();
  }
}

export const prefetchService = new PrefetchService();
export default prefetchService;
