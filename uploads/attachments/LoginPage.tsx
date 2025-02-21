import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, StyleSheet, Pressable, Animated, Modal, TouchableOpacity, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationPropType } from '../../type';
import Icon from 'react-native-vector-icons/FontAwesome'; // Import FontAwesome icons
import axios from 'axios';

const API_BASE_URL = 'http://192.168.0.103:8000/api'; // Update base URL

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');

  const navigation = useNavigation<StackNavigationPropType>();

  const scaleAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(scaleAnim, {
          toValue: 1.2,
          duration: 500,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [scaleAnim]);

  const handleLogin = async () => {
    if (email === '') {
      Alert.alert('', 'Email is required.');
      return;
    }
  
    if (password === '') {
      Alert.alert('', 'Password is required.');
      return;
    }
  
    try {
      const response = await axios.post(`${API_BASE_URL}/login/`, { username: email, password });
      const { role } = response.data; // Make sure your API returns a 'role' or similar field
  
      if (role === 'ADMIN') {
        Alert.alert('Success', 'Login successful.', [
          {
            text: 'OK',
            onPress: () => {
              // Clear the form fields
              setEmail('');
              setPassword('');
              // Navigate to AdminAccessMenu
              navigation.navigate('AddPatientProfile');
            },
          },
        ]);
      
      } else if (role === 'PATIENT') {
        Alert.alert('Success', 'Login successful.', [
          {
            text: 'OK',
            onPress: () => {
              setEmail('');
              setPassword('');
              navigation.navigate('DisclaimerPage');
            },
          },
        ]);
      } else {
        Alert.alert('Access Denied', 'You do not have access to this application.', [
          {
            text: 'OK',
            onPress: () => {
              // Clear the form fields
              setEmail('');
              setPassword('');
            },
          },
        ]);
      }
    } catch (error) {
      console.error('Login Error:', error.response ? error.response.data : error.message);
      Alert.alert('Login Failed', 'Invalid credentials.', [
        {
          text: 'OK',
          onPress: () => {
            // Clear the form fields
            setEmail('');
            setPassword('');
          },
        },
      ]);
    }
  };
  
  

  const closeModal = () => {
    setModalVisible(false);
  };

  return (
    <View style={styles.container}>
      <Animated.View style={[styles.iconContainer, { transform: [{ scale: scaleAnim }] }]}>
        <Icon name="heartbeat" size={50} color="#1E90FF" />
      </Animated.View>

      <View style={styles.innerContainer}>
        <Text style={styles.title}>Login</Text>
        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor="#888"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#888"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <Pressable style={styles.button} onPress={handleLogin}>
          <Text style={styles.buttonText}>Log In</Text>
        </Pressable>
        <View style={styles.footer}>
          <Text style={styles.footerText}>Don't have an account?</Text>
          <Pressable>
            <Text style={styles.footerLink}>Sign Up</Text>
          </Pressable>
        </View>
      </View>

      <Modal
        transparent={true}
        visible={modalVisible}
        animationType="slide"
        onRequestClose={closeModal}
      >
        <View style={styles.modalBackground}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalText}>{alertMessage}</Text>
            <TouchableOpacity style={styles.modalButton} onPress={closeModal}>
              <Text style={styles.modalButtonText}>OK</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};
const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#F0F0F0',
  },
  iconContainer: {
    marginBottom: 40,
    alignItems: 'center',
  },
  innerContainer: {
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 40,
  },
  input: {
    width: '100%',
    height: 50,
    borderColor: '#ddd',
    borderWidth: 1,
    borderRadius: 15,
    paddingHorizontal: 15,
    marginBottom: 20,
    backgroundColor: '#fff',
    fontSize: 16,
    color: '#333',
  },
  button: {
    width: '50%',
    height: 50,
    backgroundColor: '#1E90FF',
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  buttonText: {
    fontSize: 18,
    color: '#fff',
    fontWeight: 'bold',
  },
  footer: {
    marginTop: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 16,
    color: '#555',
  },
  footerLink: {
    fontSize: 16,
    color: '#1E90FF',
    fontWeight: 'bold',
    marginTop: 5,
  },
  modalBackground: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContainer: {
    width: 300,
    padding: 25,
    backgroundColor: '#fff',
    borderRadius: 30,
    alignItems: 'center',
  },
  modalText: {
    fontSize: 18,
    marginBottom: 20,
    textAlign: 'center',
  },
  modalButton: {
    backgroundColor: '#1E90FF',
    padding: 10,
    borderRadius: 5,
  },
  modalButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default LoginPage;
