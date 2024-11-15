import os
import json
import random

import numpy as np
from PIL import Image
import re
import cv2
import matplotlib.pyplot as plt
import matplotlib

DEBUG = True

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

def resize_and_crop_image(image_path, factor):
    image = Image.open(image_path).convert('L')
    image_array = np.array(image)
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
    print(x_vals)
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

def extract_cropped_rescaled_images(image_path, island_columns, factor=5):
    image = Image.open(image_path)
    image_array = np.array(image)
    cropped_images = []

    for i in range(len(island_columns) - 1):
        left = island_columns[i]
        right = island_columns[i + 1]
        cropped_image_array = image_array[:, left:right]
        cropped_image = Image.fromarray(cropped_image_array)

        # Resize the cropped image to the original size of the height
        original_height = image_array.shape[0]
        rescaled_image = cropped_image.resize((right - left, original_height), Image.LANCZOS)
        cropped_images.append(rescaled_image)

    return cropped_images

def main():
    def all_images_in_music21(base_dir):
        # Traverse through the base directory
        all = []
        for root, dirs, files in os.walk(base_dir):
            # Check if the folder is named '__images__'
            if os.path.basename(root) == '__images__':
                for file in files:
                    if file.endswith(('.png', '.jpg', '.jpeg')):  # Adjust image extensions if needed
                        image_path = os.path.join(root, file)
                        try:
                            all.append(image_path)
                        except Exception as e:
                            print(f"Failed to process {image_path}: {e}")
        return all

    # Set your base directory for the music21 project here
    base_directory = '/media/simsim314/DATA/Github/music21/Pieces2/youtubes/G Minor Bach'
    all_images = all_images_in_music21(base_directory)
    random.seed(1234)
    #random.shuffle(all_images)
    for image_path in all_images:
        islands, ys = find_islands(image_path)

if __name__ == '__main__':
    main()
