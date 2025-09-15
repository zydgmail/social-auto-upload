# -*- coding: utf-8 -*-
'''单独的运行文件,用于取消web端的抖音关注'''
import asyncio
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

# Ensure project root is importable
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from conf import LOCAL_CHROME_PATH  # noqa: E402
from utils.base_social_media import set_init_script  # noqa: E402


DOUYIN_FOLLOWING_URL = "https://creator.douyin.com/creator-micro/data/following/following"
COOKIE_FILE = str(ROOT_DIR / "cookiesFile/7fb186f6-9211-11f0-a291-cc28aaa9635f.json")
MAX_UNFOLLOW_TIMES = 100


async def click_unfollow_once(page) -> bool:
    """
    Click the first visible "取消关注" and confirm if a dialog appears.
    Returns True if click succeeded (button found and processed), else False.
    """
    # Try to find the first actionable unfollow link/button
    # Prefer anchor; fall back to any element containing the text
    unfollow = page.locator("a:has-text('取消关注')").first
    if not await unfollow.count():
        unfollow = page.get_by_text("取消关注").first
        if not await unfollow.count():
            return False

    try:
        await unfollow.scroll_into_view_if_needed()
        await unfollow.click()
    except Exception:
        return False

    # Handle potential confirm dialog
    try:
        # Common confirm actions: 确定 / 确认 / 取消关注
        for selector in [
            "button:has-text('确认')",
            "button:has-text('取消关注')",
            "[role='button']:has-text('确认')",
        ]:
            if await page.locator(selector).first.count():
                await page.locator(selector).first.click()
                break
    except Exception:
        pass

    # Small wait to allow state to change
    await page.wait_for_timeout(1000)
    return True


async def main():
    if not os.path.exists(COOKIE_FILE):
        print(f"[-] Cookie file not found: {COOKIE_FILE}")
        return

    async with async_playwright() as p:
        launch_kwargs = {"headless": False}
        if LOCAL_CHROME_PATH:
            launch_kwargs["executable_path"] = LOCAL_CHROME_PATH
        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(storage_state=COOKIE_FILE)
        context = await set_init_script(context)
        page = await context.new_page()

        success = 0
        for i in range(MAX_UNFOLLOW_TIMES):
            print(f"[+] Round {i + 1}/{MAX_UNFOLLOW_TIMES}: opening following page ...")
            await page.goto(DOUYIN_FOLLOWING_URL, wait_until="domcontentloaded")

            # Wait for any unfollow entry to appear
            try:
                await page.wait_for_selector("text=取消关注", timeout=8000)
            except Exception:
                print("[-] No '取消关注' found on the page. Stopping.")
                break

            if await click_unfollow_once(page):
                success += 1
                print(f"  [-] Unfollowed successfully. Total: {success}")
            else:
                print("  [-] Could not click '取消关注'. Stopping.")
                break

            # Refresh for the next iteration
            await page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(2)

        # Save cookies back (in case of updates)
        await context.storage_state(path=COOKIE_FILE)
        print(f"[+] Done. Unfollow attempts: {success}/{MAX_UNFOLLOW_TIMES}")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
