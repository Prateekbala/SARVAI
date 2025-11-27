'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { analyticsAPI } from '@/lib/api';
import { BarChart3, TrendingUp, FileText, Image, File, Mic, Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export function AnalyticsPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['analytics-stats'],
    queryFn: analyticsAPI.getDashboardStats,
  });

  const { data: popularSearches } = useQuery({
    queryKey: ['popular-searches'],
    queryFn: () => analyticsAPI.getPopularSearches(10),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  const contentTypeData = stats ? [
    { name: 'Text', value: stats.memories_by_type.text, color: '#3b82f6' },
    { name: 'Images', value: stats.memories_by_type.image, color: '#a855f7' },
    { name: 'PDFs', value: stats.memories_by_type.pdf, color: '#10b981' },
    { name: 'Audio', value: stats.memories_by_type.audio, color: '#f97316' },
  ] : [];

  const activityData = stats?.recent_activity || [];

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-fade-in-up">
      <div className="space-y-2">
        <h2 className="text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-500">Analytics</h2>
        <p className="text-muted-foreground text-lg">
          Insights into your memory usage and patterns
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="hover-lift border border-red-900/20 shadow-lg overflow-hidden group bg-gradient-to-br from-black to-gray-900">
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-red-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Total Memories</p>
                <p className="text-4xl font-bold tracking-tight">{stats?.total_memories || 0}</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-red-600 to-red-700 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300 shadow-red-900/50">
                <BarChart3 className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover-lift border border-orange-900/20 shadow-lg overflow-hidden group bg-gradient-to-br from-black to-gray-900">
          <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-orange-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Conversations</p>
                <p className="text-4xl font-bold tracking-tight">{stats?.total_conversations || 0}</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-orange-600 to-red-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300 shadow-orange-900/50">
                <TrendingUp className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover-lift border border-yellow-900/20 shadow-lg overflow-hidden group bg-gradient-to-br from-black to-gray-900">
          <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Messages</p>
                <p className="text-4xl font-bold tracking-tight">{stats?.total_messages || 0}</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-yellow-600 to-orange-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300 shadow-yellow-900/50">
                <FileText className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover-lift border border-rose-900/20 shadow-lg overflow-hidden group bg-gradient-to-br from-black to-gray-900">
          <div className="absolute inset-0 bg-gradient-to-br from-rose-500/10 to-rose-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Storage Used</p>
                <p className="text-4xl font-bold tracking-tight">{stats?.storage_used_mb.toFixed(1) || 0} MB</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-rose-600 to-red-700 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300 shadow-rose-900/50">
                <FileText className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Content Type Distribution */}
        <Card className="hover-lift border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl">Content Type Distribution</CardTitle>
            <CardDescription>Breakdown of your memories by type</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={contentTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {contentTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="hover-lift border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl">Recent Activity</CardTitle>
            <CardDescription>Memories created over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#a855f7" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Popular Searches */}
      <Card className="hover-lift border-0 shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl">Popular Searches</CardTitle>
          <CardDescription>Your most frequent search queries</CardDescription>
        </CardHeader>
        <CardContent>
          {popularSearches && popularSearches.searches.length > 0 ? (
            <div className="space-y-3">
              {popularSearches.searches.map((search, index) => (
                <div key={index} className="group flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800/50 dark:to-gray-800/80 rounded-xl hover:from-purple-50 hover:to-blue-50 dark:hover:from-purple-900/20 dark:hover:to-blue-900/20 transition-all duration-300 border border-transparent hover:border-purple-200 dark:hover:border-purple-700">
                  <div className="flex-1">
                    <p className="font-semibold text-base">{search.query}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Last searched: {new Date(search.last_searched).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-muted-foreground">{search.count} times</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              No search history yet
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
