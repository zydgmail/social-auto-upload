import asyncio
import sqlite3

from playwright.async_api import async_playwright

from myUtils.auth import check_cookie
from utils.base_social_media import set_init_script
import uuid
from pathlib import Path
from conf import BASE_DIR

# 抖音登录
async def douyin_cookie_gen(id,status_queue, update_mode=False, record_id=None):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(
            **options,
            executable_path=str(BASE_DIR / "third_party" / "playwright" / "ms-playwright" / "chromium-1169" / "chrome-win" / "chrome.exe")
        )
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        original_url = page.url
        img_locator = page.get_by_role("img", name="二维码")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            status_queue.put("500")
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        await context.storage_state(path=Path(BASE_DIR / "cookiesFile" / f"{uuid_v1}.json"))
        result = await check_cookie(3, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            if update_mode and record_id:
                cursor.execute('''
                    UPDATE user_info SET type = ?, filePath = ?, userName = ?, status = ? WHERE id = ?
                ''', (3, f"{uuid_v1}.json", id, 1, int(record_id)))
            else:
                cursor.execute('''
                                    INSERT INTO user_info (type, filePath, userName, status)
                                    VALUES (?, ?, ?, ?)
                                    ''', (3, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")


# 视频号登录
async def get_tencent_cookie(id,status_queue, update_mode=False, record_id=None):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(
            **options,
            executable_path=str(BASE_DIR / "third_party" / "playwright" / "ms-playwright" / "chromium-1169" / "chrome-win" / "chrome.exe")
        )
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        # Pause the page, and start recording manually.
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://channels.weixin.qq.com")
        original_url = page.url

        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        # 等待 iframe 出现（最多等 60 秒）
        iframe_locator = page.frame_locator("iframe").first

        # 获取 iframe 中的第一个 img 元素
        img_locator = iframe_locator.get_by_role("img").first

        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        await context.storage_state(path=Path(BASE_DIR / "cookiesFile" / f"{uuid_v1}.json"))
        result = await check_cookie(2,f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            if update_mode and record_id:
                cursor.execute('''
                    UPDATE user_info SET type = ?, filePath = ?, userName = ?, status = ? WHERE id = ?
                ''', (2, f"{uuid_v1}.json", id, 1, int(record_id)))
            else:
                cursor.execute('''
                                INSERT INTO user_info (type, filePath, userName, status)
                                VALUES (?, ?, ?, ?)
                                ''', (2, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

# 快手登录
async def get_ks_cookie(id,status_queue, update_mode=False, record_id=None):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(
            **options,
            executable_path=str(BASE_DIR / "third_party" / "playwright" / "ms-playwright" / "chromium-1169" / "chrome-win" / "chrome.exe")
        )
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://cp.kuaishou.com")

        # 定位并点击“立即登录”按钮（类型为 link）
        await page.get_by_role("link", name="立即登录").click()
        await page.get_by_text("扫码登录").click()
        img_locator = page.get_by_role("img", name="qrcode")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        await context.storage_state(path=Path(BASE_DIR / "cookiesFile" / f"{uuid_v1}.json"))
        result = await check_cookie(4, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            if update_mode and record_id:
                cursor.execute('''
                    UPDATE user_info SET type = ?, filePath = ?, userName = ?, status = ? WHERE id = ?
                ''', (4, f"{uuid_v1}.json", id, 1, int(record_id)))
            else:
                cursor.execute('''
                                        INSERT INTO user_info (type, filePath, userName, status)
                                        VALUES (?, ?, ?, ?)
                                        ''', (4, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

# 小红书登录
async def xiaohongshu_cookie_gen(id,status_queue, update_mode=False, record_id=None):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(
            **options,
            executable_path=str(BASE_DIR / "third_party" / "playwright" / "ms-playwright" / "chromium-1169" / "chrome-win" / "chrome.exe")
        )
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/")
        await page.locator('img.css-wemwzq').click()

        img_locator = page.get_by_role("img").nth(2)
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        await context.storage_state(path=Path(BASE_DIR / "cookiesFile" / f"{uuid_v1}.json"))
        result = await check_cookie(1, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            if update_mode and record_id:
                cursor.execute('''
                    UPDATE user_info SET type = ?, filePath = ?, userName = ?, status = ? WHERE id = ?
                ''', (1, f"{uuid_v1}.json", id, 1, int(record_id)))
            else:
                cursor.execute('''
                           INSERT INTO user_info (type, filePath, userName, status)
                           VALUES (?, ?, ?, ?)
                           ''', (1, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

# a = asyncio.run(xiaohongshu_cookie_gen(4,None))
# print(a)

# B站登录
async def bilibili_cookie_gen(id, status_queue, update_mode=False, record_id=None):
    from utils.log import bilibili_logger
    
    bilibili_logger.info(f"[bilibili_login] 开始B站登录流程，用户ID: {id}")
    
    url_changed_event = asyncio.Event()

    async def on_url_change():
        bilibili_logger.info(f"[bilibili_login] 页面URL变化: {page.url}")
        if page.url != original_url:
            bilibili_logger.info(f"[bilibili_login] 检测到URL变化，原始URL: {original_url}, 新URL: {page.url}")
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        bilibili_logger.info("[bilibili_login] 启动浏览器...")
        browser = await playwright.chromium.launch(
            **options,
            executable_path=str(BASE_DIR / "third_party" / "playwright" / "ms-playwright" / "chromium-1169" / "chrome-win" / "chrome.exe")
        )
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()
        
        bilibili_logger.info("[bilibili_login] 导航到B站上传页面...")
        await page.goto("https://member.bilibili.com/platform/upload/video/frame")
        original_url = page.url
        bilibili_logger.info(f"[bilibili_login] 初始页面URL: {original_url}")

        # 尝试抓取二维码
        bilibili_logger.info("[bilibili_login] 尝试查找二维码...")
        try:
            img_locator = page.locator('img[src*="qrcode"]').first
            if await img_locator.count() == 0:
                bilibili_logger.info("[bilibili_login] 未找到qrcode图片，尝试查找其他img元素")
                img_locator = page.locator('img').first
                
            if await img_locator.count() > 0:
                src = await img_locator.get_attribute("src")
                if src:
                    bilibili_logger.info(f"[bilibili_login] 找到二维码图片: {src[:50]}...")
                    status_queue.put(src)
                else:
                    bilibili_logger.warning("[bilibili_login] 找到img元素但无src属性")
            else:
                bilibili_logger.warning("[bilibili_login] 未找到任何img元素")
        except Exception as e:
            bilibili_logger.error(f"[bilibili_login] 查找二维码时出错: {e}")

        bilibili_logger.info("[bilibili_login] 等待用户扫码登录...")
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
        try:
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)
            bilibili_logger.info("[bilibili_login] 检测到页面跳转，登录可能成功")
        except asyncio.TimeoutError:
            bilibili_logger.error("[bilibili_login] 登录超时（200秒）")
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None

        bilibili_logger.info("[bilibili_login] 保存登录状态...")
        uuid_v1 = uuid.uuid1()
        cookie_file = f"{uuid_v1}.json"
        await context.storage_state(path=Path(BASE_DIR / "cookiesFile" / cookie_file))
        bilibili_logger.info(f"[bilibili_login] 登录状态已保存到: {cookie_file}")
        
        bilibili_logger.info("[bilibili_login] 验证cookie有效性...")
        result = await check_cookie(5, cookie_file)
        bilibili_logger.info(f"[bilibili_login] cookie验证结果: {result}")
        
        if not result:
            bilibili_logger.error("[bilibili_login] cookie验证失败，登录失败")
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None

        bilibili_logger.info("[bilibili_login] 关闭浏览器...")
        await page.close()
        await context.close()
        await browser.close()

        bilibili_logger.info("[bilibili_login] 保存用户信息到数据库...")
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            if update_mode and record_id:
                bilibili_logger.info(f"[bilibili_login] 更新现有记录ID: {record_id}")
                cursor.execute('''
                    UPDATE user_info SET type = ?, filePath = ?, userName = ?, status = ? WHERE id = ?
                ''', (5, cookie_file, id, 1, int(record_id)))
            else:
                bilibili_logger.info("[bilibili_login] 插入新用户记录")
                cursor.execute('''
                                    INSERT INTO user_info (type, filePath, userName, status)
                                    VALUES (?, ?, ?, ?)
                                    ''', (5, cookie_file, id, 1))
            conn.commit()
            bilibili_logger.info("✅ [bilibili_login] 用户状态已记录到数据库")
        
        bilibili_logger.info("[bilibili_login] B站登录流程完成，返回成功状态")
        status_queue.put("200")