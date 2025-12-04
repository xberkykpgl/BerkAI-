import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, Video, Calendar, LogOut, Brain } from 'lucide-react';
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-teal-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-teal-500 to-blue-600 rounded-xl">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent">
                BerkAI
              </h1>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback>{user?.name?.charAt(0)}</AvatarFallback>
                </Avatar>
                <div className="hidden sm:block">
                  <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                  <p className="text-xs text-gray-500">ID: {user?.user_id_number || 'Yükleniyor...'}</p>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="icon"
                onClick={handleLogout}
                data-testid="logout-button"
                className="text-gray-600 hover:text-gray-900"
              >
                <LogOut className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Hoş Geldiniz, {user?.name?.split(' ')[0]}</h2>
          <p className="text-gray-600">Psikolojik destek seanslarınızı buradan yönetebilirsiniz</p>
        </div>

        {/* Patient ID Card */}
        <Card className="p-6 mb-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-sm text-purple-100 mb-1">Danışan ID Numaranız</p>
              <div className="flex items-center gap-3">
                <p className="text-3xl font-bold font-mono">{user?.user_id_number || 'Yükleniyor...'}</p>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    navigator.clipboard.writeText(user?.user_id_number || '');
                    toast.success('ID kopyalandı!');
                  }}
                  className="bg-white/20 hover:bg-white/30 text-white"
                >
                  Kopyala
                </Button>
              </div>
              <p className="text-sm text-purple-100 mt-2">
                👨‍⚕️ Bu ID'yi doktorunuzla paylaşın
              </p>
            </div>
          </div>
        </Card>

        {/* New Session Button */}
        <Card className="p-8 mb-8 bg-gradient-to-br from-teal-500 to-blue-600 text-white border-0 shadow-xl hover:shadow-2xl transition-shadow">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-2xl font-bold mb-2">Yeni Seans Başlat</h3>
              <p className="text-teal-100">
                {sessions.length > 0 
                  ? "BerkAI sizi tanıyor - önceki seanslarınızı hatırlayacak 💚" 
                  : "BerkAI ile görüntülü terapi seanslarınıza başlayın"}
              </p>
            </div>
            <Button 
              size="lg"
              onClick={createNewSession}
              data-testid="new-session-button"
              className="bg-white text-teal-600 hover:bg-gray-50 shadow-lg rounded-full px-8"
            >
              <Plus className="w-5 h-5 mr-2" />
              Yeni Seans
            </Button>
          </div>
        </Card>

        {/* Sessions List */}
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Seanslarım
          </h3>
          
          {sessions.length === 0 ? (
            <Card className="p-12 text-center bg-white/80 backdrop-blur-sm">
              <Video className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">Henüz hiç seans oluşturmadınız</p>
              <Button 
                onClick={createNewSession}
                className="bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                İlk Seansınızı Oluşturun
              </Button>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sessions.map(session => (
                <SessionCard 
                  key={session.id}
                  session={session}
                  onClick={() => navigate(`/session/${session.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function SessionCard({ session, onClick }) {
  const date = new Date(session.started_at);
  const isActive = session.status === 'active';

  return (
    <Card 
      className="p-6 cursor-pointer hover:shadow-xl transition-all duration-300 hover:-translate-y-1 bg-white/80 backdrop-blur-sm border-l-4 border-l-teal-500"
      onClick={onClick}
      data-testid={`session-card-${session.id}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
            isActive 
              ? 'bg-gradient-to-br from-teal-500 to-emerald-500' 
              : 'bg-gray-200'
          }`}>
            <Video className={`w-6 h-6 ${isActive ? 'text-white' : 'text-gray-500'}`} />
          </div>
          <div>
            <h4 className="font-semibold text-gray-900">{session.session_name}</h4>
            <p className="text-xs text-gray-500">{date.toLocaleDateString('tr-TR')}</p>
          </div>
        </div>
        {isActive && (
          <span className="px-3 py-1 bg-teal-100 text-teal-700 text-xs font-medium rounded-full">
            Aktif
          </span>
        )}
      </div>
      
      <p className="text-sm text-gray-600">
        {date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
      </p>
    </Card>
  );
}