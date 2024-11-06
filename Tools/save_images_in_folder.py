import os
import re
import zipfile
import subprocess
import argparse
from music21 import environment
import shutil 

# Set the MuseScore paths
env = environment.Environment()

def remove_tempo_information(input_file, output_file, use_zip):
    print("Removing tempo information from:", input_file)
    
    if use_zip:
        temp_dir = "temp_musicxml"
        os.makedirs(temp_dir, exist_ok=True)
        
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the first .xml file in extracted contents
        musicxml_file = next(
            (os.path.join(root, file) for root, _, files in os.walk(temp_dir) for file in files if file.endswith(".xml")),
            None
        )
        
        if not musicxml_file:
            raise FileNotFoundError("No MusicXML (.xml) file found in the .mxl package")

        with open(musicxml_file, 'r', encoding='utf-8') as file:
            xml_content = file.read()

        # Remove tempo information using regex
        direction_regex = re.compile(
            r'<direction[^>]*>\s*<direction-type>(?:(?!</direction>).)*?<sound tempo="[^"]*"/>.*?</direction>', 
            re.DOTALL
        )
        
        modified_xml_content = re.sub(direction_regex, '', xml_content)
        
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(modified_xml_content)
        
        shutil.rmtree(temp_dir)  # Clean up temporary directory
        
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
    os.makedirs(output_dir, exist_ok=True)
    musescore_path = env['musicxmlPath']
    subprocess.run([musescore_path, '-o', os.path.join(output_dir, 'page.png'), mxl_file])

def extract_images(mxl_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    modified_xml_file = os.path.join(output_dir, 'modified.musicxml')
    remove_tempo_information(mxl_file, modified_xml_file, mxl_file.endswith('.mxl'))

    png_dir = os.path.join(output_dir, '__images__')
    os.makedirs(png_dir, exist_ok=True)
    convert_mxl_to_png(modified_xml_file, png_dir)

def process_folder(folder_path):
    # Traverse the folder and subfolders to find all .mxl files
    for subfolder in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, subfolder)
        
        if os.path.isdir(subfolder_path):
            for item in os.listdir(subfolder_path):
                item_path = os.path.join(subfolder_path, item)
                if item.endswith('.mxl'):
                    # Process each .mxl file found
                    output_dir = os.path.join(subfolder_path, 'output')
                    print(f"Processing {item_path}")
                    extract_images(item_path, output_dir)

def main():
    parser = argparse.ArgumentParser(description='Process all MXL files in a folder and its subfolders to remove tempo and extract images.')
    parser.add_argument('-i', '--input', required=True, help='Path to the folder containing MXL files.')
    parser.add_argument('-m', '--muse_path', default=r'C:\Program Files\MuseScore 3\bin\MuseScore3.exe', help='Path to MuseScore executable')
    
    args = parser.parse_args()
    env['musicxmlPath'] = args.muse_path
    env['musescoreDirectPNGPath'] = args.muse_path

    args = parser.parse_args()

    folder_path = args.input
    print(f"Processing folder: {folder_path}")
    process_folder(folder_path)
    print("Process completed successfully for all MXL files.")

if __name__ == '__main__':
    main()

