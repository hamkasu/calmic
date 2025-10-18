import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Dimensions,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Slider from '@react-native-community/slider';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { photoAPI } from '../services/api';

const { width } = Dimensions.get('window');
const BASE_URL = 'https://web-production-535bd.up.railway.app';

export default function EnhancePhotoScreen({ route, navigation }) {
  const { photo } = route.params;
  const [processing, setProcessing] = useState(false);
  const [showOriginal, setShowOriginal] = useState(true);
  const [authToken, setAuthToken] = useState(null);
  const [isBlackAndWhite, setIsBlackAndWhite] = useState(null);
  const [detectingColor, setDetectingColor] = useState(true);
  
  // Sharpen controls modal state
  const [showSharpenControls, setShowSharpenControls] = useState(false);
  const [sharpenIntensity, setSharpenIntensity] = useState(1.5);
  const [sharpenRadius, setSharpenRadius] = useState(2.0);
  const [sharpenThreshold, setSharpenThreshold] = useState(3);

  useEffect(() => {
    loadAuthToken();
    detectImageColor();
  }, []);

  const loadAuthToken = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      setAuthToken(token);
    } catch (error) {
      console.error('Failed to load auth token:', error);
    }
  };

  const detectImageColor = async () => {
    try {
      setDetectingColor(true);
      
      // Call the backend API to check if photo is grayscale
      const response = await photoAPI.checkGrayscale(photo.id);
      
      if (response.success) {
        setIsBlackAndWhite(response.is_grayscale);
        console.log(`Photo ${photo.id} grayscale check: ${response.is_grayscale}`);
      } else {
        // On error, enable colorization (conservative approach)
        console.warn('Grayscale check failed, enabling colorization by default');
        setIsBlackAndWhite(true);
      }
      
    } catch (error) {
      console.error('Error detecting image color:', error);
      // On error, enable colorization (conservative approach)
      setIsBlackAndWhite(true);
    } finally {
      setDetectingColor(false);
    }
  };

  const handleSharpenWithControls = () => {
    setShowSharpenControls(true);
  };

  const applySharpen = async () => {
    setShowSharpenControls(false);
    setProcessing(true);
    try {
      const options = {
        intensity: sharpenIntensity,
        radius: sharpenRadius,
        threshold: sharpenThreshold,
        method: 'unsharp'
      };
      
      console.log('Applying sharpen with options:', options);
      const response = await photoAPI.sharpenPhoto(photo.id, options);
      
      // Fetch the updated photo data
      const updatedPhoto = await photoAPI.getPhotoDetail(photo.id);

      Alert.alert('Success', 'Photo sharpened successfully!', [
        {
          text: 'View',
          onPress: () => {
            // Navigate back and replace the photo data
            navigation.navigate('PhotoDetail', { photo: updatedPhoto, refresh: true });
          },
        },
      ]);
    } catch (error) {
      Alert.alert('Error', 'Failed to sharpen photo');
      console.error(error);
    } finally {
      setProcessing(false);
    }
  };

  const handleColorize = async (useAI = false) => {
    setProcessing(true);
    try {
      let response;
      if (useAI) {
        response = await photoAPI.colorizePhotoAI(photo.id);
      } else {
        response = await photoAPI.colorizePhoto(photo.id, 'auto');
      }

      // Fetch the updated photo data
      const updatedPhoto = await photoAPI.getPhotoDetail(photo.id);

      Alert.alert('Success', `Photo colorized successfully using ${useAI ? 'AI' : 'DNN'}!`, [
        {
          text: 'View',
          onPress: () => {
            // Navigate back and replace the photo data
            navigation.navigate('PhotoDetail', { photo: updatedPhoto, refresh: true });
          },
        },
      ]);
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Failed to colorize photo';
      Alert.alert('Error', errorMsg);
      console.error(error);
    } finally {
      setProcessing(false);
    }
  };

  const EnhancementOption = ({ icon, title, description, onPress, color, disabled = false }) => (
    <TouchableOpacity
      style={[styles.option, disabled && styles.optionDisabled]}
      onPress={onPress}
      disabled={processing || disabled}
    >
      <View style={[styles.optionIcon, { backgroundColor: color + '20' }]}>
        <Ionicons name={icon} size={32} color={disabled ? '#ccc' : color} />
      </View>
      <View style={styles.optionInfo}>
        <Text style={[styles.optionTitle, disabled && styles.optionTitleDisabled]}>{title}</Text>
        <Text style={[styles.optionDescription, disabled && styles.optionDescriptionDisabled]}>
          {disabled ? 'Only for black & white photos' : description}
        </Text>
      </View>
      <Ionicons name="chevron-forward" size={24} color={disabled ? '#eee' : '#ccc'} />
    </TouchableOpacity>
  );

  const imageUrl = showOriginal 
    ? (photo.original_url || photo.url) 
    : (photo.edited_url || photo.original_url || photo.url);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={28} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Enhance Photo</Text>
        <View style={styles.placeholder} />
      </View>

      <ScrollView>
        {authToken && imageUrl ? (
          <Image 
            source={{ 
              uri: `${BASE_URL}${imageUrl}`,
              headers: {
                Authorization: `Bearer ${authToken}`
              }
            }} 
            style={styles.image}
            resizeMode="contain"
          />
        ) : (
          <View style={styles.image}>
            <ActivityIndicator size="large" color="#E85D75" />
          </View>
        )}

        {photo.edited_url && (
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                showOriginal && styles.toggleButtonActive,
              ]}
              onPress={() => setShowOriginal(true)}
            >
              <Text
                style={[
                  styles.toggleText,
                  showOriginal && styles.toggleTextActive,
                ]}
              >
                Original
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                !showOriginal && styles.toggleButtonActive,
              ]}
              onPress={() => setShowOriginal(false)}
            >
              <Text
                style={[
                  styles.toggleText,
                  !showOriginal && styles.toggleTextActive,
                ]}
              >
                Colorized
              </Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.options}>
          <Text style={styles.sectionTitle}>Legacy Photo Restoration</Text>

          <EnhancementOption
            icon="brush"
            title="Sharpen"
            description="Fix blurry or degraded photos with custom controls"
            onPress={handleSharpenWithControls}
            color="#FF9800"
          />

          <EnhancementOption
            icon="color-palette"
            title="Colorize (DNN)"
            description="Fast colorization using DNN"
            onPress={() => handleColorize(false)}
            color="#4CAF50"
            disabled={!isBlackAndWhite}
          />

          <EnhancementOption
            icon="sparkles-outline"
            title="Colorize (AI)"
            description="Intelligent AI-powered colorization"
            onPress={() => handleColorize(true)}
            color="#9C27B0"
            disabled={!isBlackAndWhite}
          />
        </View>

        {processing && (
          <View style={styles.processingOverlay}>
            <ActivityIndicator size="large" color="#E85D75" />
            <Text style={styles.processingText}>Processing...</Text>
          </View>
        )}
      </ScrollView>

      <Modal
        visible={showSharpenControls}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowSharpenControls(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Sharpen Controls</Text>
              <TouchableOpacity onPress={() => setShowSharpenControls(false)}>
                <Ionicons name="close" size={28} color="#333" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.controlGroup}>
                <View style={styles.controlHeader}>
                  <Text style={styles.controlLabel}>Intensity</Text>
                  <Text style={styles.controlValue}>{sharpenIntensity.toFixed(1)}</Text>
                </View>
                <Slider
                  style={styles.slider}
                  minimumValue={0.5}
                  maximumValue={3.0}
                  step={0.1}
                  value={sharpenIntensity}
                  onValueChange={setSharpenIntensity}
                  minimumTrackTintColor="#FF9800"
                  maximumTrackTintColor="#ddd"
                  thumbTintColor="#FF9800"
                />
                <Text style={styles.controlDescription}>
                  Higher values create sharper images but may introduce artifacts
                </Text>
              </View>

              <View style={styles.controlGroup}>
                <View style={styles.controlHeader}>
                  <Text style={styles.controlLabel}>Radius</Text>
                  <Text style={styles.controlValue}>{sharpenRadius.toFixed(1)}</Text>
                </View>
                <Slider
                  style={styles.slider}
                  minimumValue={1.0}
                  maximumValue={5.0}
                  step={0.5}
                  value={sharpenRadius}
                  onValueChange={setSharpenRadius}
                  minimumTrackTintColor="#FF9800"
                  maximumTrackTintColor="#ddd"
                  thumbTintColor="#FF9800"
                />
                <Text style={styles.controlDescription}>
                  Controls the sharpening area size (smaller = finer detail)
                </Text>
              </View>

              <View style={styles.controlGroup}>
                <View style={styles.controlHeader}>
                  <Text style={styles.controlLabel}>Threshold</Text>
                  <Text style={styles.controlValue}>{sharpenThreshold}</Text>
                </View>
                <Slider
                  style={styles.slider}
                  minimumValue={0}
                  maximumValue={10}
                  step={1}
                  value={sharpenThreshold}
                  onValueChange={setSharpenThreshold}
                  minimumTrackTintColor="#FF9800"
                  maximumTrackTintColor="#ddd"
                  thumbTintColor="#FF9800"
                />
                <Text style={styles.controlDescription}>
                  Prevents sharpening low-contrast areas (reduces noise)
                </Text>
              </View>

              <View style={styles.presetContainer}>
                <Text style={styles.presetTitle}>Quick Presets</Text>
                <View style={styles.presetButtons}>
                  <TouchableOpacity
                    style={styles.presetButton}
                    onPress={() => {
                      setSharpenIntensity(1.0);
                      setSharpenRadius(1.5);
                      setSharpenThreshold(3);
                    }}
                  >
                    <Text style={styles.presetButtonText}>Light</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.presetButton}
                    onPress={() => {
                      setSharpenIntensity(1.5);
                      setSharpenRadius(2.0);
                      setSharpenThreshold(3);
                    }}
                  >
                    <Text style={styles.presetButtonText}>Medium</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.presetButton}
                    onPress={() => {
                      setSharpenIntensity(2.5);
                      setSharpenRadius(2.5);
                      setSharpenThreshold(2);
                    }}
                  >
                    <Text style={styles.presetButtonText}>Strong</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </ScrollView>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setShowSharpenControls(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.applyButton]}
                onPress={applySharpen}
              >
                <Text style={styles.applyButtonText}>Apply Sharpen</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  placeholder: {
    width: 28,
  },
  image: {
    width: width,
    height: width,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  toggleContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    padding: 15,
    gap: 10,
  },
  toggleButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
  },
  toggleButtonActive: {
    backgroundColor: '#E85D75',
  },
  toggleText: {
    fontSize: 14,
    color: '#666',
  },
  toggleTextActive: {
    color: '#fff',
    fontWeight: 'bold',
  },
  options: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
    borderRadius: 15,
    padding: 15,
    marginBottom: 12,
  },
  optionIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  optionInfo: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  optionDescription: {
    fontSize: 14,
    color: '#666',
  },
  optionDisabled: {
    opacity: 0.5,
    backgroundColor: '#f0f0f0',
  },
  optionTitleDisabled: {
    color: '#999',
  },
  optionDescriptionDisabled: {
    color: '#aaa',
    fontStyle: 'italic',
  },
  processingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255,255,255,0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  processingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 15,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 25,
    borderTopRightRadius: 25,
    maxHeight: '80%',
    paddingBottom: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
  },
  modalBody: {
    flex: 1,
    padding: 20,
  },
  controlGroup: {
    marginBottom: 30,
  },
  controlHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  controlLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  controlValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FF9800',
  },
  slider: {
    width: '100%',
    height: 40,
  },
  controlDescription: {
    fontSize: 12,
    color: '#999',
    marginTop: 5,
    fontStyle: 'italic',
  },
  presetContainer: {
    marginTop: 10,
  },
  presetTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
  },
  presetButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
  },
  presetButton: {
    flex: 1,
    backgroundColor: '#f0f0f0',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    alignItems: 'center',
  },
  presetButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FF9800',
  },
  modalFooter: {
    flexDirection: 'row',
    padding: 20,
    gap: 10,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 15,
    borderRadius: 12,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#f0f0f0',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  applyButton: {
    backgroundColor: '#FF9800',
  },
  applyButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
});
