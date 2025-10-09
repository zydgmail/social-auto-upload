import asyncio
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from queue import Queue
from flask_cors import CORS
from myUtils.auth import check_cookie
from flask import Flask, request, jsonify, Response, render_template, send_from_directory
from conf import BASE_DIR
from myUtils.login import get_tencent_cookie, douyin_cookie_gen, get_ks_cookie, xiaohongshu_cookie_gen, bilibili_cookie_gen
from myUtils.postVideo import post_video_tencent, post_video_DouYin, post_video_ks, post_video_xhs
from myUtils.postVideo import post_video_bilibili
from utils.base_social_media import launch_chromium_with_codecs, set_init_script
from playwright.async_api import async_playwright


active_queues = {}
_open_browsers = []  # keep references to prevent GC/auto-close

# 全局账号验证缓存时间（秒），默认 3600 秒（1 小时）
ACCOUNT_STATUS_TTL_SECONDS = int(os.getenv('ACCOUNT_STATUS_TTL_SECONDS', '3600'))
# 上次完整验证时间戳
_last_accounts_validation_ts: float = 0.0

# Detect frontend dist directory for portable serving
ROOT_DIR = Path(__file__).resolve().parent

def _find_frontend_dist():
    candidates = [
        ROOT_DIR / "frontend" / "dist",
        ROOT_DIR.parent / "frontend" / "dist",
    ]
    for p in candidates:
        if (p / "index.html").exists():
            return p
    return ROOT_DIR / "frontend"

FRONTEND_DIST = _find_frontend_dist()
print(f"FRONTEND_DIST: {FRONTEND_DIST}")

def initialize_database() -> None:
    db_dir = Path(BASE_DIR / "db")
    db_dir.mkdir(parents=True, exist_ok=True)
    db_file = db_dir / "database.db"
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute('''
CREATE TABLE IF NOT EXISTS user_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type INTEGER NOT NULL,
    filePath TEXT NOT NULL,
    userName TEXT NOT NULL,
    status INTEGER DEFAULT 0
)
''')
        cursor.execute('''
CREATE TABLE IF NOT EXISTS file_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filesize REAL,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT
)
''')
        conn.commit()
    print("✅ 数据库已初始化")

app = Flask(__name__, static_folder=str(FRONTEND_DIST))

#允许所有来源跨域访问
CORS(app)

# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

@app.route('/')
def hello_world():
    return app.send_static_file('index.html')

# SPA fallback: serve files if exist, else index.html
@app.route('/<path:path>')
def spa_fallback(path):
    target = FRONTEND_DIST / path
    if target.exists() and target.is_file():
        return send_from_directory(str(FRONTEND_DIST), path)
    return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No file part in the request"
        }), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No selected file"
        }), 400
    try:
        # 保存文件到指定位置
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{file.filename}")
        file.save(filepath)
        return jsonify({"code":200,"msg": "File uploaded successfully", "data": f"{uuid_v1}_{file.filename}"}), 200
    except Exception as e:
        return jsonify({"code":200,"msg": str(e),"data":None}), 500

@app.route('/getFile', methods=['GET'])
def get_file():
    # 获取 filename 参数
    filename = request.args.get('filename')

    if not filename:
        return {"error": "filename is required"}, 400

    # 防止路径穿越攻击
    if '..' in filename or filename.startswith('/'):
        return {"error": "Invalid filename"}, 400

    # 拼接完整路径
    file_path = str(Path(BASE_DIR / "videoFile"))

    # 返回文件
    return send_from_directory(file_path,filename)


