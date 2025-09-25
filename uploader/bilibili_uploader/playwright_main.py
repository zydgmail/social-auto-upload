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
        # B站简介可能是富文本编辑器或其他特殊组件，探测结果显示没有textarea
        candidates = [
            '.ql-editor',  # Quill富文本编辑器
            '[contenteditable="true"]',  # 可编辑div
            'div[role="textbox"]',  # 文本框角色
            'textarea[placeholder*="简介"]',  # 传统textarea（备用）
            'textarea[aria-label*="简介"]',  # 无障碍标签
            'textarea',  # 回退选择器
        ]
        for selector in candidates:
            try:
                if await page.locator(selector).first.count():
                    try:
                        await page.locator(selector).first.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    
                    # 对于富文本编辑器，可能需要点击激活
                    try:
                        await page.locator(selector).first.click()
                        await page.wait_for_timeout(200)
                    except Exception:
                        pass
                    
                    # 尝试填充内容
                    try:
                        await page.locator(selector).first.fill(self.desc[:2000])
                    except Exception:
                        # 对于 contenteditable 元素，可能需要使用 innerHTML
                        try:
                            await page.locator(selector).first.evaluate(f"el => el.innerHTML = '{self.desc[:2000]}'")
                        except Exception:
                            # 最后尝试输入
                            await page.locator(selector).first.type(self.desc[:2000])
                    return
            except Exception:
                continue

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
                f'div:has-text("{self.bili_type}")',  # div元素
                f'[data-value="{self.bili_type}"]',  # data属性
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
            
            # 1. 首先尝试找到分区选择器并打开下拉菜单
            partition_openers = [
                'div:has-text("分区") select',  # 传统select
                'div:has-text("分区") .ant-select',  # Ant Design选择器
                'div:has-text("分区") .semi-select',  # Semi Design选择器
                'div:has-text("分区") [class*="select"]',  # 通用选择器
                'div:has-text("分区") + div',  # 分区标签后的元素
                '[aria-label*="分区"]',  # 无障碍标签
            ]
            
            dropdown_opened = False
            for opener_sel in partition_openers:
                try:
                    if await page.locator(opener_sel).first.count():
                        await page.locator(opener_sel).first.scroll_into_view_if_needed()
                        await page.locator(opener_sel).first.click()
                        await page.wait_for_timeout(500)  # 等待下拉菜单展开
                        dropdown_opened = True
                        bilibili_logger.info(f"[bilibili] 成功打开分区选择器: {opener_sel}")
                        break
                except Exception:
                    continue
            
            if not dropdown_opened:
                bilibili_logger.warning("[bilibili] 未能打开分区选择器")
                return
            
            # 2. 尝试选择具体的分区选项
            partition_selectors = [
                f'option:has-text("{self.partition}")',  # select option
                f'div[role="option"]:has-text("{self.partition}")',  # 下拉选项
                f'li:has-text("{self.partition}")',  # 列表项
                f'span:has-text("{self.partition}")',  # span文本
                f'div:has-text("{self.partition}")',  # div文本
                f'[title="{self.partition}"]',  # title属性
                f'[data-value*="{self.partition}"]',  # data属性
                f'text={self.partition}',  # 原始文本选择器
            ]
            
            for selector in partition_selectors:
                try:
                    if await page.locator(selector).first.count():
                        await page.locator(selector).first.click()
                        bilibili_logger.info(f"[bilibili] 成功选择分区: {self.partition}")
                        return
                except Exception:
                    continue
            
            bilibili_logger.warning(f"[bilibili] 未能找到分区选项: {self.partition}")
            
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
        
        publish_selectors = [
            'button:has-text("立即投稿")',  # B站标准发布按钮
            'button:has-text("投稿")',  # 简化版本
            'button:has-text("发布")',  # 通用发布
            'button:has-text("提交")',  # 提交按钮
            'button[class*="submit"]',  # 提交类名
            'button[class*="publish"]',  # 发布类名
            '.submit-btn',  # 提交按钮类
            '.publish-btn',  # 发布按钮类
        ]
        
        for selector in publish_selectors:
            try:
                if await page.locator(selector).first.count():
                    await page.locator(selector).first.scroll_into_view_if_needed()
                    await page.locator(selector).first.click()
                    bilibili_logger.info(f"[bilibili] 成功点击发布按钮: {selector}")
                    return
            except Exception as e:
                bilibili_logger.debug(f"[bilibili] 发布按钮选择器失败 {selector}: {e}")
                continue
        
        bilibili_logger.warning("[bilibili] 未找到任何发布按钮")

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
        
        # 首先等待micro-app微前端应用加载完成
        try:
            # 等待micro-app元素出现
            await page.wait_for_selector('micro-app[name="video-up"]', timeout=15000)
            bilibili_logger.info("[bilibili] micro-app detected")
            
            # 等待微应用内容加载
            await page.wait_for_selector('#video-up-app', timeout=10000)
            bilibili_logger.info("[bilibili] video-up-app loaded")
            
            # 等待上传区域完全加载
            await page.wait_for_selector('.bcc-upload-wrapper', timeout=10000)
            bilibili_logger.info("[bilibili] upload wrapper loaded")
            
        except Exception as e:
            bilibili_logger.warning(f"[bilibili] micro-app loading failed: {e}")
        
        # 等待核心上传元素就绪
        ready = False
        for attempt in range(40):  # 增加等待时间，最多等待约20秒
            try:
                # 检查多种可能的上传input（基于实际页面分析）
                upload_selectors = [
                    'input[type="file"][accept*=".mp4"]',  # 视频上传
                    '.bcc-upload-wrapper input[type="file"]',  # B站上传组件
                    'input[name="buploader"]',  # B站动态生成的上传器
                    'input[type="file"][multiple]',  # 多文件上传
                ]
                
                for selector in upload_selectors:
                    if await page.locator(selector).count():
                        bilibili_logger.info(f"[bilibili] upload input found: {selector}")
                        ready = True
                        break
                        
                if ready:
                    break
                    
                # 检查是否有标题输入框作为备用判断（说明已进入编辑页面）
                for sel in (
                    'input[placeholder*="标题"]',
                    'input[placeholder="请输入稿件标题"]',
                    'input[maxlength="80"]',
                ):
                    if await page.locator(sel).count():
                        bilibili_logger.info(f"[bilibili] title input found: {sel}")
                        ready = True
                        break
                        
                if ready:
                    break
                    
            except Exception as e:
                bilibili_logger.debug(f"[bilibili] waiting attempt {attempt + 1}: {e}")
                
            await page.wait_for_timeout(500)
        
        if not ready:
            bilibili_logger.error("[bilibili] page readiness check failed")
        else:
            bilibili_logger.info("[bilibili] page ready confirmed")

        bilibili_logger.info("[bilibili] locate upload input")
        # 基于chrome-mcp实际页面分析的文件上传选择器
        file_inputs = [
            '.bcc-upload-wrapper input[type="file"]',  # B站上传组件内的input
            'input[name="buploader"]',  # B站动态生成的上传器（不限制accept）
            'input[type="file"][accept*=".mp4"]',  # 视频文件上传
            'input[type="file"][multiple]',  # 多文件上传
            'div[id*="b-uploader-input-container"] input[type="file"]',  # B站上传容器
            'div[class*="upload"] input[type="file"]',  # 通用上传容器
            'input[type="file"]',  # 最后的回退选择器
        ]
        uploaded = False
        for selector in file_inputs:
            try:
                if await page.locator(selector).first.count():
                    try:
                        await page.locator(selector).first.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    await page.locator(selector).first.set_input_files(self.file_path)
                    uploaded = True
                    break
            except Exception:
                continue
        if not uploaded:
            # 尝试检测是否在登录页，给出更明确错误
            login_indicators = [
                'a:has-text("登录")',
                'button:has-text("登录")',
                'iframe[src*="passport"]',
            ]
            for sel in login_indicators:
                try:
                    if await page.locator(sel).count():
                        raise RuntimeError("bilibili cookie invalid; please re-login")
                except Exception:
                    continue
            raise RuntimeError("bilibili upload input not found")

        bilibili_logger.info("[bilibili] upload triggered; fill title/tags/desc/type/partition/schedule")
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

        # 发布时间暂不支持（B站可能需要更复杂表单/资质）
        bilibili_logger.info("[bilibili] click publish")
        await self._click_publish(page)

        # 保存cookie
        await context.storage_state(path=str(self.account_file))

        # 调试阶段：不关闭浏览器
        bilibili_logger.info("[bilibili] keep browser open for debug")
        OPEN_DEBUG_BROWSERS.append(browser)

    async def main(self) -> None:
        from playwright.async_api import async_playwright
        async with async_playwright() as playwright:
            await self.upload(playwright)


