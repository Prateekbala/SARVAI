'use client';

import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { conversationAPI, ragAPI } from '@/lib/api';
import { toast } from 'sonner';
import { 
  MessageSquare, 
  Send, 
  Loader2, 
  Plus, 
  FileText, 
  Image, 
  File, 
  Mic,
  Globe,
  Bot,
  User
} from 'lucide-react';
import type { ConversationWithMessages } from '@/lib/types';

export function ChatPage() {
  const [input, setInput] = useState('');
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [streamingAnswer, setStreamingAnswer] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: conversationAPI.list,
  });

  const { data: currentConversation } = useQuery({
    queryKey: ['conversation', currentConversationId],
    queryFn: () => conversationAPI.get(currentConversationId!),
    enabled: !!currentConversationId,
  });

  const createConversationMutation = useMutation({
    mutationFn: () => conversationAPI.create('New Conversation'),
    onSuccess: (data) => {
      setCurrentConversationId(data.id);
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  const askMutation = useMutation({
    mutationFn: async (question: string) => {
      setIsStreaming(true);
      setStreamingAnswer('');

      await ragAPI.askStream(
        {
          question,
          conversation_id: currentConversationId || undefined,
          enable_web_search: true,
        },
        (chunk) => {
          setStreamingAnswer((prev) => prev + chunk);
        },
        (conversationId) => {
          setIsStreaming(false);
          setCurrentConversationId(conversationId);
          queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] });
          queryClient.invalidateQueries({ queryKey: ['conversations'] });
        },
        (error) => {
          setIsStreaming(false);
          toast.error(error);
        }
      );
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const question = input;
    setInput('');
    
    await askMutation.mutateAsync(question);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentConversation?.messages, streamingAnswer]);

  const contentTypeIcons = {
    text: FileText,
    image: Image,
    pdf: File,
    audio: Mic,
  };

  return (
    <div className="flex gap-6 h-[calc(100vh-8rem)] animate-fade-in-up">
      {/* Conversations Sidebar */}
      <Card className="w-80 flex flex-col border-0 shadow-lg">
        <CardContent className="p-4 flex flex-col h-full">
          <Button
            onClick={() => createConversationMutation.mutate()}
            className="w-full mb-4 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-lg hover:shadow-xl transition-all hover:scale-105 border border-red-500"
            disabled={createConversationMutation.isPending}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Chat
          </Button>

          <ScrollArea className="flex-1">
            <div className="space-y-2">
              {conversations?.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setCurrentConversationId(conv.id)}
                  className={`w-full text-left p-3 rounded-xl transition-all duration-300 ${
                    currentConversationId === conv.id
                      ? 'bg-gradient-to-r from-red-900/50 to-orange-900/50 text-white shadow-md border-2 border-red-600'
                      : 'hover:bg-gray-900 border-2 border-transparent hover:border-red-900/50'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <MessageSquare className="h-4 w-4 mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{conv.title}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {new Date(conv.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col border border-red-900/20 shadow-lg">
        <CardContent className="p-6 flex flex-col h-full bg-gradient-to-br from-black to-gray-900">
          {currentConversation ? (
            <>
              {/* Messages */}
              <ScrollArea className="flex-1 pr-4" ref={scrollRef}>
                <div className="space-y-6">
                  {currentConversation.messages.map((message, index) => (
                    <div key={message.id} className="flex gap-4 animate-fade-in-up" style={{ animationDelay: `${index * 50}ms` }}>
                      <div className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-lg ${
                        message.role === 'user'
                          ? 'bg-gradient-to-br from-red-600 to-red-700'
                          : 'bg-gradient-to-br from-orange-600 to-red-600'
                      }`}>
                        {message.role === 'user' ? (
                          <User className="h-5 w-5 text-white" />
                        ) : (
                          <Bot className="h-5 w-5 text-white" />
                        )}
                      </div>
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-base">
                            {message.role === 'user' ? 'You' : 'AI Assistant'}
                          </span>
                          {message.meta_data?.web_search_used && (
                            <Badge variant="secondary" className="text-xs">
                              <Globe className="h-3 w-3 mr-1" />
                              Web Search
                            </Badge>
                          )}
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-sm">
                          {message.content}
                        </div>
                        {message.meta_data?.sources_count && message.meta_data.sources_count > 0 && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {message.meta_data.sources_count} sources cited
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {/* Streaming Message */}
                  {isStreaming && streamingAnswer && (
                    <div className="flex gap-4">
                      <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-blue-100 dark:bg-blue-900/20">
                        <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div className="flex-1 space-y-2">
                        <span className="font-medium text-sm">AI Assistant</span>
                        <div className="prose dark:prose-invert max-w-none text-sm">
                          {streamingAnswer}
                          <span className="inline-block w-2 h-4 bg-purple-600 animate-pulse ml-1" />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>

              <Separator className="my-4" />

              {/* Input */}
              <form onSubmit={handleSubmit} className="flex gap-3">
                <Input
                  placeholder="Ask anything about your memories..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={isStreaming}
                  className="flex-1 h-12 text-base border-2 focus:border-red-500 transition-all bg-gray-900/50"
                />
                <Button 
                  type="submit" 
                  disabled={isStreaming || !input.trim()}
                  className="h-12 px-6 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-lg hover:shadow-xl transition-all hover:scale-105 border border-red-500"
                >
                  {isStreaming ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </Button>
              </form>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-medium mb-2">Start a Conversation</p>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Create a new chat or select an existing one
                </p>
                <Button onClick={() => createConversationMutation.mutate()}>
                  <Plus className="mr-2 h-4 w-4" />
                  New Chat
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
