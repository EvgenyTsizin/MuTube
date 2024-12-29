import json
import argparse
import os

# Set up argument parsing
parser = argparse.ArgumentParser(description="Process play_order.json and sync.json to generate sync_measures.json.")
parser.add_argument("-i", "--base_folder", required=True, help="Base folder containing input files and for saving output.")

args = parser.parse_args()

# Define file paths
base_folder = args.base_folder
play_order_path = os.path.join(base_folder, 'play_order.json')
sync_path = os.path.join(base_folder, 'sync.json')
output_path = os.path.join(base_folder, 'sync_measures.json')

# Load play_order.json
with open(play_order_path, 'r') as f:
    play_order = json.load(f)

# Load sync.json
with open(sync_path, 'r') as f:
    sync_dict = json.load(f)

# Extract measure_play_timeline
measure_play_timeline = play_order.get("measure_play_timeline", {})

# Initialize new dictionary
dict_measures = {}

# Variables to track changes
previous_value = None

# Loop over sorted keys of measure_play_timeline
for string_key in sorted(measure_play_timeline.keys(), key=lambda x: float(x)):
    current_value = measure_play_timeline[string_key]
    if current_value != previous_value:  # Check if value has changed
        dict_measures[current_value] = sync_dict.get(string_key)
        previous_value = current_value  # Update previous_value for the next iteration

# Save the resulting dictionary as sync_measures.json
with open(output_path, 'w') as f:
    json.dump(dict_measures, f, indent=4)

print(f"Saved sync_measures.json in {base_folder}")

