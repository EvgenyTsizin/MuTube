import json
import requests
from googleapiclient.discovery import build
import argparse

def search_youtube_videos(query, max_results=40, api_key="YOUR_YOUTUBE_API_KEY"):
    youtube = build("youtube", "v3", developerKey=api_key)
    video_list = []
    next_page_token = None

    while len(video_list) < max_results:
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=min(50, max_results - len(video_list)),  # Fetch up to 50 results at a time
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response["items"]:
            video_list.append({
                "title": item["snippet"]["title"],
                "link": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "id": item["id"]["videoId"],
                "description": item["snippet"]["description"]
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break  # No more results

    return video_list

def check_embedding(video_id):
    try:
        response = requests.get(f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json")
        return response.status_code == 200
    except:
        return False

def save_to_json(data, json_file="youtube_videos.json"):
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
def generate_youtube_report(json_file="youtube_videos.json", output_file="youtube_report.html", title="YouTube Video Report"):
    # Open the JSON file and load the data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{json_file}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file '{json_file}' contains invalid JSON.")
        return

    all_videos = data if isinstance(data, list) else []  # Ensure data is a list

    # Start generating the HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            h1 {{
                text-align: center;
            }}
            h2 {{
                margin-top: 40px;
            }}
            ol {{
                margin-left: 20px;
            }}
            li {{
                margin-bottom: 10px;
            }}
            iframe {{
                width: 80%;
                max-width: 640px;
                height: 360px;
                display: block;
                margin: 10px auto;
            }}
            .rating {{
                margin: 10px 0;
            }}
            textarea {{
                width: 100%;
                height: 150px;
                margin-top: 20px;
                display: block;
            }}
        </style>
        <script>
            function saveRatingToLocalStorage(videoId, rating) {{
                localStorage.setItem(videoId, rating);
            }}

            function getRatingFromLocalStorage(videoId) {{
                return localStorage.getItem(videoId);
            }}

            function saveRatings() {{
                const ratings = {{}};
                document.querySelectorAll('li').forEach(li => {{
                    const videoId = li.dataset.videoId;
                    const rating = li.querySelector('input[name="rating-' + videoId + '"]:checked');
                    if (rating) {{
                        ratings[videoId] = rating.value;
                        saveRatingToLocalStorage(videoId, rating.value);
                    }}
                }});
                updateJsonDisplay(ratings);
                console.log("Saved ratings:", ratings);
                alert('Ratings saved successfully!');
            }}

            function loadRatings() {{
                const loadedRatings = {{}};
                document.querySelectorAll('li').forEach(li => {{
                    const videoId = li.dataset.videoId;
                    let savedRating = getRatingFromLocalStorage(videoId);

                    if (!savedRating) {{
                        // If no saved rating, default to "Bad"
                        savedRating = "Bad";
                        saveRatingToLocalStorage(videoId, savedRating);

                        // Automatically select the "Bad" radio button
                        const badRadio = li.querySelector('input[value="Bad"]');
                        if (badRadio) {{
                            badRadio.checked = true;
                        }}
                    }} else {{
                        // Load the saved rating and select the correct radio button
                        const radio = li.querySelector('input[value="' + savedRating + '"]');
                        if (radio) {{
                            radio.checked = true;
                        }}
                    }}

                    loadedRatings[videoId] = savedRating;
                }});
                updateJsonDisplay(loadedRatings);
                console.log("Loaded ratings:", loadedRatings);
            }}

            function updateJsonDisplay(ratings) {{
                const textarea = document.getElementById('json-display');
                textarea.value = JSON.stringify(ratings, null, 2);  // Pretty print the JSON
            }}

            window.onload = loadRatings;
        </script>
    </head>
    <body>
        <h1>{title}</h1>
        <h2>All Videos</h2>
        <ol>
    """

    # Add each video to the HTML content with rating options
    for video in all_videos:
        video_id = video.get("id", "unknown_id")
        video_title = video.get("title", "No Title Provided")
        video_link = video.get("link", "#")

        html_content += f"""
            <li data-video-id="{video_id}">
                <div>{video_title} - <a href="{video_link}" target="_blank">Link</a></div>
                <iframe src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>
                <div class="rating">
                    <label><input type="radio" name="rating-{video_id}" value="Good"> Good</label>
                    <label><input type="radio" name="rating-{video_id}" value="Bad"> Bad</label>
                </div>
            </li>
        """

    # Close the HTML tags and add a textarea for JSON display
    html_content += """
        </ol>
        <button onclick="saveRatings()">Save Ratings</button>
        <button onclick="loadRatings()">Load Ratings</button>
        <textarea id="json-display" readonly></textarea>
    </body>
    </html>
    """

    # Save the HTML content to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML report generated: {output_file}")

# Perform YouTube video search and save results
def process_queries(queries, api_key, max_results=100):
    for idx, query in enumerate(queries, start=1):
        # Search YouTube videos for the query
        video_list = search_youtube_videos(query + " played by pianist", max_results=max_results, api_key=api_key)
        
        # Only include embeddable videos
        embeddable_videos = [video for video in video_list if check_embedding(video["id"])]
        
        # Save results to a JSON file with index suffix
        save_to_json(embeddable_videos, json_file=f"youtube_videos_{idx}.json")
        
        # Generate a YouTube report (optional, implement as needed)
        generate_youtube_report(json_file=f"youtube_videos_{idx}.json", output_file=f"youtube_report_{idx}.html",  title=query)

# Read search queries from file
def read_queries_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


# Main function
if __name__ == "__main__":
    # Argument parser setup
    parser = argparse.ArgumentParser(description="YouTube Video Search")
    parser.add_argument('-f', '--file', required=True, help='File with search queries (one per line)')
    parser.add_argument('-k', '--api_key', required=True, help='YouTube API key')
    args = parser.parse_args()

    # Load queries from the file
    queries = read_queries_from_file(args.file)
    
    # Perform search and save results for each query
    api_key = args.api_key
    process_queries(queries, api_key)