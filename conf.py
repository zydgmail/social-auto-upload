from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
XHS_SERVER = "" # "http://127.0.0.1:11901"
LOCAL_CHROME_PATH = ""   # change me necessary！ for example C:/Program Files/Google/Chrome/Application/chrome.exe
USE_SYSTEM_BROWSER = False  # set False to force bundled Playwright Chromium from third_party
