import json
import random
import urllib.request

# ✅ Configuration
GITHUB_URL = "https://raw.githubusercontent.com/ragetraxx/glowing-dollop/refs/heads/main/movies.json"
MOVIE_FILE = "movies.json"
PLAY_FILE = "play.json"

def download_movies():
    """Fetch the latest movie list from GitHub and save it locally."""
    print(f"📡 Downloading latest data from GitHub...")
    try:
        with urllib.request.urlopen(GITHUB_URL) as response:
            data = response.read().decode('utf-8')
            # Save it to movies.json so the script can use it
            with open(MOVIE_FILE, "w", encoding="utf-8") as f:
                f.write(data)
            return json.loads(data)
    except Exception as e:
        print(f"❌ Failed to download from GitHub: {e}")
        return []

def update_play_json():
    # 1. Download/Load movies
    all_movies = download_movies()
    
    if not all_movies:
        print(f"❌ Error: Could not get data. Check your internet or URL.")
        return

    # 2. Pick 15 random movies
    count = min(len(all_movies), 15)
    selected_movies = random.sample(all_movies, count)

    # 3. Save to play.json
    with open(PLAY_FILE, "w", encoding="utf-8") as file:
        json.dump(selected_movies, file, indent=4)
    
    print(f"✅ Success! play.json updated with {count} movies from GitHub.")

if __name__ == "__main__":
    update_play_json()
