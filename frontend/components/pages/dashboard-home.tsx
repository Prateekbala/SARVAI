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
  Sparkles,
  Upload
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
    <div className="space-y-6 animate-fade-in-up">
      {/* Welcome Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-black via-gray-900 to-red-950 rounded-2xl p-8 text-white shadow-2xl border border-red-900/20">
        <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:20px_20px]" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-red-600/10 rounded-full blur-3xl" />
        <div className="relative flex items-start justify-between">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-500/10 rounded-full backdrop-blur-sm border border-red-500/30">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-sm font-medium">System Active</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Welcome to Your Memory Hub
            </h2>
            <p className="text-gray-300 text-lg max-w-2xl">
              You have <span className="font-bold text-red-500">{stats?.total_memories || 0}</span> memories stored and ready to search with AI-powered intelligence
            </p>
            <div className="flex gap-3 pt-2">
              <Button
                onClick={() => setCurrentPage('upload')}
                className="bg-red-600 text-white hover:bg-red-700 shadow-lg hover:shadow-xl transition-all hover:scale-105 border border-red-500"
              >
                <FileText className="mr-2 h-4 w-4" />
                Add Memory
              </Button>
              <Button
                onClick={() => setCurrentPage('chat')}
                variant="outline"
                className="border-red-500/50 text-red-400 hover:bg-red-950/50 backdrop-blur-sm transition-all hover:scale-105"
              >
                <MessageSquare className="mr-2 h-4 w-4" />
                Ask AI
              </Button>
            </div>
          </div>
          <Sparkles className="h-16 w-16 text-red-400/50 animate-float" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          {
            label: 'Text Memories',
            value: stats?.memories_by_type.text || 0,
            icon: FileText,
            color: 'text-red-400',
            bgColor: 'bg-gradient-to-br from-red-600 to-red-700',
            gradient: 'from-red-500/10 to-red-600/10',
          },
          {
            label: 'Images',
            value: stats?.memories_by_type.image || 0,
            icon: Image,
            color: 'text-orange-400',
            bgColor: 'bg-gradient-to-br from-orange-600 to-red-600',
            gradient: 'from-orange-500/10 to-red-600/10',
          },
          {
            label: 'PDFs',
            value: stats?.memories_by_type.pdf || 0,
            icon: File,
            color: 'text-yellow-400',
            bgColor: 'bg-gradient-to-br from-yellow-600 to-orange-600',
            gradient: 'from-yellow-500/10 to-orange-600/10',
          },
          {
            label: 'Audio Files',
            value: stats?.memories_by_type.audio || 0,
            icon: Mic,
            color: 'text-rose-400',
            bgColor: 'bg-gradient-to-br from-rose-600 to-red-700',
            gradient: 'from-rose-500/10 to-red-700/10',
          },
        ].map((stat, index) => (
          <Card key={stat.label} className="hover-lift border-0 shadow-lg overflow-hidden group" style={{ animationDelay: `${index * 75}ms` }}>
            <div className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
            <CardContent className="p-6 relative">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                  <p className="text-4xl font-bold tracking-tight">{stat.value}</p>
                </div>
                <div className={`${stat.bgColor} p-4 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                  <stat.icon className="h-7 w-7 text-white" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activity & Conversations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Memories */}
        <Card className="hover-lift border-0 shadow-lg">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl">Recent Memories</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentPage('memories')}
                className="hover:bg-purple-100 dark:hover:bg-purple-900/20 transition-colors"
              >
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
            <CardDescription>Your latest uploaded content</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentMemories?.memories.map((memory, index) => {
                const Icon = contentTypeIcons[memory.content_type as keyof typeof contentTypeIcons];
                return (
                  <div 
                    key={memory.id} 
                    className="group flex items-start gap-3 p-4 rounded-xl hover:bg-gradient-to-r hover:from-red-950/30 hover:to-gray-900/50 transition-all duration-300 cursor-pointer border border-transparent hover:border-red-900/50 shadow-sm hover:shadow-md"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <div className="p-2.5 bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-sm border border-red-900/20">
                      <Icon className="h-5 w-5 text-gray-700 dark:text-gray-300" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium leading-relaxed line-clamp-2">{memory.content.slice(0, 100)}</p>
                      <p className="text-xs text-muted-foreground mt-1.5 flex items-center gap-1">
                        <span className="w-1 h-1 rounded-full bg-green-500" />
                        {new Date(memory.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                );
              })}
              {(!recentMemories?.memories || recentMemories.memories.length === 0) && (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                  <p className="text-sm text-muted-foreground">
                    No memories yet. Start by uploading content!
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Conversations */}
        <Card className="hover-lift border-0 shadow-lg">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl">Recent Conversations</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentPage('chat')}
                className="hover:bg-purple-100 dark:hover:bg-purple-900/20 transition-colors"
              >
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
            <CardDescription>Your AI chat history</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {conversations?.slice(0, 5).map((conversation, index) => (
                <div
                  key={conversation.id}
                  className="group flex items-start gap-3 p-4 rounded-xl hover:bg-gradient-to-r hover:from-red-950/30 hover:to-orange-950/30 transition-all duration-300 cursor-pointer border border-transparent hover:border-red-900/50 shadow-sm hover:shadow-md"
                  onClick={() => setCurrentPage('chat')}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="p-2.5 bg-gradient-to-br from-red-900/50 to-orange-900/50 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-sm border border-red-800/30">
                    <MessageSquare className="h-5 w-5 text-red-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{conversation.title}</p>
                    <p className="text-xs text-muted-foreground mt-1.5 flex items-center gap-1">
                      <span className="w-1 h-1 rounded-full bg-purple-500" />
                      {new Date(conversation.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
              {(!conversations || conversations.length === 0) && (
                <div className="text-center py-12">
                  <MessageSquare className="h-12 w-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                  <p className="text-sm text-muted-foreground">
                    No conversations yet. Start chatting with AI!
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="hover-lift border border-red-900/20 shadow-lg overflow-hidden bg-gradient-to-br from-black to-gray-900">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-red-600/10 to-orange-600/10 rounded-full blur-3xl -z-10" />
        <CardHeader>
          <CardTitle className="text-xl">Quick Actions</CardTitle>
          <CardDescription>Common tasks to get you started</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              className="h-auto flex-col gap-3 p-6 hover:bg-gradient-to-br hover:from-red-950/50 hover:to-red-900/50 border-2 border-red-900/30 hover:border-red-600 transition-all duration-300 group"
              onClick={() => setCurrentPage('upload')}
            >
              <div className="p-3 bg-gradient-to-br from-red-600 to-red-700 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-red-900/50">
                <Upload className="h-6 w-6 text-white" />
              </div>
              <span className="font-semibold">Upload Content</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col gap-3 p-6 hover:bg-gradient-to-br hover:from-orange-950/50 hover:to-orange-900/50 border-2 border-orange-900/30 hover:border-orange-600 transition-all duration-300 group"
              onClick={() => setCurrentPage('search')}
            >
              <div className="p-3 bg-gradient-to-br from-orange-600 to-red-600 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-orange-900/50">
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
              <span className="font-semibold">Search Memories</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col gap-3 p-6 hover:bg-gradient-to-br hover:from-rose-950/50 hover:to-rose-900/50 border-2 border-rose-900/30 hover:border-rose-600 transition-all duration-300 group"
              onClick={() => setCurrentPage('chat')}
            >
              <div className="p-3 bg-gradient-to-br from-rose-600 to-red-700 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-rose-900/50">
                <MessageSquare className="h-6 w-6 text-white" />
              </div>
              <span className="font-semibold">Ask AI</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
