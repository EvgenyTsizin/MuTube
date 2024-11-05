import os
import json
import argparse
from rapidfuzz import process, fuzz

# Setup argument parser
parser = argparse.ArgumentParser(description='Match MXL files to YouTube entries in a JSON file.')
parser.add_argument('pieces_folder', type=str, help='Path to the folder containing MXL files and JSON data.')
args = parser.parse_args()

# Define the folder path for MXL files and the JSON file based on the input argument
pieces_folder = args.pieces_folder
json_file_path = os.path.join(pieces_folder, 'youtubes.json')
output_json_path = os.path.join(pieces_folder, 'youtube_with_notes.json')

# Check if the files exist
if not os.path.exists(json_file_path):
    raise FileNotFoundError(f"JSON file not found at {json_file_path}")

if not os.path.isdir(pieces_folder):
    raise NotADirectoryError(f"Directory {pieces_folder} does not exist or is not a valid directory")

# Load the JSON file with utf-8 encoding
with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get all the MXL files in the Pieces folder
mxl_files = [f for f in os.listdir(pieces_folder) if f.endswith('.mxl')]

if not mxl_files:
    raise FileNotFoundError(f"No MXL files found in {pieces_folder}")

# Extract song titles and their corresponding YouTube lists from the JSON data
song_data = [(entry[0], entry[1]) for entry in data]

# List to hold the result tuples
results = []

# Iterate through each MXL file and find the best match in the list
for mxl_file in mxl_files:
    # Remove file extension to get the base name
    mxl_name = os.path.splitext(mxl_file)[0]
    
    # Use rapidfuzz's process.extractOne to find the best match
    best_match = process.extractOne(mxl_name, [item[0] for item in song_data], scorer=fuzz.token_set_ratio)
    
    if best_match:  # Ensure there's a match
        # Find the corresponding YouTube list for the best match
        for song_title, youtube_list in song_data:
            if song_title == best_match[0]:
                # Append tuple of (mxl_name, best_match song title, YouTube list) to results
                results.append((mxl_name, song_title, youtube_list))
                break

# Save the results to a new JSON file with utf-8 encoding
with open(output_json_path, 'w', encoding='utf-8') as output_file:
    json.dump(results, output_file, ensure_ascii=False, indent=4)

print(f"Results saved to {output_json_path}")
