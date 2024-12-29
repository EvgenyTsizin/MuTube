from pydub import AudioSegment
import os
import json
import subprocess
import argparse
from xml.etree import ElementTree as ET
from music21 import converter
import music21

def extract_endings_from_xml(xml_path):
    """
    Extracts measure endings from a MusicXML file using XML parsing.

    Parameters:
        xml_path (str): Path to the MusicXML file.

    Returns:
        dict: Dictionary mapping measure numbers to ending numbers (if any).
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    measure_endings = {}

    # Search for all measures
    for measure in root.findall(".//measure"):
        measure_number = int(measure.get('number'))
        ending_number = None

        # Search for barline with 'ending'
        for barline in measure.findall('.//barline'):
            ending = barline.find('.//ending')
            if ending is not None:
                ending_number = int(ending.get('number'))
                break

        measure_endings[measure_number] = ending_number

    return measure_endings

def get_repeats_and_order(mxl_path):
    """
    Generates the play order of measures considering repeats and first/second endings.

    Parameters:
        mxl_path (str): Path to the MusicXML file.

    Returns:
        list: Ordered list of measure indices to be played.
    """
    score = converter.parse(mxl_path)
    endings = extract_endings_from_xml(mxl_path)

    measure_index = 0
    measure_repeat_start = 0

    play_order = []

    for measure in score.parts[0].getElementsByClass('Measure'):
    
        measure_index += 1
        
        if measure.leftBarline and isinstance(measure.leftBarline, music21.bar.Repeat):
            measure_repeat_start = measure_index

        if not (measure_repeat_start != -1 and endings.get(measure_index) == 2):
            play_order.append(measure_index)

        if measure.rightBarline and isinstance(measure.rightBarline, music21.bar.Repeat):
            if measure_repeat_start < 0:
                continue

            for idx in range(measure_repeat_start, measure_index + 1):
                if endings[idx] == 1:
                    continue
                play_order.append(idx)

            measure_repeat_start = -1

    return play_order

def split_and_combine_musicxml_to_wav(input_file, musescore_path):
    """
    Splits a MusicXML file into individual measures, converts them to MP3 and WAV,
    and combines the WAV files into a single WAV file based on the correct play order.

    Parameters:
        input_file (str): Path to the input MusicXML file.
        musescore_path (str): Path to the MuseScore executable.

    Returns:
        None
    """
    print("Conversion started")
    base_folder = os.path.dirname(input_file)
    output_folder = os.path.join(base_folder, "output/measure_combined")
    os.makedirs(output_folder, exist_ok=True)

    score = converter.parse(input_file)

    play_order = get_repeats_and_order(input_file)
    part_wav = {}

    for part_idx, part in enumerate(score.parts):
        wav_files = {}
        measure_durations = {}
        measure_play_timeline = {}
        measure_index = 0

        for measure_stream in part.getElementsByClass('Measure'):
            measure_index += 1
            print("Generating", measure_index, "Part", part_idx)
            musicxml_path = os.path.join(output_folder, f"measure_{measure_index}_part{part_idx}.musicxml")
            mp3_path = os.path.join(output_folder, f"measure_{measure_index}_part{part_idx}.mp3")
            wav_path = os.path.join(output_folder, f"measure_{measure_index}_part{part_idx}.wav")

            try:
                measure_stream.write("musicxml", fp=musicxml_path)

                subprocess.run([musescore_path, musicxml_path, '-o', mp3_path], capture_output=True, text=True)

                audio = AudioSegment.from_mp3(mp3_path)
                audio.export(wav_path, format="wav")

                wav_files[measure_index] = wav_path
                duration = len(AudioSegment.from_wav(wav_path)) / 1000.0  # Duration in seconds
                measure_durations[measure_index] = duration
            except:
                pass

        part_wav[part_idx] = (wav_files, measure_durations)

def combine_wav_files_from_parts(input_file):
    # Parse the score to determine the number of parts and play order
    score = converter.parse(input_file)
    num_parts = len(score.parts)
    play_order = get_repeats_and_order(input_file)
    base_folder = os.path.dirname(input_file)
    output_folder = os.path.join(base_folder, "output/measure_combined")

    combined = AudioSegment.silent(duration=1000)
    current_time = 1.0
    measure_play_timeline = {}

    for measure_index in play_order:
        print(measure_index)
        part_segments = []

        # Load WAV files for all parts for the current measure
        for part_idx in range(num_parts):
            wav_path = os.path.join(output_folder, f"measure_{measure_index}_part{part_idx}.wav")
            if os.path.exists(wav_path):
                part_segment = AudioSegment.from_wav(wav_path)
                part_segments.append(part_segment)

        # Combine parts for simultaneous playback
        if part_segments:
            combined_segment = part_segments[0]
            for segment in part_segments[1:]:
                combined_segment = combined_segment.overlay(segment)

            # Trim silence from the end
            combined_segment = combined_segment.strip_silence(silence_thresh=-50, padding=0)

            # Adjust duration to ensure it ends on a multiple of 0.1 seconds
            segment_duration = len(combined_segment) / 1000.0
            adjusted_duration = (int(segment_duration * 10) + 1) / 10.0
            silence_padding = int((adjusted_duration - segment_duration) * 1000)
            combined_segment += AudioSegment.silent(duration=silence_padding)

            # Append to the final combined audio
            combined += combined_segment

        else:
            # Add 2 seconds of silence if no segments exist
            combined += AudioSegment.silent(duration=2000)
            adjusted_duration = 2.
            # Update play timeline

        for t in range(int(current_time * 10), int((current_time + adjusted_duration) * 10)):
            measure_play_timeline[t / 10] = measure_index

        current_time += adjusted_duration

    combined += AudioSegment.silent(duration=2000)

    combined_wav_path = os.path.join(output_folder, "combined.wav")
    combined.export(combined_wav_path, format="wav", parameters=["-ar", "22050"])
    print(f"Combined WAV file saved as {combined_wav_path}")

    json_path = os.path.join(output_folder, "play_order.json")
    with open(json_path, "w") as json_file:
        json.dump({
            "play_order": play_order,
            "measure_play_timeline": measure_play_timeline
        }, json_file, indent=4)
    print(f"Play order and timeline saved as {json_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split a MusicXML file into measures and combine them into a single WAV file.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input MusicXML file.")
    parser.add_argument("-m", "--musescore", required=True, help="Path to the MuseScore executable.")
    parser.add_argument("--split-only", action="store_true", help="Perform only the splitting operation.")
    parser.add_argument("--combine-only", action="store_true", help="Perform only the combining operation.")

    args = parser.parse_args()

    if args.split_only and args.combine_only:
        print("Error: --split-only and --combine-only cannot be used together.")
    elif args.split_only:
        split_and_combine_musicxml_to_wav(args.input, args.musescore)
    elif args.combine_only:
        combine_wav_files_from_parts(args.input)
    else:
        split_and_combine_musicxml_to_wav(args.input, args.musescore)
        combine_wav_files_from_parts(args.input)

