import os
import json
import subprocess
import time

# ✅ Configuration
PLAY_FILE = "play.json"
RTMP_URL = os.getenv("RTMP_URL")
OVERLAY = os.path.abspath("overlay.png")
FONT_PATH = os.path.abspath("Roboto-Black.ttf")
RETRY_DELAY = 60
PREBUFFER_SECONDS = 5

if not RTMP_URL:
    print("❌ ERROR: RTMP_URL environment variable is not set!")
    exit(1)

def load_playlist():
    try:
        with open(PLAY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def escape_drawtext(text):
    return text.replace('\\', '\\\\\\\\').replace(':', '\\:').replace("'", "\\'")

def build_ffmpeg_command(url, title, key=None):
    text = escape_drawtext(title)
    
    # ✅ Optimized for stability and decryption
    input_options = [
        "-user_agent", "VLC/3.0.18 LibVLC/3.0.18",
        "-headers", "Referer: https://hollymoviehd.cc\r\n",
        "-reconnect", "1", "-reconnect_at_eof", "1",
        "-reconnect_streamed", "1", "-reconnect_delay_max", "5"
    ]
    
    if key:
        input_options.extend(["-decryption_key", key])

    return [
        "ffmpeg", "-re", "-fflags", "+nobuffer", "-flags", "low_delay", "-threads", "1",
        "-ss", str(PREBUFFER_SECONDS), *input_options, "-i", url, "-i", OVERLAY,
        "-filter_complex",
        f"[0:v]scale=1280:720:flags=lanczos,unsharp=5:5:0.8:5:5:0.0[v];"
        f"[1:v]scale=1280:720[ol];"
        f"[v][ol]overlay=0:0[vo];"
        f"[vo]drawtext=fontfile='{FONT_PATH}':text='{text}':fontcolor=white:fontsize=20:x=35:y=35",
        "-r", "29.97", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        "-g", "60", "-b:v", "1500k", "-maxrate", "2000k", "-bufsize", "2000k",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-f", "flv", RTMP_URL
    ]

def stream_movie(movie):
    title = movie.get("name", "Untitled")
    # Clean the URL from trailing quotes found in your JSON data
    url = movie.get("url", "").replace('\\"', '').replace('"', '').strip()
    key = movie.get("key")

    if not url:
        return

    print(f"🎬 Now streaming: {title}")
    command = build_ffmpeg_command(url, title, key)

    try:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        for line in process.stderr:
            if "403 Forbidden" in line:
                print(f"🚫 403 Forbidden! Skipping: {title}")
                process.kill()
                return
        process.wait() 
    except Exception as e:
        print(f"❌ FFmpeg crashed: {e}")

def main():
    print("🚀 Streamer Started...")
    while True:
        # 1. Load the current 15 movies
        playlist = load_playlist()

        # 2. If play.json is missing or empty, trigger play.py
        if not playlist:
            print("📂 play.json is empty. Running play.py to generate 15 movies...")
            os.system("python3 play.py")
            playlist = load_playlist()
            if not playlist:
                time.sleep(RETRY_DELAY)
                continue

        # 3. Stream the movies one by one
        for movie in playlist:
            stream_movie(movie)
            print("⏭️  Short break before next movie...")
            time.sleep(5)
        
        # 4. Once the 15 movies are done, run play.py again for a NEW batch
        print("🔄 15 movies finished. Generating a new random batch...")
        os.system("python3 play.py")

if __name__ == "__main__":
    main()
