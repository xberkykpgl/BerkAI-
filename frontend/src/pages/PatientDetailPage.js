import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, AlertTriangle, FileText, Plus, Activity, Video, Calendar, TrendingUp, Mic, MicOff } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { VoiceRecognition } from '../utils/voiceRecognition';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function PatientDetailPage() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [riskAlerts, setRiskAlerts] = useState([]);
  const [notes, setNotes] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const voiceRecognitionRef = useRef(null);

  useEffect(() => {
    loadPatientData();
  }, [patientId]);

  const loadPatientData = async () => {
    try {
      const [patientRes, riskRes, notesRes] = await Promise.all([
        axios.get(`${API}/admin/users/${patientId}`),
        axios.get(`${API}/doctor/patient/${patientId}/risk-alerts`),
        axios.get(`${API}/doctor/patient/${patientId}/notes`)
      ]);

      setPatient(patientRes.data.user);
      setSessions(patientRes.data.sessions);
      setMessages(patientRes.data.all_messages || patientRes.data.recent_messages);
      setProfile(patientRes.data.profile);
      setRiskAlerts(riskRes.data);
      setNotes(notesRes.data);
    } catch (error) {
      console.error('Error loading patient data:', error);
      if (error.response?.status === 403) {
        toast.error('Bu danışana erişim yetkiniz yok');
        navigate('/doctor/dashboard');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveNote = async () => {
    if (!newNote.trim()) {
      toast.error('Lütfen not girin');
      return;
    }

    setSavingNote(true);
    try {
      await axios.post(`${API}/doctor/patient/${patientId}/note`, {
        content: newNote,
        note_type: 'clinical_note',
        tags: []
      });
      toast.success('Not kaydedildi');
      setNewNote('');
      loadPatientData();
    } catch (error) {
      console.error('Error saving note:', error);
      toast.error('Not kaydedilemedi');
    } finally {
      setSavingNote(false);
    }
  };

  const handleVoiceNote = () => {
    if (isRecording) {
      // Stop recording
      if (voiceRecognitionRef.current) {
        voiceRecognitionRef.current.stop();
      }
      setIsRecording(false);
      return;
    }

    // Initialize voice recognition if not exists
    if (!voiceRecognitionRef.current) {
      voiceRecognitionRef.current = new VoiceRecognition(
        // onResult
        (transcript, isFinal) => {
          setNewNote(transcript);
        },
        // onError  
        (errorMessage) => {
          toast.error(errorMessage);
          setIsRecording(false);
        },
        // onStart
        () => {
          setIsRecording(true);
          toast.success('🎤 Dinliyorum - not alıyorum...', { duration: 30000 });
        },
        // onEnd
        (finalTranscript) => {
          setIsRecording(false);
          if (finalTranscript) {
            toast.success('✅ Not kaydedildi!');
          }
        }
      );
    }

    // Check support
    if (!voiceRecognitionRef.current.isSupported()) {
      toast.error('Tarayıcınız ses tanımayı desteklemiyor. Lütfen Chrome veya Edge kullanın.');
      return;
    }

    // Start recording
    const started = voiceRecognitionRef.current.start();
    if (!started) {
      toast.error('Ses tanıma başlatılamadı. Lütfen metin yazın.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const criticalRisks = riskAlerts.filter(r => r.risk_category === 'critical');
  const highRisks = riskAlerts.filter(r => r.risk_category === 'high');
  const avgRisk = riskAlerts.length > 0 
    ? (riskAlerts.reduce((sum, r) => sum + r.risk_level, 0) / riskAlerts.length).toFixed(1)
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/doctor/dashboard')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-4 flex-1">
              <Avatar className="w-12 h-12">
                <AvatarImage src={patient?.picture} />
                <AvatarFallback>{patient?.name?.charAt(0)}</AvatarFallback>
              </Avatar>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{patient?.name}</h1>
                <p className="text-sm text-gray-500">ID: {patient?.user_id_number}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Risk Summary */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<AlertTriangle />}
            title="Kritik Risk"
            value={criticalRisks.length}
            color="red"
          />
          <StatCard
            icon={<Activity />}
            title="Yüksek Risk"
            value={highRisks.length}
            color="orange"
          />
          <StatCard
            icon={<TrendingUp />}
            title="Ort. Risk Seviyesi"
            value={avgRisk}
            color="blue"
          />
          <StatCard
            icon={<Video />}
            title="Toplam Seans"
            value={sessions.length}
            color="green"
          />
        </div>

        {/* Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Genel Bakış</TabsTrigger>
            <TabsTrigger value="ai-insights">AI Özetleri & Profil</TabsTrigger>
            <TabsTrigger value="sessions">Seanslar</TabsTrigger>
            <TabsTrigger value="risks">Risk Uyarıları</TabsTrigger>
            <TabsTrigger value="notes">Klinik Notlar</TabsTrigger>
          </TabsList>

          {/* Overview */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Recent Messages */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Son Mesajlar</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {messages.slice(0, 10).map(msg => (
                    <div key={msg.id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start mb-1">
                        <Badge variant={msg.role === 'user' ? 'default' : 'secondary'} className="text-xs">
                          {msg.role === 'user' ? 'Danışan' : 'BerkAI'}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {new Date(msg.timestamp).toLocaleDateString('tr-TR')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">{msg.content.substring(0, 150)}...</p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Recent Risks */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Son Risk Değerlendirmeleri</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {riskAlerts.slice(0, 10).map(risk => (
                    <RiskCard key={risk.id} risk={risk} />
                  ))}
                </div>
              </Card>
            </div>
          </TabsContent>

          {/* Sessions */}
          <TabsContent value="sessions">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Tüm Seanslar ({sessions.length})</h3>
              <div className="space-y-4">
                {sessions.map(session => (
                  <div key={session.id} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-teal-500 to-blue-500 flex items-center justify-center">
                          <Video className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h4 className="font-semibold">{session.session_name}</h4>
                          <p className="text-sm text-gray-500">
                            {new Date(session.started_at).toLocaleString('tr-TR')}
                          </p>
                        </div>
                      </div>
                      <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
                        {session.status === 'active' ? 'Aktif' : 'Tamamlandı'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Risk Alerts */}
          <TabsContent value="risks">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Tüm Risk Uyarıları ({riskAlerts.length})</h3>
              <div className="space-y-4">
                {riskAlerts.map(risk => (
                  <RiskCard key={risk.id} risk={risk} detailed />
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Clinical Notes */}
          <TabsContent value="notes">
            <div className="space-y-6">
              {/* Add New Note */}
              <Card className="p-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Yeni Not Ekle</h3>
                  <Button
                    onClick={handleVoiceNote}
                    variant="secondary"
                    size="sm"
                    className={`${isRecording ? 'bg-red-500 hover:bg-red-600' : 'bg-white/20 hover:bg-white/30'} text-white`}
                  >
                    {isRecording ? (
                      <>
                        <MicOff className="w-4 h-4 mr-2" />
                        Durdur
                      </>
                    ) : (
                      <>
                        <Mic className="w-4 h-4 mr-2" />
                        Sesli Not
                      </>
                    )}
                  </Button>
                </div>
                {isRecording && (
                  <div className="mb-3 text-sm bg-white/10 p-2 rounded animate-pulse">
                    🎤 Dinliyorum... Konuşun
                  </div>
                )}
                <Textarea
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder="Klinik notunuzu buraya yazın veya sesli kaydedin..."
                  rows={6}
                  className="bg-white/20 text-white placeholder:text-white/60 border-white/30"
                />
                <div className="flex gap-3 mt-4">
                  <Button
                    onClick={handleSaveNote}
                    disabled={savingNote || !newNote.trim()}
                    className="flex-1 bg-white text-purple-600 hover:bg-gray-50"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    {savingNote ? 'Kaydediliyor...' : 'Not Ekle'}
                  </Button>
                  {newNote.trim() && (
                    <Button
                      onClick={() => setNewNote('')}
                      variant="secondary"
                      className="bg-white/20 hover:bg-white/30 text-white"
                    >
                      Temizle
                    </Button>
                  )}
                </div>
              </Card>

              {/* Notes List */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Klinik Notlar ({notes.length})</h3>
                <div className="space-y-4">
                  {notes.map(note => (
                    <div key={note.id} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <Badge>{note.note_type}</Badge>
                        <span className="text-xs text-gray-500">
                          {new Date(note.timestamp).toLocaleString('tr-TR')}
                        </span>
                      </div>
                      <p className="text-gray-700 whitespace-pre-wrap">{note.content}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

function StatCard({ icon, title, value, color }) {
  const colors = {
    red: 'from-red-500 to-pink-500',
    orange: 'from-orange-500 to-yellow-500',
    blue: 'from-blue-500 to-cyan-500',
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

function RiskCard({ risk, detailed = false }) {
  const riskColors = {
    low: 'bg-green-100 text-green-700 border-green-300',
    medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    high: 'bg-orange-100 text-orange-700 border-orange-300',
    critical: 'bg-red-100 text-red-700 border-red-300'
  };

  return (
    <div className={`p-4 rounded-lg border-2 ${riskColors[risk.risk_category]}`}>
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          <span className="font-semibold">Risk Seviyesi: {risk.risk_level}/10</span>
        </div>
        <span className="text-xs">
          {new Date(risk.timestamp).toLocaleString('tr-TR')}
        </span>
      </div>
      
      {risk.suicide_risk && (
        <Badge className="mr-2 bg-red-600 text-white">İntihar Riski</Badge>
      )}
      {risk.self_harm_risk && (
        <Badge className="mr-2 bg-orange-600 text-white">Kendine Zarar</Badge>
      )}
      {risk.crisis_detected && (
        <Badge className="bg-yellow-600 text-white">Kriz</Badge>
      )}

      {detailed && risk.risk_indicators && risk.risk_indicators.length > 0 && (
        <div className="mt-3">
          <p className="text-sm font-medium mb-1">Göstergeler:</p>
          <ul className="text-sm space-y-1">
            {risk.risk_indicators.map((indicator, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span>•</span>
                <span>{indicator}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
