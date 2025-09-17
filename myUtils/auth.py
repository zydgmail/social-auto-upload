import asyncio
import configparser
import os

from playwright.async_api import async_playwright
from xhs import XhsClient

from conf import BASE_DIR
from utils.base_social_media import set_init_script, launch_chromium_with_codecs
from utils.log import (
    tencent_logger,
    kuaishou_logger,
    douyin_logger,
    xiaohongshu_logger,
)
from pathlib import Path
from uploader.xhs_uploader.main import sign_local

async def cookie_auth_douyin(account_file, preview: bool = False):
    async with async_playwright() as playwright:
        browser = await launch_chromium_with_codecs(playwright, headless=not preview, executable_path=None)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
        except:
            douyin_logger.warning("[douyin] cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            douyin_logger.warning("[douyin] cookie 失效")
            if preview:
                await page.wait_for_timeout(1500)
            return False
        else:
            douyin_logger.success("[douyin] cookie 有效")
            if preview:
                await page.wait_for_timeout(1500)
            return True

async def cookie_auth_tencent(account_file, preview: bool = False):
    async with async_playwright() as playwright:
        browser = await launch_chromium_with_codecs(playwright, headless=not preview, executable_path=None)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        try:
            await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)  # 等待5秒
            tencent_logger.error("[tencent] cookie 失效")
            if preview:
                await page.wait_for_timeout(1500)
            return False
        except:
            tencent_logger.success("[tencent] cookie 有效")
            if preview:
                await page.wait_for_timeout(1500)
            return True

async def cookie_auth_ks(account_file, preview: bool = False):
    async with async_playwright() as playwright:
        browser = await launch_chromium_with_codecs(playwright, headless=not preview, executable_path=None)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://cp.kuaishou.com/article/publish/video")
        try:
            await page.wait_for_selector("div.names div.container div.name:text('机构服务')", timeout=5000)  # 等待5秒
            kuaishou_logger.info("[kuaishou] cookie 失效")
            if preview:
                await page.wait_for_timeout(1500)
            return False
        except:
            kuaishou_logger.success("[kuaishou] cookie 有效")
            if preview:
                await page.wait_for_timeout(1500)
            return True


async def cookie_auth_xhs(account_file, preview: bool = False):
    async with async_playwright() as playwright:
        browser = await launch_chromium_with_codecs(playwright, headless=not preview, executable_path=None)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.xiaohongshu.com/creator-micro/content/upload", timeout=5000)
        except:
            xiaohongshu_logger.warning("[xhs] cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            xiaohongshu_logger.warning("[xhs] cookie 失效")
            if preview:
                await page.wait_for_timeout(1500)
            return False
        else:
            xiaohongshu_logger.success("[xhs] cookie 有效")
            if preview:
                await page.wait_for_timeout(1500)
            return True


async def check_cookie(type, file_path, preview: bool = False):
    match type:
        # 小红书
        case 1:
            return await cookie_auth_xhs(Path(BASE_DIR / "cookiesFile" / file_path), preview)
        # 视频号
        case 2:
            return await cookie_auth_tencent(Path(BASE_DIR / "cookiesFile" / file_path), preview)
        # 抖音
        case 3:
            return await cookie_auth_douyin(Path(BASE_DIR / "cookiesFile" / file_path), preview)
        # 快手
        case 4:
            return await cookie_auth_ks(Path(BASE_DIR / "cookiesFile" / file_path), preview)
        case _:
            return False

# a = asyncio.run(check_cookie(1,"3a6cfdc0-3d51-11f0-8507-44e51723d63c.json"))
# print(a)