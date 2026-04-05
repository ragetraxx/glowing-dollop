import json
import random
import os

# ✅ Configuration
MOVIE_FILE = "movies.json"
PLAY_FILE = "play.json"

def load_json(filename):
    """Load JSON data from a local file."""
    if not os.path.exists(filename):
        print(f"❌ Error: {filename} not found in the current folder.")
        return []
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"❌ Failed to parse {filename}: {e}")
        return []

def update_play_json():
    # 1. Load movies from the local movies.json
    all_movies = load_json(MOVIE_FILE)
    
    if not all_movies:
        print("❌ Error: No movies found to select from.")
        return

    # 2. Randomly select 15 movies (or all if total < 15)
    count = min(len(all_movies), 15)
    selected_movies = random.sample(all_movies, count)

    # 3. Save the selection to play.json
    try:
        with open(PLAY_FILE, "w", encoding="utf-8") as file:
            json.dump(selected_movies, file, indent=4)
        print(f"✅ play.json created/updated with {count} random movies.")
    except Exception as e:
        print(f"❌ Failed to save {PLAY_FILE}: {e}")

if __name__ == "__main__":
    update_play_json()
