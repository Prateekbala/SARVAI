'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { searchAPI } from '@/lib/api';
import { Search, FileText, Image, File, Mic, Loader2, ExternalLink } from 'lucide-react';

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [contentType, setContentType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['search', searchQuery, contentType],
    queryFn: () => searchAPI.search(searchQuery, 20, contentType === 'all' ? undefined : contentType),
    enabled: !!searchQuery,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchQuery(query);
      refetch();
    }
  };

  const contentTypeIcons = {
    text: FileText,
    image: Image,
    pdf: File,
    audio: Mic,
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold mb-2">Search Memories</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Find anything using semantic search
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  placeholder="What are you looking for?"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="h-12 text-lg"
                />
              </div>
              <Select value={contentType} onValueChange={setContentType}>
                <SelectTrigger className="w-40 h-12">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="image">Images</SelectItem>
                  <SelectItem value="pdf">PDFs</SelectItem>
                  <SelectItem value="audio">Audio</SelectItem>
                </SelectContent>
              </Select>
              <Button type="submit" size="lg" disabled={isLoading}>
                {isLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <>
                    <Search className="mr-2 h-5 w-5" />
                    Search
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Search Results */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
        </div>
      )}

      {data && data.results.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Found {data.total_results} results for "{data.query}"
            </p>
          </div>

          <div className="space-y-4">
            {data.results.map((result) => {
              const Icon = contentTypeIcons[result.content_type as keyof typeof contentTypeIcons];
              return (
                <Card key={result.memory_id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg shrink-0">
                        <Icon className="h-6 w-6" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <Badge variant="secondary" className="capitalize">
                            {result.content_type}
                          </Badge>
                          <Badge className={getScoreColor(result.similarity)}>
                            {Math.round(result.similarity * 100)}% match
                          </Badge>
                        </div>
                        <p className="text-sm leading-relaxed mb-2">
                          {result.content.slice(0, 400)}
                          {result.content.length > 400 && '...'}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                          <span>{new Date(result.created_at).toLocaleDateString()}</span>
                          {result.file_path && (
                            <a
                              href={`http://localhost:8000${result.file_path}`}
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
        </div>
      )}

      {data && data.results.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium mb-2">No results found</p>
            <p className="text-gray-600 dark:text-gray-400">
              Try different keywords or upload more content
            </p>
          </CardContent>
        </Card>
      )}

      {!searchQuery && (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium mb-2">Start Searching</p>
            <p className="text-gray-600 dark:text-gray-400">
              Enter a query to search across all your memories
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
