import tkinter as tk
from tkinter import messagebox
import simpleaudio as sa
import json
import os
from pathlib import Path
import sys
import wave
import threading
import time

class AudioSyncPlayer:
    def __init__(self, master, main_folder):
        self.master = master
        self.master.title("Audio Sync Player")

        self.main_folder = main_folder
        self.audio_players = {}
        self.json_syncs = {}
        self.audio_buttons = {}
        self.audio_sync_files = []
        self.current_play_thread = None
        self.stop_playing = threading.Event()
        self.update_time_thread = None

        self.load_files()

        # Start Time Input
        tk.Label(master, text="Start Time (seconds):").grid(row=0, column=0, padx=10, pady=5)
        self.start_time_entry = tk.Entry(master, width=10)
        self.start_time_entry.grid(row=0, column=1, padx=10, pady=5)

        # Main Audio Buttons
        self.main_play_button = tk.Button(master, text="Play Main", command=self.play_main_audio)
        self.main_play_button.grid(row=1, column=0, padx=10, pady=5)
        self.main_stop_button = tk.Button(master, text="Stop Main", command=self.stop_audio)
        self.main_stop_button.grid(row=1, column=1, padx=10, pady=5)

        # Current Play Time Label
        self.play_time_label = tk.Label(master, text="Current Play Time: 0.0s")
        self.play_time_label.grid(row=1, column=2, padx=10, pady=5)

    def load_files(self):
        self.audio_players.clear()
        self.json_syncs.clear()
        self.audio_buttons.clear()

        for root, dirs, files in os.walk(self.main_folder):
            for file in files:
                if file == "audio.wav":
                    audio_path = os.path.join(root, file)
                    self.audio_players[audio_path] = None  # Placeholder for wave object
                elif file == "audio_sync.json":
                    json_path = os.path.join(root, file)
                    self.json_syncs[json_path] = self.load_json(json_path)

        # Clear and repopulate buttons
        for widget in self.master.winfo_children()[5:]:  # Remove old buttons
            widget.destroy()
        self.populate_buttons(self.master)

    def load_json(self, json_path):
        with open(json_path, 'r') as f:
            return json.load(f)

    def populate_buttons(self, master):
        for idx, (json_path, sync_data) in enumerate(sorted(self.json_syncs.items())):

            audio_path = os.path.join(os.path.dirname(json_path), "audio.wav")
            label = tk.Label(master, text=f"Play {Path(json_path).parent.name}")
            label.grid(row=idx+2, column=0, padx=10, pady=5)
            play_button = tk.Button(master, text="Play", command=lambda path=audio_path, sync=sync_data: self.play_sub_audio(path, sync))
            play_button.grid(row=idx+2, column=1, padx=10, pady=5)
            stop_button = tk.Button(master, text="Stop", command=self.stop_audio)
            stop_button.grid(row=idx+2, column=2, padx=10, pady=5)
            self.audio_buttons[audio_path] = (play_button, stop_button)

    def play_main_audio(self):
        self.reset_playback_state()
        start_time = round(float(self.start_time_entry.get()), 1)
        main_wav_path = next((os.path.join(self.main_folder, file) for file in os.listdir(self.main_folder) if file.endswith('.wav')), None)
        if main_wav_path is None or not os.path.exists(main_wav_path):
            messagebox.showerror("Error", "Main audio file not found.")
            return
        
        self.current_play_thread = threading.Thread(target=self.play_audio_thread, args=(main_wav_path, start_time))
        self.current_play_thread.start()

        # Start the time updating thread
        self.update_time_thread = threading.Thread(target=self.update_play_time, args=(start_time,))
        self.update_time_thread.start()

    def play_sub_audio(self, audio_path, sync_data):
        self.reset_playback_state()
        start_time = float(self.start_time_entry.get())
        start_time_str = f"{start_time:.1f}"
        if start_time_str not in sync_data:
            messagebox.showerror("Error", f"Start time {start_time} not found in sync data.")
            return
        
        mapped_time = float(sync_data[start_time_str])
        
        self.current_play_thread = threading.Thread(target=self.play_audio_thread, args=(audio_path, mapped_time))
        self.current_play_thread.start()

    def play_audio_thread(self, audio_path, start_time):
        try:
            with wave.open(audio_path, 'rb') as wf:
                frame_rate = wf.getframerate()
                start_frame = int(start_time * frame_rate)
                wf.setpos(start_frame)
                audio_data = wf.readframes(wf.getnframes() - start_frame)
                self.stop_playing.clear()
                play_obj = sa.play_buffer(audio_data, wf.getnchannels(), wf.getsampwidth(), frame_rate)
                self.audio_players[audio_path] = play_obj
                while play_obj.is_playing():
                    if self.stop_playing.is_set():
                        play_obj.stop()
                        break
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_play_time(self, start_time):
        start_play_time = time.time()
        while not self.stop_playing.is_set():
            current_play_time = time.time() - start_play_time + start_time
            self.update_play_time_label(current_play_time)
            time.sleep(0.1)

    def update_play_time_label(self, current_time):
        self.play_time_label.config(text=f"Current Play Time: {current_time:.1f}s")

    def stop_audio(self):
        self.stop_playing.set()
        if self.current_play_thread and self.current_play_thread.is_alive():
            self.current_play_thread.join()
        if self.update_time_thread and self.update_time_thread.is_alive():
            self.update_time_thread.join()

    def reset_playback_state(self):
        self.stop_audio()
        self.stop_playing.clear()
        self.current_play_thread = None
        self.update_time_thread = None

if __name__ == "__main__":
    main_folder = '/media/simsim314/DATA/Github/music21/Pieces_raphsody/youtubes/Franz Liszt - Hungarian Rhapsody No. 2 in C-sharp minor'
    root = tk.Tk()
    app = AudioSyncPlayer(root, main_folder)
    root.mainloop()

