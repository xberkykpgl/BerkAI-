import { useState, useEffect } from 'react';
import axios from 'axios';
import { Settings, Save, Mic, Brain, Video } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminSettings({ onUpdate }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/settings`, settings);
      toast.success('Ayarlar kaydedildi!');
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Ayarlar kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-white text-center py-8">Yükleniyor...</div>;
  }

  return (
    <div className="space-y-6">
      <Card className="p-6 bg-white/10 backdrop-blur-lg border-white/20">
        <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
          <Brain className="w-6 h-6" />
          Chat AI Ayarları
        </h3>
        
        <div className="space-y-4">
          <div>
            <Label className="text-gray-200">Chat Model</Label>
            <Select
              value={settings?.chat_model}
              onValueChange={(value) => setSettings({...settings, chat_model: value})}
            >
              <SelectTrigger className="bg-white/10 border-white/20 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-white/20">
                <SelectItem value="gpt-5">GPT-5</SelectItem>
                <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                <SelectItem value="claude-4-sonnet">Claude 4 Sonnet</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-gray-200">Provider</Label>
            <Select
              value={settings?.chat_provider}
              onValueChange={(value) => setSettings({...settings, chat_provider: value})}
            >
              <SelectTrigger className="bg-white/10 border-white/20 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-white/20">
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-gray-200">System Prompt</Label>
            <Textarea
              value={settings?.system_prompt}
              onChange={(e) => setSettings({...settings, system_prompt: e.target.value})}
              rows={6}
              className="bg-white/10 border-white/20 text-white"
            />
          </div>

          <div>
            <Label className="text-gray-200">Maksimum Mesaj Uzunluğu</Label>
            <Input
              type="number"
              value={settings?.max_message_length}
              onChange={(e) => setSettings({...settings, max_message_length: parseInt(e.target.value)})}
              className="bg-white/10 border-white/20 text-white"
            />
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-white/10 backdrop-blur-lg border-white/20">
        <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
          <Video className="w-6 h-6" />
          Video Analiz Ayarları
        </h3>
        
        <div className="space-y-4">
          <div>
            <Label className="text-gray-200">Vision Model</Label>
            <Select
              value={settings?.vision_model}
              onValueChange={(value) => setSettings({...settings, vision_model: value})}
            >
              <SelectTrigger className="bg-white/10 border-white/20 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-white/20">
                <SelectItem value="gemini-2.5-pro">Gemini 2.5 Pro</SelectItem>
                <SelectItem value="gpt-5-vision">GPT-5 Vision</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <Label className="text-gray-200">Video Analizi Aktif</Label>
            <Switch
              checked={settings?.enable_video_analysis}
              onCheckedChange={(checked) => setSettings({...settings, enable_video_analysis: checked})}
            />
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-white/10 backdrop-blur-lg border-white/20">
        <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
          <Mic className="w-6 h-6" />
          TTS Ses Ayarları
        </h3>
        
        <div className="space-y-4">
          <div>
            <Label className="text-gray-200">TTS Model</Label>
            <Select
              value={settings?.tts_model}
              onValueChange={(value) => setSettings({...settings, tts_model: value})}
            >
              <SelectTrigger className="bg-white/10 border-white/20 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-white/20">
                <SelectItem value="tts-1">TTS-1 (Hızlı)</SelectItem>
                <SelectItem value="tts-1-hd">TTS-1-HD (Yüksek Kalite)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-gray-200">Ses</Label>
            <Select
              value={settings?.tts_voice}
              onValueChange={(value) => setSettings({...settings, tts_voice: value})}
            >
              <SelectTrigger className="bg-white/10 border-white/20 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-white/20">
                <SelectItem value="alloy">Alloy</SelectItem>
                <SelectItem value="echo">Echo</SelectItem>
                <SelectItem value="fable">Fable</SelectItem>
                <SelectItem value="nova">Nova (Önerilen)</SelectItem>
                <SelectItem value="onyx">Onyx</SelectItem>
                <SelectItem value="shimmer">Shimmer</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <Label className="text-gray-200">TTS Aktif</Label>
            <Switch
              checked={settings?.enable_tts}
              onCheckedChange={(checked) => setSettings({...settings, enable_tts: checked})}
            />
          </div>
        </div>
      </Card>

      <Button
        onClick={handleSave}
        disabled={saving}
        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
        data-testid="save-settings-button"
      >
        <Save className="w-4 h-4 mr-2" />
        {saving ? 'Kaydediliyor...' : 'Ayarları Kaydet'}
      </Button>
    </div>
  );
}
