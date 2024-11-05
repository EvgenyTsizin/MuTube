import os
import subprocess
import argparse

def process_youtube_subfolders(base_directory):
    # Traverse through all subfolders of base_directory
    for composition_subfolder in os.listdir(base_directory):
        comp_path = os.path.join(base_directory, composition_subfolder)
        if not os.path.isdir(comp_path) or composition_subfolder == "output":
            continue

        # Traverse through all subfolders inside composition_subfolder
        for youtube_subfolder in os.listdir(comp_path):
            youtube_subfolder_path = os.path.join(comp_path, youtube_subfolder)
            
            if not os.path.isdir(youtube_subfolder_path):
                continue

            frames_folder_path = os.path.join(youtube_subfolder_path, "frames")
            detects_folder_path = os.path.join(youtube_subfolder_path, "detects")

            # Ensure "detects" folder exists
            if not os.path.exists(detects_folder_path):
                os.makedirs(detects_folder_path)

            # Run the detect_np.py script
            if os.path.exists(frames_folder_path) and os.path.isdir(frames_folder_path):
                command = [
                    "python", "detect_np.py",
                    "-i", "../" + frames_folder_path,
                    "-o", "../" + detects_folder_path
                ]
                print(f"running command {str(command)}")
                
                try:
                    subprocess.run(command, check=True, cwd="one-click-dense-pose")
                    print(f"Processed frames in {frames_folder_path}")
                except subprocess.CalledProcessError as e:
                    print(f"Error occurred while processing {frames_folder_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process youtube subfolders.")
    parser.add_argument("-i", "--input", required=True, help="Path to the base directory containing composition subfolders.")
    args = parser.parse_args()

    base_directory = args.input
    process_youtube_subfolders(base_directory)


