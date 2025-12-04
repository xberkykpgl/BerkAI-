import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { LogOut, LayoutDashboard, Users, MessageSquare, Activity, Database, Brain } from 'lucide-react';
import { Button } from '../components/ui/button';
import AdminOverview from '../components/admin/AdminOverview';
import AdminAllUsers from '../components/admin/AdminAllUsers';
import AdminUserDetail from '../components/admin/AdminUserDetail';
import AdminAllSessions from '../components/admin/AdminAllSessions';
import AdminAllMessages from '../components/admin/AdminAllMessages';
import AdminProfiles from '../components/admin/AdminProfiles';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [sessionMessages, setSessionMessages] = useState([]);

  useEffect(() => {
    verifyAdmin();
  }, []);

  const verifyAdmin = async () => {
    try {
      await axios.get(`${API}/admin/verify`, { withCredentials: true });
    } catch (error) {
      console.error('Not authorized:', error);
      navigate('/admin/login');
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/admin/logout`, {}, { withCredentials: true });
      toast.success('Çıkış başarılı');
      navigate('/admin/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/admin/sessions/${sessionId}/messages`, {
        withCredentials: true
      });
      setSessionMessages(response.data);
      setSelectedSessionId(sessionId);
    } catch (error) {
      console.error('Error loading session messages:', error);
      toast.error('Mesajlar yüklenemedi');
    }
  };

  const tabs = [
    { id: 'overview', label: 'Özet', icon: LayoutDashboard },
    { id: 'users', label: 'Kullanıcılar', icon: Users },
    { id: 'sessions', label: 'Seanslar', icon: Activity },
    { id: 'messages', label: 'Mesajlar', icon: MessageSquare },
    { id: 'profiles', label: 'RAG Profilleri', icon: Brain },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-teal-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-teal-600 to-blue-600 rounded-lg flex items-center justify-center">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">BerkAI Admin Panel</h1>
                <p className="text-sm text-gray-500">Kapsamlı Yönetim Sistemi</p>
              </div>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              className="flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Çıkış Yap
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <div className="w-64 flex-shrink-0">
            <div className="bg-white rounded-xl shadow-sm p-4 sticky top-24">
              <nav className="space-y-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => {
                        setActiveTab(tab.id);
                        setSelectedUserId(null);
                        setSelectedSessionId(null);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                        activeTab === tab.id
                          ? 'bg-gradient-to-r from-teal-600 to-blue-600 text-white shadow-md'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="font-medium">{tab.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            <div className="bg-white rounded-xl shadow-sm p-8">
              {activeTab === 'overview' && <AdminOverview />}
              
              {activeTab === 'users' && (
                selectedUserId ? (
                  <AdminUserDetail
                    userId={selectedUserId}
                    onBack={() => setSelectedUserId(null)}
                  />
                ) : (
                  <AdminAllUsers onSelectUser={(id) => setSelectedUserId(id)} />
                )
              )}
              
              {activeTab === 'sessions' && (
                selectedSessionId ? (
                  <div className="space-y-4">
                    <Button onClick={() => setSelectedSessionId(null)} variant="ghost">
                      ← Geri
                    </Button>
                    <h3 className="text-xl font-bold">Seans Mesajları</h3>
                    <div className="space-y-3 max-h-[600px] overflow-y-auto">
                      {sessionMessages.map((msg, idx) => (
                        <div
                          key={idx}
                          className={`p-4 rounded-lg ${
                            msg.role === 'user'
                              ? 'bg-gradient-to-r from-teal-50 to-blue-50 ml-8'
                              : 'bg-gray-50 mr-8'
                          }`}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs font-medium text-gray-600">
                              {msg.role === 'user' ? 'Kullanıcı' : 'BerkAI'}
                            </span>
                            <span className="text-xs text-gray-500">
                              {new Date(msg.timestamp).toLocaleString('tr-TR')}
                            </span>
                          </div>
                          <p className="text-sm text-gray-800 whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <AdminAllSessions onSelectSession={loadSessionMessages} />
                )
              )}
              
              {activeTab === 'messages' && <AdminAllMessages />}
              {activeTab === 'profiles' && <AdminProfiles />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
