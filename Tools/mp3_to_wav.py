import os
from pydub import AudioSegment
from pathlib import Path
import argparse

def convert_mp3_to_wav(mp3_file, sample_rate=22050):
    audio = AudioSegment.from_mp3(mp3_file)
    audio = audio.set_frame_rate(sample_rate)
    wav_file = mp3_file.with_suffix('.wav')
    audio.export(wav_file, format="wav")
    print(f"Converted {mp3_file} to {wav_file} with sample rate {sample_rate} Hz")

def find_and_convert(directory, sample_rate=22050):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp3'):
                mp3_file = Path(root) / file
                convert_mp3_to_wav(mp3_file, sample_rate)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and convert MP3 files to WAV in a directory with a specified sample rate.")
    parser.add_argument('-i', '--input', required=True, help='Path to the directory containing MP3 files.')
    parser.add_argument('-r', '--rate', type=int, default=22050, help='Sample rate for the WAV files.')
    
    args = parser.parse_args()
    directory = args.input
    sample_rate = args.rate

    find_and_convert(directory, sample_rate)
