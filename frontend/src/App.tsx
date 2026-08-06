import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DesktopLayout } from './components/layout/DesktopLayout';
import { SplashScreen } from './components/specialized/SplashScreen';
import { Dashboard } from './pages/Dashboard';
import { Recognition } from './pages/Recognition';
import { Enrollment } from './pages/Enrollment';
import { Database } from './pages/Database';
import { System } from './pages/System';
import { History } from './pages/History';
import { Logs } from './pages/Logs';
import { Settings } from './pages/Settings';
import { About } from './pages/About';
import { Cameras } from './pages/Cameras';
import { Login } from './pages/Login';
import { AuthProvider, useAuth } from './context/AuthContext';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  const [isReady, React_useState] = React.useState(false);
  const queryClient = new QueryClient();

  return (
    <>
      {!isReady && <SplashScreen onComplete={() => React_useState(true)} />}

      {isReady && (
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={<ProtectedRoute><DesktopLayout /></ProtectedRoute>}>
                  <Route index element={<Dashboard />} />
                  <Route path="recognition" element={<Recognition />} />
                  <Route path="enrollment" element={<Enrollment />} />
                  <Route path="history" element={<History />} />
                  <Route path="database" element={<Database />} />
                  <Route path="cameras" element={<Cameras />} />
                  <Route path="system" element={<System />} />
                  <Route path="settings" element={<Settings />} />
                  <Route path="logs" element={<Logs />} />
                  <Route path="about" element={<About />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </QueryClientProvider>
      )}
    </>
  );
}

export default App;
