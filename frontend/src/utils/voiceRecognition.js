// Reliable Speech Recognition Helper for BerkAI
// Handles all edge cases and provides fallbacks

export class VoiceRecognition {
  constructor(onResult, onError, onStart, onEnd) {
    this.onResult = onResult;
    this.onError = onError;
    this.onStart = onStart;
    this.onEnd = onEnd;
    this.recognition = null;
    this.isRecording = false;
    this.finalTranscript = '';
  }

  isSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  start() {
    if (!this.isSupported()) {
      this.onError('Tarayıcınız ses tanımayı desteklemiyor. Lütfen Chrome veya Edge kullanın.');
      return false;
    }

    if (this.isRecording) {
      return false;
    }

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      
      // Configure
      this.recognition.lang = 'tr-TR';
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.maxAlternatives = 1;

      // Event handlers
      this.recognition.onstart = () => {
        this.isRecording = true;
        this.finalTranscript = '';
        if (this.onStart) this.onStart();
      };

      this.recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          this.finalTranscript += finalTranscript;
          if (this.onResult) {
            this.onResult(this.finalTranscript, false);
          }
        }
      };

      this.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        
        // Don't show error for "no-speech" during continuous recording
        if (event.error === 'no-speech') {
          // Just continue listening
          return;
        }
        
        // Don't show error for "aborted" - user stopped it
        if (event.error === 'aborted') {
          return;
        }
        
        this.isRecording = false;
        
        let errorMessage = '';
        switch(event.error) {
          case 'network':
            errorMessage = 'İnternet bağlantısı gerekli. Lütfen bağlantınızı kontrol edin.';
            break;
          case 'not-allowed':
            errorMessage = 'Mikrofon izni gerekli. Tarayıcı ayarlarından izin verin.';
            break;
          case 'service-not-allowed':
            errorMessage = 'Ses tanıma servisi kullanılamıyor. Lütfen metin yazın.';
            break;
          default:
            errorMessage = `Ses tanıma hatası: ${event.error}`;
        }
        
        if (this.onError) {
          this.onError(errorMessage);
        }
      };

      this.recognition.onend = () => {
        this.isRecording = false;
        if (this.onEnd) {
          this.onEnd(this.finalTranscript);
        }
      };

      // Start recording
      this.recognition.start();
      return true;
      
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      if (this.onError) {
        this.onError('Ses tanıma başlatılamadı. Lütfen metin yazın.');
      }
      return false;
    }
  }

  stop() {
    if (this.recognition && this.isRecording) {
      try {
        this.recognition.stop();
      } catch (error) {
        console.error('Error stopping recognition:', error);
      }
    }
    this.isRecording = false;
  }

  isActive() {
    return this.isRecording;
  }
}
