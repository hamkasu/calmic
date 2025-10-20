import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Image,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import { authAPI } from '../services/api';
import { useLoading } from '../contexts/LoadingContext';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { startLoading, stopLoading } = useLoading();

  const handleLogin = async (skipBiometricSave = false, credEmail = null, credPassword = null) => {
    const loginEmail = credEmail || email;
    const loginPassword = credPassword || password;
    
    if (!loginEmail || !loginPassword) {
      Alert.alert('Error', 'Please enter both email and password');
      return;
    }

    const loadingId = startLoading('Logging in...');
    try {
      const response = await authAPI.login(loginEmail, loginPassword);
      
      if (response.token) {
        await AsyncStorage.setItem('authToken', response.token);
        await AsyncStorage.setItem('userData', JSON.stringify(response.user));
        
        // Save credentials securely for biometric login if not already saved
        if (!skipBiometricSave) {
          const biometricEnabled = await AsyncStorage.getItem('biometricEnabled');
          if (biometricEnabled === 'true') {
            await SecureStore.setItemAsync('userEmail', loginEmail);
            await SecureStore.setItemAsync('userPassword', loginPassword);
          } else {
            // Ask user if they want to enable biometric login
            const hasHardware = await LocalAuthentication.hasHardwareAsync();
            const isEnrolled = await LocalAuthentication.isEnrolledAsync();
            
            if (hasHardware && isEnrolled) {
              const biometricType = Platform.OS === 'ios' ? 'Face ID/Touch ID' : 'Fingerprint/Face Unlock';
              Alert.alert(
                'Enable Biometric Login',
                `Would you like to use ${biometricType} for quick login?`,
                [
                  {
                    text: 'No',
                    style: 'cancel',
                  },
                  {
                    text: 'Yes',
                    onPress: async () => {
                      await SecureStore.setItemAsync('userEmail', loginEmail);
                      await SecureStore.setItemAsync('userPassword', loginPassword);
                      await AsyncStorage.setItem('biometricEnabled', 'true');
                    },
                  },
                ]
              );
            }
          }
        }
        
        // Navigation will be handled automatically by App.js when auth state changes
      }
    } catch (error) {
      Alert.alert('Login Failed', error.response?.data?.message || 'Invalid credentials');
    } finally {
      stopLoading(loadingId);
    }
  };

  const checkBiometric = async () => {
    try {
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();
      const biometricEnabled = await AsyncStorage.getItem('biometricEnabled');

      if (!compatible || !enrolled) {
        Alert.alert('Not Available', 'Biometric authentication is not available on this device');
        return;
      }

      if (biometricEnabled !== 'true') {
        Alert.alert('Not Enabled', 'Please login with email and password first to enable biometric login');
        return;
      }

      const biometricPrompt = Platform.OS === 'ios' ? 'Login with Face ID/Touch ID' : 'Login with biometrics';
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: biometricPrompt,
        cancelLabel: 'Cancel',
        fallbackLabel: 'Use Password',
      });

      if (result.success) {
        const savedEmail = await SecureStore.getItemAsync('userEmail');
        const savedPassword = await SecureStore.getItemAsync('userPassword');
        
        if (savedEmail && savedPassword) {
          // Pass credentials directly to avoid stale state closure issue
          handleLogin(true, savedEmail, savedPassword);
        } else {
          Alert.alert('Error', 'No saved credentials found. Please login with email and password.');
        }
      }
    } catch (error) {
      console.error('Biometric error:', error);
      Alert.alert('Error', 'Biometric authentication failed. Please try again.');
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.content}>
        <Image
          source={require('../assets/logo.png')}
          style={styles.logo}
          resizeMode="contain"
        />
        
        <Text style={styles.title}>Welcome to StoryKeep</Text>
        <Text style={styles.subtitle}>Save Your Family Stories</Text>

        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="Email"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
          />

          <TextInput
            style={styles.input}
            placeholder="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <TouchableOpacity
            style={styles.button}
            onPress={handleLogin}
          >
            <Text style={styles.buttonText}>Login</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={checkBiometric} style={styles.biometricButton}>
            <Text style={styles.biometricText}>
              🔐 Login with {Platform.OS === 'ios' ? 'Face ID' : 'Biometrics'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => navigation.navigate('Register')}>
            <Text style={styles.linkText}>
              Don't have an account? <Text style={styles.linkBold}>Sign Up</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  logo: {
    width: 120,
    height: 120,
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 40,
  },
  form: {
    width: '100%',
  },
  input: {
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#E85D75',
    borderRadius: 10,
    padding: 15,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  biometricButton: {
    marginTop: 15,
    alignItems: 'center',
  },
  biometricText: {
    fontSize: 16,
    color: '#E85D75',
  },
  linkText: {
    textAlign: 'center',
    marginTop: 20,
    fontSize: 16,
    color: '#666',
  },
  linkBold: {
    color: '#E85D75',
    fontWeight: 'bold',
  },
});
