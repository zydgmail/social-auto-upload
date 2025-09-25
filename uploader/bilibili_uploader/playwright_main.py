import asyncio
import os
from datetime import datetime
from pathlib import Path
import time

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
        ]
        for selector in candidates:
            try:
                if await page.locator(selector).first.count():
                    try:
                        await page.locator(selector).first.scroll_into_view_if_needed()
                        bilibili_logger.info(f"[bilibili] 标题输入框已滚动到可见位置: {selector}")
                    except Exception:
                        pass
                    await page.locator(selector).first.fill(self.title[:80])
                    bilibili_logger.info(f"[bilibili] 标题已填写: {self.title[:80]}")
                    return
                bilibili_logger.warning(f"[bilibili] 未能找到标题输入框: {selector}")
            except Exception:
                continue

    async def _fill_tags(self, page) -> None:
        if not self.tags:
            return
        # 基于实际B站页面的选择器（探测结果：placeholder="按回车键Enter创建标签"）
        candidates = [
            'input[placeholder*="标签"]',  # 主要选择器，已验证有效
            'input[placeholder*="按回车键Enter创建标签"]',  # 精确匹配
        ]
        for selector in candidates:
            try:
                if await page.locator(selector).first.count():
                    try:
                        await page.locator(selector).first.scroll_into_view_if_needed()
                        bilibili_logger.info(f"[bilibili] 标签输入框已滚动到可见位置: {selector}")
                    except Exception:
                        pass
                    # 聚焦输入框并先清空已有内容（长按删除 + 选择删除 双保险）
                    try:
                        await page.locator(selector).first.click()
                        await asyncio.sleep(0.2)
                        for _ in range(10):
                            await page.keyboard.press('Backspace')
                            await asyncio.sleep(0.02)
                        bilibili_logger.info("[bilibili] 已清空标签输入框")
                    except Exception as e:
                        bilibili_logger.warning(f"[bilibili] 清空标签输入框失败: {e}")
                    for tag in self.tags:
                        await page.locator(selector).first.type(tag)
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(0.5)
                        bilibili_logger.info(f"[bilibili] 标签已填写: {tag}")
                    return
                bilibili_logger.warning(f"[bilibili] 未能找到标签输入框: {selector}")
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
                        bilibili_logger.info(f"[bilibili] 简介输入框已滚动到可见位置: {selector}")
                    except Exception:
                        pass
                    
                    # 输入内容
                    await page.locator(selector).first.fill(self.desc[:2000])
                    bilibili_logger.info(f"[bilibili] 简介已填写: {self.desc[:2000]}")
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
            bilibili_logger.info(f"[bilibili] 正在选择类型: {self.bili_type}")

            # 先限制在微应用容器内，避免命中弹窗/批量填充对话框中的同名项
            container = page.locator('#video-up-app').first

            if self.bili_type == "自制":
                # 更精确：仅点击类型单选的名称节点
                await container.locator('.check-radio-v2-name:has-text("自制")').first.click()
                bilibili_logger.info("[bilibili] 成功选择类型: 自制")
            elif self.bili_type == "转载":
                await container.locator('.check-radio-v2-name:has-text("转载")').first.click()
                bilibili_logger.info("[bilibili] 成功选择类型: 转载")
            else:
                bilibili_logger.warning(f"[bilibili] 未知的类型: {self.bili_type}，支持的类型: 自制, 转载")

        except Exception as e:
            bilibili_logger.warning(f"[bilibili] 类型选择失败: {e}")

    async def _set_partition(self, page) -> None:
        # 基于实际B站页面的分区选择
        if not self.partition:
            return
        
        try:
            bilibili_logger.info(f"[bilibili] 正在选择分区: {self.partition}")
            
            # 1. 点击下拉框展开选项（限定在微应用容器且定位到“分区”这一项）
            container = page.locator('#video-up-app').first
            opener_candidates = [
                '.setting-item:has-text("分区") .select-controller',
                '.select-area:has-text("分区") .select-controller',
                '.select-controller'
            ]
            clicked = False
            for oc in opener_candidates:
                try:
                    if await container.locator(oc).count():
                        await container.locator(oc).first.scroll_into_view_if_needed()
                        await container.locator(oc).first.click()
                        bilibili_logger.info(f"[bilibili] 分区下拉框已点击: {oc}")
                        clicked = True
                        break
                except Exception:
                    continue
            if not clicked:
                bilibili_logger.warning("[bilibili] 未找到分区下拉触发器")
                return
            
            # 等待下拉菜单展开
            await page.wait_for_timeout(500)
            
            # 2. 选择指定的分区选项
            # 使用多种选择器尝试匹配分区
            partition_selectors = [
                f'div.select-dropdown >> text={self.partition}',  # 精确匹配，在当前下拉菜单中
                f'.select-dropdown .select-item-cont:has-text("{self.partition}")',
                f'.select-item-cont:has-text("{self.partition}")',  # 回退
                f'text={self.partition}',  # 最后回退
            ]
            
            option_selected = False
            for selector in partition_selectors:
                try:
                    if await container.locator(selector).count():
                        bilibili_logger.info(f"[bilibili] 找到分区选项: {selector}")
                        await container.locator(selector).first.click()
                        option_selected = True
                        bilibili_logger.info(f"[bilibili] 成功选择分区: {self.partition}")
                        break
                except Exception as e:
                    bilibili_logger.warning(f"[bilibili] 分区选项 {selector} 点击失败: {e}")
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
        if not self.publish_date or self.publish_date == 0:
            return
            
        try:
            bilibili_logger.info("[bilibili] 开始设置定时发布")
            
            # 1. 点击定时发布开关
            switch_selectors = [
                '.switch-container',  # 基于您提供的HTML结构
                '.time-switch-wrp .switch-container',  # 更精确的选择器
                'div[class*="switch-container"]',  # 包含switch-container的元素
            ]
            
            switch_clicked = False
            for selector in switch_selectors:
                try:
                    if await page.locator(selector).count():
                        await page.locator(selector).first.click()
                        bilibili_logger.info(f"[bilibili] 定时发布开关已点击: {selector}")
                        await page.wait_for_timeout(500)  # 等待界面展开
                        switch_clicked = True
                        break
                except Exception as e:
                    bilibili_logger.warning(f"[bilibili] 开关点击失败 {selector}: {e}")
            
            if not switch_clicked:
                bilibili_logger.warning("[bilibili] 未能点击定时发布开关")
                return
            
            # 2. 处理发布时间
            from datetime import datetime as _dt
            if isinstance(self.publish_date, str):
                # 如果是字符串格式：'2025-09-25 22:22'
                try:
                    ts = _dt.strptime(self.publish_date, '%Y-%m-%d %H:%M')
                except:
                    bilibili_logger.warning(f"[bilibili] 时间格式解析失败: {self.publish_date}")
                    return
            elif isinstance(self.publish_date, _dt):
                ts = self.publish_date
            elif isinstance(self.publish_date, (int, float)):
                ts = _dt.fromtimestamp(self.publish_date)
            else:
                bilibili_logger.warning(f"[bilibili] 不支持的时间格式: {type(self.publish_date)}")
                return
            
            date_str = ts.strftime('%Y-%m-%d')
            time_str = ts.strftime('%H:%M')
            
            bilibili_logger.info(f"[bilibili] 设置发布时间: {date_str} {time_str}")
            
            # 3. (可选) 设置时区为北京（若存在时区选择器）
            try:
                container = page.locator('#video-up-app').first
                tz_opener = container.locator('.date-picker-timezone-wrp .bcc-select-input-wrap').first
                if await tz_opener.count():
                    await tz_opener.click()
                    await asyncio.sleep(0.2)
                    # 选择含 Beijing 的项
                    tz_option = container.locator('.bcc-select-list-wrap .bcc-option:has-text("Beijing")').first
                    if await tz_option.count():
                        await tz_option.click()
                        bilibili_logger.info('[bilibili] 已设置时区为 Beijing')
                        await asyncio.sleep(0.2)
            except Exception as e:
                bilibili_logger.warning(f"[bilibili] 设置时区失败: {e}")

            # 4. 设置日期
            try:
                # 点击日期选择器
                date_selectors = [
                    '.date-picker-date .date-show',  # 基于HTML结构
                    'p.date-show:has-text("-")',  # 包含日期格式的元素
                    '.date-picker-date-wrp .date-show',  # 日期包装器内的显示元素
                ]
                
                for selector in date_selectors:
                    if await page.locator(selector).count():
                        await page.locator(selector).first.click()
                        await page.wait_for_timeout(300)
                        # 这里可能需要进一步的日期选择逻辑，但B站通常有默认的日期
                        bilibili_logger.info(f"[bilibili] 日期选择器已点击: {selector}")
                        break
            except Exception as e:
                bilibili_logger.warning(f"[bilibili] 日期设置失败: {e}")
            
            # 5. 设置时间
            try:
                # 点击时间选择器
                time_selectors = [
                    '.date-picker-timer .date-show',  # 基于HTML结构
                    'p.date-show:has-text(":")',  # 包含时间格式的元素
                    '.date-picker-timer',  # 时间选择器容器
                ]
                
                for selector in time_selectors:
                    if await page.locator(selector).count():
                        await page.locator(selector).first.click()
                        await page.wait_for_timeout(300)
                        # 这里可能需要进一步的时间选择逻辑
                        bilibili_logger.info(f"[bilibili] 时间选择器已点击: {selector}")
                        break
            except Exception as e:
                bilibili_logger.warning(f"[bilibili] 时间设置失败: {e}")
            
            # 6. 打印回读：页面当前显示的时区/日期/时间，便于对齐前后端
            try:
                container = page.locator('#video-up-app').first
                tz_text = None
                date_text = None
                time_text = None
                try:
                    tz_text = await container.locator('.date-picker-timezone-wrp .bcc-select-input-inner').first.inner_text()
                except Exception:
                    pass
                try:
                    date_text = await container.locator('.date-picker-date .date-show').first.inner_text()
                except Exception:
                    pass
                try:
                    time_text = await container.locator('.date-picker-timer .date-show').first.inner_text()
                except Exception:
                    pass
                bilibili_logger.info(f"[bilibili] 回读定时：tz={tz_text or '-'} date={date_text or '-'} time={time_text or '-'}  (目标: {date_str} {time_str})")
            except Exception:
                pass

            bilibili_logger.info("[bilibili] 定时发布设置完成")
            
        except Exception as e:
            bilibili_logger.warning(f"[bilibili] 定时发布设置失败: {e}")

    async def _dismiss_unsubmitted_prompt(self, page) -> None:
        """轮询几次，如果存在“未提交的视频”提示则点击“不用了”。避免瞬时出现被错过。"""
        try:
            # 最长轮询 ~3 秒（10 次，每次 300ms）
            for _ in range(10):
                try:
                    tip = page.locator('.upload-wrp .entrance-tip').first
                    if await tip.count():
                        bilibili_logger.info('[bilibili] 检测到未提交视频提示，尝试关闭')
                        candidates = [
                            '.upload-wrp .entrance-tip .entrance-tip-btn[data-reporter-id="32"]',
                            '.upload-wrp .entrance-tip .entrance-tip-btn:has-text("不用了")',
                            'text=不用了',
                        ]
                        clicked = False
                        for sel in candidates:
                            try:
                                btn = page.locator(sel).first
                                if await btn.count():
                                    await btn.scroll_into_view_if_needed()
                                    await btn.click()
                                    bilibili_logger.info(f"[bilibili] 已点击‘不用了’: {sel}")
                                    clicked = True
                                    break
                            except Exception:
                                continue
                        if clicked:
                            # 给页面一点时间收起提示
                            await asyncio.sleep(0.3)
                            return
                except Exception:
                    pass
                await asyncio.sleep(0.3)
        except Exception as e:
            bilibili_logger.warning(f"[bilibili] 关闭未提交提示失败: {e}")

    async def _wait_upload_complete(self, page) -> None:
        bilibili_logger.info("[bilibili] 等待视频上传完成...")
        
        # 轮询检测上传完成状态（要求完成状态稳定出现多次，避免误判）
        success_stable_ticks = 0
        container = page.locator('#video-up-app').first
        
        for i in range(180):  # 最多轮询 ~3 分钟
            try:
                # 读取状态容器文本（若有）
                status_text = None
                try:
                    if await container.locator('.file-item-content-status-text').first.count():
                        status_text = (await container.locator('.file-item-content-status-text').first.inner_text() or '').strip()
                except Exception:
                    status_text = None

                # 1) 判断是否仍在上传中
                in_progress = False
                # 文案信号
                if status_text and any(key in status_text for key in ("上传中", "当前速度", "剩余时间")):
                    in_progress = True

                # 2) 判断是否上传完成（结合容器文本/图标/百分比）
                success_found = False
                # 图标/文本标识
                if await container.locator('.file-item-content-status-text .success:has-text("上传完成")').count():
                    success_found = True
                elif status_text and ("上传完成" in status_text):
                    success_found = True

                # 稳定判定：需非上传中且连续3次检测到完成
                bilibili_logger.info(f"[bilibili] success_found: {success_found}, in_progress: {in_progress}")
                if success_found and not in_progress:
                    success_stable_ticks += 1
                    if success_stable_ticks >= 3:
                        bilibili_logger.info("[bilibili] 上传完成状态稳定，继续后续流程")
                        return
                else:
                    success_stable_ticks = 0

                # 每3秒打印一次当前状态
                if i % 3 == 0:
                    if status_text:
                        bilibili_logger.info(f"[bilibili] 上传状态: {status_text}")
                    else:
                        # 回退打印部分结构存在性
                        exists = await container.locator('.upload-audit-progress').count()
                        bilibili_logger.info(f"[bilibili] 仍在等待上传完成... ({i}秒) progress_container={exists>0}")

            except Exception as e:
                bilibili_logger.warning(f"[bilibili] 检测上传状态时出错: {e}")
            
            await asyncio.sleep(1)
        
        bilibili_logger.warning("[bilibili] 上传完成检测超时（3分钟）")

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
        
        # 若存在“未提交的视频”提示，优先关闭
        await self._dismiss_unsubmitted_prompt(page)

        # 选择视频上传输入框（第一个，接受视频格式的）
        video_input_selector = 'input[type="file"][accept*=".mp4"]'
        await page.locator(video_input_selector).first.set_input_files(self.file_path)
        bilibili_logger.info(f"[bilibili] 视频文件已设置: {self.file_path}")

        bilibili_logger.info("[bilibili] wait upload complete")
        # 等待上传完成或稳定
        await self._wait_upload_complete(page)

        await asyncio.sleep(1)
        await self._fill_title(page)
        await asyncio.sleep(1)
        await self._set_type(page)
        await asyncio.sleep(1)
        await self._set_partition(page)
        await asyncio.sleep(1)
        await self._fill_tags(page)
        await asyncio.sleep(1)
        await self._fill_desc(page)
        await asyncio.sleep(1)
        await self._set_schedule(page)

        # 等待300秒再发布（用户观察和确认）
        bilibili_logger.info("[bilibili] waiting n seconds before publish...")
        await asyncio.sleep(120)
        
        # 发布
        bilibili_logger.info("[bilibili] click publish")
        await self._click_publish(page)

        # 保存cookie
        await context.storage_state(path=str(self.account_file))

    async def main(self) -> None:
        from playwright.async_api import async_playwright
        async with async_playwright() as playwright:
            await self.upload(playwright)


