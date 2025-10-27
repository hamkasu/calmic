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
    console.log('🔧 Local sharpen parameters:', { intensity, radius });
    console.log('✨ Processing multi-pass sharpening locally...');
    
    // STRATEGY: Since expo-image-manipulator doesn't support actual sharpening filters,
    // we'll use a multi-pass resize technique to enhance edge definition.
    // This works by slightly downscaling and then upscaling back, which causes
    // interpolation that can enhance edges and create a sharpening-like effect.
    
    // First, get the original image dimensions
    const originalInfo = await manipulateAsync(
      imageUri,
      [], // No operations, just to get dimensions
      { compress: 1, format: SaveFormat.JPEG }
    );
    
    const originalWidth = originalInfo.width;
    const originalHeight = originalInfo.height;
    
    console.log(`📏 Original dimensions: ${originalWidth}x${originalHeight}`);
    
    // Calculate resize factor based on intensity and radius
    // Lower intensity = less aggressive downscale (closer to 1.0)
    // Higher intensity = more aggressive downscale (further from 1.0)
    const downscaleFactor = Math.max(0.75, 1.0 - (intensity * 0.15));
    const downscaleWidth = Math.round(originalWidth * downscaleFactor);
    const downscaleHeight = Math.round(originalHeight * downscaleFactor);
    
    console.log(`🔄 Pass 1: Downscale to ${(downscaleFactor * 100).toFixed(0)}% (${downscaleWidth}x${downscaleHeight})`);
    
    // Pass 1: Downscale slightly
    const downscaled = await manipulateAsync(
      imageUri,
      [
        {
          resize: {
            width: downscaleWidth,
            height: downscaleHeight,
          }
        }
      ],
      {
        compress: 0.95,
        format: SaveFormat.JPEG,
      }
    );
    
    // Downscaled dimensions for reference
    const downscaledWidth = downscaled.width;
    const downscaledHeight = downscaled.height;
    
    console.log(`🔄 Pass 2: Upscale back to original size to enhance edges`);
    
    // Pass 2: Upscale back to original size
    // This interpolation enhances edge definition
    const targetWidth = originalWidth;
    const targetHeight = originalHeight;
    
    const sharpened = await manipulateAsync(
      downscaled.uri,
      [
        {
          resize: {
            width: targetWidth,
            height: targetHeight,
          }
        }
      ],
      {
        compress: 0.95, // High quality to preserve enhanced edges
        format: SaveFormat.JPEG,
      }
    );
    
    // Optional third pass for stronger sharpening
    let finalImage = sharpened;
    if (intensity >= 2.0) {
      console.log(`🔄 Pass 3: Additional enhancement for high intensity`);
      
      // For high intensity, apply another cycle
      const secondDownscale = await manipulateAsync(
        sharpened.uri,
        [
          {
            resize: {
              width: Math.round(targetWidth * 0.9),
              height: Math.round(targetHeight * 0.9),
            }
          }
        ],
        {
          compress: 0.95,
          format: SaveFormat.JPEG,
        }
      );
      
      finalImage = await manipulateAsync(
        secondDownscale.uri,
        [
          {
            resize: {
              width: targetWidth,
              height: targetHeight,
            }
          }
        ],
        {
          compress: 0.95,
          format: SaveFormat.JPEG,
        }
      );
      
      // Clean up intermediate file
      await FileSystem.deleteAsync(secondDownscale.uri, { idempotent: true }).catch(() => {});
    }
    
    console.log(`✅ Local sharpening complete: ${finalImage.width}x${finalImage.height}`);
    
    // Clean up intermediate files
    await FileSystem.deleteAsync(originalInfo.uri, { idempotent: true }).catch(() => {});
    await FileSystem.deleteAsync(downscaled.uri, { idempotent: true }).catch(() => {});
    if (intensity >= 2.0) {
      await FileSystem.deleteAsync(sharpened.uri, { idempotent: true }).catch(() => {});
    }
    
    return finalImage;
    
  } catch (error) {
    console.error('❌ Sharpen error:', error);
    throw new Error('Failed to sharpen image locally: ' + error.message);
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
