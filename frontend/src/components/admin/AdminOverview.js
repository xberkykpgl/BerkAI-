import { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, MessageSquare, Activity, TrendingUp, Database } from 'lucide-react';
import { Card } from '../ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminOverview() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/stats`, {
        withCredentials: true
      });
      setStats(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading stats:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  if (!stats) {
    return <div className="text-center py-12">İstatistikler yüklenemedi</div>;
  }

  const statCards = [
    {
      title: 'Toplam Kullanıcı',
      value: stats.totals.users,
      icon: Users,
      color: 'from-blue-500 to-blue-600'
    },
    {
      title: 'Toplam Seans',
      value: stats.totals.sessions,
      icon: Activity,
      color: 'from-teal-500 to-teal-600'
    },
    {
      title: 'Toplam Mesaj',
      value: stats.totals.messages,
      icon: MessageSquare,
      color: 'from-purple-500 to-purple-600'
    },
    {
      title: 'Aktif Seanslar',
      value: stats.totals.active_sessions,
      icon: TrendingUp,
      color: 'from-green-500 to-green-600'
    },
    {
      title: 'Video Analizi',
      value: stats.totals.video_analyses,
      icon: Database,
      color: 'from-orange-500 to-orange-600'
    }
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Platform Özeti</h2>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {statCards.map((stat, idx) => (
          <Card key={idx} className="p-6 bg-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">{stat.title}</p>
                <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 bg-white">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Ortalama Stres Seviyesi</h3>
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="text-5xl font-bold text-teal-600 mb-2">
                {stats.analytics.average_stress}
              </div>
              <div className="text-sm text-gray-500">/ 10</div>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-white">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Duygu Dağılımı</h3>
          <div className="space-y-2">
            {Object.entries(stats.analytics.emotion_distribution).slice(0, 5).map(([emotion, count]) => (
              <div key={emotion} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 capitalize">{emotion}</span>
                <span className="text-sm font-semibold text-gray-900">{count}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 bg-white">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Son Seanslar</h3>
          <div className="space-y-3">
            {stats.recent_activity.sessions.slice(0, 5).map((session) => (
              <div key={session.id} className="flex items-center justify-between border-b border-gray-100 pb-2">
                <div>
                  <p className="text-sm text-gray-600">User: {session.user_id.slice(0, 8)}...</p>
                  <p className="text-xs text-gray-400">{new Date(session.started_at).toLocaleString('tr-TR')}</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs ${
                  session.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                }`}>
                  {session.status}
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6 bg-white">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Yeni Kullanıcılar</h3>
          <div className="space-y-3">
            {stats.recent_activity.users.slice(0, 5).map((user, idx) => (
              <div key={idx} className="flex items-center justify-between border-b border-gray-100 pb-2">
                <div>
                  <p className="text-sm font-medium text-gray-900">{user.name}</p>
                  <p className="text-xs text-gray-400">{user.email}</p>
                </div>
                <p className="text-xs text-gray-500">{new Date(user.created_at).toLocaleDateString('tr-TR')}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
