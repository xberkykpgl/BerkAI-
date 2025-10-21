import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Video, VideoOff, Send, Brain, Activity, AlertCircle, CheckCircle, Mic, MicOff } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function SessionPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const captureIntervalRef = useRef(null);
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isVideoOn, setIsVideoOn] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [currentAudioUrl, setCurrentAudioUrl] = useState(null);

  useEffect(() => {
    loadSession();
    loadMessages();
    loadAnalytics();

    return () => {
      stopVideo();
    };
  }, [sessionId]);

  const loadSession = async () => {
    try {
      const response = await axios.get(`${API}/sessions/${sessionId}`);
      setSession(response.data);
    } catch (error) {
      console.error('Error loading session:', error);
      if (error.response?.status === 404) {
        toast.error('Seans bulunamadı');
        navigate('/dashboard');
      }
    }
  };

  const loadMessages = async () => {
    try {
      const response = await axios.get(`${API}/sessions/${sessionId}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/sessions/${sessionId}/analytics`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const startVideo = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 1280, height: 720 }, 
        audio: false 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setIsVideoOn(true);
        toast.success('Kamera aktif');

        // Start periodic frame capture (every 10 seconds)
        captureIntervalRef.current = setInterval(() => {
          captureFrame();
        }, 10000);
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      toast.error('Kamera erişimi reddedildi');
    }
  };

  const stopVideo = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (captureIntervalRef.current) {
      clearInterval(captureIntervalRef.current);
      captureIntervalRef.current = null;
    }
    setIsVideoOn(false);
  };

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    return canvas.toDataURL('image/jpeg', 0.8);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Transcribe audio using Whisper
        try {
          const formData = new FormData();
          formData.append('file', audioBlob, 'recording.webm');
          
          const response = await axios.post(`${API}/transcribe`, formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          });
          
          // Set transcribed text to input
          setInputMessage(response.data.text);
          toast.success('Ses metne çevrildi!');
        } catch (error) {
          console.error('Transcription error:', error);
          toast.error('Ses çevrilemedi');
        }
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      toast.success('Ses kaydı başladı - konuşun');
    } catch (error) {
      console.error('Microphone access error:', error);
      toast.error('Mikrofon erişimi reddedildi');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isSending) return;

    setIsSending(true);
    const messageText = inputMessage;
    setInputMessage('');

    // Add user message to UI
    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);

    // Add loading message
    const loadingMsg = {
      id: Date.now().toString() + '_loading',
      role: 'assistant',
      content: 'BerkAI düşünüyor ve yanıt hazırlıyor...',
      timestamp: new Date().toISOString(),
      isLoading: true
    };
    setMessages(prev => [...prev, loadingMsg]);

    try {
      // Capture frame if video is on
      const frameData = isVideoOn ? captureFrame() : null;

      const response = await axios.post(`${API}/sessions/${sessionId}/chat`, {
        message: messageText,
        video_frame: frameData
      });

      // Remove loading message and add AI response
      setMessages(prev => prev.filter(m => m.id !== loadingMsg.id));

      const aiMsg = {
        id: Date.now().toString() + '_ai',
        role: 'assistant',
        content: response.data.message,
        video_analysis: response.data.video_analysis,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMsg]);

      // Speak response using Web Speech API
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(response.data.message);
        utterance.lang = 'tr-TR';
        utterance.rate = 0.9;
        utterance.pitch = 1;
        window.speechSynthesis.speak(utterance);
      }

      // Update current analysis
      if (response.data.video_analysis) {
        setCurrentAnalysis(response.data.video_analysis);
        loadAnalytics(); // Refresh analytics
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => prev.filter(m => m.id !== loadingMsg.id));
      toast.error('Mesaj gönderilemedi');
    } finally {
      setIsSending(false);
    }
  };

  const completeSession = async () => {
    try {
      await axios.patch(`${API}/sessions/${sessionId}/complete`, {
        analysis_summary: analytics
      });
      toast.success('Seans tamamlandı');
      navigate('/dashboard');
    } catch (error) {
      console.error('Error completing session:', error);
      toast.error('Seans tamamlanamadı');
    }
  };

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-teal-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                size="icon"
                onClick={() => navigate('/dashboard')}
                data-testid="back-button"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{session.session_name}</h1>
                <p className="text-sm text-gray-500">
                  {new Date(session.started_at).toLocaleString('tr-TR')}
                </p>
              </div>
            </div>
            <Button 
              onClick={completeSession}
              data-testid="complete-session-button"
              className="bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Seansı Bitir
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Chat Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Video Section */}
            <Card className="p-6 bg-white/80 backdrop-blur-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Video className="w-5 h-5" />
                  Video Analizi
                </h3>
                <Button
                  onClick={isVideoOn ? stopVideo : startVideo}
                  data-testid="toggle-video-button"
                  variant={isVideoOn ? 'destructive' : 'default'}
                  className={!isVideoOn ? 'bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700' : ''}
                >
                  {isVideoOn ? (
                    <><VideoOff className="w-4 h-4 mr-2" /> Kamerayı Kapat</>
                  ) : (
                    <><Video className="w-4 h-4 mr-2" /> Kamerayı Aç</>
                  )}
                </Button>
              </div>
              <div className="video-container bg-gray-900 rounded-xl overflow-hidden" style={{ aspectRatio: '16/9' }}>
                <video 
                  ref={videoRef} 
                  autoPlay 
                  playsInline 
                  muted
                  className="w-full h-full object-cover"
                  data-testid="video-element"
                />
                <canvas ref={canvasRef} style={{ display: 'none' }} />
                {!isVideoOn && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center text-gray-400">
                      <VideoOff className="w-16 h-16 mx-auto mb-4" />
                      <p>Kamera kapalı</p>
                    </div>
                  </div>
                )}
              </div>
            </Card>

            {/* Chat Section */}
            <Card className="p-6 bg-white/80 backdrop-blur-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5" />
                BerkAI ile Sohbet
              </h3>
              
              <div className="space-y-4 mb-4 max-h-96 overflow-y-auto" data-testid="messages-container">
                {messages.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <p>Sohbete hoş geldiniz. BerkAI sizinle konuşmaya hazır.</p>
                  </div>
                )}
                {messages.map(msg => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
              </div>

              <div className="space-y-3">
                <div className="flex gap-2">
                  <Textarea 
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
                    placeholder="Mesajınızı yazın veya ses ile konuşun..."
                    data-testid="message-input"
                    className="resize-none flex-1"
                    rows={3}
                    disabled={isSending}
                  />
                  <div className="flex flex-col gap-2">
                    <Button 
                      onClick={isRecording ? stopRecording : startRecording}
                      data-testid="toggle-mic-button"
                      variant={isRecording ? 'destructive' : 'outline'}
                      size="icon"
                      className="h-12 w-12"
                    >
                      {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                    </Button>
                    <Button 
                      onClick={sendMessage}
                      disabled={!inputMessage.trim() || isSending}
                      data-testid="send-message-button"
                      size="icon"
                      className="bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700 h-12 w-12"
                    >
                      <Send className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
                {/* Hidden audio player for TTS */}
                <audio ref={audioRef} className="hidden" />
              </div>
            </Card>
          </div>

          {/* Analytics Sidebar */}
          <div className="space-y-6">
            {/* Current Analysis */}
            {currentAnalysis && (
              <Card className="p-6 bg-white/80 backdrop-blur-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Anlık Analiz
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Duygu Durumu</label>
                    <Badge className="mt-1 w-full justify-center py-2 bg-gradient-to-r from-teal-500 to-blue-500 text-white">
                      {currentAnalysis.emotion || 'Belirsiz'}
                    </Badge>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-600 block mb-2">Stres Seviyesi</label>
                    <Progress 
                      value={(currentAnalysis.stress_level || 5) * 10} 
                      className="h-3"
                    />
                    <p className="text-xs text-gray-500 mt-1">{currentAnalysis.stress_level || 5}/10</p>
                  </div>

                  {currentAnalysis.deception_indicators && currentAnalysis.deception_indicators.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-600 flex items-center gap-1 mb-2">
                        <AlertCircle className="w-4 h-4" />
                        Belirti Göstergeleri
                      </label>
                      <ul className="text-xs text-gray-600 space-y-1">
                        {currentAnalysis.deception_indicators.map((indicator, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-orange-500">•</span>
                            {indicator}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Session Summary */}
            {analytics && (
              <Card className="p-6 bg-white/80 backdrop-blur-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Seans Özeti</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Ortalama Stres</span>
                    <span className="font-semibold text-gray-900">{analytics.summary?.average_stress || 0}/10</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Analiz Sayısı</span>
                    <span className="font-semibold text-gray-900">{analytics.summary?.total_frames || 0}</span>
                  </div>
                  {analytics.summary?.detected_emotions && analytics.summary.detected_emotions.length > 0 && (
                    <div>
                      <span className="text-sm text-gray-600 block mb-2">Tespit Edilen Duygular</span>
                      <div className="flex flex-wrap gap-2">
                        {[...new Set(analytics.summary.detected_emotions)].map((emotion, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {emotion}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isLoading = message.isLoading;
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} chat-message`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
        isUser 
          ? 'bg-gradient-to-r from-teal-600 to-blue-600 text-white' 
          : 'bg-gray-100 text-gray-900'
      }`}>
        <p className={`text-sm whitespace-pre-wrap ${isLoading ? 'pulse-animation' : ''}`}>
          {message.content}
        </p>
        <p className={`text-xs mt-1 ${
          isUser ? 'text-teal-100' : 'text-gray-500'
        }`}>
          {new Date(message.timestamp).toLocaleTimeString('tr-TR', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </p>
      </div>
    </div>
  );
}