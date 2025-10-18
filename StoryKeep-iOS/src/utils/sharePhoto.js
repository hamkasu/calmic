import { Alert } from 'react-native';
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system/legacy';

const BASE_URL = 'https://web-production-535bd.up.railway.app';

export const sharePhoto = async (photo, authToken, preferEnhanced = false) => {
  try {
    if (!authToken) {
      Alert.alert('Error', 'Please wait for authentication to complete');
      return false;
    }

    const hasEnhanced = !!photo.edited_url;
    
    let selectedVersion = 'original';
    
    if (hasEnhanced && !preferEnhanced) {
      selectedVersion = await new Promise((resolve) => {
        Alert.alert(
          'Share Photo',
          'Which version would you like to share?',
          [
            {
              text: 'Original',
              onPress: () => resolve('original'),
            },
            {
              text: 'Enhanced',
              onPress: () => resolve('enhanced'),
            },
            {
              text: 'Cancel',
              style: 'cancel',
              onPress: () => resolve(null),
            },
          ],
          { cancelable: true, onDismiss: () => resolve(null) }
        );
      });
    } else if (hasEnhanced && preferEnhanced) {
      selectedVersion = 'enhanced';
    }

    if (!selectedVersion) {
      return;
    }

    const isAvailable = await Sharing.isAvailableAsync();
    if (!isAvailable) {
      Alert.alert('Error', 'Sharing is not available on this device');
      return;
    }

    const relativePath = selectedVersion === 'enhanced' ? photo.edited_url : (photo.url || photo.original_url);
    const imageUrl = relativePath?.startsWith('http') ? relativePath : `${BASE_URL}${relativePath}`;
    const fileUri = FileSystem.documentDirectory + `share_photo_${photo.id}_${Date.now()}.jpg`;

    console.log('📤 Sharing photo from:', imageUrl);

    const { uri } = await FileSystem.downloadAsync(
      imageUrl,
      fileUri,
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      }
    );

    console.log('✅ Downloaded for sharing:', uri);

    await Sharing.shareAsync(uri, {
      mimeType: 'image/jpeg',
      dialogTitle: 'Share Photo',
    });

    console.log('✅ Share completed');

    setTimeout(async () => {
      try {
        await FileSystem.deleteAsync(uri, { idempotent: true });
        console.log('🗑️ Cleaned up temporary file');
      } catch (error) {
        console.warn('⚠️ Could not delete temp file:', error);
      }
    }, 5000);

    return true;
  } catch (error) {
    console.error('❌ Share error:', error);
    Alert.alert('Error', 'Failed to share photo: ' + error.message);
    return false;
  }
};
