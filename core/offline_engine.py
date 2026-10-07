import asyncio
import threading
import pyttsx3
import speech_recognition as sr
from faster_whisper import WhisperModel
import time

class OfflineEngine:
    def __init__(self, ui_logger=None):
        self.ui_logger = ui_logger
        self.running = False
        self._stt_thread = None
        self._tts_engine = pyttsx3.init()
        # Set some default voice properties
        self._tts_engine.setProperty('rate', 170)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Load the whisper model (using tiny for speed, can be configured)
        self.log("Loading faster-whisper model (tiny)...")
        # You might want to use "cuda" if available, else "cpu"
        self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        self.log("Offline engine ready.")

    def log(self, message: str):
        if self.ui_logger:
            self.ui_logger(f"[Offline] {message}", "sys")
        else:
            print(f"[Offline] {message}")

    def start(self):
        self.running = True
        self._stt_thread = threading.Thread(target=self._stt_loop, daemon=True)
        self._stt_thread.start()

    def stop(self):
        self.running = False

    def say(self, text: str):
        self.log(f"JARVIS: {text}")
        def tts_task():
            self._tts_engine.say(text)
            self._tts_engine.runAndWait()
        threading.Thread(target=tts_task, daemon=True).start()

    def _stt_loop(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            self.log("Listening for offline voice commands...")
            
        while self.running:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                
                # We have audio, transcribe it
                self.log("Transcribing...")
                
                # Write audio to a temporary wav file for faster-whisper
                temp_wav = "temp_offline.wav"
                with open(temp_wav, "wb") as f:
                    f.write(audio.get_wav_data())
                
                segments, info = self.whisper_model.transcribe(temp_wav, beam_size=5)
                transcription = " ".join([segment.text for segment in segments])
                
                if transcription.strip():
                    self.log(f"User: {transcription.strip()}")
                    self.process_command(transcription.strip())
                    
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                self.log(f"STT Error: {e}")
                time.sleep(1)

    def process_command(self, command: str):
        # Basic offline command processing
        cmd = command.lower()
        if "hello" in cmd or "hi" in cmd:
            self.say("Hello sir. Offline systems are fully functional.")
        elif "time" in cmd:
            import datetime
            now = datetime.datetime.now().strftime("%H:%M")
            self.say(f"The time is {now}")
        elif "stop" in cmd or "quit" in cmd:
            self.say("Shutting down offline systems.")
            # self.stop()
        else:
            self.say("I heard you, but complex processing is not available offline.")
