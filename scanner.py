import os
import string
import time
from typing import Callable, Generator

def get_available_drives():
    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            drives.append(drive_path)
    return drives

def find_ipas_iterative() -> Generator[str, None, None]:
    """
    Generator yielding .ipa file paths immediately as they are discovered.
    Prioritizes fast folders (OneDrive Desktop, Desktop, Downloads, Documents).
    """
    user_home = os.path.expanduser("~")
    high_priority_dirs = [
        os.path.join(user_home, "OneDrive", "Desktop"),
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Downloads"),
        os.path.join(user_home, "OneDrive", "Documents"),
        os.path.join(user_home, "Documents"),
        r"C:\Users\dawoo\.gemini\antigravity\scratch",
    ]
    
    seen_files = set()
    
    # 1. Fast priority scan
    for p_dir in high_priority_dirs:
        if not os.path.exists(p_dir):
            continue
        try:
            base_depth = p_dir.count(os.sep)
            for root, dirs, files in os.walk(p_dir):
                # Restrict depth to 4 levels max for instant scanning
                if root.count(os.sep) - base_depth > 4:
                    dirs.clear()
                    continue
                # Skip heavy dirs
                dirs[:] = [d for d in dirs if d.lower() not in {"node_modules", ".git", ".venv", "build", "deriveddata", "__pycache__"}]
                for f in files:
                    if f.lower().endswith(".ipa"):
                        full_path = os.path.normpath(os.path.join(root, f))
                        if full_path not in seen_files:
                            seen_files.add(full_path)
                            yield full_path
        except Exception:
            pass

def stream_search_ipas(on_found: Callable[[str], None], is_cancelled: Callable[[], bool] = lambda: False):
    for path in find_ipas_iterative():
        if is_cancelled():
            break
        on_found(path)
