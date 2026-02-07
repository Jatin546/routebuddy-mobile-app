import React from 'react';
import { Stack } from 'expo-router';
import { AuthProvider } from '../contexts/AuthContext';
import { SocketProvider } from '../contexts/SocketContext';

export default function RootLayout() {
  return (
    <AuthProvider>
      <SocketProvider>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="onboarding" />
          <Stack.Screen name="(auth)/login" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="profile-setup" />
          <Stack.Screen name="route-setup" />
          <Stack.Screen name="user-profile" />
          <Stack.Screen name="chat" />
          <Stack.Screen name="verify-id" />
          <Stack.Screen name="report-user" />
        </Stack>
      </SocketProvider>
    </AuthProvider>
  );
}