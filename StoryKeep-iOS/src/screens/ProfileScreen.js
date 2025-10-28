/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system/legacy';
import { authAPI, dashboardAPI } from '../services/api';

export default function ProfileScreen({ navigation }) {
  const [userData, setUserData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [profileImageUri, setProfileImageUri] = useState(null);
  const BASE_URL = 'https://storykeep.calmic.com.my';

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      const [profile, dashStats, token] = await Promise.all([
        authAPI.getProfile(),
        dashboardAPI.getStats(),
        AsyncStorage.getItem('authToken'),
      ]);

      console.log('👤 Profile data:', profile);
      console.log('📸 Profile picture URL:', profile.profile_picture);

      setUserData(profile);
      setStats(dashStats);
      setAuthToken(token);
      
      // Load profile picture with authentication
      if (profile.profile_picture && token) {
        console.log('✅ Profile picture exists, loading...');
        await loadProfileImage(profile.profile_picture, token);
      } else {
        console.log('⚠️ No profile picture or token:', {
          hasPicture: !!profile.profile_picture,
          hasToken: !!token
        });
      }
    } catch (error) {
      console.error('Profile error:', error);
      Alert.alert('Error', 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const loadProfileImage = async (imageUrl, token) => {
    try {
      console.log('🖼️ Loading profile image:', imageUrl);
      console.log('🔑 Token:', token ? 'Present' : 'Missing');
      
      const fileUri = `${FileSystem.cacheDirectory}profile_picture.jpg`;
      const fullUrl = `${BASE_URL}${imageUrl}`;
      
      console.log('📥 Downloading from:', fullUrl);
      
      const downloadResult = await FileSystem.downloadAsync(
        fullUrl,
        fileUri,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      console.log('📦 Download result:', downloadResult);

      if (downloadResult.status === 200) {
        // Force refresh by adding timestamp
        const imageUri = `${downloadResult.uri}?t=${Date.now()}`;
        console.log('✅ Profile image loaded:', imageUri);
        setProfileImageUri(imageUri);
      } else {
        console.error('❌ Download failed with status:', downloadResult.status);
      }
    } catch (error) {
      console.error('❌ Failed to load profile image:', error);
    }
  };

  const handlePickImage = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'We need camera roll permissions to change your profile picture');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        await uploadProfilePicture(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Image picker error:', error);
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const uploadProfilePicture = async (imageUri) => {
    try {
      setUploading(true);

      const response = await authAPI.uploadAvatar(imageUri);

      if (response.success) {
        setUserData({ ...userData, profile_picture: response.avatar_url });
        // Reload the profile image with authentication
        if (authToken) {
          await loadProfileImage(response.avatar_url, authToken);
        }
        Alert.alert('Success', 'Profile picture updated');
      }
    } catch (error) {
      console.error('Upload error:', error);
      Alert.alert('Error', 'Failed to upload profile picture');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#E85D75" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={28} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Profile</Text>
        <TouchableOpacity>
          <Ionicons name="create-outline" size={24} color="#E85D75" />
        </TouchableOpacity>
      </View>

      <View style={styles.profileSection}>
        <TouchableOpacity 
          style={styles.avatarContainer} 
          onPress={handlePickImage}
          disabled={uploading}
        >
          {profileImageUri ? (
            <Image
              source={{ uri: profileImageUri }}
              style={styles.avatarImage}
            />
          ) : (
            <View style={styles.avatar}>
              <Ionicons name="person" size={78} color="#E85D75" />
            </View>
          )}
          <View style={styles.cameraIconContainer}>
            {uploading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Ionicons name="camera" size={20} color="#fff" />
            )}
          </View>
        </TouchableOpacity>
        <Text style={styles.username}>{userData?.username || 'User'}</Text>
        <Text style={styles.email}>{userData?.email || ''}</Text>
        {stats?.subscription_plan && (
          <View style={styles.planBadge}>
            <Ionicons name="shield-checkmark" size={16} color="#E85D75" />
            <Text style={styles.planText}>{stats.subscription_plan} Plan</Text>
          </View>
        )}
      </View>

      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats?.total_photos || 0}</Text>
          <Text style={styles.statLabel}>Photos</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats?.enhanced_photos || 0}</Text>
          <Text style={styles.statLabel}>Colorized</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats?.albums || 0}</Text>
          <Text style={styles.statLabel}>Albums</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>
            {stats?.storage_used ? `${stats.storage_used}MB` : '0MB'}
          </Text>
          <Text style={styles.statLabel}>Storage</Text>
        </View>
      </View>

      <View style={styles.infoSection}>
        <Text style={styles.sectionTitle}>Account Information</Text>
        
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Username</Text>
          <Text style={styles.infoValue}>{userData?.username || 'N/A'}</Text>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Email</Text>
          <Text style={styles.infoValue}>{userData?.email || 'N/A'}</Text>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Member Since</Text>
          <Text style={styles.infoValue}>
            {userData?.created_at
              ? new Date(userData.created_at).toLocaleDateString()
              : 'N/A'}
          </Text>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Account Type</Text>
          <Text style={styles.infoValue}>{userData?.role || 'User'}</Text>
        </View>
      </View>

      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionButton}>
          <Ionicons name="create" size={24} color="#E85D75" />
          <Text style={styles.actionText}>Edit Profile</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButton}>
          <Ionicons name="lock-closed" size={24} color="#E85D75" />
          <Text style={styles.actionText}>Change Password</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButton}>
          <Ionicons name="shield-checkmark" size={24} color="#E85D75" />
          <Text style={styles.actionText}>Manage Subscription</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
  profileSection: {
    alignItems: 'center',
    padding: 30,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  avatarContainer: {
    position: 'relative',
    marginBottom: 15,
  },
  avatar: {
    width: 156,
    height: 156,
    borderRadius: 78,
    backgroundColor: '#FFF0F3',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarImage: {
    width: 156,
    height: 156,
    borderRadius: 78,
    backgroundColor: '#FFF0F3',
  },
  cameraIconContainer: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E85D75',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#fff',
  },
  username: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  email: {
    fontSize: 16,
    color: '#666',
    marginBottom: 15,
  },
  planBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF0F3',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
  },
  planText: {
    fontSize: 14,
    color: '#E85D75',
    fontWeight: 'bold',
    marginLeft: 5,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  statCard: {
    width: '50%',
    alignItems: 'center',
    paddingVertical: 15,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  infoSection: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  infoLabel: {
    fontSize: 16,
    color: '#666',
  },
  infoValue: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  actions: {
    padding: 20,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#f8f8f8',
    borderRadius: 10,
    marginBottom: 10,
  },
  actionText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 15,
  },
});
