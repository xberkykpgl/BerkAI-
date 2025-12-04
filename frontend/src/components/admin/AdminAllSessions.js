import { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar, User, Eye, MessageSquare } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminAllSessions({ onSelectSession }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState(50);

  useEffect(() => {
    loadSessions();
  }, [limit]);

  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API}/admin/sessions?limit=${limit}`, {
        withCredentials: true
      });
      setSessions(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading sessions:', error);
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Tüm Seanslar ({sessions.length})</h2>
        <select
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value={50}>Son 50</option>
          <option value={100}>Son 100</option>
          <option value={200}>Son 200</option>
          <option value={500}>Son 500</option>
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {sessions.map((session) => (
          <Card key={session.id} className="p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-teal-600" />
                  <h3 className="text-lg font-semibold text-gray-900">{session.session_name}</h3>
                  <Badge className={session.status === 'active' ? 'bg-green-500' : 'bg-gray-500'}>
                    {session.status}
                  </Badge>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Kullanıcı ID</p>
                    <p className="font-mono text-xs text-gray-700">{session.user_id}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Başlangıç</p>
                    <p className="font-medium text-gray-900">
                      {new Date(session.started_at).toLocaleString('tr-TR')}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Bitiş</p>
                    <p className="font-medium text-gray-900">
                      {session.ended_at ? new Date(session.ended_at).toLocaleString('tr-TR') : 'Devam ediyor'}
                    </p>
                  </div>
                </div>

                {session.ai_summary && (
                  <div className="mt-3 p-3 bg-blue-50 rounded">
                    <p className="text-xs font-medium text-blue-900 mb-1">AI Özeti:</p>
                    <p className="text-sm text-blue-800 whitespace-pre-wrap line-clamp-3">{session.ai_summary}</p>
                  </div>
                )}
              </div>

              <Button
                onClick={() => onSelectSession(session.id)}
                variant="outline"
                size="sm"
              >
                <Eye className="w-4 h-4 mr-2" />
                Mesajları Gör
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {sessions.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          Seans bulunamadı
        </div>
      )}
    </div>
  );
}
