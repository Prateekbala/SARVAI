'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { analyticsAPI, memoryAPI, conversationAPI } from '@/lib/api';
import { 
  FileText, 
  Image, 
  File, 
  Mic, 
  TrendingUp,
  MessageSquare,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { useAtom } from 'jotai';
import { currentPageAtom } from '@/lib/store';

export function DashboardHome() {
  const [, setCurrentPage] = useAtom(currentPageAtom);

  const { data: stats, isLoading, isError: statsError } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: analyticsAPI.getDashboardStats,
    retry: false,
  });

  const { data: recentMemories, isError: memoriesError } = useQuery({
    queryKey: ['recent-memories'],
    queryFn: () => memoryAPI.list(1, 5),
    retry: false,
  });

  const { data: conversations, isError: conversationsError } = useQuery({
    queryKey: ['recent-conversations'],
    queryFn: conversationAPI.list,
    retry: false,
  });

  const contentTypeIcons = {
    text: FileText,
    image: Image,
    pdf: File,
    audio: Mic,
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (statsError || memoriesError || conversationsError) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">Failed to load dashboard data</p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">Please check if the backend is running</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-linear-to-r from-purple-600 to-blue-600 rounded-lg p-6 text-white">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Welcome to Your Memory Hub</h2>
            <p className="text-purple-100 mb-4">
              You have {stats?.total_memories || 0} memories stored and ready to search
            </p>
            <div className="flex gap-3">
              <Button
                onClick={() => setCurrentPage('upload')}
                className="bg-white text-purple-600 hover:bg-purple-50"
              >
                Add Memory
              </Button>
              <Button
                onClick={() => setCurrentPage('chat')}
                variant="outline"
                className="border-white text-white hover:bg-white/20"
              >
                Ask AI
              </Button>
            </div>
          </div>
          <Sparkles className="h-12 w-12 text-purple-200" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: 'Text Memories',
            value: stats?.memories_by_type.text || 0,
            icon: FileText,
            color: 'text-blue-600 dark:text-blue-400',
            bgColor: 'bg-blue-100 dark:bg-blue-900/20',
          },
          {
            label: 'Images',
            value: stats?.memories_by_type.image || 0,
            icon: Image,
            color: 'text-purple-600 dark:text-purple-400',
            bgColor: 'bg-purple-100 dark:bg-purple-900/20',
          },
          {
            label: 'PDFs',
            value: stats?.memories_by_type.pdf || 0,
            icon: File,
            color: 'text-green-600 dark:text-green-400',
            bgColor: 'bg-green-100 dark:bg-green-900/20',
          },
          {
            label: 'Audio Files',
            value: stats?.memories_by_type.audio || 0,
            icon: Mic,
            color: 'text-orange-600 dark:text-orange-400',
            bgColor: 'bg-orange-100 dark:bg-orange-900/20',
          },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</p>
                  <p className="text-3xl font-bold mt-1">{stat.value}</p>
                </div>
                <div className={`${stat.bgColor} p-3 rounded-lg`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activity & Conversations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Memories */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Memories</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentPage('memories')}
              >
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
            <CardDescription>Your latest uploaded content</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentMemories?.memories.map((memory) => {
                const Icon = contentTypeIcons[memory.content_type as keyof typeof contentTypeIcons];
                return (
                  <div key={memory.id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                    <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{memory.content.slice(0, 100)}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {new Date(memory.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                );
              })}
              {(!recentMemories?.memories || recentMemories.memories.length === 0) && (
                <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                  No memories yet. Start by uploading content!
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Conversations */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Conversations</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentPage('chat')}
              >
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
            <CardDescription>Your AI chat history</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {conversations?.slice(0, 5).map((conversation) => (
                <div
                  key={conversation.id}
                  className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
                  onClick={() => setCurrentPage('chat')}
                >
                  <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                    <MessageSquare className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{conversation.title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {new Date(conversation.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
              {(!conversations || conversations.length === 0) && (
                <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                  No conversations yet. Start chatting with AI!
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks to get you started</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              className="h-auto flex-col gap-2 p-4"
              onClick={() => setCurrentPage('upload')}
            >
              <TrendingUp className="h-6 w-6" />
              <span>Upload Content</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col gap-2 p-4"
              onClick={() => setCurrentPage('search')}
            >
              <TrendingUp className="h-6 w-6" />
              <span>Search Memories</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col gap-2 p-4"
              onClick={() => setCurrentPage('chat')}
            >
              <MessageSquare className="h-6 w-6" />
              <span>Ask AI</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
