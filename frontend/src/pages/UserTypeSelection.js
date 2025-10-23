import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, UserCircle, Stethoscope, Hospital } from 'lucide-react';
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
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="max-w-5xl w-full">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-teal-500 to-blue-600 rounded-2xl shadow-lg">
              <Brain className="w-12 h-12 text-white" />
            </div>
          </div>
          
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-teal-600 via-blue-600 to-indigo-600 bg-clip-text text-transparent">
            BerkAI Professional
          </h1>
          
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Profesyonel psikolojik destek platformu. Lütfen kullanıcı tipinizi seçin.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <UserTypeCard
            icon={<UserCircle className="w-12 h-12" />}
            title="Hasta"
            description="Psikolojik destek almak istiyorum"
            gradient="from-blue-500 to-cyan-500"
            onClick={() => handleLogin('patient')}
            dataTestId="patient-card"
          />

          <UserTypeCard
            icon={<Stethoscope className="w-12 h-12" />}
            title="Psikolog"
            description="Hastalarımı takip etmek istiyorum"
            gradient="from-purple-500 to-pink-500"
            onClick={() => handleLogin('doctor')}
            dataTestId="doctor-card"
          />

          <UserTypeCard
            icon={<Hospital className="w-12 h-12" />}
            title="Psikiyatrist"
            description="Hastalarımı yönetmek istiyorum"
            gradient="from-emerald-500 to-teal-500"
            onClick={() => handleLogin('psychiatrist')}
            dataTestId="psychiatrist-card"
          />
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            Zaten hesabınız var mı?{' '}
            <button onClick={() => navigate('/login')} className="text-blue-600 hover:underline">
              Giriş yapın
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

function UserTypeCard({ icon, title, description, gradient, onClick, dataTestId }) {
  return (
    <Card 
      className="p-8 cursor-pointer hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 bg-white/80 backdrop-blur-sm border-2 border-transparent hover:border-blue-200"
      onClick={onClick}
      data-testid={dataTestId}
    >
      <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${gradient} flex items-center justify-center text-white mb-6 mx-auto shadow-lg`}>
        {icon}
      </div>
      <h3 className="text-2xl font-bold mb-3 text-gray-900 text-center">{title}</h3>
      <p className="text-gray-600 text-center leading-relaxed">{description}</p>
      <div className="mt-6">
        <Button className="w-full bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700">
          Seç ve Devam Et
        </Button>
      </div>
    </Card>
  );
}
