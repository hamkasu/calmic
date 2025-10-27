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
import ProgressBar from '../components/ProgressBar';
import { sharpenImage, SharpenPresets } from '../utils/imageProcessing';
import * as FileSystem from 'expo-file-system/legacy';

const { width } = Dimensions.get('window');
const BASE_URL = 'https://storykeep.calmic.com.my';

export default function EnhancePhotoScreen({ route, navigation }) {
  const { photo } = route.params;
  const [processing, setProcessing] = useState(false);
  const [showOriginal, setShowOriginal] = useState(true);
  const [authToken, setAuthToken] = useState(null);
  const [isBlackAndWhite, setIsBlackAndWhite] = useState(null);
  const [detectingColor, setDetectingColor] = useState(true);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [processingMessage, setProcessingMessage] = useState('');
  
  // Sharpen controls modal state
  const [showSharpenControls, setShowSharpenControls] = useState(false);
  const [sharpenIntensity, setSharpenIntensity] = useState(1.5);
  const [sharpenRadius, setSharpenRadius] = useState(2.5);
  const [sharpenPreview, setSharpenPreview] = useState(null);
  const [sharpenOriginal, setSharpenOriginal] = useState(null);
  const [sharpenProcessing, setSharpenProcessing] = useState(false);
  const [showBeforeAfter, setShowBeforeAfter] = useState(false);
  
  // AI Restoration controls modal state
  const [showAIRestorationControls, setShowAIRestorationControls] = useState(false);
  const [aiModel, setAIModel] = useState('codeformer'); // 'gfpgan' or 'codeformer'
  const [aiQuality, setAIQuality] = useState('balanced'); // 'fast', 'balanced', 'quality', 'maximum'
  const [fidelity, setFidelity] = useState(0.5); // CodeFormer fidelity (0.0-1.0)

  useEffect(() => {
    loadAuthToken();
    detectImageColor();
  }, []);

  // Auto-generate preview when sharpen modal opens
  useEffect(() => {
    if (showSharpenControls && authToken && !sharpenPreview) {
      console.log('🚀 Auto-generating preview on modal open');
      generateSharpenPreview();
    }
  }, [showSharpenControls, authToken]);

  // Debounced preview regeneration when sliders change
  useEffect(() => {
    if (!showSharpenControls || !sharpenOriginal) return;
    
    console.log('🎚️ Slider changed, scheduling preview update...');
    const debounceTimer = setTimeout(() => {
      console.log('⏱️ Debounce complete, regenerating preview');
      regeneratePreviewFromCache();
    }, 500); // 500ms debounce
    
    return () => clearTimeout(debounceTimer);
  }, [sharpenIntensity, sharpenRadius]);

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

  const generateSharpenPreview = async () => {
    let tempUri = null;
    let previewUri = null;
    try {
      setSharpenProcessing(true);
      
      // Get the image URI
      const imageUrl = showOriginal ? photo.original_url : (photo.edited_url || photo.original_url);
      const fullUrl = `${BASE_URL}${imageUrl}`;
      
      console.log('📥 Downloading image for preview...');
      // Download image to temp location with auth (with timeout)
      tempUri = FileSystem.documentDirectory + 'temp_sharpen_preview.jpg';
      
      const downloadPromise = FileSystem.downloadAsync(fullUrl, tempUri, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      // Add 30 second timeout
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Download timeout - check your connection')), 30000)
      );
      
      await Promise.race([downloadPromise, timeoutPromise]);
      
      // Store original for before/after comparison
      setSharpenOriginal(tempUri);
      
      console.log('⚡ Generating instant preview...');
      // Apply sharpening locally (instant)
      const result = await sharpenImage(tempUri, sharpenIntensity, sharpenRadius);
      previewUri = result.uri;
      setSharpenPreview(previewUri);
      setShowBeforeAfter(false); // Default to showing after (sharpened)
      
      console.log('✅ Preview ready!');
      
    } catch (error) {
      console.error('❌ Preview generation error:', error);
      Alert.alert(
        'Preview Error', 
        error.message || 'Failed to generate preview. Please check your connection and try again.',
        [{ text: 'OK' }]
      );
      // Cleanup on error - delete both temp and preview
      if (tempUri) {
        await FileSystem.deleteAsync(tempUri, { idempotent: true }).catch(() => {});
      }
      if (previewUri) {
        await FileSystem.deleteAsync(previewUri, { idempotent: true }).catch(() => {});
      }
      setSharpenOriginal(null);
      setSharpenPreview(null);
    } finally {
      setSharpenProcessing(false);
    }
  };

  // Fast preview regeneration using already-downloaded image
  const regeneratePreviewFromCache = async () => {
    if (!sharpenOriginal) {
      console.log('⚠️ No cached image, skipping regeneration');
      return;
    }
    
    let previewUri = null;
    try {
      setSharpenProcessing(true);
      
      // Clean up old preview
      if (sharpenPreview) {
        await FileSystem.deleteAsync(sharpenPreview, { idempotent: true }).catch(() => {});
      }
      
      // Generate new preview from cached original (instant!)
      console.log('⚡ Regenerating preview from cache...');
      const result = await sharpenImage(sharpenOriginal, sharpenIntensity, sharpenRadius);
      previewUri = result.uri;
      setSharpenPreview(previewUri);
      
      console.log('✅ Preview updated!');
      
    } catch (error) {
      console.error('❌ Preview regeneration error:', error);
      if (previewUri) {
        await FileSystem.deleteAsync(previewUri, { idempotent: true }).catch(() => {});
      }
    } finally {
      setSharpenProcessing(false);
    }
  };
  
  const cleanupSharpenModal = async () => {
    // Cleanup all temp files when modal closes
    if (sharpenPreview) {
      await FileSystem.deleteAsync(sharpenPreview, { idempotent: true }).catch(() => {});
    }
    if (sharpenOriginal) {
      await FileSystem.deleteAsync(sharpenOriginal, { idempotent: true }).catch(() => {});
    }
    setSharpenPreview(null);
    setSharpenOriginal(null);
    setShowBeforeAfter(false);
  };

  const applySharpen = async () => {
    if (!sharpenPreview) {
      Alert.alert('Error', 'Please generate a preview first');
      return;
    }

    setShowSharpenControls(false);
    setProcessing(true);
    setProcessingProgress(0);
    setProcessingMessage('Saving sharpened photo...');
    
    try {
      console.log('📤 Uploading client-side sharpened photo');
      
      setProcessingProgress(20);
      setProcessingMessage('Preparing upload...');
      
      // Read the sharpened preview file
      const fileInfo = await FileSystem.getInfoAsync(sharpenPreview);
      if (!fileInfo.exists) {
        throw new Error('Sharpened preview file not found');
      }
      
      setProcessingProgress(40);
      setProcessingMessage('Uploading to gallery...');
      
      // Create form data with the sharpened image
      const formData = new FormData();
      
      // Add the sharpened image file
      formData.append('photo', {
        uri: sharpenPreview,
        type: 'image/jpeg',
        name: `sharpened_${Date.now()}.jpg`,
      });
      
      // Add metadata
      formData.append('title', `${photo.title || 'Photo'} (Sharpened)`);
      formData.append('description', `Sharpened with intensity ${sharpenIntensity}, radius ${sharpenRadius}`);
      formData.append('enhancement_type', 'sharpen');
      formData.append('original_photo_id', photo.id.toString());
      
      console.log('🚀 Uploading sharpened photo to server');
      
      // Upload to server using the standard upload endpoint
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
      
      const response = await fetch(`${BASE_URL}/api/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
        body: formData,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Upload failed');
      }
      
      setProcessingProgress(75);
      setProcessingMessage('Saving to gallery...');
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Upload failed');
      }
      
      console.log('✅ Sharpened photo uploaded:', result);
      
      setProcessingProgress(90);
      setProcessingMessage('Fetching photo details...');
      
      // Fetch the newly created photo
      const newPhoto = await photoAPI.getPhotoDetail(result.photo_id);

      setProcessingProgress(100);
      setProcessingMessage('Complete!');
      
      // Success - cleanup preview files
      await cleanupSharpenModal();

      Alert.alert(
        'Photo Sharpened!', 
        'Your sharpened photo has been saved to your gallery.',
        [
          {
            text: 'View',
            onPress: () => {
              navigation.navigate('PhotoDetail', { photo: newPhoto, refresh: true });
            },
          },
          {
            text: 'OK',
            style: 'cancel',
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to save sharpened photo: ' + error.message);
      console.error('Sharpen save error:', error);
    } finally {
      setProcessing(false);
      setProcessingProgress(0);
      setProcessingMessage('');
    }
  };
  
  const applyPreset = async (presetKey) => {
    const preset = SharpenPresets[presetKey];
    console.log('🎯 Applying preset:', preset.name);
    setSharpenIntensity(preset.intensity);
    setSharpenRadius(preset.radius);
    // Preview will auto-update via debouncing (no manual call needed)
  };

  const handleColorize = async (useAI = false) => {
    setProcessing(true);
    setProcessingProgress(0);
    setProcessingMessage(`Initializing ${useAI ? 'AI' : 'DNN'} colorization...`);
    
    try {
      let response;
      setProcessingProgress(20);
      
      if (useAI) {
        setProcessingMessage('Processing with AI model (this may take 30-60 seconds)...');
        setProcessingProgress(30);
        response = await photoAPI.colorizePhotoAI(photo.id);
      } else {
        setProcessingMessage('Applying DNN colorization...');
        setProcessingProgress(40);
        response = await photoAPI.colorizePhoto(photo.id, 'auto');
      }

      setProcessingProgress(75);
      setProcessingMessage('Fetching colorized photo...');
      
      // Fetch the updated photo data
      const updatedPhoto = await photoAPI.getPhotoDetail(photo.id);

      setProcessingProgress(100);
      setProcessingMessage('Complete!');

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
      setProcessingProgress(0);
      setProcessingMessage('');
    }
  };

  const handleAIRestorationWithControls = () => {
    setShowAIRestorationControls(true);
  };

  const applyAIRestoration = async () => {
    setShowAIRestorationControls(false);
    setProcessing(true);
    setProcessingProgress(0);
    setProcessingMessage(`Initializing ${aiModel.toUpperCase()} model...`);
    
    try {
      console.log('Applying AI restoration with:', { model: aiModel, quality: aiQuality, fidelity });
      setProcessingProgress(15);
      setProcessingMessage('Loading AI model...');
      
      setProcessingProgress(25);
      setProcessingMessage(`Analyzing photo with ${aiModel.toUpperCase()} (30-90 seconds)...`);
      
      const response = await photoAPI.repairDamage(photo.id, {
        type: 'ai',
        model: aiModel,
        quality: aiQuality,
        fidelity: fidelity
      });
      
      setProcessingProgress(80);
      setProcessingMessage('Fetching restored photo...');
      
      // Fetch the updated photo data
      const updatedPhoto = await photoAPI.getPhotoDetail(photo.id);

      setProcessingProgress(100);
      setProcessingMessage('Restoration complete!');

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
      setProcessingProgress(0);
      setProcessingMessage('');
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
            <View style={styles.processingContent}>
              <ActivityIndicator size="large" color="#E85D75" />
              <ProgressBar 
                progress={processingProgress} 
                message={processingMessage}
                color="#E85D75"
                showPercentage={true}
              />
            </View>
          </View>
        )}
      </ScrollView>

      <Modal
        visible={showSharpenControls}
        animationType="slide"
        transparent={false}
        onRequestClose={async () => {
          await cleanupSharpenModal();
          setShowSharpenControls(false);
        }}
      >
        <View style={styles.fullScreenModal}>
          <View style={styles.fullScreenHeader}>
            <TouchableOpacity 
              onPress={async () => {
                await cleanupSharpenModal();
                setShowSharpenControls(false);
              }} 
              style={styles.closeButton}
            >
              <Ionicons name="close" size={28} color="#333" />
            </TouchableOpacity>
            <Text style={styles.fullScreenTitle}>Sharpen Photo</Text>
            <TouchableOpacity onPress={applySharpen} style={styles.doneButton}>
              <Text style={styles.doneButtonText}>Done</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.fullScreenBody}>
            {/* Preview Section */}
            <View style={styles.previewSection}>
              <Text style={styles.sectionLabel}>Preview</Text>
              <View style={styles.previewContainer}>
                {sharpenProcessing ? (
                  <View style={styles.previewLoading}>
                    <ActivityIndicator size="large" color="#FF9800" />
                    <Text style={styles.previewLoadingText}>Generating preview...</Text>
                  </View>
                ) : sharpenPreview ? (
                  <View style={styles.beforeAfterContainer}>
                    <Image 
                      source={{ uri: showBeforeAfter ? sharpenOriginal : sharpenPreview }} 
                      style={styles.previewImage}
                      resizeMode="contain"
                    />
                    <TouchableOpacity 
                      style={styles.compareButton}
                      onPress={() => setShowBeforeAfter(!showBeforeAfter)}
                    >
                      <Ionicons name={showBeforeAfter ? "eye-off" : "eye"} size={20} color="#fff" />
                      <Text style={styles.compareButtonText}>
                        {showBeforeAfter ? "Before" : "After"}
                      </Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  <View style={styles.noPreview}>
                    <Image 
                      source={{ 
                        uri: `${BASE_URL}${showOriginal ? photo.original_url : (photo.edited_url || photo.original_url)}`,
                        headers: { Authorization: `Bearer ${authToken}` }
                      }} 
                      style={styles.previewImage}
                      resizeMode="contain"
                    />
                    <TouchableOpacity 
                      style={styles.generatePreviewButton}
                      onPress={generateSharpenPreview}
                    >
                      <Ionicons name="eye" size={20} color="#fff" />
                      <Text style={styles.generatePreviewButtonText}>Generate Preview</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            </View>

            {/* Quick Presets */}
            <View style={styles.presetsSection}>
              <Text style={styles.sectionLabel}>Quick Presets</Text>
              <View style={styles.presetsGrid}>
                {Object.entries(SharpenPresets).map(([key, preset]) => (
                  <TouchableOpacity
                    key={key}
                    style={[
                      styles.presetCard,
                      sharpenIntensity === preset.intensity && sharpenRadius === preset.radius && styles.presetCardActive
                    ]}
                    onPress={() => applyPreset(key)}
                  >
                    <Ionicons name={preset.icon} size={32} color="#FF9800" />
                    <Text style={styles.presetCardTitle}>{preset.name}</Text>
                    <Text style={styles.presetCardDescription}>{preset.description}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Manual Controls */}
            <View style={styles.manualSection}>
              <Text style={styles.sectionLabel}>Fine-Tune</Text>
              
              <View style={styles.controlGroup}>
                <View style={styles.controlHeader}>
                  <Text style={styles.controlLabel}>
                    <Ionicons name="contrast" size={16} /> Intensity
                  </Text>
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
                  Controls sharpening strength
                </Text>
              </View>

              <View style={styles.controlGroup}>
                <View style={styles.controlHeader}>
                  <Text style={styles.controlLabel}>
                    <Ionicons name="resize" size={16} /> Radius
                  </Text>
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
                  Affects sharpening detail level
                </Text>
              </View>
            </View>

            <View style={styles.infoBox}>
              <Ionicons name="information-circle" size={20} color="#FF9800" />
              <Text style={styles.infoText}>
                Sharpening is processed instantly on your device for better speed and privacy. 
                The result will be saved to your photo library after applying.
              </Text>
            </View>
          </ScrollView>
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
    backgroundColor: 'rgba(255,255,255,0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  processingContent: {
    backgroundColor: '#fff',
    padding: 30,
    borderRadius: 15,
    width: '80%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
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
  // Full-screen sharpen modal styles
  fullScreenModal: {
    flex: 1,
    backgroundColor: '#fff',
  },
  fullScreenHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    backgroundColor: '#fff',
  },
  closeButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'flex-start',
  },
  fullScreenTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  doneButton: {
    width: 60,
    height: 40,
    justifyContent: 'center',
    alignItems: 'flex-end',
  },
  doneButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FF9800',
  },
  fullScreenBody: {
    flex: 1,
    backgroundColor: '#f8f8f8',
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  previewSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 15,
  },
  previewContainer: {
    width: '100%',
    height: 300,
    backgroundColor: '#f0f0f0',
    borderRadius: 12,
    overflow: 'hidden',
  },
  previewImage: {
    width: '100%',
    height: '100%',
  },
  previewLoading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  previewLoadingText: {
    marginTop: 10,
    fontSize: 14,
    color: '#666',
  },
  beforeAfterContainer: {
    position: 'relative',
    width: '100%',
    height: '100%',
  },
  compareButton: {
    position: 'absolute',
    bottom: 15,
    right: 15,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 20,
    gap: 5,
  },
  compareButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  noPreview: {
    position: 'relative',
    width: '100%',
    height: '100%',
  },
  generatePreviewButton: {
    position: 'absolute',
    bottom: 15,
    left: '50%',
    transform: [{ translateX: -75 }],
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FF9800',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
    gap: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  generatePreviewButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: 'bold',
  },
  presetsSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 15,
  },
  presetsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  presetCard: {
    flex: 1,
    backgroundColor: '#f8f8f8',
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderRadius: 15,
    padding: 15,
    alignItems: 'center',
    minHeight: 120,
  },
  presetCardActive: {
    backgroundColor: '#FFF5F7',
    borderColor: '#FF9800',
  },
  presetCardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
    marginBottom: 4,
  },
  presetCardDescription: {
    fontSize: 11,
    color: '#666',
    textAlign: 'center',
    lineHeight: 14,
  },
  manualSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 15,
  },
});
