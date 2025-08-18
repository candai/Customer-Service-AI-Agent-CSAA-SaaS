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
import { Slider } from '@/components/ui/slider';
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

export default function AgentTestPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;
  
  const [agent, setAgent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [voiceText, setVoiceText] = useState('Hello! I am your AI assistant. How can I help you today?');
  const [playingVoice, setPlayingVoice] = useState(false);
  const [testPhoneNumber, setTestPhoneNumber] = useState('');
  const [calling, setCalling] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    fetchAgent();
  }, [agentId]);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const fetchAgent = async () => {
    try {
      const response = await apiClient.get(`/agents/${agentId}`);
      setAgent(response.data);
      
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
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setSending(true);
    
    try {
      const response = await apiClient.post(`/agents/${agentId}/test-chat`, {
        message: inputMessage,
      });
      
      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: response.data.agent_response,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, agentMessage]);
      
      // Show token usage
      if (response.data.tokens_used) {
        toast.info(`Tokens used: ${response.data.tokens_used}`);
      }
    } catch (error) {
      toast.error('Failed to get response');
    } finally {
      setSending(false);
    }
  };
  
//   const handleVoicePreview = async () => {
//     setPlayingVoice(true);
    
//     try {
//         const response = await apiClient.post(`/agents/${agentId}/preview-voice`, {
//         text: voiceText,
//         });
        
//         toast.success('Voice preview generated successfully');
        
//         // Simulate playing for the duration
//         const duration = response.data.duration_seconds || 3.5;
        
//         // Show playing state for the duration
//         setTimeout(() => {
//         setPlayingVoice(false);
//         toast.info('Voice preview completed');
//         }, duration * 1000);
        
//     } catch (error: any) {
//         toast.error(error.response?.data?.error || 'Failed to generate voice preview');
//         setPlayingVoice(false);
//     }
//  };

  const handleVoicePreview = async () => {
    // Set the playing state at the start of the process
    setPlayingVoice(true);

    try {
        const response = await apiClient.post(`/agents/${agentId}/preview-voice`, {
            text: voiceText,
        });

        const { audio_url, duration_seconds } = response.data;
        
        if (audio_url) {
            // Use a try-catch block to handle potential audio object errors
            try {
                // Ensure the MIME type matches the actual format
                const audio = new Audio(audio_url);
                
                // Add an error listener to catch playback issues
                audio.onerror = (e) => {
                    console.error('Audio playback failed:', e);
                    toast.error('Failed to play voice preview. The audio data may be corrupted.');
                    setPlayingVoice(false);
                };

                audio.onended = () => {
                    setPlayingVoice(false);
                    toast.info('Voice preview completed');
                };

                // Using `await audio.play()` returns a Promise that resolves when playback starts
                await audio.play();

                toast.success('Voice preview started!');

            } catch (playError) {
                console.error('Error creating or playing audio:', playError);
                toast.error('An error occurred during audio playback.');
                setPlayingVoice(false);
            }
        } else {
            // Handle cases where audio data is missing
            toast.error('No audio data received from the server.');
            setPlayingVoice(false);
        }
    } catch (apiError) {
        // Handle API request errors
        console.error('API call failed:', apiError);
        toast.error('Failed to generate voice preview. Please check your network connection.');
        setPlayingVoice(false);
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
      
      // Simulate call duration
      setTimeout(() => {
        setCalling(false);
        toast.info('Test call completed');
      }, 5000);
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to initiate test call');
      setCalling(false);
    }
  };
  
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
            <CardHeader>
              <CardTitle>Chat Test</CardTitle>
              <CardDescription>
                Test your agent's chat responses in real-time
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              {/* Messages */}
              <ScrollArea className="flex-1 pr-4 mb-4">
                <div className="space-y-4">
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
              </ScrollArea>
              
              {/* Input */}
              <div className="flex space-x-2">
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
        
        <TabsContent value="voice" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Voice Preview</CardTitle>
              <CardDescription>
                Test how your agent sounds with text-to-speech
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Voice ID</label>
                <p className="text-sm text-muted-foreground">
                  {agent?.voice_id || 'Default voice'}
                </p>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Test Text</label>
                <Textarea
                  value={voiceText}
                  onChange={(e) => setVoiceText(e.target.value)}
                  rows={4}
                  placeholder="Enter text to preview..."
                />
              </div>
              
              <Button
                onClick={handleVoicePreview}
                disabled={playingVoice || !voiceText}
                className="w-full"
              >
                {playingVoice ? (
                  <>
                    <Volume2 className="mr-2 h-4 w-4 animate-pulse" />
                    Playing...
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