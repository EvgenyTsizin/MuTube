import argparse
import os
import subprocess
from music21 import converter, tempo, meter, environment
import zipfile
import re
import numpy as np
import shutil

env = environment.Environment()

def remove_tempo_information(input_file, output_file):
    print("remove_tempo_information", input_file, output_file)
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
    
    shutil.rmtree(temp_dir) 

def convert_mxl_to_mp3(mxl_path):

    modified_xml_file = mxl_path[:-4] + '_modified.musicxml'
    
    # Define the output path by replacing the .mxl extension with .mp3
    mp3_path = mxl_path[:-4] + '.mp3'

    if os.path.exists(mp3_path):
        return 
        
    remove_tempo_information(mxl_path, modified_xml_file)    
    # Construct the MuseScore command to convert the file
    command = [env['musicxmlPath'], modified_xml_file, '-o', mp3_path, '-R']
    
    # Execute the command
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error during conversion:")
        print(result.stderr)
    else:
        print(f"Conversion completed. MP3 file saved at '{mp3_path}'.")

def process_folder(input_folder):

    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith(".mxl"):
                mxl_path = os.path.join(root, file)
                convert_mxl_to_mp3(mxl_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process MusicXML files in a folder and convert to mp3.')
    parser.add_argument('-i', '--input', required=True, help='Input folder containing .mxl files')
    parser.add_argument('-m', '--muse_path', default=r'C:\Program Files\MuseScore 3\bin\MuseScore3.exe', help='Path to MuseScore executable')
    
    args = parser.parse_args()
    env['musicxmlPath'] = args.muse_path
    env['musescoreDirectPNGPath'] = args.muse_path

    process_folder(args.input)
