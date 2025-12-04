import { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, User, Mail, Calendar, Hash, MessageSquare, Activity, Brain } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminUserDetail({ userId, onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('info');

  useEffect(() => {
    loadUserDetail();
  }, [userId]);

  const loadUserDetail = async () => {
    try {
      const response = await axios.get(`${API}/admin/users/${userId}`, {
        withCredentials: true
      });
      setData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading user detail:', error);
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

  if (!data) {
    return <div className="text-center py-12">Kullanıcı bulunamadı</div>;
  }

  const { user, sessions, all_messages, profile } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button onClick={onBack} variant="ghost">
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex items-center gap-4 flex-1">
          <img
            src={user.picture || 'https://via.placeholder.com/64'}
            alt={user.name}
            className="w-16 h-16 rounded-full"
          />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{user.name}</h2>
            <p className="text-gray-600">{user.email}</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-teal-600" />
            <div>
              <p className="text-sm text-gray-600">Toplam Seans</p>
              <p className="text-2xl font-bold">{data.total_sessions}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <MessageSquare className="w-8 h-8 text-blue-600" />
            <div>
              <p className="text-sm text-gray-600">Toplam Mesaj</p>
              <p className="text-2xl font-bold">{data.total_messages}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Hash className="w-8 h-8 text-purple-600" />
            <div>
              <p className="text-sm text-gray-600">Kullanıcı ID</p>
              <p className="text-sm font-mono">{user.user_id_number || 'Yok'}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Calendar className="w-8 h-8 text-green-600" />
            <div>
              <p className="text-sm text-gray-600">Kayıt Tarihi</p>
              <p className="text-sm font-medium">{new Date(user.created_at).toLocaleDateString('tr-TR')}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-4">
          {['info', 'sessions', 'messages', 'profile'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === tab
                  ? 'border-b-2 border-teal-600 text-teal-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab === 'info' && 'Bilgiler'}
              {tab === 'sessions' && 'Seanslar'}
              {tab === 'messages' && 'Tüm Mesajlar'}
              {tab === 'profile' && 'RAG Profili'}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'info' && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Kullanıcı Bilgileri</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">İsim</p>
              <p className="font-medium">{user.name}</p>
            </div>
            <div>
              <p className="text-gray-600">Email</p>
              <p className="font-medium">{user.email}</p>
            </div>
            <div>
              <p className="text-gray-600">Kullanıcı Tipi</p>
              <p className="font-medium capitalize">{user.user_type}</p>
            </div>
            <div>
              <p className="text-gray-600">Kullanıcı ID</p>
              <p className="font-medium">{user.user_id_number || 'Yok'}</p>
            </div>
            <div>
              <p className="text-gray-600">Terapi Yaklaşımı</p>
              <p className="font-medium uppercase">{user.therapy_approach}</p>
            </div>
            <div>
              <p className="text-gray-600">Kayıt Tarihi</p>
              <p className="font-medium">{new Date(user.created_at).toLocaleString('tr-TR')}</p>
            </div>
            {user.password_hash && (
              <div className="col-span-2">
                <p className="text-gray-600 mb-2">Şifre Hash (Güvenlik)</p>
                <p className="font-mono text-xs bg-gray-100 p-3 rounded break-all">{user.password_hash}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {activeTab === 'sessions' && (
        <div className="space-y-4">
          {sessions.map((session) => (
            <Card key={session.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900">{session.session_name}</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Başlangıç: {new Date(session.started_at).toLocaleString('tr-TR')}
                  </p>
                  {session.ended_at && (
                    <p className="text-sm text-gray-600">
                      Bitiş: {new Date(session.ended_at).toLocaleString('tr-TR')}
                    </p>
                  )}
                  {session.ai_summary && (
                    <div className="mt-3 p-3 bg-blue-50 rounded">
                      <p className="text-sm font-medium text-blue-900 mb-1">AI Özeti:</p>
                      <p className="text-sm text-blue-800 whitespace-pre-wrap">{session.ai_summary}</p>
                    </div>
                  )}
                </div>
                <Badge className={session.status === 'active' ? 'bg-green-500' : 'bg-gray-500'}>
                  {session.status}
                </Badge>
              </div>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'messages' && (
        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          {all_messages.map((msg, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-teal-50 to-blue-50 ml-8'
                  : 'bg-gray-50 mr-8'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline">{msg.role === 'user' ? 'Kullanıcı' : 'MiraMind'}</Badge>
                <span className="text-xs text-gray-500">
                  {new Date(msg.timestamp).toLocaleString('tr-TR')}
                </span>
              </div>
              <p className="text-sm text-gray-800 whitespace-pre-wrap">{msg.content}</p>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'profile' && (
        <Card className="p-6">
          {profile ? (
            <div className="space-y-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-600" />
                  RAG Memory Profili
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  {profile.main_issues && profile.main_issues.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-600 mb-2">Ana Sorunlar</p>
                      <div className="flex flex-wrap gap-2">
                        {profile.main_issues.map((issue, idx) => (
                          <Badge key={idx} variant="secondary">{issue}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {profile.triggers && profile.triggers.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-600 mb-2">Tetikleyiciler</p>
                      <div className="flex flex-wrap gap-2">
                        {profile.triggers.map((trigger, idx) => (
                          <Badge key={idx} className="bg-orange-100 text-orange-700">{trigger}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {profile.session_summaries && profile.session_summaries.length > 0 && (
                <div>
                  <h5 className="font-semibold text-gray-900 mb-3">Seans Özetleri</h5>
                  <div className="space-y-3">
                    {profile.session_summaries.map((summary, idx) => (
                      <div key={idx} className="p-4 bg-purple-50 rounded">
                        <p className="text-xs text-purple-600 mb-2">
                          {new Date(summary.date).toLocaleDateString('tr-TR')}
                        </p>
                        <p className="text-sm text-gray-800 whitespace-pre-wrap">{summary.summary}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-center text-gray-500">Henüz profil oluşturulmamış</p>
          )}
        </Card>
      )}
    </div>
  );
}
