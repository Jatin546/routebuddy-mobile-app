import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Image,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../contexts/AuthContext';
import { useSocket } from '../contexts/SocketContext';
import { api } from '../utils/api';

interface Message {
  message_id: string;
  sender_id: string;
  receiver_id: string;
  content: string;
  timestamp: string;
  read: boolean;
}

export default function ChatScreen() {
  const router = useRouter();
  const { userId, name } = useLocalSearchParams<{ userId: string; name: string }>();
  const { user } = useAuth();
  const { socket } = useSocket();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    loadMessages();

    // Listen for real-time messages
    if (socket) {
      socket.on('receive_message', (message: Message) => {
        if (message.sender_id === userId) {
          setMessages((prev) => [...prev, message]);
          scrollToBottom();
        }
      });
    }

    return () => {
      if (socket) {
        socket.off('receive_message');
      }
    };
  }, [socket, userId]);

  const loadMessages = async () => {
    try {
      const data = await api.get(`/api/messages/conversation/${userId}`);
      setMessages(data);
      scrollToBottom();
      
      // Mark messages as read
      await api.post(`/api/messages/mark-read/${userId}`, {});
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const messageContent = inputText.trim();
    setInputText('');

    // Optimistic UI update
    const tempMessage: Message = {
      message_id: `temp_${Date.now()}`,
      sender_id: user!.user_id,
      receiver_id: userId,
      content: messageContent,
      timestamp: new Date().toISOString(),
      read: false,
    };
    setMessages((prev) => [...prev, tempMessage]);
    scrollToBottom();

    try {
      if (socket) {
        socket.emit('send_message', {
          sender_id: user!.user_id,
          receiver_id: userId,
          content: messageContent,
        });
      } else {
        await api.post('/api/messages/send', {
          receiver_id: userId,
          content: messageContent,
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={0}
    >
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#1F2937" />
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.headerCenter}
          onPress={() => router.push(`/user-profile?userId=${userId}`)}
        >
          <Text style={styles.headerTitle}>{name}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => router.push(`/report-user?userId=${userId}`)}>
          <Ionicons name="ellipsis-vertical" size={24} color="#1F2937" />
        </TouchableOpacity>
      </View>

      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
      >
        {messages.map((message) => {
          const isMe = message.sender_id === user?.user_id;
          return (
            <View
              key={message.message_id}
              style={[styles.messageRow, isMe && styles.messageRowMe]}
            >
              <View style={[styles.messageBubble, isMe && styles.messageBubbleMe]}>
                <Text style={[styles.messageText, isMe && styles.messageTextMe]}>
                  {message.content}
                </Text>
                <Text style={[styles.messageTime, isMe && styles.messageTimeMe]}>
                  {formatTime(message.timestamp)}
                </Text>
              </View>
            </View>
          );
        })}
      </ScrollView>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type a message..."
          placeholderTextColor="#9CA3AF"
          multiline
          maxLength={500}
        />
        <TouchableOpacity style={styles.sendButton} onPress={sendMessage}>
          <Ionicons name="send" size={20} color="white" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
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
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
  },
  messageRow: {
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  messageRowMe: {
    alignItems: 'flex-end',
  },
  messageBubble: {
    maxWidth: '75%',
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  messageBubbleMe: {
    backgroundColor: '#6366F1',
  },
  messageText: {
    fontSize: 16,
    color: '#1F2937',
    marginBottom: 4,
  },
  messageTextMe: {
    color: 'white',
  },
  messageTime: {
    fontSize: 11,
    color: '#9CA3AF',
  },
  messageTimeMe: {
    color: 'rgba(255,255,255,0.8)',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 16,
    backgroundColor: 'white',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  input: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    color: '#1F2937',
    maxHeight: 100,
    marginRight: 8,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#6366F1',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
