import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Dimensions,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');
const BASE_URL = 'https://storykeep.calmic.com.my';

export default function EnhancedGalleryScreen({ route, navigation }) {
  const { photo } = route.params;
  const [enhancedVersions, setEnhancedVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [authToken, setAuthToken] = useState(null);

  useEffect(() => {
    loadEnhancedVersions();
  }, []);

  const loadEnhancedVersions = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      setAuthToken(token);

      const response = await fetch(`${BASE_URL}/api/photos/${photo.id}/enhanced-versions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setEnhancedVersions(data.enhanced_versions || []);
      } else {
        Alert.alert('Error', 'Failed to load enhanced versions');
      }
    } catch (error) {
      console.error('Error loading enhanced versions:', error);
      Alert.alert('Error', 'Failed to load enhanced versions');
    } finally {
      setLoading(false);
    }
  };

  const getEnhancementLabel = (type) => {
    const labels = {
      'colorized': 'Colorized',
      'sharpened': 'Sharpened',
      'auto_enhanced': 'Auto Enhanced',
      'enhanced': 'Enhanced'
    };
    return labels[type] || 'Enhanced';
  };

  const getEnhancementIcon = (type) => {
    const icons = {
      'colorized': 'color-palette',
      'sharpened': 'aperture',
      'auto_enhanced': 'sparkles',
      'enhanced': 'sparkles'
    };
    return icons[type] || 'sparkles';
  };

  const handleViewEnhanced = (enhancedPhoto) => {
    // Navigate to photo detail screen with the enhanced version
    navigation.navigate('PhotoDetail', {
      photo: {
        ...photo,
        id: enhancedPhoto.id,
        url: enhancedPhoto.url,
        original_url: enhancedPhoto.url,
        edited_url: null, // Enhanced versions don't have further edits
        enhancement_type: enhancedPhoto.enhancement_type
      }
    });
  };

  const handleDeleteEnhanced = async (enhancedPhoto) => {
    Alert.alert(
      'Delete Enhanced Version',
      'Are you sure you want to delete this enhanced version?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await fetch(`${BASE_URL}/api/photos/${enhancedPhoto.id}`, {
                method: 'DELETE',
                headers: {
                  'Authorization': `Bearer ${authToken}`
                }
              });

              if (response.ok) {
                Alert.alert('Success', 'Enhanced version deleted');
                loadEnhancedVersions(); // Reload the list
              } else {
                Alert.alert('Error', 'Failed to delete enhanced version');
              }
            } catch (error) {
              console.error('Delete error:', error);
              Alert.alert('Error', 'Failed to delete enhanced version');
            }
          }
        }
      ]
    );
  };

  const renderEnhancedVersion = ({ item }) => (
    <TouchableOpacity
      style={styles.enhancedCard}
      onPress={() => handleViewEnhanced(item)}
    >
      <Image
        source={{
          uri: BASE_URL + item.url,
          headers: { 'Authorization': `Bearer ${authToken}` }
        }}
        style={styles.thumbnail}
        resizeMode="cover"
      />
      <View style={styles.cardInfo}>
        <View style={styles.labelContainer}>
          <Ionicons
            name={getEnhancementIcon(item.enhancement_type)}
            size={16}
            color="#e91e63"
          />
          <Text style={styles.enhancementLabel}>
            {getEnhancementLabel(item.enhancement_type)}
          </Text>
        </View>
        <Text style={styles.dateText}>
          {new Date(item.created_at).toLocaleDateString()}
        </Text>
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={() => handleDeleteEnhanced(item)}
        >
          <Ionicons name="trash-outline" size={20} color="#ff4444" />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#e91e63" />
        <Text style={styles.loadingText}>Loading enhanced versions...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Enhanced Versions</Text>
        <View style={styles.placeholder} />
      </View>

      {enhancedVersions.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="images-outline" size={64} color="#ccc" />
          <Text style={styles.emptyText}>No enhanced versions yet</Text>
          <Text style={styles.emptySubtext}>
            Tap the Enhance button to create enhanced versions
          </Text>
        </View>
      ) : (
        <>
          <View style={styles.countContainer}>
            <Text style={styles.countText}>
              {enhancedVersions.length} enhanced {enhancedVersions.length === 1 ? 'version' : 'versions'}
            </Text>
          </View>
          <FlatList
            data={enhancedVersions}
            renderItem={renderEnhancedVersion}
            keyExtractor={(item) => item.id.toString()}
            numColumns={2}
            columnWrapperStyle={styles.columnWrapper}
            contentContainerStyle={styles.listContainer}
            showsVerticalScrollIndicator={false}
          />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 50,
    paddingBottom: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  placeholder: {
    width: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  countContainer: {
    padding: 16,
    backgroundColor: '#fff',
  },
  countText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  listContainer: {
    padding: 16,
  },
  columnWrapper: {
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  enhancedCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    width: (width - 48) / 2,
  },
  thumbnail: {
    width: '100%',
    height: 150,
    backgroundColor: '#f0f0f0',
  },
  cardInfo: {
    padding: 12,
  },
  labelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  enhancementLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginLeft: 6,
  },
  dateText: {
    fontSize: 12,
    color: '#666',
  },
  deleteButton: {
    position: 'absolute',
    top: 12,
    right: 12,
    padding: 6,
    backgroundColor: '#fff',
    borderRadius: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
  },
});
