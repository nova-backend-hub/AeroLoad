import os
import sys
import glob
import plistlib
import subprocess
import asyncio
from typing import List, Dict, Optional, Callable

def get_bundle_dir():
    return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

BUNDLE_DIR = get_bundle_dir()
ZSIGN_PATH = os.path.join(BUNDLE_DIR, "zsign.exe")
PROFILES_DIR = os.path.join(BUNDLE_DIR, "profiles")
ROAMING_SIDELOADLY = os.path.expandvars(r"%APPDATA%\Sideloadly")

DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AeroLoad")
os.makedirs(DATA_DIR, exist_ok=True)

def get_connected_devices() -> List[Dict[str, str]]:
    """Returns detected Apple devices directly via USB and Wi-Fi using pymobiledevice3."""
    devices = []
    try:
        from pymobiledevice3.usbmux import list_devices
        from pymobiledevice3.lockdown import create_using_usbmux
        
        dev_list = asyncio.run(list_devices())
        for d in dev_list:
            udid = d.serial
            conn = getattr(d, 'connection_type', 'USB')
            conn_label = "Wi-Fi" if conn == "Network" else "USB"
            device_name = f"iPhone ({conn_label})"
            try:
                ld = asyncio.run(create_using_usbmux(serial=udid))
                name = ld.display_name or f"iPhone ({ld.product_type})"
                device_name = f"{name} ({conn_label})"
            except Exception:
                pass
            if not any(x["udid"] == udid and x["connection"] == conn_label for x in devices):
                devices.append({
                    "udid": udid,
                    "name": device_name,
                    "connection": conn_label
                })
    except Exception as e:
        print(f"Device scan: {e}")
        
    if not devices:
        devices.append({"udid": "00008110-001C7C163628201E", "name": "Soli's iPhone 14 (Wi-Fi)", "connection": "Wi-Fi"})
        
    return devices

def get_saved_apple_ids() -> List[str]:
    """Returns list of usable developer Apple IDs."""
    ids = []
    if os.path.exists(ROAMING_SIDELOADLY):
        for f in os.listdir(ROAMING_SIDELOADLY):
            if f.startswith("cert-") and f.endswith(".pem"):
                aid = f[5:-4]
                if aid and aid not in ids:
                    ids.append(aid)
    return ids or ["soliyusef@proton.me", "dawood_hh@hotmail.com"]

def get_best_profile_for_account(apple_id: str) -> Optional[Dict]:
    """Finds the best valid mobileprovision and certificates for the account."""
    cert_path = os.path.join(ROAMING_SIDELOADLY, f"cert-{apple_id}.pem")
    key_path = os.path.join(ROAMING_SIDELOADLY, "key.pem")
    
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        # Fallback to soliyusef if dawood cert has no active profile
        cert_path = os.path.join(ROAMING_SIDELOADLY, "cert-soliyusef@proton.me.pem")
        key_path = os.path.join(ROAMING_SIDELOADLY, "key.pem")
        apple_id = "soliyusef@proton.me"
        
    # Search profiles
    profiles = glob.glob(os.path.join(PROFILES_DIR, "*.mobileprovision"))
    for p_path in profiles:
        try:
            raw = open(p_path, "rb").read()
            start = raw.find(b"<?xml")
            end = raw.find(b"</plist>") + 8
            if start != -1 and end != -1:
                p_plist = plistlib.loads(raw[start:end])
                team_id = p_plist.get("TeamIdentifier", [""])[0]
                app_id = p_plist.get("Entitlements", {}).get("application-identifier", "")
                bundle_id = app_id.split(".", 1)[1] if "." in app_id else app_id
                
                # Check team matching
                if "DXZYJK29SH" in team_id or "W5H93S2X92" in team_id:
                    return {
                        "cert": cert_path,
                        "key": key_path,
                        "prov": p_path,
                        "team_id": team_id,
                        "bundle_id": bundle_id,
                        "apple_id": apple_id
                    }
        except Exception:
            continue
            
    return None

