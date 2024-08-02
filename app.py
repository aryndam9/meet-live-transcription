import sounddevice as sd
import numpy as np
import websocket
import json
from transformers import MarianMTModel, MarianTokenizer
import tkinter as tk
from threading import Thread
import queue

class RealtimeTranslator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Realtime Meeting Translator")
        
        self.text_area = tk.Text(self.root, height=20, width=50)
        self.text_area.pack(pady=10)
        
        self.start_button = tk.Button(self.root, text="Start Translation", command=self.start_translation)
        self.start_button.pack(pady=5)
        
        self.stop_button = tk.Button(self.root, text="Stop Translation", command=self.stop_translation, state=tk.DISABLED)
        self.stop_button.pack(pady=5)
        
        self.is_translating = False
        self.audio_queue = queue.Queue()

        # Get list of audio devices
        self.input_devices = sd.query_devices()

        # Create dropdown for input device selection
        self.input_var = tk.StringVar(self.root)
        self.input_var.set("Select Input Device")
        self.input_dropdown = tk.OptionMenu(self.root, self.input_var, *[device['name'] for device in self.input_devices if device['max_input_channels'] > 0])
        self.input_dropdown.pack(pady=5)

        # Load translation model
        self.load_translation_model()

        # WebSocket setup
        self.ws = None

    def load_translation_model(self):
        # Load MarianMT model for Spanish to English translation
        self.translator_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-es-en")
        self.translator_tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-es-en")

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(indata.tobytes(), websocket.ABNF.OPCODE_BINARY)

    def on_message(self, ws, message):
        data = json.loads(message)
        if 'text' in data:
            transcription = data['text']
            
            # Perform translation
            inputs = self.translator_tokenizer(transcription, return_tensors="pt")
            outputs = self.translator_model.generate(**inputs)
            translation = self.translator_tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Display results
            self.text_area.insert(tk.END, f"Spanish: {transcription}\nEnglish: {translation}\n\n")
            self.text_area.see(tk.END)

    def on_error(self, ws, error):
        print(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")

    def on_open(self, ws):
        print("WebSocket connection opened")

    def start_translation(self):
        input_device = next((device for device in self.input_devices if device['name'] == self.input_var.get()), None)

        if not input_device:
            print("Please select an input device")
            return

        self.is_translating = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Connect to WhisperLive WebSocket
        self.ws = websocket.WebSocketApp("ws://localhost:9090/",
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         on_open=self.on_open)
        Thread(target=self.ws.run_forever).start()

        self.stream = sd.InputStream(
            device=int(input_device['index']),
            samplerate=16000,
            channels=1,
            callback=self.audio_callback)

        self.stream.start()

    def stop_translation(self):
        self.is_translating = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        if self.ws:
            self.ws.close()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = RealtimeTranslator()
    app.run()