import json
import argparse
import os

def seconds_to_minutes_seconds(seconds):
    """Convert seconds to minutes:seconds.milliseconds format."""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    if milliseconds > 0:
        return f"{minutes}:{remaining_seconds:02}.{milliseconds:03}"
    else:
        return f"{minutes}:{remaining_seconds:02}"

# Set up argument parsing
parser = argparse.ArgumentParser(description="Convert JSON values from seconds to minutes:seconds.milliseconds format and print them.")
parser.add_argument("-i", "--input_file", required=True, help="Path to the JSON file.")

args = parser.parse_args()

# Load the JSON file
input_file = args.input_file
if not os.path.isfile(input_file):
    print(f"Error: File {input_file} does not exist.")
    exit(1)

with open(input_file, 'r') as f:
    data = json.load(f)

# Convert and print each key-value pair
for key, value in data.items():
    try:
        seconds = float(value)
        formatted_time = seconds_to_minutes_seconds(seconds)
        print(f"{key}: {formatted_time}")
    except (ValueError, TypeError):
        print(f"{key}: {value} (not a numeric value, skipped)")

