import os
import json
import argparse
import numpy as np
from PIL import Image
import re 
import cv2 

DEBUG = False 

def crop_white_edges(image_data, delta = 1):
    white_threshold = 250
    first_non_white_row, last_non_white_row = None, None

    for i in range(image_data.shape[0]):
        if np.any(image_data[i, :] < white_threshold):
            if first_non_white_row is None:
                first_non_white_row = i
            last_non_white_row = i

    if first_non_white_row is not None and last_non_white_row is not None:
        return image_data[first_non_white_row:last_non_white_row + delta, :]
    
    return image_data

def resize_and_crop_image(image_path, factor):
    image = Image.open(image_path).convert('L')
    image_array = np.array(image)
    image_array = crop_white_edges(image_array, delta = 10)
    
    new_height, new_width = image_array.shape[0] // factor, image_array.shape[1] // factor

    resized_array = np.zeros((new_height, new_width), dtype=image_array.dtype)
    for i in range(new_height):
        for j in range(new_width):
            block = image_array[i * factor:(i + 1) * factor, j * factor:(j + 1) * factor]
            resized_array[i, j] = np.min(block)

    image_data = crop_white_edges(resized_array)
    return image_data

def remove_consecutive_values(x_vals):
    result = []
    for i in range(len(x_vals)):
        if i == 0 or x_vals[i] != x_vals[i-1] + 1:
            result.append(x_vals[i])
    return result

def max_continuous_ones(image_data):
    # Use numpy to find the maximum count of consecutive 1s in each row
    def max_consecutive_ones(row):
        # Find indices where values are 0
        zero_indices = np.where(row == 0)[0]
        # Split the row at zero indices and calculate lengths of segments of 1s
        ones_segments = zero_indices[1:] - zero_indices[:-1]

        max_count = np.max(ones_segments)
        return max_count

    max_counts = np.apply_along_axis(max_consecutive_ones, axis=1, arr=image_data)
    return max_counts

def find_islands(image_path, black_threshold=150, skip_pixels=7):
    factor = 5
    
    image_data = resize_and_crop_image(image_path, factor)
    image_data[image_data < black_threshold] = 0
    image_data[image_data >= black_threshold] = 255
    image_data //= 255

    island_columns, ys = [], []

    if DEBUG:
        # Convert image to RGB
        image_with_lines = cv2.cvtColor(image_data * 255, cv2.COLOR_GRAY2RGB)

    # Sum all X-axis values for each level of Y
    y_sums = max_continuous_ones(1 - image_data)

    # Scatter plot of values in the top 10% of maximum y_sums
    max_value = np.max(y_sums)
    threshold = 0.99 * max_value
    x_vals = remove_consecutive_values(np.where(y_sums >= threshold)[0])
    x_vals.sort()
    
    if len(x_vals) >= 10:
        y0 = x_vals[-10]
        y1 = x_vals[-1]
        ys = [y0, y1]

        y_sum_total = np.sum(1 - (image_data[y0:y1 + 1, :]), axis=0)

        # Scan all x values to determine if it is an island
        x = 0
        while x < y_sum_total.shape[0]:
            if y_sum_total[x] >= 0.985 * (y1 - y0):
                island_columns.append(x)
                # Draw the red line to indicate the island
                if DEBUG:
                    cv2.line(image_with_lines, (x-1, y0), (x-1, y1), (0, 0, 255), 1)  # Red line
                x += skip_pixels  # Skip pixels after finding an island
            else:
                x += 1

    # Display image with lines at x_vals
    if DEBUG:
        for x in x_vals:
            cv2.line(image_with_lines, (0, x), (image_with_lines.shape[1], x), (255, 0, 0), 1)  # Blue line

        # Show the image using OpenCV
        cv2.imshow('Image with Detected Lines', image_with_lines)
        while True:
            if cv2.waitKey(1) & 0xFF == 13:  # Wait for the Enter key
                break

    return island_columns, ys

def ocr_measures(json_file_path):
    with open(json_file_path, 'r') as file:
        all_data = json.load(file)
    
    all_data.sort(key=lambda x: x["image"])
    result_dict, previous_number = {}, None

    for entry in all_data:
        current_number = int(entry["word"])
        if previous_number is None or 0 < current_number - previous_number < 50:
            result_dict[entry["image"]] = current_number
        previous_number = current_number
    
    return result_dict

def report_measures(directory_path):
    json_file_path = os.path.join(directory_path, 'output/ocr_results.json')
    ocr_dict = ocr_measures(json_file_path)
    results = {}
    images_directory = os.path.join(directory_path, "output/__images__")
    cropped_images_directory = os.path.join(directory_path, "output/cropped_images")

    if not os.path.exists(cropped_images_directory):
        os.makedirs(cropped_images_directory)

    measure_idx = 1

    print("Starting processing images...")

    # Helper function to extract the numeric part of the filename
    def extract_number(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else float('inf')

    # Sort filenames by the numeric part
    for filename in sorted(os.listdir(images_directory), key=extract_number):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"Processing {filename}..., measure_idx = {measure_idx}")
            image_path = os.path.join(images_directory, filename)

            if filename in ocr_dict:
                if measure_idx != ocr_dict[filename]:
                    print(f"Adjusting measure index for {filename} from {measure_idx} to {ocr_dict[filename]}")
                    measure_idx = ocr_dict[filename]

            islands, ys = find_islands(image_path)
            results[filename] = (islands, measure_idx)
            measure_idx += len(islands) - 1
            
            # Save cropped image
            image = Image.open(image_path)
            image_array = np.array(image)[:image.size[1] // 2, :]
            cropped_image_data = crop_white_edges(image_array)
            cropped_image = Image.fromarray(cropped_image_data)
            cropped_image.save(os.path.join(cropped_images_directory, filename))

    with open(os.path.join(directory_path, 'output/island_locations.json'), 'w') as f:
        json.dump(results, f, indent=4)

    print("Processing completed successfully.")
    
def main():
    parser = argparse.ArgumentParser(description='Process images to extract measures and islands.')
    parser.add_argument('-i', '--input', required=True, help='Path to the input directory containing images and OCR results.')
    args = parser.parse_args()

    input_dir = args.input

    # List all subdirectories in the input directory
    for item in os.listdir(input_dir):

        item_path = os.path.join(input_dir, item)
        item_path_output = os.path.join(input_dir, item, "output")

        # Check if it's a directory and contains the necessary files
        if os.path.isdir(item_path_output):
            subfolder_items = os.listdir(item_path_output)
		
            if 'ocr_results.json' in subfolder_items and '__images__' in subfolder_items:
                print(f"Processing directory: {item_path}")
                report_measures(item_path)

if __name__ == '__main__':
    main()

