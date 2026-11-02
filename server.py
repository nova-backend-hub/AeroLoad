"""
AeroLoad Vercel-Engine Server & Background Auto-Refresh Host
"""

import os
import sys
import io
import warnings
import base64
import requests
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List

# Silence noisy requests warnings
warnings.filterwarnings("ignore")

import scanner
import ipa_parser
import sideload_service
from app_library import get_all_library_apps, get_categories
from refresh_engine import refresh_engine

def get_bundle_dir():
    return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

BUNDLE_DIR = get_bundle_dir()
STATIC_DIR = os.path.join(BUNDLE_DIR, "static")

# Persistent data directory
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AeroLoad")
os.makedirs(DATA_DIR, exist_ok=True)
DOWNLOADS_DIR = os.path.join(DATA_DIR, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start auto-refresh daemon in background thread
    refresh_engine.start_background_daemon()
    yield

app = FastAPI(title="AeroLoad Server", lifespan=lifespan)

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class SideloadRequest(BaseModel):
    ipa_path: str
    name: Optional[str] = "App"
    bundle_id: Optional[str] = ""
    apple_id: Optional[str] = "soliyusef@proton.me"
    udid: Optional[str] = None

class DownloadSideloadRequest(BaseModel):
    download_url: str
    name: str
    bundle_id: Optional[str] = ""
    apple_id: Optional[str] = "soliyusef@proton.me"
    udid: Optional[str] = None

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api/devices")
def api_devices():
    devs = sideload_service.get_connected_devices()
    return {"devices": devs}

@app.get("/api/local-ipas")
def api_local_ipas():
    results = []
    for path in scanner.find_ipas_iterative():
        try:
            info = ipa_parser.parse_ipa(path)
            icon_url = "/static/default_icon.png"
            if info.get("icon_image"):
                buffered = io.BytesIO()
                info["icon_image"].save(buffered, format="PNG")
                icon_b64 = base64.b64encode(buffered.getvalue()).decode()
                icon_url = f"data:image/png;base64,{icon_b64}"
                
            size_mb = round(info.get("size_bytes", 0) / (1024 * 1024), 1)
            results.append({
                "name": info.get("name", "Unknown App"),
                "version": info.get("version", "1.0"),
                "bundle_id": info.get("bundle_id", "com.app"),
                "size_formatted": f"{size_mb} MB",
                "path": path,
                "filename": os.path.basename(path),
                "icon_url": icon_url
            })
        except Exception:
            continue
    return {"ipas": results}

@app.get("/api/app-library")
def api_app_library():
    return {
        "apps": get_all_library_apps(),
        "categories": get_categories()
    }

@app.get("/api/refresh-status")
def api_refresh_status():
    apps = refresh_engine.get_tracked_apps()
    return {"apps": apps}

@app.post("/api/sideload")
def api_sideload(req: SideloadRequest):
    logs = []
    def log_cb(msg: str):
        logs.append(msg)
        print(f"[AeroLoad] {msg}")

    success = sideload_service.sideload_ipa(
        ipa_path=req.ipa_path,
        apple_id=req.apple_id,
        device_udid=req.udid,
        progress_callback=log_cb
    )

    if success:
        refresh_engine.register_installed_app(
            name=req.name,
            bundle_id=req.bundle_id or "com.app",
            version="1.0",
            ipa_path=req.ipa_path,
            apple_id=req.apple_id,
            device_udid=req.udid or "00008110-001C7C163628201E"
        )

    return {"success": success, "logs": logs}

@app.post("/api/download-and-sideload")
def api_download_and_sideload(req: DownloadSideloadRequest):
    logs = []
    def log_cb(msg: str):
        logs.append(msg)
        print(f"[AeroLoad] {msg}")

    log_cb(f"Downloading {req.name} from {req.download_url}...")
    temp_dir = DOWNLOADS_DIR
    target_ipa = os.path.join(temp_dir, f"{req.name.replace(' ', '_')}.ipa")

    try:
        r = requests.get(req.download_url, stream=True, timeout=60)
        if r.status_code == 200:
            with open(target_ipa, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            log_cb(f"✓ Download complete ({round(os.path.getsize(target_ipa)/1024/1024, 2)} MB).")
        else:
            log_cb(f"Error: Download failed with status {r.status_code}")
            return {"success": False, "logs": logs}
    except Exception as e:
        log_cb(f"Download error: {e}")
        return {"success": False, "logs": logs}

    success = sideload_service.sideload_ipa(
        ipa_path=target_ipa,
        apple_id=req.apple_id,
        device_udid=req.udid,
        progress_callback=log_cb
    )

    if success:
        refresh_engine.register_installed_app(
            name=req.name,
            bundle_id=req.bundle_id or req.name,
            version="1.0",
            ipa_path=target_ipa,
            apple_id=req.apple_id,
            device_udid=req.udid or "00008110-001C7C163628201E"
        )

    return {"success": success, "logs": logs}

@app.post("/api/refresh-all")
def api_refresh_all():
    refresh_engine._check_and_refresh()
    return {"status": "Refresh triggered"}

if __name__ == "__main__":
    print("\n=======================================================")
    print("  AEROLOAD VERCEL ENGINE IS RUNNING")
    print("  • Local PC UI:      http://localhost:5050")
    print("  • iPhone Wi-Fi URL:  http://192.168.1.54:5050")
    print("=======================================================\n")
    uvicorn.run(app, host="0.0.0.0", port=5050, log_level="warning")
