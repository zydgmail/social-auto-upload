import asyncio
import os
from datetime import datetime
from pathlib import Path

from playwright.async_api import Playwright

from conf import LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script, launch_chromium_with_codecs
from utils.log import bilibili_logger


OPEN_DEBUG_BROWSERS: list = []


class BilibiliVideo:
    def __init__(
        self,
        title: str,
        file_path: str,
        tags: list[str],
        publish_date: datetime | int,
        account_file: Path,
        thumbnail_path: str | None = None,
        desc: str | None = None,
        bili_type: str | None = None,
        partition: str | None = None,
    ) -> None:
        self.title = title
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.thumbnail_path = thumbnail_path
        self.local_executable_path = LOCAL_CHROME_PATH
        self.desc = desc or ""
        self.bili_type = (bili_type or "自制").strip()
        self.partition = (partition or "").strip()

    async def _fill_title(self, page) -> None:
        # 基于实际B站页面的选择器（探测结果：placeholder="请输入稿件标题"）
        candidates = [
            'input[placeholder*="标题"]',  # 主要选择器，已验证有效
            'input[placeholder="请输入稿件标题"]',  # 精确匹配
            'input[maxlength="80"]',  # 备用选择器
            'input[aria-label*="标题"]',
        ]
        for selector in candidates:
            try:
                if await page.locator(selector).first.count():
                    try:
                        await page.locator(selector).first.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    await page.locator(selector).first.fill(self.title[:80])
                    return
            except Exception:
                continue

    async def _fill_tags(self, page) -> None:
        if not self.tags:
            return
        # 基于实际B站页面的选择器（探测结果：placeholder="按回车键Enter创建标签"）
        candidates = [
            'input[placeholder*="标签"]',  # 主要选择器，已验证有效
            'input[placeholder*="按回车键Enter创建标签"]',  # 精确匹配
            'input[placeholder*="Enter"]',  # 部分匹配
            'input[placeholder*="#"]',
        ]
        for selector in candidates:
            try:
                if await page.locator(selector).first.count():
                    try:
                        await page.locator(selector).first.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    for tag in self.tags:
                        await page.locator(selector).first.type(tag)
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(200)
                    return
            except Exception:
                continue

    async def _fill_desc(self, page) -> None:
        if not self.desc:
            return
        
        bilibili_logger.info(f"[bilibili] 正在填写简介: {self.desc[:50]}...")
        
        # 基于实际B站页面的Quill编辑器结构
        desc_selectors = [
            '.ql-editor[contenteditable="true"]',  # 精确匹配Quill编辑器
            '.ql-editor',  # Quill富文本编辑器
            '[contenteditable="true"][data-placeholder*="简介"]',  # 有简介placeholder的可编辑元素
            '[contenteditable="true"]',  # 通用可编辑div
        ]
        
        for selector in desc_selectors:
            try:
                if await page.locator(selector).first.count():
                    bilibili_logger.info(f"[bilibili] 找到简介输入框: {selector}")
                    
                    # 滚动到元素可见位置
                    try:
                        await page.locator(selector).first.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    
                    # 点击激活编辑器
                    await page.locator(selector).first.click()
                    await page.wait_for_timeout(300)
                    
                    # 清空现有内容
                    await page.locator(selector).first.press('Ctrl+A')
                    await page.wait_for_timeout(100)
                    
                    # 对于Quill编辑器，使用innerHTML设置内容更可靠
                    try:
                        # 转义HTML特殊字符
                        escaped_desc = self.desc[:2000].replace("'", "\\'").replace('"', '\\"').replace('\n', '<br>')
                        await page.locator(selector).first.evaluate(f"el => el.innerHTML = '<p>{escaped_desc}</p>'")
                        bilibili_logger.info("[bilibili] 简介填写成功（innerHTML方式）")
                        return
                    except Exception:
                        # 备用：直接输入文本
                        await page.locator(selector).first.type(self.desc[:2000], delay=30)
                        bilibili_logger.info("[bilibili] 简介填写成功（输入方式）")
                        return
            except Exception as e:
                bilibili_logger.warning(f"[bilibili] 简介选择器 {selector} 失败: {e}")
                continue
        
        bilibili_logger.warning("[bilibili] 未能找到简介输入框")

    async def _set_type(self, page) -> None:
        # 基于实际B站页面的类型选择（自制/转载）
        if not self.bili_type:
            return
        
        try:
            # 尝试多种选择器来定位类型选择按钮
            type_selectors = [
                f'text="{self.bili_type}"',  # 精确文本匹配
                f'label:has-text("{self.bili_type}")',  # label元素
                f'span:has-text("{self.bili_type}")',  # span元素
            ]
            
            for selector in type_selectors:
                try:
                    if await page.locator(selector).first.count():
                        await page.locator(selector).first.scroll_into_view_if_needed()
                        await page.locator(selector).first.click()
                        bilibili_logger.info(f"[bilibili] 成功选择类型: {self.bili_type}")
                        return
                except Exception:
                    continue
            
            bilibili_logger.warning(f"[bilibili] 未能找到类型选择: {self.bili_type}")
        except Exception as e:
            bilibili_logger.warning(f"[bilibili] 类型选择失败: {e}")

    async def _set_partition(self, page) -> None:
        # 基于实际B站页面的分区选择
        if not self.partition:
            return
        
        try:
            bilibili_logger.info(f"[bilibili] 正在选择分区: {self.partition}")
            
            # 1. 基于实际HTML结构，找到分区选择器控制器并点击打开下拉菜单
            partition_controller_selectors = [
                '.select-controller',  # 精确匹配分区控制器
                'div[class*="select-controller"]',  # 包含select-controller的类
                '.select-item-cont-inserted',  # 分区内容容器
            ]
            
            dropdown_opened = False
            for controller_sel in partition_controller_selectors:
                try:
                    if await page.locator(controller_sel).count():
                        bilibili_logger.info(f"[bilibili] 找到分区控制器: {controller_sel}")
                        await page.locator(controller_sel).first.scroll_into_view_if_needed()
                        await page.locator(controller_sel).first.click()
                        await page.wait_for_timeout(800)  # 等待下拉菜单展开
                        
                        # 验证下拉菜单是否已打开
                        if await page.locator('.drop-list-v2-container').count():
                            dropdown_opened = True
                            bilibili_logger.info("[bilibili] 分区下拉菜单已打开")
                            break
                except Exception as e:
                    bilibili_logger.warning(f"[bilibili] 分区控制器 {controller_sel} 点击失败: {e}")
                    continue
            
            if not dropdown_opened:
                bilibili_logger.warning("[bilibili] 未能打开分区下拉菜单")
                return
            
            # 2. 在下拉菜单中查找并选择指定分区
            # 基于实际HTML结构的精确选择器
            partition_option_selectors = [
                f'.drop-list-v2-item[title="{self.partition}"]',  # 使用title属性精确匹配
                f'.drop-list-v2-item:has(.item-cont-main:text-is("{self.partition}"))',  # 匹配主要内容文本
                f'.item-cont-main:text-is("{self.partition}")',  # 直接匹配分区名称
                f'.drop-list-v2-item-cont:has-text("{self.partition}")',  # 匹配内容容器
            ]
            
            option_selected = False
            for option_sel in partition_option_selectors:
                try:
                    if await page.locator(option_sel).count():
                        bilibili_logger.info(f"[bilibili] 找到分区选项: {option_sel}")
                        await page.locator(option_sel).first.click()
                        await page.wait_for_timeout(500)  # 等待选择完成
                        option_selected = True
                        bilibili_logger.info(f"[bilibili] 成功选择分区: {self.partition}")
                        break
                except Exception as e:
                    bilibili_logger.warning(f"[bilibili] 分区选项 {option_sel} 点击失败: {e}")
                    continue
            
            if not option_selected:
                bilibili_logger.warning(f"[bilibili] 未能找到分区选项: {self.partition}")
                # 尝试点击页面其他位置关闭下拉菜单
                try:
                    await page.click('body', timeout=1000)
                except Exception:
                    pass
            
        except Exception as e:
            bilibili_logger.warning(f"[bilibili] 分区选择失败: {e}")

    async def _set_schedule(self, page) -> None:
        # 仅当提供了具体发布时间才尝试
        try:
            if not self.publish_date or self.publish_date == 0:
                return
            # 打开定时发布开关
            try:
                for sel in (
                    'label:has-text("定时发布") input[type="checkbox"]',
                    'div:has-text("定时发布") input[type="checkbox"]',
                    '.semi-switch-native-control',
                ):
                    if await page.locator(sel).first.count():
                        await page.locator(sel).first.click()
                        await page.wait_for_timeout(300)
                        break
            except Exception:
                pass

            # 输入时间（尽力而为，UI 可能变化）
            try:
                from datetime import datetime as _dt
                if isinstance(self.publish_date, _dt):
                    ts = self.publish_date
                else:
                    ts = _dt.fromtimestamp(self.publish_date) if isinstance(self.publish_date, (int, float)) else None
                if ts:
                    dt_str = ts.strftime('%Y-%m-%d %H:%M')
                    for input_sel in (
                        'input[placeholder*="日期"]',
                        'input[placeholder*="时间"]',
                        'input[placeholder*="日期和时间"]',
                        'input[aria-label*="时间"]',
                    ):
                        if await page.locator(input_sel).first.count():
                            el = page.locator(input_sel).first
                            try:
                                await el.scroll_into_view_if_needed()
                            except Exception:
                                pass
                            await el.click()
                            await page.keyboard.press('Control+KeyA')
                            await page.keyboard.type(dt_str)
                            await page.keyboard.press('Enter')
                            break
            except Exception:
                pass
        except Exception:
            pass

    async def _wait_upload_complete(self, page) -> None:
        # 轮询一些常见的完成提示或进度消失
        for _ in range(180):  # 最多轮询 ~3 分钟
            try:
                # 常见进度条消失或出现“上传完成/处理完成/审核通过”等提示
                done_texts = ["上传完成", "处理完成", "审核", "已上传", "重新上传"]
                for text in done_texts:
                    if await page.get_by_text(text).count():
                        return
            except Exception:
                pass
            await asyncio.sleep(1)

    async def _click_publish(self, page) -> None:
        # 基于实际B站页面的发布按钮选择器
        bilibili_logger.info("[bilibili] 正在寻找发布按钮...")
        
        # 基于实际HTML结构，发布按钮是span元素
        publish_selectors = [
            'span.submit-add:has-text("立即投稿")',  # 精确匹配实际结构
            '.submit-add:has-text("立即投稿")',  # 类名匹配
            'span:has-text("立即投稿")',  # span元素匹配
        ]
        
        for selector in publish_selectors:
            try:
                if await page.locator(selector).count():
                    bilibili_logger.info(f"[bilibili] 找到发布按钮: {selector}")
                    await page.locator(selector).first.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)  # 等待元素稳定
                    await page.locator(selector).first.click()
                    bilibili_logger.info(f"[bilibili] 成功点击发布按钮: {selector}")
                    
                    # 等待一下看是否有提交反应
                    await page.wait_for_timeout(1000)
                    return
            except Exception as e:
                bilibili_logger.warning(f"[bilibili] 发布按钮选择器失败 {selector}: {e}")
                continue
        
        bilibili_logger.error("[bilibili] 未找到任何发布按钮")

    async def upload(self, playwright: Playwright) -> None:
        browser = await launch_chromium_with_codecs(
            playwright,
            headless=False,
            executable_path=self.local_executable_path,
        )
        context = await browser.new_context(
            storage_state=str(self.account_file),
            permissions=[],
            geolocation=None,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )
        context = await set_init_script(context)
        page = await context.new_page()

        bilibili_logger.info("[bilibili] goto upload page")
        # 打开B站创作中心上传页（优先带 page_from 参数）
        try:
            await page.goto(
                "https://member.bilibili.com/platform/upload/video/frame?page_from=creative_home_top_upload",
                timeout=15000,
            )
        except Exception:
            try:
                await page.goto("https://member.bilibili.com/platform/upload/video/frame", timeout=15000)
            except Exception:
                # 回退到旧地址
                await page.goto("https://member.bilibili.com/platform/upload/video", timeout=20000)

        bilibili_logger.info("[bilibili] wait page ready")
        
        await page.locator('input[type="file"]').set_input_files(self.file_path) # 上传视频
        
        await asyncio.sleep(1)
        await self._fill_title(page)
        await self._fill_tags(page)
        await self._fill_desc(page)
        await self._set_type(page)
        await self._set_partition(page)
        await self._set_schedule(page)

        bilibili_logger.info("[bilibili] wait upload complete")
        # 等待上传完成或稳定
        await self._wait_upload_complete(page)

        # 等待300秒再发布（用户观察和确认）
        bilibili_logger.info("[bilibili] waiting 300 seconds before publish...")
        await asyncio.sleep(300)
        
        # 发布
        bilibili_logger.info("[bilibili] click publish")
        await self._click_publish(page)

        # 保存cookie
        await context.storage_state(path=str(self.account_file))

    async def main(self) -> None:
        from playwright.async_api import async_playwright
        async with async_playwright() as playwright:
            await self.upload(playwright)


