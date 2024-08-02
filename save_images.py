import os
import re
import zipfile
import subprocess
import argparse
from PIL import Image
import numpy as np
from music21 import environment

# Set the MuseScore paths
env = environment.Environment()
env['musicxmlPath'] = r'C:\Program Files\MuseScore 3\bin\MuseScore3.exe'
env['musescoreDirectPNGPath'] = r'C:\Program Files\MuseScore 3\bin\MuseScore3.exe'

def remove_tempo_information(input_file, output_file, use_zip):
    if use_zip:
        temp_dir = "temp_musicxml"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        musicxml_file = None
        for root_dir, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".xml"):
                    musicxml_file = os.path.join(root_dir, file)
                    break
            if musicxml_file:
                break

        if not musicxml_file:
            raise FileNotFoundError("No MusicXML (.xml) file found in the .mxl package")

        with open(musicxml_file, 'r', encoding='utf-8') as file:
            xml_content = file.read()

        direction_regex = re.compile(
            r'<direction[^>]*>\s*<direction-type>(?:(?!</direction>).)*?<sound tempo="[^"]*"/>.*?</direction>', 
            re.DOTALL
        )
        
        modified_xml_content = re.sub(direction_regex, '', xml_content)
        
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(modified_xml_content)
    else:
        with open(input_file, 'r', encoding='utf-8') as file:
            xml_content = file.read()
        
        direction_regex = re.compile(
            r'<direction[^>]*>\s*<direction-type>(?:(?!</direction>).)*?<sound tempo="[^"]*"/>.*?</direction>', 
            re.DOTALL
        )

        modified_xml_content = re.sub(direction_regex, '', xml_content)
        
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(modified_xml_content)

def convert_mxl_to_png(mxl_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    musescore_path = env['musicxmlPath']
    subprocess.run([musescore_path, '-o', os.path.join(output_dir, 'page.png'), mxl_file])

def extract_images(mxl_file, output_dir):
    modified_xml_file = os.path.join(output_dir, 'modified.musicxml')
    remove_tempo_information(mxl_file, modified_xml_file, mxl_file.endswith('.mxl'))

    png_dir = os.path.join(output_dir, 'images')
    convert_mxl_to_png(modified_xml_file, png_dir)

def main():
    parser = argparse.ArgumentParser(description='Process MXL file to remove tempo and extract images.')
    parser.add_argument('-i', '--input', required=True, help='Path to the input MXL file.')
    args = parser.parse_args()

    input_file = args.input
    base_dir = os.path.dirname(input_file)
    
    extract_images(input_file, base_dir)
    print("Process completed successfully.")

if __name__ == '__main__':
    main()
