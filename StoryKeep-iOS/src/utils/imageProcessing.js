import { manipulateAsync, SaveFormat } from 'expo-image-manipulator';
import * as FileSystem from 'expo-file-system/legacy';

/**
 * Prepare image for sharpening - preserves quality for upload
 * 
 * NOTE: True client-side sharpening (unsharp mask with convolution kernels) 
 * is not available in React Native/Expo without WebGL pixel shader access.
 * This function preserves image quality for server-side processing.
 * 
 * @param {string} imageUri - URI of the image
 * @param {number} intensity - Sharpening intensity (for reference only)
 * @param {number} radius - Blur radius (for reference only)
 * @returns {Promise<{uri: string, width: number, height: number}>} - Image ready for upload
 */
export async function sharpenImage(imageUri, intensity = 1.5, radius = 2.5) {
  try {
    console.log('📸 Preparing image for sharpening - Intensity:', intensity, 'Radius:', radius);
    console.log('ℹ️  Client-side sharpening is limited. Image will be uploaded for processing.');
    
    // Preserve original image quality for upload
    // The server will handle actual sharpening using PIL/OpenCV
    const result = await manipulateAsync(
      imageUri,
      [], // No modifications - preserve original
      {
        compress: 0.95, // High quality preservation
        format: SaveFormat.JPEG,
      }
    );
    
    console.log('✅ Image prepared for upload');
    return result;
    
  } catch (error) {
    console.error('❌ Image preparation error:', error);
    throw new Error('Failed to prepare image: ' + error.message);
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
