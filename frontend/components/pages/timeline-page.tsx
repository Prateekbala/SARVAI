'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { analyticsAPI } from '@/lib/api';
import { FileText, Image, File, Mic, Loader2, Calendar } from 'lucide-react';

export function TimelinePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['timeline'],
    queryFn: () => analyticsAPI.getTimeline(),
  });

  const contentTypeIcons = {
    text: FileText,
    image: Image,
    pdf: File,
    audio: Mic,
  };

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
        <h2 className="text-3xl font-bold mb-2">Memory Timeline</h2>
        <p className="text-gray-600 dark:text-gray-400">
          View your memories organized by date
        </p>
      </div>

      {data && data.timeline.length > 0 ? (
        <div className="space-y-8">
          {data.timeline.map((group) => (
            <div key={group.date} className="relative">
              {/* Date Header */}
              <div className="sticky top-20 z-10 flex items-center gap-3 mb-4 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md py-2">
                <Calendar className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                <h3 className="text-lg font-semibold">
                  {new Date(group.date).toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </h3>
                <Badge variant="secondary">{group.memories.length} memories</Badge>
              </div>

              {/* Memories */}
              <div className="space-y-3 pl-8 border-l-2 border-gray-200 dark:border-gray-800">
                {group.memories.map((memory) => {
                  const Icon = contentTypeIcons[memory.content_type as keyof typeof contentTypeIcons];
                  return (
                    <Card key={memory.id} className="relative">
                      <div className="absolute -left-8.5 top-6 w-4 h-4 bg-purple-600 dark:bg-purple-400 rounded-full border-4 border-white dark:border-gray-950" />
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg shrink-0">
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="secondary" className="capitalize text-xs">
                                {memory.content_type}
                              </Badge>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {new Date(memory.created_at).toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-sm line-clamp-2">
                              {memory.content}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium mb-2">No memories yet</p>
            <p className="text-gray-600 dark:text-gray-400">
              Your timeline will appear here as you add memories
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
