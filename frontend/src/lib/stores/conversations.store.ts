// src/lib/stores/conversations.store.ts (updated with toast notifications)
import { create } from 'zustand';
import { Conversation, Message } from '@/types';
import { apiClient } from '@/lib/api/client';
import { wsService } from '@/lib/websocket';
import { toast } from 'sonner';

interface ConversationsState {
  conversations: Conversation[];
  activeConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  fetchConversations: () => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
}

export const useConversationsStore = create<ConversationsState>((set, get) => ({
  conversations: [],
  activeConversation: null,
  messages: [],
  isLoading: false,

  fetchConversations: async () => {
    set({ isLoading: true });
    try {
      const response = await apiClient.get('/conversations');
      set({ conversations: response.data, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      toast.error('Failed to load conversations');
      set({ isLoading: false });
    }
  },

  selectConversation: async (id: string) => {
    set({ isLoading: true });
    try {
      const response = await apiClient.get(`/conversations/${id}`);
      set({ 
        activeConversation: response.data.conversation,
        messages: response.data.messages,
        isLoading: false 
      });
    } catch (error) {
      console.error('Failed to fetch conversation:', error);
      toast.error('Failed to load conversation details');
      set({ isLoading: false });
    }
  },

  sendMessage: async (content: string) => {
    const { activeConversation } = get();
    if (!activeConversation) return;

    const toastId = toast.loading('Sending message...');
    
    try {
      await apiClient.post(`/conversations/${activeConversation.id}/messages`, {
        content,
      });
      toast.success('Message sent', { id: toastId });
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message', { id: toastId });
    }
  },
}));

// Listen to WebSocket events and show notifications
wsService.on('conversation_update', (data) => {
  const store = useConversationsStore.getState();
  
  // Show notification for new messages
  if (data.update_type === 'new_message' && data.data?.messages?.[0]) {
    const latestMessage = data.data.messages[0];
    if (latestMessage.sender_type === 'customer') {
      toast.info('New message', {
        description: `${data.data.customer_phone}: ${latestMessage.content.substring(0, 50)}...`,
      });
    }
  }
  
  // Update conversation in list
  const updatedConversations = store.conversations.map(conv =>
    conv.id === data.conversation_id
      ? { ...conv, ...data.data }
      : conv
  );
  
  useConversationsStore.setState({ conversations: updatedConversations });
  
  // Update messages if this is the active conversation
  if (store.activeConversation?.id === data.conversation_id && data.data?.messages) {
    const newMessages = [...data.data.messages, ...store.messages];
    useConversationsStore.setState({ messages: newMessages });
  }
});

wsService.on('new_conversation', (data) => {
  const store = useConversationsStore.getState();
  
  // Show notification for new conversation
  toast.success('New conversation started', {
    description: `From ${data.conversation.customer_phone}`,
  });
  
  useConversationsStore.setState({
    conversations: [data.conversation, ...store.conversations],
  });
});