@app.route('/uploadSave', methods=['POST'])
def upload_save():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400

    # 获取表单中的自定义文件名（可选）
    custom_filename = request.form.get('filename', None)
    if custom_filename:
        filename = custom_filename + "." + file.filename.split('.')[-1]
    else:
        filename = file.filename

    try:
        # 生成 UUID v1
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 构造文件名和路径
        final_filename = f"{uuid_v1}_{filename}"
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{filename}")
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file.save(filepath)

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO file_records (filename, filesize, file_path)
            VALUES (?, ?, ?)
                                ''', (filename, round(float(os.path.getsize(filepath)) / (1024 * 1024),2), final_filename))
            conn.commit()
            print("✅ 上传文件已记录")

        return jsonify({
            "code": 200,
            "msg": "File uploaded and saved successfully",
            "data": {
                "filename": filename,
                "filepath": final_filename
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("upload failed!"),
            "data": None
        }), 500

@app.route('/getFiles', methods=['GET'])
def get_all_files():
    try:
        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute("SELECT * FROM file_records")
            rows = cursor.fetchall()

            # 将结果转为字典列表
            data = [dict(row) for row in rows]

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500


@app.route("/getValidAccounts",methods=['GET'])
async def getValidAccounts():
    """
    获取账号列表。
    可选参数：
      - validate: 1/true 表示触发校验；0/false 表示仅返回数据库缓存状态（更快）。默认 0。
      - force: 1/true 表示忽略 TTL 强制校验。
      - ids: 可选，逗号分隔的账号 id 列表。提供时，仅对这些账号执行校验，其余账号保留缓存状态。
    说明：
      - 为避免频繁打开浏览器验证，增加了 TTL，默认 1 小时内重复请求不会再次校验。
    """
    global _last_accounts_validation_ts

    validate = request.args.get('validate', '0').lower() in ('1', 'true', 'yes')
    force = request.args.get('force', '0').lower() in ('1', 'true', 'yes')
    ids_param = request.args.get('ids', '').strip()
    selected_ids = set()
    if ids_param:
        try:
            selected_ids = {int(x) for x in ids_param.split(',') if x.strip().isdigit()}
        except Exception:
            selected_ids = set()

    now_ts = time.time()
    should_validate = validate and (force or (now_ts - _last_accounts_validation_ts >= ACCOUNT_STATUS_TTL_SECONDS))

    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM user_info''')
        rows = cursor.fetchall()
        rows_list = [list(row) for row in rows]

        # 快速返回：不需要校验时，直接返回数据库中的缓存状态
        if not should_validate:
            return jsonify({
                "code": 200,
                "msg": None,
                "data": rows_list
            }), 200

        print("\n📋 开始账号有效性校验（可能需数秒）...")
        any_updated = False
        for row in rows_list:
            # row: [id, type, filePath, userName, status]
            try:
                # 若指定了 selected_ids，则只校验被选中的账号，其余账号跳过
                if selected_ids and row[0] not in selected_ids:
                    continue
                # 预览模式：当请求带 preview=1 时打开可视化浏览器以便观察
                preview = request.args.get('preview', '0').lower() in ('1', 'true', 'yes')
                platform = {1: 'xhs', 2: 'tencent', 3: 'douyin', 4: 'kuaishou'}.get(row[1], 'unknown')
                print(f"   - 正在校验 [{platform}] 账号: id={row[0]} user={row[3]}")
                flag = await check_cookie(row[1], row[2], preview=preview)
                print(f"     → [{platform}] 结果: {'cookie 有效' if flag else 'cookie 失效'}")
            except Exception as e:
                # 出错时保守置为无效
                print(f"check_cookie 出错: platform={row[1]} id={row[0]} user={row[3]} err={e}")
                flag = False

            new_status = 1 if flag else 0
            if row[4] != new_status:
                row[4] = new_status
                cursor.execute('''
                UPDATE user_info 
                SET status = ? 
                WHERE id = ?
                ''', (new_status, row[0]))
                any_updated = True

        if any_updated:
            conn.commit()
            print("✅ 用户状态已更新并写入数据库")
        else:
            print("ℹ️ 用户状态无变更，保持现状")

        _last_accounts_validation_ts = time.time()

        return jsonify({
            "code": 200,
            "msg": None,
            "data": rows_list
        }), 200

@app.route('/deleteFile', methods=['GET'])
def delete_file():
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

