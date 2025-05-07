import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Make a folder to save images
os.makedirs("images", exist_ok=True)

res = []

# Function to handle rate-limited API fetching
def fetch_characters(anime_id):
    try:
        r = requests.get(f'https://api.jikan.moe/v4/anime/{anime_id}/characters', timeout=10)
        if r.status_code == 200:
            characters = []
            res1 = r.json()
            for character in res1['data']:
                img_url = character["character"]["images"]["jpg"]["image_url"]
                name = character["character"]["name"]
                safe_name = name.replace('/', '_').replace('\\', '_').replace(' ', '_')
                characters.append((img_url, safe_name))
            print(f"Fetched {len(characters)} characters from Anime ID {anime_id}")
            return characters
        else:
            print(f"Anime ID {anime_id} - Status Code: {r.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching Anime ID {anime_id}: {e}")
        return []

# Function to download images
def download_image(item):
    img_url, name = item
    try:
        img_data = requests.get(img_url, timeout=10).content
        with open(f"images/{name}.jpg", 'wb') as handler:
            handler.write(img_data)
        print(f"Downloaded: {name}")
    except Exception as e:
        print(f"Failed to download {name}: {e}")

# Step 1: Fetch all character images (parallelized)
anime_ids = range(20000 , 30000)  # Increase range as needed, small for testing

# Track time to ensure rate limiting
start_time = time.time()
requests_made = 0

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = []
    for anime_id in anime_ids:
        # Ensure requests per minute limit
        if requests_made >= 45:
            elapsed_time = time.time() - start_time
            if elapsed_time < 45:  # If it's less than a minute, wait
                time_to_wait = 45 - elapsed_time
                print(f"Rate limit reached. Sleeping for {time_to_wait} seconds...")
                time.sleep(time_to_wait)
                start_time = time.time()  # Reset time
                requests_made = 0  # Reset the request counter
        
        futures.append(executor.submit(fetch_characters, anime_id))
        requests_made += 1
        time.sleep(1)  # Slow down to 1 request per second
    
    for future in as_completed(futures):
        characters = future.result()
        res.extend(characters)

print(f"\nTotal characters fetched: {len(res)}\n")

# Step 2: Download all images (parallelized)
with ThreadPoolExecutor(max_workers=20) as executor:
    executor.map(download_image, res)

print(f"\n🎯 Downloaded {len(res)} images successfully!")
