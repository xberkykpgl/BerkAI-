// Reliable Speech Recognition Helper for BerkAI
// Handles all edge cases and provides fallbacks

export class VoiceRecognition {
  constructor(onResult, onError, onStart, onEnd, options = {}) {
    this.onResult = onResult;
    this.onError = onError;
    this.onStart = onStart;
    this.onEnd = onEnd;
    this.recognition = null;
    this.isRecording = false;
    this.finalTranscript = '';
    this.shouldContinue = false;
    this.restartTimeout = null;
    this.networkErrorCount = 0;
    this.maxNetworkErrors = 3;
    
    // Options: continuous mode (default false for better network stability)
    this.continuous = options.continuous !== undefined ? options.continuous : false;
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

    this.shouldContinue = true;
    this.networkErrorCount = 0;
    this._startRecognition();
    return true;
  }

  _startRecognition() {
    if (!this.shouldContinue) return;

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      
      // Configure - use non-continuous for better network stability
      this.recognition.lang = 'tr-TR';
      this.recognition.continuous = this.continuous;
      this.recognition.interimResults = true;
      this.recognition.maxAlternatives = 1;

      // Event handlers
      this.recognition.onstart = () => {
        this.isRecording = true;
        if (this.onStart && this.finalTranscript === '') {
          this.onStart();
        }
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
        } else if (interimTranscript && this.onResult) {
          // Show interim results
          this.onResult(this.finalTranscript + interimTranscript, true);
        }
      };

      this.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        
        // Don't show error for "no-speech" or "aborted"
        if (event.error === 'no-speech') {
          // Auto-restart after no speech
          if (this.shouldContinue && !this.continuous) {
            this._scheduleRestart(500);
          }
          return;
        }
        
        if (event.error === 'aborted') {
          return;
        }
        
        // Handle network errors with retry limit
        if (event.error === 'network') {
          this.networkErrorCount++;
          
          if (this.networkErrorCount >= this.maxNetworkErrors) {
            this.isRecording = false;
            this.shouldContinue = false;
            if (this.onError) {
              this.onError('Bağlantı sorunu devam ediyor. Lütfen metin girişi kullanın.');
            }
            return;
          }
          
          // Retry with exponential backoff
          if (this.shouldContinue && !this.continuous) {
            this._scheduleRestart(1000 * this.networkErrorCount);
          }
          return;
        }
        
        this.isRecording = false;
        
        let errorMessage = '';
        switch(event.error) {
          case 'not-allowed':
            errorMessage = 'Mikrofon izni gerekli. Tarayıcı ayarlarından izin verin.';
            this.shouldContinue = false;
            break;
          case 'service-not-allowed':
            errorMessage = 'Ses tanıma servisi kullanılamıyor. Lütfen metin yazın.';
            this.shouldContinue = false;
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
        
        // Auto-restart if should continue (simulates continuous mode)
        if (this.shouldContinue && !this.continuous) {
          this._scheduleRestart(300);
        } else if (this.onEnd) {
          this.onEnd(this.finalTranscript);
        }
      };

      // Start recording
      this.recognition.start();
      
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      this.isRecording = false;
      this.shouldContinue = false;
      if (this.onError) {
        this.onError('Ses tanıma başlatılamadı. Lütfen metin yazın.');
      }
    }
  }

  _scheduleRestart(delay) {
    if (this.restartTimeout) {
      clearTimeout(this.restartTimeout);
    }
    
    this.restartTimeout = setTimeout(() => {
      if (this.shouldContinue) {
        this._startRecognition();
      }
    }, delay);
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