@app.route('/batchDeleteFiles', methods=['POST'])
def batch_delete_files():
    data = request.get_json()
    
    if not data or 'ids' not in data:
        return jsonify({
            "code": 400,
            "msg": "Missing or invalid request data",
            "data": None
        }), 400
    
    ids = data['ids']
    
    if not isinstance(ids, list) or len(ids) == 0:
        return jsonify({
            "code": 400,
            "msg": "Invalid IDs list",
            "data": None
        }), 400
    
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查询要删除的记录
            placeholders = ','.join(['?' for _ in ids])
            cursor.execute(f"SELECT * FROM file_records WHERE id IN ({placeholders})", ids)
            records = cursor.fetchall()
            
            if not records:
                return jsonify({
                    "code": 404,
                    "msg": "No files found",
                    "data": None
                }), 404
            
            # 删除数据库记录
            cursor.execute(f"DELETE FROM file_records WHERE id IN ({placeholders})", ids)
            conn.commit()
            
            deleted_count = cursor.rowcount
            
        return jsonify({
            "code": 200,
            "msg": f"Successfully deleted {deleted_count} files",
            "data": {
                "deleted_count": deleted_count,
                "deleted_ids": ids
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("Batch delete failed!"),
            "data": None
        }), 500

@app.route('/deleteAccount', methods=['GET'])
def delete_account():
    account_id = int(request.args.get('id'))

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500


# SSE 登录接口
@app.route('/login')
def login():
    # 1 小红书 2 视频号 3 抖音 4 快手
    type = request.args.get('type')
    # 账号名
    id = request.args.get('id')
    # 是否更新已有记录
    update_mode = request.args.get('update', '0') in ('1', 'true', 'True')
    record_id = request.args.get('record_id')

    # 模拟一个用于异步通信的队列
    status_queue = Queue()
    active_queues[id] = status_queue

    def on_close():
        print(f"清理队列: {id}")
        del active_queues[id]
    # 启动异步任务线程
    thread = threading.Thread(target=run_async_function, args=(type,id,status_queue, update_mode, record_id), daemon=True)
    thread.start()
    response = Response(sse_stream(status_queue,), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/postVideo', methods=['POST'])
def postVideo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取fileList和accountList
    file_list = data.get('fileList', [])
    account_list = data.get('accountList', [])
    type = data.get('type')
    title = data.get('title')
    tags = data.get('tags')
    category = data.get('category')
    enableTimer = data.get('enableTimer')
    cover_path = data.get('coverPath')  # 可选封面路径（相对 videoFile 下的存储名）
    # B站专用字段
    bili_desc = data.get('biliDesc')
    bili_type = data.get('biliType')  # 自制/转载
    bili_partition = data.get('biliPartition')
    if category == 0:
        category = None

    videos_per_day = data.get('videosPerDay')
    daily_times = data.get('dailyTimes')
    start_days = data.get('startDays')
    # 打印获取到的数据（仅作为示例）
    print("File List:", file_list)
    print("Account List:", account_list)
    match type:
        case 1:
            post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                               start_days, cover_path=cover_path)
        case 2:
            post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                               start_days, cover_path=cover_path)
        case 3:
            post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days, cover_path=cover_path)
        case 4:
            post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days, cover_path=cover_path)
        case 5:
            post_video_bilibili(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days, desc=bili_desc, bili_type=bili_type, bili_partition=bili_partition, cover_path=cover_path)
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200


