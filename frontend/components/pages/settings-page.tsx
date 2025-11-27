'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { preferencesAPI } from '@/lib/api';
import { toast } from 'sonner';
import { Settings, Plus, X, Loader2, TrendingUp, TrendingDown } from 'lucide-react';

export function SettingsPage() {
  const [newBoostTopic, setNewBoostTopic] = useState('');
  const [newSuppressTopic, setNewSuppressTopic] = useState('');
  const queryClient = useQueryClient();

  const { data: preferences, isLoading } = useQuery({
    queryKey: ['preferences'],
    queryFn: preferencesAPI.get,
  });

  const addBoostMutation = useMutation({
    mutationFn: preferencesAPI.addBoostTopic,
    onSuccess: () => {
      toast.success('Topic added to boost list');
      setNewBoostTopic('');
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
    },
    onError: () => {
      toast.error('Failed to add topic');
    },
  });

  const removeBoostMutation = useMutation({
    mutationFn: preferencesAPI.removeBoostTopic,
    onSuccess: () => {
      toast.success('Topic removed from boost list');
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
    },
  });

  const addSuppressMutation = useMutation({
    mutationFn: preferencesAPI.addSuppressTopic,
    onSuccess: () => {
      toast.success('Topic added to suppress list');
      setNewSuppressTopic('');
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
    },
    onError: () => {
      toast.error('Failed to add topic');
    },
  });

  const removeSuppressMutation = useMutation({
    mutationFn: preferencesAPI.removeSuppressTopic,
    onSuccess: () => {
      toast.success('Topic removed from suppress list');
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in-up">
      <div className="space-y-2">
        <h2 className="text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-500">Settings</h2>
        <p className="text-muted-foreground text-lg">
          Manage your preferences and personalization
        </p>
      </div>

      {/* Boost Topics */}
      <Card className="hover-lift border border-green-900/20 shadow-lg overflow-hidden bg-gradient-to-br from-black to-gray-900">
        <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5" />
        <CardHeader className="relative">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-green-600 to-emerald-700 rounded-lg shadow-lg shadow-green-900/50">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <CardTitle className="text-xl">Boost Topics</CardTitle>
          </div>
          <CardDescription>
            Topics to prioritize in search results and recommendations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {preferences?.boost_topics.map((topic) => (
              <Badge key={topic} variant="secondary" className="text-sm px-3 py-1">
                {topic}
                <button
                  onClick={() => removeBoostMutation.mutate(topic)}
                  className="ml-2 hover:text-red-600 dark:hover:text-red-400"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            {(!preferences?.boost_topics || preferences.boost_topics.length === 0) && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No boost topics yet
              </p>
            )}
          </div>

          <div className="flex gap-2">
            <Input
              placeholder="Add topic (e.g., 'machine learning')"
              value={newBoostTopic}
              onChange={(e) => setNewBoostTopic(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && newBoostTopic.trim()) {
                  addBoostMutation.mutate(newBoostTopic.trim());
                }
              }}
            />
            <Button
              onClick={() => {
                if (newBoostTopic.trim()) {
                  addBoostMutation.mutate(newBoostTopic.trim());
                }
              }}
              disabled={addBoostMutation.isPending || !newBoostTopic.trim()}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Suppress Topics */}
      <Card className="hover-lift border border-red-900/20 shadow-lg overflow-hidden bg-gradient-to-br from-black to-gray-900">
        <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-orange-500/5" />
        <CardHeader className="relative">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-red-600 to-orange-700 rounded-lg shadow-lg shadow-red-900/50">
              <TrendingDown className="h-5 w-5 text-white" />
            </div>
            <CardTitle className="text-xl">Suppress Topics</CardTitle>
          </div>
          <CardDescription>
            Topics to de-prioritize in search results
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {preferences?.suppress_topics.map((topic) => (
              <Badge key={topic} variant="secondary" className="text-sm px-3 py-1">
                {topic}
                <button
                  onClick={() => removeSuppressMutation.mutate(topic)}
                  className="ml-2 hover:text-red-600 dark:hover:text-red-400"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            {(!preferences?.suppress_topics || preferences.suppress_topics.length === 0) && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No suppress topics yet
              </p>
            )}
          </div>

          <div className="flex gap-2">
            <Input
              placeholder="Add topic to suppress"
              value={newSuppressTopic}
              onChange={(e) => setNewSuppressTopic(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && newSuppressTopic.trim()) {
                  addSuppressMutation.mutate(newSuppressTopic.trim());
                }
              }}
            />
            <Button
              onClick={() => {
                if (newSuppressTopic.trim()) {
                  addSuppressMutation.mutate(newSuppressTopic.trim());
                }
              }}
              disabled={addSuppressMutation.isPending || !newSuppressTopic.trim()}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Account Info */}
      <Card className="hover-lift border border-gray-800 shadow-lg overflow-hidden bg-gradient-to-br from-black to-gray-900">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-500/5 to-gray-600/5" />
        <CardHeader className="relative">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg shadow-lg">
              <Settings className="h-5 w-5 text-white" />
            </div>
            <CardTitle className="text-xl">Account Information</CardTitle>
          </div>
          <CardDescription>
            Your account details and preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Namespace</Label>
            <Input value={preferences?.namespace || ''} disabled />
          </div>
          <div className="space-y-2">
            <Label>Created</Label>
            <Input
              value={preferences ? new Date(preferences.created_at).toLocaleDateString() : ''}
              disabled
            />
          </div>
          <div className="space-y-2">
            <Label>Last Updated</Label>
            <Input
              value={preferences ? new Date(preferences.updated_at).toLocaleDateString() : ''}
              disabled
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
