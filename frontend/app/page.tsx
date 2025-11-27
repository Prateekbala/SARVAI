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
  Layers,
  CircuitBoard,
  Cpu
} from 'lucide-react';

export default function Home() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(120,119,198,0.1),transparent_50%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1a1a1a_1px,transparent_1px),linear-gradient(to_bottom,#1a1a1a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)] pointer-events-none" />
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-black/40 backdrop-blur-xl border-b border-white/10 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute inset-0 bg-purple-500/20 blur-xl rounded-full" />
                <CircuitBoard className="h-10 w-10 text-purple-400 relative" />
              </div>
              <span className="text-3xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
                SarvAI
              </span>
            </div>
            <div className="flex items-center gap-4">
              <Button 
                onClick={() => router.push('/dashboard')} 
                className="bg-white/5 hover:bg-white/10 border border-white/20 text-white backdrop-blur-xl"
              >
                Launch App
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-40 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 relative">
            {/* Floating elements */}
            <div className="absolute top-0 left-1/4 w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
            <div className="absolute top-20 right-1/4 w-1 h-1 bg-cyan-400 rounded-full animate-pulse delay-75" />
            <div className="absolute bottom-10 left-1/3 w-1.5 h-1.5 bg-pink-400 rounded-full animate-pulse delay-150" />
            
            <div className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full mb-8">
              <Cpu className="h-4 w-4 text-purple-400 animate-pulse" />
              <span className="text-sm font-medium text-gray-300">
                Neural Memory Infrastructure
              </span>
            </div>
            
            <h1 className="text-6xl sm:text-7xl lg:text-8xl font-bold mb-8 leading-tight">
              <span className="text-white">Remember</span>
              <br />
              <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent animate-gradient">
                Everything
              </span>
            </h1>
            
            <p className="text-xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
              A multi-modal memory system that captures and recalls text, images, PDFs, and audio.
              <br className="hidden sm:block" />
              Search by meaning, not keywords. Your knowledge, infinitely accessible.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button 
                size="lg" 
                onClick={() => router.push('/dashboard')} 
                className="text-lg px-8 py-6 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 border-0 shadow-[0_0_30px_rgba(168,85,247,0.4)]"
              >
                Enter Dashboard
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>
          </div>

          {/* Hero Visual */}
          <div className="relative mt-20">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 via-pink-500/20 to-cyan-500/20 blur-3xl" />
            <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { icon: FileText, label: 'Text', color: 'from-blue-400 to-cyan-400' },
                  { icon: Image, label: 'Images', color: 'from-purple-400 to-pink-400' },
                  { icon: FileText, label: 'PDFs', color: 'from-green-400 to-emerald-400' },
                  { icon: Mic, label: 'Audio', color: 'from-orange-400 to-red-400' },
                ].map((item) => (
                  <div key={item.label} className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all group">
                    <div className={`w-12 h-12 bg-gradient-to-br ${item.color} rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                      <item.icon className="h-6 w-6 text-white" />
                    </div>
                    <p className="text-gray-300 font-medium">{item.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="relative py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-5xl font-bold mb-6 text-white">Multi-Modal Memory</h2>
            <p className="text-xl text-gray-400">
              Upload any format, search everything, remember forever
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: FileText,
                title: 'Text',
                description: 'Notes, documents, and articles',
                gradient: 'from-blue-500/20 to-cyan-500/20',
                iconColor: 'text-cyan-400',
              },
              {
                icon: Image,
                title: 'Images',
                description: 'Photos with OCR extraction',
                gradient: 'from-purple-500/20 to-pink-500/20',
                iconColor: 'text-pink-400',
              },
              {
                icon: FileText,
                title: 'PDFs',
                description: 'Documents with smart chunking',
                gradient: 'from-green-500/20 to-emerald-500/20',
                iconColor: 'text-emerald-400',
              },
              {
                icon: Mic,
                title: 'Audio',
                description: 'Voice notes with transcription',
                gradient: 'from-orange-500/20 to-red-500/20',
                iconColor: 'text-orange-400',
              },
            ].map((feature) => (
              <div key={feature.title} className="group relative">
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity`} />
                <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-all">
                  <feature.icon className={`h-14 w-14 ${feature.iconColor} mb-4`} />
                  <h3 className="text-2xl font-semibold mb-3 text-white">{feature.title}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="relative py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Search,
                title: 'Semantic Search',
                description: 'Find memories by meaning, not just keywords. Vector search understands context.',
              },
              {
                icon: MessageSquare,
                title: 'Chat Interface',
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
                description: 'Vector embeddings ensure sub-second search across millions of memories.',
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
              <div key={feature.title} className="group relative">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-all text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-2xl mb-6 group-hover:scale-110 transition-transform">
                    <feature.icon className="h-8 w-8 text-purple-400" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3 text-white">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="relative py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-5xl font-bold mb-6 text-white">Built For Everyone</h2>
            <p className="text-xl text-gray-400">
              From students to researchers, creators to professionals
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                emoji: '📚',
                title: 'Students',
                description: 'Store lecture notes, textbooks, and research papers. Ask questions and get instant study help.',
              },
              {
                emoji: '🔬',
                title: 'Researchers',
                description: 'Organize papers, data, and findings. Query your research corpus with natural language.',
              },
              {
                emoji: '✍️',
                title: 'Content Creators',
                description: 'Save inspiration, drafts, and resources. Never lose a great idea again.',
              },
              {
                emoji: '💼',
                title: 'Professionals',
                description: 'Keep meeting notes, documents, and presentations searchable and accessible.',
              },
            ].map((useCase) => (
              <div key={useCase.title} className="group relative">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-cyan-500/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-all">
                  <div className="text-4xl mb-4">{useCase.emoji}</div>
                  <h3 className="text-2xl font-semibold mb-4 text-white">{useCase.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{useCase.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="relative inline-block mb-8">
            <div className="absolute inset-0 bg-purple-500/30 blur-3xl" />
            <Database className="h-20 w-20 mx-auto text-purple-400 relative" />
          </div>
          <h2 className="text-5xl font-bold mb-6 text-white">Start Building Your Memory Layer</h2>
          <p className="text-xl text-gray-400 mb-10 leading-relaxed">
            Join users who are revolutionizing how they remember and access information
          </p>
          <Button 
            size="lg" 
            onClick={() => router.push('/dashboard')} 
            className="text-lg px-10 py-7 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 border-0 shadow-[0_0_30px_rgba(168,85,247,0.4)]"
          >
            Get Started Free
            <ArrowRight className="ml-2 h-6 w-6" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-white/10 py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-purple-500/20 blur-xl rounded-full" />
              <CircuitBoard className="h-8 w-8 text-purple-400 relative" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
              SarvAI
            </span>
          </div>
          <p className="text-gray-500">&copy; 2025 SarvAI. Your Neural Memory Infrastructure.</p>
        </div>
      </footer>
    </div>
  );
}
