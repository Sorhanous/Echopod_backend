import requests
from bs4 import BeautifulSoup
import re
import json

def extract_video_ids_from_youtube(youtube_url):
    def extract_video_ids(content):
        video_ids = []
        try:
            data = json.loads(content)
            video_ids.extend(find_video_ids(data))
        except json.JSONDecodeError:
            video_ids.extend(re.findall(r'"videoId"\s*:\s*"([^"]+)"', content))
        
        return list(set(video_ids))  # Remove duplicates

    def find_video_ids(obj):
        video_ids = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "videoId" and isinstance(value, str):
                    video_ids.append(value)
                elif isinstance(value, (dict, list)):
                    video_ids.extend(find_video_ids(value))
        elif isinstance(obj, list):
            for item in obj:
                video_ids.extend(find_video_ids(item))
        return video_ids

    # Send a GET request to the YouTube URL
    response = requests.get(youtube_url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Convert the parsed HTML content to a string
    html_content = soup.prettify()

    # Delete top 2/3 of the HTML content
    trimmed_content = html_content[len(html_content) // 3:]

    # Use regex to find the secondaryResults parameter and return everything after it
    match = re.search(r'("secondaryResults":\s*{.*)', trimmed_content, re.DOTALL)

    if match:
        secondary_results = match.group(1)
        
        # Extract video IDs
        video_ids = extract_video_ids(secondary_results)
        
        return video_ids
    else:
        return []
