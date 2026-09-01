// src/app/(dashboard)/conversations/[id]/page.tsx
'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  ArrowLeft,
  Send,
  User,
  Bot,
  Clock,
  MessageCircle,
  Phone,
  UserPlus,
  Download,
  Info,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { format, formatDistanceToNow, isToday, isYesterday, isSameDay } from 'date-fns';
import { apiClient } from '@/lib/api/client';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { wsService } from '@/lib/websocket';
import { Message, SpecificConversation } from '@/types';
import React from 'react';


export default function ConversationDetailPage() {
    const params = useParams();
    const router = useRouter();
    const conversationId = params.id as string;
    
    const [conversation, setConversation] = useState<SpecificConversation | null>(null);
    const [loading, setLoading] = useState(true);
    const [messageInput, setMessageInput] = useState('');
    const [sending, setSending] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [showHandoffWarning, setShowHandoffWarning] = useState(false);
    const [isHandingOff, setIsHandingOff] = useState(false);
    const [isReturningToAI, setIsReturningToAI] = useState(false);
    const [returnedToAIAt, setReturnedToAIAt] = useState<string | null>(null);
    const [isProcessingHandoff, setIsProcessingHandoff] = useState(false);

    useEffect(() => {
        fetchConversation();
    }, [conversationId]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [conversation?.messages]);

    useEffect(() => {
        // Listen for real-time updates
        const handleUpdate = (data: any) => {
        if (data.conversation_id === conversationId) {
            fetchConversation();
        }
        };

        const handleNewMessage = (data: any) => {
        if (data.conversation_id === conversationId) {
            // Add the new message to the existing conversation
            if (conversation) {
            const newMessage: Message = {
                id: data.message_id,
                sender_type: data.sender_type,
                content: data.content,
                message_type: data.message_type || 'text',
                created_at: data.created_at || new Date().toISOString(),
            };
            
            setConversation({
                ...conversation,
                messages: [...conversation.messages, newMessage],
                message_count: conversation.message_count + 1,
                last_message_at: newMessage.created_at,
            });
            }
        }
        };

        wsService.on('conversation_update', handleUpdate);
        wsService.on('new_message', handleNewMessage);

        return () => {
        wsService.off('conversation_update', handleUpdate);
        wsService.off('new_message', handleNewMessage);
        };
    }, [conversationId, conversation]);

    const fetchConversation = async () => {
        try {
        const response = await apiClient.get<SpecificConversation>(
            `/conversations/${conversationId}`
        );
        console.log(response.data)
        setConversation(response.data);
        } catch (error) {
        console.error('Failed to load conversation:', error);
        toast.error('Failed to load conversation');
        router.push('/conversations');
        } finally {
        setLoading(false);
        }
    };

    const handleSendMessage = async () => {
        if (!messageInput.trim() || !conversation) return;

        // If conversation is active (not handed off) and this is first human message, show warning
        // Skip handoff check if we're already processing a handoff
        if (!isProcessingHandoff && conversation.status === 'active' && !conversation.metadata?.human_intervened) {
            setShowHandoffWarning(true);
            return;
        }

        const tempMessage: Message = {
            id: `temp-${Date.now()}`, // Temporary ID
            sender_type: 'human',
            content: messageInput,
            message_type: 'text',
            created_at: new Date().toISOString(),
        };

        // Optimistically add the message to UI
        setConversation({
            ...conversation,
            messages: [...conversation.messages, tempMessage],
            message_count: conversation.message_count + 1,
            last_message_at: tempMessage.created_at,
        });

        // Clear input immediately for better UX
        const messageToSend = messageInput;
        setMessageInput('');

        setSending(true);
        try {
            const response = await apiClient.post(`/conversations/${conversationId}/messages`, {
            content: messageToSend,
            });
            
            // Replace temp message with real one from server
            if (response.data.id) {
            setConversation(prev => {
                if (!prev) return prev;
                const messages = prev.messages.map(msg => 
                msg.id === tempMessage.id 
                    ? { ...msg, id: response.data.id, created_at: response.data.created_at }
                    : msg
                );
                return { ...prev, messages };
            });
            }
            
            // Check if message was sent to customer
            if (response.data.sent_to_customer === false) {
            toast.warning('Message saved but could not be sent to customer');
            } else {
            toast.success('Message sent');
            }
            
        } catch (error: any) {
            console.error('Failed to send message:', error);
            
            // Remove the optimistic message on error
            setConversation(prev => {
            if (!prev) return prev;
            const messages = prev.messages.filter(msg => msg.id !== tempMessage.id);
            return { ...prev, messages, message_count: prev.message_count - 1 };
            });
            
            // Restore the input so user doesn't lose their message
            setMessageInput(messageToSend);
            
            // Show specific error message
            const errorMessage = error.response?.data?.error || 'Failed to send message';
            toast.error(errorMessage);
        } finally {
            setSending(false);
        }
    };

  const handleExport = async () => {
    try {
      const response = await apiClient.post(`/conversations/export`, {
        format: 'json',
      });
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: 'application/json',
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-${conversationId}-${format(new Date(), 'yyyy-MM-dd')}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Conversation exported');
    } catch (error) {
      toast.error('Failed to export conversation');
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'whatsapp':
        return <MessageCircle className="h-4 w-4 text-green-600" />;
      case 'sms':
        return <MessageCircle className="h-4 w-4 text-blue-600" />;
      case 'voice':
        return <Phone className="h-4 w-4 text-purple-600" />;
      default:
        return <MessageCircle className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'ended':
        return 'bg-gray-100 text-gray-800';
      case 'handed_off':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <MessageCircle className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-lg font-medium">Conversation not found</p>
        <Button
          variant="link"
          onClick={() => router.push('/conversations')}
          className="mt-2"
        >
          Back to conversations
        </Button>
      </div>
    );
  }

  // Unified Avatar Logic - A pure helper function
  const getAvatarIcon = (sender_type: string) => {
    switch (sender_type) {
        case 'agent':
            return Bot;
        case 'human':
            return UserPlus;
        case 'customer':
        default:
            return User;
    }
  };

  // Date separator function
  const formatDateSeparator = (dateString: string): string => {
    const date = new Date(dateString);
    // Using isToday and isYesterday from date-fns for a better UX
    if (isToday(date)) {
        return 'Today';
    }
    if (isYesterday(date)) {
        return 'Yesterday';
    }
    // For any other day, show the full date. e.g., "Friday, August 15, 2025"
    return format(date, 'PPPP'); // PPPP is a long-form date format from date-fns
    };


    // Critical Fucntion to handle handoff to Human Agent
    const handleHandoff = async () => {
        try {
            const response = await apiClient.post(`/conversations/${conversationId}/handoff`);
            
            // Fetch the updated conversation to get all the new data
            await fetchConversation();
            
            toast.success('Conversation handed off to you');
        } catch (error) {
            console.error('Failed to handoff:', error);
            toast.error('Failed to handoff conversation');
        } finally {
            setIsHandingOff(false);
        }
        };

    // Function to handle returning conversation to AI agent
    const handleReturnToAI = async () => {
        setIsReturningToAI(true);
        try {
            await apiClient.post(`/conversations/${conversationId}/handoff_back_to_ai_agent`);
            
            // Update local conversation state
            // setConversation(prev => {
            // if (!prev) return prev;
            // return {
            //     ...prev,
            //     status: 'active',
            //     assigned_to: null,
            // };
            // });
            await fetchConversation();
            
            toast.success('Conversation returned to AI agent');
        } catch (error) {
            console.error('Failed to return to AI:', error);
            toast.error('Failed to return conversation to AI');
        } finally {
            setIsReturningToAI(false);
        }
        };


    // Add function to send message after handoff confirmation
    const handleSendWithHandoff = async () => {
 
        const messageToSend = messageInput;
        
        // Clear the warning state FIRST
        setShowHandoffWarning(false);
        
        // Perform the handoff
        await handleHandoff();
        
        // After handoff, send the message directly without re-checking
        if (messageToSend.trim()) {
            const tempMessage: Message = {
            id: `temp-${Date.now()}`,
            sender_type: 'human',
            content: messageToSend,
            message_type: 'text',
            created_at: new Date().toISOString(),
            };

            // Add message optimistically
            setConversation(prev => {
            if (!prev) return prev;
            return {
                ...prev,
                messages: [...prev.messages, tempMessage],
                message_count: prev.message_count + 1,
                last_message_at: tempMessage.created_at,
            };
            });

            // Clear input
            setMessageInput('');
            setSending(true);

            try {
            const response = await apiClient.post(`/conversations/${conversationId}/messages`, {
                content: messageToSend,
            });
            
            // Replace temp message with real one
            if (response.data.id) {
                setConversation(prev => {
                if (!prev) return prev;
                const messages = prev.messages.map(msg => 
                    msg.id === tempMessage.id 
                    ? { ...msg, id: response.data.id, created_at: response.data.created_at }
                    : msg
                );
                return { ...prev, messages };
                });
            }
            
            if (response.data.sent_to_customer === false) {
                toast.warning('Message saved but could not be sent to customer');
            } else {
                toast.success('Message sent');
            }
            } catch (error: any) {
            console.error('Failed to send message:', error);
            
            // Remove optimistic message on error
            setConversation(prev => {
                if (!prev) return prev;
                const messages = prev.messages.filter(msg => msg.id !== tempMessage.id);
                return { ...prev, messages, message_count: prev.message_count - 1 };
            });
            
            // Restore input
            setMessageInput(messageToSend);
            
            const errorMessage = error.response?.data?.error || 'Failed to send message';
            toast.error(errorMessage);
            } finally {
            setSending(false);
            }
        }
        };





  return (
    <>
      {/* Handoff Warning Dialog */}
      <AlertDialog open={showHandoffWarning} onOpenChange={setShowHandoffWarning}>
        <AlertDialogContent>
            <AlertDialogHeader>
            <AlertDialogTitle>Take Over Conversation?</AlertDialogTitle>
            <AlertDialogDescription>
                Sending this message will hand off the conversation to you. The AI agent will stop responding to customer messages.
            </AlertDialogDescription>
            </AlertDialogHeader>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3 mt-2 mb-4">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
                <strong>Note:</strong> You'll need to handle all future customer messages until you return control to the AI.
            </p>
            </div>
            <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
                onClick={handleSendWithHandoff}
                className="bg-blue-600 hover:bg-blue-700"
            >
                Take Over & Send Message
            </AlertDialogAction>
            </AlertDialogFooter>
        </AlertDialogContent>
        </AlertDialog>

      <div className="flex h-full overflow-hidden">
        {/* Main chat area */}
        <div className="flex-1 flex flex-col h-full">
          {/* Header - Fixed */}
          <div className="flex-shrink-0 p-4 border-b bg-card">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => router.push('/conversations')}
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                <Avatar>
                  <AvatarFallback>
                    <User className="h-4 w-4" />
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h2 className="font-semibold">
                    {conversation.customer_name || conversation.customer_phone}
                  </h2>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      {getChannelIcon(conversation.channel)}
                      <span className="capitalize">{conversation.channel}</span>
                    </div>
                    <span>•</span>
                    <span>{conversation.agent_name}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                  {/* Control Status Badge */}
                  {conversation.status === 'handed_off' && conversation.assigned_to ? (
                    <Badge className="bg-blue-100 text-blue-800 border-blue-200">
                    <UserPlus className="h-3 w-3 mr-1" />
                    {conversation.assigned_to.full_name || conversation.assigned_to.email}
                    </Badge>
                ) : conversation.status === 'handed_off' ? (
                    <Badge className="bg-blue-100 text-blue-800 border-blue-200">
                    <UserPlus className="h-3 w-3 mr-1" />
                    Human Control
                    </Badge>
                ) : (
                    <Badge className="bg-green-100 text-green-800 border-green-200">
                    <Bot className="h-3 w-3 mr-1" />
                    AI Active
                    </Badge>
                )}
                  {/* Status Badge */}
                <Badge className={cn('capitalize', getStatusColor(conversation.status))}>
                  {conversation.status.replace('_', ' ')}
                </Badge>
                {conversation.sentiment_score !== undefined && (
                  <Badge variant="outline">
                    Sentiment: {(conversation.sentiment_score * 100).toFixed(0)}%
                  </Badge>
                )}
                <Button variant="outline" size="sm" onClick={handleExport}>
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-6 max-w-3xl mx-auto">
              {conversation.messages.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  No messages yet
                </div>
              ) : (
                conversation.messages.map((message, index) => {
                    // --- Date Separator Logic (this part is correct and remains) ---
  let showDateSeparator = false;
  if (index === 0) {
    showDateSeparator = true;
  } else {
    const prevMessage = conversation.messages[index - 1];
    if (prevMessage?.created_at && message.created_at) {
        const prevMessageDate = new Date(prevMessage.created_at);
        const currentMessageDate = new Date(message.created_at);
        if (!isSameDay(prevMessageDate, currentMessageDate)) {
            showDateSeparator = true;
        }
    }
  }

  // --- NEW: Unified System Message Handling ---
  // We check if the message is a system event first.
  if (message.sender_type === 'system') {
    // Determine which icon to use for the event
    const isHandoff = message.content.toLowerCase().includes('handed off');
    const EventIcon = isHandoff ? UserPlus : Bot;

    return (
      <React.Fragment key={message.id}>
        {showDateSeparator && (
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center" aria-hidden="true">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-background px-2 text-xs text-muted-foreground">
                {formatDateSeparator(message.created_at)}
              </span>
            </div>
          </div>
        )}
        {/* The new, visually distinct component for ALL system messages */}
        <div className="relative my-4">
            <div className="absolute inset-0 flex items-center" aria-hidden="true">
                <div className="w-full border-t border-dashed border-border" />
            </div>
            <div className="relative flex justify-center">
                <div className="bg-background px-3 py-1">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <EventIcon className="h-3 w-3" />
                    <span className="font-medium">{message.content}</span>
                    <span className="opacity-70">
                    • {format(new Date(message.created_at), 'h:mm a')}
                    </span>
                </div>
                </div>
            </div>
        </div>
      </React.Fragment>
    );
  }

  // --- Logic for regular chat bubbles (customer, agent, human) ---
  const isCustomer = message.sender_type === 'customer';
  const AvatarIcon = getAvatarIcon(message.sender_type);
  const isTempMessage = message.id.startsWith('temp-');

  return (
    <React.Fragment key={message.id}>
      {showDateSeparator && (
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center" aria-hidden="true">
            <div className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-background px-2 text-xs text-muted-foreground">
              {formatDateSeparator(message.created_at)}
            </span>
          </div>
        </div>
      )}
      <div
        className={cn(
          'flex items-start gap-3',
          !isCustomer && 'flex-row-reverse',
          isTempMessage && 'opacity-70'
        )}
      >
        <Avatar className="h-8 w-8 flex-shrink-0 mt-7">
          <AvatarFallback>
            <AvatarIcon className="h-5 w-5" />
          </AvatarFallback>
        </Avatar>

        <div className="flex flex-col gap-1">
          <div className={cn(
            'flex items-center gap-2',
            !isCustomer && 'flex-row-reverse'
          )}>
            <span className="text-sm font-medium">
              {isCustomer
                ? 'Customer'
                : message.sender_type === 'agent'
                ? 'AI Agent'
                : 'Human Agent'}
            </span>
            <span className="text-xs text-muted-foreground">
              {new Date(message.created_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>

          <div
            className={cn(
              'max-w-md rounded-lg px-4 py-2 text-sm',
              isCustomer
                ? 'bg-muted rounded-bl-none'
                : message.sender_type === 'agent'
                ? 'bg-primary text-primary-foreground rounded-br-none'
                : 'bg-blue-600 text-white rounded-br-none'
            )}
          >
            <p className="whitespace-pre-wrap">{message.content}</p>
            {isTempMessage ? (
              <p className="text-xs opacity-50 mt-1 text-right">Sending...</p>
            ) : message.delivered_at ? (
              <p className="text-xs opacity-50 mt-1 text-right">Delivered</p>
            ) : null}
          </div>
        </div>
      </div>
    </React.Fragment>
  );
})
            //         {/* Date Seperator Logic */}
            //         let showDateSeparator = false;
            //         if (index === 0) {
            //             showDateSeparator = true;
            //         } else {
            //             const prevMessage = conversation.messages[index - 1];
            //             const prevMessageDate = new Date(prevMessage.created_at);
            //             const currentMessageDate = new Date(message.created_at);
            //             if (!isSameDay(prevMessageDate, currentMessageDate)) {
            //                 showDateSeparator = true;
            //             }
            //         }
            //         {/* System Message Seperator */}
            //         let showHandoffSeparator = false;
            //         if (conversation.handed_off_at) {
            //             const handoffTime = new Date(conversation.handed_off_at);
            //             const messageTime = new Date(message.created_at);
                        
            //             // Show separator before the first message after handoff
            //             if (messageTime >= handoffTime) {
            //             if (index === 0) {
            //                 showHandoffSeparator = true;
            //             } else {
            //                 const prevMessageTime = new Date(conversation.messages[index - 1].created_at);
            //                 // Show if previous message was before handoff and current is after
            //                 if (prevMessageTime < handoffTime) {
            //                 showHandoffSeparator = true;
            //                 }
            //             }
            //             }
            //         }

            //       const isCustomer = message.sender_type === 'customer';
            //       const AvatarIcon = getAvatarIcon(message.sender_type);
            //       const isTempMessage = message.id.startsWith('temp-');
            //       const wasDuringHandoff = message.sender_type === 'human' && 
            //                conversation.handed_off_at &&
            //                new Date(message.created_at) >= new Date(conversation.handed_off_at);

            //       return (
            //           <React.Fragment key={message.id}>
            //             {/* Date seperator */}
            //               {showDateSeparator && (
            //               <div className="relative my-4">
            //                   <div className="absolute inset-0 flex items-center" aria-hidden="true">
            //                   <div className="w-full border-t border-border" />
            //                   </div>
            //                   <div className="relative flex justify-center">
            //                   <span className="bg-background px-2 text-xs text-muted-foreground">
            //                       {formatDateSeparator(message.created_at)}
            //                   </span>
            //                   </div>
            //               </div>
            //               )}
            //               {/* Handoff System Message seperator */}
            //               {showHandoffSeparator && conversation.assigned_to && (
            //                 <div className="relative my-6">
            //                 <div className="absolute inset-0 flex items-center" aria-hidden="true">
            //                     <div className="w-full border-t border-blue-200 dark:border-blue-800" />
            //                 </div>
            //                 <div className="relative flex justify-center">
            //                     <div className="bg-background px-3 py-1">
            //                     <div className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400">
            //                         <UserPlus className="h-3 w-3" />
            //                         <span className="font-medium">
            //                         Conversation handed off to {conversation.assigned_to.full_name || conversation.assigned_to.email}
            //                         </span>
            //                         <span className="text-muted-foreground">
            //                         • {format(new Date(conversation.handed_off_at!), 'h:mm a')}
            //                         </span>
            //                     </div>
            //                     </div>
            //                 </div>
            //                 </div>
            //             )}
            //         <div
            //           className={cn(
            //             'flex items-start gap-3',
            //             !isCustomer && 'flex-row-reverse',
            //             isTempMessage && 'opacity-70'
            //           )}
            //         >
            //           <Avatar className="h-8 w-8 flex-shrink-0 mt-7">
            //             <AvatarFallback>
            //               <AvatarIcon className="h-5 w-5" />
            //             </AvatarFallback>
            //           </Avatar>

            //           <div className="flex flex-col gap-1">
            //             <div className={cn(
            //                 'flex items-center gap-2',
            //                 !isCustomer && 'flex-row-reverse'
            //             )}>
            //                 <span className="text-sm font-medium">
            //                 {isCustomer
            //                     ? 'Customer'
            //                     : message.sender_type === 'agent'
            //                     ? 'AI Agent'
            //                     : 'Human Agent'}
            //                 </span>
            //                 {wasDuringHandoff && (
            //                 <Badge variant="outline" className="text-xs">
            //                     In Control
            //                 </Badge>
            //                 )}
            //               <span className="text-xs text-muted-foreground">
            //                 {new Date(message.created_at).toLocaleTimeString([], {
            //                   hour: '2-digit',
            //                   minute: '2-digit',
            //                 })}
            //               </span>
            //             </div>

            //             <div
            //               className={cn(
            //                 'max-w-md rounded-lg px-4 py-2 text-sm',
            //                 isCustomer
            //                   ? 'bg-muted rounded-bl-none'
            //                   : message.sender_type === 'agent'
            //                   ? 'bg-primary text-primary-foreground rounded-br-none'
            //                   : 'bg-blue-600 text-white rounded-br-none'
            //               )}
            //             >
            //               <p className="whitespace-pre-wrap">{message.content}</p>
            //               {isTempMessage ? (
            //               <p className="text-xs opacity-50 mt-1 text-right">
            //                   Sending...
            //               </p>
            //               ) : message.delivered_at ? (
            //               <p className="text-xs opacity-50 mt-1 text-right">
            //                   Delivered
            //               </p>
            //               ) : null}
            //           </div>
            //           </div>
            //       </div>
            //       </React.Fragment>
            //   );
            //   })
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {(conversation.status === 'handed_off' || conversation.status === 'active') && (
          <div className="flex-shrink-0 border-t bg-card">
              <div className="p-3 border-b bg-muted/30">
              <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                  {conversation.status === 'handed_off' ? (
                      <>
                      <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                          <span className="text-sm font-medium">You have control</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                          AI responses disabled
                      </Badge>
                      </>
                  ) : (
                      <>
                      <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                          <span className="text-sm font-medium">AI is active</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                          AI will respond to customer
                      </Badge>
                      </>
                  )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                  {conversation.status === 'handed_off' ? (
                      <Button
                      size="sm"
                      variant="outline"
                      onClick={handleReturnToAI}
                      disabled={isReturningToAI}
                      className="text-green-600 border-green-200 hover:bg-green-50"
                      >
                      {isReturningToAI ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                          <Bot className="h-4 w-4 mr-2" />
                      )}
                      Return to AI
                      </Button>
                  ) : conversation.metadata?.human_intervened ? (
                      <Button
                      size="sm"
                      variant="outline"
                      onClick={handleHandoff}
                      disabled={isHandingOff}
                      className="text-blue-600 border-blue-200 hover:bg-blue-50"
                      >
                      {isHandingOff ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                          <UserPlus className="h-4 w-4 mr-2" />
                      )}
                      Take Full Control
                      </Button>
                  ) : null}
                  </div>
              </div>
              
              {conversation.status === 'active' && conversation.metadata?.human_intervened && (
                  <div className="mt-2 text-xs text-muted-foreground bg-yellow-50 dark:bg-yellow-900/20 rounded p-2">
                  <AlertCircle className="h-3 w-3 inline mr-1" />
                  You're intervening but AI is still active. Click "Take Full Control" to disable AI responses.
                  </div>
              )}
              </div>
              
              <div className="p-4">
              <div className="flex space-x-2">
                  <Input
                  placeholder={
                      conversation.status === 'handed_off' 
                      ? "Type your message to customer..." 
                      : "Type to intervene (AI is still active)..."
                  }
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                      }
                  }}
                  disabled={sending}
                  />
                  <Button 
                  onClick={handleSendMessage} 
                  disabled={sending || !messageInput.trim()}
                  >
                  {sending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                      <Send className="h-4 w-4" />
                  )}
                  </Button>
              </div>
              </div>
          </div>
          )}
        </div>
        
        <div className="w-80 border-l bg-card p-4 overflow-y-auto flex-shrink-0">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Info className="h-4 w-4" />
            Conversation Details
          </h3>
          
          <div className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Started</p>
              <p className="text-sm">
                {format(new Date(conversation.started_at), 'PPpp')}
              </p>
            </div>
            
            {conversation.ended_at && (
              <>
                <Separator />
                <div>
                  <p className="text-sm text-muted-foreground">Ended</p>
                  <p className="text-sm">
                    {format(new Date(conversation.ended_at), 'PPpp')}
                  </p>
                </div>
              </>
            )}
            
            <Separator />
            
            <div>
              <p className="text-sm text-muted-foreground">Duration</p>
              <p className="text-sm">
                {conversation.ended_at
                  ? formatDistanceToNow(new Date(conversation.started_at), {
                      addSuffix: false,
                    })
                  : 'Ongoing'}
              </p>
            </div>
            
            <Separator />
            
            <div>
              <p className="text-sm text-muted-foreground">Total Messages</p>
              <p className="text-sm">{conversation.message_count}</p>
            </div>
            
            <Separator />
            
            <div>
              <p className="text-sm text-muted-foreground">Customer</p>
              <p className="text-sm font-medium">{conversation.customer_phone}</p>
              {conversation.customer_name && (
                <p className="text-sm">{conversation.customer_name}</p>
              )}
            </div>
            
            {conversation.customer_metadata && Object.keys(conversation.customer_metadata).length > 0 && (
              <>
                <Separator />
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Customer Info</p>
                  <div className="space-y-1">
                    {Object.entries(conversation.customer_metadata).map(([key, value]) => (
                      <div key={key} className="text-sm">
                        <span className="text-muted-foreground">{key}:</span>{' '}
                        <span>{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
            
            <Separator />
            
            <div>
              <p className="text-sm text-muted-foreground">Channel</p>
              <p className="text-sm capitalize flex items-center gap-2">
                {getChannelIcon(conversation.channel)}
                {conversation.channel}
              </p>
            </div>
            
            <Separator />
            
            <div>
              <p className="text-sm text-muted-foreground">Agent</p>
              <p className="text-sm">{conversation.agent_name}</p>
              <p className="text-xs text-muted-foreground">{conversation.agent_id}</p>
            </div>
            
            {conversation.metadata && Object.keys(conversation.metadata).length > 0 && (
              <>
                <Separator />
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Additional Info</p>
                  <div className="space-y-1">
                    {Object.entries(conversation.metadata).map(([key, value]) => (
                      <div key={key} className="text-sm">
                        <span className="text-muted-foreground">{key}:</span>{' '}
                        <span>{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div> 
        </div>
      </div>
    </>
  );
}