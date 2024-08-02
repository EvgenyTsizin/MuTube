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
parser.add_argument('-o', '--output_folder', type=str, default='./output_folder', help='Folder to save JSON results')
args = parser.parse_args()

# Ensure output directory exists
os.makedirs(args.output_folder, exist_ok=True)

# Main functions
def recognize_from_image(image_path):
    img_gray = imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = imread(image_path)
    img = img[:512, :512]

    # Predict
    horizontal_list, free_list = detector_predict(detector, img)
    result = recognizer_predict('chinese', lang_list, character, symbol, recognizer, img_gray, horizontal_list[0], free_list[0])

    # Prepare and save result
    result_json = [{
        'word': r[1], 
        'confidence': float(r[2]), 
        'bbox': [int(coord) for coord in r[0]]
    } for r in result]
    
    save_path = os.path.join(args.output_folder, os.path.basename(image_path) + '.json')
    with open(save_path, 'w') as f:
        json.dump(result_json, f)

    print(f'Results saved to {save_path}')

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
