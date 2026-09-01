// src/app/(dashboard)/billing/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  CreditCard, TrendingUp, DollarSign, MessageSquare, 
  Phone, AlertCircle, Check, X
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';


interface UsageData {
  period_start: string;
  period_end: string;
  usage: {
    conversations: number;
    messages: number;
    voice_minutes: number;
    estimated_cost: number;
  };
  limits: {
    conversations: number;
    messages: number;
    voice_minutes: number;
  };
  subscription_plan: string;
}

interface CostBreakdown {
  month: number;
  year: number;
  daily_breakdown: Array<{
    date: string;
    whatsapp: number;
    sms: number;
    voice: number;
    total: number;
  }>;
  totals: {
    whatsapp: number;
    sms: number;
    voice: number;
    total: number;
  };
}

const SUBSCRIPTION_TIERS = {
  free: {
    name: 'Free',
    price: 0,
    features: ['1,000 messages/month', '100 voice minutes', '1 agent', 'Community support'],
  },
  starter: {
    name: 'Starter',
    price: 99,
    features: ['10,000 messages/month', '1,000 voice minutes', '5 agents', 'Email support'],
  },
  professional: {
    name: 'Professional',
    price: 299,
    features: ['50,000 messages/month', '5,000 voice minutes', '20 agents', 'Priority support'],
  },
  enterprise: {
    name: 'Enterprise',
    price: 999,
    features: ['Unlimited messages', 'Unlimited voice', 'Unlimited agents', 'Dedicated support'],
  },
};

export default function BillingPage() {
  const [loading, setLoading] = useState(true);
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown | null>(null);
  const [currentTier, setCurrentTier] = useState('free');

  useEffect(() => {
    fetchUsageData();
    fetchCostBreakdown();
  }, []);

  const fetchUsageData = async () => {
    try {
      const response = await apiClient.get('/billing/usage/current');
      setUsageData(response.data);
      setCurrentTier(response.data.subscription_plan.toLowerCase());
    } catch (error) {
      toast.error('Failed to load usage data');
    } finally {
      setLoading(false);
    }
  };

  const fetchCostBreakdown = async () => {
    try {
      const response = await apiClient.get('/billing/cost-breakdown');
      setCostBreakdown(response.data);
    } catch (error) {
      console.error('Failed to load cost breakdown');
    }
  };

  const handleUpgrade = async (tier: string) => {
    try {
      await apiClient.post('/billing/subscription/upgrade', { tier });
      toast.success(`Successfully upgraded to ${tier} plan`);
      fetchUsageData();
    } catch (error) {
      toast.error('Failed to upgrade subscription');
    }
  };

  const getUsagePercentage = (used: number, limit: number) => {
    if (limit === -1) return 0; // Unlimited
    return Math.min((used / limit) * 100, 100);
  };

  const getUsageColor = (percentage: number) => {
    if (percentage < 50) return 'text-green-600';
    if (percentage < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Billing & Usage</h1>
        <p className="text-muted-foreground">
          Manage your subscription and monitor usage
        </p>
      </div>

      {/* Current Usage */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Messages</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageData?.usage.messages.toLocaleString()}
            </div>
            <Progress 
              value={getUsagePercentage(
                usageData?.usage.messages || 0,
                usageData?.limits.messages || 1
              )} 
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              of {usageData?.limits.messages === -1 ? 'Unlimited' : usageData?.limits.messages.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Voice Minutes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageData?.usage.voice_minutes.toLocaleString()}
            </div>
            <Progress 
              value={getUsagePercentage(
                usageData?.usage.voice_minutes || 0,
                usageData?.limits.voice_minutes || 1
              )} 
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              of {usageData?.limits.voice_minutes === -1 ? 'Unlimited' : usageData?.limits.voice_minutes.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Estimated Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${usageData?.usage.estimated_cost.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              Current billing period
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Subscription Plans */}
      <Card>
        <CardHeader>
          <CardTitle>Subscription Plans</CardTitle>
          <CardDescription>Choose the plan that fits your needs</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            {Object.entries(SUBSCRIPTION_TIERS).map(([key, tier]) => (
              <div
                key={key}
                className={cn(
                  'relative rounded-lg border p-4',
                  currentTier === key && 'border-primary bg-primary/5'
                )}
              >
                {currentTier === key && (
                  <Badge className="absolute -top-2 right-4">Current Plan</Badge>
                )}
                <div className="mb-4">
                  <h3 className="font-semibold">{tier.name}</h3>
                  <div className="mt-2">
                    <span className="text-3xl font-bold">${tier.price}</span>
                    <span className="text-muted-foreground">/month</span>
                  </div>
                </div>
                <ul className="space-y-2 mb-4">
                  {tier.features.map((feature, i) => (
                    <li key={i} className="flex items-center text-sm">
                      <Check className="h-4 w-4 mr-2 text-green-600" />
                      {feature}
                    </li>
                  ))}
                </ul>
                {currentTier !== key && (
                  <Button
                    className="w-full"
                    variant={tier.price > SUBSCRIPTION_TIERS[currentTier as keyof typeof SUBSCRIPTION_TIERS].price ? 'default' : 'outline'}
                    onClick={() => handleUpgrade(key)}
                  >
                    {tier.price > SUBSCRIPTION_TIERS[currentTier as keyof typeof SUBSCRIPTION_TIERS].price ? 'Upgrade' : 'Downgrade'}
                  </Button>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Cost Breakdown */}
      {costBreakdown && (
        <Card>
          <CardHeader>
            <CardTitle>Cost Breakdown</CardTitle>
            <CardDescription>
              {format(new Date(costBreakdown.year, costBreakdown.month - 1), 'MMMM yyyy')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4 mb-6">
              <div className="text-center">
                <p className="text-sm text-muted-foreground">WhatsApp</p>
                <p className="text-2xl font-bold">${costBreakdown.totals.whatsapp.toFixed(2)}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground">SMS</p>
                <p className="text-2xl font-bold">${costBreakdown.totals.sms.toFixed(2)}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground">Voice</p>
                <p className="text-2xl font-bold">${costBreakdown.totals.voice.toFixed(2)}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground">Total</p>
                <p className="text-2xl font-bold text-primary">
                  ${costBreakdown.totals.total.toFixed(2)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}