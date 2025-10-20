import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';

export default function SettingsScreen({ navigation }) {
  const [autoEnhance, setAutoEnhance] = useState(false);
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const [offlineMode, setOfflineMode] = useState(true);

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

  const SettingItem = ({ icon, title, subtitle, onPress, rightElement }) => (
    <TouchableOpacity style={styles.settingItem} onPress={onPress}>
      <View style={styles.settingLeft}>
        <Ionicons name={icon} size={24} color="#E85D75" />
        <View style={styles.settingText}>
          <Text style={styles.settingTitle}>{title}</Text>
          {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
        </View>
      </View>
      {rightElement || <Ionicons name="chevron-forward" size={24} color="#ccc" />}
    </TouchableOpacity>
  );

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account</Text>
        <SettingItem
          icon="person"
          title="Profile"
          subtitle="Manage your account details"
          onPress={() => navigation.navigate('Profile')}
        />
        <SettingItem
          icon="shield-checkmark"
          title="Subscription"
          subtitle="View your plan and billing"
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Photo Settings</Text>
        <SettingItem
          icon="sparkles"
          title="Auto-Enhance"
          subtitle="Automatically enhance captured photos"
          rightElement={
            <Switch
              value={autoEnhance}
              onValueChange={setAutoEnhance}
              trackColor={{ false: '#ccc', true: '#E85D75' }}
            />
          }
        />
        <SettingItem
          icon="cloud-offline"
          title="Offline Queue"
          subtitle="Save photos offline and upload later"
          rightElement={
            <Switch
              value={offlineMode}
              onValueChange={setOfflineMode}
              trackColor={{ false: '#ccc', true: '#E85D75' }}
            />
          }
        />
        <SettingItem
          icon="resize"
          title="Photo Quality"
          subtitle="High quality (original size)"
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Security</Text>
        <SettingItem
          icon="finger-print"
          title="Biometric Login"
          subtitle="Use Face ID or Touch ID"
          rightElement={
            <Switch
              value={biometricEnabled}
              onValueChange={setBiometricEnabled}
              trackColor={{ false: '#ccc', true: '#E85D75' }}
            />
          }
        />
        <SettingItem
          icon="lock-closed"
          title="Change Password"
          subtitle="Update your account password"
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Storage</Text>
        <SettingItem
          icon="cloud"
          title="Storage Usage"
          subtitle="Manage your storage"
        />
        <SettingItem
          icon="trash"
          title="Clear Cache"
          subtitle="Free up space on your device"
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <SettingItem
          icon="information-circle"
          title="App Version"
          subtitle="1.0.0"
        />
        <SettingItem
          icon="document-text"
          title="Terms of Service"
        />
        <SettingItem
          icon="shield"
          title="Privacy Policy"
        />
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out" size={24} color="#fff" />
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>

      <Text style={styles.footer}>StoryKeep by CALMIC SDN BHD</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    padding: 20,
    paddingTop: 60,
    backgroundColor: '#f8f8f8',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#666',
    paddingHorizontal: 20,
    marginBottom: 10,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingText: {
    marginLeft: 15,
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  settingSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E85D75',
    marginHorizontal: 20,
    marginTop: 30,
    marginBottom: 20,
    padding: 15,
    borderRadius: 10,
  },
  logoutText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  footer: {
    textAlign: 'center',
    fontSize: 14,
    color: '#999',
    padding: 20,
  },
});
