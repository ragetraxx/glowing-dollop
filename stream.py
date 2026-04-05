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

def build_ffmpeg_command(url, title, key_id=None, key=None):
    text = escape_drawtext(title)
    
    # ✅ Optimized for stability
    input_options = [
        "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "-headers", "Referer: https://www.iwanttfc.com/\r\n",
        "-reconnect", "1", "-reconnect_at_eof", "1",
        "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
        "-err_detect", "ignore_err"
    ]
    
    # ✅ FIX: For Encrypted DASH, we use -decryption_key for the specific stream
    # Note: Some FFmpeg versions require the format: -decryption_key <HEX_KEY>
    if key:
        input_options.extend(["-decryption_key", key])

    return [
        "ffmpeg", "-re", "-fflags", "+nobuffer+genpts", "-flags", "low_delay", 
        *input_options, "-i", url, "-i", OVERLAY,
        "-filter_complex",
        f"[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v];"
        f"[1:v]scale=1280:720[ol];"
        f"[v][ol]overlay=0:0[vo];"
        f"[vo]drawtext=fontfile='{FONT_PATH}':text='{text}':fontcolor=white:fontsize=20:x=35:y=35",
        "-r", "29.97", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        "-g", "60", "-b:v", "2500k", "-maxrate", "2500k", "-bufsize", "5000k",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-f", "flv", RTMP_URL
    ]

def stream_movie(movie):
    title = movie.get("name", "Untitled")
    url = movie.get("url", "").replace('\\"', '').replace('"', '').strip()
    key = movie.get("key")
    key_id = movie.get("keyId")

    if not url:
        return

    print(f"🎬 Now streaming: {title}")
    command = build_ffmpeg_command(url, title, key_id, key)

    try:
        # We use stderr=subprocess.STDOUT to see errors in the console
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        
        for line in process.stderr:
            print(f"DEBUG: {line.strip()}") # Watch this to see why it fails
            if "403 Forbidden" in line:
                print(f"🚫 403 Forbidden! Skipping: {title}")
                process.kill()
                return
            if "Error" in line or "Invalid data" in line:
                if "decryption" in line.lower():
                    print(f"🔑 Decryption error on: {title}")
        process.wait() 
    except Exception as e:
        print(f"❌ FFmpeg crashed: {e}")

def main():
    print("🚀 Streamer Started...")
    while True:
        playlist = load_playlist()

        if not playlist:
            print("📂 play.json is empty. Running play.py...")
            os.system("python3 play.py")
            playlist = load_playlist()
            if not playlist:
                time.sleep(RETRY_DELAY)
                continue

        for movie in playlist:
            stream_movie(movie)
            print("⏭️  Short break before next movie...")
            time.sleep(5)
        
        print("🔄 15 movies finished. Refreshing...")
        os.system("python3 play.py")

if __name__ == "__main__":
    main()
