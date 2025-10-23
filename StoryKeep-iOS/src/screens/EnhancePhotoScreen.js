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
const BASE_URL = 'https://storykeep.calmic.com.my';

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
  
  // AI Restoration controls modal state
  const [showAIRestorationControls, setShowAIRestorationControls] = useState(false);
  const [aiModel, setAIModel] = useState('codeformer'); // 'gfpgan' or 'codeformer'
  const [aiQuality, setAIQuality] = useState('balanced'); // 'fast', 'balanced', 'quality', 'maximum'
  const [fidelity, setFidelity] = useState(0.5); // CodeFormer fidelity (0.0-1.0)

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

  const handleAIRestorationWithControls = () => {
    setShowAIRestorationControls(true);
  };

  const applyAIRestoration = async () => {
    setShowAIRestorationControls(false);
    setProcessing(true);
    try {
      console.log('Applying AI restoration with:', { model: aiModel, quality: aiQuality, fidelity });
      const response = await photoAPI.repairDamage(photo.id, {
        type: 'ai',
        model: aiModel,
        quality: aiQuality,
        fidelity: fidelity
      });
      
      // Fetch the updated photo data
      const updatedPhoto = await photoAPI.getPhotoDetail(photo.id);

      Alert.alert('Success', `Photo restored successfully using ${aiModel.toUpperCase()}!`, [
        {
          text: 'View',
          onPress: () => {
            // Navigate back and replace the photo data
            navigation.navigate('PhotoDetail', { photo: updatedPhoto, refresh: true });
          },
        },
      ]);
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Failed to restore photo with AI';
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
          <Text style={styles.sectionTitle}>AI-Powered Restoration</Text>

          <EnhancementOption
            icon="sparkles"
            title="AI Restore (Professional)"
            description="Dramatically improve damaged/cracked photos using AI"
            onPress={handleAIRestorationWithControls}
            color="#E85D75"
          />

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

      <Modal
        visible={showAIRestorationControls}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowAIRestorationControls(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>AI Restoration Settings</Text>
              <TouchableOpacity onPress={() => setShowAIRestorationControls(false)}>
                <Ionicons name="close" size={28} color="#333" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.controlGroup}>
                <Text style={styles.controlLabel}>AI Model</Text>
                <View style={styles.modelButtons}>
                  <TouchableOpacity
                    style={[styles.modelButton, aiModel === 'gfpgan' && styles.modelButtonActive]}
                    onPress={() => setAIModel('gfpgan')}
                  >
                    <Text style={[styles.modelButtonText, aiModel === 'gfpgan' && styles.modelButtonTextActive]}>
                      GFPGAN
                    </Text>
                    <Text style={styles.modelSubtext}>Fast, preserves identity</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.modelButton, aiModel === 'codeformer' && styles.modelButtonActive]}
                    onPress={() => setAIModel('codeformer')}
                  >
                    <Text style={[styles.modelButtonText, aiModel === 'codeformer' && styles.modelButtonTextActive]}>
                      CodeFormer
                    </Text>
                    <Text style={styles.modelSubtext}>Best for severe damage</Text>
                  </TouchableOpacity>
                </View>
              </View>

              <View style={styles.controlGroup}>
                <Text style={styles.controlLabel}>Quality Preset</Text>
                <View style={styles.qualityButtons}>
                  {['fast', 'balanced', 'quality', 'maximum'].map((q) => (
                    <TouchableOpacity
                      key={q}
                      style={[styles.qualityButton, aiQuality === q && styles.qualityButtonActive]}
                      onPress={() => setAIQuality(q)}
                    >
                      <Text style={[styles.qualityButtonText, aiQuality === q && styles.qualityButtonTextActive]}>
                        {q.charAt(0).toUpperCase() + q.slice(1)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {aiModel === 'codeformer' && (
                <View style={styles.controlGroup}>
                  <View style={styles.controlHeader}>
                    <Text style={styles.controlLabel}>Fidelity</Text>
                    <Text style={styles.controlValue}>{fidelity.toFixed(2)}</Text>
                  </View>
                  <Slider
                    style={styles.slider}
                    minimumValue={0.0}
                    maximumValue={1.0}
                    step={0.05}
                    value={fidelity}
                    onValueChange={setFidelity}
                    minimumTrackTintColor="#E85D75"
                    maximumTrackTintColor="#ddd"
                    thumbTintColor="#E85D75"
                  />
                  <Text style={styles.controlDescription}>
                    Lower values = more enhancement, higher values = preserve original look
                  </Text>
                </View>
              )}

              <View style={styles.infoBox}>
                <Ionicons name="information-circle" size={20} color="#E85D75" />
                <Text style={styles.infoText}>
                  AI restoration works best on photos with faces. Processing may take 30-60 seconds.
                </Text>
              </View>
            </ScrollView>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setShowAIRestorationControls(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.applyButton]}
                onPress={applyAIRestoration}
              >
                <Text style={styles.applyButtonText}>Restore with AI</Text>
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
  modelButtons: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  modelButton: {
    flex: 1,
    backgroundColor: '#f8f8f8',
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
  },
  modelButtonActive: {
    backgroundColor: '#FFE5EC',
    borderColor: '#E85D75',
  },
  modelButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 5,
  },
  modelButtonTextActive: {
    color: '#E85D75',
  },
  modelSubtext: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
  },
  qualityButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  qualityButton: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#f8f8f8',
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 15,
    alignItems: 'center',
  },
  qualityButtonActive: {
    backgroundColor: '#FFE5EC',
    borderColor: '#E85D75',
  },
  qualityButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  qualityButtonTextActive: {
    color: '#E85D75',
    fontWeight: 'bold',
  },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: '#FFF5F7',
    borderRadius: 10,
    padding: 15,
    marginTop: 10,
    alignItems: 'flex-start',
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#666',
    marginLeft: 10,
    lineHeight: 20,
  },
});
