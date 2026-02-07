import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions, Animated } from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

const slides = [
  {
    title: 'Find Your Route Buddies',
    description: 'Connect with people traveling on the same route as you',
    icon: '🗺️',
  },
  {
    title: 'Safe & Verified',
    description: 'ID verification and safety features to ensure secure connections',
    icon: '🛡️',
  },
  {
    title: 'Chat & Plan Together',
    description: 'Real-time chat to coordinate your commute and plan activities',
    icon: '💬',
  },
];

export default function OnboardingScreen() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const router = useRouter();
  const { colors, isDark } = useTheme();
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;
  const iconScale = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    animateIn();
  }, [currentIndex]);

  const animateIn = () => {
    fadeAnim.setValue(0);
    slideAnim.setValue(50);
    iconScale.setValue(0);

    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.spring(iconScale, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const handleNext = async () => {
    if (currentIndex < slides.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      await AsyncStorage.setItem('hasSeenOnboarding', 'true');
      router.replace('/(auth)/login');
    }
  };

  const handleSkip = async () => {
    await AsyncStorage.setItem('hasSeenOnboarding', 'true');
    router.replace('/(auth)/login');
  };

  const slide = slides[currentIndex];
  const slideColors = ['#6366F1', '#EC4899', '#10B981'];

  return (
    <View style={[styles.container, { backgroundColor: isDark ? colors.card : slideColors[currentIndex] }]}>
      <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
        <Text style={[styles.skipText, { color: isDark ? colors.text : 'white' }]}>Skip</Text>
      </TouchableOpacity>

      <Animated.View 
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ translateY: slideAnim }]
          }
        ]}
      >
        <Animated.Text 
          style={[
            styles.icon,
            {
              transform: [{ scale: iconScale }]
            }
          ]}
        >
          {slide.icon}
        </Animated.Text>
        <Text style={[styles.title, { color: isDark ? colors.text : 'white' }]}>
          {slide.title}
        </Text>
        <Text style={[styles.description, { color: isDark ? colors.textSecondary : 'rgba(255,255,255,0.9)' }]}>
          {slide.description}
        </Text>
      </Animated.View>

      <View style={styles.footer}>
        <View style={styles.pagination}>
          {slides.map((_, index) => (
            <Animated.View
              key={index}
              style={[
                styles.dot,
                {
                  backgroundColor: isDark 
                    ? (index === currentIndex ? colors.primary : colors.border)
                    : (index === currentIndex ? 'white' : 'rgba(255,255,255,0.4)'),
                  width: index === currentIndex ? 24 : 8,
                },
              ]}
            />
          ))}
        </View>

        <TouchableOpacity 
          style={[styles.nextButton, { backgroundColor: isDark ? colors.primary : 'white' }]} 
          onPress={handleNext}
        >
          <Text style={[styles.nextText, { color: isDark ? 'white' : slideColors[currentIndex] }]}>
            {currentIndex === slides.length - 1 ? "Get Started" : "Next"}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 60,
    paddingBottom: 40,
  },
  skipButton: {
    alignSelf: 'flex-end',
    marginRight: 24,
  },
  skipText: {
    fontSize: 16,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  icon: {
    fontSize: 120,
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 16,
  },
  description: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
  },
  footer: {
    paddingHorizontal: 32,
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 32,
  },
  dot: {
    height: 8,
    borderRadius: 4,
    marginHorizontal: 4,
  },
  nextButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  nextText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
});