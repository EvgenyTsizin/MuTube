import os
import re
import argparse
import yt_dlp
import subprocess
import json

def sanitize_folder_name(name):
    """Sanitize folder names by removing or replacing invalid characters."""
    return re.sub(r'[<>:"/\\|?*()\'"]', '', name)
def get_unique_folder_name(base_folder, folder_name):
    """Generate a unique folder name by adding a suffix if the folder already exists."""
    original_folder_name = folder_name
    counter = 1
    while os.path.exists(os.path.join(base_folder, folder_name)):
        folder_name = f"{original_folder_name} V{counter}"
        counter += 1
    return folder_name

def download_youtube_video(url, output_folder, cookies_file):
    yt = yt_dlp.YoutubeDL({
        'cookiefile': cookies_file
    }).extract_info(url, download=False)
    video_title = yt['title']
    video_title_sanitized = sanitize_folder_name(video_title)

    # Ensure unique folder name
    video_output_folder = get_unique_folder_name(output_folder, video_title_sanitized)
    video_output_path = os.path.join(output_folder, video_output_folder)
    
    os.makedirs(video_output_path)  # Create the folder
    
    video_opts = {
        'format': 'bestvideo[ext=mp4]',
        'outtmpl': os.path.join(video_output_path, 'video.%(ext)s'),
        'cookiefile': cookies_file,
    }

    audio_opts = {
        'format': 'bestaudio[ext=m4a]',
        'outtmpl': os.path.join(video_output_path, 'audio.%(ext)s'),
        'cookiefile': cookies_file,
    }

    print("Loading stream...")
    with yt_dlp.YoutubeDL(video_opts) as ydl:
        ydl.download([url])

    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        ydl.download([url])
        
    video_file = os.path.join(video_output_path, 'video.mp4')
    audio_file = os.path.join(video_output_path, 'audio.m4a')
    
    output_file = os.path.join(video_output_path, 'output.mp4')
    print("Merging video and audio...")
    subprocess.run(['ffmpeg', '-i', video_file, '-i', audio_file, '-c', 'copy', output_file], check=True)

    return video_output_path, output_file, audio_file

def convert_audio_to_mp3(audio_file, output_path):
    audio_mp3_file = os.path.join(output_path, "audio.mp3")
    subprocess.run(['ffmpeg', '-y', '-i', audio_file, audio_mp3_file], check=True)
    return audio_mp3_file

def extract_frames(video_file, output_path, interval=0.5):
    frames_folder = os.path.join(output_path, "frames")
    if not os.path.exists(frames_folder):
        os.makedirs(frames_folder)
    subprocess.run(['ffmpeg', '-y', '-i', video_file, '-vf', f'fps=1/{interval}', f'{frames_folder}/frame_%04d.jpg'], check=True)

def process_json(json_file, cookies_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    base_folder = os.path.dirname(json_file)
    output_folder = os.path.join(base_folder, 'youtubes')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    processed_data = {}

    for item in data:
        mxl_file = item[0]
        search_term = sanitize_folder_name(item[1])
        youtube_suffixes = item[2]
        
        mxl_file_path = os.path.join(base_folder, mxl_file)
        search_output_folder = os.path.join(output_folder, search_term)
        
        if not os.path.exists(search_output_folder):
            os.makedirs(search_output_folder)
        
        for suffix in youtube_suffixes:
            url = f"https://www.youtube.com/watch?v={suffix}"
            print(f"Processing URL: {url}")
            try:
                video_output_path, video_file, audio_file = download_youtube_video(url, search_output_folder, cookies_file)
                audio_mp3_file = convert_audio_to_mp3(audio_file, video_output_path)
                extract_frames(video_file, video_output_path)

                processed_data[url] = os.path.basename(video_output_path)
            except Exception as e:
                print(f"Failed to process URL: {url}")
                print(e)

    json_output_path = os.path.join(base_folder, 'youtube_to_name.json')
    with open(json_output_path, 'w', encoding='utf-8') as json_file:
        json.dump(processed_data, json_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube videos and extract audio and frames from a JSON file.")
    parser.add_argument('-i', '--input', required=True, help='Path to the JSON file containing YouTube data.')
    parser.add_argument('-c', '--cookies', default="cookies.txt", required=False, help='Path to the cookies file.')

    args = parser.parse_args()
    json_file = args.input
    cookies_file = args.cookies

    process_json(json_file, cookies_file)

    print(f"Processing completed. Videos and extracted content are saved in '{os.path.join(os.path.dirname(json_file), 'youtubes')}'.")
