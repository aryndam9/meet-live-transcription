import soundcard as sc
import soundfile as sf
import numpy as np
from whisper_online import FasterWhisperASR, OnlineASRProcessor
from googletrans import Translator
import threading
import queue
import pyaudio
import wave
import tkinter as tk
from tkinter import ttk

class RealtimeMeetingTranslator:
    def __init__(self):
        self.source_language = "es"  # Spanish
        self.target_language = "en"  # English
        self.asr = FasterWhisperASR(self.source_language, "large-v2")
        self.online_asr = OnlineASRProcessor(self.asr)
        self.translator = Translator()
        
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        
        self.is_recording = False
        self.speakers = self.list_speakers()
        
        self.setup_gui()

    def list_speakers(self):
        return sc.all_speakers()

    def select_speaker(self):
        speaker_window = tk.Toplevel(self.root)
        speaker_window.title("Select Speaker")
        
        for i, speaker in enumerate(self.speakers):
            btn = ttk.Button(speaker_window, text=speaker.name, 
                             command=lambda s=speaker: self.set_speaker(s, speaker_window))
            btn.pack(pady=5)

    def set_speaker(self, speaker, window):
        self.selected_speaker = speaker
        self.speaker_label.config(text=f"Selected: {speaker.name}")
        window.destroy()

    def start_recording(self):
        if not hasattr(self, 'selected_speaker'):
            print("Please select a speaker first.")
            return
        
        self.is_recording = True
        threading.Thread(target=self.record_audio, daemon=True).start()
        threading.Thread(target=self.process_audio, daemon=True).start()

    def stop_recording(self):
        self.is_recording = False

    def record_audio(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        while self.is_recording:
            data = stream.read(CHUNK)
            self.audio_queue.put(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

    def process_audio(self):
        while self.is_recording:
            if not self.audio_queue.empty():
                audio_chunk = self.audio_queue.get()
                self.online_asr.insert_audio_chunk(audio_chunk)
                output = self.online_asr.process_iter()
                if output:
                    translated = self.translator.translate(output, src=self.source_language, dest=self.target_language).text
                    self.text_queue.put(translated)

    def update_transcript(self):
        while not self.text_queue.empty():
            text = self.text_queue.get()
            self.transcript.insert(tk.END, text + "\n")
            self.transcript.see(tk.END)
        self.root.after(100, self.update_transcript)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Realtime Meeting Translator")

        self.speaker_label = ttk.Label(self.root, text="No speaker selected")
        self.speaker_label.pack(pady=10)

        ttk.Button(self.root, text="Select Speaker", command=self.select_speaker).pack(pady=5)
        ttk.Button(self.root, text="Start Recording", command=self.start_recording).pack(pady=5)
        ttk.Button(self.root, text="Stop Recording", command=self.stop_recording).pack(pady=5)

        self.transcript = tk.Text(self.root, wrap=tk.WORD, width=50, height=20)
        self.transcript.pack(pady=10)

        self.root.after(100, self.update_transcript)
        self.root.mainloop()

if __name__ == "__main__":
    app = RealtimeMeetingTranslator()