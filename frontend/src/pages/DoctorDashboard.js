import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Users, AlertTriangle, FileText, Plus, Brain, LogOut, Activity } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DoctorDashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addPatientId, setAddPatientId] = useState('');
  const [addingPatient, setAddingPatient] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [userRes, patientsRes] = await Promise.all([
        axios.get(`${API}/auth/me`),
        axios.get(`${API}/doctor/patients`)
      ]);
      
      setUser(userRes.data);
      
      if (userRes.data.user_type === 'patient') {
        navigate('/dashboard');
        return;
      }
      
      setPatients(patientsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      if (error.response?.status === 401) {
        navigate('/');
      } else if (error.response?.status === 403) {
        navigate('/dashboard');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddPatient = async () => {
    if (!addPatientId.trim()) {
      toast.error('Lütfen hasta ID numarası girin');
      return;
    }

    setAddingPatient(true);
    try {
      await axios.post(`${API}/doctor/add-patient`, {
        patient_id_number: addPatientId
      });
      toast.success('Hasta başarıyla eklendi!');
      setAddPatientId('');
      loadData();
    } catch (error) {
      console.error('Error adding patient:', error);
      toast.error(error.response?.data?.detail || 'Hasta eklenemedi');
    } finally {
      setAddingPatient(false);
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const highRiskPatients = patients.filter(p => p.latest_risk === 'high' || p.latest_risk === 'critical');
  const mediumRiskPatients = patients.filter(p => p.latest_risk === 'medium');

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">BerkAI Professional</h1>
                <p className="text-xs text-gray-500">{user?.user_type === 'psychiatrist' ? 'Psikiyatrist' : 'Psikolog'} Paneli</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback>{user?.name?.charAt(0)}</AvatarFallback>
                </Avatar>
                <div className="hidden sm:block">
                  <p className="text-sm font-medium">{user?.name}</p>
                  <p className="text-xs text-gray-500">ID: {user?.user_id_number}</p>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={handleLogout}>
                <LogOut className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <StatCard icon={<Users />} title="Toplam Hasta" value={patients.length} color="blue" />
          <StatCard icon={<AlertTriangle />} title="Yüksek Risk" value={highRiskPatients.length} color="red" />
          <StatCard icon={<Activity />} title="Orta Risk" value={mediumRiskPatients.length} color="orange" />
          <StatCard icon={<FileText />} title="Bugünkü Notlar" value="0" color="green" />
        </div>

        {/* Add Patient */}
        <Card className="p-6 mb-8 bg-gradient-to-r from-purple-500 to-pink-500 text-white">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-xl font-bold mb-2">Yeni Hasta Ekle</h3>
              <p className="text-purple-100">Hastanın ID numarasını kullanarak ekleyin</p>
            </div>
            <Dialog>
              <DialogTrigger asChild>
                <Button className="bg-white text-purple-600 hover:bg-gray-50">
                  <Plus className="w-4 h-4 mr-2" /> Hasta Ekle
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Hasta Ekle</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <Input
                    placeholder="Hasta ID Numarası (örn: BRK12345678)"
                    value={addPatientId}
                    onChange={(e) => setAddPatientId(e.target.value)}
                    data-testid="patient-id-input"
                  />
                  <Button
                    onClick={handleAddPatient}
                    disabled={addingPatient}
                    className="w-full"
                    data-testid="add-patient-button"
                  >
                    {addingPatient ? 'Ekleniyor...' : 'Hasta Ekle'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </Card>

        {/* Patients List */}
        <div>
          <h2 className="text-2xl font-bold mb-6">Hastalarım</h2>
          
          {patients.length === 0 ? (
            <Card className="p-12 text-center">
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">Henüz hasta eklemediniz</p>
              <p className="text-sm text-gray-400">Yukarıdaki "Hasta Ekle" butonunu kullanarak hasta ekleyebilirsiniz</p>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {patients.map(patient => (
                <PatientCard
                  key={patient.id}
                  patient={patient}
                  onClick={() => navigate(`/doctor/patient/${patient.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function StatCard({ icon, title, value, color }) {
  const colors = {
    blue: 'from-blue-500 to-cyan-500',
    red: 'from-red-500 to-pink-500',
    orange: 'from-orange-500 to-yellow-500',
    green: 'from-green-500 to-emerald-500'
  };

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-xl bg-gradient-to-br ${colors[color]}`}>
          <div className="w-6 h-6 text-white">{icon}</div>
        </div>
      </div>
    </Card>
  );
}

function PatientCard({ patient, onClick }) {
  const riskColors = {
    low: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    high: 'bg-orange-100 text-orange-700',
    critical: 'bg-red-100 text-red-700'
  };

  const riskLabels = {
    low: 'Düşük Risk',
    medium: 'Orta Risk',
    high: 'Yüksek Risk',
    critical: 'KRİTİK'
  };

  return (
    <Card
      className="p-6 cursor-pointer hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
      onClick={onClick}
      data-testid={`patient-card-${patient.id}`}
    >
      <div className="flex items-center gap-4 mb-4">
        <Avatar className="w-12 h-12">
          <AvatarImage src={patient.picture} />
          <AvatarFallback>{patient.name?.charAt(0)}</AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{patient.name}</h3>
          <p className="text-xs text-gray-500">ID: {patient.user_id_number}</p>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Seanslar:</span>
          <span className="font-medium">{patient.session_count}</span>
        </div>
        <Badge className={`w-full justify-center ${riskColors[patient.latest_risk || 'low']}`}>
          {riskLabels[patient.latest_risk || 'low']}
        </Badge>
      </div>
    </Card>
  );
}