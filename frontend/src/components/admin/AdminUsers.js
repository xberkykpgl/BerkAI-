import { useState, useEffect } from 'react';
import axios from 'axios';
import { User, Mail, Calendar, MessageSquare } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDetail, setUserDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserDetail = async (userId) => {
    try {
      const response = await axios.get(`${API}/admin/users/${userId}`);
      setUserDetail(response.data);
      setSelectedUser(userId);
    } catch (error) {
      console.error('Error loading user detail:', error);
    }
  };

  if (loading) {
    return <div className="text-white text-center py-8">Yükleniyor...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {users.map(user => (
          <Card
            key={user.id}
            className="p-4 bg-white/10 backdrop-blur-lg border-white/20 hover:bg-white/15 transition-all cursor-pointer"
            onClick={() => loadUserDetail(user.id)}
            data-testid={`user-card-${user.id}`}
          >
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-semibold">
                {user.name?.charAt(0)}
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-white">{user.name}</h4>
                <p className="text-sm text-gray-300 flex items-center gap-1">
                  <Mail className="w-3 h-3" />
                  {user.email}
                </p>
                <div className="flex gap-4 mt-2 text-xs text-gray-400">
                  <span>{user.session_count} seans</span>
                  <span>{user.message_count} mesaj</span>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* User Detail Dialog */}
      <Dialog open={!!selectedUser} onOpenChange={() => setSelectedUser(null)}>
        <DialogContent className="bg-slate-900 border-white/20 text-white max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">Kullanıcı Detayları</DialogTitle>
          </DialogHeader>
          {userDetail && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-white/5 rounded-lg">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white text-2xl font-semibold">
                  {userDetail.user.name?.charAt(0)}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">{userDetail.user.name}</h3>
                  <p className="text-gray-300">{userDetail.user.email}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Kayıt: {new Date(userDetail.user.created_at).toLocaleDateString('tr-TR')}
                  </p>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-3">Seanslar ({userDetail.sessions.length})</h4>
                <div className="space-y-2">
                  {userDetail.sessions.map(session => (
                    <div key={session.id} className="p-3 bg-white/5 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium text-white">{session.session_name}</p>
                          <p className="text-xs text-gray-400">
                            {new Date(session.started_at).toLocaleString('tr-TR')}
                          </p>
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          session.status === 'active'
                            ? 'bg-green-500/20 text-green-300'
                            : 'bg-gray-500/20 text-gray-300'
                        }`}>
                          {session.status === 'active' ? 'Aktif' : 'Tamamlandı'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-3 flex items-center justify-between">
                  <span>Tüm Mesajlar ({userDetail.recent_messages.length})</span>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => {
                      const allMessages = userDetail.recent_messages.map(m => 
                        `[${new Date(m.timestamp).toLocaleString('tr-TR')}] ${m.role === 'user' ? 'Kullanıcı' : 'BerkAI'}: ${m.content}`
                      ).join('\n\n');
                      navigator.clipboard.writeText(allMessages);
                      toast.success('Mesajlar kopyalandı!');
                    }}
                    className="text-xs"
                  >
                    Kopyala
                  </Button>
                </h4>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {userDetail.recent_messages.map(msg => (
                    <div key={msg.id} className="p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <span className={`text-xs font-medium px-2 py-1 rounded ${
                          msg.role === 'user' ? 'bg-blue-500/20 text-blue-300' : 'bg-purple-500/20 text-purple-300'
                        }`}>
                          {msg.role === 'user' ? 'Kullanıcı' : 'BerkAI'}
                        </span>
                        <span className="text-xs text-gray-400">
                          {new Date(msg.timestamp).toLocaleString('tr-TR')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-300 whitespace-pre-wrap">{msg.content}</p>
                      {msg.video_analysis && (
                        <div className="mt-2 pt-2 border-t border-white/10">
                          <p className="text-xs text-gray-400">Video Analizi:</p>
                          <div className="text-xs text-gray-300 mt-1">
                            <span className="mr-3">Duygu: {msg.video_analysis.emotion}</span>
                            <span>Stres: {msg.video_analysis.stress_level}/10</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}