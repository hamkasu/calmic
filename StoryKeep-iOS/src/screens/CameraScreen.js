/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  ScrollView,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImageManipulator from 'expo-image-manipulator';
import * as ImagePicker from 'expo-image-picker';
import { photoAPI } from '../services/api';
import ProgressBar from '../components/ProgressBar';

export default function CameraScreen({ navigation }) {
  const [batchMode, setBatchMode] = useState(false);
  const [capturedPhotos, setCapturedPhotos] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadMessage, setUploadMessage] = useState('');

  const launchNativeCamera = async () => {
    try {
      const permissionResult = await ImagePicker.requestCameraPermissionsAsync();
      
      if (!permissionResult.granted) {
        Alert.alert('Permission Required', 'Please allow camera access to take photos');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 1.0,
        exif: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setProcessing(true);

        const enhancedPhoto = await ImageManipulator.manipulateAsync(
          result.assets[0].uri,
          [{ resize: { width: 1920 } }],
          { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG }
        );

        if (batchMode) {
          setCapturedPhotos([...capturedPhotos, enhancedPhoto]);
          Alert.alert('Photo Captured', `${capturedPhotos.length + 1} photos in batch`);
          setProcessing(false);
        } else {
          await processAndUpload(enhancedPhoto.uri);
          setProcessing(false);
        }
      }
    } catch (error) {
      console.error('Camera error:', error);
      Alert.alert('Error', 'Failed to launch camera');
      setProcessing(false);
    }
  };

  const processAndUpload = async (photoUri, showAlerts = true) => {
    try {
      setUploadProgress(10);
      setUploadMessage('Preparing image...');
      
      const formData = new FormData();
      formData.append('image', {
        uri: photoUri,
        type: 'image/jpeg',
        name: `photo_${Date.now()}.jpg`,
      });

      setUploadProgress(30);
      setUploadMessage('Uploading photo...');

      const response = await photoAPI.detectAndExtract(formData);

      setUploadProgress(70);
      setUploadMessage('Detecting photos...');

      await new Promise(resolve => setTimeout(resolve, 500));

      setUploadProgress(100);
      setUploadMessage('Complete!');

      if (showAlerts) {
        if (response.success) {
          Alert.alert(
            'Success',
            `Photo uploaded! ${response.photos_extracted || 0} photo(s) extracted`,
            [
              {
                text: 'OK',
                onPress: () => navigation.navigate('Gallery'),
              },
            ]
          );
        } else {
          Alert.alert('Upload Complete', 'Photo uploaded but no extraction needed');
        }
      }
      
      return response;
    } catch (error) {
      if (showAlerts) {
        Alert.alert('Upload Failed', error.response?.data?.message || 'Please try again');
      }
      throw error;
    } finally {
      setUploadProgress(0);
      setUploadMessage('');
    }
  };

  const uploadBatch = async () => {
    if (capturedPhotos.length === 0) {
      Alert.alert('No Photos', 'Capture some photos first');
      return;
    }

    setProcessing(true);
    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < capturedPhotos.length; i++) {
      try {
        setUploadMessage(`Uploading ${i + 1} of ${capturedPhotos.length}...`);
        await processAndUpload(capturedPhotos[i].uri, false);
        successCount++;
      } catch (error) {
        failCount++;
      }
    }

    setProcessing(false);
    setCapturedPhotos([]);

    Alert.alert(
      'Batch Upload Complete',
      `Successfully uploaded: ${successCount}\nFailed: ${failCount}`,
      [
        {
          text: 'OK',
          onPress: () => navigation.navigate('Gallery'),
        },
      ]
    );
  };

  const removeBatchPhoto = (index) => {
    const newPhotos = capturedPhotos.filter((_, i) => i !== index);
    setCapturedPhotos(newPhotos);
  };

  const pickFromLibrary = async () => {
    try {
      const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
      
      if (!permissionResult.granted) {
        Alert.alert('Permission Required', 'Please allow access to your photo library');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsMultipleSelection: batchMode,
        quality: 1.0,
        allowsEditing: false,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setProcessing(true);

        if (batchMode) {
          const enhancedPhotos = [];
          for (const asset of result.assets) {
            const enhancedPhoto = await ImageManipulator.manipulateAsync(
              asset.uri,
              [{ resize: { width: 1920 } }],
              { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG }
            );
            enhancedPhotos.push(enhancedPhoto);
          }
          
          setCapturedPhotos([...capturedPhotos, ...enhancedPhotos]);
          Alert.alert(
            'Photos Added',
            `${enhancedPhotos.length} photo(s) added to batch. Total: ${capturedPhotos.length + enhancedPhotos.length}`
          );
        } else {
          const enhancedPhoto = await ImageManipulator.manipulateAsync(
            result.assets[0].uri,
            [{ resize: { width: 1920 } }],
            { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG }
          );
          await processAndUpload(enhancedPhoto.uri);
        }

        setProcessing(false);
      }
    } catch (error) {
      console.error('Photo library error:', error);
      Alert.alert('Error', 'Failed to pick photo from library');
      setProcessing(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={28} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Digitizer</Text>
        <TouchableOpacity
          onPress={() => setBatchMode(!batchMode)}
          style={styles.batchButton}
        >
          <Ionicons
            name={batchMode ? 'albums' : 'albums-outline'}
            size={28}
            color={batchMode ? '#4CAF50' : '#fff'}
          />
        </TouchableOpacity>
      </View>

      {/* Main Content */}
      <View style={styles.content}>
        {/* Info Card */}
        <View style={styles.infoCard}>
          <Ionicons name="camera" size={48} color="#E91E63" />
          <Text style={styles.infoTitle}>Native iOS Camera</Text>
          <Text style={styles.infoText}>
            Tap the camera button to open the native iOS camera app with all its features
          </Text>
          {batchMode && (
            <View style={styles.batchInfo}>
              <Ionicons name="albums" size={24} color="#4CAF50" />
              <Text style={styles.batchText}>Batch Mode Active</Text>
              <Text style={styles.batchSubtext}>
                Capture multiple photos before uploading
              </Text>
            </View>
          )}
        </View>

        {/* Batch Photos Preview */}
        {batchMode && capturedPhotos.length > 0 && (
          <View style={styles.batchPreviewContainer}>
            <Text style={styles.batchPreviewTitle}>
              {capturedPhotos.length} Photo{capturedPhotos.length !== 1 ? 's' : ''} Captured
            </Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {capturedPhotos.map((photo, index) => (
                <View key={index} style={styles.batchPhotoItem}>
                  <Image source={{ uri: photo.uri }} style={styles.batchPhotoImage} />
                  <TouchableOpacity
                    style={styles.removePhotoButton}
                    onPress={() => removeBatchPhoto(index)}
                  >
                    <Ionicons name="close-circle" size={24} color="#E91E63" />
                  </TouchableOpacity>
                </View>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Processing Indicator */}
        {processing && (
          <View style={styles.processingContainer}>
            <ActivityIndicator size="large" color="#E91E63" />
            <Text style={styles.processingText}>Processing...</Text>
          </View>
        )}

        {/* Upload Progress */}
        {uploadProgress > 0 && (
          <View style={styles.progressContainer}>
            <Text style={styles.progressText}>{uploadMessage}</Text>
            <ProgressBar progress={uploadProgress} />
          </View>
        )}
      </View>

      {/* Bottom Controls */}
      <View style={styles.controls}>
        {/* Library Button */}
        <TouchableOpacity
          style={styles.controlButton}
          onPress={pickFromLibrary}
          disabled={processing}
        >
          <Ionicons name="images" size={32} color="#fff" />
          <Text style={styles.controlButtonText}>Library</Text>
        </TouchableOpacity>

        {/* Camera Button */}
        <TouchableOpacity
          style={[styles.captureButton, processing && styles.captureButtonDisabled]}
          onPress={launchNativeCamera}
          disabled={processing}
        >
          <Ionicons name="camera" size={40} color="#fff" />
        </TouchableOpacity>

        {/* Upload Batch or Info */}
        {batchMode && capturedPhotos.length > 0 ? (
          <TouchableOpacity
            style={styles.controlButton}
            onPress={uploadBatch}
            disabled={processing}
          >
            <Ionicons name="cloud-upload" size={32} color="#4CAF50" />
            <Text style={styles.controlButtonText}>Upload ({capturedPhotos.length})</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.controlButton}>
            <Ionicons name="information-circle" size={32} color="#fff" />
            <Text style={styles.controlButtonText}>
              {batchMode ? 'Batch' : 'Single'}
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingHorizontal: 20,
    paddingBottom: 15,
    backgroundColor: '#2a2a2a',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  batchButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  infoCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 30,
    alignItems: 'center',
    width: '100%',
    maxWidth: 400,
  },
  infoTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 15,
    marginBottom: 10,
  },
  infoText: {
    fontSize: 16,
    color: '#bbb',
    textAlign: 'center',
    lineHeight: 22,
  },
  batchInfo: {
    marginTop: 20,
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    width: '100%',
  },
  batchText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#4CAF50',
    marginTop: 8,
  },
  batchSubtext: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  batchPreviewContainer: {
    marginTop: 20,
    width: '100%',
  },
  batchPreviewTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 10,
  },
  batchPhotoItem: {
    marginRight: 10,
    position: 'relative',
  },
  batchPhotoImage: {
    width: 100,
    height: 100,
    borderRadius: 8,
  },
  removePhotoButton: {
    position: 'absolute',
    top: -8,
    right: -8,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  processingContainer: {
    marginTop: 20,
    alignItems: 'center',
  },
  processingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#fff',
  },
  progressContainer: {
    marginTop: 20,
    width: '100%',
  },
  progressText: {
    fontSize: 14,
    color: '#fff',
    marginBottom: 8,
    textAlign: 'center',
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 30,
    paddingHorizontal: 20,
    backgroundColor: '#2a2a2a',
  },
  controlButton: {
    alignItems: 'center',
    padding: 10,
  },
  controlButtonText: {
    color: '#fff',
    fontSize: 12,
    marginTop: 5,
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#E91E63',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 8,
  },
  captureButtonDisabled: {
    opacity: 0.5,
  },
});
