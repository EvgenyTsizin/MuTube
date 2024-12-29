import os
import json
import tkinter as tk
from tkinter import ttk, PhotoImage
from PIL import Image, ImageTk
import pygame
import music21

root_path = "/media/simsim314/DATA/Github/music21/Pieces/youtubes/Franz Liszt - Hungarian Rhapsody No. 2 in C-sharp minor"
mxl_path = next((os.path.join(root_path, f) for f in os.listdir(root_path) if f.endswith('_modified.musicxml')), None)
images_path = os.path.join(root_path, "output/cropped_images")
metadata_path = os.path.join(root_path, "output/island_locations.json")

def load_metadata(metadata_path):
    with open(metadata_path, 'r') as f:
        return json.load(f)

def get_measure_times(mxl_path):
    score = None
    try:
        score = music21.converter.parse(mxl_path)
    except:
        mxl_path = next((os.path.join(os.path.dirname(mxl_path), f) for f in os.listdir(os.path.dirname(mxl_path)) if f.endswith('.mxl')), None)
    if mxl_path is None:
        return None
    if score is None:
        try:
            score = music21.converter.parse(mxl_path)
        except:
            return None
    if score is None:
        return None

    measure_times = {}
    current_time = 0.0
    repeat_start_time = 0
    measure_index = -1

    for _ in score.parts[0].getElementsByClass('Measure'):
        measure_index += 1
    last_measure = measure_index
    measure_index = -1
    prev_t = 0

    for measure in score.parts[0].getElementsByClass('Measure'):
        measure_index += 1
        measure_times[measure_index + 1] = current_time
        if measure.leftBarline and isinstance(measure.leftBarline, music21.bar.Repeat) and (
                getattr(measure.leftBarline, 'style', None) == 'heavy-light' or getattr(measure.leftBarline, 'type', None) == 'heavy-light'):
            repeat_start_time = current_time
        current_time += measure.duration.quarterLength
        t = current_time / 2
        tminutes = t // 60
        tseconds = round(t - 60 * tminutes, 4)
        
        
        prevtminutes = prev_t // 60
        prevtseconds = round(prev_t - 60 * prevtminutes, 4)
        prev_t = t
        
        print(measure_index + 1, measure.duration.quarterLength * 0.5, "|", int(tminutes), ":", str(tseconds).replace(".",":"), "|", int(prevtminutes), ":", str(prevtseconds).replace(".",":"))
        
        if measure_index + 1 == 69:
                print(measure)
                
        if measure.rightBarline and isinstance(measure.rightBarline, music21.bar.Repeat) and (
                getattr(measure.rightBarline, 'style', None) == 'final' or getattr(measure.rightBarline, 'type', None) == 'final'):
            if (repeat_start_time >= 0 and measure_index != last_measure) or repeat_start_time > 0:
                repeat_duration = current_time - repeat_start_time
                current_time += repeat_duration
                repeat_start_time = -1
    return measure_times, current_time

# Scale measure times to fit the length of the WAV file
def scale_measure_times(measure_times, total_time, audio_length):
    scale_factor = 0.5 # audio_length / total_time
    print(scale_factor)
    return {measure: time * scale_factor for measure, time in measure_times.items()}

# Pre-compute data outside the UI logic
image_metadata = load_metadata(metadata_path)
measure_times, total_time = get_measure_times(mxl_path)

# Initialize pygame mixer for audio playback
pygame.mixer.init()
audio_path = next((os.path.join(root_path, f) for f in os.listdir(root_path) if f.endswith('.wav')), None)
if audio_path:
    pygame.mixer.music.load(audio_path)
    audio_length = pygame.mixer.Sound(audio_path).get_length()
    measure_times = scale_measure_times(measure_times, total_time, audio_length)

# Create main window
root = tk.Tk()
root.title("Music Score UI")

# Start Time Label
start_time_label = tk.Label(root, text="Start Time: 00:00")
start_time_label.pack()

# Top Image Display
image_label = tk.Label(root, width=1000, height=200)
image_label.pack()

# Function to load image
current_image = None
def load_image(image_path):
    global current_image
    img = Image.open(image_path).convert('RGB')
    img = img.resize((1000, 200), Image.LANCZOS)
    current_image = ImageTk.PhotoImage(img)
    image_label.config(image=current_image)

# Dropdown menu for images
image_combo = ttk.Combobox(root, values=[f"{key} (Measure {value[1]})" for key, value in image_metadata.items()], width=50)
# Load the first image initially
first_image = list(image_metadata.keys())[0]
load_image(os.path.join(images_path, first_image))
# Start playing from the beginning initially if audio is available
if audio_path:
    pygame.mixer.music.play()
image_combo.pack()

def on_image_select(event):
    selected_image = image_combo.get().split(' (Measure ')[0] if ' (Measure ' in image_combo.get() else image_combo.get()
    image_path = os.path.join(images_path, selected_image)
    load_image(image_path)
    measure_number = image_metadata[selected_image][1]
    start_time_seconds = measure_times.get(measure_number, 0)
    minutes = start_time_seconds // 60
    seconds = round(start_time_seconds - 60 * minutes, 4)
    start_time_label.config(text=f"Start Time: {int(minutes):02}:{seconds}")
    if measure_number in measure_times:
        pygame.mixer.music.stop()
        pygame.mixer.music.play(start=measure_times[measure_number])
        play_button.config(text="Pause")
        global is_playing
        is_playing = True

image_combo.bind("<<ComboboxSelected>>", on_image_select)

# Play/Stop Button
is_playing = False
def toggle_play():
    global is_playing
    selected_image = image_combo.get()
    measure_number = image_metadata[selected_image][1] if selected_image in image_metadata else 0
    if is_playing:
        pygame.mixer.music.stop()
        play_button.config(text="Play")
    else:
        if measure_number in measure_times:
            pygame.mixer.music.play(start=measure_times.get(measure_number, 0))
        play_button.config(text="Pause")
    is_playing = not is_playing

play_button = tk.Button(root, text="Play", command=toggle_play)
play_button.pack()

# Start the Tkinter loop
root.mainloop()

