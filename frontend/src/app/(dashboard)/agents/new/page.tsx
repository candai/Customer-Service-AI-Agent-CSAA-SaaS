//new agent creation page
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Save, Bot } from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { toast } from 'sonner';

export default function NewAgentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt: '',
    welcome_message: 'Hello! How can I help you today?',
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    max_tokens: 500,
    language: 'en',
    personality_traits: 'Professional, helpful, and friendly',
    whatsapp_enabled: false,
    whatsapp_number: '',
    sms_enabled: false,
    sms_number: '',
    voice_enabled: false,
    voice_number: '',
    voice_id: '',
    response_delay_seconds: 1,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.name || !formData.system_prompt) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);

    try {
      const response = await apiClient.post('/agents/', formData);
      
      if (response.data.id) {
        toast.success('Agent created successfully');
        router.push('/agents');
      }
    } catch (error: any) {
      console.error('Error creating agent:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.error || 
                          'Failed to create agent';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center mb-8">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push('/agents')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Create New Agent</h1>
          <p className="text-muted-foreground">
            Configure your AI agent's behavior and capabilities
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Tabs defaultValue="general" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="ai">AI Settings</TabsTrigger>
            <TabsTrigger value="channels">Channels</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
                <CardDescription>
                  Set up your agent's identity and behavior
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="name">Agent Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Customer Support Agent"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="language">Language</Label>
                    <Select
                      value={formData.language}
                      onValueChange={(value) => setFormData({ ...formData, language: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="es">Spanish</SelectItem>
                        <SelectItem value="fr">French</SelectItem>
                        <SelectItem value="de">German</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Describe what this agent does..."
                    rows={3}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="system_prompt">System Prompt *</Label>
                  <Textarea
                    id="system_prompt"
                    value={formData.system_prompt}
                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                    placeholder="You are a helpful customer support agent..."
                    rows={5}
                    required
                  />
                  <p className="text-sm text-muted-foreground">
                    This defines how your agent behaves and responds
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="welcome_message">Welcome Message</Label>
                  <Textarea
                    id="welcome_message"
                    value={formData.welcome_message}
                    onChange={(e) => setFormData({ ...formData, welcome_message: e.target.value })}
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="personality_traits">Personality Traits *</Label>
                  <Input
                    id="personality_traits"
                    value={formData.personality_traits}
                    onChange={(e) => setFormData({ ...formData, personality_traits: e.target.value })}
                    placeholder="Professional, helpful, friendly..."
                    required
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ai" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>AI Configuration</CardTitle>
                <CardDescription>
                  Fine-tune the AI model parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="model">Model</Label>
                  <Select
                    value={formData.model}
                    onValueChange={(value) => setFormData({ ...formData, model: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                      <SelectItem value="gpt-4">GPT-4</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <Label htmlFor="temperature">Temperature</Label>
                    <span className="text-sm text-muted-foreground">{formData.temperature}</span>
                  </div>
                  <Slider
                    id="temperature"
                    min={0}
                    max={2}
                    step={0.1}
                    value={[formData.temperature]}
                    onValueChange={(value) => setFormData({ ...formData, temperature: value[0] })}
                  />
                  <p className="text-sm text-muted-foreground">
                    Lower values make output more focused and deterministic
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <Label htmlFor="max_tokens">Max Tokens</Label>
                    <span className="text-sm text-muted-foreground">{formData.max_tokens}</span>
                  </div>
                  <Slider
                    id="max_tokens"
                    min={50}
                    max={2000}
                    step={50}
                    value={[formData.max_tokens]}
                    onValueChange={(value) => setFormData({ ...formData, max_tokens: value[0] })}
                  />
                  <p className="text-sm text-muted-foreground">
                    Maximum length of the response
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <Label htmlFor="response_delay">Response Delay (seconds)</Label>
                    <span className="text-sm text-muted-foreground">{formData.response_delay_seconds}s</span>
                  </div>
                  <Slider
                    id="response_delay"
                    min={0}
                    max={5}
                    step={1}
                    value={[formData.response_delay_seconds]}
                    onValueChange={(value) => setFormData({ ...formData, response_delay_seconds: value[0] })}
                  />
                  <p className="text-sm text-muted-foreground">
                    Simulate typing delay for more natural conversation
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="channels" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Communication Channels</CardTitle>
                <CardDescription>
                  Configure which channels this agent can use
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* WhatsApp */}
                <div className="space-y-4 p-4 border rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>WhatsApp</Label>
                      <p className="text-sm text-muted-foreground">
                        Enable WhatsApp messaging
                      </p>
                    </div>
                    <Switch
                      checked={formData.whatsapp_enabled}
                      onCheckedChange={(checked) => setFormData({ ...formData, whatsapp_enabled: checked })}
                    />
                  </div>
                  {formData.whatsapp_enabled && (
                    <Input
                      placeholder="WhatsApp phone number (e.g., +14155238886)"
                      value={formData.whatsapp_number}
                      onChange={(e) => setFormData({ ...formData, whatsapp_number: e.target.value })}
                    />
                  )}
                </div>

                {/* SMS */}
                <div className="space-y-4 p-4 border rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>SMS</Label>
                      <p className="text-sm text-muted-foreground">
                        Enable SMS messaging
                      </p>
                    </div>
                    <Switch
                      checked={formData.sms_enabled}
                      onCheckedChange={(checked) => setFormData({ ...formData, sms_enabled: checked })}
                    />
                  </div>
                  {formData.sms_enabled && (
                    <Input
                      placeholder="SMS phone number"
                      value={formData.sms_number}
                      onChange={(e) => setFormData({ ...formData, sms_number: e.target.value })}
                    />
                  )}
                </div>

                {/* Voice */}
                <div className="space-y-4 p-4 border rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Voice</Label>
                      <p className="text-sm text-muted-foreground">
                        Enable voice calls
                      </p>
                    </div>
                    <Switch
                      checked={formData.voice_enabled}
                      onCheckedChange={(checked) => setFormData({ ...formData, voice_enabled: checked })}
                    />
                  </div>
                  {formData.voice_enabled && (
                    <div className="space-y-4">
                      <Input
                        placeholder="Voice phone number"
                        value={formData.voice_number}
                        onChange={(e) => setFormData({ ...formData, voice_number: e.target.value })}
                      />
                      <Input
                        placeholder="ElevenLabs Voice ID (optional)"
                        value={formData.voice_id || ''}
                        onChange={(e) => setFormData({ ...formData, voice_id: e.target.value })}
                      />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Actions */}
        <div className="flex justify-end space-x-4 mt-8">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push('/agents')}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            <Save className="mr-2 h-4 w-4" />
            {loading ? 'Creating...' : 'Create Agent'}
          </Button>
        </div>
      </form>
    </div>
  );
}