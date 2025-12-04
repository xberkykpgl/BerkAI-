import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, UserCircle, Stethoscope, Hospital, Sparkles, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';

const REDIRECT_URL = encodeURIComponent(window.location.origin + '/auth-callback');
const AUTH_URL = `${process.env.REACT_APP_AUTH_URL}/?redirect=${REDIRECT_URL}`;

export default function UserTypeSelection() {
  const navigate = useNavigate();
  const [selectedType, setSelectedType] = useState(null);

  const handleLogin = (userType) => {
    // Store user type in session storage
    sessionStorage.setItem('pending_user_type', userType);
    // Redirect to auth
    window.location.href = AUTH_URL;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 relative overflow-hidden">
      {/* Animated Background Stars */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="stars"></div>
        <div className="stars2"></div>
        <div className="stars3"></div>
      </div>

      {/* Back Button */}
      <div className="absolute top-6 left-6 z-20">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-white/80 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="text-sm">Ana Sayfaya Dön</span>
        </button>
      </div>

      <div className="relative z-10 flex items-center justify-center min-h-screen p-4">
        <div className="max-w-6xl w-full">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20 mb-8">
              <Brain className="w-5 h-5 text-pink-300" />
              <span className="text-sm font-medium text-white">BerkAI Professional</span>
            </div>
            
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6">
              <span className="block bg-gradient-to-r from-pink-300 via-purple-300 to-blue-300 bg-clip-text text-transparent neon-glow">
                Kimsin?
              </span>
            </h1>
            
            <p className="text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
              Sana en uygun deneyimi sunabilmemiz için<br />
              <span className="text-pink-200 font-medium">kullanıcı tipini seç</span>
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <UserTypeCard
              icon={<UserCircle className="w-12 h-12" />}
              title="Danışan"
              description="Psikolojik destek almak istiyorum"
              gradient="from-blue-500 to-cyan-500"
              glowColor="blue"
              onClick={() => handleLogin('patient')}
              dataTestId="patient-card"
            />

            <UserTypeCard
              icon={<Stethoscope className="w-12 h-12" />}
              title="Psikolog"
              description="Danışanlarımı takip etmek istiyorum"
              gradient="from-purple-500 to-pink-500"
              glowColor="purple"
              onClick={() => handleLogin('doctor')}
              dataTestId="doctor-card"
            />

            <UserTypeCard
              icon={<Hospital className="w-12 h-12" />}
              title="Psikiyatrist"
              description="Danışanlarımı yönetmek istiyorum"
              gradient="from-emerald-500 to-teal-500"
              glowColor="emerald"
              onClick={() => handleLogin('psychiatrist')}
              dataTestId="psychiatrist-card"
            />
          </div>

          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-6 py-3 bg-white/5 backdrop-blur-sm rounded-full border border-white/10">
              <Sparkles className="w-4 h-4 text-yellow-300" />
              <p className="text-sm text-gray-300">
                Ücretsiz denemeye başla — Kredi kartı gerekmez
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function UserTypeCard({ icon, title, description, gradient, glowColor, onClick, dataTestId }) {
  const glowColors = {
    blue: 'hover:shadow-[0_0_40px_rgba(59,130,246,0.5)]',
    purple: 'hover:shadow-[0_0_40px_rgba(168,85,247,0.5)]',
    emerald: 'hover:shadow-[0_0_40px_rgba(16,185,129,0.5)]'
  };

  return (
    <div 
      className={`group relative cursor-pointer transition-all duration-300 hover:-translate-y-2 ${glowColors[glowColor]}`}
      onClick={onClick}
      data-testid={dataTestId}
    >
      {/* Glow Effect */}
      <div className={`absolute -inset-1 bg-gradient-to-r ${gradient} rounded-3xl opacity-0 group-hover:opacity-30 blur-xl transition-opacity duration-300`}></div>
      
      {/* Card Content */}
      <div className="relative bg-white/5 backdrop-blur-lg rounded-3xl p-8 border border-white/10 group-hover:border-white/30 transition-all duration-300">
        <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${gradient} flex items-center justify-center text-white mb-6 mx-auto shadow-lg group-hover:scale-110 transition-transform duration-300`}>
          {icon}
        </div>
        
        <h3 className="text-2xl font-bold mb-3 text-white text-center group-hover:text-pink-200 transition-colors">
          {title}
        </h3>
        
        <p className="text-gray-300 text-center leading-relaxed mb-6">
          {description}
        </p>
        
        <Button className={`w-full bg-gradient-to-r ${gradient} hover:opacity-90 text-white border-0 shadow-lg group-hover:shadow-xl transition-all duration-300`}>
          <Sparkles className="w-4 h-4 mr-2" />
          Seç ve Devam Et
        </Button>
      </div>
    </div>
  );
}
