import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { StatusBar, Platform, BackHandler, Alert } from 'react-native';

import { LoadingProvider } from './src/contexts/LoadingContext';
import LoadingOverlay from './src/components/LoadingOverlay';

import SplashScreen from './src/screens/SplashScreen';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import CameraScreen from './src/screens/CameraScreen';
import GalleryScreen from './src/screens/GalleryScreen';
import PhotoDetailScreen from './src/screens/PhotoDetailScreen';
import FamilyVaultsScreen from './src/screens/FamilyVaultsScreen';
import VaultDetailScreen from './src/screens/VaultDetailScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import EnhancePhotoScreen from './src/screens/EnhancePhotoScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Dashboard') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Camera') {
            iconName = focused ? 'camera' : 'camera-outline';
          } else if (route.name === 'Gallery') {
            iconName = focused ? 'images' : 'images-outline';
          } else if (route.name === 'Vaults') {
            iconName = focused ? 'people' : 'people-outline';
          } else if (route.name === 'Settings') {
            iconName = focused ? 'settings' : 'settings-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#E85D75',
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Camera" component={CameraScreen} />
      <Tab.Screen name="Gallery" component={GalleryScreen} />
      <Tab.Screen name="Vaults" component={FamilyVaultsScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    checkAuthStatus();
    
    // Check auth status periodically (500ms is responsive but not battery-draining)
    const interval = setInterval(checkAuthStatus, 500);
    return () => clearInterval(interval);
  }, []);

  // Android back button handling
  useEffect(() => {
    if (Platform.OS === 'android') {
      const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
        if (!isAuthenticated) {
          // If on login/register screen, confirm exit
          Alert.alert(
            'Exit App',
            'Are you sure you want to exit?',
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Exit', onPress: () => BackHandler.exitApp() }
            ]
          );
          return true; // Prevent default back behavior
        }
        return false; // Allow default back behavior when authenticated
      });

      return () => backHandler.remove();
    }
  }, [isAuthenticated]);

  const checkAuthStatus = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const newAuthState = !!token;
      // Always update state based on current token presence
      setIsAuthenticated(newAuthState);
    } catch (error) {
      console.error('Error checking auth status:', error);
    } finally {
      if (isLoading) {
        setIsLoading(false);
      }
    }
  };

  const handleSplashFinish = () => {
    setShowSplash(false);
  };

  if (isLoading) {
    return null;
  }

  if (showSplash) {
    return <SplashScreen onFinish={handleSplashFinish} />;
  }

  return (
    <LoadingProvider>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <StatusBar 
          barStyle="dark-content" 
          backgroundColor="#ffffff"
          translucent={false}
        />
        <NavigationContainer>
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            {!isAuthenticated ? (
              <>
                <Stack.Screen name="Login" component={LoginScreen} />
                <Stack.Screen name="Register" component={RegisterScreen} />
              </>
            ) : (
              <>
                <Stack.Screen name="Main" component={MainTabs} />
                <Stack.Screen name="PhotoDetail" component={PhotoDetailScreen} />
                <Stack.Screen name="VaultDetail" component={VaultDetailScreen} />
                <Stack.Screen name="Profile" component={ProfileScreen} />
                <Stack.Screen name="EnhancePhoto" component={EnhancePhotoScreen} />
              </>
            )}
          </Stack.Navigator>
        </NavigationContainer>
        <LoadingOverlay />
      </GestureHandlerRootView>
    </LoadingProvider>
  );
}
