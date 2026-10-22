#!/usr/bin/env python3
"""
Sovereign Engine — Rhythm Game Launcher
Builds the TeaVM game via Maven and serves it locally, opening the browser.

Usage:
    python3 launch_rhythm.py
    (or ./launch_rhythm.py if chmod +x is applied)
"""

import os
import sys
import subprocess
import threading
import http.server
import socketserver
import webbrowser
import time

# Configuration
GAME_DIR = "games/teavm-rhythm"
WEBAPP_DIR = os.path.join(GAME_DIR, "target", "webapp")
PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve from the target/webapp directory."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEBAPP_DIR, **kwargs)

    def log_message(self, format, *args):
        # Suppress HTTP server logs to keep the console clean
        pass

def run_server():
    """Starts the HTTP server in a background thread."""
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Serving TeaVM Rhythm at http://localhost:{PORT}")
        print("   Press Ctrl+C to stop the server.")
        httpd.serve_forever()

def main():
    print("🜁∀ Sovereign Engine — TeaVM Rhythm Launcher ∀🜁")
    
    # 1. Verify Maven is installed
    try:
        subprocess.run(["mvn", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Maven (mvn) is not installed or not in PATH.")
        print("   Please install Maven to build the Java/TeaVM source.")
        sys.exit(1)

    # 2. Build the TeaVM Game
    print(f"🔨 Building game in {GAME_DIR} (this may take a moment)...")
    try:
        subprocess.run(["mvn", "clean", "package"], cwd=GAME_DIR, check=True)
    except subprocess.CalledProcessError:
        print("❌ Error: Maven build failed. Check the logs above.")
        sys.exit(1)

    # 3. Verify build output
    if not os.path.exists(os.path.join(WEBAPP_DIR, "index.html")):
        print(f"❌ Error: Build succeeded, but {WEBAPP_DIR}/index.html not found.")
        sys.exit(1)

    # 4. Start the Server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # 5. Open Browser
    time.sleep(1) # Give the server a second to bind
    url = f"http://localhost:{PORT}"
    print(f"🚀 Opening {url} in your default browser...")
    webbrowser.open(url)

    # 6. Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server. Sovereignty preserved.")

if __name__ == "__main__":
    main()
