'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { memoryAPI } from '@/lib/api';
import { toast } from 'sonner';
import { FileText, Image, File, Mic, Trash2, Loader2, ExternalLink } from 'lucide-react';
import { useState } from 'react';

export function MemoriesPage() {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['memories', page],
    queryFn: () => memoryAPI.list(page, 20),
  });

  const deleteMutation = useMutation({
    mutationFn: memoryAPI.delete,
    onSuccess: () => {
      toast.success('Memory deleted');
      queryClient.invalidateQueries({ queryKey: ['memories'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onError: () => {
      toast.error('Failed to delete memory');
    },
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
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h2 className="text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-500">My Memories</h2>
          <p className="text-muted-foreground text-lg">
            {data?.total || 0} total memories stored
          </p>
        </div>
      </div>

      {data && data.memories.length > 0 ? (
        <>
          <div className="grid gap-4">
            {data.memories.map((memory, index) => {
              const Icon = contentTypeIcons[memory.content_type as keyof typeof contentTypeIcons];
              return (
                <Card key={memory.id} className="hover-lift border-0 shadow-lg overflow-hidden group" style={{ animationDelay: `${index * 50}ms` }}>
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <CardContent className="p-6 relative">
                    <div className="flex items-start gap-4">
                      <div className="p-4 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 rounded-xl shadow-md group-hover:scale-110 transition-transform duration-300 shrink-0">
                        <Icon className="h-7 w-7 text-gray-700 dark:text-gray-300" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4 mb-3">
                          <Badge variant="secondary" className="capitalize text-sm font-semibold">
                            {memory.content_type}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteMutation.mutate(memory.id)}
                            disabled={deleteMutation.isPending}
                            className="hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                          >
                            <Trash2 className="h-4 w-4 text-red-600 dark:text-red-400" />
                          </Button>
                        </div>
                        <p className="text-sm leading-relaxed mb-3 text-foreground/90">
                          {memory.content.slice(0, 300)}
                          {memory.content.length > 300 && '...'}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                          <span>{new Date(memory.created_at).toLocaleString()}</span>
                          {memory.file_path && (
                            <a
                              href={`http://localhost:8000${memory.file_path}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 hover:text-purple-600 dark:hover:text-purple-400"
                            >
                              View file
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Pagination */}
          {data.total > data.page_size && (
            <div className="flex justify-center gap-2">
              <Button
                variant="outline"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <span className="flex items-center px-4">
                Page {page} of {Math.ceil(data.total / data.page_size)}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil(data.total / data.page_size)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium mb-2">No memories yet</p>
            <p className="text-gray-600 dark:text-gray-400">
              Start by uploading some content
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
