import os
import re
import argparse
import yt_dlp
import subprocess
import json

def download_youtube_video(url, output_folder, cookies_file):
    yt = yt_dlp.YoutubeDL({
        'cookiefile': cookies_file
    }).extract_info(url, download=False)
    video_title = yt['title']
    video_title_sanitized = re.sub(r'[^\w\s]', '', video_title)
    video_output_path = os.path.join(output_folder, video_title_sanitized)
    if not os.path.exists(video_output_path):
        os.makedirs(video_output_path)

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

def process_youtube_links(links_file, cookies_file):
    with open(links_file, 'r') as file:
        links = file.read().splitlines()
    base_folder = os.path.dirname(links_file)
    output_folder = os.path.join(base_folder, 'youtube_videos')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    processed_data = {}

    for url in links:
        url = url.strip()
        print(url)
        try:
            video_output_path, video_file, audio_file = download_youtube_video(url, output_folder, cookies_file)
            audio_mp3_file = convert_audio_to_mp3(audio_file, video_output_path)
            extract_frames(video_file, video_output_path)

            processed_data[url] = os.path.basename(video_output_path)
        except Exception as e:
            print("Failed to process URL:", url)
            print(e)
    
    json_output_path = os.path.join(base_folder, 'youtube_to_name.json')
    with open(json_output_path, 'w', encoding='utf-8') as json_file:
        json.dump(processed_data, json_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube videos and extract audio and frames.")
    parser.add_argument('-i', '--input', required=True, help='Path to the file containing YouTube links.')
    parser.add_argument('-c', '--cookies', default = "cookies.txt", required=False, help='Path to the cookies file.')

    args = parser.parse_args()
    links_file = args.input
    cookies_file = args.cookies

    process_youtube_links(links_file, cookies_file)
    
    print(f"Processing completed. Videos and extracted content are saved in '{os.path.join(os.path.dirname(links_file), 'youtube_videos')}'.")
