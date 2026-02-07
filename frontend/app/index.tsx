import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function SplashScreen() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const { colors, isDark } = useTheme();
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.3)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Start animations
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 10,
        friction: 3,
        useNativeDriver: true,
      }),
    ]).start();

    // Pulse animation loop
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Navigation logic
    const checkOnboarding = async () => {
      if (!loading) {
        const hasSeenOnboarding = await AsyncStorage.getItem('hasSeenOnboarding');
        
        if (!user) {
          if (hasSeenOnboarding) {
            router.replace('/(auth)/login');
          } else {
            router.replace('/onboarding');
          }
        } else {
          router.replace('/(tabs)/discover');
        }
      }
    };

    const timer = setTimeout(checkOnboarding, 2500);
    return () => clearTimeout(timer);
  }, [loading, user]);

  return (
    <View style={[styles.container, { backgroundColor: isDark ? colors.card : colors.primary }]}>
      <Animated.View 
        style={[
          styles.logoContainer,
          {
            opacity: fadeAnim,
            transform: [{ scale: scaleAnim }]
          }
        ]}
      >
        <Animated.View 
          style={[
            styles.logo,
            {
              backgroundColor: isDark ? colors.primary : 'white',
              transform: [{ scale: pulseAnim }]
            }
          ]}
        >
          <Text style={styles.logoText}>🚗</Text>
        </Animated.View>
        <Animated.Text 
          style={[
            styles.title,
            { 
              color: isDark ? colors.text : 'white',
              opacity: fadeAnim 
            }
          ]}
        >
          RouteBuddy
        </Animated.Text>
        <Animated.Text 
          style={[
            styles.subtitle,
            { 
              color: isDark ? colors.textSecondary : 'rgba(255,255,255,0.9)',
              opacity: fadeAnim 
            }
          ]}
        >
          Find Your Commute Companion
        </Animated.Text>
      </Animated.View>
      
      {/* Loading indicator */}
      <Animated.View style={{ opacity: fadeAnim, marginTop: 40 }}>
        <View style={styles.loadingDots}>
          {[0, 1, 2].map((i) => (
            <Animated.View
              key={i}
              style={[
                styles.dot,
                { 
                  backgroundColor: isDark ? colors.primary : 'rgba(255,255,255,0.8)',
                }
              ]}
            />
          ))}
        </View>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
  },
  logo: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 12,
  },
  logoText: {
    fontSize: 56,
  },
  title: {
    fontSize: 42,
    fontWeight: 'bold',
    marginBottom: 8,
    letterSpacing: -1,
  },
  subtitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  loadingDots: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginHorizontal: 4,
  },
});