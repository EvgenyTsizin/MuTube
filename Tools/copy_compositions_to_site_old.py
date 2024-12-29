import os
import shutil
import json
import argparse
import music21
import bisect
import music21
from xml.etree import ElementTree as ET
from music21 import expressions

def sanitize_folder_name(name):
    """Sanitize folder names by removing or replacing invalid characters and non-ASCII characters."""
    # Normalize the name to decompose characters like é into base characters
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    # Remove invalid characters for folder names
    return re.sub(r'[<>:"/\\|?*()\'"]', '', name)
    

def extract_endings_from_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Namespace handling for MusicXML
    ns = {'mxl': 'http://www.musicxml.org'}

    # List to store measure endings
    measure_endings = dict()

    # Search for all measures
    for measure in root.findall(".//measure"):
        measure_number = measure.get('number')
        ending_number = None  # Default to None

        # Search for barline with 'ending'
        for barline in measure.findall('.//barline', ns):
            ending = barline.findall('.//ending')
            if ending:
                ending_number = int(ending[0].attrib['number'])
                break  # Stop searching after finding the first ending

        # Append result as a tuple: (measure_number, ending_number)
        measure_endings[int(measure_number)] = ending_number

    return measure_endings

def duration_fixed(measure):
    fermata_list = []
    # Iterate over all elements in the measure
    total = 0

    elements = measure.elements

    for element in measure.elements:
        if isinstance(element, music21.stream.Voice):
            elements = element.elements
            break

    for element in elements:
        cur_duration = element.duration.quarterLength

        # Check if the element has the 'expressions' attribute
        if hasattr(element, "expressions"):
            for expr in element.expressions:
                # Check if the expression is a Fermata
                if isinstance(expr, expressions.Fermata):
                    cur_duration *= 2

        total += cur_duration
    return total

def get_repeats(score):

    repeat_start = False

    repeats = {}
    measure_index = 0

    for measure in score.parts[0].getElementsByClass('Measure'):
        measure_index += 1
        repeats[measure_index] = False

        if measure.leftBarline and isinstance(measure.leftBarline, music21.bar.Repeat):
            repeat_start = True

        if repeat_start:
            repeats[measure_index] = True

        if measure.rightBarline and isinstance(measure.rightBarline, music21.bar.Repeat):
            if repeat_start:
                repeat_start = False
            else:
                for i in range(measure_index + 1):
                    repeats[measure_index] = True

    return repeats


def get_measure_times(mxl_path):
    score = music21.converter.parse(mxl_path)
    endings = extract_endings_from_xml(mxl_path)
    repeats = get_repeats(score)

    measure_times = {}
    measure_durations = {}

    current_time = 0.0
    repeat_start_time = 0
    measure_index = 0

    for _ in score.parts[0].getElementsByClass('Measure'):
        measure_index += 1

    last_measure = measure_index

    measure_index = 0
    prev_t = 0
    measure_repeat_start = -1

    for measure in score.parts[0].getElementsByClass('Measure'):
        measure_index += 1

        if measure.leftBarline and isinstance(measure.leftBarline, music21.bar.Repeat):
            repeat_start_time = current_time
            measure_repeat_start = measure_index

            print("repeat started", measure_index)

        measure_durations[measure_index] = duration_fixed(measure)

        if not (repeats[measure_index] and endings[measure_index] == 2):
            measure_times[measure_index] = current_time
            current_time += measure_durations[measure_index]

        t = current_time / 2
        tminutes = t // 60
        tseconds = round(t - 60 * tminutes, 4)

        prevtminutes = prev_t // 60
        prevtseconds = round(prev_t - 60 * prevtminutes, 4)
        prev_t = t

        print(measure_index, duration_fixed(measure) * 0.5, "|", int(tminutes), ":",
             str(tseconds).replace(".", ":"), "|", int(prevtminutes), ":", str(prevtseconds).replace(".", ":"))

        if measure.rightBarline and isinstance(measure.rightBarline, music21.bar.Repeat):
            if repeat_start_time < 0:
                repeat_start_time = 0
                measure_repeat_start = 0

            for idx in range(measure_repeat_start, measure_index + 1):
                dt = measure_durations[idx]

                if endings[idx] == 1:
                    continue

                current_time += dt

                if idx not in measure_times:
                    measure_times[idx] = current_time

                t = current_time / 2
                tminutes = t // 60
                tseconds = round(t - 60 * tminutes, 4)

                print("repeat", idx, int(tminutes), ":", str(tseconds).replace(".", ":"))

            repeat_start_time = -1

    return measure_times, current_time

