import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { BarChart3, Users, MessageSquare, Video, Activity, LogOut, Settings, Shield } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import AdminUsers from '../components/admin/AdminUsers';
import AdminSessions from '../components/admin/AdminSessions';
import AdminSettings from '../components/admin/AdminSettings';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    verifyAdmin();
    loadStats();
  }, []);

  const verifyAdmin = async () => {
    try {
      await axios.get(`${API}/admin/verify`);
    } catch (error) {
      toast.error('Yetkiniz yok');
      navigate('/admin/login');
    }
  };

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/admin/logout`);
      toast.success('Çıkış yapıldı');
      navigate('/admin/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-lg border-b border-white/10 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">BerkAI Admin</h1>
                <p className="text-xs text-gray-400">Yönetim Paneli</p>
              </div>
            </div>

            <Button
              variant="ghost"
              onClick={handleLogout}
              data-testid="admin-logout-button"
              className="text-white hover:bg-white/10"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Çıkış
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Users className="w-6 h-6" />}
            title="Toplam Kullanıcı"
            value={stats?.totals?.users || 0}
            gradient="from-blue-500 to-cyan-500"
          />
          <StatCard
            icon={<Video className="w-6 h-6" />}
            title="Toplam Seans"
            value={stats?.totals?.sessions || 0}
            gradient="from-purple-500 to-pink-500"
          />
          <StatCard
            icon={<MessageSquare className="w-6 h-6" />}
            title="Toplam Mesaj"
            value={stats?.totals?.messages || 0}
            gradient="from-green-500 to-emerald-500"
          />
          <StatCard
            icon={<Activity className="w-6 h-6" />}
            title="Aktif Seans"
            value={stats?.totals?.active_sessions || 0}
            gradient="from-orange-500 to-red-500"
          />
        </div>

        {/* Analytics */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card className="p-6 bg-white/10 backdrop-blur-lg border-white/20">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Ortalama Stres Seviyesi
            </h3>
            <div className="text-4xl font-bold text-white">
              {stats?.analytics?.average_stress || 0}/10
            </div>
          </Card>

          <Card className="p-6 bg-white/10 backdrop-blur-lg border-white/20">
            <h3 className="text-lg font-semibold text-white mb-4">Duygu Dağılımı</h3>
            <div className="space-y-2">
              {stats?.analytics?.emotion_distribution && Object.entries(stats.analytics.emotion_distribution).map(([emotion, count]) => (
                <div key={emotion} className="flex justify-between items-center text-white">
                  <span className="capitalize">{emotion}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="users" className="space-y-6">
          <TabsList className="bg-white/10 border-white/20">
            <TabsTrigger value="users" className="data-[state=active]:bg-purple-600 text-white">
              <Users className="w-4 h-4 mr-2" />
              Kullanıcılar
            </TabsTrigger>
            <TabsTrigger value="sessions" className="data-[state=active]:bg-purple-600 text-white">
              <Video className="w-4 h-4 mr-2" />
              Seanslar
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-purple-600 text-white">
              <Settings className="w-4 h-4 mr-2" />
              Ayarlar
            </TabsTrigger>
          </TabsList>

          <TabsContent value="users">
            <AdminUsers />
          </TabsContent>

          <TabsContent value="sessions">
            <AdminSessions />
          </TabsContent>

          <TabsContent value="settings">
            <AdminSettings onUpdate={loadStats} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

function StatCard({ icon, title, value, gradient }) {
  return (
    <Card className="p-6 bg-white/10 backdrop-blur-lg border-white/20 hover:bg-white/15 transition-all">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-300 text-sm mb-1">{title}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
        </div>
        <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
}