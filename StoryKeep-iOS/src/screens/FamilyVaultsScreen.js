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
  Modal,
  TextInput,
  KeyboardAvoidingView,
  ScrollView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { vaultAPI } from '../services/api';

export default function FamilyVaultsScreen({ navigation }) {
  const [vaults, setVaults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [newVaultName, setNewVaultName] = useState('');
  const [newVaultDescription, setNewVaultDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadVaults();
  }, []);

  const loadVaults = async () => {
    try {
      const response = await vaultAPI.getVaults();
      setVaults(response.vaults || []);
    } catch (error) {
      console.error('Vaults error:', error);
      Alert.alert('Error', 'Failed to load family vaults');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadVaults();
  };

  const handleCreateVault = async () => {
    if (!newVaultName.trim()) {
      Alert.alert('Error', 'Please enter a vault name');
      return;
    }

    if (!newVaultDescription.trim()) {
      Alert.alert('Error', 'Please enter a vault description');
      return;
    }

    setCreating(true);
    try {
      const response = await vaultAPI.createVault(newVaultName.trim(), newVaultDescription.trim());
      
      if (response.vault) {
        Alert.alert(
          'Success',
          `Vault "${response.vault.name}" created!\n\nVault Code: ${response.vault.vault_code}\n\nShare this code with family members to invite them.`,
          [{ text: 'OK', onPress: () => {
            setCreateModalVisible(false);
            setNewVaultName('');
            setNewVaultDescription('');
            loadVaults();
          }}]
        );
      } else {
        Alert.alert('Error', response.error || 'Failed to create vault');
      }
    } catch (error) {
      console.error('Create vault error:', error);
      Alert.alert('Error', error.response?.data?.error || 'Failed to create vault');
    } finally {
      setCreating(false);
    }
  };

  const renderVault = ({ item }) => (
    <TouchableOpacity
      style={styles.vaultCard}
      onPress={() => navigation.navigate('VaultDetail', { vaultId: item.id })}
    >
      <View style={styles.vaultIcon}>
        <Ionicons name="people" size={32} color="#E85D75" />
      </View>
      <View style={styles.vaultInfo}>
        <Text style={styles.vaultName}>{item.name}</Text>
        <Text style={styles.vaultDescription} numberOfLines={2}>
          {item.description || 'No description'}
        </Text>
        <View style={styles.vaultMeta}>
          <Text style={styles.vaultCode}>Code: {item.vault_code}</Text>
          {item.is_creator && (
            <View style={styles.creatorBadge}>
              <Text style={styles.creatorText}>Creator</Text>
            </View>
          )}
        </View>
      </View>
      <Ionicons name="chevron-forward" size={24} color="#ccc" />
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#E85D75" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Family Vaults</Text>
        <TouchableOpacity 
          style={styles.addButton}
          onPress={() => setCreateModalVisible(true)}
        >
          <Ionicons name="add-circle" size={32} color="#E85D75" />
        </TouchableOpacity>
      </View>

      {vaults.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="people-outline" size={80} color="#ccc" />
          <Text style={styles.emptyText}>No family vaults yet</Text>
          <Text style={styles.emptySubtext}>
            Create a vault to share photos with family
          </Text>
          <TouchableOpacity 
            style={styles.createButton}
            onPress={() => setCreateModalVisible(true)}
          >
            <Text style={styles.createButtonText}>Create Your First Vault</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={vaults}
          renderItem={renderVault}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.vaultList}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
      )}

      <Modal
        animationType="slide"
        transparent={true}
        visible={createModalVisible}
        onRequestClose={() => !creating && setCreateModalVisible(false)}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create Family Vault</Text>
              <TouchableOpacity 
                onPress={() => !creating && setCreateModalVisible(false)}
                disabled={creating}
              >
                <Ionicons name="close" size={28} color="#666" />
              </TouchableOpacity>
            </View>

            <ScrollView 
              style={styles.modalBody} 
              contentContainerStyle={styles.scrollContent}
              showsVerticalScrollIndicator={false}
              keyboardShouldPersistTaps="handled"
            >
              <Text style={styles.inputLabel}>Vault Name</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Family Memories 2024"
                value={newVaultName}
                onChangeText={setNewVaultName}
                editable={!creating}
              />

              <Text style={styles.inputLabel}>Description</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="Describe what this vault is for..."
                value={newVaultDescription}
                onChangeText={setNewVaultDescription}
                multiline
                numberOfLines={4}
                editable={!creating}
              />

              <TouchableOpacity 
                style={[styles.submitButton, creating && styles.submitButtonDisabled]}
                onPress={handleCreateVault}
                disabled={creating}
              >
                {creating ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.submitButtonText}>Create Vault</Text>
                )}
              </TouchableOpacity>
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
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
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  addButton: {
    padding: 5,
  },
  vaultList: {
    padding: 15,
  },
  vaultCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 15,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#eee',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  vaultIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#FFF0F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  vaultInfo: {
    flex: 1,
  },
  vaultName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  vaultDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  vaultMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  vaultCode: {
    fontSize: 12,
    color: '#999',
    fontFamily: 'monospace',
  },
  creatorBadge: {
    backgroundColor: '#E85D75',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  creatorText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginTop: 20,
    marginBottom: 10,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginBottom: 30,
  },
  createButton: {
    backgroundColor: '#E85D75',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 10,
  },
  createButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
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
    paddingBottom: 40,
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
    padding: 20,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    marginTop: 15,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  submitButton: {
    backgroundColor: '#E85D75',
    padding: 18,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 25,
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
