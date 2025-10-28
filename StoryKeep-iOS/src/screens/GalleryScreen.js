/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Dimensions,
  Modal,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { photoAPI, vaultAPI } from '../services/api';
import * as FileSystem from 'expo-file-system/legacy';
import * as MediaLibrary from 'expo-media-library';
import { sharePhoto } from '../utils/sharePhoto';
import { useLoading } from '../contexts/LoadingContext';
import ProgressBar from '../components/ProgressBar';

const { width } = Dimensions.get('window');
const COLUMN_COUNT = 3;
const ITEM_WIDTH = (width - 6) / COLUMN_COUNT; // 2px gap between items
const BASE_URL = 'https://storykeep.calmic.com.my';
const PAGE_SIZE = 30;

export default function GalleryScreen({ navigation }) {
  const [allPhotos, setAllPhotos] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('all');
  const [authToken, setAuthToken] = useState(null);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedPhotos, setSelectedPhotos] = useState([]);
  const [downloadProgress, setDownloadProgress] = useState({ current: 0, total: 0, isDownloading: false });
  const [loadingMore, setLoadingMore] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [totalPhotos, setTotalPhotos] = useState(0);
  const { startLoading, stopLoading } = useLoading();
  
  // Vault sharing states
  const [showVaultModal, setShowVaultModal] = useState(false);
  const [vaults, setVaults] = useState([]);
  const [loadingVaults, setLoadingVaults] = useState(false);
  const [sharingToVault, setSharingToVault] = useState(false);

  useEffect(() => {
    loadPhotos();
  }, []);

  useEffect(() => {
    // When filter changes, reload from server
    if (!initialLoading) {
      setCurrentPage(1);
      loadPhotos(1, false);
    }
  }, [filter]);


  const loadPhotos = async (pageNum = 1, append = false) => {
    const loadingId = !refreshing && !append ? startLoading('Loading gallery...') : null;
    try {
      if (!append) {
        setInitialLoading(true);
        setLoadingProgress(0);
      }
      
      const token = await AsyncStorage.getItem('authToken');
      setAuthToken(token);
      
      if (!append) setLoadingProgress(30);
      
      // Use paginated photos endpoint for efficient loading
      const response = await fetch(`${BASE_URL}/api/photos?page=${pageNum}&per_page=30&filter=${filter}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!append) setLoadingProgress(70);
      
      const data = await response.json();
      
      if (data.success && data.photos) {
        if (append) {
          // Append new page to existing photos
          setAllPhotos(prev => [...prev, ...data.photos]);
        } else {
          // Replace all photos (fresh load or refresh)
          setAllPhotos(data.photos);
        }
        
        // Store pagination metadata
        if (data.pagination) {
          setCurrentPage(data.pagination.current_page);
          setTotalPhotos(data.pagination.total_count);
          // Store if there are more pages to load
          if (!data.pagination.has_more) {
            setLoadingMore(false);
          }
        }
      } else {
        if (!append) {
          setAllPhotos([]);
        }
      }
      
      if (!append) setLoadingProgress(100);
    } catch (error) {
      console.error('Gallery error:', error);
      Alert.alert('Error', 'Failed to load photos');
    } finally {
      if (loadingId !== null) {
        stopLoading(loadingId);
      }
      setRefreshing(false);
      setInitialLoading(false);
      setLoadingMore(false);
    }
  };

  const loadMorePhotos = () => {
    if (!loadingMore && !initialLoading) {
      setLoadingMore(true);
      // Load next page from server
      loadPhotos(currentPage + 1, true);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    setCurrentPage(1);
    loadPhotos(1, false);
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

  const selectAll = () => {
    const allPhotoIds = allPhotos.map(photo => photo.id);
    setSelectedPhotos(allPhotoIds);
  };

  const deselectAll = () => {
    setSelectedPhotos([]);
  };

  const handleBulkDownload = async () => {
    if (selectedPhotos.length === 0) {
      Alert.alert('No Selection', 'Please select photos to download');
      return;
    }

    try {
      const { status } = await MediaLibrary.requestPermissionsAsync();
      
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Cannot save photos without permission');
        return;
      }

      const totalPhotos = selectedPhotos.length;
      setDownloadProgress({ current: 0, total: totalPhotos, isDownloading: true });
      
      let successCount = 0;
      let failCount = 0;
      const failedPhotos = [];

      for (let i = 0; i < selectedPhotos.length; i++) {
        const photoId = selectedPhotos[i];
        const photo = allPhotos.find(p => p.id === photoId);
        
        setDownloadProgress({ current: i + 1, total: totalPhotos, isDownloading: true });
        
        if (!photo) {
          failedPhotos.push({ id: photoId, reason: 'Photo not found' });
          failCount++;
          continue;
        }

        try {
          console.log(`📥 Downloading ${i + 1}/${selectedPhotos.length}: Photo ${photoId}`);
          
          const relativePath = photo.edited_url || photo.url;
          const imageUrl = BASE_URL + relativePath;
          const fileUri = FileSystem.documentDirectory + `photo_${photo.id}_${Date.now()}.jpg`;
          
          const { uri } = await FileSystem.downloadAsync(
            imageUrl, 
            fileUri,
            {
              headers: {
                'Authorization': `Bearer ${authToken}`
              }
            }
          );
          
          await MediaLibrary.createAssetAsync(uri);
          successCount++;
          console.log(`✅ Saved ${i + 1}/${selectedPhotos.length}`);
        } catch (error) {
          console.error(`❌ Failed to download photo ${photoId}:`, error);
          const photoDate = formatDate(photo.created_at);
          failedPhotos.push({ id: photoId, date: photoDate });
          failCount++;
        }
      }

      setDownloadProgress({ current: 0, total: 0, isDownloading: false });
      
      if (successCount > 0) {
        let message = `Successfully saved ${successCount} photo(s) to your library!`;
        
        if (failCount > 0) {
          const failedDetails = failedPhotos.map(p => `ID ${p.id}${p.date ? ` (${p.date})` : ''}`).join(', ');
          message = `Successfully saved ${successCount} photo(s). ${failCount} failed:\n${failedDetails}`;
        }
        
        Alert.alert(
          'Download Complete', 
          message,
          [{ text: 'OK', onPress: () => {
            setSelectionMode(false);
            setSelectedPhotos([]);
          }}]
        );
      } else {
        const failedDetails = failedPhotos.map(p => `ID ${p.id}${p.date ? ` (${p.date})` : ''}`).join('\n');
        Alert.alert('Error', `Failed to download all photos:\n${failedDetails}`);
        setDownloadProgress({ current: 0, total: 0, isDownloading: false });
      }
    } catch (error) {
      console.error('Bulk download error:', error);
      Alert.alert('Error', 'Failed to download photos');
      setDownloadProgress({ current: 0, total: 0, isDownloading: false });
    }
  };

  const handleBulkDelete = async () => {
    if (selectedPhotos.length === 0) {
      Alert.alert('No Selection', 'Please select photos to delete');
      return;
    }

    Alert.alert(
      'Delete Photos',
      `Are you sure you want to delete ${selectedPhotos.length} photo(s)?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            const loadingId = startLoading('Deleting photos...');
            try {
              const result = await photoAPI.bulkDeletePhotos(selectedPhotos);
              
              Alert.alert(
                'Success', 
                result.message || `Deleted ${result.deleted_count} photos`,
                [{ text: 'OK', onPress: () => {
                  setSelectionMode(false);
                  setSelectedPhotos([]);
                  loadPhotos();
                }}]
              );
            } catch (error) {
              console.error('Bulk delete error:', error);
              Alert.alert('Error', 'Failed to delete photos');
            } finally {
              stopLoading(loadingId);
            }
          },
        },
      ]
    );
  };

  const loadVaults = async () => {
    setLoadingVaults(true);
    try {
      const response = await vaultAPI.getVaults();
      setVaults(response.vaults || []);
    } catch (error) {
      console.error('Load vaults error:', error);
      Alert.alert('Error', 'Failed to load family vaults');
    } finally {
      setLoadingVaults(false);
    }
  };

  const openVaultModal = () => {
    if (selectedPhotos.length === 0) {
      Alert.alert('No Selection', 'Please select photos to share');
      return;
    }
    loadVaults();
    setShowVaultModal(true);
  };

  const shareToVault = async (vaultId, vaultName) => {
    if (selectedPhotos.length === 0) {
      Alert.alert('No Selection', 'Please select photos to share');
      return;
    }

    setSharingToVault(true);
    try {
      // Use bulk API endpoint for efficient sharing
      const response = await vaultAPI.addPhotosToVaultBulk(vaultId, selectedPhotos, '');
      
      const successCount = response.success_count || 0;
      const failCount = response.failed_count || 0;
      const failedPhotoIds = response.failed_photo_ids || [];
      
      if (failCount === 0) {
        // All photos shared successfully
        Alert.alert(
          'Success',
          `Successfully shared ${successCount} photo${successCount > 1 ? 's' : ''} to "${vaultName}"`,
          [{ text: 'OK', onPress: () => {
            setShowVaultModal(false);
            setSelectionMode(false);
            setSelectedPhotos([]);
          }}]
        );
      } else if (successCount > 0) {
        // Partial success - keep failed photos selected for retry
        setSelectedPhotos(failedPhotoIds);
        Alert.alert(
          'Partial Success',
          `Shared ${successCount} photo(s) successfully. ${failCount} photo(s) failed and remain selected for retry.`,
          [{ text: 'OK' }]
        );
      } else {
        // All photos failed
        Alert.alert(
          'Error', 
          `Failed to share all ${failCount} photo(s) to vault. Please try again.`,
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Share to vault error:', error);
      Alert.alert(
        'Error',
        'Failed to share photos to vault. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setSharingToVault(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
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

  const handleSharePhoto = async (photo, event) => {
    event.stopPropagation();
    await sharePhoto(photo, authToken, !!photo.edited_url);
  };

  const renderPhoto = ({ item, index }) => {
    // Get the image URL - prefer thumbnail, fallback to url or original_url
    const imageUrl = item.thumbnail_url || item.url || item.original_url;
    
    // Construct full URL if it's a relative path
    const fullImageUrl = imageUrl?.startsWith('http') 
      ? imageUrl 
      : imageUrl?.startsWith('/') 
        ? `${BASE_URL}${imageUrl}`
        : imageUrl;

    const isSelected = selectedPhotos.includes(item.id);

    return (
      <TouchableOpacity
        style={[styles.photoCard, selectionMode && isSelected && styles.photoCardSelected]}
        onPress={() => selectionMode ? togglePhotoSelection(item.id) : navigation.navigate('PhotoDetail', { photo: item })}
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
            resizeMode="cover"
          />
        ) : (
          <View style={styles.photoImagePlaceholder}>
            <ActivityIndicator size="small" color="#E85D75" />
          </View>
        )}
        
        {/* Bottom gradient overlay */}
        <View style={styles.bottomOverlay}>
          <Text style={styles.photoDate} numberOfLines={1}>
            {formatDate(item.created_at)}
          </Text>
          {!selectionMode && (
            <TouchableOpacity
              style={styles.shareIconButton}
              onPress={(e) => handleSharePhoto(item, e)}
            >
              <Ionicons name="share-social" size={16} color="#fff" />
            </TouchableOpacity>
          )}
        </View>

        {/* Top right badges - Colorized */}
        {item.edited_url && (
          <View style={styles.enhancedBadge}>
            <Ionicons name="sparkles" size={14} color="#fff" />
          </View>
        )}
        
        {/* Top left badges */}
        {item.voice_memo_count > 0 && (
          <View style={styles.voiceBadge}>
            <Ionicons name="mic" size={12} color="#fff" />
            <Text style={styles.voiceBadgeText}>{item.voice_memo_count}</Text>
          </View>
        )}
        
        {item.comment_count > 0 && (
          <View style={[styles.voiceBadge, { top: item.voice_memo_count > 0 ? 34 : 6 }]}>
            <Ionicons name="chatbox" size={12} color="#fff" />
            <Text style={styles.voiceBadgeText}>{item.comment_count}</Text>
          </View>
        )}

        {/* Selection checkbox */}
        {selectionMode && (
          <View style={styles.checkboxContainer}>
            <View style={[styles.checkbox, isSelected && styles.checkboxSelected]}>
              {isSelected && <Ionicons name="checkmark" size={16} color="#fff" />}
            </View>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const FilterButton = ({ label, value }) => (
    <TouchableOpacity
      style={[
        styles.filterButton,
        filter === value && styles.filterButtonActive,
      ]}
      onPress={() => setFilter(value)}
    >
      <Text
        style={[
          styles.filterText,
          filter === value && styles.filterTextActive,
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.title}>Gallery</Text>
          <Text style={styles.count}>
            {downloadProgress.isDownloading 
              ? `Downloading ${downloadProgress.current} of ${downloadProgress.total}...`
              : selectionMode 
                ? `${selectedPhotos.length} selected` 
                : totalPhotos > 0 ? `${totalPhotos} photos` : `${allPhotos.length} photos`}
          </Text>
        </View>
        <View style={styles.headerRight}>
          {selectionMode && (
            <>
              {selectedPhotos.length > 0 && !downloadProgress.isDownloading && (
                <>
                  <TouchableOpacity 
                    style={styles.shareButton}
                    onPress={openVaultModal}
                  >
                    <Ionicons name="share-social" size={24} color="#fff" />
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={styles.downloadButton}
                    onPress={handleBulkDownload}
                  >
                    <Ionicons name="download" size={24} color="#fff" />
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={styles.deleteButton}
                    onPress={handleBulkDelete}
                  >
                    <Ionicons name="trash" size={24} color="#fff" />
                  </TouchableOpacity>
                </>
              )}
              {!downloadProgress.isDownloading && (
                <TouchableOpacity 
                  style={[styles.selectAllButton, selectedPhotos.length === allPhotos.length && styles.selectAllButtonActive]}
                  onPress={selectedPhotos.length === allPhotos.length ? deselectAll : selectAll}
                >
                  <Text style={styles.selectAllButtonText}>
                    {selectedPhotos.length === allPhotos.length ? 'None' : 'All'}
                  </Text>
                </TouchableOpacity>
              )}
            </>
          )}
          {!downloadProgress.isDownloading && (
            <TouchableOpacity 
              style={styles.selectButton}
              onPress={toggleSelectionMode}
            >
              <Text style={styles.selectButtonText}>
                {selectionMode ? 'Done' : 'Select'}
              </Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      <View style={styles.filterContainer}>
        <FilterButton label="All" value="all" />
        <FilterButton label="DNN" value="dnn" />
        <FilterButton label="AI" value="ai" />
        <FilterButton label="Uncolorized" value="uncolorized" />
        <FilterButton label="Originals" value="originals" />
        <FilterButton label="Colorized" value="colorized" />
      </View>

      {initialLoading ? (
        <View style={styles.loadingContainer}>
          <View style={styles.loadingSpinnerContainer}>
            <ActivityIndicator size="large" color="#E85D75" />
            <View style={styles.loadingRing} />
          </View>
          <Text style={styles.loadingTitle}>Loading Your Photos</Text>
          <Text style={styles.loadingSubtitle}>
            {totalPhotos > 0 ? `${totalPhotos} photos total` : 'Fetching gallery...'}
          </Text>
          <ProgressBar 
            progress={loadingProgress} 
            message={loadingProgress < 50 ? "Connecting to server..." : "Loading photos..."}
            color="#E85D75"
            showPercentage={true}
          />
        </View>
      ) : allPhotos.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="images-outline" size={80} color="#ccc" />
          <Text style={styles.emptyText}>No photos yet</Text>
          <TouchableOpacity
            style={styles.captureButton}
            onPress={() => navigation.navigate('Camera')}
          >
            <Text style={styles.captureButtonText}>Capture Photos</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={allPhotos}
          renderItem={renderPhoto}
          keyExtractor={(item) => item.id.toString()}
          numColumns={COLUMN_COUNT}
          contentContainerStyle={styles.photoList}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          onEndReached={loadMorePhotos}
          onEndReachedThreshold={0.5}
          initialNumToRender={PAGE_SIZE}
          maxToRenderPerBatch={PAGE_SIZE}
          windowSize={5}
          removeClippedSubviews={true}
          ListFooterComponent={() => 
            loadingMore ? (
              <View style={{ padding: 20, alignItems: 'center' }}>
                <ActivityIndicator size="small" color="#E85D75" />
              </View>
            ) : null
          }
        />
      )}

      {/* Vault Selection Modal */}
      <Modal
        visible={showVaultModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowVaultModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Share to Family Vault</Text>
              <TouchableOpacity onPress={() => setShowVaultModal(false)}>
                <Ionicons name="close" size={28} color="#333" />
              </TouchableOpacity>
            </View>

            {loadingVaults ? (
              <View style={styles.modalLoading}>
                <ActivityIndicator size="large" color="#E85D75" />
                <Text style={styles.loadingText}>Loading vaults...</Text>
              </View>
            ) : vaults.length === 0 ? (
              <View style={styles.emptyVaults}>
                <Ionicons name="people-outline" size={60} color="#666" />
                <Text style={styles.emptyVaultsText}>No family vaults yet</Text>
                <Text style={styles.emptyVaultsSubtext}>
                  Create a family vault to share photos
                </Text>
              </View>
            ) : (
              <>
                <ScrollView style={styles.vaultList}>
                  {vaults.map((vault) => (
                    <TouchableOpacity
                      key={vault.id}
                      style={[styles.vaultItem, sharingToVault && styles.vaultItemDisabled]}
                      onPress={() => shareToVault(vault.id, vault.name)}
                      disabled={sharingToVault}
                    >
                      <View style={styles.vaultIcon}>
                        <Ionicons name="people" size={24} color="#E85D75" />
                      </View>
                      <View style={styles.vaultDetails}>
                        <Text style={styles.vaultName}>{vault.name}</Text>
                        <Text style={styles.vaultDescription} numberOfLines={1}>
                          {vault.description || 'No description'}
                        </Text>
                      </View>
                      <Ionicons name="chevron-forward" size={24} color="#999" />
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                {sharingToVault && (
                  <View style={styles.sharingOverlay}>
                    <View style={styles.sharingContainer}>
                      <ActivityIndicator size="large" color="#E85D75" />
                      <Text style={styles.sharingText}>
                        Sharing {selectedPhotos.length} photo{selectedPhotos.length > 1 ? 's' : ''}...
                      </Text>
                    </View>
                  </View>
                )}
              </>
            )}
          </View>
        </View>
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
    paddingHorizontal: 40,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginTop: 20,
    marginBottom: 30,
  },
  captureButton: {
    backgroundColor: '#E85D75',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
  },
  captureButtonText: {
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
  headerLeft: {
    flex: 1,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  count: {
    fontSize: 14,
    color: '#999',
    marginTop: 4,
  },
  selectButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#E85D75',
  },
  selectButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  downloadButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#34C759',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  deleteButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#ff3b30',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  selectAllButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#333',
    marginRight: 10,
  },
  selectAllButtonActive: {
    backgroundColor: '#555',
  },
  selectAllButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  filterContainer: {
    flexDirection: 'row',
    padding: 15,
    backgroundColor: '#000',
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  filterButton: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#1a1a1a',
    marginRight: 10,
  },
  filterButtonActive: {
    backgroundColor: '#E85D75',
  },
  filterText: {
    fontSize: 14,
    color: '#666',
  },
  filterTextActive: {
    color: '#fff',
    fontWeight: 'bold',
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
  photoCardSelected: {
    opacity: 0.7,
    borderWidth: 3,
    borderColor: '#E85D75',
  },
  photoImage: {
    width: '100%',
    height: '100%',
  },
  checkboxContainer: {
    position: 'absolute',
    top: 8,
    right: 8,
    zIndex: 10,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#fff',
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxSelected: {
    backgroundColor: '#E85D75',
    borderColor: '#E85D75',
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  photoDate: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '500',
    flex: 1,
  },
  shareIconButton: {
    padding: 4,
    marginLeft: 8,
  },
  enhancedBadge: {
    position: 'absolute',
    top: 6,
    right: 6,
    backgroundColor: '#E85D75',
    borderRadius: 10,
    padding: 3,
  },
  voiceBadge: {
    position: 'absolute',
    top: 6,
    left: 6,
    backgroundColor: 'rgba(0,0,0,0.7)',
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 3,
    flexDirection: 'row',
    alignItems: 'center',
  },
  voiceBadgeText: {
    color: '#fff',
    fontSize: 10,
    marginLeft: 3,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#000',
  },
  loadingSpinnerContainer: {
    width: 80,
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
    position: 'relative',
  },
  loadingRing: {
    position: 'absolute',
    width: 70,
    height: 70,
    borderRadius: 35,
    borderWidth: 3,
    borderColor: 'rgba(232, 93, 117, 0.2)',
    borderTopColor: '#E85D75',
  },
  loadingTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  loadingSubtitle: {
    fontSize: 16,
    color: '#888',
    marginBottom: 30,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 18,
    color: '#999',
    marginTop: 20,
    marginBottom: 30,
  },
  captureButton: {
    backgroundColor: '#E85D75',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 10,
  },
  captureButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  shareButton: {
    backgroundColor: '#4CAF50',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 25,
    borderTopRightRadius: 25,
    maxHeight: '70%',
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
  modalLoading: {
    padding: 60,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#666',
  },
  emptyVaults: {
    padding: 60,
    alignItems: 'center',
  },
  emptyVaultsText: {
    fontSize: 18,
    color: '#666',
    marginTop: 15,
  },
  emptyVaultsSubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
  },
  vaultList: {
    maxHeight: 400,
  },
  vaultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  vaultIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#FFF0F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  vaultDetails: {
    flex: 1,
  },
  vaultName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  vaultDescription: {
    fontSize: 14,
    color: '#666',
  },
  vaultItemDisabled: {
    opacity: 0.5,
  },
  sharingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255,255,255,0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sharingContainer: {
    alignItems: 'center',
    padding: 30,
  },
  sharingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#333',
    fontWeight: '600',
  },
});
