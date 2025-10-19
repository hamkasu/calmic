import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import * as FileSystem from 'expo-file-system/legacy';
import { dashboardAPI, photoAPI, authAPI } from '../services/api';
import api from '../services/api';
import { useLoading } from '../contexts/LoadingContext';

export default function DashboardScreen({ navigation }) {
  const [stats, setStats] = useState(null);
  const [recentPhotos, setRecentPhotos] = useState([]);
  const [userData, setUserData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [profileImageUri, setProfileImageUri] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const { startLoading, stopLoading } = useLoading();
  const BASE_URL = 'https://web-production-535bd.up.railway.app';

  useEffect(() => {
    loadDashboardData();
  }, []);

  // ALWAYS reload profile picture when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      console.log('📱 Dashboard focused - reloading profile picture...');
      refreshProfilePicture();
    }, [])
  );

  const refreshProfilePicture = async () => {
    try {
      setProfileLoading(true);
      
      // ALWAYS fetch fresh profile data from database
      const profileData = await authAPI.getProfile();
      const token = await AsyncStorage.getItem('authToken');
      
      console.log('👤 Fresh profile data from database:', {
        username: profileData.username,
        profile_picture: profileData.profile_picture,
        hasToken: !!token
      });
      
      setUserData(profileData);
      
      // Clear any existing profile image first
      setProfileImageUri(null);
      
      // Download fresh profile picture from server
      if (profileData.profile_picture && token) {
        console.log('📥 Downloading fresh profile picture from database...');
        await loadProfileImage(profileData.profile_picture, token);
      } else {
        console.log('⚠️ No profile picture in database or no token');
      }
    } catch (error) {
      console.error('❌ Error refreshing profile:', error);
    } finally {
      setProfileLoading(false);
    }
  };

  const loadProfileImage = async (imageUrl, token) => {
    try {
      // Use unique filename with timestamp to avoid cache
      const timestamp = Date.now();
      const fileUri = `${FileSystem.cacheDirectory}dashboard_profile_${timestamp}.jpg`;
      const fullUrl = `${BASE_URL}${imageUrl}`;
      
      console.log('🖼️ Downloading profile image from:', fullUrl);
      console.log('💾 Saving to cache:', fileUri);
      
      const downloadResult = await FileSystem.downloadAsync(
        fullUrl,
        fileUri,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      console.log('📦 Download result:', {
        status: downloadResult.status,
        uri: downloadResult.uri
      });

      if (downloadResult.status === 200) {
        // Set image URI without timestamp (file is already unique)
        setProfileImageUri(downloadResult.uri);
        console.log('✅ Profile image loaded successfully');
      } else {
        console.error('❌ Download failed with status:', downloadResult.status);
        setProfileImageUri(null);
      }
    } catch (error) {
      console.error('❌ Failed to load profile image:', error);
      setProfileImageUri(null);
    }
  };

  const loadDashboardData = async () => {
    const loadingId = startLoading('Loading dashboard...');
    try {
      const [statsData, photosData, profileData, token] = await Promise.all([
        dashboardAPI.getStats(),
        photoAPI.getPhotos('all'),
        authAPI.getProfile(),
        AsyncStorage.getItem('authToken'),
      ]);

      console.log('📊 Dashboard data loaded:', {
        total_photos: statsData.total_photos,
        username: profileData.username,
        profile_picture: profileData.profile_picture
      });

      setStats(statsData);
      setRecentPhotos(photosData.photos?.slice(0, 6) || []);
      setUserData(profileData);
      setAuthToken(token);
      
      // Load profile picture from fresh database data
      if (profileData.profile_picture && token) {
        console.log('📥 Loading profile picture from database...');
        await loadProfileImage(profileData.profile_picture, token);
      } else {
        console.log('⚠️ No profile picture or token');
      }
    } catch (error) {
      console.error('❌ Dashboard error:', error);
      Alert.alert('Error', 'Failed to load dashboard data');
    } finally {
      stopLoading(loadingId);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    // Clear existing image before refresh
    setProfileImageUri(null);
    loadDashboardData();
  };

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            try {
              // Clear all storage and biometric credentials
              await AsyncStorage.clear();
              await SecureStore.deleteItemAsync('userEmail').catch(() => {});
              await SecureStore.deleteItemAsync('userPassword').catch(() => {});
              
              // App.js will automatically detect token removal and navigate to Login
            } catch (error) {
              console.error('Logout error:', error);
              Alert.alert('Error', 'Failed to logout. Please try again.');
            }
          },
        },
      ]
    );
  };

  if (!stats || !userData) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#E85D75" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.username}>{userData?.username || 'User'}</Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity
            style={styles.profileButton}
            onPress={() => navigation.navigate('Profile')}
          >
            {profileLoading ? (
              <ActivityIndicator size="small" color="#E85D75" />
            ) : profileImageUri ? (
              <Image
                source={{ uri: profileImageUri }}
                style={styles.profileImage}
              />
            ) : (
              <Ionicons name="person-circle" size={62} color="#E85D75" />
            )}
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.logoutButton}
            onPress={handleLogout}
          >
            <Ionicons name="log-out-outline" size={28} color="#E85D75" />
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Ionicons name="images" size={42} color="#E85D75" />
          <Text style={styles.statNumber}>{stats?.total_photos || 0}</Text>
          <Text style={styles.statLabel}>Total Photos</Text>
        </View>

        <View style={styles.statCard}>
          <Ionicons name="sparkles" size={42} color="#E85D75" />
          <Text style={styles.statNumber}>{stats?.enhanced_photos || 0}</Text>
          <Text style={styles.statLabel}>Colorized</Text>
        </View>

        <View style={[styles.statCard, styles.highlightedStat]}>
          <Ionicons name="people" size={42} color="#E85D75" />
          <Text style={styles.statNumber}>{stats?.vaults || 0}</Text>
          <Text style={styles.statLabel}>Vaults</Text>
        </View>

        <View style={styles.statCard}>
          <Ionicons name="cloud" size={42} color="#E85D75" />
          <Text style={styles.statNumber}>
            {stats?.storage_used ? `${stats.storage_used}MB` : '0MB'}
          </Text>
          <Text style={styles.statLabel}>Storage</Text>
        </View>
      </View>

      {stats?.subscription_plan && (
        <View style={styles.subscriptionCard}>
          <View style={styles.subscriptionHeader}>
            <Ionicons name="shield-checkmark" size={24} color="#E85D75" />
            <Text style={styles.subscriptionText}>
              {stats.subscription_plan} Plan
            </Text>
          </View>
          
          {/* Storage Quota */}
          <View style={styles.storageQuota}>
            <View style={styles.storageHeader}>
              <Text style={styles.storageLabel}>Storage</Text>
              <Text style={styles.storageAmount}>
                {stats.storage_limit_mb === -1 
                  ? `${stats.storage_used.toFixed(1)} MB used (Unlimited)` 
                  : stats.storage_limit_mb >= 1024
                    ? `${stats.storage_used.toFixed(1)} MB used of ${Math.round(stats.storage_limit_mb / 1024)} GB allocated`
                    : `${stats.storage_used.toFixed(1)} MB used of ${stats.storage_limit_mb} MB allocated`
                }
              </Text>
            </View>
            
            {stats.storage_limit_mb !== -1 && (
              <>
                <View style={styles.progressBarContainer}>
                  <View 
                    style={[
                      styles.progressBar, 
                      { 
                        width: `${Math.min(stats.storage_usage_percent, 100)}%`,
                        backgroundColor: 
                          stats.storage_usage_percent >= 90 ? '#F44336' :
                          stats.storage_usage_percent >= 70 ? '#FFC107' :
                          '#4CAF50'
                      }
                    ]} 
                  />
                </View>
                <Text style={[
                  styles.storagePercent,
                  { color: 
                    stats.storage_usage_percent >= 90 ? '#F44336' :
                    stats.storage_usage_percent >= 70 ? '#FFC107' :
                    '#4CAF50'
                  }
                ]}>
                  {stats.storage_usage_percent.toFixed(1)}% used
                </Text>
              </>
            )}
          </View>
        </View>
      )}

      <View style={styles.quickActions}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('Camera')}
        >
          <Ionicons name="camera" size={24} color="#fff" />
          <Text style={styles.actionButtonText}>Digitize Photos</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.actionButtonSecondary]}
          onPress={() => navigation.navigate('Gallery')}
        >
          <Ionicons name="images" size={24} color="#E85D75" />
          <Text style={[styles.actionButtonText, styles.actionButtonTextSecondary]}>
            View Gallery
          </Text>
        </TouchableOpacity>
      </View>

      {/* DIAGNOSTIC SECTION */}
      {stats?.recent_photo && (
        <View style={styles.diagnosticSection}>
          <Text style={styles.sectionTitle}>🔍 Diagnostic Info</Text>
          <Text style={styles.diagnosticText}>Debug Photos Count: {stats?.debug_photos_count || 0}</Text>
          <Text style={styles.diagnosticText}>All Photos Array: {stats?.all_photos?.length || 0}</Text>
          <Text style={styles.diagnosticText}>Recent Photo ID: {stats.recent_photo.id}</Text>
          <Text style={styles.diagnosticText}>Filename: {stats.recent_photo.filename}</Text>
          <Text style={styles.diagnosticText}>URL: {stats.recent_photo.original_url || 'NULL'}</Text>
          <Text style={styles.diagnosticText}>Auth Token: {authToken ? 'Present' : 'Missing'}</Text>
          {stats.recent_photo.original_url && authToken && (
            <>
              <Text style={styles.diagnosticText}>Loading from: https://web-production-535bd.up.railway.app{stats.recent_photo.original_url}</Text>
              <Image
                source={{ 
                  uri: `https://web-production-535bd.up.railway.app${stats.recent_photo.original_url}`,
                  headers: {
                    Authorization: `Bearer ${authToken}`
                  }
                }}
                style={styles.diagnosticImage}
                resizeMode="contain"
                onError={(error) => console.error('📷 Image load error:', error.nativeEvent.error)}
                onLoad={() => console.log('✅ Image loaded successfully')}
              />
            </>
          )}
          {stats?.all_photos && stats.all_photos.length > 0 && (
            <View style={{marginTop: 15}}>
              <Text style={styles.diagnosticText}>First Photo from all_photos Array:</Text>
              <Text style={styles.diagnosticText}>- ID: {stats.all_photos[0].id}</Text>
              <Text style={styles.diagnosticText}>- URL: {stats.all_photos[0].url || 'NULL'}</Text>
              <Text style={styles.diagnosticText}>- Filename: {stats.all_photos[0].filename}</Text>
            </View>
          )}
        </View>
      )}

      {recentPhotos.length > 0 && (
        <View style={styles.recentSection}>
          <Text style={styles.sectionTitle}>Recent Photos</Text>
          <View style={styles.photoGrid}>
            {recentPhotos.map((photo) => (
              <TouchableOpacity
                key={photo.id}
                style={styles.photoCard}
                onPress={() => navigation.navigate('PhotoDetail', { photo })}
              >
                <Image
                  source={{ uri: photo.thumbnail_url || photo.url }}
                  style={styles.photoThumbnail}
                />
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
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
    backgroundColor: '#f8f8f8',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  greeting: {
    fontSize: 16,
    color: '#666',
  },
  username: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  profileButton: {
    marginRight: 10,
    width: 62,
    height: 62,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileImage: {
    width: 62,
    height: 62,
    borderRadius: 31,
    backgroundColor: '#FFF0F3',
  },
  logoutButton: {
    padding: 5,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 20,
  },
  statCard: {
    alignItems: 'center',
  },
  highlightedStat: {
    borderWidth: 3,
    borderColor: '#00FF9D',
    borderRadius: 20,
    padding: 10,
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  subscriptionCard: {
    backgroundColor: '#FFF0F3',
    padding: 15,
    marginHorizontal: 20,
    marginBottom: 20,
    borderRadius: 10,
  },
  subscriptionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  subscriptionText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#E85D75',
    marginLeft: 10,
  },
  storageQuota: {
    marginTop: 5,
  },
  storageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  storageLabel: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  storageAmount: {
    fontSize: 14,
    color: '#333',
    fontWeight: 'bold',
  },
  progressBarContainer: {
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 6,
  },
  progressBar: {
    height: '100%',
    borderRadius: 4,
  },
  storagePercent: {
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'right',
  },
  quickActions: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  actionButton: {
    backgroundColor: '#E85D75',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
  },
  actionButtonSecondary: {
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#E85D75',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  actionButtonTextSecondary: {
    color: '#E85D75',
  },
  diagnosticSection: {
    padding: 20,
    backgroundColor: '#FFF9E6',
    margin: 15,
    borderRadius: 10,
  },
  diagnosticText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    fontFamily: 'monospace',
  },
  diagnosticImage: {
    width: '100%',
    height: 200,
    marginTop: 10,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
  },
  recentSection: {
    padding: 20,
  },
  photoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  photoCard: {
    width: '48%',
    aspectRatio: 1,
    marginBottom: 10,
    borderRadius: 10,
    overflow: 'hidden',
  },
  photoThumbnail: {
    width: '100%',
    height: '100%',
  },
});
