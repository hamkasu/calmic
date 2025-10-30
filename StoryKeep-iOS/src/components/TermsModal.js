/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
} from 'react-native';

export default function TermsModal({ visible, onClose, onAccept }) {
  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Terms and Conditions</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <Text style={styles.heading}>Welcome to StoryKeep</Text>
            <Text style={styles.paragraph}>
              By using StoryKeep, you agree to the following terms and conditions.
              Please read them carefully.
            </Text>

            <Text style={styles.heading}>1. Acceptance of Terms</Text>
            <Text style={styles.paragraph}>
              By creating an account and using StoryKeep, you accept and agree to be bound
              by these Terms and Conditions. If you do not agree to these terms, please do
              not use our service.
            </Text>

            <Text style={styles.heading}>2. User Content and Privacy</Text>
            <Text style={styles.paragraph}>
              You retain all rights to your photos and content uploaded to StoryKeep. We
              will never share, sell, or use your photos without your explicit permission.
              Your privacy is our top priority.
            </Text>

            <Text style={styles.heading}>3. Storage and Backups</Text>
            <Text style={styles.paragraph}>
              StoryKeep provides secure cloud storage for your family memories. While we
              take every precaution to protect your data, we recommend maintaining your own
              backups of irreplaceable photos.
            </Text>

            <Text style={styles.heading}>4. AI Enhancement</Text>
            <Text style={styles.paragraph}>
              Our AI-powered photo enhancement features are designed to restore and improve
              your photos. Original photos are always preserved and you can revert changes
              at any time.
            </Text>

            <Text style={styles.heading}>5. Account Responsibility</Text>
            <Text style={styles.paragraph}>
              You are responsible for maintaining the confidentiality of your account
              credentials. Please notify us immediately of any unauthorized access.
            </Text>

            <Text style={styles.heading}>6. Prohibited Use</Text>
            <Text style={styles.paragraph}>
              You may not use StoryKeep for any illegal purposes or to upload content that
              violates copyright, privacy, or other rights of third parties.
            </Text>

            <Text style={styles.heading}>7. Modifications</Text>
            <Text style={styles.paragraph}>
              We may update these terms from time to time. Continued use of StoryKeep after
              changes constitutes acceptance of the updated terms.
            </Text>

            <Text style={styles.heading}>8. Contact Us</Text>
            <Text style={styles.paragraph}>
              If you have questions about these terms, please contact us through the app
              or email support@storykeep.com.
            </Text>

            <Text style={styles.lastUpdated}>
              Last updated: October 2025
            </Text>
          </ScrollView>

          <View style={styles.modalFooter}>
            <TouchableOpacity style={styles.declineButton} onPress={onClose}>
              <Text style={styles.declineButtonText}>Close</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.acceptButton}
              onPress={() => {
                onAccept();
                onClose();
              }}
            >
              <Text style={styles.acceptButtonText}>Accept</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '85%',
    paddingBottom: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  closeButton: {
    padding: 5,
  },
  closeButtonText: {
    fontSize: 24,
    color: '#666',
  },
  modalContent: {
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  heading: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 15,
    marginBottom: 8,
  },
  paragraph: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 10,
  },
  lastUpdated: {
    fontSize: 12,
    color: '#999',
    fontStyle: 'italic',
    marginTop: 20,
    marginBottom: 10,
  },
  modalFooter: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingTop: 15,
    gap: 10,
  },
  declineButton: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    padding: 15,
    alignItems: 'center',
  },
  declineButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  acceptButton: {
    flex: 1,
    backgroundColor: '#E85D75',
    borderRadius: 10,
    padding: 15,
    alignItems: 'center',
  },
  acceptButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
