import os
import sys
import subprocess
import threading
import requests
import plistlib
from typing import Callable, Optional

ZSIGN_PATH = os.path.join(os.path.dirname(__file__), "zsign.exe")

class SideloadEngine:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback or print
        
    def log(self, msg: str):
        self.log_callback(msg)
        
    def fetch_anisette_headers(self) -> dict:
        """Fetches fresh Anisette headers required by Apple authentication."""
        self.log("Fetching Anisette v3 cryptographic data from SideStore...")
        try:
            r = requests.get("https://ani.sidestore.io/", timeout=10)
            if r.status_code == 200:
                self.log("✓ Anisette data received.")
                return r.json()
        except Exception as e:
            self.log(f"Warning: Remote Anisette fetch failed ({e}).")
        return {}

    def sign_ipa_with_zsign(self, ipa_path: str, cert_path: str, key_path: str, prov_path: str, output_path: str) -> bool:
        """
        Signs an .ipa using the embedded high-performance zsign binary.
        """
        if not os.path.exists(ZSIGN_PATH):
            self.log("Error: zsign.exe binary not found.")
            return False
            
        self.log(f"Signing IPA: {os.path.basename(ipa_path)} ...")
        cmd = [
            ZSIGN_PATH,
            "-k", key_path,
            "-c", cert_path,
            "-m", prov_path,
            "-o", output_path,
            "-z", "9",
            ipa_path
        ]
        
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                line_str = line.strip()
                if line_str:
                    self.log(f"[zsign] {line_str}")
            p.wait()
            return p.returncode == 0
        except Exception as e:
            self.log(f"Signing error: {e}")
            return False

    def install_to_device(self, signed_ipa_path: str, udid: Optional[str] = None) -> bool:
        """
        Installs the signed IPA to the connected iPhone directly via pymobiledevice3.
        """
        self.log(f"Installing {os.path.basename(signed_ipa_path)} to device via USB...")
        cmd = [
            sys.executable,
            "-m", "pymobiledevice3",
            "apps", "install",
            signed_ipa_path
        ]
        if udid:
            cmd.extend(["--udid", udid])
            
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                line_str = line.strip()
                if line_str:
                    self.log(f"[Device] {line_str}")
            p.wait()
            if p.returncode == 0:
                self.log("✓ Sideload installation completed successfully!")
                return True
            else:
                self.log(f"Installation exited with code {p.returncode}")
                return False
        except Exception as e:
            self.log(f"Direct device install error: {e}")
            return False

