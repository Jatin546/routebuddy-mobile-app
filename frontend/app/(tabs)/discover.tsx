import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  Image,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../utils/api';

interface MatchedUser {
  user_id: string;
  name: string;
  picture?: string;
  bio?: string;
  verified: boolean;
  route_match_score: number;
  distance_to_start: number;
  distance_to_end: number;
}

export default function DiscoverScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [matches, setMatches] = useState<MatchedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [hasRoute, setHasRoute] = useState(false);

  useEffect(() => {
    loadMatches();
    checkUserRoute();
  }, []);

  const checkUserRoute = async () => {
    try {
      const routes = await api.get('/api/routes/my-routes');
      setHasRoute(routes.length > 0);
    } catch (error) {
      console.error('Error checking routes:', error);
    }
  };

  const loadMatches = async () => {
    try {
      const data = await api.get('/api/discovery/matches');
      setMatches(data);
    } catch (error) {
      console.error('Error loading matches:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadMatches();
  };

  const handleConnect = async (userId: string) => {
    try {
      await api.post('/api/connections/request', { target_user_id: userId });
      Alert.alert('Success', 'Connection request sent!');
      loadMatches();
    } catch (error) {
      Alert.alert('Error', 'Failed to send connection request');
    }
  };

  if (!hasRoute && !loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Discover</Text>
        </View>
        
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>🗺️</Text>
          <Text style={styles.emptyTitle}>Set up your route first</Text>
          <Text style={styles.emptyText}>
            Add your commute route to discover people traveling on the same path
          </Text>
          <TouchableOpacity
            style={styles.setupButton}
            onPress={() => router.push('/route-setup')}
          >
            <Text style={styles.setupButtonText}>Add Route</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Discover Route Buddies</Text>
        <TouchableOpacity onPress={() => router.push('/route-setup')}>
          <Ionicons name="add-circle" size={28} color="#6366F1" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {matches.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>🔍</Text>
            <Text style={styles.emptyTitle}>No matches yet</Text>
            <Text style={styles.emptyText}>
              Check back later or try adjusting your route
            </Text>
          </View>
        ) : (
          matches.map((match) => (
            <TouchableOpacity
              key={match.user_id}
              style={styles.matchCard}
              onPress={() => router.push(`/user-profile?userId=${match.user_id}`)}
            >
              <View style={styles.matchHeader}>
                <View style={styles.userInfo}>
                  {match.picture ? (
                    <Image source={{ uri: match.picture }} style={styles.avatar} />
                  ) : (
                    <View style={[styles.avatar, styles.avatarPlaceholder]}>
                      <Text style={styles.avatarText}>
                        {match.name.charAt(0).toUpperCase()}
                      </Text>
                    </View>
                  )}
                  <View style={styles.userDetails}>
                    <View style={styles.nameRow}>
                      <Text style={styles.userName}>{match.name}</Text>
                      {match.verified && (
                        <Ionicons name="checkmark-circle" size={16} color="#10B981" />
                      )}
                    </View>
                    {match.bio && (
                      <Text style={styles.userBio} numberOfLines={2}>
                        {match.bio}
                      </Text>
                    )}
                  </View>
                </View>
              </View>

              <View style={styles.matchStats}>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{match.route_match_score}%</Text>
                  <Text style={styles.statLabel}>Match</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{match.distance_to_start.toFixed(1)} km</Text>
                  <Text style={styles.statLabel}>Start Distance</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{match.distance_to_end.toFixed(1)} km</Text>
                  <Text style={styles.statLabel}>End Distance</Text>
                </View>
              </View>

              <TouchableOpacity
                style={styles.connectButton}
                onPress={() => handleConnect(match.user_id)}
              >
                <Ionicons name="person-add" size={18} color="white" />
                <Text style={styles.connectButtonText}>Connect</Text>
              </TouchableOpacity>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  matchCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  matchHeader: {
    marginBottom: 16,
  },
  userInfo: {
    flexDirection: 'row',
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    marginRight: 12,
  },
  avatarPlaceholder: {
    backgroundColor: '#DBEAFE',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2563EB',
  },
  userDetails: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  userName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
    marginRight: 6,
  },
  userBio: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  matchStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#E5E7EB',
    marginBottom: 12,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6366F1',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  connectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#6366F1',
    paddingVertical: 12,
    borderRadius: 8,
  },
  connectButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
    paddingHorizontal: 32,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  setupButton: {
    marginTop: 24,
    backgroundColor: '#6366F1',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 8,
  },
  setupButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});
