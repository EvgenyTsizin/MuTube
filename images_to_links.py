import json
import os
import argparse
from os.path import join 

# Function to load JSON data from a file with UTF-8 encoding
def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def main(youtube_to_name_file, youtube_timing_folder, images_metadata_file, images_folder, output_file):
    # Load youtube_to_name.json
    youtube_to_name = load_json(youtube_to_name_file)
    
    # Load images metadata
    images_metadata = load_json(images_metadata_file)

    # Initialize output dictionary
    output_data = {}

    # Iterate over each image in the images metadata
    for image_filename, metadata in images_metadata.items():
        # Extract the measure index from metadata
        measure_index = metadata[1]
        
        # Initialize the entry for this image
        output_data[image_filename] = []

        # Iterate over each YouTube link and find the timing
        for youtube_link, youtube_name in youtube_to_name.items():
            timing_filepath = os.path.join(youtube_timing_folder, f'{youtube_name}.json')
            if not os.path.exists(timing_filepath):
                continue

            timing_data = load_json(timing_filepath)
            timing = timing_data.get(str(measure_index))
            if timing is not None:
                output_data[image_filename].append({
                    'youtube_link': youtube_link,
                    'timing': timing
                })

    # Save the output data to a JSON file
    with open(output_file, 'w', encoding='utf-8') as output_file:
        json.dump(output_data, output_file, indent=4, ensure_ascii=False)

    print(f"Process completed successfully. Output saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process images and extract YouTube timings.")
    
    parser.add_argument('-c', '--composition_name', required=True, help="composition name path.")
    
    parser.add_argument('-o', '--output', required=False, default = "site", help="site path")

    args = parser.parse_args()
    
    composition_name = args.composition_name
    
    youtube_to_name = join(args.output, "timings", composition_name, "youtube_to_name.json")
    youtube_timing_folder = join(args.output, "timings", composition_name, "youtube_score_mappings") 
    images_metadata_file = join(args.output, "images_metadata", composition_name + ".json")
    images_folder = join(args.output, "images", composition_name)
    output = join(args.output, "timings", composition_name, "image_links.json") 
    
    main(youtube_to_name, youtube_timing_folder, images_metadata_file, images_folder,output)