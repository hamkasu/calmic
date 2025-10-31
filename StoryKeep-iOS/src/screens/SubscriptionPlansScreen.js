import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { subscriptionAPI } from '../services/api';

export default function SubscriptionPlansScreen({ navigation }) {
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [plansData, subscriptionData] = await Promise.all([
        subscriptionAPI.getPlans(),
        subscriptionAPI.getCurrentSubscription(),
      ]);

      setPlans(plansData.plans || []);
      setCurrentSubscription(subscriptionData.subscription);
    } catch (error) {
      console.error('Failed to load subscription data:', error);
      Alert.alert('Error', 'Failed to load subscription plans. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan) => {
    // Don't allow upgrading to current plan
    if (plan.is_current) {
      Alert.alert('Current Plan', 'You are already subscribed to this plan.');
      return;
    }

    // Free plan doesn't need upgrade
    if (plan.name === 'Free') {
      Alert.alert('Free Plan', 'This is the free plan. No payment required!');
      return;
    }

    Alert.alert(
      'Upgrade Subscription',
      `Upgrade to ${plan.display_name} for RM ${plan.price_myr.toFixed(2)}/month?\n\nFeatures:\n${plan.features.join('\n')}`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Upgrade',
          onPress: () => processUpgrade(plan),
        },
      ]
    );
  };

  const processUpgrade = async (plan) => {
    try {
      setUpgrading(true);
      const result = await subscriptionAPI.upgradeSubscription(plan.id);

      if (result.dev_mode) {
        // Development mode - subscription created directly
        Alert.alert('Success', result.message, [
          { text: 'OK', onPress: () => loadData() },
        ]);
      } else if (result.checkout_url) {
        // Production mode - open Stripe checkout
        Alert.alert(
          'Payment Required',
          'You will be redirected to Stripe to complete your payment.',
          [
            { text: 'Cancel', style: 'cancel' },
            {
              text: 'Continue',
              onPress: () => {
                Linking.openURL(result.checkout_url);
                Alert.alert(
                  'Return to App',
                  'After completing payment, please return to the app and refresh to see your updated subscription.',
                  [{ text: 'OK', onPress: () => loadData() }]
                );
              },
            },
          ]
        );
      }
    } catch (error) {
      console.error('Upgrade failed:', error);
      Alert.alert(
        'Upgrade Failed',
        error.response?.data?.error || 'Failed to process upgrade. Please try again.'
      );
    } finally {
      setUpgrading(false);
    }
  };

  const renderPlanCard = (plan) => {
    const isCurrentPlan = plan.is_current;
    const isFeatured = plan.is_featured;
    const isFree = plan.price_myr === 0;

    return (
      <View
        key={plan.id}
        style={[
          styles.planCard,
          isCurrentPlan && styles.currentPlanCard,
          isFeatured && styles.featuredPlanCard,
        ]}
      >
        {isFeatured && (
          <View style={styles.featuredBadge}>
            <Ionicons name="star" size={16} color="#fff" />
            <Text style={styles.featuredText}>FEATURED</Text>
          </View>
        )}

        {isCurrentPlan && (
          <View style={styles.currentBadge}>
            <Ionicons name="checkmark-circle" size={16} color="#fff" />
            <Text style={styles.currentText}>CURRENT PLAN</Text>
          </View>
        )}

        <Text style={styles.planName}>{plan.display_name}</Text>

        <View style={styles.priceContainer}>
          {isFree ? (
            <Text style={styles.price}>FREE</Text>
          ) : (
            <>
              <Text style={styles.currency}>RM</Text>
              <Text style={styles.price}>{plan.price_myr.toFixed(2)}</Text>
              <Text style={styles.period}>/month</Text>
            </>
          )}
        </View>

        <View style={styles.featuresContainer}>
          {plan.features.map((feature, index) => (
            <View key={index} style={styles.featureRow}>
              <Ionicons name="checkmark-circle" size={20} color="#4CAF50" />
              <Text style={styles.featureText}>{feature}</Text>
            </View>
          ))}
        </View>

        {!isCurrentPlan && (
          <TouchableOpacity
            style={[
              styles.upgradeButton,
              isFeatured && styles.featuredButton,
              upgrading && styles.disabledButton,
            ]}
            onPress={() => handleUpgrade(plan)}
            disabled={upgrading}
          >
            {upgrading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.upgradeButtonText}>
                {isFree ? 'Current Plan' : 'Upgrade'}
              </Text>
            )}
          </TouchableOpacity>
        )}

        {isCurrentPlan && (
          <View style={styles.currentPlanButton}>
            <Text style={styles.currentPlanButtonText}>Active</Text>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF6B6B" />
        <Text style={styles.loadingText}>Loading subscription plans...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Subscription Plans</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <View style={styles.currentSubscriptionInfo}>
          <Text style={styles.infoTitle}>Current Subscription</Text>
          <Text style={styles.infoText}>
            {currentSubscription?.plan_display_name || 'Free Plan'}
          </Text>
          {!currentSubscription?.is_free && (
            <Text style={styles.infoSubtext}>
              Next billing: {new Date(currentSubscription?.next_billing_date).toLocaleDateString()}
            </Text>
          )}
        </View>

        <Text style={styles.sectionTitle}>Available Plans</Text>
        <Text style={styles.sectionSubtitle}>
          Choose the plan that fits your needs
        </Text>

        {plans.map((plan) => renderPlanCard(plan))}

        <View style={styles.footerInfo}>
          <Text style={styles.footerText}>
            • All prices in Malaysian Ringgit (MYR)
          </Text>
          <Text style={styles.footerText}>
            • Cancel anytime from your account settings
          </Text>
          <Text style={styles.footerText}>
            • Secure payment powered by Stripe
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
    paddingTop: 50,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  backButton: {
    padding: 5,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  currentSubscriptionInfo: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  infoTitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  infoText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  infoSubtext: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 20,
  },
  planCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
    position: 'relative',
  },
  currentPlanCard: {
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  featuredPlanCard: {
    borderWidth: 2,
    borderColor: '#FF6B6B',
  },
  featuredBadge: {
    position: 'absolute',
    top: -10,
    right: 20,
    backgroundColor: '#FF6B6B',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  featuredText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    marginLeft: 4,
  },
  currentBadge: {
    position: 'absolute',
    top: -10,
    right: 20,
    backgroundColor: '#4CAF50',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  currentText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    marginLeft: 4,
  },
  planName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 20,
  },
  currency: {
    fontSize: 18,
    color: '#666',
    marginRight: 4,
  },
  price: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FF6B6B',
  },
  period: {
    fontSize: 16,
    color: '#666',
    marginLeft: 4,
  },
  featuresContainer: {
    marginBottom: 20,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  featureText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 12,
    flex: 1,
  },
  upgradeButton: {
    backgroundColor: '#FF6B6B',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  featuredButton: {
    backgroundColor: '#FF6B6B',
  },
  disabledButton: {
    opacity: 0.5,
  },
  upgradeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  currentPlanButton: {
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  currentPlanButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  footerInfo: {
    marginTop: 24,
    padding: 20,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  footerText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
});
