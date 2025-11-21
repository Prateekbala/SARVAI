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
import { useAtom } from 'jotai';
import { currentPageAtom } from '@/lib/store';

export default function DashboardPage() {
  const [currentPage] = useAtom(currentPageAtom);

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
      default:
        return <DashboardHome />;
    }
  };

  return (
    <DashboardLayout>
      {renderPage()}
    </DashboardLayout>
  );
}
