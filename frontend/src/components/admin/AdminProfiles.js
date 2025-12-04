import { useState, useEffect } from 'react';
import axios from 'axios';
import { Brain, User, Calendar, Tag, TrendingUp } from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminProfiles() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const response = await axios.get(`${API}/admin/profiles`, {
        withCredentials: true
      });
      setProfiles(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading profiles:', error);
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
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Brain className="w-8 h-8 text-purple-600" />
          RAG Memory Profilleri ({profiles.length})
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {profiles.map((profile, idx) => (
          <Card key={idx} className="p-6">
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{profile.user_name || 'Bilinmeyen'}</h3>
                  <p className="text-sm text-gray-600">{profile.user_email}</p>
                </div>
                <Badge variant="outline" className="bg-purple-100 text-purple-700">
                  {profile.session_summaries?.length || 0} Seans
                </Badge>
              </div>

              {/* Main Issues */}
              {profile.main_issues && profile.main_issues.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                    <Tag className="w-4 h-4" />
                    Ana Sorunlar
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {profile.main_issues.map((issue, i) => (
                      <Badge key={i} className="bg-red-100 text-red-700">{issue}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Triggers */}
              {profile.triggers && profile.triggers.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                    <TrendingUp className="w-4 h-4" />
                    Tetikleyiciler
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {profile.triggers.map((trigger, i) => (
                      <Badge key={i} className="bg-orange-100 text-orange-700">{trigger}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Coping Strategies */}
              {profile.coping_strategies && profile.coping_strategies.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Başa Çıkma Stratejileri</p>
                  <div className="flex flex-wrap gap-2">
                    {profile.coping_strategies.map((strategy, i) => (
                      <Badge key={i} className="bg-green-100 text-green-700">{strategy}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Session Summaries */}
              {profile.session_summaries && profile.session_summaries.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Son Seans Özetleri</p>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {profile.session_summaries.slice(-3).reverse().map((summary, i) => (
                      <div key={i} className="p-3 bg-purple-50 rounded text-sm">
                        <p className="text-xs text-purple-600 mb-1">
                          {new Date(summary.date).toLocaleDateString('tr-TR')}
                        </p>
                        <p className="text-gray-800 line-clamp-3">{summary.summary}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="pt-3 border-t border-gray-200 text-xs text-gray-500">
                Son güncelleme: {new Date(profile.last_updated).toLocaleString('tr-TR')}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {profiles.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          Henüz profil oluşturulmamış
        </div>
      )}
    </div>
  );
}
