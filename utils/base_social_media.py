import os
from pathlib import Path
from typing import List, Optional

from conf import BASE_DIR, USE_SYSTEM_BROWSER

SOCIAL_MEDIA_DOUYIN = "douyin"
SOCIAL_MEDIA_TENCENT = "tencent"
SOCIAL_MEDIA_TIKTOK = "tiktok"
SOCIAL_MEDIA_BILIBILI = "bilibili"
SOCIAL_MEDIA_KUAISHOU = "kuaishou"


def get_supported_social_media() -> List[str]:
    return [SOCIAL_MEDIA_DOUYIN, SOCIAL_MEDIA_TENCENT, SOCIAL_MEDIA_TIKTOK, SOCIAL_MEDIA_KUAISHOU]


def get_cli_action() -> List[str]:
    return ["upload", "login", "watch"]


async def set_init_script(context):
    stealth_js_path = Path(BASE_DIR / "utils/stealth.min.js")
    await context.add_init_script(path=stealth_js_path)
    return context


async def launch_chromium_with_codecs(playwright, headless: bool = False, executable_path: Optional[str] = None):
    """
    Prefer launching with system Chrome/Edge for proprietary codecs (H.264) and stable media playback.
    Falls back to bundled Chromium if neither is available.
    """
    launch_args = [
        "--autoplay-policy=no-user-gesture-required",
        "--enable-gpu",
        "--ignore-gpu-blocklist",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--mute-audio",
        "--lang=zh-CN",
    ]

    # If user prefers bundled/runtime-only mode, skip system channels and try third_party or bundled Chromium
    if not USE_SYSTEM_BROWSER:
        # Point Playwright to in-repo browsers if present
        third_party_pw = Path(BASE_DIR / "third_party" / "playwright" / "ms-playwright")
        if third_party_pw.exists():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(third_party_pw)
            print(f"[launch] Using bundled browsers at {third_party_pw}")

        # Probe portable Chrome/Edge under third_party (with proprietary codecs)
        portable_candidates = [
            Path(BASE_DIR / "third_party" / "chrome-win" / "chrome.exe"),
            Path(BASE_DIR / "third_party" / "chrome" / "chrome.exe"),
            Path(BASE_DIR / "third_party" / "edge" / "msedge.exe"),
            Path(BASE_DIR / "third_party" / "msedge" / "msedge.exe"),
        ]
        for candidate in portable_candidates:
            try:
                if candidate.exists():
                    print(f"[launch] Using portable browser: {candidate}")
                    return await playwright.chromium.launch(
                        headless=headless,
                        executable_path=str(candidate),
                        args=launch_args,
                    )
            except Exception as e:
                print(f"[launch] portable exec failed {candidate}: {e}")

        print("[launch] Forcing bundled Chromium (no system browser). H.264 may be unavailable.")
        return await playwright.chromium.launch(headless=headless, args=launch_args)

    # 1) Explicit executable path wins
    try:
        if executable_path and executable_path.strip():
            return await playwright.chromium.launch(
                headless=headless,
                executable_path=executable_path,
                args=launch_args,
            )
    except Exception as e:
        print(f"[launch] executable_path failed: {e}")

    # 2) Try installed Chrome
    try:
        return await playwright.chromium.launch(
            headless=headless,
            channel="chrome",
            args=launch_args,
        )
    except Exception as e:
        print(f"[launch] channel=chrome failed: {e}")

    # 3) Try installed Edge (also supports proprietary codecs on Windows)
    try:
        return await playwright.chromium.launch(
            headless=headless,
            channel="msedge",
            args=launch_args,
        )
    except Exception as e:
        print(f"[launch] channel=msedge failed: {e}")

    # 4) Fallback to bundled Chromium (may lack H.264)
    print("[launch] Falling back to bundled Chromium; H.264 may be unavailable.")
    return await playwright.chromium.launch(headless=headless, args=launch_args)
