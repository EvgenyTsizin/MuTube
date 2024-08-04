import os
import shutil
import json
import argparse
import music21
import pandas as pd
import bisect

def get_measure_times(mxl_path):
    score = music21.converter.parse(mxl_path)
    measure_times = {}
    for measure in score.parts[0].getElementsByClass('Measure'):
        measure_index = measure.measureNumber
        time_offset = measure.offset
        measure_times[measure_index] = float(time_offset)
    
    print("Successfully extracted", len(measure_times), "measures")
    return measure_times

def save_to_json(data, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

def get_csv_score_scale(csv_file, json_file):
    # Read the CSV file
    csv_data = pd.read_csv(csv_file)
    # Read the JSON file
    with open(json_file, 'r') as json_file:
        json_data = json.load(json_file)
    
    # Extract the first column (assuming it is the timing)
    csv_timings = csv_data.iloc[:, 0]
    json_timings = list(json_data.values())

    # Get the first and last timings from both CSV and JSON
    csv_last_timing = float(csv_timings.iloc[-1].split(';')[0])
    json_last_timing = json_timings[-1]

    # Calculate the scale factor
    scale_factor = json_last_timing / csv_last_timing
    return scale_factor

def find_youtube_time_for_measure(score_index, score_data, csv_score_scale, youtube_timings):
    # Get the score time for the given index
    score_time = score_data.get(str(score_index))

    if score_time is None:
        raise ValueError(f"Score index {score_index} not found in the score JSON data")
    
    # Scale the score time by the csv_score_scale
    scaled_time = float(score_time) / csv_score_scale

    # Convert youtube_timings to a list of floats for comparison
    youtube_timings_float = [(float(k), v) for k, v in youtube_timings.items()]
    
    # Find the insertion point for the scaled_time
    youtube_timings_float.sort()
    idx = bisect.bisect_left([yt[0] for yt in youtube_timings_float], scaled_time)
    
    # If the scaled_time is exactly one of the points
    if idx < len(youtube_timings_float) and youtube_timings_float[idx][0] == scaled_time:
        return youtube_timings_float[idx][1]
    
    # Get the timings just before and just after the scaled_time
    lower_timing, lower_value = youtube_timings_float[idx - 1] if idx > 0 else youtube_timings_float[0]
    higher_timing, higher_value = youtube_timings_float[idx] if idx < len(youtube_timings_float) else youtube_timings_float[-1]
    
    # Linear interpolation
    if lower_timing == higher_timing:
        return lower_value
    else:
        proportion = (scaled_time - lower_timing) / (higher_timing - lower_timing)
        interpolated_time = lower_value + proportion * (higher_value - lower_value)
        return interpolated_time

def create_score_to_youtube_mappings(input_folder, output_folder):
    csv_file_path = None
    for file in os.listdir(input_folder):
        if file.endswith('.csv'):
            csv_file_path = os.path.join(input_folder, file)
            break

    if not csv_file_path:
        raise FileNotFoundError("No CSV file found in the input folder.")

    composition_name = os.path.basename(os.path.normpath(input_folder))
    
    score_json_path = os.path.join(output_folder, 'timings', composition_name, 'measure_times.json')
    
    youtube_dir = os.path.join(input_folder, 'youtube_videos')
    
    # Load JSON data
    score_data = load_json_file(score_json_path)
    csv_score_scale = get_csv_score_scale(csv_file_path, score_json_path)
    
    # Create output directory
    output_directory = os.path.join(output_folder, "timings", composition_name, "youtube_score_mappings")
    os.makedirs(output_directory, exist_ok=True)
    
    # Traverse each YouTube video directory
    for subdir in os.listdir(youtube_dir):
        subdir_path = os.path.join(youtube_dir, subdir)
        if os.path.isdir(subdir_path):
            json_file_path = os.path.join(subdir_path, 'audio_sync.json')
            if os.path.exists(json_file_path):
                youtube_data = load_json_file(json_file_path)
                
                # Create a mapping for this video
                score_to_youtube = {}
                for idx in score_data.keys():
                    youtube_time = find_youtube_time_for_measure(idx, score_data, csv_score_scale, youtube_data)
                    score_to_youtube[int(idx)] = youtube_time
                
                # Save the mapping to the output directory
                output_file_path = os.path.join(output_directory, f'{subdir}.json')
                with open(output_file_path, 'w') as output_file:
                    json.dump(score_to_youtube, output_file, indent=4)
    
    print(f"Mappings created in folder: {output_directory}")

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def update_images_json(output_folder, composition_name, images_list):
    images_json_path = os.path.join(output_folder, "images.json")
    images_data = {}

    if os.path.exists(images_json_path):
        with open(images_json_path, 'r') as file:
            images_data = json.load(file)
    
    images_data[composition_name] = images_list

    with open(images_json_path, 'w') as file:
        json.dump(images_data, file, indent=4)

def copy_and_rename_folder(input_folder, output_folder="site"):
    # Extract composition name from the input folder path
    composition_name = os.path.basename(os.path.normpath(input_folder))
    cropped_images_src = os.path.join(input_folder, "cropped_images")
    cropped_images_dst = os.path.join(output_folder, "images", composition_name)
    island_locations_src = os.path.join(input_folder, "island_locations.json")
    island_locations_dst = os.path.join(output_folder, "images_metadata", f"{composition_name}.json")
    mxl_src = os.path.join(input_folder, "modified.musicxml")
    timing_dst = os.path.join(output_folder, "timings", composition_name, "measure_times.json")

    youtub_to_names_src = os.path.join(input_folder, "youtube_to_name.json")
    youtub_to_name_dst = os.path.join(output_folder, "timings", composition_name, "youtube_to_name.json")

    # Create necessary directories
    os.makedirs(cropped_images_dst, exist_ok=True)
    os.makedirs(os.path.dirname(island_locations_dst), exist_ok=True)
    os.makedirs(os.path.dirname(timing_dst), exist_ok=True)
    
    # Copy cropped images folder
    images_list = []
    for root, dirs, files in os.walk(cropped_images_src):
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(cropped_images_dst, os.path.relpath(src_file, cropped_images_src))
            shutil.copy2(src_file, dst_file)
            images_list.append(file)  # Only the filename
    print(f"Copied {cropped_images_src} to {cropped_images_dst}")

    # Copy and rename island_locations.json file
    shutil.copy2(island_locations_src, island_locations_dst)
    print(f"Copied {island_locations_src} to {island_locations_dst}")

    shutil.copy2(youtub_to_names_src, youtub_to_name_dst)
    print(f"Copied {youtub_to_names_src} to {youtub_to_name_dst}")

    # Process and save measure times from MusicXML file
    measure_times = get_measure_times(mxl_src)
    save_to_json(measure_times, timing_dst)
    print(f"Saved measure times to {timing_dst}")

    # Create mappings for YouTube videos
    create_score_to_youtube_mappings(input_folder, output_folder)

    # Update images.json with the new images list
    update_images_json(output_folder, composition_name, images_list)
    print(f"Updated images.json with images from {composition_name}")

    print("Copy and rename operations completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy and rename folders and files.")
    parser.add_argument('-i', '--input', required=True, help="Input folder (e.g., synctoolbox/<composition_name>)")
    parser.add_argument('-o', '--output', default="site", help="Output folder (default is 'site')")
    
    args = parser.parse_args()
    copy_and_rename_folder(args.input, args.output)
