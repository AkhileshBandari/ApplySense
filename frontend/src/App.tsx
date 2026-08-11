import { useState, ReactNode } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Briefcase, FileText, User, Sparkles, LogOut, TrendingUp } from 'lucide-react';
import DashboardPage from './pages/DashboardPage';
import ApplicationsPage from './pages/ApplicationsPage';
import ProfilePage from './pages/ProfilePage';
import ResumesPage from './pages/ResumesPage';
import CoachPage from './pages/CoachPage';
import JobsPage from './pages/JobsPage';
import LoginPage from './pages/LoginPage';
import CareerGrowth from './pages/CareerGrowth';
import CareerEvidencePage from './pages/CareerEvidencePage';
import CareerBrandPage from './pages/CareerBrandPage';
import InterviewPrepPage from './pages/InterviewPrepPage';
import CareerOutcomesPage from './pages/CareerOutcomesPage';
import CareerOperatingSystemPage from './pages/CareerOperatingSystemPage';
import { CareerDecisionPage } from './pages/CareerDecisionPage';
import { CareerExecutionPage } from './pages/CareerExecutionPage';
import OpsDashboardPage from './pages/OpsDashboardPage';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuth } from './contexts/AuthContext';

// Define a type for our navigation tabs
type Tab = {
  id: string;
  name: string;
  icon: React.ElementType;
  component: ReactNode;
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { isAuthenticated, loading, logout } = useAuth();
  const navigate = useNavigate();

  const tabs: Tab[] = [
    {
      id: 'dashboard',
      name: 'Dashboard',
      icon: LayoutDashboard,
      component: <DashboardPage />
    },
    {
      id: 'jobs',
      name: 'Smart Job Feed',
      icon: Briefcase,
      component: <JobsPage />
    },
    {
      id: 'applications',
      name: 'Applications',
      icon: Briefcase,
      component: <ApplicationsPage />
    },
    {
      id: 'profile',
      name: 'Profile',
      icon: User,
      component: <ProfilePage />
    },
    {
      id: 'resumes',
      name: 'Resumes',
      icon: FileText,
      component: <ResumesPage />
    },
    {
      id: 'career-growth',
      name: 'Career Growth',
      icon: TrendingUp,
      component: <CareerGrowth />
    },
    {
      id: 'evidence',
      name: 'Evidence & Intelligence',
      icon: Sparkles,
      component: <CareerEvidencePage />
    },
    {
      id: 'coach',
      name: 'AI Career Coach',
      icon: Sparkles,
      component: <CoachPage />
    },
    {
      id: 'career-brand',
      name: 'Career Brand',
      icon: Sparkles,
      component: <CareerBrandPage />
    },
    {
      id: 'interview-prep',
      name: 'Interview Intelligence',
      icon: Sparkles,
      component: <InterviewPrepPage />
    },
    {
      id: 'career-decisions',
      name: 'Action Planner',
      icon: Sparkles,
      component: <CareerDecisionPage />
    },
    {
      id: 'career-execution',
      name: 'Execution Plan',
      icon: TrendingUp,
      component: <CareerExecutionPage />
    },
    {
      id: 'os-dashboard',
      name: 'OS Dashboard',
      icon: LayoutDashboard,
      component: <CareerOperatingSystemPage />
    },
    {
      id: 'ops',
      name: 'Ops Dashboard',
      icon: LayoutDashboard,
      component: <OpsDashboardPage />
    },
    {
      id: 'career-outcomes',
      name: 'Career Outcomes',
      icon: TrendingUp,
      component: <CareerOutcomesPage />
    },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (loading) {
    return <div className="flex h-screen items-center justify-center text-primaryText bg-darkBg">Loading...</div>;
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

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
                onClick={() => {
                  setActiveTab(item.id);
                  navigate(item.id === 'dashboard' ? '/' : `/${item.id}`);
                }}
              >
                <item.icon className="mr-2" />
                {item.name}
              </button>
            ))}
          </nav>
        </div>
        <div className="space-y-2">
          <button onClick={handleLogout} className="flex w-full items-center justify-center gap-2 p-2 rounded bg-red-600/80 text-white">
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>
      {/* Main Content */}
      <main className="flex-1 p-6 overflow-auto">
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/resumes" element={<ResumesPage />} />
            <Route path="/career-growth" element={<CareerGrowth />} />
            <Route path="/evidence" element={<CareerEvidencePage />} />
            <Route path="/career-brand" element={<CareerBrandPage />} />
            <Route path="/interview-prep" element={<InterviewPrepPage />} />
            <Route path="/coach" element={<CoachPage />} />
            <Route path="/career-decisions" element={<CareerDecisionPage />} />
            <Route path="/career-execution" element={<CareerExecutionPage />} />
            <Route path="/os-dashboard" element={<CareerOperatingSystemPage />} />
            <Route path="/ops" element={<OpsDashboardPage />} />
            <Route path="/career-outcomes" element={<CareerOutcomesPage />} />
          </Route>
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}