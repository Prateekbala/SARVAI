'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { namespaceAPI } from '@/lib/api';
import { Brain, Sparkles, Zap, Shield } from 'lucide-react';

export function OnboardingPage() {
  const router = useRouter();
  const [namespace, setNamespace] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const validateForm = (): boolean => {
    setError('');

    // Convert namespace to lowercase for validation
    const namespaceLower = namespace.toLowerCase().trim();

    if (!namespaceLower) {
      setError('Namespace is required');
      return false;
    }

    if (namespaceLower.length < 3) {
      setError('Namespace must be at least 3 characters');
      return false;
    }

    if (!/^[a-z0-9-_]+$/.test(namespaceLower)) {
      setError('Namespace can only contain lowercase letters, numbers, hyphens, and underscores');
      return false;
    }

    return true;
  };

  const handleCreateNamespace = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      // Step 1: Create the namespace (register)
      const newNamespace = await namespaceAPI.create({
        namespace: namespace.toLowerCase().trim(),
      });

      // Step 2: Login to get token
      const loginResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/login`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            namespace: newNamespace.namespace,
          }),
        }
      );

      if (!loginResponse.ok) {
        throw new Error('Failed to login after registration');
      }

      const tokenData = await loginResponse.json();

      // Step 3: Save to localStorage (ensure no quotes)
      const namespaceName = newNamespace.namespace.trim();
      localStorage.setItem('namespace', namespaceName);
      localStorage.setItem('token', tokenData.access_token);

      // Verify it was saved correctly
      const savedNamespace = localStorage.getItem('namespace');
      console.log('Saved namespace:', savedNamespace);
      console.log('Token:', tokenData.access_token);

      toast.success('Namespace created successfully!');

      // Redirect to dashboard immediately
      router.push('/dashboard');
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to create namespace';
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-950 to-red-950 relative overflow-hidden">
      {/* Enhanced Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-red-600 to-red-700 rounded-full blur-3xl opacity-20 animate-float" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-br from-orange-600 to-red-700 rounded-full blur-3xl opacity-20 animate-float" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-gradient-to-br from-red-500 to-orange-600 rounded-full blur-3xl opacity-10 animate-pulse" />
      </div>

      <div className="relative flex flex-col items-center justify-center min-h-screen px-4 py-8 animate-fade-in-up">
        {/* Logo and Title */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-br from-red-600 to-red-700 rounded-2xl shadow-xl animate-pulse-glow border border-red-500">
              <Brain className="h-12 w-12 text-white" />
            </div>
            <span className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-500">
              SarvAI
            </span>
          </div>
          <h1 className="text-5xl font-bold mb-3 tracking-tight">Welcome to SarvAI</h1>
          <p className="text-xl text-muted-foreground">
            Your personal AI memory infrastructure
          </p>
        </div>

        {/* Main Card */}
        <div className="w-full max-w-md">
          <Card className="border border-red-900/30 shadow-2xl hover-lift backdrop-blur-sm bg-gradient-to-br from-black to-gray-900">
            <CardHeader className="space-y-2">
              <CardTitle className="text-2xl">Create Your First Namespace</CardTitle>
              <CardDescription className="text-base">
                A namespace is your personal workspace. Think of it as your account.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateNamespace} className="space-y-6">
                {error && (
                  <div className="p-4 bg-gradient-to-r from-red-950/80 to-orange-950/80 border-2 border-red-600 rounded-xl animate-fade-in-up">
                    <p className="text-sm font-medium text-red-400">{error}</p>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="namespace" className="text-base font-semibold">Namespace *</Label>
                  <Input
                    id="namespace"
                    type="text"
                    placeholder="e.g., my-workspace"
                    value={namespace}
                    onChange={(e) => setNamespace(e.target.value.toLowerCase())}
                    disabled={isLoading}
                    className="lowercase h-12 text-base border-2 focus:border-red-500 transition-all bg-gray-900/50"
                  />
                  <p className="text-sm text-muted-foreground">
                    Only lowercase letters, numbers, hyphens, and underscores
                  </p>
                </div>

                <Button
                  type="submit"
                  className="w-full h-12 text-base bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-lg hover:shadow-xl transition-all hover:scale-105 border border-red-500"
                  size="lg"
                  disabled={isLoading}
                >
                  {isLoading ? 'Creating Namespace...' : 'Create My Namespace'}
                </Button>
              </form>

              <p className="text-sm text-muted-foreground text-center mt-6">
                You can create additional namespaces later from your dashboard
              </p>
            </CardContent>
          </Card>

          {/* Features */}
          <div className="grid grid-cols-3 gap-6 mt-12">
            {[
              { icon: Sparkles, label: 'Multi-Modal', color: 'from-red-600 to-red-700' },
              { icon: Zap, label: 'Fast Search', color: 'from-orange-600 to-red-700' },
              { icon: Shield, label: 'Private', color: 'from-yellow-600 to-orange-700' },
            ].map((feature, index) => (
              <div key={feature.label} className="text-center animate-fade-in-up" style={{ animationDelay: `${index * 100}ms` }}>
                <div className={`inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br ${feature.color} rounded-xl mb-3 shadow-lg hover:scale-110 transition-transform duration-300 border border-red-800/30`}>
                  <feature.icon className="h-7 w-7 text-white" />
                </div>
                <p className="text-sm font-semibold text-foreground">
                  {feature.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
