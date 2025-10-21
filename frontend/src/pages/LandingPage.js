import { Brain, Video, MessageCircle, Shield, Sparkles, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';

const REDIRECT_URL = encodeURIComponent(window.location.origin + '/dashboard');
const AUTH_URL = `https://auth.emergentagent.com/?redirect=${REDIRECT_URL}`;

export default function LandingPage() {
  const handleLogin = () => {
    window.location.href = AUTH_URL;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-indigo-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex items-center justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-teal-500 to-blue-600 rounded-2xl shadow-lg">
              <Brain className="w-12 h-12 text-white" />
            </div>
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 bg-gradient-to-r from-teal-600 via-blue-600 to-indigo-600 bg-clip-text text-transparent">
            BerkAI
          </h1>
          
          <p className="text-lg sm:text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Yapay zeka destekli psikolojik destek platformu. Görüntülü konuşma ile duygusal analiz ve kişiselleştirilmiş terapi deneyimi.
          </p>
          
          <Button 
            onClick={handleLogin}
            data-testid="login-button"
            size="lg"
            className="bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700 text-white px-8 py-6 text-lg rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
          >
            <Sparkles className="w-5 h-5 mr-2" />
            Google ile Giriş Yap
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mt-24 max-w-7xl mx-auto">
          <FeatureCard 
            icon={<Video className="w-8 h-8" />}
            title="Görüntülü Terapi"
            description="Gerçek zamanlı video görüşmesi ile psikolojik destek"
            gradient="from-teal-500 to-emerald-500"
          />
          
          <FeatureCard 
            icon={<Brain className="w-8 h-8" />}
            title="AI Analizi"
            description="Yüz ifadesi, ses tonu ve vücut dili analizi"
            gradient="from-blue-500 to-cyan-500"
          />
          
          <FeatureCard 
            icon={<MessageCircle className="w-8 h-8" />}
            title="Empatik Sohbet"
            description="Hem dost hem psikolog gibi anlayışlı yaklaşım"
            gradient="from-indigo-500 to-purple-500"
          />
          
          <FeatureCard 
            icon={<Shield className="w-8 h-8" />}
            title="Gizlilik"
            description="Tüm görüşmeleriniz güvenli ve özel"
            gradient="from-purple-500 to-pink-500"
          />
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-20 py-8 border-t border-gray-200">
        <div className="container mx-auto px-4 text-center text-gray-600">
          <p className="text-sm">© 2025 BerkAI - Psikolojik Destek Platformu</p>
          <p className="text-xs mt-2 text-gray-500">Bu platform tıbbi tavsiye yerine geçmez. Acil durumlarda lütfen profesyonel yardım alın.</p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description, gradient }) {
  return (
    <div className="p-6 rounded-2xl bg-white/80 backdrop-blur-sm border border-white/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
      <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center text-white mb-4 shadow-md`}>
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2 text-gray-800">{title}</h3>
      <p className="text-gray-600 text-sm leading-relaxed">{description}</p>
    </div>
  );
}