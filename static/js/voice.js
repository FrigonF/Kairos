/**
 * KAIROS: Tactical AI Voice Assistant Engine
 * Integrates Web Speech Recognition, Siri Waveform Visualizer, and Backend Tool Execution.
 */

class KairosVoiceModule {
    constructor(appInstance) {
        this.app = appInstance;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.waveformCanvas = null;
        this.waveformCtx = null;
        this.animFrameId = null;
    }

    init() {
        this.initRecognition();
        this.initWaveform();
        this.bindEvents();
    }

    initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';

            this.recognition.onstart = () => {
                if (this.synthesis && this.synthesis.speaking) {
                    this.synthesis.cancel();
                }
                this.setListeningState(true);
                this.updateTranscript("Listening for tactical command...", true);
            };

            this.recognition.onresult = (event) => {
                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                if (finalTranscript) {
                    this.updateTranscript(`"${finalTranscript}"`, false);
                    this.sendVoiceQuery(finalTranscript);
                } else if (interimTranscript) {
                    this.updateTranscript(`"${interimTranscript}"`, true);
                }
            };

            this.recognition.onerror = (event) => {
                console.warn("Speech recognition error:", event.error);
                this.setListeningState(false);
                if (event.error === 'not-allowed' || event.error === 'service-not-allowed' || event.error === 'audio-capture') {
                    this.updateTranscript("Microphone access blocked. Click Mic for text input.", false);
                    this.promptTextInput();
                } else {
                    this.updateTranscript("Awaiting voice command...", false);
                }
            };

            this.recognition.onend = () => {
                this.setListeningState(false);
            };
        } else {
            console.warn("Web Speech API not supported in this browser. Fallback input available.");
        }
    }

    initWaveform() {
        this.waveformCanvas = document.getElementById('voice-waveform');
        if (this.waveformCanvas) {
            this.waveformCtx = this.waveformCanvas.getContext('2d');
            this.drawIdleWaveform();
        }
    }

    drawIdleWaveform() {
        if (!this.waveformCtx) return;
        const ctx = this.waveformCtx;
        const width = this.waveformCanvas.width;
        const height = this.waveformCanvas.height;

        ctx.clearRect(0, 0, width, height);

        // Apple Siri gradient wave
        const grad = ctx.createLinearGradient(0, 0, width, 0);
        grad.addColorStop(0, '#0071e3');
        grad.addColorStop(0.5, '#af52de');
        grad.addColorStop(1, '#ff3b30');

        ctx.strokeStyle = grad;
        ctx.lineWidth = 2.2;
        ctx.lineCap = 'round';

        ctx.beginPath();
        const steps = 30;
        const sliceWidth = width / steps;
        let x = 0;
        const amp = this.isListening ? 10 : 3.5;
        const freq = this.isListening ? 0.007 : 0.0025;

        for (let i = 0; i <= steps; i++) {
            const v = Math.sin(i * 0.4 + Date.now() * freq) * Math.cos(i * 0.15) * amp;
            const y = height / 2 + v;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
            x += sliceWidth;
        }
        ctx.stroke();

        this.animFrameId = requestAnimationFrame(() => this.drawIdleWaveform());
    }

    bindEvents() {
        const micBtn = document.getElementById('btn-voice-mic');
        if (micBtn) {
            micBtn.addEventListener('click', () => this.toggleListening());
        }

        // Bind both .voice-chip and .voice-command-pill query chips
        const chips = document.querySelectorAll('.voice-chip, .voice-command-pill');
        chips.forEach(chip => {
            chip.addEventListener('click', (e) => {
                e.stopPropagation();
                const query = chip.dataset.query || chip.textContent.trim();
                this.updateTranscript(`"${query}"`, false);
                this.sendVoiceQuery(query);
            });
        });
    }

    toggleListening() {
        // Intercept: If AI is currently speaking, stop speech synthesis immediately and start listening
        if (this.synthesis && this.synthesis.speaking) {
            this.synthesis.cancel();
        }

        if (!this.recognition) {
            this.promptTextInput();
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            try {
                this.recognition.start();
            } catch (e) {
                console.warn("Speech recognition start failed, using input dialog fallback:", e);
                this.promptTextInput();
            }
        }
    }

    promptTextInput() {
        const query = prompt("Speak or type KAIROS command (e.g. 'Who is the culprit?', '24h forecast'):");
        if (query && query.trim()) {
            this.updateTranscript(`"${query.trim()}"`, false);
            this.sendVoiceQuery(query.trim());
        }
    }

    setListeningState(listening) {
        this.isListening = listening;
        const micBtn = document.getElementById('btn-voice-mic');
        if (micBtn) {
            micBtn.classList.toggle('listening', listening);
        }
    }

    updateTranscript(text, isInterim = false) {
        const transcriptEl = document.getElementById('voice-transcript-text');
        if (transcriptEl) {
            transcriptEl.textContent = text;
            transcriptEl.style.opacity = isInterim ? '0.7' : '1.0';
        }
    }

    async sendVoiceQuery(text) {
        this.updateTranscript(`Processing: "${text}"...`, true);

        try {
            const res = await fetch('/api/voice_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: text })
            });

            const data = await res.json();
            this.handleVoiceResponse(data);
        } catch (e) {
            console.error("Voice dispatch error:", e);
            this.updateTranscript("Error communicating with KAIROS backend.", false);
        }
    }

    handleVoiceResponse(resp) {
        const speechText = resp.speech_response || "Command executed.";
        this.updateTranscript(`KAIROS: ${speechText}`, false);

        // Speak back via Web Speech Synthesis (TTS)
        this.speak(speechText);

        // Execute returned UI action
        if (resp.ui_action) {
            this.app.executeTacticalAction(resp.ui_action, resp.data);
        }
    }

    speak(text) {
        if (!this.synthesis) return;
        this.synthesis.cancel(); // Stop any pending speech

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.05;
        utterance.pitch = 1.0;

        // Choose English natural voice if available
        const voices = this.synthesis.getVoices();
        const preferredVoice = voices.find(v => v.lang.includes('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('David')));
        if (preferredVoice) utterance.voice = preferredVoice;

        this.synthesis.speak(utterance);
    }
}

window.KairosVoice = KairosVoiceModule;
