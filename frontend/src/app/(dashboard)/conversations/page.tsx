// src/app/(dashboard)/conversations/page.tsx
'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  MessageCircle,
  Phone,
  Search,
  Filter,
  Download,
  MoreVertical,
  User,
  Clock,
  ArrowUpDown,
  X,
  ChevronDown,
  Calendar,
  MessageSquare,
  PhoneCall,
  CheckCircle,
  XCircle,
  AlertCircle,
  UserPlus,
  RefreshCw,
} from 'lucide-react';
import { format, formatDistanceToNow, subDays, startOfDay, endOfDay } from 'date-fns';
import { apiClient } from '@/lib/api/client';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { useRouter } from 'next/navigation';
import { wsService } from '@/lib/websocket';
import { Conversation, SearchParams, SearchResponse } from '@/types';

// Quick filter presets
const QUICK_FILTERS = [
  { label: 'Today', value: 'today' },
  { label: 'This Week', value: 'week' },
  { label: 'Active', value: 'active' },
  { label: 'Handed Off', value: 'handed_off' },
];

export default function ConversationsPage() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [selectedConversations, setSelectedConversations] = useState<Set<string>>(new Set());
  const [totalCount, setTotalCount] = useState(0);
  const [filteredCount, setFilteredCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  
  // Search and filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchParams, setSearchParams] = useState<SearchParams>({
    limit: pageSize,
    offset: 0,
    sort_by: 'last_message_at',
    order: 'desc',
  });
  const hello = 'abc';
  const [showFilters, setShowFilters] = useState(false);
  const [activeFilters, setActiveFilters] = useState<string[]>([]);

  // Fetch conversations with search
  const fetchConversations = useCallback(async () => {
    setSearching(true);
    try {
        const searchPayload = {
          ...searchParams,
          query: searchQuery || undefined,
          offset: (currentPage - 1) * pageSize,
        };
        console.log("conversations search params:", searchPayload);


      const response = await apiClient.get<SearchResponse>(
        '/conversations/search',
        {
          params: searchPayload
        }
      );
      
      setConversations(response.data.conversations);
      setTotalCount(response.data.total);
      setFilteredCount(response.data.filtered);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      toast.error('Failed to load conversations');
    } finally {
      setSearching(false);
      setLoading(false);
    }
  }, [searchParams, searchQuery, currentPage, pageSize]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // WebSocket updates
  useEffect(() => {
    const handleUpdate = (data: any) => {
      // Refresh list when new conversation or update
      fetchConversations();
    };

    wsService.on('conversation_update', handleUpdate);
    wsService.on('new_conversation', handleUpdate);

    return () => {
      wsService.off('conversation_update', handleUpdate);
      wsService.off('new_conversation', handleUpdate);
    };
  }, [fetchConversations]);

  // Handle quick filters
  const applyQuickFilter = (filter: string) => {
    const newParams: SearchParams = { ...searchParams };
    
    switch (filter) {
      case 'today':
        newParams.date_from = startOfDay(new Date()).toISOString();
        newParams.date_to = endOfDay(new Date()).toISOString();
        break;
      case 'week':
        newParams.date_from = startOfDay(subDays(new Date(), 7)).toISOString();
        newParams.date_to = endOfDay(new Date()).toISOString();
        break;
      case 'active':
        newParams.status = 'active';
        break;
      case 'handed_off':
        newParams.has_handoff = true;
        break;
    }
    
    setSearchParams(newParams);
    setActiveFilters([...activeFilters, filter]);
    setCurrentPage(1);
  };

  // Clear filter
  const clearFilter = (filter: string) => {
    const newParams = { ...searchParams };
    
    switch (filter) {
      case 'today':
      case 'week':
        delete newParams.date_from;
        delete newParams.date_to;
        break;
      case 'active':
        delete newParams.status;
        break;
      case 'handed_off':
        delete newParams.has_handoff;
        break;
    }
    
    setSearchParams(newParams);
    setActiveFilters(activeFilters.filter(f => f !== filter));
  };

  // Clear all filters
  const clearAllFilters = () => {
    setSearchParams({
      limit: pageSize,
      offset: 0,
      sort_by: 'last_message_at',
      order: 'desc',
    });
    setActiveFilters([]);
    setSearchQuery('');
    setCurrentPage(1);
  };

  // Export conversations
  const handleExport = async (exportFormat: 'json' | 'csv') => {
    try {
      const response = await apiClient.post('/conversations/export', {
        ...searchParams,
        query: searchQuery || undefined,
        format: exportFormat,
      });
      
      if (exportFormat === 'csv') {
        // Create download link for CSV
        const blob = new Blob([response.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversations-${format(new Date(), 'yyyy-MM-dd')}.csv`;
        a.click();
      } else {
        // Download JSON
        const blob = new Blob([JSON.stringify(response.data, null, 2)], { 
          type: 'application/json' 
        });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversations-${format(new Date(), 'yyyy-MM-dd')}.json`;
        a.click();
      }
      
      toast.success(`Exported ${exportFormat.toUpperCase()} successfully`);
    } catch (error) {
      toast.error('Failed to export conversations');
    }
  };

  // Toggle conversation selection
  const toggleSelection = (id: string) => {
    const newSelection = new Set(selectedConversations);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedConversations(newSelection);
  };

  // Select all
  const toggleSelectAll = () => {
    if (selectedConversations.size === conversations.length) {
      setSelectedConversations(new Set());
    } else {
      setSelectedConversations(new Set(conversations.map(c => c.id)));
    }
  };

  // Get channel icon
  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'whatsapp':
        return <MessageCircle className="h-4 w-4 text-green-600" />;
      case 'sms':
        return <MessageSquare className="h-4 w-4 text-blue-600" />;
      case 'voice':
        return <PhoneCall className="h-4 w-4 text-purple-600" />;
      default:
        return <MessageCircle className="h-4 w-4" />;
    }
  };

  // Get status icon and color
  const getStatusBadge = (status: string) => {
    const config = {
      active: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100' },
      waiting: { icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-100' },
      ended: { icon: XCircle, color: 'text-gray-600', bg: 'bg-gray-100' },
      handed_off: { icon: UserPlus, color: 'text-blue-600', bg: 'bg-blue-100' },
    };
    
    const { icon: Icon, color, bg } = config[status as keyof typeof config] || config.active;
    
    return (
      <Badge variant="outline" className={cn('gap-1', bg)}>
        <Icon className={cn('h-3 w-3', color)} />
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  // Sort conversations
  const handleSort = (field: string) => {
    const newOrder = searchParams.sort_by === field && searchParams.order === 'desc' ? 'asc' : 'desc';
    setSearchParams({
      ...searchParams,
      sort_by: field,
      order: newOrder,
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b bg-background">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold">Conversations</h1>
            <p className="text-sm text-muted-foreground">
              {filteredCount} of {totalCount} conversations
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchConversations()}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuLabel>Export Format</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => handleExport('json')}>
                  Export as JSON
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('csv')}>
                  Export as CSV
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Search and filters */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  setCurrentPage(1);
                  fetchConversations();
                }
              }}
              className="pl-10"
            />
          </div>
          
          <Sheet open={showFilters} onOpenChange={setShowFilters}>
            <SheetTrigger asChild>
              <Button variant="outline">
                <Filter className="h-4 w-4 mr-2" />
                Filters
                {activeFilters.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {activeFilters.length}
                  </Badge>
                )}
              </Button>
            </SheetTrigger>
            <SheetContent>
              <SheetHeader>
                <SheetTitle>Filter Conversations</SheetTitle>
                <SheetDescription>
                  Narrow down your conversation list
                </SheetDescription>
              </SheetHeader>
              
              <div className="mt-6 space-y-4">
                {/* Status filter */}
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={searchParams.status || ''}
                    onValueChange={(value) => setSearchParams({
                      ...searchParams,
                      status: value || undefined,
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All statuses" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All</SelectItem>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="waiting">Waiting</SelectItem>
                      <SelectItem value="ended">Ended</SelectItem>
                      <SelectItem value="handed_off">Handed Off</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Channel filter */}
                <div className="space-y-2">
                  <Label>Channel</Label>
                  <Select
                    value={searchParams.channel || ''}
                    onValueChange={(value) => setSearchParams({
                      ...searchParams,
                      channel: value || undefined,
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All channels" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All</SelectItem>
                      <SelectItem value="whatsapp">WhatsApp</SelectItem>
                      <SelectItem value="sms">SMS</SelectItem>
                      <SelectItem value="voice">Voice</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Message count range */}
                <div className="space-y-2">
                  <Label>Message Count</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      placeholder="Min"
                      value={searchParams.min_messages || ''}
                      onChange={(e) => setSearchParams({
                        ...searchParams,
                        min_messages: e.target.value ? parseInt(e.target.value) : undefined,
                      })}
                    />
                    <Input
                      type="number"
                      placeholder="Max"
                      value={searchParams.max_messages || ''}
                      onChange={(e) => setSearchParams({
                        ...searchParams,
                        max_messages: e.target.value ? parseInt(e.target.value) : undefined,
                      })}
                    />
                  </div>
                </div>

                {/* Apply filters button */}
                <div className="flex gap-2 pt-4">
                  <Button
                    onClick={() => {
                      setCurrentPage(1);
                      fetchConversations();
                      setShowFilters(false);
                    }}
                    className="flex-1"
                  >
                    Apply Filters
                  </Button>
                  <Button
                    variant="outline"
                    onClick={clearAllFilters}
                  >
                    Clear All
                  </Button>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>

        {/* Quick filters */}
        <div className="flex gap-2 mt-3">
          {QUICK_FILTERS.map((filter) => (
            <Button
              key={filter.value}
              variant={activeFilters.includes(filter.value) ? 'default' : 'outline'}
              size="sm"
              onClick={() => {
                if (activeFilters.includes(filter.value)) {
                  clearFilter(filter.value);
                } else {
                  applyQuickFilter(filter.value);
                }
              }}
            >
              {filter.label}
              {activeFilters.includes(filter.value) && (
                <X className="h-3 w-3 ml-1" />
              )}
            </Button>
          ))}
        </div>

        {/* Active filters display */}
        {activeFilters.length > 0 && (
          <div className="flex items-center gap-2 mt-3">
            <span className="text-sm text-muted-foreground">Active filters:</span>
            {activeFilters.map((filter) => (
              <Badge key={filter} variant="secondary">
                {filter}
                <button
                  onClick={() => clearFilter(filter)}
                  className="ml-1 hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFilters}
            >
              Clear all
            </Button>
          </div>
        )}
      </div>

      {/* Bulk actions bar */}
      {selectedConversations.size > 0 && (
        <div className="p-3 bg-muted border-b">
          <div className="flex items-center justify-between">
            <span className="text-sm">
              {selectedConversations.size} conversation(s) selected
            </span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline">
                Export Selected
              </Button>
              <Button size="sm" variant="outline">
                Assign
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setSelectedConversations(new Set())}
              >
                Clear Selection
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Conversations table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="p-6 space-y-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <MessageCircle className="h-12 w-12 mb-2" />
            <p>No conversations found</p>
            {(searchQuery || activeFilters.length > 0) && (
              <Button
                variant="link"
                onClick={clearAllFilters}
                className="mt-2"
              >
                Clear filters
              </Button>
            )}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedConversations.size === conversations.length}
                    onCheckedChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Channel</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort('message_count')}
                  >
                    Messages
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort('last_message_at')}
                  >
                    Last Message
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {conversations.map((conversation) => (
                <TableRow
                  key={conversation.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => router.push(`/conversations/${conversation.id}`)}
                >
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <Checkbox
                      checked={selectedConversations.has(conversation.id)}
                      onCheckedChange={() => toggleSelection(conversation.id)}
                    />
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">
                        {conversation.customer_name || conversation.customer_phone}
                      </p>
                      {conversation.customer_name && (
                        <p className="text-sm text-muted-foreground">
                          {conversation.customer_phone}
                        </p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getChannelIcon(conversation.channel)}
                      <span className="capitalize">{conversation.channel}</span>
                    </div>
                  </TableCell>
                  <TableCell>{conversation.agent_name}</TableCell>
                  <TableCell>{getStatusBadge(conversation.status)}</TableCell>
                  <TableCell>{conversation.message_count}</TableCell>
                  <TableCell>
                    {conversation.last_message_at ? (
                      <div>
                        {conversation.last_message && (
                          <p className="text-sm truncate max-w-[400px]">
                            {conversation.last_message.content}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground ">
                          {formatDistanceToNow(new Date(conversation.last_message_at), {
                            addSuffix: true,
                          })}
                        </p>
                      </div>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => router.push(`/conversations/${conversation.id}`)}
                        >
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          Assign Agent
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          Export Chat
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-destructive">
                          End Conversation
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Pagination */}
      {totalCount > pageSize && (
        <div className="p-4 border-t">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {((currentPage - 1) * pageSize) + 1} to{' '}
              {Math.min(currentPage * pageSize, filteredCount)} of {filteredCount} results
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage * pageSize >= filteredCount}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}