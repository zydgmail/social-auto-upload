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
        # B站
        case 5:
            return await cookie_auth_bilibili(Path(BASE_DIR / "cookiesFile" / file_path), preview)
        case _:
            return False

async def cookie_auth_bilibili(account_file, preview: bool = False):
    """B站cookie验证函数"""
    from utils.log import bilibili_logger
    
    bilibili_logger.info(f"[bilibili_auth] 开始验证B站cookie: {account_file}")
    
    async with async_playwright() as playwright:
        browser = await launch_chromium_with_codecs(playwright, headless=not preview, executable_path=None)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        page = await context.new_page()
        
        try:
            # 访问B站创作中心
            await page.goto("https://member.bilibili.com/platform/upload/video/frame")
            bilibili_logger.info(f"[bilibili_auth] 页面已加载: {page.url}")
            
            # 等待页面加载完成
            await page.wait_for_timeout(3000)
            
            # 更精确的登录状态检查
            # 首先检查是否被重定向到登录页面
            if "passport.bilibili.com" in page.url:
                bilibili_logger.warning("[bilibili_auth] 页面重定向到登录页，cookie失效")
                if preview:
                    await page.wait_for_timeout(1500)
                await context.close()
                await browser.close()
                return False
            
            # 检查页面是否有明确的登录表单或按钮（更精确的选择器）
            login_form_indicators = [
                'button:has-text("立即登录")',  # 登录按钮
                'button:has-text("扫码登录")',  # 扫码登录按钮
                'form[action*="login"]',  # 登录表单
                '.login-form',  # 登录表单类
                'input[type="password"]',  # 密码输入框
                '.qr-login',  # 二维码登录区域
            ]
            
            found_login_form = False
            for indicator in login_form_indicators:
                if await page.locator(indicator).count():
                    bilibili_logger.warning(f"[bilibili_auth] 发现登录表单元素: {indicator}")
                    found_login_form = True
                    break
            
            if found_login_form:
                bilibili_logger.warning("[bilibili_auth] 检测到登录表单，cookie失效")
                if preview:
                    await page.wait_for_timeout(1500)
                await context.close()
                await browser.close()
                return False
            
            # 额外调试：记录页面上的所有"登录"文字
            login_texts = await page.locator('text=登录').all()
            if login_texts:
                bilibili_logger.info(f"[bilibili_auth] 页面上发现{len(login_texts)}个'登录'文字，但都不是登录表单")
                for i, text_elem in enumerate(login_texts[:3]):  # 只记录前3个
                    try:
                        content = await text_elem.text_content()
                        bilibili_logger.info(f"[bilibili_auth] 登录文字{i+1}: {content}")
                    except:
                        pass
            
            # 如果没有登录提示，认为验证成功
            bilibili_logger.info("[bilibili_auth] cookie验证成功")
            if preview:
                await page.wait_for_timeout(1500)
            await context.close()
            await browser.close()
            return True
            
        except Exception as e:
            bilibili_logger.error(f"[bilibili_auth] cookie验证失败: {e}")
            try:
                await context.close()
            except Exception:
                pass
            try:
                await browser.close()
            except Exception:
                pass
            return False

# a = asyncio.run(check_cookie(1,"3a6cfdc0-3d51-11f0-8507-44e51723d63c.json"))
# print(a)