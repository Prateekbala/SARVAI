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
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold mb-2">My Memories</h2>
          <p className="text-gray-600 dark:text-gray-400">
            {data?.total || 0} total memories stored
          </p>
        </div>
      </div>

      {data && data.memories.length > 0 ? (
        <>
          <div className="grid gap-4">
            {data.memories.map((memory) => {
              const Icon = contentTypeIcons[memory.content_type as keyof typeof contentTypeIcons];
              return (
                <Card key={memory.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg shrink-0">
                        <Icon className="h-6 w-6" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <Badge variant="secondary" className="capitalize">
                            {memory.content_type}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteMutation.mutate(memory.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4 text-red-600 dark:text-red-400" />
                          </Button>
                        </div>
                        <p className="text-sm leading-relaxed mb-2">
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
