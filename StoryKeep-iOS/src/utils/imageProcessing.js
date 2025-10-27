import { manipulateAsync, SaveFormat } from 'expo-image-manipulator';
import * as FileSystem from 'expo-file-system/legacy';

/**
 * Apply unsharp mask sharpening to an image locally on device
 * This uses a combination of blur and overlay to simulate sharpening
 * 
 * @param {string} imageUri - URI of the image to sharpen
 * @param {number} intensity - Sharpening intensity (0.5 - 3.0, default 1.5)
 * @param {number} radius - Blur radius for unsharp mask (1.0 - 5.0, default 2.5)
 * @returns {Promise<{uri: string, width: number, height: number}>} - Sharpened image details
 */
export async function sharpenImage(imageUri, intensity = 1.5, radius = 2.5) {
  try {
    console.log('🔧 Sharpen parameters:', { intensity, radius });
    console.log('ℹ️ Sharpening will be done server-side for best quality');
    
    // NOTE: expo-image-manipulator doesn't support contrast/brightness adjustments
    // These actions are not available: { contrast: value }, { brightness: value }
    // Only supported actions are: resize, rotate, flip, crop
    // 
    // Therefore, we skip local preview sharpening and let the server handle it.
    // The server uses PIL's UnsharpMask filter which provides professional-quality sharpening.
    
    // Return original image unchanged - server will do the actual sharpening
    return { uri: imageUri };
    
  } catch (error) {
    console.error('❌ Sharpen error:', error);
    throw new Error('Failed to prepare image for sharpening: ' + error.message);
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
