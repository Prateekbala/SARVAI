'use client';

import { DashboardLayout } from '@/components/dashboard-layout';
import { DashboardHome } from '@/components/pages/dashboard-home';
import { UploadPage } from '@/components/pages/upload-page';
import { SearchPage } from '@/components/pages/search-page';
import { ChatPage } from '@/components/pages/chat-page';
import { MemoriesPage } from '@/components/pages/memories-page';
import { TimelinePage } from '@/components/pages/timeline-page';
import { AnalyticsPage } from '@/components/pages/analytics-page';
import { SettingsPage } from '@/components/pages/settings-page';
import { NamespacesPage } from '@/components/pages/namespaces-page';
import { useAtom } from 'jotai';
import { currentPageAtom } from '@/lib/store';
import { useEffect, useState } from 'react';
import { useLoadNamespaces, useIsNamespaceReady } from '@/lib/jotai-hooks';
import { OnboardingPage } from '@/components/pages/onboarding-page';
import { namespacesAtom } from '@/lib/atoms';

export default function DashboardPage() {
  const [currentPage] = useAtom(currentPageAtom);
  const [namespaces] = useAtom(namespacesAtom);
  const [isLoading, setIsLoading] = useState(true);
  const [hasNamespace, setHasNamespace] = useState(false);
  const loadNamespaces = useLoadNamespaces();

  // Load namespaces on mount
  useEffect(() => {
    const load = async () => {
      try {
        // Check if user has namespace in localStorage
        const storedNamespace = localStorage.getItem('namespace');
        console.log('Stored namespace:', storedNamespace);
        
        if (storedNamespace) {
          setHasNamespace(true);
          await loadNamespaces();
        } else {
          // No namespace stored, show onboarding
          setHasNamespace(false);
        }
      } catch (error) {
        console.error('Failed to load namespaces:', error);
        setHasNamespace(false);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  // Show onboarding if no namespace in localStorage
  if (!isLoading && !hasNamespace) {
    return <OnboardingPage />;
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardHome />;
      case 'upload':
        return <UploadPage />;
      case 'search':
        return <SearchPage />;
      case 'chat':
        return <ChatPage />;
      case 'memories':
        return <MemoriesPage />;
      case 'timeline':
        return <TimelinePage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'settings':
        return <SettingsPage />;
      case 'namespaces':
        return <NamespacesPage />;
      default:
        return <DashboardHome />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl mb-4">
            <div className="w-8 h-8 border-2 border-purple-200 dark:border-purple-800 border-t-purple-600 dark:border-t-purple-400 rounded-full animate-spin" />
          </div>
          <p className="text-gray-600 dark:text-gray-400">Loading your namespace...</p>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout>
      {renderPage()}
    </DashboardLayout>
  );
}
