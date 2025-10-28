/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

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
  TextInput,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import { photoAPI, voiceMemoAPI, commentAPI } from '../services/api';
import * as FileSystem from 'expo-file-system/legacy';
import * as MediaLibrary from 'expo-media-library';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { GestureDetector, Gesture } from 'react-native-gesture-handler';
import { sharePhoto } from '../utils/sharePhoto';

const { width } = Dimensions.get('window');
const BASE_URL = 'https://storykeep.calmic.com.my';

export default function PhotoDetailScreen({ route, navigation }) {
  const { photo: initialPhoto } = route.params;
  const [photo, setPhoto] = useState(initialPhoto);
  // Default to showing edited version if it exists, otherwise show original
  const [showOriginal, setShowOriginal] = useState(!initialPhoto.edited_url);
  const [aiMetadata, setAIMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [imageLoading, setImageLoading] = useState(true);
  
  // Pinch zoom states
  const scale = new Animated.Value(1);
  const [currentScale, setCurrentScale] = useState(1);
  
  // Simple voice memo debug states
  const [recording, setRecording] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedUri, setRecordedUri] = useState(null);
  const [fileSize, setFileSize] = useState(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [sound, setSound] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Existing voice memos states
  const [existingVoiceMemos, setExistingVoiceMemos] = useState([]);
  const [playingMemoId, setPlayingMemoId] = useState(null);

  // Comments/Annotations states
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loadingComments, setLoadingComments] = useState(false);

  useEffect(() => {
    loadData();
    loadExistingVoiceMemos();
    loadComments();
    
    // Cleanup on unmount
    return () => {
      if (sound) {
        sound.unloadAsync();
      }
    };
  }, []);

  // Reset image loading state when switching between original/edited
  useEffect(() => {
    setImageLoading(true);
  }, [showOriginal]);

  const loadData = async () => {
    const token = await AsyncStorage.getItem('authToken');
    setAuthToken(token);
    loadAIMetadata();
  };

  const loadAIMetadata = async () => {
    try {
      const response = await photoAPI.getAIMetadata(photo.id);
      setAIMetadata(response);
    } catch (error) {
      console.error('AI metadata error:', error);
    }
  };

  const loadExistingVoiceMemos = async () => {
    try {
      // If photo already has voice_memos array (from family vault), use it directly
      if (photo.voice_memos && Array.isArray(photo.voice_memos)) {
        setExistingVoiceMemos(photo.voice_memos);
        console.log('📝 Loaded voice memos from photo object:', photo.voice_memos.length);
        return;
      }

      // Otherwise, fetch from API (for regular photos)
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${BASE_URL}/api/photos/${photo.id}/voice-memos`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setExistingVoiceMemos(data.voice_memos || []);
        console.log('📝 Loaded voice memos from API:', data.voice_memos?.length || 0);
      }
    } catch (error) {
      console.error('❌ Error loading voice memos:', error);
    }
  };

  const playExistingVoiceMemo = async (memoId) => {
    try {
      console.log('▶️ Playing voice memo:', memoId);
      
      // Stop any existing playback
      if (sound) {
        await sound.unloadAsync();
        setSound(null);
      }

      const token = await AsyncStorage.getItem('authToken');
      
      // Download the audio file to a temporary location
      const audioUrl = `${BASE_URL}/api/voice-memos/${memoId}/audio`;
      const fileUri = FileSystem.documentDirectory + `voice_memo_${memoId}.m4a`;
      
      const downloadResult = await FileSystem.downloadAsync(
        audioUrl,
        fileUri,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      console.log('📥 Downloaded to:', downloadResult.uri);

      // Set audio mode for playback
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
        staysActiveInBackground: false,
      });

      // Play the downloaded file
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: downloadResult.uri },
        { shouldPlay: true }
      );
      
      setSound(newSound);
      setPlayingMemoId(memoId);
      
      newSound.setOnPlaybackStatusUpdate((status) => {
        if (status.didJustFinish) {
          console.log('✅ Playback finished');
          setPlayingMemoId(null);
          // Clean up temp file
          FileSystem.deleteAsync(downloadResult.uri, { idempotent: true }).catch(() => {});
        }
      });
      
      console.log('✅ Playing voice memo');
    } catch (error) {
      console.error('❌ Error playing voice memo:', error);
      Alert.alert('Error', 'Failed to play voice note: ' + error.message);
      setPlayingMemoId(null);
    }
  };

  const stopExistingVoiceMemo = async () => {
    try {
      if (sound) {
        console.log('⏹️ Stopping voice memo playback');
        await sound.stopAsync();
        await sound.unloadAsync();
        setSound(null);
        setPlayingMemoId(null);
      }
    } catch (error) {
      console.error('❌ Error stopping playback:', error);
    }
  };

  const loadComments = async () => {
    try {
      setLoadingComments(true);
      
      // If photo already has comments array (from family vault), use it directly
      if (photo.comments && Array.isArray(photo.comments)) {
        setComments(photo.comments);
        console.log('💬 Loaded comments from photo object:', photo.comments.length);
        return;
      }

      // Otherwise, fetch from API (for regular photos)
      const response = await commentAPI.getComments(photo.id);
      setComments(response.comments || []);
      console.log('💬 Loaded comments from API:', response.comments?.length || 0);
    } catch (error) {
      console.error('❌ Error loading comments:', error);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) {
      Alert.alert('Error', 'Please enter a comment');
      return;
    }

    try {
      setLoadingComments(true);
      const response = await commentAPI.addComment(photo.id, newComment.trim());
      
      if (response.success) {
        setComments([response.comment, ...comments]);
        setNewComment('');
        Alert.alert('Success', 'Comment added successfully');
      }
    } catch (error) {
      console.error('❌ Error adding comment:', error);
      Alert.alert('Error', 'Failed to add comment');
    } finally {
      setLoadingComments(false);
    }
  };

  const handleDeleteComment = (commentId) => {
    Alert.alert(
      'Delete Comment',
      'Are you sure you want to delete this comment?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await commentAPI.deleteComment(commentId);
              setComments(comments.filter(c => c.id !== commentId));
              Alert.alert('Success', 'Comment deleted');
            } catch (error) {
              console.error('❌ Error deleting comment:', error);
              Alert.alert('Error', 'Failed to delete comment');
            }
          },
        },
      ]
    );
  };

  const handleEnhance = () => {
    navigation.navigate('EnhancePhoto', { photo });
  };

  const handleDownload = async () => {
    try {
      setLoading(true);
      const { status } = await MediaLibrary.requestPermissionsAsync();
      
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Cannot save photo without permission');
        return;
      }

      const relativePath = showOriginal ? photo.url : (photo.edited_url || photo.url);
      const imageUrl = BASE_URL + relativePath;
      const fileUri = FileSystem.documentDirectory + `photo_${photo.id}.jpg`;
      
      console.log('📥 Downloading photo from:', imageUrl);
      
      const { uri } = await FileSystem.downloadAsync(
        imageUrl, 
        fileUri,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        }
      );
      
      console.log('💾 Saving to library from:', uri);
      const asset = await MediaLibrary.createAssetAsync(uri);
      
      Alert.alert('Success', 'Photo saved to your library!');
      console.log('✅ Photo saved successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to save photo');
      console.error('❌ Download error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Photo',
      'Are you sure you want to delete this photo?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await photoAPI.deletePhoto(photo.id);
              Alert.alert('Success', 'Photo deleted', [
                {
                  text: 'OK',
                  onPress: () => navigation.goBack(),
                },
              ]);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete photo');
            }
          },
        },
      ]
    );
  };

  const handleShare = async () => {
    await sharePhoto(photo, authToken, !showOriginal);
  };

  const handleRename = () => {
    Alert.prompt(
      'Rename Photo',
      'Enter a new name for this photo:',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Rename',
          onPress: async (newName) => {
            if (!newName || !newName.trim()) {
              Alert.alert('Error', 'Photo name cannot be empty');
              return;
            }
            
            try {
              setLoading(true);
              const response = await photoAPI.renamePhoto(photo.id, newName.trim());
              
              if (response.success) {
                // Update local photo state
                setPhoto({ ...photo, original_name: newName.trim() });
                Alert.alert('Success', 'Photo renamed successfully');
              } else {
                Alert.alert('Error', response.error || 'Failed to rename photo');
              }
            } catch (error) {
              console.error('❌ Rename error:', error);
              Alert.alert('Error', 'Failed to rename photo');
            } finally {
              setLoading(false);
            }
          },
        },
      ],
      'plain-text',
      photo.original_name || 'Photo'
    );
  };

  // Simple debugging voice memo functions
  const startRecording = async () => {
    try {
      console.log('🎤 Starting recording...');
      
      const permission = await Audio.requestPermissionsAsync();
      if (permission.status !== 'granted') {
        Alert.alert('Permission Required', 'Microphone access is needed');
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      
      setRecording(recording);
      setIsRecording(true);
      setRecordedUri(null);
      setFileSize(null);
      console.log('✅ Recording started');
    } catch (error) {
      console.error('❌ Recording start error:', error);
      Alert.alert('Error', 'Failed to start recording');
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      console.log('⏹️ Stopping recording...');
      setIsRecording(false);
      
      // Get status before stopping to capture duration
      const status = await recording.getStatusAsync();
      const durationMillis = status.durationMillis || 0;
      const durationSeconds = durationMillis / 1000;
      
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);
      setRecordedUri(uri);
      setRecordingDuration(durationSeconds);

      // Get file size
      const fileInfo = await FileSystem.getInfoAsync(uri);
      const sizeMB = (fileInfo.size / (1024 * 1024)).toFixed(2);
      setFileSize(`${sizeMB} MB`);
      
      console.log('✅ Recording stopped');
      console.log('📁 File URI:', uri);
      console.log('📊 File size:', sizeMB, 'MB');
      console.log('⏱️ Duration:', durationSeconds.toFixed(2), 'seconds');
      
      Alert.alert('Recording Complete', `File size: ${sizeMB} MB\nDuration: ${durationSeconds.toFixed(1)}s`);
    } catch (error) {
      console.error('❌ Recording stop error:', error);
      Alert.alert('Error', 'Failed to stop recording');
    }
  };

  const playRecording = async () => {
    if (!recordedUri) return;

    try {
      console.log('▶️ Playing recording...');
      
      // Stop any existing playback
      if (sound) {
        await sound.unloadAsync();
      }

      // Set audio mode for playback (works even in silent mode)
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
        staysActiveInBackground: false,
      });

      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: recordedUri },
        { shouldPlay: true }
      );
      
      setSound(newSound);
      setIsPlaying(true);
      
      newSound.setOnPlaybackStatusUpdate((status) => {
        if (status.didJustFinish) {
          console.log('✅ Playback finished');
          setIsPlaying(false);
        }
      });
      
      console.log('✅ Playing with audio mode configured...');
    } catch (error) {
      console.error('❌ Playback error:', error);
      Alert.alert('Error', 'Failed to play recording: ' + error.message);
      setIsPlaying(false);
    }
  };

  const stopPlayback = async () => {
    try {
      if (sound) {
        console.log('⏹️ Stopping playback...');
        await sound.stopAsync();
        await sound.unloadAsync();
        setSound(null);
        setIsPlaying(false);
        console.log('✅ Playback stopped');
      }
    } catch (error) {
      console.error('❌ Stop playback error:', error);
    }
  };

  const uploadRecording = async () => {
    if (!recordedUri) return;

    try {
      console.log('📤 Uploading recording...');
      setLoading(true);

      // Use the same upload pattern as camera (working)
      const formData = new FormData();
      formData.append('audio', {
        uri: recordedUri,
        type: 'audio/m4a',
        name: `voice-memo-${Date.now()}.m4a`,
      });
      formData.append('duration', recordingDuration.toString());

      // Get auth token
      const token = await AsyncStorage.getItem('authToken');
      
      // Direct fetch upload like camera
      const response = await fetch(`${BASE_URL}/api/photos/${photo.id}/voice-memos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      console.log('✅ Upload successful:', data);
      
      // Clear the recording state after successful upload
      setRecordedUri(null);
      setFileSize(null);
      setRecordingDuration(0);
      if (sound) {
        await sound.unloadAsync();
        setSound(null);
      }
      setIsPlaying(false);
      
      // Reload voice memos to show the new one
      await loadExistingVoiceMemos();
      
      Alert.alert('Success', 'Voice note uploaded successfully!');
    } catch (error) {
      console.error('❌ Upload error:', error);
      Alert.alert('Upload Failed', error.message || 'Failed to upload voice note');
    } finally {
      setLoading(false);
    }
  };

  // Use same URL pattern as Dashboard and Gallery
  const getImageUrl = (urlPath) => {
    if (!urlPath) return null;
    if (urlPath.startsWith('http')) return urlPath;
    if (urlPath.startsWith('/')) return `${BASE_URL}${urlPath}`;
    return urlPath;
  };

  const originalImageUrl = getImageUrl(photo.original_url || photo.url);
  const editedImageUrl = getImageUrl(photo.edited_url);
  const imageUrl = showOriginal ? originalImageUrl : (editedImageUrl || originalImageUrl);

  // Pinch zoom gesture
  const pinchGesture = Gesture.Pinch()
    .onUpdate((e) => {
      const newScale = currentScale * e.scale;
      // Limit zoom between 1x and 5x
      if (newScale >= 1 && newScale <= 5) {
        scale.setValue(newScale);
      }
    })
    .onEnd((e) => {
      const newScale = currentScale * e.scale;
      // Limit zoom between 1x and 5x
      const clampedScale = Math.min(Math.max(newScale, 1), 5);
      setCurrentScale(clampedScale);
      
      // If zoomed out past 1x, reset to 1x
      if (clampedScale < 1.1) {
        Animated.spring(scale, {
          toValue: 1,
          useNativeDriver: true,
        }).start();
        setCurrentScale(1);
      }
    });

  // Double tap to reset zoom
  const doubleTapGesture = Gesture.Tap()
    .numberOfTaps(2)
    .onEnd(() => {
      Animated.spring(scale, {
        toValue: 1,
        useNativeDriver: true,
      }).start();
      setCurrentScale(1);
    });

  const composedGesture = Gesture.Race(doubleTapGesture, pinchGesture);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={28} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Photo Detail</Text>
        <TouchableOpacity onPress={handleDelete}>
          <Ionicons name="trash-outline" size={24} color="#E85D75" />
        </TouchableOpacity>
      </View>

      <ScrollView>
        <View style={styles.imageContainer}>
          {imageUrl && authToken ? (
            <>
              <GestureDetector gesture={composedGesture}>
                <Animated.Image 
                  source={{ 
                    uri: imageUrl,
                    headers: {
                      Authorization: `Bearer ${authToken}`
                    }
                  }} 
                  style={[
                    styles.image,
                    {
                      transform: [{ scale: scale }]
                    }
                  ]}
                  resizeMode="contain"
                  onLoadStart={() => setImageLoading(true)}
                  onLoad={() => setImageLoading(false)}
                  onError={() => setImageLoading(false)}
                />
              </GestureDetector>
              {imageLoading && (
                <View style={styles.imageLoadingOverlay}>
                  <ActivityIndicator size="large" color="#E85D75" />
                  <Text style={styles.loadingText}>Loading photo...</Text>
                </View>
              )}
            </>
          ) : (
            <View style={styles.image}>
              <ActivityIndicator size="large" color="#E85D75" />
            </View>
          )}
          {currentScale > 1 && (
            <View style={styles.zoomIndicator}>
              <Text style={styles.zoomText}>{currentScale.toFixed(1)}x</Text>
            </View>
          )}
        </View>

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
              onPress={() => {
                // Navigate to enhanced gallery instead of toggling
                navigation.navigate('EnhancedGallery', { photo });
              }}
            >
              <Text
                style={[
                  styles.toggleText,
                  !showOriginal && styles.toggleTextActive,
                ]}
              >
                Enhanced
              </Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.actions}>
          <TouchableOpacity style={styles.actionButton} onPress={handleEnhance}>
            <Ionicons name="sparkles" size={24} color="#E85D75" />
            <Text style={styles.actionText}>Enhance</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={handleDownload}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#E85D75" />
            ) : (
              <>
                <Ionicons name="download" size={24} color="#E85D75" />
                <Text style={styles.actionText}>Download</Text>
              </>
            )}
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.actionButton} 
            onPress={handleShare}
          >
            <Ionicons name="share-social" size={24} color="#E85D75" />
            <Text style={styles.actionText}>Share</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.actionButton} 
            onPress={handleRename}
          >
            <Ionicons name="pencil" size={24} color="#E85D75" />
            <Text style={styles.actionText}>Rename</Text>
          </TouchableOpacity>
        </View>

        {existingVoiceMemos.length > 0 && (
          <View style={styles.existingVoicesContainer}>
            <Text style={styles.existingVoicesTitle}>
              Voice Notes ({existingVoiceMemos.length})
            </Text>
            
            {existingVoiceMemos.map((memo) => (
              <View key={memo.id} style={styles.voiceMemoCard}>
                <View style={styles.voiceMemoInfo}>
                  <Text style={styles.voiceMemoTitle}>
                    {memo.title || `Voice Note ${memo.id}`}
                  </Text>
                  <Text style={styles.voiceMemoMeta}>
                    {memo.duration_formatted || `${memo.duration}s`} • {memo.file_size_mb} MB
                  </Text>
                  <Text style={styles.voiceMemoDate}>
                    {new Date(memo.created_at).toLocaleString()}
                  </Text>
                </View>
                
                <TouchableOpacity
                  style={[
                    styles.playButton,
                    playingMemoId === memo.id && styles.playButtonActive
                  ]}
                  onPress={() => {
                    if (playingMemoId === memo.id) {
                      stopExistingVoiceMemo();
                    } else {
                      playExistingVoiceMemo(memo.id);
                    }
                  }}
                >
                  <Ionicons 
                    name={playingMemoId === memo.id ? "stop-circle" : "play-circle"} 
                    size={28} 
                    color="#fff" 
                  />
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

        <View style={styles.voiceContainer}>
          <Text style={styles.voiceTitle}>Record New Voice Note</Text>
          
          <View style={styles.debugControls}>
            {!isRecording && !recordedUri && (
              <TouchableOpacity
                style={styles.startButton}
                onPress={startRecording}
              >
                <Ionicons name="mic" size={32} color="#fff" />
                <Text style={styles.buttonText}>Start Recording</Text>
              </TouchableOpacity>
            )}

            {isRecording && (
              <TouchableOpacity
                style={styles.stopButton}
                onPress={stopRecording}
              >
                <Ionicons name="stop-circle" size={32} color="#fff" />
                <Text style={styles.buttonText}>Stop Recording</Text>
              </TouchableOpacity>
            )}

            {recordedUri && (
              <View style={styles.recordingInfo}>
                <View style={styles.fileSizeContainer}>
                  <Text style={styles.fileSizeLabel}>File Size:</Text>
                  <Text style={styles.fileSizeValue}>{fileSize}</Text>
                </View>
                
                <View style={styles.playbackControls}>
                  {!isPlaying ? (
                    <TouchableOpacity
                      style={styles.replayButton}
                      onPress={playRecording}
                    >
                      <Ionicons name="play-circle" size={32} color="#fff" />
                      <Text style={styles.buttonText}>Replay</Text>
                    </TouchableOpacity>
                  ) : (
                    <TouchableOpacity
                      style={styles.stopPlaybackButton}
                      onPress={stopPlayback}
                    >
                      <Ionicons name="stop-circle" size={32} color="#fff" />
                      <Text style={styles.buttonText}>Stop</Text>
                    </TouchableOpacity>
                  )}

                  <TouchableOpacity
                    style={styles.uploadButton}
                    onPress={uploadRecording}
                    disabled={loading}
                  >
                    {loading ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <>
                        <Ionicons name="cloud-upload" size={32} color="#fff" />
                        <Text style={styles.buttonText}>Upload</Text>
                      </>
                    )}
                  </TouchableOpacity>
                </View>

                <TouchableOpacity
                  style={styles.resetButton}
                  onPress={() => {
                    setRecordedUri(null);
                    setFileSize(null);
                    setIsPlaying(false);
                    if (sound) {
                      sound.unloadAsync();
                      setSound(null);
                    }
                  }}
                >
                  <Text style={styles.resetButtonText}>New Recording</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>

        {/* Annotations/Comments Section */}
        <View style={styles.commentsContainer}>
          <Text style={styles.commentsTitle}>Annotations</Text>
          
          {/* Add Comment Input */}
          <View style={styles.addCommentContainer}>
            <TextInput
              style={styles.commentInput}
              placeholder="Add a note or comment..."
              placeholderTextColor="#999"
              value={newComment}
              onChangeText={setNewComment}
              multiline
              numberOfLines={3}
            />
            <TouchableOpacity
              style={styles.addCommentButton}
              onPress={handleAddComment}
              disabled={loadingComments || !newComment.trim()}
            >
              {loadingComments ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Ionicons name="add-circle" size={20} color="#fff" />
                  <Text style={styles.addCommentButtonText}>Add</Text>
                </>
              )}
            </TouchableOpacity>
          </View>

          {/* Comments List */}
          {comments.length > 0 ? (
            <View style={styles.commentsList}>
              <Text style={styles.commentsCount}>
                {comments.length} {comments.length === 1 ? 'annotation' : 'annotations'}
              </Text>
              {comments.map((comment) => (
                <View key={comment.id} style={styles.commentCard}>
                  <View style={styles.commentHeader}>
                    <View>
                      <Text style={styles.commentUsername}>{comment.username}</Text>
                      <Text style={styles.commentDate}>
                        {new Date(comment.created_at).toLocaleString()}
                      </Text>
                    </View>
                    <TouchableOpacity
                      onPress={() => handleDeleteComment(comment.id)}
                      style={styles.deleteCommentButton}
                    >
                      <Ionicons name="trash-outline" size={20} color="#ff4444" />
                    </TouchableOpacity>
                  </View>
                  <Text style={styles.commentText}>{comment.comment_text}</Text>
                </View>
              ))}
            </View>
          ) : (
            <Text style={styles.noComments}>No annotations yet. Add one above!</Text>
          )}
        </View>

        {/* Photo Metadata/Annotations from Railway */}
        {(photo.processing_notes || photo.back_text || photo.date_text || photo.location_text || photo.occasion || photo.photo_date || photo.condition || photo.photo_source) && (
          <View style={styles.metadataContainer}>
            <Text style={styles.metadataTitle}>Photo Details</Text>
            
            {photo.processing_notes && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Processing Notes:</Text>
                <Text style={styles.metadataValue}>{photo.processing_notes}</Text>
              </View>
            )}

            {photo.photo_date && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Photo Date:</Text>
                <Text style={styles.metadataValue}>{new Date(photo.photo_date).toLocaleDateString()}</Text>
              </View>
            )}

            {photo.date_text && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Date Description:</Text>
                <Text style={styles.metadataValue}>{photo.date_text}</Text>
              </View>
            )}

            {photo.location_text && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Location:</Text>
                <Text style={styles.metadataValue}>{photo.location_text}</Text>
              </View>
            )}

            {photo.occasion && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Occasion:</Text>
                <Text style={styles.metadataValue}>{photo.occasion}</Text>
              </View>
            )}

            {photo.back_text && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Back of Photo Text:</Text>
                <Text style={styles.metadataValue}>{photo.back_text}</Text>
              </View>
            )}

            {photo.condition && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Condition:</Text>
                <Text style={styles.metadataValue}>{photo.condition}</Text>
              </View>
            )}

            {photo.photo_source && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Source:</Text>
                <Text style={styles.metadataValue}>{photo.photo_source}</Text>
              </View>
            )}
            
            {photo.enhancement_metadata && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Enhancement:</Text>
                <Text style={styles.metadataValue}>
                  {photo.enhancement_metadata.colorization?.method === 'dnn' ? 'DNN Colorization' : 
                   photo.enhancement_metadata.colorization?.method === 'ai_guided_dnn' ? 'AI-Guided Colorization' : 
                   'Enhanced'}
                </Text>
              </View>
            )}
          </View>
        )}

        {aiMetadata && (
          <View style={styles.metadataContainer}>
            <Text style={styles.metadataTitle}>AI Analysis</Text>
            
            {aiMetadata.objects && aiMetadata.objects.length > 0 && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Objects Detected:</Text>
                <View style={styles.tagContainer}>
                  {aiMetadata.objects.map((obj, index) => (
                    <View key={index} style={styles.tag}>
                      <Text style={styles.tagText}>{obj}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {aiMetadata.description && (
              <View style={styles.metadataSection}>
                <Text style={styles.metadataLabel}>Description:</Text>
                <Text style={styles.metadataValue}>{aiMetadata.description}</Text>
              </View>
            )}
          </View>
        )}

        <View style={styles.infoContainer}>
          <Text style={styles.infoTitle}>Photo Information</Text>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Filename:</Text>
            <Text style={styles.infoValue}>{photo.filename}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Created:</Text>
            <Text style={styles.infoValue}>
              {new Date(photo.created_at).toLocaleDateString()}
            </Text>
          </View>
          {photo.file_size && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Size:</Text>
              <Text style={styles.infoValue}>
                {(photo.file_size / 1024 / 1024).toFixed(2)} MB
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
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
  imageContainer: {
    width: width,
    height: width,
    position: 'relative',
    backgroundColor: '#f0f0f0',
  },
  image: {
    width: width,
    height: width,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  imageLoadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(240, 240, 240, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 5,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 14,
    color: '#666',
  },
  zoomIndicator: {
    position: 'absolute',
    top: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
    zIndex: 10,
  },
  zoomText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
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
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  actionButton: {
    alignItems: 'center',
  },
  actionText: {
    fontSize: 12,
    color: '#E85D75',
    marginTop: 5,
  },
  actionButtonDisabled: {
    opacity: 0.5,
  },
  actionTextDisabled: {
    color: '#999',
  },
  metadataContainer: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  metadataTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  metadataSection: {
    marginBottom: 15,
  },
  metadataLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  metadataValue: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  tagContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tag: {
    backgroundColor: '#FFF0F3',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  tagText: {
    fontSize: 12,
    color: '#E85D75',
  },
  infoContainer: {
    padding: 20,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  infoLabel: {
    fontSize: 14,
    color: '#666',
  },
  infoValue: {
    fontSize: 14,
    color: '#333',
  },
  voiceContainer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  voiceTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  debugControls: {
    alignItems: 'center',
    gap: 15,
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E85D75',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 30,
    gap: 10,
  },
  stopButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FF4444',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 30,
    gap: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  recordingInfo: {
    width: '100%',
    alignItems: 'center',
    gap: 15,
  },
  fileSizeContainer: {
    backgroundColor: '#f0f0f0',
    padding: 15,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
  },
  fileSizeLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  fileSizeValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#E85D75',
  },
  playbackControls: {
    flexDirection: 'row',
    width: '100%',
    gap: 10,
    justifyContent: 'center',
  },
  replayButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#4CAF50',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 30,
    gap: 10,
  },
  stopPlaybackButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FF6B6B',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 30,
    gap: 10,
  },
  uploadButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2196F3',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 30,
    gap: 10,
  },
  resetButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  resetButtonText: {
    color: '#666',
    fontSize: 14,
  },
  existingVoicesContainer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#eee',
    backgroundColor: '#f8f8f8',
  },
  existingVoicesTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  voiceMemoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 12,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  voiceMemoInfo: {
    flex: 1,
    marginRight: 15,
  },
  voiceMemoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  voiceMemoMeta: {
    fontSize: 13,
    color: '#666',
    marginBottom: 2,
  },
  voiceMemoDate: {
    fontSize: 12,
    color: '#999',
  },
  playButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#E85D75',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playButtonActive: {
    backgroundColor: '#FF6B6B',
  },
  commentsContainer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  commentsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  addCommentContainer: {
    marginBottom: 20,
  },
  commentInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    color: '#333',
    backgroundColor: '#fff',
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: 10,
  },
  addCommentButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E85D75',
    paddingVertical: 12,
    borderRadius: 10,
    gap: 8,
  },
  addCommentButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  commentsList: {
    marginTop: 10,
  },
  commentsCount: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  commentCard: {
    backgroundColor: '#f9f9f9',
    borderRadius: 10,
    padding: 15,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#eee',
  },
  commentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  commentUsername: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  commentDate: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  deleteCommentButton: {
    padding: 5,
  },
  commentText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  noComments: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginTop: 10,
    fontStyle: 'italic',
  },
});
