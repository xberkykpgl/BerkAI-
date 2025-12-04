import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import LandingPage from './pages/LandingPage';
import UserTypeSelection from './pages/UserTypeSelection';
import Dashboard from './pages/Dashboard';
import DoctorDashboard from './pages/DoctorDashboard';
import PatientDetailPage from './pages/PatientDetailPage';
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
    // Skip auth check for admin routes and landing page
    if (location.pathname.startsWith('/admin') || location.pathname === '/') {
      setIsChecking(false);
      return;
    }

    const checkAuth = async () => {
      // Check for session_id in URL fragment
      const hash = window.location.hash;
      if (hash.includes('session_id=')) {
        const sessionId = hash.split('session_id=')[1].split('&')[0];
        const pendingUserType = sessionStorage.getItem('pending_user_type') || 'patient';
        
        try {
          // Exchange session_id for session_token
          const response = await axios.post(`${API}/auth/session`, {
            session_id: sessionId,
            user_type: pendingUserType
          });
          
          if (response.data.success) {
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
            sessionStorage.removeItem('pending_user_type');
            
            // Check for pending approval or rejection
            if (response.data.pending_approval) {
              alert(response.data.message);
              navigate('/');
              return;
            }
            
            if (response.data.rejected) {
              alert(response.data.message);
              navigate('/');
              return;
            }
            
            // Redirect based on user type
            if (response.data.user_type === 'doctor' || response.data.user_type === 'psychiatrist') {
              navigate('/doctor/dashboard');
            } else {
              navigate('/dashboard');
            }
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
        
        if (location.pathname === '/user-type-selection') {
          // Redirect based on user type
          if (response.data.user_type === 'doctor' || response.data.user_type === 'psychiatrist') {
            navigate('/doctor/dashboard');
          } else {
            navigate('/dashboard');
          }
        }
      } catch (error) {
        setUser(null);
        if (location.pathname !== '/' && location.pathname !== '/user-type-selection') {
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
          <Route path="/" element={<LandingPage />} />
          <Route path="/user-type-selection" element={<UserTypeSelection />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/doctor/dashboard" element={<DoctorDashboard />} />
          <Route path="/doctor/patient/:patientId" element={<PatientDetailPage />} />
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