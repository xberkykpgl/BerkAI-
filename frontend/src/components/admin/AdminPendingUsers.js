import { useState, useEffect } from 'react';
import axios from 'axios';
import { UserCheck, UserX, Clock, AlertCircle, Mail, User, Calendar, Hash } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Textarea } from '../ui/textarea';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminPendingUsers() {
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadPendingUsers();
  }, []);

  const loadPendingUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/pending-users`, {
        withCredentials: true
      });
      setPendingUsers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading pending users:', error);
      setLoading(false);
    }
  };

  const handleApprove = async (userId) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/admin/approve-user/${userId}`, {}, {
        withCredentials: true
      });
      toast.success('Kullanıcı onaylandı!');
      loadPendingUsers();
    } catch (error) {
      console.error('Error approving user:', error);
      toast.error('Kullanıcı onaylanamadı');
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      toast.error('Lütfen red nedeni girin');
      return;
    }

    setProcessing(true);
    try {
      await axios.post(`${API}/admin/reject-user/${selectedUser.id}`, {
        reason: rejectionReason
      }, {
        withCredentials: true
      });
      toast.success('Kullanıcı reddedildi');
      setRejectDialogOpen(false);
      setRejectionReason('');
      setSelectedUser(null);
      loadPendingUsers();
    } catch (error) {
      console.error('Error rejecting user:', error);
      toast.error('Kullanıcı reddedilemedi');
    } finally {
      setProcessing(false);
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
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Clock className="w-7 h-7 text-orange-600" />
            Onay Bekleyen Kullanıcılar
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Psikolog ve psikiyatrist hesapları admin onayı bekliyor
          </p>
        </div>
        <Badge className="bg-orange-500 text-white text-lg px-4 py-2">
          {pendingUsers.length} Bekliyor
        </Badge>
      </div>

      {pendingUsers.length === 0 ? (
        <Card className="p-12 text-center">
          <UserCheck className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Tüm Kullanıcılar Onaylandı</h3>
          <p className="text-gray-500">Onay bekleyen kullanıcı bulunmuyor</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {pendingUsers.map((user) => (
            <Card key={user.id} className="p-6 border-l-4 border-orange-500 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1 space-y-3">
                  {/* User Info */}
                  <div className="flex items-center gap-4">
                    <img
                      src={user.picture || 'https://via.placeholder.com/64'}
                      alt={user.name}
                      className="w-16 h-16 rounded-full border-2 border-orange-200"
                    />
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900">{user.name}</h3>
                      <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                        <span className="flex items-center gap-1">
                          <Mail className="w-4 h-4" />
                          {user.email}
                        </span>
                        <span className="flex items-center gap-1">
                          <User className="w-4 h-4" />
                          {user.user_type === 'doctor' ? 'Psikolog' : 'Psikiyatrist'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Additional Info */}
                  <div className="grid grid-cols-3 gap-4 text-sm bg-gray-50 p-3 rounded">
                    <div>
                      <p className="text-gray-500">ID Numarası</p>
                      <p className="font-medium text-gray-900">{user.user_id_number}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Kayıt Tarihi</p>
                      <p className="font-medium text-gray-900">
                        {new Date(user.created_at).toLocaleDateString('tr-TR')}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Terapi Yaklaşımı</p>
                      <p className="font-medium text-gray-900 uppercase">{user.therapy_approach}</p>
                    </div>
                  </div>

                  {user.license_number && (
                    <div className="p-3 bg-blue-50 rounded">
                      <p className="text-xs text-blue-600 font-medium">Lisans Numarası</p>
                      <p className="text-sm text-blue-900">{user.license_number}</p>
                    </div>
                  )}

                  {user.specialization && (
                    <div className="p-3 bg-purple-50 rounded">
                      <p className="text-xs text-purple-600 font-medium">Uzmanlık Alanı</p>
                      <p className="text-sm text-purple-900">{user.specialization}</p>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-3 ml-6">
                  <Button
                    onClick={() => handleApprove(user.id)}
                    disabled={processing}
                    className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white"
                  >
                    <UserCheck className="w-4 h-4 mr-2" />
                    Onayla
                  </Button>
                  <Button
                    onClick={() => {
                      setSelectedUser(user);
                      setRejectDialogOpen(true);
                    }}
                    disabled={processing}
                    variant="destructive"
                    className="bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700"
                  >
                    <UserX className="w-4 h-4 mr-2" />
                    Reddet
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-5 h-5" />
              Kullanıcıyı Reddet
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div>
              <p className="text-sm text-gray-700 mb-2">
                <strong>{selectedUser?.name}</strong> adlı kullanıcıyı reddetmek üzeresiniz.
              </p>
              <p className="text-sm text-gray-600 mb-4">
                Lütfen red nedenini açıklayın:
              </p>
              <Textarea
                placeholder="Red nedeni..."
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                rows={4}
                className="w-full"
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleReject}
                disabled={processing || !rejectionReason.trim()}
                variant="destructive"
                className="flex-1"
              >
                {processing ? 'İşleniyor...' : 'Reddet'}
              </Button>
              <Button
                onClick={() => {
                  setRejectDialogOpen(false);
                  setRejectionReason('');
                  setSelectedUser(null);
                }}
                variant="outline"
                className="flex-1"
              >
                İptal
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
