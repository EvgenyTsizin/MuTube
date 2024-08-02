import os
import json
import argparse
import numpy as np
from PIL import Image

def crop_white_edges(image_data):
    white_threshold = 250
    first_non_white_row, last_non_white_row = None, None

    for i in range(image_data.shape[0]):
        if np.any(image_data[i, :] < white_threshold):
            if first_non_white_row is None:
                first_non_white_row = i
            last_non_white_row = i

    if first_non_white_row is not None and last_non_white_row is not None:
        return image_data[first_non_white_row:last_non_white_row + 1, :]
    return image_data

def find_islands(image_path, black_threshold=150, min_length=220, skip_pixels=4):
    factor = 5
    min_length /= factor
    min_length -= 2

    image = Image.open(image_path).convert('L')
    image_array = np.array(image)
    new_height, new_width = image_array.shape[0] // factor, image_array.shape[1] // factor

    resized_array = np.zeros((new_height, new_width), dtype=image_array.dtype)
    for i in range(new_height):
        for j in range(new_width):
            block = image_array[i * factor:(i + 1) * factor, j * factor:(j + 1) * factor]
            resized_array[i, j] = np.min(block)

    image_data = crop_white_edges(resized_array)
    
    island_columns, ys = set(), []
    col, first_center = 0, None
    
    while col < image_data.shape[1]:
        current_count, h = 0, image_data.shape[0]
    
        for row in range(h):
            if image_data[row, col] < black_threshold:
                current_count += 1
            else:
                if current_count >= min_length:
                    is_valid = False 
                    if first_center is None:
                        first_center = row - current_count * 0.5
                        ys = [row - current_count, row]
                        is_valid = True
                    else:
                        cur_center = row - current_count * 0.5
                        if abs(cur_center - first_center) < 0.003 * h:
                            is_valid = True
                    
                    if is_valid:
                        island_columns.add(factor * col)
                        col += skip_pixels
                        break
                current_count = 0
        col += 1
        
    island_columns = sorted(list(island_columns))
    if island_columns and island_columns[-1] < 0.9 * image_data.shape[1] * factor:
        island_columns.append(factor * image_data.shape[1] - 1)
    
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
    json_file_path = os.path.join(directory_path, 'ocr_results.json')
    ocr_dict = ocr_measures(json_file_path)
    results = {}
    images_directory = os.path.join(directory_path, "images")
    cropped_images_directory = os.path.join(directory_path, "cropped_images")

    if not os.path.exists(cropped_images_directory):
        os.makedirs(cropped_images_directory)

    measure_idx = 1

    print("Starting processing images...")
    
    for filename in os.listdir(images_directory):
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

    with open(os.path.join(directory_path, 'island_locations.json'), 'w') as f:
        json.dump(results, f, indent=4)

    print("Processing completed successfully.")

def main():
    parser = argparse.ArgumentParser(description='Process images to extract measures and islands.')
    parser.add_argument('-i', '--input', required=True, help='Path to the input directory containing images and OCR results.')
    args = parser.parse_args()

    input_dir = args.input
    report_measures(input_dir)

if __name__ == '__main__':
    main()
