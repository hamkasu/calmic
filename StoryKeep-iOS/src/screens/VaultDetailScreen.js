/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  ScrollView,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  TouchableWithoutFeedback,
  Dimensions,
} from 'react-native';
import { Image } from 'expo-image';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import { vaultAPI, photoAPI, authAPI } from '../services/api';

const { width } = Dimensions.get('window');
const COLUMN_COUNT = 3;
const ITEM_WIDTH = (width - 6) / COLUMN_COUNT; // 2px gap between items
const BASE_URL = 'https://storykeep.calmic.com.my';

export default function VaultDetailScreen({ route, navigation }) {
  const { vaultId } = route.params;
  const [vault, setVault] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [activeTab, setActiveTab] = useState('photos'); // 'photos' or 'members'
  
  // Photo picker states
  const [showPhotoPicker, setShowPhotoPicker] = useState(false);
  const [userPhotos, setUserPhotos] = useState([]);
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [selectedGalleryPhotos, setSelectedGalleryPhotos] = useState([]);
  const [photoCaption, setPhotoCaption] = useState('');
  const [adding, setAdding] = useState(false);
  
  // Invite member states
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviting, setInviting] = useState(false);
  
  // Multiple selection and delete states
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedPhotos, setSelectedPhotos] = useState([]);
  const [deleting, setDeleting] = useState(false);
  
  // Camera library upload states
  const [uploadingFromLibrary, setUploadingFromLibrary] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
  
  // Edit vault states
  const [showEditModal, setShowEditModal] = useState(false);
  const [editVaultName, setEditVaultName] = useState('');
  const [editVaultDescription, setEditVaultDescription] = useState('');
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    loadAuthToken();
  }, []);

  useEffect(() => {
    if (authToken) {
      loadVaultDetails();
    }
  }, [authToken]);

  const loadAuthToken = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      setAuthToken(token);
      
      // Fetch user profile to get user ID
      if (token) {
        try {
          const profileResponse = await authAPI.getProfile();
          if (profileResponse && profileResponse.id) {
            setCurrentUserId(profileResponse.id);
            // Also store it for future use
            await AsyncStorage.setItem('userId', profileResponse.id.toString());
          }
        } catch (profileError) {
          console.error('Failed to load user profile:', profileError);
          // Try to fall back to stored userId if profile fetch fails
          const storedUserId = await AsyncStorage.getItem('userId');
          if (storedUserId) {
            setCurrentUserId(parseInt(storedUserId));
          }
        }
      }
    } catch (error) {
      console.error('Failed to load auth token:', error);
    }
  };

  const loadVaultDetails = async () => {
    try {
      const response = await vaultAPI.getVaultDetail(vaultId);
      
      if (response.vault) {
        setVault(response.vault);
        setPhotos(response.photos || []);
        setMembers(response.members || []);
      } else {
        Alert.alert('Error', response.error || 'Failed to load vault details');
      }
    } catch (error) {
      console.error('Vault detail error:', error);
      Alert.alert('Error', error.response?.data?.error || 'Failed to load vault details');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadVaultDetails();
  };

  const loadUserPhotos = async () => {
    try {
      // Load user's photos from dashboard (same as gallery)
      const response = await fetch(`${BASE_URL}/api/dashboard`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      const data = await response.json();
      
      if (data.all_photos && data.all_photos.length > 0) {
        setUserPhotos(data.all_photos);
      } else {
        setUserPhotos([]);
        Alert.alert('No Photos', 'You need to add photos to your gallery first');
      }
    } catch (error) {
      console.error('Load photos error:', error);
      Alert.alert('Error', 'Failed to load your photos');
    }
  };

  const openPhotoPicker = () => {
    loadUserPhotos();
    setSelectedPhoto(null);
    setSelectedGalleryPhotos([]);
    setPhotoCaption('');
    setShowPhotoPicker(true);
  };

  const toggleGalleryPhotoSelection = (photo) => {
    const isSelected = selectedGalleryPhotos.some(p => p.id === photo.id);
    if (isSelected) {
      setSelectedGalleryPhotos(selectedGalleryPhotos.filter(p => p.id !== photo.id));
    } else {
      setSelectedGalleryPhotos([...selectedGalleryPhotos, photo]);
    }
  };

  const addPhotoToVault = async () => {
    const photosToAdd = selectedGalleryPhotos.length > 0 ? selectedGalleryPhotos : (selectedPhoto ? [selectedPhoto] : []);
    
    if (photosToAdd.length === 0) {
      Alert.alert('Select Photo', 'Please select at least one photo to add');
      return;
    }

    setAdding(true);
    setUploadProgress({ current: 0, total: photosToAdd.length });
    
    try {
      let successCount = 0;
      let failCount = 0;

      for (let i = 0; i < photosToAdd.length; i++) {
        try {
          setUploadProgress({ current: i + 1, total: photosToAdd.length });
          await vaultAPI.addPhotoToVault(vaultId, photosToAdd[i].id, photoCaption);
          successCount++;
        } catch (photoError) {
          console.error(`Error adding photo ${i + 1}:`, photoError);
          failCount++;
        }
      }

      loadVaultDetails(); // Refresh vault
      
      if (failCount === 0) {
        Alert.alert('Success', `Successfully added ${successCount} photo(s) to vault`);
      } else {
        Alert.alert('Partial Success', `Added ${successCount} photo(s). ${failCount} failed.`);
      }
      
      setShowPhotoPicker(false);
      setSelectedPhoto(null);
      setSelectedGalleryPhotos([]);
      setPhotoCaption('');
    } catch (error) {
      console.error('Add photo error:', error);
      Alert.alert('Error', error.response?.data?.error || 'Failed to add photos to vault');
    } finally {
      setAdding(false);
      setUploadProgress({ current: 0, total: 0 });
    }
  };

  const openInviteModal = () => {
    setInviteEmail('');
    setInviteRole('member');
    setShowInviteModal(true);
  };

  const inviteMemberToVault = async () => {
    if (!inviteEmail.trim()) {
      Alert.alert('Error', 'Please enter an email address');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(inviteEmail.trim())) {
      Alert.alert('Error', 'Please enter a valid email address');
      return;
    }

    setInviting(true);
    try {
      const response = await vaultAPI.inviteMember(vaultId, inviteEmail.trim(), inviteRole);
      
      Alert.alert('Success', `Invitation sent to ${inviteEmail}`);
      setShowInviteModal(false);
      setInviteEmail('');
      setInviteRole('member');
      loadVaultDetails(); // Refresh vault to see pending invitations
    } catch (error) {
      console.error('Invite member error:', error);
      Alert.alert('Error', error.response?.data?.error || 'Failed to send invitation');
    } finally {
      setInviting(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'No date';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
    return `${Math.floor(diffDays / 365)}y ago`;
  };

  const toggleSelectionMode = () => {
    setSelectionMode(!selectionMode);
    setSelectedPhotos([]);
  };

  const togglePhotoSelection = (photoId) => {
    if (selectedPhotos.includes(photoId)) {
      setSelectedPhotos(selectedPhotos.filter(id => id !== photoId));
    } else {
      setSelectedPhotos([...selectedPhotos, photoId]);
    }
  };

  const deleteSelectedPhotos = async () => {
    if (selectedPhotos.length === 0) {
      Alert.alert('No Photos Selected', 'Please select photos to delete');
      return;
    }

    Alert.alert(
      'Delete Photos',
      `Are you sure you want to delete ${selectedPhotos.length} photo(s) from this vault?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            setDeleting(true);
            try {
              // Use bulk delete API for better performance
              const result = await vaultAPI.removePhotosFromVaultBulk(vaultId, selectedPhotos);
              
              if (result.success) {
                const message = result.failed_count > 0 
                  ? `Removed ${result.success_count} photo(s). ${result.failed_count} failed.`
                  : `Removed ${result.success_count} photo(s) from vault`;
                
                Alert.alert('Success', message);
                setSelectionMode(false);
                setSelectedPhotos([]);
                loadVaultDetails();
              } else {
                Alert.alert('Error', result.error || 'Failed to delete photos');
              }
            } catch (error) {
              console.error('Delete photos error:', error);
              const errorMsg = error.response?.data?.error || 'Failed to delete photos';
              Alert.alert('Error', errorMsg);
            } finally {
              setDeleting(false);
            }
          },
        },
      ]
    );
  };

  const uploadFromCameraLibrary = async () => {
    try {
      const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
      
      if (!permissionResult.granted) {
        Alert.alert('Permission Required', 'Please allow access to your photo library');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        allowsMultipleSelection: true,
        quality: 1.0,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setUploadingFromLibrary(true);
        const totalPhotos = result.assets.length;
        setUploadProgress({ current: 0, total: totalPhotos });
        
        let successCount = 0;
        let failCount = 0;

        // Process each selected photo
        for (let i = 0; i < result.assets.length; i++) {
          try {
            setUploadProgress({ current: i + 1, total: totalPhotos });

            // Always convert to JPEG using ImageManipulator (same as working gallery/camera pattern)
            const enhancedPhoto = await ImageManipulator.manipulateAsync(
              result.assets[i].uri,
              [{ resize: { width: 1920 } }],
              { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG }
            );
            
            // Build FormData using 'image' field name (same as working uploads)
            const formData = new FormData();
            formData.append('image', {
              uri: enhancedPhoto.uri,
              type: 'image/jpeg',
              name: `vault_upload_${Date.now()}_${i}.jpg`,
            });

            // Upload photo using detectAndExtract (same as working Digitizer)
            const data = await photoAPI.detectAndExtract(formData);

            if (data.success) {
              // Handle response - detectAndExtract returns either extracted_photos array or single photo object
              let photoId = null;
              
              if (data.extracted_photos && data.extracted_photos.length > 0) {
                // Multiple photos detected - use first extracted photo
                photoId = data.extracted_photos[0].id;
              } else if (data.photo && data.photo.id) {
                // Single photo, no extraction needed
                photoId = data.photo.id;
              }
              
              if (photoId) {
                // Add the uploaded photo to vault
                await vaultAPI.addPhotoToVault(vaultId, photoId, '');
                successCount++;
              } else {
                failCount++;
              }
            } else {
              failCount++;
            }
          } catch (photoError) {
            console.error(`Error processing photo ${i + 1}:`, photoError);
            failCount++;
          }
        }

        // Show summary
        loadVaultDetails();
        if (failCount === 0) {
          Alert.alert('Success', `Successfully added ${successCount} photo(s) to vault`);
        } else {
          Alert.alert('Partial Success', `Added ${successCount} photo(s). ${failCount} failed.`);
        }
      }
    } catch (error) {
      console.error('Camera library upload error:', error);
      Alert.alert('Error', error.response?.data?.error || 'Failed to upload photos from library');
    } finally {
      setUploadingFromLibrary(false);
      setUploadProgress({ current: 0, total: 0 });
    }
  };

  const openEditModal = () => {
    setEditVaultName(vault.name);
    setEditVaultDescription(vault.description || '');
    setShowEditModal(true);
  };

  const handleEditVault = async () => {
    if (!editVaultName.trim()) {
      Alert.alert('Error', 'Vault name cannot be empty');
      return;
    }

    setEditing(true);
    try {
      await vaultAPI.editVault(vaultId, editVaultName.trim(), editVaultDescription.trim());
      Alert.alert('Success', 'Vault updated successfully');
      setShowEditModal(false);
      loadVaultDetails();
    } catch (error) {
      console.error('Edit vault error:', error);
      Alert.alert('Error', error.response?.data?.error || 'Failed to update vault');
    } finally {
      setEditing(false);
    }
  };

  const handleDeleteVault = () => {
    Alert.alert(
      'Delete Vault',
      'Are you sure you want to delete this vault? This action cannot be undone. All photos and members will be removed.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await vaultAPI.deleteVault(vaultId);
              Alert.alert('Success', 'Vault deleted successfully');
              navigation.goBack();
            } catch (error) {
              console.error('Delete vault error:', error);
              Alert.alert('Error', error.response?.data?.error || 'Failed to delete vault');
            }
          },
        },
      ]
    );
  };

  const handleRemoveMember = (member) => {
    Alert.alert(
      'Remove Member',
      `Remove ${member.username || member.email} from this vault?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await vaultAPI.removeMember(vaultId, member.id);
              Alert.alert('Success', 'Member removed successfully');
              loadVaultDetails();
            } catch (error) {
              console.error('Remove member error:', error);
              Alert.alert('Error', error.response?.data?.error || 'Failed to remove member');
            }
          },
        },
      ]
    );
  };

  const handleChangeMemberRole = (member) => {
    const newRole = member.role === 'admin' ? 'member' : 'admin';
    Alert.alert(
      'Change Role',
      `Change ${member.username || member.email} to ${newRole}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Change',
          onPress: async () => {
            try {
              await vaultAPI.changeMemberRole(vaultId, member.id, newRole);
              Alert.alert('Success', `Member role changed to ${newRole}`);
              loadVaultDetails();
            } catch (error) {
              console.error('Change role error:', error);
              Alert.alert('Error', error.response?.data?.error || 'Failed to change member role');
            }
          },
        },
      ]
    );
  };

  const renderPhoto = ({ item }) => {
    const isSelected = selectedPhotos.includes(item.id);
    const isOwned = currentUserId && item.shared_by_user_id === currentUserId;
    const isAdmin = vault?.is_creator || vault?.member_role === 'admin';
    
    // Use grid thumbnail for faster loading (200x200), fallback to regular thumbnail
    const imageUrl = item.grid_thumbnail_url || item.thumbnail_url || item.url || item.original_url;
    
    // Construct full URL if it's a relative path
    const fullImageUrl = imageUrl?.startsWith('http') 
      ? imageUrl 
      : imageUrl?.startsWith('/') 
        ? `${BASE_URL}${imageUrl}`
        : imageUrl;
    
    return (
      <TouchableOpacity
        style={styles.photoCard}
        onPress={() => {
          if (selectionMode) {
            togglePhotoSelection(item.id);
          } else {
            navigation.navigate('PhotoDetail', { photo: item });
          }
        }}
        onLongPress={() => {
          if (!selectionMode) {
            setSelectionMode(true);
            setSelectedPhotos([item.id]);
          }
        }}
      >
        {fullImageUrl && authToken ? (
          <Image
            source={{ 
              uri: fullImageUrl,
              headers: {
                Authorization: `Bearer ${authToken}`
              }
            }}
            style={styles.photoImage}
            contentFit="cover"
            placeholder={item.blurhash}
            transition={200}
            cachePolicy="memory-disk"
            priority="high"
          />
        ) : (
          <View style={styles.photoImagePlaceholder}>
            <ActivityIndicator size="small" color="#E85D75" />
          </View>
        )}
        
        {/* Bottom gradient overlay */}
        <View style={styles.bottomOverlay}>
          <Text style={styles.photoDate} numberOfLines={1}>
            {item.caption || formatDate(item.created_at)}
          </Text>
          {item.shared_by_username && (
            <Text style={styles.photoSharedBy} numberOfLines={1}>
              Shared by {item.shared_by_username}
            </Text>
          )}
        </View>

        {/* Owner badge - shows if photo belongs to current user */}
        {isOwned && !selectionMode && (
          <View style={styles.ownerBadge}>
            <Ionicons name="person" size={10} color="#fff" />
          </View>
        )}

        {/* Colorized badge */}
        {item.edited_url && (
          <View style={styles.enhancedBadge}>
            <Ionicons name="sparkles" size={14} color="#fff" />
          </View>
        )}

        {/* Voice memo badge */}
        {item.voice_memos && item.voice_memos.length > 0 && (
          <View style={styles.voiceMemoBadge}>
            <Ionicons name="mic" size={12} color="#fff" />
            <Text style={styles.badgeCount}>{item.voice_memos.length}</Text>
          </View>
        )}

        {/* Comment badge */}
        {item.comments && item.comments.length > 0 && (
          <View style={styles.commentBadge}>
            <Ionicons name="chatbox" size={12} color="#fff" />
            <Text style={styles.badgeCount}>{item.comments.length}</Text>
          </View>
        )}

        {/* Selection checkbox */}
        {selectionMode && (
          <View style={styles.selectionCheckbox}>
            <Ionicons 
              name={isSelected ? "checkmark-circle" : "ellipse-outline"} 
              size={28} 
              color={isSelected ? "#E85D75" : "#fff"} 
            />
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderMember = ({ item }) => {
    const isOwner = vault?.is_creator;
    const isAdmin = vault?.member_role === 'admin';
    const canManage = isOwner || isAdmin;
    const isCurrentMemberCreator = item.is_creator === true;
    
    return (
      <View style={styles.memberCard}>
        <View style={styles.memberAvatar}>
          <Ionicons name="person" size={24} color="#E85D75" />
        </View>
        <View style={styles.memberInfo}>
          <Text style={styles.memberName}>{item.username || item.email}</Text>
          <View style={styles.memberRoleBadge}>
            <Ionicons 
              name={item.role === 'admin' || isCurrentMemberCreator ? 'shield' : 'person'}
              size={12}
              color={item.role === 'admin' || isCurrentMemberCreator ? '#E85D75' : '#666'}
              style={{ marginRight: 4 }}
            />
            <Text style={[styles.memberRole, (item.role === 'admin' || isCurrentMemberCreator) && styles.memberRoleAdmin]}>
              {isCurrentMemberCreator ? 'Creator' : item.role}
            </Text>
          </View>
        </View>
        
        {canManage && !isCurrentMemberCreator && (
          <View style={styles.memberActions}>
            <TouchableOpacity
              style={styles.memberActionButton}
              onPress={() => handleChangeMemberRole(item)}
            >
              <Ionicons 
                name={item.role === 'admin' ? 'person-remove' : 'person-add'} 
                size={20} 
                color="#666" 
              />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.memberActionButton}
              onPress={() => handleRemoveMember(item)}
            >
              <Ionicons name="trash-outline" size={20} color="#E85D75" />
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#E85D75" />
      </View>
    );
  }

  if (!vault) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={80} color="#ccc" />
        <Text style={styles.errorText}>Failed to load vault</Text>
        <TouchableOpacity 
          style={styles.retryButton}
          onPress={loadVaultDetails}
        >
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        {selectionMode ? (
          <>
            <TouchableOpacity onPress={toggleSelectionMode}>
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.headerTitle}>
              {selectedPhotos.length} Selected
            </Text>
            <TouchableOpacity 
              onPress={deleteSelectedPhotos}
              disabled={deleting || selectedPhotos.length === 0}
            >
              {deleting ? (
                <ActivityIndicator color="#E85D75" size="small" />
              ) : (
                <Ionicons 
                  name="trash" 
                  size={28} 
                  color={selectedPhotos.length > 0 ? "#E85D75" : "#666"} 
                />
              )}
            </TouchableOpacity>
          </>
        ) : (
          <>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name="arrow-back" size={28} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.headerTitle} numberOfLines={1}>{vault.name}</Text>
            <View style={styles.headerActions}>
              {(vault.is_creator || vault.member_role === 'admin') && (
                <TouchableOpacity 
                  style={styles.headerButton}
                  onPress={openEditModal}
                >
                  <Ionicons name="create-outline" size={24} color="#fff" />
                </TouchableOpacity>
              )}
              {vault.is_creator && (
                <TouchableOpacity 
                  style={styles.headerButton}
                  onPress={handleDeleteVault}
                >
                  <Ionicons name="trash-outline" size={24} color="#fff" />
                </TouchableOpacity>
              )}
              <TouchableOpacity onPress={toggleSelectionMode}>
                <Ionicons name="checkmark-circle-outline" size={28} color="#fff" />
              </TouchableOpacity>
            </View>
          </>
        )}
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'photos' && styles.tabActive]}
          onPress={() => setActiveTab('photos')}
        >
          <Text style={[styles.tabText, activeTab === 'photos' && styles.tabTextActive]}>
            Photos
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'members' && styles.tabActive]}
          onPress={() => setActiveTab('members')}
        >
          <Text style={[styles.tabText, activeTab === 'members' && styles.tabTextActive]}>
            Members
          </Text>
        </TouchableOpacity>
      </View>

      {activeTab === 'members' ? (
        <ScrollView
          style={styles.membersContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          <View style={styles.membersList}>
            <View style={styles.membersHeader}>
              <Text style={styles.membersTitle}>Members</Text>
              <TouchableOpacity onPress={openInviteModal}>
                <Ionicons name="person-add" size={24} color="#E85D75" />
              </TouchableOpacity>
            </View>
            
            {members.length === 0 ? (
              <View style={styles.emptyMembers}>
                <Ionicons name="people-outline" size={60} color="#666" />
                <Text style={styles.emptyText}>No members yet</Text>
              </View>
            ) : (
              members.map((member) => (
                <View key={member.id}>{renderMember({ item: member })}</View>
              ))
            )}
          </View>
        </ScrollView>
      ) : (
        <View style={styles.photosContainer}>
          {photos.length === 0 ? (
            <View style={styles.emptyPhotos}>
              <Ionicons name="images-outline" size={80} color="#666" />
              <Text style={styles.emptyText}>No photos yet</Text>
              <Text style={styles.emptySubtext}>
                Add photos to share with family members
              </Text>
            </View>
          ) : (
            <FlatList
              data={photos}
              renderItem={renderPhoto}
              keyExtractor={(item) => item.id.toString()}
              numColumns={COLUMN_COUNT}
              contentContainerStyle={styles.photoList}
              showsVerticalScrollIndicator={false}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              initialNumToRender={45}
              maxToRenderPerBatch={20}
              windowSize={3}
              removeClippedSubviews={true}
              updateCellsBatchingPeriod={50}
            />
          )}
          
          {/* Upload Progress Indicator */}
          {uploadingFromLibrary && uploadProgress.total > 0 && (
            <View style={styles.uploadProgressOverlay}>
              <View style={styles.uploadProgressCard}>
                <ActivityIndicator size="large" color="#E85D75" />
                <Text style={styles.uploadProgressText}>
                  Uploading {uploadProgress.current} of {uploadProgress.total} photos...
                </Text>
                <View style={styles.uploadProgressBarContainer}>
                  <View 
                    style={[
                      styles.uploadProgressBarFill, 
                      { width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }
                    ]} 
                  />
                </View>
              </View>
            </View>
          )}
          
          {/* Floating Add Buttons with Labels */}
          <View style={styles.floatingButtonsContainer}>
            <View style={styles.floatingButtonWrapper}>
              <TouchableOpacity
                style={styles.floatingAddButton}
                onPress={openPhotoPicker}
              >
                <Ionicons name="images" size={24} color="#fff" />
              </TouchableOpacity>
              <Text style={styles.floatingButtonLabel}>My Gallery</Text>
            </View>
            
            <View style={styles.floatingButtonWrapper}>
              <TouchableOpacity
                style={[styles.floatingAddButton, styles.floatingLibraryButton]}
                onPress={uploadFromCameraLibrary}
                disabled={uploadingFromLibrary}
              >
                {uploadingFromLibrary ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Ionicons name="image" size={24} color="#fff" />
                )}
              </TouchableOpacity>
              <Text style={styles.floatingButtonLabel}>Camera Roll</Text>
            </View>
          </View>
        </View>
      )}

      {/* Photo Picker Modal */}
      <Modal
        visible={showPhotoPicker}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowPhotoPicker(false)}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
            <View style={styles.modalContainer}>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Select Photos</Text>
                  <TouchableOpacity onPress={() => setShowPhotoPicker(false)}>
                    <Ionicons name="close" size={28} color="#333" />
                  </TouchableOpacity>
                </View>
                
                {selectedGalleryPhotos.length > 0 && (
                  <View style={styles.selectionInfo}>
                    <Text style={styles.selectionInfoText}>
                      {selectedGalleryPhotos.length} photo(s) selected
                    </Text>
                    <TouchableOpacity onPress={() => setSelectedGalleryPhotos([])}>
                      <Text style={styles.clearSelectionText}>Clear</Text>
                    </TouchableOpacity>
                  </View>
                )}

                <ScrollView style={styles.photoPickerScroll}>
                  <View style={styles.photoPickerGrid}>
                    {userPhotos.map((photo) => {
                      const isSelected = selectedGalleryPhotos.some(p => p.id === photo.id);
                      return (
                        <TouchableOpacity
                          key={photo.id}
                          style={[
                            styles.photoPickerItem,
                            isSelected && styles.photoPickerItemSelected
                          ]}
                          onPress={() => toggleGalleryPhotoSelection(photo)}
                        >
                          <Image
                            source={{ 
                              uri: `${BASE_URL}${photo.original_url}`,
                              headers: { 'Authorization': `Bearer ${authToken}` }
                            }}
                            style={styles.photoPickerImage}
                          />
                          {isSelected && (
                            <View style={styles.photoPickerCheck}>
                              <Ionicons name="checkmark-circle" size={32} color="#E85D75" />
                            </View>
                          )}
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </ScrollView>

                <View style={styles.modalFooter}>
                  <TextInput
                    style={styles.captionInput}
                    placeholder="Add caption (optional)"
                    value={photoCaption}
                    onChangeText={setPhotoCaption}
                    multiline
                    returnKeyType="done"
                    blurOnSubmit={true}
                  />
                  
                  {uploadProgress.total > 0 && (
                    <View style={styles.progressContainer}>
                      <Text style={styles.progressText}>
                        Adding {uploadProgress.current} of {uploadProgress.total} photos...
                      </Text>
                      <View style={styles.progressBar}>
                        <View 
                          style={[
                            styles.progressFill, 
                            { width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }
                          ]} 
                        />
                      </View>
                    </View>
                  )}
                  
                  <TouchableOpacity
                    style={[styles.addButton, (adding || selectedGalleryPhotos.length === 0) && styles.addButtonDisabled]}
                    onPress={addPhotoToVault}
                    disabled={adding || selectedGalleryPhotos.length === 0}
                  >
                    {adding ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={styles.addButtonText}>
                        Add {selectedGalleryPhotos.length > 0 ? `${selectedGalleryPhotos.length} ` : ''}to Vault
                      </Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </KeyboardAvoidingView>
      </Modal>

      {/* Invite Member Modal */}
      <Modal
        visible={showInviteModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowInviteModal(false)}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
            <View style={styles.modalContainer}>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Invite Member</Text>
                  <TouchableOpacity onPress={() => setShowInviteModal(false)}>
                    <Ionicons name="close" size={28} color="#333" />
                  </TouchableOpacity>
                </View>

                <View style={styles.inviteForm}>
                  <Text style={styles.inputLabel}>Email Address</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="member@example.com"
                    value={inviteEmail}
                    onChangeText={setInviteEmail}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoCorrect={false}
                  />

                  <Text style={styles.inputLabel}>Role</Text>
                  <View style={styles.roleSelector}>
                    <TouchableOpacity
                      style={[
                        styles.roleOption,
                        inviteRole === 'member' && styles.roleOptionSelected
                      ]}
                      onPress={() => setInviteRole('member')}
                    >
                      <Text style={[
                        styles.roleOptionText,
                        inviteRole === 'member' && styles.roleOptionTextSelected
                      ]}>Member</Text>
                    </TouchableOpacity>
                    
                    <TouchableOpacity
                      style={[
                        styles.roleOption,
                        inviteRole === 'admin' && styles.roleOptionSelected
                      ]}
                      onPress={() => setInviteRole('admin')}
                    >
                      <Text style={[
                        styles.roleOptionText,
                        inviteRole === 'admin' && styles.roleOptionTextSelected
                      ]}>Admin</Text>
                    </TouchableOpacity>
                  </View>

                  <TouchableOpacity
                    style={[styles.inviteButton, inviting && styles.inviteButtonDisabled]}
                    onPress={inviteMemberToVault}
                    disabled={inviting || !inviteEmail.trim()}
                  >
                    {inviting ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={styles.inviteButtonText}>Send Invitation</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </KeyboardAvoidingView>
      </Modal>

      {/* Edit Vault Modal */}
      <Modal
        visible={showEditModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => !editing && setShowEditModal(false)}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
            <View style={styles.modalContainer}>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Edit Vault</Text>
                  <TouchableOpacity onPress={() => !editing && setShowEditModal(false)}>
                    <Ionicons name="close" size={28} color="#333" />
                  </TouchableOpacity>
                </View>

                <View style={styles.inviteForm}>
                  <Text style={styles.inputLabel}>Vault Name</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Vault name"
                    value={editVaultName}
                    onChangeText={setEditVaultName}
                    editable={!editing}
                  />

                  <Text style={styles.inputLabel}>Description</Text>
                  <TextInput
                    style={[styles.input, styles.textArea]}
                    placeholder="Vault description"
                    value={editVaultDescription}
                    onChangeText={setEditVaultDescription}
                    multiline
                    numberOfLines={4}
                    editable={!editing}
                  />

                  <TouchableOpacity
                    style={[styles.inviteButton, editing && styles.inviteButtonDisabled]}
                    onPress={handleEditVault}
                    disabled={editing || !editVaultName.trim()}
                  >
                    {editing ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={styles.inviteButtonText}>Save Changes</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#000',
  },
  errorText: {
    fontSize: 18,
    color: '#999',
    marginTop: 20,
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#E85D75',
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 10,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
    backgroundColor: '#000',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
    marginHorizontal: 15,
    textAlign: 'center',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#000',
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: '#E85D75',
  },
  tabText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#fff',
    fontWeight: 'bold',
  },
  photosContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  photoList: {
    paddingBottom: 80,
  },
  photoCard: {
    width: ITEM_WIDTH,
    height: ITEM_WIDTH * 1.6, // Vertical aspect ratio like TikTok
    margin: 1,
    backgroundColor: '#1a1a1a',
    position: 'relative',
  },
  photoImage: {
    width: '100%',
    height: '100%',
  },
  photoImagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
  },
  bottomOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 8,
    paddingBottom: 6,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  photoDate: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '500',
  },
  photoSharedBy: {
    color: '#fff',
    fontSize: 9,
    fontWeight: '400',
    opacity: 0.8,
    marginTop: 2,
  },
  ownerBadge: {
    position: 'absolute',
    top: 6,
    left: 6,
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    padding: 2,
  },
  enhancedBadge: {
    position: 'absolute',
    top: 6,
    right: 6,
    backgroundColor: '#E85D75',
    borderRadius: 10,
    padding: 3,
  },
  voiceMemoBadge: {
    position: 'absolute',
    top: 30,
    right: 6,
    backgroundColor: '#4CAF50',
    borderRadius: 10,
    padding: 3,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 5,
  },
  commentBadge: {
    position: 'absolute',
    top: 54,
    right: 6,
    backgroundColor: '#2196F3',
    borderRadius: 10,
    padding: 3,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 5,
  },
  badgeCount: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
    marginLeft: 2,
  },
  cancelText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  selectionCheckbox: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 14,
  },
  floatingButtonsContainer: {
    position: 'absolute',
    bottom: 30,
    right: 30,
    gap: 20,
    alignItems: 'center',
  },
  floatingButtonWrapper: {
    alignItems: 'center',
    gap: 8,
  },
  floatingButtonLabel: {
    color: '#333',
    fontSize: 12,
    fontWeight: '600',
    backgroundColor: '#fff',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  floatingLibraryButton: {
    backgroundColor: '#4CAF50',
  },
  emptyPhotos: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 18,
    color: '#999',
    marginTop: 20,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
  },
  floatingAddButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#E85D75',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  membersContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  membersList: {
    padding: 20,
  },
  membersHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  membersTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  memberCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
  },
  memberAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  memberInfo: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  memberName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  memberRoleBadge: {
    backgroundColor: '#E85D75',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  memberRole: {
    fontSize: 12,
    color: '#fff',
    fontWeight: 'bold',
    textTransform: 'capitalize',
  },
  memberRoleAdmin: {
    color: '#E85D75',
  },
  memberActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  memberActionButton: {
    padding: 8,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerButton: {
    padding: 4,
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  emptyMembers: {
    alignItems: 'center',
    padding: 60,
  },
  // Photo Picker Modal Styles
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '85%',
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
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  photoPickerScroll: {
    maxHeight: 400,
  },
  photoPickerGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  photoPickerItem: {
    width: '31%',
    aspectRatio: 1,
    margin: '1%',
    borderRadius: 10,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  photoPickerItemSelected: {
    borderColor: '#E85D75',
  },
  photoPickerImage: {
    width: '100%',
    height: '100%',
  },
  photoPickerCheck: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -16 }, { translateY: -16 }],
  },
  modalFooter: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  captionInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 12,
    fontSize: 16,
    marginBottom: 15,
    minHeight: 60,
    textAlignVertical: 'top',
  },
  addButton: {
    backgroundColor: '#E85D75',
    padding: 16,
    borderRadius: 10,
    alignItems: 'center',
  },
  addButtonDisabled: {
    opacity: 0.6,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  // Invite Member Modal Styles
  inviteForm: {
    padding: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 12,
    fontSize: 16,
  },
  roleSelector: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },
  roleOption: {
    flex: 1,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ddd',
    alignItems: 'center',
  },
  roleOptionSelected: {
    borderColor: '#E85D75',
    backgroundColor: '#FFF0F3',
  },
  roleOptionText: {
    fontSize: 16,
    color: '#666',
  },
  roleOptionTextSelected: {
    color: '#E85D75',
    fontWeight: 'bold',
  },
  inviteButton: {
    backgroundColor: '#E85D75',
    padding: 16,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  inviteButtonDisabled: {
    opacity: 0.6,
  },
  inviteButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  // Upload Progress Styles
  uploadProgressOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  uploadProgressCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 30,
    alignItems: 'center',
    minWidth: 250,
  },
  uploadProgressText: {
    fontSize: 16,
    color: '#333',
    marginTop: 15,
    marginBottom: 15,
    textAlign: 'center',
  },
  uploadProgressBarContainer: {
    width: '100%',
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  uploadProgressBarFill: {
    height: '100%',
    backgroundColor: '#E85D75',
    borderRadius: 4,
  },
  // Selection Info Styles
  selectionInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#FFF0F3',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  selectionInfoText: {
    fontSize: 14,
    color: '#333',
    fontWeight: '600',
  },
  clearSelectionText: {
    fontSize: 14,
    color: '#E85D75',
    fontWeight: '600',
  },
  // Progress Container (in modal)
  progressContainer: {
    marginBottom: 15,
  },
  progressText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    textAlign: 'center',
  },
  progressBar: {
    width: '100%',
    height: 6,
    backgroundColor: '#f0f0f0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#E85D75',
    borderRadius: 3,
  },
});
