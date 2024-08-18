import os
import json
import argparse

def scan_directories(root_dir):
    images_dict = {}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip the root directory itself
        if dirpath == root_dir:
            continue
        
        # Get the directory name
        dir_name = os.path.basename(dirpath)
        
        # Filter and sort image files
        images = sorted([f for f in filenames if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        
        if images:
            images_dict[dir_name] = images
    
    return images_dict

def save_to_json(data, output_file):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

def main(root_dir, output_file):
    images_dict = scan_directories(root_dir)
    save_to_json(images_dict, output_file)
    print(f'Saved images dictionary to {output_file}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scan directories for images and save to JSON.')
    parser.add_argument('-d', '--directory', default='images', help='Root directory to scan (default: images)')
    parser.add_argument('-o', '--output', default='images.json', help='Output JSON file (default: images.json)')
    args = parser.parse_args()
    
    main(args.directory, args.output)
