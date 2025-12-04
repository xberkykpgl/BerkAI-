import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, Video, Calendar, LogOut, Brain, Sparkles, Clock, MessageCircle, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Avatar, AvatarImage, AvatarFallback } from '../components/ui/avatar';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [userRes, sessionsRes] = await Promise.all([
        axios.get(`${API}/auth/me`),
        axios.get(`${API}/sessions`)
      ]);
      
      setUser(userRes.data);
      setSessions(sessionsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      if (error.response?.status === 401) {
        navigate('/');
      }
    } finally {
      setLoading(false);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await axios.post(`${API}/sessions?session_name=Yeni Seans`);
      toast.success('Yeni seans oluşturuldu!');
      navigate(`/session/${response.data.id}`);
    } catch (error) {
      console.error('Error creating session:', error);
      toast.error('Seans oluşturulamadı');
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
      toast.success('Çıkış yapıldı');
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-300">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 relative overflow-hidden">
      {/* Animated Background Stars */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="stars"></div>
        <div className="stars2"></div>
        <div className="stars3"></div>
      </div>

      {/* Header */}
      <header className="relative z-10 bg-white/5 backdrop-blur-lg border-b border-white/10 sticky top-0">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-pink-500 to-purple-500 rounded-xl">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">BerkAI</h1>
                <p className="text-xs text-gray-400">Senin için buradayım</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-white">{user?.name}</p>
                <p className="text-xs text-gray-400">Danışan ID: {user?.user_id_number}</p>
              </div>
              <Avatar className="border-2 border-pink-500">
                <AvatarImage src={user?.picture} />
                <AvatarFallback className="bg-gradient-to-br from-pink-500 to-purple-500 text-white">
                  {user?.name?.charAt(0)}
                </AvatarFallback>
              </Avatar>
              <Button 
                onClick={handleLogout}
                variant="ghost"
                size="sm"
                className="text-white hover:bg-white/10"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <div className="bg-gradient-to-r from-pink-500/10 via-purple-500/10 to-blue-500/10 backdrop-blur-lg rounded-3xl p-8 border border-white/10">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <h2 className="text-3xl font-bold text-white mb-2">
                  Merhaba, {user?.name?.split(' ')[0]} 👋
                </h2>
                <p className="text-gray-300 text-lg">
                  Bugün nasıl hissediyorsun? Seninle konuşmaya hazırım.
                </p>
              </div>
              <Button 
                onClick={createNewSession}
                size="lg"
                className="bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 hover:from-pink-600 hover:via-purple-600 hover:to-blue-600 text-white px-8 py-6 rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
              >
                <Plus className="w-5 h-5 mr-2" />
                Yeni Seans Başlat
                <Sparkles className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </div>
        </div>

        {/* Sessions */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-white flex items-center gap-2">
              <MessageCircle className="w-6 h-6 text-pink-400" />
              Seanslarım
            </h3>
            <span className="px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20 text-white text-sm">
              {sessions.length} seans
            </span>
          </div>

          {sessions.length === 0 ? (
            <div className="bg-white/5 backdrop-blur-lg rounded-3xl p-12 border border-white/10 text-center">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-pink-500/20 to-purple-500/20 flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="w-10 h-10 text-pink-300" />
              </div>
              <h4 className="text-xl font-semibold text-white mb-2">Henüz seans yok</h4>
              <p className="text-gray-400 mb-6">İlk seansını başlatmak için yukarıdaki butona tıkla</p>
              <Button 
                onClick={createNewSession}
                className="bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                İlk Seansı Başlat
              </Button>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sessions.map((session) => (
                <SessionCard 
                  key={session.id}
                  session={session}
                  onClick={() => navigate(`/session/${session.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SessionCard({ session, onClick }) {
  const hasHistory = session.started_at !== session.created_at;
  
  return (
    <div 
      onClick={onClick}
      className="group cursor-pointer transition-all duration-300 hover:-translate-y-2"
    >
      <div className="absolute -inset-1 bg-gradient-to-r from-pink-500 to-purple-500 rounded-3xl opacity-0 group-hover:opacity-30 blur-xl transition-opacity duration-300"></div>
      
      <div className="relative bg-white/5 backdrop-blur-lg rounded-3xl p-6 border border-white/10 group-hover:border-white/30 transition-all duration-300">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h4 className="text-lg font-semibold text-white mb-1 group-hover:text-pink-200 transition-colors">
              {session.session_name}
            </h4>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Calendar className="w-4 h-4" />
              <span>{new Date(session.started_at).toLocaleDateString('tr-TR')}</span>
            </div>
          </div>
          {hasHistory && (
            <div className="px-3 py-1 bg-purple-500/20 border border-purple-400/30 rounded-full">
              <span className="text-xs text-purple-300 font-medium">Geçmiş</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Clock className="w-4 h-4" />
            <span>{new Date(session.started_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
          <div className="px-3 py-1 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full text-white text-xs font-medium flex items-center gap-1">
            Devam Et
            <ArrowRight className="w-3 h-3" />
          </div>
        </div>
      </div>
    </div>
  );
}
