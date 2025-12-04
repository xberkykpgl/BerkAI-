import { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, User, Calendar, MessageSquare, Filter } from 'lucide-react';
import { Card } from '../ui/card';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminAllMessages() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [limit, setLimit] = useState(100);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadMessages();
  }, [limit, page]);

  const loadMessages = async () => {
    try {
      const skip = page * limit;
      const response = await axios.get(`${API}/admin/all-messages?limit=${limit}&skip=${skip}`, {
        withCredentials: true
      });
      setMessages(response.data.messages);
      setTotal(response.data.total);
      setLoading(false);
    } catch (error) {
      console.error('Error loading messages:', error);
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const response = await axios.get(`${API}/admin/search?query=${encodeURIComponent(searchQuery)}`, {
        withCredentials: true
      });
      setSearchResults(response.data.results);
      setSearching(false);
    } catch (error) {
      console.error('Error searching:', error);
      setSearching(false);
    }
  };

  const displayMessages = searchResults.length > 0 ? searchResults : messages;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Tüm Mesajlar ({total})</h2>
        <div className="flex items-center gap-4">
          <select
            value={limit}
            onChange={(e) => { setLimit(Number(e.target.value)); setPage(0); }}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value={50}>50 mesaj</option>
            <option value={100}>100 mesaj</option>
            <option value={200}>200 mesaj</option>
          </select>
        </div>
      </div>

      {/* Search */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            type="text"
            placeholder="Mesaj içeriğinde ara..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="pl-10"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={searching}
          className="px-6 py-2 bg-gradient-to-r from-teal-600 to-blue-600 text-white rounded-lg hover:from-teal-700 hover:to-blue-700 disabled:opacity-50"
        >
          {searching ? 'Araniyor...' : 'Ara'}
        </button>
      </div>

      {searchResults.length > 0 && (
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-900">
            <strong>{searchResults.length}</strong> sonuç bulundu: "{searchQuery}"
          </p>
        </div>
      )}

      {/* Messages */}
      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {displayMessages.map((msg, idx) => (
          <Card key={idx} className={`p-4 ${
            msg.role === 'user'
              ? 'bg-gradient-to-r from-teal-50 to-blue-50 border-l-4 border-teal-500'
              : 'bg-gray-50 border-l-4 border-gray-300'
          }`}>
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline">
                  {msg.role === 'user' ? 'Kullanıcı' : 'BerkAI'}
                </Badge>
                {msg.user_name && (
                  <span className="text-sm font-medium text-gray-700">{msg.user_name}</span>
                )}
                {msg.user_email && (
                  <span className="text-xs text-gray-500">({msg.user_email})</span>
                )}
              </div>
              <span className="text-xs text-gray-500">
                {new Date(msg.timestamp).toLocaleString('tr-TR')}
              </span>
            </div>
            <p className="text-sm text-gray-800 whitespace-pre-wrap">{msg.content}</p>
            {msg.session_id && (
              <p className="text-xs text-gray-400 mt-2">Seans ID: {msg.session_id}</p>
            )}
          </Card>
        ))}
      </div>

      {/* Pagination */}
      {!searchResults.length && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
          >
            Önceki
          </button>
          <span className="text-sm text-gray-600">
            Sayfa {page + 1} / {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
          >
            Sonraki
          </button>
        </div>
      )}

      {displayMessages.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          Mesaj bulunamadı
        </div>
      )}
    </div>
  );
}
