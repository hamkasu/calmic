/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authAPI } from '../services/api';
import { useLoading } from '../contexts/LoadingContext';
import TermsModal from '../components/TermsModal';

export default function RegisterScreen({ navigation }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const { startLoading, stopLoading } = useLoading();

  // Field-specific error states
  const [usernameError, setUsernameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');

  // Password strength tracking
  const [passwordStrength, setPasswordStrength] = useState({
    score: 0,
    label: '',
    color: '#ccc',
  });

  // Real-time username validation
  useEffect(() => {
    if (!username) {
      setUsernameError('');
      return;
    }

    if (username.length < 3) {
      setUsernameError('Username must be at least 3 characters');
    } else if (username.length > 20) {
      setUsernameError('Username must be 20 characters or less');
    } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      setUsernameError('Only letters, numbers, and underscores allowed');
    } else {
      setUsernameError('');
    }
  }, [username]);

  // Real-time email validation
  useEffect(() => {
    if (!email) {
      setEmailError('');
      return;
    }

    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(email)) {
      setEmailError('Please enter a valid email address');
    } else {
      setEmailError('');
    }
  }, [email]);

  // Real-time password strength calculation
  useEffect(() => {
    if (!password) {
      setPasswordStrength({ score: 0, label: '', color: '#ccc' });
      setPasswordError('');
      return;
    }

    let score = 0;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

    // Check password length
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    
    // Check character variety
    if (hasUpperCase) score++;
    if (hasLowerCase) score++;
    if (hasNumber) score++;
    if (hasSpecial) score++;

    // Determine strength
    let strength = { score: 0, label: '', color: '#ccc' };
    if (score <= 2) {
      strength = { score: 1, label: 'Weak', color: '#ff4444' };
    } else if (score <= 4) {
      strength = { score: 2, label: 'Fair', color: '#ffaa00' };
    } else if (score <= 5) {
      strength = { score: 3, label: 'Good', color: '#00cc44' };
    } else {
      strength = { score: 4, label: 'Strong', color: '#00aa00' };
    }

    setPasswordStrength(strength);

    // Validate minimum requirements (8 chars minimum)
    if (password.length < 8) {
      setPasswordError('Password must be at least 8 characters');
    } else if (!hasUpperCase) {
      setPasswordError('Add at least one uppercase letter');
    } else if (!hasLowerCase) {
      setPasswordError('Add at least one lowercase letter');
    } else if (!hasNumber) {
      setPasswordError('Add at least one number');
    } else {
      setPasswordError('');
    }
  }, [password]);

  // Real-time confirm password validation
  useEffect(() => {
    if (!confirmPassword) {
      setConfirmPasswordError('');
      return;
    }

    if (password !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match');
    } else {
      setConfirmPasswordError('');
    }
  }, [password, confirmPassword]);

  const handleRegister = async () => {
    // Final validation before submission
    if (!username) {
      Alert.alert('Missing Information', 'Please enter a username');
      return;
    }

    if (usernameError) {
      Alert.alert('Invalid Username', usernameError);
      return;
    }

    if (!email) {
      Alert.alert('Missing Information', 'Please enter your email address');
      return;
    }

    if (emailError) {
      Alert.alert('Invalid Email', emailError);
      return;
    }

    if (!password) {
      Alert.alert('Missing Information', 'Please enter a password');
      return;
    }

    if (passwordError) {
      Alert.alert('Weak Password', passwordError);
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    if (!termsAccepted) {
      Alert.alert('Terms Required', 'Please accept the Terms and Conditions to continue');
      return;
    }

    const loadingId = startLoading('Creating account...');
    try {
      const response = await authAPI.register(username, email, password, termsAccepted);
      
      if (response.token) {
        await AsyncStorage.setItem('authToken', response.token);
        await AsyncStorage.setItem('userData', JSON.stringify(response.user));
        
        Alert.alert('Success', 'Account created successfully! Welcome to StoryKeep!');
        // Navigation will be handled automatically by App.js when auth state changes
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Registration failed. Please try again.';
      const errorField = error.response?.data?.field;

      // Show field-specific errors
      if (errorField === 'username') {
        setUsernameError(errorMessage);
      } else if (errorField === 'email') {
        setEmailError(errorMessage);
      } else if (errorField === 'password') {
        setPasswordError(errorMessage);
      }

      Alert.alert('Registration Failed', errorMessage);
    } finally {
      stopLoading(loadingId);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.content}>
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>Join StoryKeep to preserve your family memories</Text>

          <View style={styles.form}>
            {/* Username Input */}
            <View style={styles.inputContainer}>
              <TextInput
                style={[styles.input, usernameError && styles.inputError]}
                placeholder="Username"
                value={username}
                onChangeText={setUsername}
                autoCapitalize="none"
                autoCorrect={false}
              />
              {usernameError ? (
                <Text style={styles.errorText}>✕ {usernameError}</Text>
              ) : username.length >= 3 && !usernameError ? (
                <Text style={styles.successText}>✓ Username looks good</Text>
              ) : null}
            </View>

            {/* Email Input */}
            <View style={styles.inputContainer}>
              <TextInput
                style={[styles.input, emailError && styles.inputError]}
                placeholder="Email"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
                autoCorrect={false}
              />
              {emailError ? (
                <Text style={styles.errorText}>✕ {emailError}</Text>
              ) : email && !emailError ? (
                <Text style={styles.successText}>✓ Email is valid</Text>
              ) : null}
            </View>

            {/* Password Input */}
            <View style={styles.inputContainer}>
              <TextInput
                style={[styles.input, passwordError && styles.inputError]}
                placeholder="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoCorrect={false}
              />
              
              {/* Password Strength Indicator */}
              {password.length > 0 && (
                <View style={styles.strengthContainer}>
                  <View style={styles.strengthBars}>
                    {[1, 2, 3, 4].map((bar) => (
                      <View
                        key={bar}
                        style={[
                          styles.strengthBar,
                          bar <= passwordStrength.score && { backgroundColor: passwordStrength.color },
                        ]}
                      />
                    ))}
                  </View>
                  <Text style={[styles.strengthLabel, { color: passwordStrength.color }]}>
                    {passwordStrength.label}
                  </Text>
                </View>
              )}

              {passwordError ? (
                <Text style={styles.errorText}>✕ {passwordError}</Text>
              ) : password.length >= 8 && !passwordError ? (
                <Text style={styles.successText}>✓ Password meets requirements</Text>
              ) : (
                <Text style={styles.hintText}>
                  Minimum 8 characters with uppercase, lowercase, and numbers
                </Text>
              )}
            </View>

            {/* Confirm Password Input */}
            <View style={styles.inputContainer}>
              <TextInput
                style={[styles.input, confirmPasswordError && styles.inputError]}
                placeholder="Confirm Password"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry
                autoCorrect={false}
              />
              {confirmPasswordError ? (
                <Text style={styles.errorText}>✕ {confirmPasswordError}</Text>
              ) : confirmPassword && !confirmPasswordError ? (
                <Text style={styles.successText}>✓ Passwords match</Text>
              ) : null}
            </View>

            {/* Terms and Conditions */}
            <TouchableOpacity
              style={styles.termsContainer}
              onPress={() => setTermsAccepted(!termsAccepted)}
            >
              <View style={[styles.checkbox, termsAccepted && styles.checkboxChecked]}>
                {termsAccepted && <Text style={styles.checkmark}>✓</Text>}
              </View>
              <Text style={styles.termsText}>
                I accept the{' '}
                <Text
                  style={styles.termsLink}
                  onPress={(e) => {
                    e.stopPropagation();
                    setShowTermsModal(true);
                  }}
                >
                  Terms and Conditions
                </Text>
              </Text>
            </TouchableOpacity>

            {/* Sign Up Button */}
            <TouchableOpacity
              style={[
                styles.button,
                (!username || !email || !password || !confirmPassword || !termsAccepted || 
                  usernameError || emailError || passwordError || confirmPasswordError) && 
                styles.buttonDisabled
              ]}
              onPress={handleRegister}
            >
              <Text style={styles.buttonText}>Create Account</Text>
            </TouchableOpacity>

            {/* Login Link */}
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={styles.linkText}>
                Already have an account? <Text style={styles.linkBold}>Login</Text>
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>

      {/* Terms Modal */}
      <TermsModal
        visible={showTermsModal}
        onClose={() => setShowTermsModal(false)}
        onAccept={() => setTermsAccepted(true)}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 30,
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  inputContainer: {
    marginBottom: 15,
  },
  input: {
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  inputError: {
    borderColor: '#ff4444',
    backgroundColor: '#fff5f5',
  },
  errorText: {
    color: '#ff4444',
    fontSize: 12,
    marginTop: 5,
    marginLeft: 5,
  },
  successText: {
    color: '#00cc44',
    fontSize: 12,
    marginTop: 5,
    marginLeft: 5,
  },
  hintText: {
    color: '#999',
    fontSize: 12,
    marginTop: 5,
    marginLeft: 5,
    lineHeight: 16,
  },
  strengthContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingHorizontal: 5,
  },
  strengthBars: {
    flexDirection: 'row',
    gap: 4,
    flex: 1,
  },
  strengthBar: {
    flex: 1,
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
  },
  strengthLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 10,
    minWidth: 50,
  },
  button: {
    backgroundColor: '#E85D75',
    borderRadius: 10,
    padding: 15,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
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
  termsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
    marginTop: 5,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 4,
    marginRight: 10,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  checkboxChecked: {
    borderColor: '#E85D75',
    backgroundColor: '#E85D75',
  },
  checkmark: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  termsText: {
    flex: 1,
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  termsLink: {
    color: '#E85D75',
    fontWeight: 'bold',
    textDecorationLine: 'underline',
  },
});
