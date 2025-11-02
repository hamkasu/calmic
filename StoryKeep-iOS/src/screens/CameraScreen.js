/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React, { useState, useEffect } from 'react';
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
import AsyncStorage from '@react-native-async-storage/async-storage';
import { photoAPI } from '../services/api';
import ProgressBar from '../components/ProgressBar';
import NetworkService from '../services/NetworkService';
import QueueService from '../services/QueueService';

const AUTO_ENHANCE_KEY = '@auto_enhance';
const OFFLINE_MODE_KEY = '@offline_mode';
const PHOTO_QUALITY_KEY = '@photo_quality';

export default function CameraScreen({ navigation }) {
  const [batchMode, setBatchMode] = useState(false);
  const [capturedPhotos, setCapturedPhotos] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadMessage, setUploadMessage] = useState('');
  const [autoEnhance, setAutoEnhance] = useState(false);
  const [offlineMode, setOfflineMode] = useState(false);
  const [photoQuality, setPhotoQuality] = useState('high');
  const [isOnline, setIsOnline] = useState(true);
  const [queueCount, setQueueCount] = useState(0);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState('success');

  useEffect(() => {
    loadSettings();
    NetworkService.initialize();
    QueueService.initialize();

    const unsubscribeNetwork = NetworkService.addListener((connected) => {
      setIsOnline(connected);
      if (connected && !offlineMode) {
        processQueuedPhotos();
      }
    });

    const unsubscribeQueue = QueueService.addListener((count) => {
      setQueueCount(count);
    });

    setIsOnline(NetworkService.getConnectionStatus());
    setQueueCount(QueueService.getQueueCount());

    return () => {
      unsubscribeNetwork();
      unsubscribeQueue();
      NetworkService.cleanup();
    };
  }, [offlineMode]);

  const loadSettings = async () => {
    try {
      const autoEnhanceValue = await AsyncStorage.getItem(AUTO_ENHANCE_KEY);
      const offlineModeValue = await AsyncStorage.getItem(OFFLINE_MODE_KEY);
      const photoQualityValue = await AsyncStorage.getItem(PHOTO_QUALITY_KEY);

      if (autoEnhanceValue !== null) {
        setAutoEnhance(autoEnhanceValue === 'true');
      }

      if (offlineModeValue !== null) {
        setOfflineMode(offlineModeValue === 'true');
      }

      if (photoQualityValue !== null) {
        setPhotoQuality(photoQualityValue);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const showToastMessage = (message, type = 'success') => {
    setToastMessage(message);
    setToastType(type);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const getQualitySettings = () => {
    switch (photoQuality) {
      case 'low':
        return { width: 1280, compress: 0.6 };
      case 'medium':
        return { width: 1920, compress: 0.8 };
      case 'high':
      default:
        return { width: undefined, compress: 0.95 }; // Original size
    }
  };

  const processQueuedPhotos = async () => {
    try {
      const result = await QueueService.processQueue();
      if (result.processed > 0) {
        Alert.alert(
          'Queue Synced',
          `Successfully uploaded ${result.processed} photo(s)${result.failed > 0 ? `, ${result.failed} failed` : ''}`
        );
      }
    } catch (error) {
      console.error('Error processing queue:', error);
    }
  };

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

        const qualitySettings = getQualitySettings();
        const manipulations = qualitySettings.width 
          ? [{ resize: { width: qualitySettings.width } }]
          : [];

        const enhancedPhoto = await ImageManipulator.manipulateAsync(
          result.assets[0].uri,
          manipulations,
          { compress: qualitySettings.compress, format: ImageManipulator.SaveFormat.JPEG }
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
    const shouldQueue = offlineMode || !isOnline;

    if (shouldQueue) {
      try {
        setUploadMessage('Adding to queue...');
        await QueueService.addToQueue(photoUri);
        
        if (showAlerts) {
          Alert.alert(
            'Queued',
            `Photo added to queue. ${QueueService.getQueueCount()} photo(s) pending upload.`,
            [
              {
                text: 'OK',
              },
            ]
          );
        }
        
        return { success: true, queued: true };
      } catch (error) {
        if (showAlerts) {
          Alert.alert('Queue Failed', 'Could not add photo to queue');
        }
        throw error;
      } finally {
        setUploadMessage('');
      }
    }

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

      if (autoEnhance && response.photo_id) {
        setUploadProgress(80);
        setUploadMessage('Auto-enhancing...');
        
        try {
          await photoAPI.enhancePhoto(response.photo_id, {
            intensity: 1.5,
            radius: 1.0,
            threshold: 0,
          });
          
          setUploadProgress(90);
          await new Promise(resolve => setTimeout(resolve, 300));
          showToastMessage('✨ Photo enhanced successfully!', 'success');
        } catch (enhanceError) {
          console.error('Auto-enhance failed:', enhanceError);
          showToastMessage('⚠️ Auto-enhance failed', 'error');
        }
      }

      setUploadProgress(100);
      setUploadMessage('Complete!');

      if (showAlerts) {
        if (response.success) {
          const message = autoEnhance 
            ? `Photo uploaded and enhanced! ${response.photos_extracted || 0} photo(s) extracted`
            : `Photo uploaded! ${response.photos_extracted || 0} photo(s) extracted`;
          
          Alert.alert(
            'Success',
            message,
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

        const qualitySettings = getQualitySettings();
        const manipulations = qualitySettings.width 
          ? [{ resize: { width: qualitySettings.width } }]
          : [];

        if (batchMode) {
          const enhancedPhotos = [];
          for (const asset of result.assets) {
            const enhancedPhoto = await ImageManipulator.manipulateAsync(
              asset.uri,
              manipulations,
              { compress: qualitySettings.compress, format: ImageManipulator.SaveFormat.JPEG }
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
            manipulations,
            { compress: qualitySettings.compress, format: ImageManipulator.SaveFormat.JPEG }
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
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>Digitizer</Text>
          <View style={styles.statusRow}>
            {!isOnline && (
              <View style={styles.statusBadge}>
                <Ionicons name="cloud-offline" size={12} color="#FF9800" />
                <Text style={styles.statusText}>Offline</Text>
              </View>
            )}
            {offlineMode && (
              <View style={styles.statusBadge}>
                <Ionicons name="albums" size={12} color="#4CAF50" />
                <Text style={styles.statusText}>Queue Mode</Text>
              </View>
            )}
            {queueCount > 0 && (
              <View style={styles.statusBadge}>
                <Ionicons name="hourglass" size={12} color="#2196F3" />
                <Text style={styles.statusText}>{queueCount} pending</Text>
              </View>
            )}
            {autoEnhance && (
              <View style={styles.statusBadge}>
                <Ionicons name="sparkles" size={12} color="#9C27B0" />
                <Text style={styles.statusText}>Auto-Enhance</Text>
              </View>
            )}
          </View>
        </View>
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

      {/* Toast Notification */}
      {showToast && (
        <View style={[
          styles.toast,
          toastType === 'error' && styles.toastError,
        ]}>
          <Text style={styles.toastText}>{toastMessage}</Text>
        </View>
      )}
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
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  statusRow: {
    flexDirection: 'row',
    marginTop: 4,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    marginHorizontal: 2,
    marginVertical: 2,
  },
  statusText: {
    color: '#fff',
    fontSize: 10,
    marginLeft: 4,
    fontWeight: '500',
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
  toast: {
    position: 'absolute',
    top: 100,
    left: 20,
    right: 20,
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 6,
    zIndex: 1000,
  },
  toastError: {
    backgroundColor: '#F44336',
  },
  toastText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
});
