import os
import subprocess
import json
import logging
import argparse

# Argument parser
parser = argparse.ArgumentParser(description="Run the YouTube download and processing pipeline.")
parser.add_argument('-i', '--input', type=str, default="Pieces2", help='Path to the pieces directory (default: Pieces2)')
parser.add_argument('-m', '--musescore', type=str, default='/media/simsim314/DATA/Downloads/MuseScore-Studio-4.4.3.242971445-x86_64.AppImage', help='Path to the MuseScore executable (default: /media/simsim314/DATA/Downloads/MuseScore-Studio-4.4.3.242971445-x86_64.AppImage)')
parser.add_argument('-l', '--log', type=str, default="Pieces2/pipeline_log.json", help='Path to the log file (default: Pieces2/pipeline_log.json)')
parser.add_argument('-s', '--site', type=str, default="site", help='Path to the site directory (default: site)')
args = parser.parse_args()

# Define paths
PIECES_DIR = args.input
MUSESCORE_PATH = args.musescore
LOG_FILE_PATH = args.log
SITE_DIR = args.site

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command, log_key):
    """
    Run a shell command and log the result.
    """
    full_log_key = f"{PIECES_DIR}_{log_key}"
    if not is_step_completed(full_log_key):
        try:
            subprocess.run(command, shell=True, check=True)
            mark_step_completed(full_log_key)
            logging.info(f"Successfully completed: {full_log_key}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error while executing: {command}\n{e}")
            exit(1)
    else:
        logging.info(f"Step already completed: {full_log_key}")

def is_step_completed(step):
    """
    Check if a specific step is already completed.
    """
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'r') as f:
            log_data = json.load(f)
            return log_data.get(step, False)
    return False

def mark_step_completed(step):
    """
    Mark a specific step as completed in the log file.
    """
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'r') as f:
            log_data = json.load(f)
    else:
        log_data = {}
    log_data[step] = True
    with open(LOG_FILE_PATH, 'w') as f:
        json.dump(log_data, f, indent=4)

if __name__ == "__main__":
    # Step 1: Download YouTube videos and extract frames + audio
    run_command(f"python Tools/youtube_download_extract.py -i {PIECES_DIR}/pieces_with_names.json", "download_extract")

    # Step 2: Convert mxl files into mp3 using MuseScore
    run_command(f"python Tools/mxls_to_mp3.py -i {PIECES_DIR} -m '{MUSESCORE_PATH}'", "mxls_to_mp3")

    # Step 3: Convert mp3 to wav
    run_command(f"python Tools/mp3_to_wav.py -i {PIECES_DIR}", "mp3_to_wav")

    # Step 4: Sync the pieces using synctoolbox
    if not is_step_completed(f"{PIECES_DIR}_sync_pieces"):
        os.chdir("synctoolbox")
        run_command("python sync_all_pieces.py -d ../Pieces2/youtubes", "sync_pieces")
        os.chdir("..")

    # Step 5: Generate note images from mxl files
    run_command(f"python Tools/save_images_in_folder.py -i {PIECES_DIR}/youtubes -m '{MUSESCORE_PATH}'", "save_images")

    # Step 6: Read numbers from images corresponding to the measure
    if not is_step_completed(f"{PIECES_DIR}_ocr_measures"):
        os.chdir("ocr")
        run_command(f"python ocr_all_subfodlers.py -i ../{PIECES_DIR}/youtubes", "ocr_measures")
        os.chdir("..")

    # Step 7: Generate 1-to-1 correspondence between images and measure indexes
    run_command(f"python Tools/folder_extract_measures.py -i {PIECES_DIR}/youtubes", "extract_measures")

    # Step 8: Copy all data from local analysis to the site folder
    run_command(f"python Tools/copy_compositions_to_site.py -i {PIECES_DIR}/youtubes", "copy_to_site")

    # Step 9: Fill the site data for page 3
    run_command("python Tools/images_to_links.py", "images_to_links")

    # Step 10: Copy image_links.json to image_links_hands_sorted.json if not present in PIECES_DIR
    for root, dirs, files in os.walk(PIECES_DIR):
        if "image_links.json" in files and "image_links_hands_sorted.json" not in files:
            src = os.path.join(root, "image_links.json")
            dst = os.path.join(root, "image_links_hands_sorted.json")
            subprocess.run(f"cp '{src}' '{dst}'", shell=True)
            logging.info(f"Copied image_links.json to image_links_hands_sorted.json in {root}")

    # Step 11: Copy image_links.json to image_links_hands_sorted.json if not present in SITE_DIR
    for root, dirs, files in os.walk(SITE_DIR):
        if "image_links.json" in files and "image_links_hands_sorted.json" not in files:
            src = os.path.join(root, "image_links.json")
            dst = os.path.join(root, "image_links_hands_sorted.json")
            subprocess.run(f"cp '{src}' '{dst}'", shell=True)
            logging.info(f"Copied image_links.json to image_links_hands_sorted.json in {root}")

