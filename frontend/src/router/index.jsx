import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Layouts
import MainLayout from '../components/layout/MainLayout';

// Pages
import LandingPage from '../pages/LandingPage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';

// Protected Route Wrapper
const ProtectedRoute = () => {
  const { user, loading } = useAuth();
  
  if (loading) return <div className="flex h-screen w-screen items-center justify-center">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  
  return <Outlet />;
};

// Auth Route Wrapper (redirects if already logged in)
const AuthRoute = () => {
  const { user, loading } = useAuth();
  
  if (loading) return <div className="flex h-screen w-screen items-center justify-center">Loading...</div>;
  if (user) return <Navigate to="/dashboard" replace />;
  
  return <Outlet />;
};

export const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    element: <AuthRoute />,
    children: [
      {
        path: '/login',
        element: <LoginPage />,
      },
      {
        path: '/register',
        element: <RegisterPage />,
      },
    ]
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <MainLayout />,
        children: [
          {
            path: '/dashboard',
            lazy: async () => ({
              Component: (await import('../pages/DashboardPage')).default,
            }),
          },
          {
            path: '/schemes',
            lazy: async () => ({
              Component: (await import('../pages/SchemesPage')).default,
            }),
          },
          {
            path: '/eligibility',
            lazy: async () => ({
              Component: (await import('../pages/EligibilityPage')).default,
            }),
          },
          {
            path: '/documents',
            lazy: async () => ({
              Component: (await import('../pages/DocumentsPage')).default,
            }),
          },
          {
            path: '/checklists',
            lazy: async () => ({
              Component: (await import('../pages/ChecklistsPage')).default,
            }),
          },
          {
            path: '/assistant',
            lazy: async () => ({
              Component: (await import('../pages/AssistantPage')).default,
            }),
          },
          {
            path: '/analytics',
            lazy: async () => ({
              Component: (await import('../pages/AnalyticsPage')).default,
            }),
          },
        ]
      }
    ]
  },
  {
    path: '*',
    element: <Navigate to="/" replace />
  }
]);
