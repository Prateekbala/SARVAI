'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { 
  Brain, 
  Image, 
  FileText, 
  Mic, 
  Search, 
  MessageSquare, 
  Zap, 
  Shield, 
  Globe,
  ArrowRight,
  Sparkles,
  Database,
  Layers
} from 'lucide-react';

export default function Home() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Brain className="h-8 w-8 text-purple-600 dark:text-purple-400" />
              <span className="text-2xl font-bold bg-linear-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                SarvAI
              </span>
            </div>
            <div className="flex items-center gap-4">
              <Button onClick={() => router.push('/dashboard')} variant="ghost">Go to Dashboard</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 dark:bg-purple-900/30 rounded-full mb-6">
            <Sparkles className="h-4 w-4 text-purple-600 dark:text-purple-400" />
            <span className="text-sm font-medium text-purple-900 dark:text-purple-100">
              AI Memory Infrastructure
            </span>
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
            Remember Everything
            <br />
            <span className="bg-linear-to-r from-purple-600 via-blue-600 to-cyan-600 bg-clip-text text-transparent">
              With AI
            </span>
          </h1>
          
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
            A multi-modal AI memory system that remembers text, images, PDFs, and audio. 
            Search semantically and get AI-powered answers from your personal knowledge base.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" onClick={() => router.push('/dashboard')} className="text-lg">
              Go to Dashboard
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Multi-Modal Memory</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Upload any format, search everything, remember forever
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: FileText,
                title: 'Text',
                description: 'Notes, documents, and articles',
                color: 'text-blue-600 dark:text-blue-400',
              },
              {
                icon: Image,
                title: 'Images',
                description: 'Photos with OCR extraction',
                color: 'text-purple-600 dark:text-purple-400',
              },
              {
                icon: FileText,
                title: 'PDFs',
                description: 'Documents with smart chunking',
                color: 'text-green-600 dark:text-green-400',
              },
              {
                icon: Mic,
                title: 'Audio',
                description: 'Voice notes with transcription',
                color: 'text-orange-600 dark:text-orange-400',
              },
            ].map((feature) => (
              <Card key={feature.title} className="border-gray-200 dark:border-gray-800 hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <feature.icon className={`h-12 w-12 ${feature.color} mb-4`} />
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            {[
              {
                icon: Search,
                title: 'Semantic Search',
                description: 'Find memories by meaning, not just keywords. Our vector search understands context.',
              },
              {
                icon: MessageSquare,
                title: 'AI Chat Interface',
                description: 'Ask questions about your memories and get intelligent, contextual answers with citations.',
              },
              {
                icon: Globe,
                title: 'Web Integration',
                description: 'Combine your personal memories with live web search for comprehensive answers.',
              },
              {
                icon: Zap,
                title: 'Lightning Fast',
                description: 'Vector embeddings and pgvector ensure sub-second search across millions of memories.',
              },
              {
                icon: Shield,
                title: 'Private & Secure',
                description: 'Your memories are isolated and encrypted. Only you can access your data.',
              },
              {
                icon: Layers,
                title: 'Smart Organization',
                description: 'Automatic tagging, timeline view, and personalized recommendations.',
              },
            ].map((feature) => (
              <div key={feature.title} className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 dark:bg-purple-900/30 rounded-2xl mb-4">
                  <feature.icon className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-600 dark:text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Built For Everyone</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              From students to researchers, creators to professionals
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[
              {
                title: '📚 Students',
                description: 'Store lecture notes, textbooks, and research papers. Ask questions and get instant study help.',
              },
              {
                title: '🔬 Researchers',
                description: 'Organize papers, data, and findings. Query your research corpus with natural language.',
              },
              {
                title: '✍️ Content Creators',
                description: 'Save inspiration, drafts, and resources. Never lose a great idea again.',
              },
              {
                title: '💼 Professionals',
                description: 'Keep meeting notes, documents, and presentations searchable and accessible.',
              },
            ].map((useCase) => (
              <Card key={useCase.title} className="border-gray-200 dark:border-gray-800">
                <CardContent className="pt-6">
                  <h3 className="text-2xl font-semibold mb-3">{useCase.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{useCase.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <Database className="h-16 w-16 mx-auto mb-6 text-purple-600 dark:text-purple-400" />
          <h2 className="text-4xl font-bold mb-4">Start Building Your Memory Layer</h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
            Join users who are revolutionizing how they remember and access information
          </p>
          <Button size="lg" onClick={() => router.push('/dashboard')} className="text-lg">
            Get Started Free
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center text-gray-600 dark:text-gray-400">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Brain className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            <span className="text-xl font-bold bg-linear-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              SarvAI
            </span>
          </div>
          <p>&copy; 2025 SarvAI. Your AI Memory Infrastructure.</p>
        </div>
      </footer>
    </div>
  );
}
