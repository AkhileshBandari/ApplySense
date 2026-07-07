import { useState, useEffect, ReactNode } from 'react';
import { LayoutDashboard, Briefcase, FileText, User, Sparkles } from 'lucide-react';
import DashboardPage from './pages/DashboardPage';
import ApplicationsPage from './pages/ApplicationsPage';
import ProfilePage from './pages/ProfilePage';
import ResumesPage from './pages/ResumesPage';
import CoachPage from './pages/CoachPage';

// Define a type for our navigation tabs
type Tab = {
  id: string;
  name: string;
  icon: React.ElementType;
  component: ReactNode;
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [apiMode, setApiMode] = useState<'mock' | 'live'>(
    () => (localStorage.getItem('applysense_api_mode') as 'mock' | 'live') || 'mock'
  );

  useEffect(() => {
    localStorage.setItem('applysense_api_mode', apiMode);
  }, [apiMode]);

  const tabs: Tab[] = [
    {
      id: 'dashboard',
      name: 'Dashboard',
      icon: LayoutDashboard,
      component: <DashboardPage apiMode={apiMode} />
    },
    {
      id: 'applications',
      name: 'Applications',
      icon: Briefcase,
      component: <ApplicationsPage apiMode={apiMode} />
    },
    {
      id: 'profile',
      name: 'Profile',
      icon: User,
      component: <ProfilePage apiMode={apiMode} />
    },
    {
      id: 'resumes',
      name: 'Resumes',
      icon: FileText,
      component: <ResumesPage apiMode={apiMode} />
    },
    {
      id: 'coach',
      name: 'AI Career Coach',
      icon: Sparkles,
      component: <CoachPage apiMode={apiMode} />
    },
  ];

  const CurrentPage = tabs.find(t => t.id === activeTab)?.component;

  return (
    <div className="flex h-screen bg-darkBg text-primaryText overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 glass-panel border-r border-cardBorder flex flex-col justify-between p-4 z-10">
        <div>
          {/* Brand Logo */}
          <div className="flex items-center gap-2 mb-8 px-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-cyan-purple flex items-center justify-center text-darkBg font-bold text-lg">A</div>
            <div>
              <span className="font-extrabold text-xl tracking-tight text-white Outfit">ApplySense</span>
              <span className="text-accentTeal font-bold ml-0.5">.AI</span>
            </div>
          </div>
          {/* Navigation Links */}
          <nav className="space-y-1">
            {tabs.map(item => (
              <button
                key={item.id}
                className={`flex items-center w-full p-2 rounded-md hover:bg-cardHover ${activeTab === item.id ? 'bg-cardActive' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <item.icon className="mr-2" />
                {item.name}
              </button>
            ))}
          </nav>
        </div>
        {/* Settings / Mode Switch */}
        <button
          onClick={() => setApiMode(prev => (prev === 'mock' ? 'live' : 'mock'))}
          className="p-2 mt-4 bg-cardHover rounded"
        >
          Switch to {apiMode === 'mock' ? 'Live' : 'Mock'} Mode
        </button>
      </aside>
      {/* Main Content */}
      <main className="flex-1 p-6 overflow-auto">
        {CurrentPage}
      </main>
    </div>
  );
}