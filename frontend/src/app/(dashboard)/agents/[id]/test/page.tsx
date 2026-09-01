// src/app/(dashboard)/agents/[id]/test/page.tsx
'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowLeft,
  Send,
  Phone,
  Mic,
  MicOff,
  Bot,
  User,
  Loader2,
  Play,
  Volume2,
  Settings,
  Save,
  RefreshCw,
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

interface VoiceOption {
  voice_id: string;
  name: string;
  category: string;
  description: string;
  preview_url: string;
  labels: Record<string, any>;
}

export default function AgentTestPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  const [agent, setAgent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sending, setSending] = useState(false);
  
  // Voice related states
  const [availableVoices, setAvailableVoices] = useState<VoiceOption[]>([]);
  const [selectedVoiceId, setSelectedVoiceId] = useState<string>('');
  const [voiceText, setVoiceText] = useState('Hello! I am your AI assistant. How can I help you today?');
  const [playingVoice, setPlayingVoice] = useState(false);
  const [loadingVoices, setLoadingVoices] = useState(false);
  const [savingVoice, setSavingVoice] = useState(false);
  
  const [testPhoneNumber, setTestPhoneNumber] = useState('');
  const [calling, setCalling] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    fetchAgent();
    fetchAvailableVoices();
  }, [agentId]);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const fetchAgent = async () => {
    try {
      const response = await apiClient.get(`/agents/${agentId}`);
      setAgent(response.data);
      
      // Set the current voice if it exists
      if (response.data.voice_id) {
        setSelectedVoiceId(response.data.voice_id);
      }
      
      // Add welcome message
      setMessages([
        {
          id: '1',
          role: 'agent',
          content: response.data.welcome_message || 'Hello! How can I help you today?',
          timestamp: new Date(),
        }
      ]);
    } catch (error) {
      toast.error('Failed to load agent');
      router.push('/agents');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    const conversationHistory = messages.map(msg => ({
      sender_type: msg.role === 'user' ? 'customer' : 'assistant',
      content: msg.content,
    }));
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setSending(true);
    
    try {
      const response = await apiClient.post(`/agents/${agentId}/test-chat`, {
        message: inputMessage,
        conversation_history: conversationHistory,
      });
      
      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: response.data.agent_response,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, agentMessage]);
      
      if (response.data.tokens_used) {
        toast.info(`Tokens used: ${response.data.tokens_used}`);
      }
    } catch (error) {
      toast.error('Failed to get response');
    } finally {
      setSending(false);
    }
  };
  
  const fetchAvailableVoices = async (forceRefresh: boolean = false) => {
    setLoadingVoices(true);
    try {
      const response = await apiClient.get('/agents/voices', {
        params: { force_refresh: forceRefresh }
      });
      setAvailableVoices(response.data);
      
      // If agent doesn't have a voice set and we have voices available, select the first one
      if (!selectedVoiceId && response.data.length > 0) {
        setSelectedVoiceId(response.data[0].voice_id);
      }
    } catch (error) {
      toast.error('Failed to load available voices');
      console.error('Error fetching voices:', error);
    } finally {
      setLoadingVoices(false);
    }
  };

  const handleVoicePreview = async () => {
  if (!selectedVoiceId) {
    toast.error('Please select a voice first');
    return;
  }
  
  setPlayingVoice(true);
  
  // Clean up previous audio if it exists
  if (audioRef.current) {
    audioRef.current.pause();
    audioRef.current = null;
  }

  try {
    const response = await apiClient.post(`/agents/${agentId}/preview-voice`, {
      text: voiceText,
      voice_id: selectedVoiceId,
    });
    //console.log('Response data:', response.data); // Add this


    const { audio_url } = response.data;
    //console.log('Audio URL format:', audio_url?.substring(0, 50)); // Check the format

    
    if (audio_url) {
      // Direct playback of base64 audio
      const audio = new Audio(audio_url);
      audioRef.current = audio;
      
      audio.onerror = (e) => {
        console.error('Audio playback failed:', e);
        toast.error('Failed to play voice preview');
        setPlayingVoice(false);
      };

      audio.onended = () => {
        setPlayingVoice(false);
        toast.success('Voice preview completed');
      };

      await audio.play();
      toast.success('Playing voice preview...');

    } else {
      toast.error('No audio data received');
      setPlayingVoice(false);
    }
  } catch (error: any) {
    console.error('Voice preview error:', error);
    
    // Check if the error is likely due to an invalid/expired voice ID
    if (error.response?.status === 400 || error.response?.status === 500) {
      const errorMessage = error.response?.data?.error || '';
      
      if (errorMessage.includes('voice') || errorMessage.includes('not found') || 
          errorMessage.includes('invalid') || error.response?.status === 500) {
        
        toast.warning('Voice might be unavailable. Refreshing voice list...');
        
        try {
          const voicesResponse = await apiClient.get('/agents/voice-options', {
            params: { force_refresh: true }
          });
          
          setAvailableVoices(voicesResponse.data);
          
          const voiceStillExists = voicesResponse.data.some(
            (v: VoiceOption) => v.voice_id === selectedVoiceId
          );
          
          if (!voiceStillExists) {
            toast.error('Selected voice is no longer available. Please choose another voice.');
            if (voicesResponse.data.length > 0) {
              setSelectedVoiceId(voicesResponse.data[0].voice_id);
            }
          } else {
            toast.info('Voice list updated. Please try again.');
          }
        } catch (refreshError) {
          console.error('Failed to refresh voices:', refreshError);
          toast.error('Failed to refresh voice list. Please try again later.');
        }
      } else {
        toast.error(errorMessage || 'Failed to generate voice preview');
      }
    } else {
      toast.error('Failed to generate voice preview');
    }
    
    setPlayingVoice(false);
  }
};
  
  const handleSaveVoice = async () => {
    if (!selectedVoiceId) {
      toast.error('Please select a voice first');
      return;
    }
    
    setSavingVoice(true);
    
    try {
      await apiClient.patch(`/agents/${agentId}/voice`, {
        voice_id: selectedVoiceId,
      });
      
      // Update local agent state
      setAgent((prev: any) => ({ ...prev, voice_id: selectedVoiceId }));
      
      toast.success('Voice settings saved successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to save voice settings');
    } finally {
      setSavingVoice(false);
    }
  };
  
  const handleTestCall = async () => {
    if (!testPhoneNumber) {
      toast.error('Please enter a phone number');
      return;
    }
    
    setCalling(true);
    
    try {
      const response = await apiClient.post(`/agents/${agentId}/test-call`, {
        phone_number: testPhoneNumber,
      });
      
      toast.success(`Test call initiated to ${testPhoneNumber}`);
      
      setTimeout(() => {
        setCalling(false);
        toast.info('Test call completed');
      }, 5000);
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to initiate test call');
      setCalling(false);
    }
  };
  
  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }
  
  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/agents/${agentId}`)}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Test Agent</h1>
            <p className="text-muted-foreground">
              Testing {agent?.name}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <Badge variant={agent?.is_active ? 'default' : 'secondary'}>
            {agent?.is_active ? 'Active' : 'Inactive'}
          </Badge>
          <Button
            variant="outline"
            onClick={() => router.push(`/agents/${agentId}`)}
          >
            <Settings className="mr-2 h-4 w-4" />
            Configure
          </Button>
        </div>
      </div>
      
      {/* Test Interface */}
      <Tabs defaultValue="chat" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="chat">Chat Test</TabsTrigger>
          <TabsTrigger value="voice" disabled={!agent?.voice_enabled}>
            Voice Test
          </TabsTrigger>
          <TabsTrigger value="call" disabled={!agent?.voice_enabled}>
            Call Test
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="chat" className="space-y-4">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="flex-shrink-0">
              <CardTitle>Chat Test</CardTitle>
              <CardDescription>
                Test your agent's chat responses in real-time
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col overflow-y-hidden">
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    <div
                      className={cn(
                        'flex items-start space-x-2 max-w-[70%]',
                        message.role === 'user' && 'flex-row-reverse space-x-reverse'
                      )}
                    >
                      <div
                        className={cn(
                          'p-2 rounded-full',
                          message.role === 'user' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'bg-muted'
                        )}
                      >
                        {message.role === 'user' ? (
                          <User className="h-4 w-4" />
                        ) : (
                          <Bot className="h-4 w-4" />
                        )}
                      </div>
                      <div
                        className={cn(
                          'rounded-lg px-4 py-2',
                          message.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        )}
                      >
                        <p className="text-sm">{message.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {message.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                {sending && (
                  <div className="flex justify-start">
                    <div className="flex items-center space-x-2">
                      <div className="p-2 rounded-full bg-muted">
                        <Bot className="h-4 w-4" />
                      </div>
                      <div className="bg-muted rounded-lg px-4 py-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              
              <div className="mt-4 flex space-x-2 flex-shrink-0">
                <Input
                  placeholder="Type a message..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  disabled={sending}
                />
                <Button onClick={handleSendMessage} disabled={sending}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Voice Preview */}
        <TabsContent value="voice" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Voice Configuration & Preview</CardTitle>
              <CardDescription>
                Select and test different voices for your agent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Voice Selection with Cards */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Select Voice</label>
                  <div className="flex items-center gap-2">
                    {agent?.voice_id && selectedVoiceId === agent.voice_id && (
                      <Badge variant="secondary" className="text-xs">
                        Current Voice
                      </Badge>
                    )}
                    {/* Save Voice button */}
                    {selectedVoiceId && selectedVoiceId !== agent?.voice_id && (
                      <Button
                        onClick={handleSaveVoice}
                        disabled={savingVoice}
                        variant="outline"
                        size="sm"
                      >
                        {savingVoice ? (
                          <>
                            <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="mr-2 h-3 w-3" />
                            Set as New AI Agent Voice
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
                
                {/* Voice Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-h-[300px] overflow-y-auto p-1">
                  {loadingVoices ? (
                    <div className="col-span-full flex justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                  ) : (
                    availableVoices.map((voice) => (
                      <button
                        key={voice.voice_id}
                        onClick={() => setSelectedVoiceId(voice.voice_id)}
                        className={cn(
                          "relative p-4 rounded-lg border-2 transition-all text-left hover:shadow-md",
                          "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                          selectedVoiceId === voice.voice_id
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-primary/50"
                        )}
                      >
                        {/* Selected indicator */}
                        {selectedVoiceId === voice.voice_id && (
                          <div className="absolute top-2 right-2">
                            <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                          </div>
                        )}
                        
                        <div className="space-y-1">
                          <p className="font-medium text-sm">{voice.name}</p>
                          {voice.description && (
                            <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                              {voice.description}
                            </p>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
                
                {!loadingVoices && availableVoices.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    No voices available
                  </div>
                )}
              </div>

              <Separator />
              
              {/* Test Text */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Test Text</label>
                <Textarea
                  value={voiceText}
                  onChange={(e) => setVoiceText(e.target.value)}
                  rows={4}
                  placeholder="Enter text to preview how this voice will sound..."
                  className="resize-none"
                />
                <p className="text-xs text-muted-foreground">
                  {voiceText.length} characters
                </p>
              </div>

              {/* Preview Button - Primary Action */}
              <Button
                onClick={handleVoicePreview}
                disabled={playingVoice || !voiceText || !selectedVoiceId}
                className="w-full"
                size="lg"
              >
                {playingVoice ? (
                  <>
                    <Volume2 className="mr-2 h-4 w-4 animate-pulse" />
                    Playing Preview...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Preview Voice
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="call" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Test Call</CardTitle>
              <CardDescription>
                Initiate a test call to experience your agent's voice capabilities
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Phone Number</label>
                <Input
                  type="tel"
                  placeholder="+1 (555) 123-4567"
                  value={testPhoneNumber}
                  onChange={(e) => setTestPhoneNumber(e.target.value)}
                  disabled={calling}
                />
                <p className="text-xs text-muted-foreground">
                  Enter your phone number to receive a test call
                </p>
              </div>
              
              <div className="bg-muted rounded-lg p-4">
                <h4 className="font-medium mb-2">Test Call Features:</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Voice greeting with agent's welcome message</li>
                  <li>• Natural conversation flow</li>
                  <li>• Response to your questions</li>
                  <li>• Proper call ending</li>
                </ul>
              </div>
              
              <Button
                onClick={handleTestCall}
                disabled={calling || !agent?.voice_enabled}
                className="w-full"
              >
                {calling ? (
                  <>
                    <Phone className="mr-2 h-4 w-4 animate-pulse" />
                    Calling...
                  </>
                ) : (
                  <>
                    <Phone className="mr-2 h-4 w-4" />
                    Start Test Call
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}