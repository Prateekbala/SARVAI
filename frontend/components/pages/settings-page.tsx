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
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold mb-2">Settings</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your preferences and personalization
        </p>
      </div>

      {/* Boost Topics */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
            <CardTitle>Boost Topics</CardTitle>
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
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingDown className="h-5 w-5 text-red-600 dark:text-red-400" />
            <CardTitle>Suppress Topics</CardTitle>
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
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            <CardTitle>Account Information</CardTitle>
          </div>
          <CardDescription>
            Your account details and preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>User ID</Label>
            <Input value={preferences?.user_id || ''} disabled />
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