def save_to_json(data, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

def get_score_scale(total_time, first_audio_sync):
    json_last_timing = float(list(first_audio_sync.keys())[-1])

    scale_factor = json_last_timing / total_time

    if abs(scale_factor - 1) < 0.05:
        scale_factor = 1

    if abs(scale_factor - 0.5) < 0.05:
        scale_factor = 0.5

    return scale_factor

def find_youtube_time_for_measure(score_index, score_data, scale_factor, youtube_timings):
    score_time = score_data.get(score_index)

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
    score_data, total_time = load_json_file(score_json_path)
    
    output_directory = os.path.join(output_folder, "timings", composition_name, "youtube_score_mappings")
    os.makedirs(output_directory, exist_ok=True)
    
    youtube_to_names = load_json_file(youtube_to_names_path)
    first_audio_sync = None
    for subfolder in os.listdir(composition_folder):
        subfolder_path = os.path.join(composition_folder, subfolder)
        
        if os.path.isdir(subfolder_path) and subfolder != 'output':
            json_file_path = os.path.join(subfolder_path, 'audio_sync.json')
            if os.path.exists(json_file_path):
                first_audio_sync = load_json_file(json_file_path)
                break

    if not first_audio_sync:
        raise FileNotFoundError("No audio_sync.json file found in the subdirectories.")

    scale_factor = get_score_scale(total_time, first_audio_sync)
    
    print("scale_factor", scale_factor)
    
    for subfolder in os.listdir(composition_folder):
        subfolder_path = os.path.join(composition_folder, subfolder)
        if os.path.isdir(subfolder_path) and subfolder != 'output':
            json_file_path = os.path.join(subfolder_path, 'audio_sync.json')
            
            if os.path.exists(json_file_path):
                youtube_data = load_json_file(json_file_path)
		
                score_to_youtube = {}
                for idx in score_data.keys():
                    youtube_time = find_youtube_time_for_measure(idx, score_data, scale_factor, youtube_data)
                    score_to_youtube[int(idx)] = youtube_time

                # Inserted logic starts here
                score_youtube_ratio = (scale_factor * (float(score_data['4']) - float(score_data['3']))) / (score_to_youtube[4] - score_to_youtube[3])

                # Backtrack to calculate score_to_youtube[2]
                score_duration_2_3 = scale_factor * (float(score_data['3']) - float(score_data['2']))
                youtube_duration_2_3 = score_duration_2_3 / score_youtube_ratio
                score_to_youtube[2] = score_to_youtube[3] - youtube_duration_2_3

                # Backtrack further to calculate score_to_youtube[1]
                score_duration_1_2 = scale_factor * (float(score_data['2']) - float(score_data['1']))
                youtube_duration_1_2 = score_duration_1_2 / score_youtube_ratio
                score_to_youtube[1] = score_to_youtube[2] - youtube_duration_1_2
                
                # Check if values are less than 0 and set to 0 if necessary
                if score_to_youtube[1] < 0:
                    score_to_youtube[1] = 0
                if score_to_youtube[2] < 0:
                    score_to_youtube[2] = 0
                # Inserted logic ends here
                
                
                output_file_path = os.path.join(output_directory, f'{subfolder}.json')
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


    composition_idx = 0
     
    for composition_name in os.listdir(input_folder):
        composition_folder = os.path.join(input_folder, composition_name)

        if not os.path.isdir(composition_folder):
            continue

        print(composition_idx, composition_name)
        composition_idx += 1

    composition_idx = 0
    for composition_name in os.listdir(input_folder):
        composition_folder = os.path.join(input_folder, composition_name)
        if not os.path.isdir(composition_folder):
            continue
        
        print("\n\n\n\n\n", composition_idx, composition_name)
        composition_idx += 1

        cropped_images_src = os.path.join(composition_folder, "output", "cropped_images")
        cropped_images_dst = os.path.join(output_folder, "images", composition_name)
        
        #if os.path.isdir(cropped_images_dst):
        #    continue
            
        island_locations_src = os.path.join(composition_folder, "output", "island_locations.json")
        island_locations_dst = os.path.join(output_folder, "images_metadata", f"{composition_name}.json")
        mxl_src = next((os.path.join(composition_folder, f) for f in os.listdir(composition_folder) if f.endswith('modified.musicxml')), None)
        
        print(island_locations_src, mxl_src)
        
        timing_dst = os.path.join(output_folder, "timings", composition_name, "measure_times.json")
        youtube_to_name_dst = os.path.join(output_folder, "timings", composition_name, "youtube_to_name.json")
    
        timings = get_measure_times(mxl_src)
    
        if timings is None:
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

        save_to_json(timings, timing_dst)
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

