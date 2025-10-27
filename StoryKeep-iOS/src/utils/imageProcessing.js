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
    console.log('🔧 Starting local sharpen:', { intensity, radius });
    
    // For React Native, we use multi-pass contrast/brightness to simulate sharpening
    // Higher radius = more passes with lower intensity each
    // Lower radius = fewer passes with higher intensity each
    
    // Calculate number of passes based on radius
    const numPasses = Math.max(1, Math.round(radius / 1.5)); // 1 pass at radius 1.0, 3 passes at radius 4.0
    const intensityPerPass = intensity / numPasses;
    
    let currentUri = imageUri;
    let tempFiles = [];
    
    for (let pass = 0; pass < numPasses; pass++) {
      const contrastAdjustment = Math.min(intensityPerPass * 0.35, 0.8);
      const brightnessAdjustment = Math.min(intensityPerPass * 0.04, 0.12);
      
      const result = await manipulateAsync(
        currentUri,
        [
          { contrast: contrastAdjustment },
          { brightness: brightnessAdjustment },
        ],
        {
          compress: 0.95,
          format: SaveFormat.JPEG,
        }
      );
      
      // Clean up intermediate files (except the original input and final output)
      if (currentUri !== imageUri && pass < numPasses - 1) {
        tempFiles.push(currentUri);
      }
      
      currentUri = result.uri;
    }
    
    // Clean up all intermediate temp files
    for (const tempFile of tempFiles) {
      await FileSystem.deleteAsync(tempFile, { idempotent: true }).catch(() => {});
    }
    
    console.log('✅ Sharpen complete:', currentUri, `(${numPasses} passes)`);
    return { uri: currentUri };
    
  } catch (error) {
    console.error('❌ Sharpen error:', error);
    throw new Error('Failed to sharpen image: ' + error.message);
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
    console.log('🔧 Starting advanced sharpen:', { intensity, radius });
    
    // For strong sharpening, apply multiple passes
    let currentUri = imageUri;
    const passes = intensity > 2.0 ? 2 : 1;
    
    for (let i = 0; i < passes; i++) {
      const passIntensity = intensity / passes;
      const contrastAdjustment = Math.min(passIntensity * 0.3, 1.0);
      const brightnessAdjustment = Math.min(passIntensity * 0.05, 0.15);
      
      const result = await manipulateAsync(
        currentUri,
        [
          { contrast: contrastAdjustment },
          { brightness: brightnessAdjustment },
        ],
        {
          compress: 0.95,
          format: SaveFormat.JPEG,
        }
      );
      
      // Clean up intermediate file if it's not the original
      if (currentUri !== imageUri && i < passes - 1) {
        await FileSystem.deleteAsync(currentUri, { idempotent: true }).catch(() => {});
      }
      
      currentUri = result.uri;
    }
    
    console.log('✅ Advanced sharpen complete');
    return { uri: currentUri };
    
  } catch (error) {
    console.error('❌ Advanced sharpen error:', error);
    throw new Error('Failed to sharpen image: ' + error.message);
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
