// src/app/(dashboard)/dashboard/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { MessageCircle, Phone, Users, TrendingUp, Clock, Bot } from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { cn } from '@/lib/utils';


interface DashboardStats {
  total_conversations: number;
  active_conversations: number;
  total_messages: number;
  total_agents: number;
  response_time_avg: number;
  satisfaction_score: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  // Fetch dashboard stats from the django backendAPI
  const fetchStats = async () => {
    try {
        const response = await apiClient.get('/conversations/dashboard/stats');
        setStats(response.data);
    } catch (error) {
        console.error('Failed to fetch stats:', error);
        // Use mock data if API fails
        setStats({
        total_conversations: 2,
        active_conversations: 1,
        total_messages: 15,
        total_agents: 1,
        response_time_avg: 2.5,
        satisfaction_score: 4.5,
        });
    } finally {
        setLoading(false);
    }
    };

  const statCards = [
    {
      title: 'Total Conversations',
      value: stats?.total_conversations || 0,
      icon: MessageCircle,
      description: 'All time conversations',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Active Now',
      value: stats?.active_conversations || 0,
      icon: Users,
      description: 'Currently active',
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Total Messages',
      value: stats?.total_messages || 0,
      icon: MessageCircle,
      description: 'Messages exchanged',
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Active Agents',
      value: stats?.total_agents || 0,
      icon: Bot,
      description: 'AI agents deployed',
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor your AI agents and conversations in real-time
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        {statCards.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <div className={cn('p-2 rounded-full', stat.bgColor)}>
                <stat.icon className={cn('h-4 w-4', stat.color)} />
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-8 w-20" />
              ) : (
                <>
                  <div className="text-2xl font-bold">
                    {stat.value.toLocaleString()}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {stat.description}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Conversation activity over the last 7 days
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-[300px]" />
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                Chart will be implemented here
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Channel Distribution</CardTitle>
            <CardDescription>
              Messages by communication channel
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-[300px]" />
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <MessageCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm">WhatsApp</span>
                  </div>
                  <Badge variant="secondary">75%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <MessageCircle className="h-4 w-4 text-blue-600" />
                    <span className="text-sm">SMS</span>
                  </div>
                  <Badge variant="secondary">20%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Phone className="h-4 w-4 text-purple-600" />
                    <span className="text-sm">Voice</span>
                  </div>
                  <Badge variant="secondary">5%</Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}