import json
import random
import os

MOVIE_FILE = "movies.json"
PLAY_FILE = "play.json"

def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def update_play_json():
    # 1. Load all available movies from your database
    all_movies = load_json(MOVIE_FILE)
    
    if not all_movies:
        print(f"❌ Error: {MOVIE_FILE} is empty or missing!")
        return

    # 2. Safety check: If you have fewer than 15 movies total, just take them all
    if len(all_movies) <= 15:
        selected_movies = all_movies
        random.shuffle(selected_movies) # Randomize the order
    else:
        # 3. Pick 15 unique random movies
        selected_movies = random.sample(all_movies, 15)

    # 4. Save to play.json
    try:
        with open(PLAY_FILE, "w", encoding="utf-8") as file:
            json.dump(selected_movies, file, indent=4)
        print(f"✅ Success! play.json now contains {len(selected_movies)} random movies.")
    except Exception as e:
        print(f"❌ Failed to save {PLAY_FILE}: {e}")

if __name__ == "__main__":
    update_play_json()
