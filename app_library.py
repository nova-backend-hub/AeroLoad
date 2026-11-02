"""
AeroLoad Curated App Library
Aggregates top community IPA sources (AltStore, SideStore, and community repos)
"""

from typing import List, Dict

CURATED_APPS: List[Dict[str, str]] = [
    # Emulators
    {
        "id": "delta",
        "name": "Delta Emulator",
        "category": "Emulators",
        "version": "1.6",
        "developer": "Riley Testut",
        "description": "All-in-one classic Nintendo emulator for iOS (GBA, GBC, SNES, NES, N64, DS).",
        "icon": "https://raw.githubusercontent.com/rileytestut/Delta/master/Delta/Assets.xcassets/AppIcon.appiconset/256.png",
        "download_url": "https://github.com/rileytestut/Delta/releases/download/v1.6/Delta.ipa",
        "bundle_id": "com.rileytestut.Delta"
    },
    {
        "id": "ppsspp",
        "name": "PPSSPP",
        "category": "Emulators",
        "version": "1.18.1",
        "developer": "Henrik Rydgård",
        "description": "Fast Sony PlayStation Portable (PSP) emulator with HD graphics and save states.",
        "icon": "https://www.ppsspp.org/static/icon.png",
        "download_url": "https://github.com/hrydgard/ppsspp/releases/download/v1.18.1/PPSSPP_iOS.ipa",
        "bundle_id": "org.ppsspp.ppsspp"
    },
    {
        "id": "flycast",
        "name": "Flycast",
        "category": "Emulators",
        "version": "2.4",
        "developer": "flyinghead",
        "description": "Sega Dreamcast, Naomi, and Atomiswave multi-platform emulator.",
        "icon": "https://raw.githubusercontent.com/flyinghead/flycast/master/shell/apple/emulator/Assets.xcassets/AppIcon.appiconset/AppIcon-512.png",
        "download_url": "https://github.com/flyinghead/flycast/releases/download/v2.4/flycast-iOS.ipa",
        "bundle_id": "com.flyinghead.Flycast"
    },
    {
        "id": "utm-se",
        "name": "UTM SE (Virtual Machines)",
        "category": "Emulators",
        "version": "4.6.2",
        "developer": "UTM Team",
        "description": "Run Windows, Linux, and classic Mac OS virtual machines natively on iPhone.",
        "icon": "https://raw.githubusercontent.com/utmapp/UTM/master/Platform/macOS/AppIcon.iconset/icon_256x256.png",
        "download_url": "https://github.com/utmapp/UTM/releases/download/v4.6.2/UTM.ipa",
        "bundle_id": "com.utmapp.UTM"
    },

    # Tweaked & Media
    {
        "id": "uyouenhanced",
        "name": "uYouEnhanced",
        "category": "Tweaked Media",
        "version": "19.34.2",
        "developer": "arichorn / qnblackcat",
        "description": "YouTube modded with AdBlock, SponsorBlock, background audio, and PiP support.",
        "icon": "https://raw.githubusercontent.com/arichorn/uYouEnhanced/main/Images/uYouEnhanced.png",
        "download_url": "https://github.com/arichorn/uYouEnhanced/releases/download/v19.34.2-3.0.4/uYouEnhanced_19.34.2_3.0.4.ipa",
        "bundle_id": "com.google.ios.youtube"
    },
    {
        "id": "enmity",
        "name": "Enmity (Discord Mod)",
        "category": "Tweaked Media",
        "version": "2.0.1",
        "developer": "Enmity Team",
        "description": "Enhanced Discord client with plugin engine, custom themes, and token security.",
        "icon": "https://raw.githubusercontent.com/enmity-mod/enmity/main/assets/icon.png",
        "download_url": "https://github.com/enmity-mod/enmity/releases/download/v2.0.1/Enmity.ipa",
        "bundle_id": "com.hammerandchisel.discord"
    },
    {
        "id": "spotilife",
        "name": "Spotilife Enhanced",
        "category": "Tweaked Media",
        "version": "8.9.20",
        "developer": "Julioverne",
        "description": "Spotify with unlimited skips, highest quality streaming, and no banner ads.",
        "icon": "https://raw.githubusercontent.com/spotdl/spotify-downloader/master/docs/assets/spotify.png",
        "download_url": "https://github.com/spotilife/spotilife/releases/download/v1.0/Spotilife.ipa",
        "bundle_id": "com.spotify.client"
    },

    # Utilities & Tools
    {
        "id": "livecontainer",
        "name": "LiveContainer",
        "category": "Utilities",
        "version": "2.1.2",
        "developer": "Khanhduy Tran",
        "description": "Run multiple apps inside a single container without using up your 3-app sideload limit.",
        "icon": "https://raw.githubusercontent.com/khanhduytran0/LiveContainer/main/LiveContainer/Assets.xcassets/AppIcon.appiconset/AppIcon-256.png",
        "download_url": "https://github.com/khanhduytran0/LiveContainer/releases/download/v2.1.2/LiveContainer.ipa",
        "bundle_id": "com.kdt.livecontainer"
    },
    {
        "id": "sidestore",
        "name": "SideStore",
        "category": "Utilities",
        "version": "0.5.8",
        "developer": "SideStore Team",
        "description": "Sideload and refresh apps directly on your iPhone using local WireGuard VPN.",
        "icon": "https://raw.githubusercontent.com/SideStore/SideStore/main/SideStore/Assets.xcassets/AppIcon.appiconset/AppIcon-256.png",
        "download_url": "https://github.com/SideStore/SideStore/releases/download/0.5.8/SideStore.ipa",
        "bundle_id": "com.sidestore.SideStore"
    },
    {
        "id": "clip",
        "name": "Clip (Clipboard Manager)",
        "category": "Utilities",
        "version": "1.1.2",
        "developer": "Riley Testut",
        "description": "Background clipboard manager with persistent history and quick paste widgets.",
        "icon": "https://raw.githubusercontent.com/rileytestut/Clip/master/Clip/Assets.xcassets/AppIcon.appiconset/256.png",
        "download_url": "https://github.com/rileytestut/Clip/releases/download/v1.1.2/Clip.ipa",
        "bundle_id": "com.rileytestut.Clip"
    },
    {
        "id": "stikdebug",
        "name": "StikDebug (JIT Enabler)",
        "category": "Utilities",
        "version": "3.1.9",
        "developer": "Stik Team",
        "description": "Developer utility to enable Just-In-Time compilation on iOS 17+ without Mac.",
        "icon": "https://raw.githubusercontent.com/stikteam/stikdebug/main/icon.png",
        "download_url": "https://github.com/stikteam/stikdebug/releases/download/3.1.9/StikDebug-3.1.9.ipa",
        "bundle_id": "com.stik.stikdebug"
    },

    # Games
    {
        "id": "pojavlauncher",
        "name": "PojavLauncher",
        "category": "Games",
        "version": "2.2",
        "developer": "PojavLauncherTeam",
        "description": "Full Minecraft: Java Edition launcher for iOS with mod support (OptiFine, Fabric).",
        "icon": "https://raw.githubusercontent.com/PojavLauncherTeam/PojavLauncher_iOS/v2.2/PojavLauncher/Images.xcassets/AppIcon.appiconset/256.png",
        "download_url": "https://github.com/PojavLauncherTeam/PojavLauncher_iOS/releases/download/v2.2/PojavLauncher.ipa",
        "bundle_id": "net.kdt.pojavlauncher"
    }
]

def get_all_library_apps() -> List[Dict[str, str]]:
    return CURATED_APPS

def get_categories() -> List[str]:
    cats = []
    for app in CURATED_APPS:
        if app["category"] not in cats:
            cats.append(app["category"])
    return cats

