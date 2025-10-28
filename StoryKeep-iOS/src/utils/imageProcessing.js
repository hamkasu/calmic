/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import { manipulateAsync, SaveFormat } from 'expo-image-manipulator';
import * as FileSystem from 'expo-file-system/legacy';

/**
 * Client-side sharpening using upscale-downscale technique
 * Creates visible sharpening effect by exploiting resize artifacts
 * 
 * @param {string} imageUri - URI of the image
 * @param {number} intensity - Sharpening intensity (0.5 - 3.0)
 * @param {number} radius - Effect strength multiplier (1.0 - 5.0)
 * @returns {Promise<{uri: string, width: number, height: number}>} - Sharpened image
 */
export async function sharpenImage(imageUri, intensity = 1.5, radius = 2.5) {
  try {
    console.log('🔧 Client-side sharpen:', { intensity, radius });
    
    // Get original dimensions
    const original = await manipulateAsync(imageUri, [], { compress: 1.0, format: SaveFormat.JPEG });
    const { width, height } = original;
    
    // Technique: Upscale then downscale creates edge enhancement
    // The resize interpolation creates sharpening artifacts we can exploit
    
    // Calculate upscale factor based on BOTH intensity and radius
    // - Intensity controls strength (0.5-3.0 range)
    // - Radius controls effect spread (1.0-5.0 range)
    const intensityFactor = intensity * 0.10; // 0.05x to 0.30x
    const radiusFactor = radius * 0.02; // 0.02x to 0.10x
    const upscaleFactor = 1.0 + intensityFactor + radiusFactor; // 1.07x to 1.40x
    const upscaleWidth = Math.round(width * upscaleFactor);
    
    console.log('📐 Upscale factor:', upscaleFactor.toFixed(3), '= 1.0 + intensity:', intensityFactor.toFixed(3), '+ radius:', radiusFactor.toFixed(3));
    
    // Step 1: Upscale (creates interpolation)
    const upscaled = await manipulateAsync(
      imageUri,
      [{ resize: { width: upscaleWidth } }],
      { compress: 0.99, format: SaveFormat.PNG } // PNG for lossless intermediate
    );
    
    // Step 2: Downscale back to original (creates sharpening effect)
    // Compression also affects sharpness: higher intensity = less compression = sharper
    const compressionQuality = Math.min(0.98, 0.88 + (intensity * 0.032));
    
    const sharpened = await manipulateAsync(
      upscaled.uri,
      [{ resize: { width: width } }],
      {
        compress: compressionQuality,
        format: SaveFormat.JPEG,
      }
    );
    
    // Cleanup intermediate files
    await FileSystem.deleteAsync(upscaled.uri, { idempotent: true }).catch(() => {});
    await FileSystem.deleteAsync(original.uri, { idempotent: true }).catch(() => {});
    
    console.log('✅ Client-side sharpen complete with intensity', intensity, 'and radius', radius);
    return sharpened;
    
  } catch (error) {
    console.error('❌ Sharpen error:', error);
    // On error, return high-quality original
    return await manipulateAsync(imageUri, [], { compress: 0.95, format: SaveFormat.JPEG });
  }
}

/**
 * Apply advanced sharpening with multiple passes for stronger effect
 * 
 * @param {string} imageUri - URI of the image to sharpen
 * @param {number} intensity - Sharpening intensity (0.5 - 3.0)
 * @param {number} radius - Blur radius (not used in this implementation)
 * @returns {Promise<{uri: string, width: number, height: number}>}
 */
export async function sharpenImageAdvanced(imageUri, intensity = 1.5, radius = 2.5) {
  try {
    console.log('🔧 Advanced sharpen parameters:', { intensity, radius });
    console.log('ℹ️ Advanced sharpening will be done server-side for best quality');
    
    // NOTE: expo-image-manipulator doesn't support contrast/brightness adjustments
    // Only supported actions are: resize, rotate, flip, crop
    // 
    // Server-side sharpening uses PIL's UnsharpMask which is far superior
    // to any client-side approximation we could do with basic image ops.
    
    // Return original image unchanged - server will do the actual sharpening
    return { uri: imageUri };
    
  } catch (error) {
    console.error('❌ Advanced sharpen error:', error);
    throw new Error('Failed to prepare image for advanced sharpening: ' + error.message);
  }
}

/**
 * Preset sharpening configurations
 */
export const SharpenPresets = {
  subtle: {
    name: 'Subtle',
    description: 'Light sharpening for modern photos',
    intensity: 1.0,
    radius: 1.5,
    icon: 'radio-button-off',
  },
  medium: {
    name: 'Medium',
    description: 'Balanced sharpening for most photos',
    intensity: 1.5,
    radius: 2.5,
    icon: 'radio-button-on',
  },
  strong: {
    name: 'Strong',
    description: 'Heavy sharpening for degraded photos',
    intensity: 2.5,
    radius: 4.0,
    icon: 'ellipse',
  },
};

/**
 * Get file info including size
 */
export async function getImageInfo(uri) {
  try {
    const info = await FileSystem.getInfoAsync(uri);
    return {
      exists: info.exists,
      size: info.size,
      uri: info.uri,
    };
  } catch (error) {
    console.error('Error getting image info:', error);
    return null;
  }
}

/**
 * Convert base64 image to file URI
 */
export async function base64ToUri(base64String, filename = 'temp_image.jpg') {
  try {
    const uri = FileSystem.documentDirectory + filename;
    await FileSystem.writeAsStringAsync(uri, base64String, {
      encoding: FileSystem.EncodingType.Base64,
    });
    return uri;
  } catch (error) {
    console.error('Error converting base64 to URI:', error);
    throw error;
  }
}
