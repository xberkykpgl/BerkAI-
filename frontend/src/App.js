import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import LandingPage from './pages/LandingPage';
import UserTypeSelection from './pages/UserTypeSelection';
import Dashboard from './pages/Dashboard';
import DoctorDashboard from './pages/DoctorDashboard';
import SessionPage from './pages/SessionPage';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import { Toaster } from './components/ui/sonner';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

axios.defaults.withCredentials = true;

function AuthHandler() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isChecking, setIsChecking] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const checkAuth = async () => {
      // Check for session_id in URL fragment
      const hash = window.location.hash;
      if (hash.includes('session_id=')) {
        const sessionId = hash.split('session_id=')[1].split('&')[0];
        
        try {
          // Exchange session_id for session_token
          const response = await axios.post(`${API}/auth/session`, {
            session_id: sessionId
          });
          
          if (response.data.success) {
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
            
            // Redirect to dashboard
            navigate('/dashboard');
            return;
          }
        } catch (error) {
          console.error('Auth error:', error);
        }
      }

      // Check existing session
      try {
        const response = await axios.get(`${API}/auth/me`);
        setUser(response.data);
        
        if (location.pathname === '/') {
          navigate('/dashboard');
        }
      } catch (error) {
        setUser(null);
        if (location.pathname !== '/') {
          navigate('/');
        }
      } finally {
        setIsChecking(false);
      }
    };

    checkAuth();
  }, [navigate, location]);

  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-teal-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return null;
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthHandler />
        <Routes>
          <Route path="/" element={<UserTypeSelection />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/doctor/dashboard" element={<DoctorDashboard />} />
          <Route path="/session/:sessionId" element={<SessionPage />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
        </Routes>
        <Toaster position="top-right" />
      </BrowserRouter>
    </div>
  );
}

export default App;