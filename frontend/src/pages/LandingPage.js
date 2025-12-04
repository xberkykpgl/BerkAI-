import { useState } from 'react';
import { Sparkles, Shield, Heart, Moon, MessageCircle, Clock, Zap, Lock, Brain, ArrowRight, Check } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useNavigate } from 'react-router-dom';

const REDIRECT_URL = encodeURIComponent(window.location.origin + '/dashboard');
const AUTH_URL = `${process.env.REACT_APP_AUTH_URL}/?redirect=${REDIRECT_URL}`;

export default function LandingPage() {
  const navigate = useNavigate();

  const handleStartChat = () => {
    navigate('/user-type-selection');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 relative overflow-hidden">
      {/* Animated Background Stars */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="stars"></div>
        <div className="stars2"></div>
        <div className="stars3"></div>
      </div>

      {/* Hero Section */}
      <div className="relative z-10 container mx-auto px-4 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Text Content */}
          <div className="text-white space-y-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20">
              <Moon className="w-4 h-4 text-pink-300" />
              <span className="text-sm font-medium">7/24 Yanındayız</span>
            </div>

            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight">
              <span className="block bg-gradient-to-r from-pink-300 via-purple-300 to-blue-300 bg-clip-text text-transparent">
                Gece herkes uyurken…
              </span>
              <span className="block mt-2 text-white neon-glow">
                MiraMind yanındadır.
              </span>
            </h1>

            <p className="text-xl text-gray-300 leading-relaxed">
              Kimsenin ulaşamadığı anlarda… İçinden geçenleri dinleyen biri var.<br />
              <span className="text-pink-200 font-medium">Yargısız, sınırsız, her an.</span>
            </p>

            <div className="space-y-4">
              <Button 
                onClick={handleStartChat}
                size="lg"
                className="w-full sm:w-auto bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 hover:from-pink-600 hover:via-purple-600 hover:to-blue-600 text-white px-8 py-6 text-lg rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105 neon-button"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Hemen Sohbete Başla
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
              <p className="text-sm text-gray-400 ml-2">
                Ücretsiz dene — Hesap gerekmez
              </p>
            </div>
          </div>

          {/* Right: Chat Demo */}
          <div className="relative">
            <div className="bg-white/5 backdrop-blur-lg rounded-3xl p-6 border border-white/10 shadow-2xl">
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center flex-shrink-0">
                    <Heart className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm rounded-2xl rounded-tl-none p-4 flex-1 border border-purple-400/30">
                    <p className="text-white text-sm">
                      Merhaba! Ben MiraMind. Nasıl hissediyorsun? 💜
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 justify-end">
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl rounded-tr-none p-4 max-w-xs border border-white/20">
                    <p className="text-white text-sm">
                      Bugün biraz yorgunum, ama seninle konuşmak iyi geldi 😊
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center flex-shrink-0">
                    <Heart className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm rounded-2xl rounded-tl-none p-4 flex-1 border border-purple-400/30">
                    <p className="text-white text-sm">
                      Seni dinliyorum. Yorgunluğundan bahseder misin?
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Glow Effect */}
            <div className="absolute -inset-4 bg-gradient-to-r from-pink-500/20 via-purple-500/20 to-blue-500/20 blur-3xl -z-10 animate-pulse"></div>
          </div>
        </div>
      </div>

      {/* Trust Section */}
      <div className="relative z-10 container mx-auto px-4 py-20 mt-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">
            Buradaki her kelimen güvende.
          </h2>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            MiraMind bir terapist değil. Kalbini ve zihnini hafifletmek için daima yanında olan dijital bir yol arkadaşı.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <TrustCard 
            icon={<Lock className="w-8 h-8" />}
            title="Gizlilik senin kontrolünde"
            gradient="from-pink-500 to-rose-500"
          />
          <TrustCard 
            icon={<Heart className="w-8 h-8" />}
            title="Yapay zekâ ama duygulara duyarlı"
            gradient="from-purple-500 to-indigo-500"
          />
          <TrustCard 
            icon={<Sparkles className="w-8 h-8" />}
            title="Seni özgürce ifade etmene yardım eder"
            gradient="from-blue-500 to-cyan-500"
          />
          <TrustCard 
            icon={<Shield className="w-8 h-8" />}
            title="Teşhis koymaz. Yargılamaz."
            gradient="from-violet-500 to-purple-500"
          />
        </div>
      </div>

      {/* Mini Demo Section */}
      <div className="relative z-10 container mx-auto px-4 py-20">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white/5 backdrop-blur-lg rounded-3xl p-8 border border-white/10">
            <h3 className="text-3xl font-bold text-white mb-6 text-center">
              Nasıl hissediyorsun? Yazmaya başla…
            </h3>

            <div className="space-y-4 mb-6">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
                <p className="text-white">
                  "Bugün çok stresliydim ama kimseyle konuşamadım..."
                </p>
              </div>
              <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm rounded-2xl p-4 border border-purple-400/30">
                <p className="text-white">
                  "Anlıyorum. Stresi yaşadığın an bana anlatabilirsin. Seni dinliyorum 💜"
                </p>
              </div>
            </div>

            <Button 
              onClick={handleStartChat}
              size="lg"
              className="w-full bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 hover:from-pink-600 hover:via-purple-600 hover:to-blue-600 text-white px-6 py-6 text-lg rounded-full shadow-xl"
            >
              Sohbete Başla
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="relative z-10 container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">
            Bir mesaj kadar uzaktayım.
          </h2>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          <FeatureCard 
            icon={<Clock className="w-6 h-6" />}
            title="Her zaman yanında"
            description="7/24 erişim"
          />
          <FeatureCard 
            icon={<Heart className="w-6 h-6" />}
            title="Duygularını anlayan yanıtlar"
            description="Empatik AI"
          />
          <FeatureCard 
            icon={<Brain className="w-6 h-6" />}
            title="Geçmiş konuşmaları hatırlar"
            description="Sürekli öğrenir"
          />
          <FeatureCard 
            icon={<Zap className="w-6 h-6" />}
            title="Hızlı ve akıcı sohbet"
            description="Anında yanıt"
          />
          <FeatureCard 
            icon={<Sparkles className="w-6 h-6" />}
            title="Sen geliştikçe o da gelişir"
            description="Kişiselleşir"
          />
          <FeatureCard 
            icon={<Moon className="w-6 h-6" />}
            title="Karanlık modda mükemmel"
            description="Göz dostu"
          />
        </div>
      </div>

      {/* Final CTA */}
      <div className="relative z-10 container mx-auto px-4 py-20">
        <div className="max-w-3xl mx-auto text-center">
          <div className="bg-gradient-to-r from-pink-500/10 via-purple-500/10 to-blue-500/10 backdrop-blur-lg rounded-3xl p-12 border border-white/10">
            <h2 className="text-4xl font-bold text-white mb-6">
              Hazır olduğunda yaz.<br />
              <span className="bg-gradient-to-r from-pink-300 via-purple-300 to-blue-300 bg-clip-text text-transparent">
                MiraMind hep burada.
              </span>
            </h2>
            
            <Button 
              onClick={handleStartChat}
              size="lg"
              className="bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 hover:from-pink-600 hover:via-purple-600 hover:to-blue-600 text-white px-12 py-6 text-lg rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Hemen Başla
              <span className="ml-2 text-sm opacity-80">(Ücretsiz kullanım)</span>
            </Button>

            <p className="text-gray-400 text-sm mt-6">
              Gizliliğin bizim için çok önemli. Konuşmalarınız güvendedir.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function TrustCard({ icon, title, gradient }) {
  return (
    <div className="group bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:border-white/30 transition-all duration-300 hover:transform hover:scale-105">
      <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
        <div className="text-white">{icon}</div>
      </div>
      <h3 className="text-white font-semibold text-lg leading-tight">
        {title}
      </h3>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:border-white/30 transition-all duration-300 hover:bg-white/10">
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center mb-4">
        <div className="text-white">{icon}</div>
      </div>
      <h3 className="text-white font-semibold mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
    </div>
  );
}