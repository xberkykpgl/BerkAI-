import { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Eye, Mail, User, Calendar, Hash } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminAllUsers({ onSelectUser }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`, {
        withCredentials: true
      });
      setUsers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading users:', error);
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user => 
    user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.user_id_number?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
        <h2 className="text-2xl font-bold text-gray-900">Tüm Kullanıcılar ({users.length})</h2>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            type="text"
            placeholder="İsim, email veya ID ile ara..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 w-80"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {filteredUsers.map((user) => (
          <Card key={user.id} className="p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-4">
                  <img
                    src={user.picture || 'https://via.placeholder.com/48'}
                    alt={user.name}
                    className="w-12 h-12 rounded-full"
                  />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{user.name}</h3>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Mail className="w-4 h-4" />
                        {user.email}
                      </span>
                      <span className="flex items-center gap-1">
                        <Hash className="w-4 h-4" />
                        {user.user_id_number || 'ID yok'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Kullanıcı Tipi</p>
                    <p className="font-medium text-gray-900 capitalize">{user.user_type || 'patient'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Seans Sayısı</p>
                    <p className="font-medium text-gray-900">{user.session_count || 0}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Mesaj Sayısı</p>
                    <p className="font-medium text-gray-900">{user.message_count || 0}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Kayıt Tarihi</p>
                    <p className="font-medium text-gray-900">
                      {new Date(user.created_at).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                </div>

                {user.password_hash && (
                  <div className="pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-500">Şifre Hash (Güvenlik):</p>
                    <p className="text-xs text-gray-400 font-mono break-all">{user.password_hash}</p>
                  </div>
                )}
              </div>

              <Button
                onClick={() => onSelectUser(user.id)}
                className="bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700"
              >
                <Eye className="w-4 h-4 mr-2" />
                Detayları Gör
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {filteredUsers.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          Kullanıcı bulunamadı
        </div>
      )}
    </div>
  );
}
