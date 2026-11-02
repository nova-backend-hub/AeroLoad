"""
AeroLoad 7-Day Auto-Refresh Engine
Tracks sideloaded app lifespans and automatically refreshes them over USB or Wi-Fi.
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Callable

def get_bundle_dir():
    return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

BUNDLE_DIR = get_bundle_dir()
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AeroLoad")
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "installed_apps.json")

class RefreshEngine:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback or print
        self.running = False
        self.apps: Dict[str, Dict] = self._load_data()
        self._ensure_initial_apps()

    def _load_data(self) -> Dict[str, Dict]:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Check scratch directory fallback to preserve existing records
        scratch_json = r"C:\Users\dawoo\.gemini\antigravity\scratch\AeroLoad\installed_apps.json"
        if os.path.exists(scratch_json):
            try:
                with open(scratch_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    with open(DATA_FILE, "w", encoding="utf-8") as out_f:
                        json.dump(data, out_f, indent=2)
                    return data
            except Exception:
                pass
                
        return {}

    def _save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.apps, f, indent=2)
        except Exception as e:
            print(f"Error saving refresh database: {e}")

    def _ensure_initial_apps(self):
        """Seed initial apps like StillClock if already present."""
        if "com.dawood.StillClock" not in self.apps:
            now_str = datetime.now(timezone.utc).isoformat()
            self.apps["com.dawood.StillClock"] = {
                "name": "StillClock",
                "bundle_id": "com.dawood.StillClock",
                "version": "1.0.0",
                "installed_at": now_str,
                "apple_id": "soliyusef@proton.me",
                "device_udid": "00008110-001C7C163628201E",
                "ipa_path": os.path.join(DATA_DIR, "StillClock-signed.ipa")
            }
            self._save_data()

    def register_installed_app(self, name: str, bundle_id: str, version: str, ipa_path: str, apple_id: str, device_udid: str):
        now_str = datetime.now(timezone.utc).isoformat()
        self.apps[bundle_id] = {
            "name": name,
            "bundle_id": bundle_id,
            "version": version,
            "installed_at": now_str,
            "apple_id": apple_id,
            "device_udid": device_udid,
            "ipa_path": ipa_path
        }
        self._save_data()

    def get_tracked_apps(self) -> List[Dict]:
        results = []
        now = datetime.now(timezone.utc)
        
        for bid, data in self.apps.items():
            try:
                installed_dt = datetime.fromisoformat(data["installed_at"])
                if installed_dt.tzinfo is None:
                    installed_dt = installed_dt.replace(tzinfo=timezone.utc)
            except Exception:
                installed_dt = now

            elapsed = now - installed_dt
            hours_elapsed = elapsed.total_seconds() / 3600.0
            hours_remaining = max(0.0, (7.0 * 24.0) - hours_elapsed)
            days_remaining = round(hours_remaining / 24.0, 1)
            percent_remaining = max(0, min(100, int((hours_remaining / (7.0 * 24.0)) * 100)))

            results.append({
                "name": data.get("name", bid),
                "bundle_id": bid,
                "version": data.get("version", "1.0"),
                "apple_id": data.get("apple_id", "dawood_hh@hotmail.com"),
                "days_remaining": days_remaining,
                "percent_remaining": percent_remaining,
                "installed_at": data.get("installed_at"),
                "needs_refresh": days_remaining <= 2.0
            })
        return results

    def start_background_daemon(self):
        if self.running:
            return
        self.running = True
        thread = threading.Thread(target=self._daemon_loop, daemon=True)
        thread.start()

    def _daemon_loop(self):
        while self.running:
            try:
                self._check_and_refresh()
            except Exception as e:
                print(f"Auto-refresh check error: {e}")
            time.sleep(300) # Check every 5 minutes

    def _check_and_refresh(self):
        import sideload_service
        devices = sideload_service.get_connected_devices()
        if not devices:
            return # Phone not connected via USB or Wi-Fi

        tracked = self.get_tracked_apps()
        for app in tracked:
            if app["needs_refresh"]:
                bid = app["bundle_id"]
                data = self.apps.get(bid)
                if not data:
                    continue
                ipa_path = data.get("ipa_path")
                if ipa_path and os.path.exists(ipa_path):
                    self.log_callback(f"[Auto-Refresh] Automatically refreshing {app['name']} (expires in {app['days_remaining']} days)...")
                    try:
                        sideload_service.sideload_ipa(
                            ipa_path=ipa_path,
                            apple_id=data.get("apple_id", "soliyusef@proton.me"),
                            device_udid=data.get("device_udid"),
                            progress_callback=self.log_callback
                        )
                        # Reset timestamp
                        data["installed_at"] = datetime.now(timezone.utc).isoformat()
                        self._save_data()
                        self.log_callback(f"[Auto-Refresh] ✓ {app['name']} successfully refreshed for another 7 days!")
                    except Exception as err:
                        self.log_callback(f"[Auto-Refresh] Failed refreshing {app['name']}: {err}")

refresh_engine = RefreshEngine()

