import os
import zipfile
import plistlib
from PIL import Image
import io
import cgbi

def parse_ipa(ipa_path):
    """
    Extracts metadata and app icon from an .ipa file without extracting the whole archive.
    Returns: dict with name, bundle_id, version, size_bytes, icon_image (PIL.Image or None)
    """
    res = {
        "path": ipa_path,
        "filename": os.path.basename(ipa_path),
        "name": os.path.splitext(os.path.basename(ipa_path))[0],
        "bundle_id": "Unknown",
        "version": "1.0",
        "size_bytes": 0,
        "icon_image": None
    }
    
    try:
        res["size_bytes"] = os.path.getsize(ipa_path)
    except Exception:
        pass

    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            names = z.namelist()
            
            # Find the main App folder in Payload/
            app_dir = None
            for n in names:
                if n.startswith("Payload/") and ".app/" in n:
                    parts = n.split(".app/")[0] + ".app/"
                    app_dir = parts
                    break
            
            main_plist_name = (app_dir + "Info.plist") if app_dir else None
            if not main_plist_name or main_plist_name not in names:
                candidates = [n for n in names if n.startswith("Payload/") and n.endswith(".app/Info.plist")]
                main_plist_name = candidates[0] if candidates else None

            info = {}
            if main_plist_name:
                try:
                    raw_data = z.read(main_plist_name)
                    info = plistlib.loads(raw_data)
                except Exception:
                    pass

            name = info.get("CFBundleDisplayName") or info.get("CFBundleName")
            if name:
                res["name"] = str(name)
            
            bundle_id = info.get("CFBundleIdentifier")
            if bundle_id:
                res["bundle_id"] = str(bundle_id)
                
            version = info.get("CFBundleShortVersionString") or info.get("CFBundleVersion")
            if version:
                res["version"] = str(version)

            # Icon extraction logic
            found_icon_bytes = None
            
            # 1. Look for png files specifically inside the app folder
            app_pngs = [
                n for n in names 
                if n.startswith(app_dir or "Payload/") and n.lower().endswith(".png") and "framework" not in n.lower()
            ]
            
            # Priority matches
            best_candidates = []
            for n in app_pngs:
                lower = n.lower()
                base = os.path.basename(lower)
                score = 0
                if "appicon" in base:
                    score += 50
                elif "icon" in base:
                    score += 30
                if "@3x" in base or "180" in base or "1024" in base:
                    score += 20
                elif "@2x" in base or "120" in base:
                    score += 15
                elif "60x60" in base or "76x76" in base:
                    score += 10
                best_candidates.append((score, n))
                
            best_candidates.sort(key=lambda x: x[0], reverse=True)
            for _, cand_name in best_candidates:
                try:
                    found_icon_bytes = z.read(cand_name)
                    if found_icon_bytes:
                        break
                except Exception:
                    continue

            if found_icon_bytes:
                try:
                    img = cgbi.load_png(found_icon_bytes)
                    res["icon_image"] = img
                except Exception:
                    pass

    except Exception:
        pass

    return res
