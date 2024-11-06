import os
import shutil
import json
import argparse
import music21
import bisect
import music21

def get_measure_times(mxl_path):

    score = None 
    
    try:
        score = music21.converter.parse(mxl_path)
    except:
        # If not found, search for another file ending with .mxl
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
    current_time = 0.0  # To track the total time considering repeats
    repeat_start_time = -1 
    
    for measure in score.parts[0].getElementsByClass('Measure'):
        measure_index = measure.measureNumber
        
        # Update the time for the current measure
        if measure_index not in measure_times:
            measure_times[measure_index] = current_time
        
        # Handle the repeats
        if measure.leftBarline and measure.leftBarline.style == 'heavy-light':
            # Repeat start - mark the time for the first repeat
            repeat_start_time = current_time
            print("repeat start time", repeat_start_time)

        # Increment the time by the duration of the current measure
        current_time += measure.duration.quarterLength

        if measure.rightBarline and measure.rightBarline.style == 'final':
            if repeat_start_time > 0:
                # Repeat end - add the duration of the repeated section
                repeat_duration = current_time - repeat_start_time
                
                print("repeat duration", repeat_duration)
                current_time += repeat_duration
                repeat_start_time = -1 
                
    print("Successfully extracted", len(measure_times), "measures")
    return measure_times


def save_to_json(data, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

def get_score_scale(score_data, first_audio_sync):
    json_last_timing = float(list(first_audio_sync.keys())[-1])
    score_last_timing = float(list(score_data.values())[-1])

    scale_factor = json_last_timing / score_last_timing
    if abs(scale_factor - 1) < 0.05:
        scale_factor = 1
    
    if abs(scale_factor - 0.5) < 0.05:
        scale_factor = 0.5

    return scale_factor

def find_youtube_time_for_measure(score_index, score_data, scale_factor, youtube_timings):
    score_time = score_data.get(str(score_index))

    if score_time is None:
        raise ValueError(f"Score index {score_index} not found in the score JSON data")
    
    # Scale the score time by the scale_factor
    scaled_time = float(score_time) * scale_factor
    
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

def create_score_to_youtube_mappings(composition_folder, output_folder, youtube_to_names_path):
    composition_name = os.path.basename(composition_folder)
    
    score_json_path = os.path.join(output_folder, 'timings', composition_name, 'measure_times.json')
    score_data = load_json_file(score_json_path)
    
    output_directory = os.path.join(output_folder, "timings", composition_name, "youtube_score_mappings")
    os.makedirs(output_directory, exist_ok=True)
    
    youtube_to_names = load_json_file(youtube_to_names_path)
    first_audio_sync = None
    for youtube_id in youtube_to_names.values():
        subdir_path = os.path.join(composition_folder, youtube_id)
        if os.path.isdir(subdir_path) and youtube_id != 'output':
            json_file_path = os.path.join(subdir_path, 'audio_sync.json')
            if os.path.exists(json_file_path):
                first_audio_sync = load_json_file(json_file_path)
                break

    if not first_audio_sync:
        raise FileNotFoundError("No audio_sync.json file found in the YouTube directories.")

    scale_factor = get_score_scale(score_data, first_audio_sync)
    print("scale_factor", scale_factor)
    for youtube_id in youtube_to_names.values():
        subdir_path = os.path.join(composition_folder, youtube_id)
        if os.path.isdir(subdir_path) and youtube_id != 'output':
            json_file_path = os.path.join(subdir_path, 'audio_sync.json')
            if os.path.exists(json_file_path):
                youtube_data = load_json_file(json_file_path)

                score_to_youtube = {}
                for idx in score_data.keys():
                    youtube_time = find_youtube_time_for_measure(idx, score_data, scale_factor, youtube_data)
                    score_to_youtube[int(idx)] = youtube_time
                
                output_file_path = os.path.join(output_directory, f'{youtube_id}.json')
                save_to_json(score_to_youtube, output_file_path)

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

    save_to_json(images_data, images_json_path)

def copy_and_rename_folder(input_folder, output_folder="site"):
    youtube_to_names_path = os.path.join(input_folder, "..", 'youtube_to_name.json')
    if not os.path.exists(youtube_to_names_path):
        raise FileNotFoundError(f"youtube_to_name.json not found in input folder: {input_folder}")

    for composition_name in os.listdir(input_folder):
        composition_folder = os.path.join(input_folder, composition_name)
        if not os.path.isdir(composition_folder):
            continue

        cropped_images_src = os.path.join(composition_folder, "output", "cropped_images")
        cropped_images_dst = os.path.join(output_folder, "images", composition_name)
        
        #if os.path.isdir(cropped_images_dst):
        #    continue
            
        island_locations_src = os.path.join(composition_folder, "output", "island_locations.json")
        island_locations_dst = os.path.join(output_folder, "images_metadata", f"{composition_name}.json")
        mxl_src = next((os.path.join(composition_folder, f) for f in os.listdir(composition_folder) if f.endswith('modified.musicxml')), None)
        timing_dst = os.path.join(output_folder, "timings", composition_name, "measure_times.json")
        youtube_to_name_dst = os.path.join(output_folder, "timings", composition_name, "youtube_to_name.json")
	
        measure_times = get_measure_times(mxl_src)
	
        if measure_times is None:
            continue 
            
        os.makedirs(cropped_images_dst, exist_ok=True)
        os.makedirs(os.path.dirname(island_locations_dst), exist_ok=True)
        os.makedirs(os.path.dirname(timing_dst), exist_ok=True)
        
        images_list = []
        for file in os.listdir(cropped_images_src):
            src_file = os.path.join(cropped_images_src, file)
            dst_file = os.path.join(cropped_images_dst, file)
            shutil.copy2(src_file, dst_file)
            images_list.append(file)
        print(f"Copied images from {cropped_images_src} to {cropped_images_dst}")

        shutil.copy2(island_locations_src, island_locations_dst)
        print(f"Copied {island_locations_src} to {island_locations_dst}")

        shutil.copy2(youtube_to_names_path, youtube_to_name_dst)
        print(f"Copied {youtube_to_names_path} to {youtube_to_name_dst}")

        save_to_json(measure_times, timing_dst)
        print(f"Saved measure times to {timing_dst}")
        
        try:
            create_score_to_youtube_mappings(composition_folder, output_folder, youtube_to_names_path)
        except Exception as e:
            print(f"Error in create_score_to_youtube_mappings for {composition_folder}: {e}")
            continue  # Skip to the next composition if there's an error


        update_images_json(output_folder, composition_name, images_list)
        print(f"Updated images.json with images from {composition_name}")

    print("Copy and rename operations completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy and rename folders and files.")
    parser.add_argument('-i', '--input', required=True, help="Input folder (e.g., Pieces/youtubes")
    parser.add_argument('-o', '--output', default="site", help="Output folder (default is 'site')")
    
    args = parser.parse_args()
    copy_and_rename_folder(args.input, args.output)