@app.route('/openAccounts', methods=['POST'])
def open_accounts():
    data = request.get_json() or {}
    ids = data.get('ids', [])
    if not isinstance(ids, list) or not ids:
        return jsonify({
            "code": 400,
            "msg": "ids required",
            "data": None
        }), 200

    # 查询账号信息
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        # rows: [id, type, filePath, userName, status]
        placeholders = ",".join(["?"] * len(ids))
        cursor.execute(f"SELECT id, type, filePath, userName, status FROM user_info WHERE id IN ({placeholders})", tuple(ids))
        rows = cursor.fetchall()

    if not rows:
        return jsonify({
            "code": 404,
            "msg": "accounts not found",
            "data": None
        }), 200

    def run_open_tabs(rows_):
        async def open_tabs_async():
            p = await async_playwright().start()
            browser = await launch_chromium_with_codecs(p, headless=False, executable_path=None)
            _open_browsers.append(browser)
            # 平台登录后页面地址
            url_map = {
                1: "https://creator.xiaohongshu.com/new/note-manager",
                2: "https://channels.weixin.qq.com/platform/post/list",
                3: "https://creator.douyin.com/creator-micro/content/manage",
                4: "https://cp.kuaishou.com/article/publish/video",
                5: "https://member.bilibili.com/platform/upload-manager/article",
            }
            for (acc_id, acc_type, file_path, user_name, _status) in rows_:
                try:
                    context = await browser.new_context(storage_state=str(Path(BASE_DIR / "cookiesFile" / file_path)))
                    context = await set_init_script(context)
                    page = await context.new_page()
                    url = url_map.get(acc_type) or "https://www.baidu.com"
                    await page.goto(url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(500)
                    # 命名标签便于识别
                    try:
                        await page.evaluate("document.title = document.title + ' - ' + arguments[0]", user_name)
                    except Exception:
                        pass
                except Exception as e:
                    print(f"open tab failed id={acc_id} err={e}")
            # 保持浏览器打开，直到进程退出（避免意外自动关闭）
            print("[openAccounts] Tabs opened, holding browser open...")
            try:
                while True:
                    await asyncio.sleep(3600)
            finally:
                # do not stop playwright/browsers here to allow persistence if loop ends unexpectedly
                pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(open_tabs_async())
        finally:
            loop.close()

    t = threading.Thread(target=run_open_tabs, args=(rows,), daemon=True)
    t.start()

    return jsonify({
        "code": 200,
        "msg": None,
        "data": {"opened": len(rows)}
    }), 200


@app.route('/updateUserinfo', methods=['POST'])
def updateUserinfo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取 type 和 userName
    user_id = data.get('id')
    type = data.get('type')
    userName = data.get('userName')
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 更新数据库记录
            cursor.execute('''
                           UPDATE user_info
                           SET type     = ?,
                               userName = ?
                           WHERE id = ?;
                           ''', (type, userName, user_id))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account update successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("update failed!"),
            "data": None
        }), 500

@app.route('/postVideoBatch', methods=['POST'])
def postVideoBatch():
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"error": "Expected a JSON array"}), 400
    for data in data_list:
        # 从JSON数据中提取fileList和accountList
        file_list = data.get('fileList', [])
        account_list = data.get('accountList', [])
        type = data.get('type')
        title = data.get('title')
        tags = data.get('tags')
        category = data.get('category')
        enableTimer = data.get('enableTimer')
        if category == 0:
            category = None

        videos_per_day = data.get('videosPerDay')
        daily_times = data.get('dailyTimes')
        start_days = data.get('startDays')
        # 打印获取到的数据（仅作为示例）
        print("File List:", file_list)
        print("Account List:", account_list)
        match type:
            case 1:
                return
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200

# 包装函数：在线程中运行异步函数
def run_async_function(type,id,status_queue, update_mode=False, record_id=None):
    cookiesFile_dir = Path(BASE_DIR / "cookiesFile")
    cookiesFile_dir.mkdir(parents=False, exist_ok=True)
    match type:
        case '1':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(xiaohongshu_cookie_gen(id, status_queue, update_mode, record_id))
            loop.close()
        case '2':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_tencent_cookie(id,status_queue, update_mode, record_id))
            loop.close()
        case '3':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(douyin_cookie_gen(id,status_queue, update_mode, record_id))
            loop.close()
        case '4':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_ks_cookie(id,status_queue, update_mode, record_id))
            loop.close()
        case '5':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bilibili_cookie_gen(id,status_queue, update_mode, record_id))
            loop.close()

# SSE 流生成器函数
def sse_stream(status_queue):
    while True:
        if not status_queue.empty():
            msg = status_queue.get()
            yield f"data: {msg}\n\n"
        else:
            # 避免 CPU 占满
            time.sleep(0.1)

if __name__ == '__main__':
    initialize_database()
    app.run(host='0.0.0.0' ,port=5409)
