import { useState, useEffect } from 'react';
import axios from 'axios';
import { Video, Calendar, MessageSquare, Eye } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminSessions() {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API}/admin/sessions`);
      setSessions(response.data);
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/admin/sessions/${sessionId}/messages`);
      setMessages(response.data);
      setSelectedSession(sessionId);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  if (loading) {
    return <div className="text-white text-center py-8">Yükleniyor...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="grid md:grid-cols-2 gap-4">
        {sessions.map(session => (
          <Card
            key={session.id}
            className="p-4 bg-white/10 backdrop-blur-lg border-white/20 hover:bg-white/15 transition-all"
            data-testid={`session-card-${session.id}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  session.status === 'active'
                    ? 'bg-gradient-to-br from-green-500 to-emerald-500'
                    : 'bg-gradient-to-br from-gray-500 to-gray-600'
                }`}>
                  <Video className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h4 className="font-semibold text-white">{session.session_name}</h4>
                  <p className="text-xs text-gray-400">
                    {new Date(session.started_at).toLocaleString('tr-TR')}
                  </p>
                </div>
              </div>
              <span className={`px-3 py-1 text-xs rounded-full ${
                session.status === 'active'
                  ? 'bg-green-500/20 text-green-300'
                  : 'bg-gray-500/20 text-gray-300'
              }`}>
                {session.status === 'active' ? 'Aktif' : 'Tamamlandı'}
              </span>
            </div>
            <div className="text-sm text-gray-300 mb-3">
              Kullanıcı ID: {session.user_id}
            </div>
            <Button
              onClick={() => loadSessionMessages(session.id)}
              size="sm"
              className="w-full bg-purple-600 hover:bg-purple-700"
            >
              <Eye className="w-4 h-4 mr-2" />
              Mesajları Gör
            </Button>
          </Card>
        ))}
      </div>

      {/* Messages Dialog */}
      <Dialog open={!!selectedSession} onOpenChange={() => setSelectedSession(null)}>
        <DialogContent className="bg-slate-900 border-white/20 text-white max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">Seans Mesajları</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`p-4 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-blue-500/20 ml-8'
                    : 'bg-purple-500/20 mr-8'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className={`text-sm font-medium ${
                    msg.role === 'user' ? 'text-blue-300' : 'text-purple-300'
                  }`}>
                    {msg.role === 'user' ? 'Kullanıcı' : 'MiraMind'}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(msg.timestamp).toLocaleString('tr-TR')}
                  </span>
                </div>
                <p className="text-white">{msg.content}</p>
                {msg.video_analysis && (
                  <div className="mt-3 pt-3 border-t border-white/10">
                    <p className="text-xs text-gray-400 mb-2">Video Analizi:</p>
                    <div className="text-sm text-gray-300">
                      <p>Duygu: {msg.video_analysis.emotion}</p>
                      <p>Stres: {msg.video_analysis.stress_level}/10</p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}