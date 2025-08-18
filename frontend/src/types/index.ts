// src/types/index.ts
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'owner' | 'admin' | 'member';
  organization_id: string;
}

export interface Organization {
  id: string;
  name: string;
  subscription_tier: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  whatsapp_enabled: boolean;
  whatsapp_number: string;
  sms_enabled: boolean;
  sms_number: string;
  voice_enabled: boolean;
  voice_number: string;
  system_prompt: string;
  welcome_message: string;
  model: string;
  temperature: number;
  max_tokens: number;
  total_conversations: number;
  total_messages: number;
}

export interface Conversation {
  id: string;
  agent_id: string;
  agent_name: string;
  customer_phone: string;
  customer_name?: string;
  channel: 'whatsapp' | 'sms' | 'voice';
  status: 'active' | 'waiting' | 'ended' | 'handed_off';
  started_at: string;
  last_message_at?: string;
  message_count: number;
  handed_off_at?: string;
  assigned_to?: string;
  last_message?: {
    content: string;
    sender_type: string;
    created_at: string;
  };
  metadata?: any;
}

// specific conversation example = /api/conversations/400897cc-30c8-4886-9822-1693e5599795
// {
//   "id": "400897cc-30c8-4886-9822-1693e5599795",
//   "agent_name": "Luron Customer Support",
//   "agent_id": "44438938-4d48-4e9c-980b-1f88a077ce00",
//   "customer_phone": "+17653370203",
//   "customer_name": "",
//   "channel": "whatsapp",
//   "status": "active",
//   "started_at": "2025-08-10T01:41:30.974Z",
//   "ended_at": null,
//   "last_message_at": "2025-08-13T01:50:44.912Z",
//   "message_count": 62,
//   "sentiment_score": 0,
//   "messages": [
//     {
//       "id": "a9ccc090-f7b1-4c91-8720-d7ae41bef2a3",
//       "sender_type": "customer",
//       "content": "Testing whatsapp int",
//       "message_type": "text",
//       "media_url": "",
//       "created_at": "2025-08-10T01:41:31.584Z",
//       "delivered_at": null,
//       "read_at": null
//     }
//   ],
//   "customer_metadata": {},
//   "metadata": {}
// }
export interface AssignedUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
}

export interface SpecificConversation {
  id: string;
  agent_id: string;
  agent_name: string;
  customer_phone: string;
  customer_name?: string;
  channel: string;
  status: string;
  started_at: string;
  ended_at?: string;
  last_message_at?: string;
  message_count: number;
  sentiment_score?: number;
  assigned_to?: AssignedUser | null;  // Add this
  handed_off_at?: string;  // Add this
  messages: Message[];
  customer_metadata?: any;
  metadata?: any;
}


// message example = inside specific conversation
// {
//   "id": "a9ccc090-f7b1-4c91-8720-d7ae41bef2a3",
//   "sender_type": "customer",
//   "content": "Testing whatsapp int",
//   "message_type": "text",
//   "media_url": "",
//   "created_at": "2025-08-10T01:41:31.584Z",
//   "delivered_at": null,
//   "read_at": null
// }

export interface Message {
  id: string;
  sender_type: 'customer' | 'agent' | 'human' | 'system';
  content: string;
  message_type: 'text' | 'image' | 'audio';
  created_at: string;
  delivered_at?: string;
  read_at?: string;
  media_url?: string;
}

export interface WebSocketMessage {
  type: 'conversation_update' | 'new_conversation' | 'conversation_status_changed' | 'error';
  conversation_id?: string;
  update_type?: string;
  data?: any;
  message?: string;
}



export interface SearchParams {
  query?: string;
  status?: string;
  channel?: string;
  agent_id?: string;
  date_from?: string;
  date_to?: string;
  has_handoff?: boolean;
  min_messages?: number;
  max_messages?: number;
  sort_by?: string;
  order?: string;
  limit?: number;
  offset?: number;
}

export interface SearchResponse {
  conversations: Conversation[];
  total: number;
  filtered: number;
  page_size: number;
  page: number;
}