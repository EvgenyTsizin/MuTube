import argparse
import os
import subprocess
from music21 import converter, tempo, meter, environment
import zipfile
import re
import numpy as np
import shutil 

env = environment.Environment()
env['musicxmlPath'] = r'C:\Program Files\MuseScore 3\bin\MuseScore3.exe'  
env['musescoreDirectPNGPath'] = r'C:\Program Files\MuseScore 3\bin\MuseScore3.exe'  

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
    remove_tempo_information(mxl_path, modified_xml_file)

    # Define the output path by replacing the .mxl extension with .mp3
    mp3_path = mxl_path[:-4] + '.mp3'

    # Construct the MuseScore command to convert the file
    command = [env['musicxmlPath'], modified_xml_file, '-o', mp3_path, '-R']
    
    # Execute the command
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error during conversion:")
        print(result.stderr)
    else:
        print(f"Conversion completed. MP3 file saved at '{mp3_path}'.")

def main():
    parser = argparse.ArgumentParser(description="Convert MusicXML (MXL) to MP3 using MuseScore.")
    parser.add_argument('-i', '--input', required=True, help='Path to the input MXL file.')
   
    args = parser.parse_args()

    # Load the score to determine the time signature
    score = converter.parse(args.input)
    time_signature = score.getTimeSignatures()[0]
    beats_per_measure = time_signature.numerator
    
    # Convert the MXL file to MP3 with the calculated tempo
    convert_mxl_to_mp3(args.input)

if __name__ == "__main__":
    main()
