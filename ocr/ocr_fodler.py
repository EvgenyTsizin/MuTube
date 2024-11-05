import sys
import os
import json
import cv2
import argparse
import numpy as np
import ailia

# Import original modules
sys.path.append('util')
from image_utils import imread
from model_utils import check_and_download_models

from easyocr_utils import *

# Parameters
DETECTOR_MODEL_PATH = 'detector_craft.onnx.prototxt'
DETECTOR_WEIGHT_PATH = 'detector_craft.onnx'
RECOGNIZER_MODEL_PATH = 'recognizer_zh_sim_g2.onnx.prototxt'
RECOGNIZER_WEIGHT_PATH = 'recognizer_zh_sim_g2.onnx'
REMOTE_PATH = 'https://storage.googleapis.com/ailia-models/easyocr/'

# Argument parser
parser = argparse.ArgumentParser(description='Process images for OCR and output JSON metadata.')
parser.add_argument('-i', '--input_folder', type=str, default='./input_folder', help='Folder containing images to process')
args = parser.parse_args()

# Main functions
all_results = []  # List to store results from all images

def recognize_from_image(image_path):
    img_gray = imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = imread(image_path)
    img = img[:768, :512]

    # Predict
    horizontal_list, free_list = detector_predict(detector, img)
    result = recognizer_predict('chinese', lang_list, character, symbol, recognizer, img_gray, horizontal_list[0], free_list[0])

    filtered_results = [{
        'image': os.path.basename(image_path),
        'word': r[1]
    } for r in result if r[1].isdigit() and float(r[2]) > 0.95]

    if filtered_results:
        print(f'Recognized digits with high confidence in {image_path}: {filtered_results}')
    
    all_results.extend(filtered_results)

if __name__ == '__main__':
    # Check and download models
    check_and_download_models(DETECTOR_WEIGHT_PATH, DETECTOR_MODEL_PATH, REMOTE_PATH)
    check_and_download_models(RECOGNIZER_WEIGHT_PATH, RECOGNIZER_MODEL_PATH, REMOTE_PATH)

    # Initialize models
    detector = ailia.Net(DETECTOR_MODEL_PATH, DETECTOR_WEIGHT_PATH, env_id=0)
    recognizer = ailia.Net(RECOGNIZER_MODEL_PATH, RECOGNIZER_WEIGHT_PATH, env_id=0)
    lang_list = ['ch_sim', 'en']
    character = recognition_models['zh_sim_g2']['characters']
    symbol = recognition_models['zh_sim_g2']['symbols']

    # Process each image in the input folder
    for file_name in os.listdir(args.input_folder):
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(args.input_folder, file_name)
            recognize_from_image(image_path)
            
    # Determine the output folder
    output_folder = os.path.dirname(os.path.abspath(args.input_folder))
    os.makedirs(output_folder, exist_ok=True)

    # Save all results into one JSON file
    with open(os.path.join(output_folder, 'all_results.json'), 'w') as f:
        json.dump(all_results, f)

    print(f'All results saved to {os.path.join(output_folder, "ocr_results.json")}')
