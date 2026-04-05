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
        if not os.path.exists(PLAY_FILE):
            return []
        with open(PLAY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def escape_drawtext(text):
    return text.replace('\\', '\\\\\\\\').replace(':', '\\:').replace("'", "\\'")

def build_ffmpeg_command(url, title, key=None):
    text = escape_drawtext(title)
    
    # ✅ Mimic a legitimate iWantTFC browser session to bypass 404/403
    input_options = [
        "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "-headers", "Referer: https://www.iwanttfc.com/\r\nOrigin: https://www.iwanttfc.com\r\n",
        "-allowed_extensions", "ALL",
        "-reconnect", "1", 
        "-reconnect_at_eof", "1", 
        "-reconnect_streamed", "1", 
        "-reconnect_delay_max", "5",
        "-fflags", "+genpts+discardcorrupt"
    ]
    
    # ✅ DASH decryption key usage
    if key:
        input_options.extend(["-decryption_key", key])

    return [
        "ffmpeg", "-re", "-loglevel", "info",
        *input_options, 
        "-i", url, 
        "-i", OVERLAY,
        "-filter_complex",
        f"[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v];"
        f"[1:v]scale=1280:720[ol];"
        f"[v][ol]overlay=0:0[vo];"
        f"[vo]drawtext=fontfile='{FONT_PATH}':text='{text}':fontcolor=white:fontsize=22:x=40:y=40:shadowcolor=black:shadowx=2:shadowy=2",
        "-r", "29.97", 
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        "-g", "60", "-b:v", "2500k", "-maxrate", "2500k", "-bufsize", "5000k",
        "-pix_fmt", "yuv420p", 
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-f", "flv", RTMP_URL
    ]

def stream_movie(movie):
    title = movie.get("name", "Untitled")
    # Clean URL of any potential JSON artifacts
    url = movie.get("url", "").strip().replace('"', '')
    key = movie.get("key")

    if not url:
        print(f"⚠️ Skipping {title}: No URL found.")
        return

    print(f"🎬 Initializing Stream: {title}")
    command = build_ffmpeg_command(url, title, key)

    try:
        # We capture stderr to monitor for 404s in real-time
        process = subprocess.Popen(command, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        for line in process.stderr:
            if "404 Not Found" in line:
                print(f"❌ 404 Error: Link for '{title}' has expired.")
                process.terminate()
                return
            if "403 Forbidden" in line:
                print(f"🚫 403 Error: Access denied for '{title}'. Check Geoblocking.")
                process.terminate()
                return
            if "frame=" in line:
                # This indicates the stream is actually running
                pass 
            
        process.wait()
    except Exception as e:
        print(f"❌ FFmpeg Error: {e}")

def main():
    print("🚀 PH-Movie Streamer Active...")
    while True:
        playlist = load_playlist()

        if not playlist:
            print("📂 Playlist empty. Refreshing via play.py...")
            os.system("python3 play.py")
            playlist = load_playlist()
            if not playlist:
                time.sleep(RETRY_DELAY)
                continue

        for movie in playlist:
            stream_movie(movie)
            print("⏭️  Transitioning to next title...")
            time.sleep(3)
        
        print("🔄 Batch complete. Fetching new movies...")
        os.system("python3 play.py")

if __name__ == "__main__":
    main()
