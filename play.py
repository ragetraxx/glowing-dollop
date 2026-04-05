import json
import random
import os

MOVIE_FILE = "movies.json"
PLAY_FILE = "play.json"

def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def update_play_json():
    all_movies = load_json(MOVIE_FILE)
    previously_played = load_json(PLAY_FILE)

    if not all_movies:
        print("❌ Error: movies.json is empty or not found.")
        return

    # Extract names to compare easily
    played_names = {m.get("name") for m in previously_played}
    
    # Filter for movies not in the current play.json
    available_movies = [m for m in all_movies if m.get("name") not in played_names]

    # Reset if we run out of new movies
    if len(available_movies) < 15:
        print("♻️  Cycle complete or not enough new movies. Resetting pool...")
        available_movies = all_movies

    # Select 15 random movies
    selected_count = min(len(available_movies), 15)
    selected_movies = random.sample(available_movies, selected_count)

    with open(PLAY_FILE, "w", encoding="utf-8") as file:
        json.dump(selected_movies, file, indent=4)
    
    print(f"✅ play.json updated with {selected_count} movies.")

if __name__ == "__main__":
    update_play_json()