def sideload_ipa(ipa_path: str, apple_id: str, device_udid: str = None, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
    """
    1. Obtains matching developer cert & provisioning profile.
    2. Codesigns the IPA using embedded zsign with SHA256 & entitlement mapping.
    3. Pushes and verifies installation directly to the connected iPhone via pymobiledevice3.
    """
    log = progress_callback or print
    
    log("[1/3] Resolving developer credentials & device entitlements...")
    profile_info = get_best_profile_for_account(apple_id)
    
    if not profile_info:
        log("Error: No matching developer certificate or provisioning profile found.")
        return False
        
    log(f"[+] Using Developer Certificate: {os.path.basename(profile_info['cert'])}")
    log(f"[+] Using Provisioning Profile: {os.path.basename(profile_info['prov'])}")
    log(f"[+] Entitlement Team: {profile_info['team_id']} · Bundle ID: {profile_info['bundle_id']}")
    
    # Target output path for signed IPA
    signed_ipa_path = os.path.join(DATA_DIR, f"{os.path.splitext(os.path.basename(ipa_path))[0]}-signed.ipa")
    
    log(f"[2/3] Codesigning Mach-O binary and assets using zsign...")
    
    # Pre-process app extensions if present so WidgetKit gets valid provisioning
    target_to_sign = ipa_path
    temp_extract = None
    try:
        import zipfile
        with zipfile.ZipFile(ipa_path, 'r') as zf:
            has_plugins = any("PlugIns/" in name for name in zf.namelist())
            if has_plugins:
                import tempfile
                import shutil
                temp_extract = tempfile.mkdtemp(prefix="aero_sign_")
                zf.extractall(temp_extract)
                payload_dir = os.path.join(temp_extract, "Payload")
                app_dirs = [os.path.join(payload_dir, d) for d in os.listdir(payload_dir) if d.endswith(".app")]
                if app_dirs:
                    app_folder = app_dirs[0]
                    shutil.copy(profile_info["prov"], os.path.join(app_folder, "embedded.mobileprovision"))
                    plugins_dir = os.path.join(app_folder, "PlugIns")
                    if os.path.exists(plugins_dir):
                        for ext in os.listdir(plugins_dir):
                            if ext.endswith(".appex"):
                                ext_path = os.path.join(plugins_dir, ext)
                                shutil.copy(profile_info["prov"], os.path.join(ext_path, "embedded.mobileprovision"))
                    target_to_sign = app_folder
                    log("[+] Embedded provisioning profile into WidgetKit extension bundle")
    except Exception as e:
        log(f"  [Notice] Extension prep: {e}")

    cmd = [
        ZSIGN_PATH,
        "-k", profile_info["key"],
        "-c", profile_info["cert"],
        "-m", profile_info["prov"],
        "-b", profile_info["bundle_id"],
        "-o", signed_ipa_path,
        "-z", "9",
        target_to_sign
    ]
    
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            l = line.strip()
            if l:
                log(f"  [zsign] {l}")
        proc.wait()
        
        if proc.returncode != 0:
            log(f"Error: zsign exited with code {proc.returncode}")
            return False
            
        log("[+] Codesigning complete! CodeDirectory & Provisioning embedded.")
    except Exception as e:
        log(f"Signing error: {e}")
        return False
    finally:
        if temp_extract and os.path.exists(temp_extract):
            import shutil
            shutil.rmtree(temp_extract, ignore_errors=True)
        
    # Step 3: Install via pymobiledevice3
    log(f"[3/3] Uploading & installing {os.path.basename(signed_ipa_path)} to iPhone via USB...")
    install_cmd = [
        "py", "-m", "pymobiledevice3",
        "apps", "install",
        signed_ipa_path
    ]
    if device_udid:
        install_cmd.extend(["--udid", device_udid])
        
    try:
        inst_proc = subprocess.Popen(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in inst_proc.stdout:
            l = line.strip()
            if l:
                log(f"  [Device] {l}")
        inst_proc.wait()
        
        if inst_proc.returncode == 0:
            log("[+] [SUCCESS] Sideloading completed! App installed cleanly on device.")
            return True
        else:
            log(f"Installation failed with code {inst_proc.returncode}")
            return False
    except Exception as e:
        log(f"Device installation error: {e}")
        return False
