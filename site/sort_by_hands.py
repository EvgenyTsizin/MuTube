import json
import os
import math

folder = "timings/F.Liszt_Dante_Sonata_S.161_No.7/"
# Load JSON files
with open(folder + 'image_links.json', 'r') as f:
    image_links = json.load(f)

with open(folder + 'youtube_to_detect.json', 'r') as f:
    youtube_to_detect = json.load(f)

with open(folder + 'hands_frames.json', 'r') as f:
    hands_frames = json.load(f)

# Create a mapping from YouTube link and timing to hands detection count
hand_counts = {}
for file_path, count in hands_frames.items():
    video_path = file_path.split("\\")[2]  # Extract the video name
    video_name = video_path.replace("Detects\\youtube_videos\\", "").replace("\\frames", "")
    video_name = video_name.split("\\")[0]
    youtube_link = next((key for key, value in youtube_to_detect.items() if value.startswith(video_name)), None)
    frame_num = int(file_path.split("_")[-1].split(".")[0])
    hand_counts[(youtube_link, frame_num)] = count

# Create a new image_links dictionary with sorted hands data
new_image_links = {}
for image, videos in image_links.items():
    new_videos = []
    for video in videos:
        youtube_link = video['youtube_link']
        timing = math.floor(video['timing']) * 2  # Floor the timing and multiply by 2
        hand_count = 0
        for i in range(12):  # Sum up the next 12 frames
            hand_count += hand_counts.get((youtube_link, timing + i), 0)
        new_videos.append((youtube_link, video['timing'], hand_count))
    # Sort by hand_count and remove the hand_count from the data
    new_image_links[image] = [{"youtube_link": youtube_link, "timing": timing}
                              for youtube_link, timing, _ in sorted(new_videos, key=lambda x: x[2], reverse=True)]

# Save to a new JSON file
with open(folder + 'image_links_hands_sorted.json', 'w') as f:
    json.dump(new_image_links, f, indent=4)
