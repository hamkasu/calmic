/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 * Image compression utilities for faster uploads
 */

import * as ImageManipulator from 'expo-image-manipulator';
import * as FileSystem from 'expo-file-system/legacy';

const COMPRESSION_SETTINGS = {
  HIGH_QUALITY: { compress: 0.9, maxDimension: 2400 },
  BALANCED: { compress: 0.8, maxDimension: 1920 },
  FAST_UPLOAD: { compress: 0.7, maxDimension: 1600 },
  THUMBNAIL: { compress: 0.6, maxDimension: 400 },
};

export const getFileSizeInMB = async (uri) => {
  try {
    const fileInfo = await FileSystem.getInfoAsync(uri);
    return fileInfo.size ? fileInfo.size / (1024 * 1024) : 0;
  } catch (error) {
    console.error('Error getting file size:', error);
    return 0;
  }
};

export const compressImage = async (uri, quality = 'BALANCED') => {
  try {
    const settings = COMPRESSION_SETTINGS[quality] || COMPRESSION_SETTINGS.BALANCED;
    const originalSize = await getFileSizeInMB(uri);
    
    console.log(`Compressing image: ${originalSize.toFixed(2)} MB`);

    const actions = [];
    
    const result = await ImageManipulator.manipulateAsync(
      uri,
      actions,
      {
        compress: settings.compress,
        format: ImageManipulator.SaveFormat.JPEG,
      }
    );

    const compressedSize = await getFileSizeInMB(result.uri);
    const savings = ((originalSize - compressedSize) / originalSize * 100).toFixed(1);
    
    console.log(`Compressed: ${compressedSize.toFixed(2)} MB (${savings}% smaller)`);

    return {
      uri: result.uri,
      width: result.width,
      height: result.height,
      originalSize,
      compressedSize,
      savingsPercent: parseFloat(savings),
    };
  } catch (error) {
    console.error('Image compression error:', error);
    return {
      uri,
      error: error.message,
    };
  }
};

export const compressForUpload = async (uri, maxSizeMB = 5) => {
  try {
    const originalSize = await getFileSizeInMB(uri);
    
    if (originalSize <= maxSizeMB) {
      console.log('Image already under size limit, applying light compression');
      return await compressImage(uri, 'HIGH_QUALITY');
    }

    const qualityLevels = ['BALANCED', 'FAST_UPLOAD'];
    
    for (const quality of qualityLevels) {
      const result = await compressImage(uri, quality);
      if (result.compressedSize <= maxSizeMB) {
        return result;
      }
    }

    return await compressImage(uri, 'FAST_UPLOAD');
  } catch (error) {
    console.error('Compress for upload error:', error);
    return { uri, error: error.message };
  }
};

export const createThumbnail = async (uri, size = 200) => {
  try {
    const result = await ImageManipulator.manipulateAsync(
      uri,
      [{ resize: { width: size, height: size } }],
      {
        compress: 0.6,
        format: ImageManipulator.SaveFormat.JPEG,
      }
    );

    return result;
  } catch (error) {
    console.error('Thumbnail creation error:', error);
    return null;
  }
};

export const resizeImage = async (uri, maxDimension = 1920) => {
  try {
    const result = await ImageManipulator.manipulateAsync(
      uri,
      [],
      {
        compress: 0.85,
        format: ImageManipulator.SaveFormat.JPEG,
      }
    );

    return result;
  } catch (error) {
    console.error('Image resize error:', error);
    return { uri };
  }
};

export default {
  compressImage,
  compressForUpload,
  createThumbnail,
  resizeImage,
  getFileSizeInMB,
  COMPRESSION_SETTINGS,
};
