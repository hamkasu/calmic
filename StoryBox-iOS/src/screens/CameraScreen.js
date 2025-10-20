import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import * as ImageManipulator from 'expo-image-manipulator';
import * as ImagePicker from 'expo-image-picker';
import { photoAPI } from '../services/api';

const { width, height } = Dimensions.get('window');

// Flash mode constants for expo-camera v17+
const FLASH_MODE = {
  off: 'off',
  on: 'on',
  auto: 'auto',
};

// Camera type constants for expo-camera v17+
const CAMERA_TYPE = {
  back: 'back',
  front: 'front',
};

export default function CameraScreen({ navigation }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [flashMode, setFlashMode] = useState(FLASH_MODE.off);
  const [batchMode, setBatchMode] = useState(false);
  const [capturedPhotos, setCapturedPhotos] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [showGuides, setShowGuides] = useState(true);
  const [zoom, setZoom] = useState(0);
  const [detectedBoundaries, setDetectedBoundaries] = useState([]);
  const [showingPreview, setShowingPreview] = useState(false);
  const [cameraKey, setCameraKey] = useState(0);
  const cameraRef = useRef(null);
  const baseZoom = useRef(0);

  // Force camera remount when screen is focused to prevent black screen
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      setCameraKey(prevKey => prevKey + 1);
    });
    return unsubscribe;
  }, [navigation]);

  // Pinch to zoom gesture
  const pinchGesture = Gesture.Pinch()
    .onUpdate((event) => {
      const newZoom = Math.min(Math.max(baseZoom.current + (event.scale - 1) * 0.5, 0), 1);
      setZoom(newZoom);
    })
    .onEnd(() => {
      baseZoom.current = zoom;
    });

  const previewDetection = async () => {
    if (cameraRef.current) {
      try {
        setShowingPreview(true);
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.5,
          base64: false,
        });

        const formData = new FormData();
        formData.append('image', {
          uri: photo.uri,
          type: 'image/jpeg',
          name: 'preview.jpg',
        });

        const response = await photoAPI.previewDetection(formData);
        
        if (response.success && response.detections && response.detections.length > 0) {
          setDetectedBoundaries(response.detections);
          Alert.alert(
            'Detection Preview',
            `Found ${response.detected_count} photo(s)!`,
            [{ text: 'OK' }]
          );
        } else {
          setDetectedBoundaries([]);
          Alert.alert('No Photos Detected', 'Try adjusting your camera angle or lighting');
        }
      } catch (error) {
        console.error('Preview detection error:', error);
        Alert.alert('Preview Failed', 'Could not analyze frame');
      } finally {
        setShowingPreview(false);
      }
    }
  };

  const toggleFlash = () => {
    setFlashMode((current) =>
      current === FLASH_MODE.off
        ? FLASH_MODE.on
        : current === FLASH_MODE.on
        ? FLASH_MODE.auto
        : FLASH_MODE.off
    );
  };

  const getFlashIcon = () => {
    if (flashMode === FLASH_MODE.off) return 'flash-off';
    if (flashMode === FLASH_MODE.on) return 'flash';
    return 'flash-outline';
  };

  const capturePhoto = async () => {
    if (cameraRef.current) {
      try {
        setProcessing(true);
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.8,
          base64: false,
          exif: true,
        });

        // Auto-enhance the captured photo
        const enhancedPhoto = await ImageManipulator.manipulateAsync(
          photo.uri,
          [
            { resize: { width: 1920 } },
          ],
          {
            compress: 0.8,
            format: ImageManipulator.SaveFormat.JPEG,
          }
        );

        if (batchMode) {
          setCapturedPhotos([...capturedPhotos, enhancedPhoto]);
          Alert.alert('Photo Captured', `${capturedPhotos.length + 1} photos in batch`);
        } else {
          await processAndUpload(enhancedPhoto.uri);
        }
      } catch (error) {
        Alert.alert('Error', 'Failed to capture photo');
        console.error(error);
      } finally {
        setProcessing(false);
      }
    }
  };

  const processAndUpload = async (photoUri, showAlerts = true) => {
    try {
      const formData = new FormData();
      formData.append('image', {
        uri: photoUri,
        type: 'image/jpeg',
        name: `photo_${Date.now()}.jpg`,
      });

      const response = await photoAPI.detectAndExtract(formData);

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
    }
  };

  const finishBatch = async () => {
    if (capturedPhotos.length === 0) {
      Alert.alert('No Photos', 'Please capture some photos first');
      return;
    }

    setProcessing(true);
    let successCount = 0;
    
    try {
      for (const photo of capturedPhotos) {
        await processAndUpload(photo.uri, false);
        successCount++;
      }

      Alert.alert(
        'Batch Complete',
        `Successfully uploaded ${successCount} of ${capturedPhotos.length} photos`,
        [
          {
            text: 'OK',
            onPress: () => {
              setCapturedPhotos([]);
              setBatchMode(false);
              navigation.navigate('Gallery');
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert(
        'Batch Upload Error',
        `Uploaded ${successCount} of ${capturedPhotos.length} photos. Some uploads failed.`,
        [
          {
            text: 'OK',
            onPress: () => {
              setCapturedPhotos([]);
              setBatchMode(false);
              if (successCount > 0) {
                navigation.navigate('Gallery');
              }
            },
          },
        ]
      );
    } finally {
      setProcessing(false);
    }
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
        quality: 0.8,
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

  if (!permission) {
    return <View style={styles.container} />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.permissionText}>No access to camera</Text>
        <TouchableOpacity
          style={styles.button}
          onPress={requestPermission}
        >
          <Text style={styles.buttonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <GestureDetector gesture={pinchGesture}>
        <CameraView
          key={cameraKey}
          ref={cameraRef}
          style={styles.camera}
          facing={CAMERA_TYPE.back}
          flash={flashMode}
          zoom={zoom}
        />
      </GestureDetector>

      {/* All UI elements overlaid with absolute positioning */}
      {showGuides && detectedBoundaries.length === 0 && (
        <View style={styles.guides}>
          <View style={styles.guideFrame} />
          <Text style={styles.guideText}>
            Align photos within the frame - Multiple photos supported
          </Text>
        </View>
      )}

      {/* Red outlines for detected photos */}
      {detectedBoundaries.length > 0 && (
        <View style={styles.detectionOverlay}>
          {detectedBoundaries.map((detection, index) => (
            <View
              key={index}
              style={[
                styles.detectedBoundary,
                {
                  left: detection.x,
                  top: detection.y,
                  width: detection.width,
                  height: detection.height,
                },
              ]}
            >
              <View style={styles.detectedBoundaryInner} />
              <Text style={styles.detectionLabel}>
                Photo {index + 1} ({Math.round(detection.confidence * 100)}%)
              </Text>
            </View>
          ))}
          <Text style={styles.detectionCount}>
            {detectedBoundaries.length} photo{detectedBoundaries.length !== 1 ? 's' : ''} detected
          </Text>
        </View>
      )}

      <View style={styles.header}>
        <TouchableOpacity
          style={styles.iconButton}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="close" size={32} color="#fff" />
        </TouchableOpacity>

        <View style={styles.headerRight}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={previewDetection}
            disabled={processing || showingPreview}
          >
            <Ionicons
              name={detectedBoundaries.length > 0 ? 'scan-circle' : 'scan-circle-outline'}
              size={28}
              color={showingPreview ? '#FFA500' : detectedBoundaries.length > 0 ? '#4CAF50' : '#fff'}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.iconButton}
            onPress={pickFromLibrary}
            disabled={processing}
          >
            <Ionicons
              name="images"
              size={28}
              color={processing ? '#999' : '#fff'}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => {
              setShowGuides(!showGuides);
              if (showGuides) setDetectedBoundaries([]);
            }}
          >
            <Ionicons
              name={showGuides ? 'grid' : 'grid-outline'}
              size={28}
              color="#fff"
            />
          </TouchableOpacity>

          <TouchableOpacity style={styles.iconButton} onPress={toggleFlash}>
            <Ionicons name={getFlashIcon()} size={28} color="#fff" />
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.controls}>
        <TouchableOpacity
          style={[
            styles.batchButton,
            batchMode && styles.batchButtonActive,
          ]}
          onPress={() => setBatchMode(!batchMode)}
        >
          <Ionicons
            name="albums"
            size={24}
            color={batchMode ? '#E85D75' : '#fff'}
          />
          <Text
            style={[
              styles.batchText,
              batchMode && styles.batchTextActive,
            ]}
          >
            {batchMode ? `Batch (${capturedPhotos.length})` : 'Single'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.captureButton,
            processing && styles.captureButtonDisabled,
          ]}
          onPress={capturePhoto}
          disabled={processing}
        >
          {processing ? (
            <ActivityIndicator color="#fff" size="large" />
          ) : (
            <View style={styles.captureButtonInner} />
          )}
        </TouchableOpacity>

        {batchMode && capturedPhotos.length > 0 ? (
          <TouchableOpacity
            style={styles.finishButton}
            onPress={finishBatch}
          >
            <Ionicons name="checkmark-circle" size={32} color="#4CAF50" />
          </TouchableOpacity>
        ) : (
          <View style={styles.placeholder} />
        )}
      </View>

      {/* Zoom Indicator */}
      {zoom > 0 && (
        <View style={styles.zoomIndicator}>
          <Text style={styles.zoomText}>{(1 + zoom * 9).toFixed(1)}x</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  permissionText: {
    color: '#fff',
    fontSize: 18,
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#E85D75',
    padding: 15,
    borderRadius: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  guides: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    pointerEvents: 'none',
  },
  guideFrame: {
    width: width * 0.95,
    height: height * 0.7,
    borderWidth: 3,
    borderColor: '#E85D75',
    borderRadius: 10,
    borderStyle: 'dashed',
  },
  guideText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
    padding: 10,
    borderRadius: 5,
    fontWeight: '600',
  },
  header: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
  },
  headerRight: {
    flexDirection: 'row',
  },
  iconButton: {
    padding: 10,
    marginLeft: 10,
  },
  controls: {
    position: 'absolute',
    bottom: 40,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  batchButton: {
    backgroundColor: 'rgba(255,255,255,0.3)',
    padding: 12,
    borderRadius: 10,
    alignItems: 'center',
    minWidth: 80,
  },
  batchButtonActive: {
    backgroundColor: '#fff',
  },
  batchText: {
    color: '#fff',
    fontSize: 12,
    marginTop: 4,
  },
  batchTextActive: {
    color: '#E85D75',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#fff',
  },
  captureButtonDisabled: {
    opacity: 0.5,
  },
  captureButtonInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#fff',
  },
  finishButton: {
    padding: 10,
  },
  placeholder: {
    width: 52,
  },
  zoomIndicator: {
    position: 'absolute',
    top: 120,
    alignSelf: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  zoomText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  detectionOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    pointerEvents: 'none',
  },
  detectedBoundary: {
    position: 'absolute',
    borderWidth: 3,
    borderColor: '#E85D75',
    borderRadius: 8,
    backgroundColor: 'rgba(232, 93, 117, 0.1)',
  },
  detectedBoundaryInner: {
    flex: 1,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    borderRadius: 6,
    margin: 2,
  },
  detectionLabel: {
    position: 'absolute',
    top: -25,
    left: 0,
    backgroundColor: '#E85D75',
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  detectionCount: {
    position: 'absolute',
    bottom: 150,
    alignSelf: 'center',
    backgroundColor: 'rgba(76, 175, 80, 0.9)',
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
});
