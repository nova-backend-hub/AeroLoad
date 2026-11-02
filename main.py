"""
AeroLoad Desktop Application Launcher
Self-contained, bundled Vercel Engine & Local Host
"""

import os
import sys
import time
import socket
import threading
import subprocess
import webbrowser
import multiprocessing
import urllib.request

# Required for frozen Windows executables
multiprocessing.freeze_support()

# Persistent data directory
data_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AeroLoad")
os.makedirs(data_dir, exist_ok=True)
log_file_path = os.path.join(data_dir, "aeroload.log")

class LoggerWriter:
    def __init__(self, filename):
        try:
            self.f = open(filename, "a", encoding="utf-8", buffering=1)
        except Exception:
            self.f = None
    def write(self, message):
        if self.f and message:
            try:
                self.f.write(message)
                self.f.flush()
            except Exception:
                pass
    def flush(self):
        if self.f:
            try:
                self.f.flush()
            except Exception:
                pass

logger = LoggerWriter(log_file_path)
sys.stdout = logger
sys.stderr = logger

import uvicorn
import server

def get_bundle_dir():
    return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

def launch_ui(url: str):
    """Launch Microsoft Edge in dedicated App Window mode, falling back to default browser."""
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
    ]
    edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)

    if edge_exe:
        try:
            cmd = [edge_exe, f"--app={url}", "--window-size=1200,860"]
            return subprocess.Popen(cmd)
        except Exception as e:
            print(f"[AeroLoad] Edge launch error: {e}")

    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[AeroLoad] Webbrowser error: {e}")
    return None

def find_available_port(start_port: int = 5050, max_tries: int = 10) -> int:
    """Find a bindable port, reusing existing AeroLoad port if already responsive."""
    for port in range(start_port, start_port + max_tries):
        # 1. Check if AeroLoad is already active on this port
        try:
            with urllib.request.urlopen(f"http://localhost:{port}/api/devices", timeout=0.5) as r:
                if r.status == 200:
                    return port
        except Exception:
            pass

        # 2. Check if port can be bound
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    return start_port

def main():
    print("\n==========================================")
    print(f"[AeroLoad] Starting at {time.ctime()}...")

    # 1. Check if AeroLoad is already running on port 5050
    try:
        with urllib.request.urlopen("http://localhost:5050/api/devices", timeout=0.6) as r:
            if r.status == 200:
                print("[AeroLoad] Existing background instance active on port 5050. Opening UI...")
                launch_ui("http://localhost:5050")
                sys.exit(0)
    except Exception:
        pass

    # 2. Select port (5050 default, or next free port)
    port = find_available_port(5050)
    print(f"[AeroLoad] Selected port {port}")

    # 3. Start server in daemon thread
    def run_server():
        try:
            config = uvicorn.Config(server.app, host="0.0.0.0", port=port, log_config=None)
            srv = uvicorn.Server(config)
            srv.run()
        except Exception as e:
            print(f"[AeroLoad] Server error: {e}")

    srv_thread = threading.Thread(target=run_server, daemon=True)
    srv_thread.start()

    # 4. Wait for server readiness
    url = f"http://localhost:{port}"
    ready = False
    for _ in range(50):
        time.sleep(0.15)
        try:
            with urllib.request.urlopen(f"{url}/api/devices", timeout=0.6) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            pass

    if not ready:
        print("[AeroLoad] Warning: Server response timed out, opening UI anyway...")

    print(f"[AeroLoad] Server ready on {url}. Launching window...")
    launch_ui(url)

    # 5. Keep process alive so background refresh daemon functions
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[AeroLoad] Stopped.")

if __name__ == "__main__":
    main()
