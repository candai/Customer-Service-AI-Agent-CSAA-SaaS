// src/app/(dashboard)/analytics/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Users, MessageSquare, Minus, Download, FunnelPlus
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { toast } from 'sonner';
import { format, subDays, startOfMonth, endOfMonth, startOfDay } from 'date-fns';
import { cn } from '@/lib/utils';
import { DateRange } from 'react-day-picker';
import { DeltaIndicator } from '@/components/ui/delta-indicator';




export interface ResponseTimeDistribution {
  under_1_min: number;
  one_to_five_min: number;
  five_to_fifteen_min: number;
  over_fifteen_min: number;
}

export interface CustomerSatisfactionDistribution {
    one_star: number;
    two_star: number;
    three_star: number;
    four_star: number;
    five_star: number;
}

interface AnalyticsData {
  summary: {
    total_conversations: number;
    total_messages: number;
    avg_messages_per_conversation: number;
    unique_customers: number;
    handoff_rate: number;
    delta_total_conversations_percentage: number;
  };
  trends: Array<{
    period: string;
    conversations: number;
    messages: number;
    unique_customers: number;
    handoffs: number;
  }>;
  channel_distribution: Array<{
    channel: string;
    count: number;
    avg_messages: number;
  }>;
  agent_performance: Array<{
    agent_id: string;
    agent_name: string;
    total_conversations: number;
    total_messages: number;
    avg_messages_per_conversation: number;
    handoff_rate: number;
    avg_response_time_seconds: number;
    channels: Array<{
        channel: string;
        count: number;
    }>
  }>;
  peak_hours: Array<{
    hour: number;
    count: number;
    avg_messages: number;
  }>;
  response_times: Array<{
    avg_first_response: number | null;
    min_first_response: number | null;
    max_first_response: number | null;
    distribution: ResponseTimeDistribution;

  }>;
  customer_satisfaction: Array<{
    average_rating: string;
    total_ratings: number;
    distribution: CustomerSatisfactionDistribution;
  }>;
}

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: startOfDay(subDays(new Date(), 30)),
    to: startOfDay(new Date()),
  });

  const [granularity, setGranularity] = useState<'hour' | 'day' | 'week' | 'month'>('day');

  useEffect(() => {
    fetchAnalytics();
   }, [ granularity]);

    const fetchAnalytics = async () => {
        if (!dateRange?.from || !dateRange?.to) {
            toast.info('Please select a complete date range.');
            return;
        };

        let adjustedFrom = dateRange.from;
        let adjustedTo = dateRange.to;
        
        if (granularity === 'hour') {
            // For hourly, limit to last 7 days max to avoid too many data points
            const daysDiff = Math.ceil((adjustedTo.getTime() - adjustedFrom.getTime()) / (1000 * 60 * 60 * 24));
            if (daysDiff > 7) {
                adjustedFrom = subDays(adjustedTo, 7);
                toast.info('Hourly view limited to 7 days');
                // set granularity selection to daily back
                setGranularity('day');
                return;
            }
        }

        // setLoading(true);
        try {
            const params = {
                granularity,
                ...(dateRange?.from && dateRange?.to && {
                date_from: dateRange.from.toISOString(),
                date_to: dateRange.to.toISOString(),
                }),
            };
            console.log('Fetching analytics with params:', params);

            const response = await apiClient.post('/analytics/overview',  params );
            console.log('Analytics data fetched:', response.data);
            setData(response.data);
        } catch (error) {
            toast.error('Failed to load analytics. Please try again later.');
            // console.error("Failed to fetch analytics:", error);
        } finally {
            setLoading(false);
        }
    };

  const exportData = async (fileFormat: 'json' | 'csv') => {
    if (!dateRange?.from || !dateRange?.to) return;
    try {
      const response = await apiClient.post('/analytics/export/time-series', {
        start_date: dateRange.from.toISOString(),
        end_date: dateRange.to.toISOString(),
        format: fileFormat,
        granularity,
      });
      
      // Handle download
      const blob = new Blob([
        fileFormat === 'csv' ? response.data : JSON.stringify(response.data)
      ], { type: fileFormat === 'csv' ? 'text/csv' : 'application/json' });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-${fileFormat}-${format(new Date(), 'yyyy-MM-dd')}.${fileFormat}`;
      a.click();
      
      toast.success('Data exported successfully');
    } catch (error) {
      toast.error('Failed to export data');
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  if (loading) {
    return (
      <div className="p-8">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="space-y-2">
                <div className="h-4 bg-muted rounded animate-pulse" />
                <div className="h-8 bg-muted rounded animate-pulse" />
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    );
  }
  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Monitor your AI agents' performance and customer interactions
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <DatePickerWithRange date={dateRange} setDate={setDateRange} />
          <Button variant="outline" onClick={fetchAnalytics}>
            <FunnelPlus className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Select value={granularity} onValueChange={(v: any) => setGranularity(v)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="hour">Hourly</SelectItem>
              <SelectItem value="day">Daily</SelectItem>
              <SelectItem value="week">Weekly</SelectItem>
              <SelectItem value="month">Monthly</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={() => exportData('csv')}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Conversations</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data?.summary.total_conversations.toLocaleString()}
            </div>
            {/* if (data?.summary.delta_total_conversations) > 0 green trend up else trend down red */}
            {/* <p className="text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 inline mr-1 text-green-500" />
              +12% from last period
            </p> */}
            <p className="text-xs text-muted-foreground">
                {/* {(() => {
                    // 1. Extract the value into a variable once. Much cleaner!
                    const percentageChange = data?.summary.delta_total_conversations_percentage ?? 0;

                    // 2. Define variables for the parts that change
                    let IconComponent;
                    let colorClass;
                    let prefix = '';

                    // 3. Use a clear if/else block to handle all three cases
                    if (percentageChange > 0) {
                    IconComponent = TrendingUp;
                    colorClass = 'text-green-500';
                    prefix = '+';
                    } else if (percentageChange < 0) {
                    IconComponent = TrendingDown;
                    colorClass = 'text-red-500';
                    } else {
                    // This correctly handles the case where the change is exactly 0
                    IconComponent = Minus; // A neutral icon is better for 0% change
                    colorClass = 'text-muted-foreground';
                    }

                    return (
                    // 4. Render a single, clean JSX structure using the variables
                    <span className="inline-flex items-center">
                        <IconComponent className={cn('h-3 w-3 inline mr-1', colorClass)} />
                        {prefix}{percentageChange.toFixed(0)}% from last period
                    </span>
                    );
                })()} */}
                <DeltaIndicator value={data?.summary.delta_total_conversations_percentage} />
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unique Customers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data?.summary.unique_customers.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 inline mr-1 text-green-500" />
              +5% from last period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Messages</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data?.summary.avg_messages_per_conversation.toFixed(1)}
            </div>
            <p className="text-xs text-muted-foreground">Per conversation</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Handoff Rate</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data?.summary.handoff_rate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              <TrendingDown className="h-3 w-3 inline mr-1 text-green-500" />
              -2% from last period
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="channels">Channels</TabsTrigger>
          <TabsTrigger value="peak-hours">Peak Hours</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Conversation Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={data?.trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  {/* <XAxis 
                    dataKey="period" 
                    tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                  /> */}
                  <XAxis 
                        dataKey="period" 
                        tickFormatter={(value) => {
                            if (granularity === 'hour') {
                                return format(new Date(value), 'MMM dd HH:mm');
                            }
                            return format(new Date(value), 'MMM dd');
                        }}
                    />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="conversations" 
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.6}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="messages" 
                    stroke="#82ca9d" 
                    fill="#82ca9d" 
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data?.agent_performance.map((agent) => (
                  <div key={agent.agent_id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <p className="font-medium">{agent.agent_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {agent.total_conversations} conversations
                      </p>
                    </div>
                    <div className="flex gap-8 text-sm">
                      <div>
                        <p className="text-muted-foreground">Avg Response</p>
                        <p className="font-medium">{agent.avg_response_time_seconds}s</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Handoff Rate</p>
                        <p className="font-medium">{agent.handoff_rate.toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="channels">
          <Card>
            <CardHeader>
              <CardTitle>Channel Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data?.channel_distribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.channel}: ${entry.count}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {data?.channel_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="peak-hours">
          <Card>
            <CardHeader>
              <CardTitle>Peak Hours Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data?.peak_hours}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}