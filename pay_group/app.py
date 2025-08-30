
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import logging
from logging.handlers import RotatingFileHandler
from pyzbar.pyzbar import decode
from PIL import Image, UnidentifiedImageError
import qrcode
from wechatpy.pay import WeChatPay
from wechatpy.utils import random_string
from datetime import datetime
import sqlite3
from flask import g, jsonify

app = Flask(__name__)

# Configuration from environment (Windows-friendly)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'change-me')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'static', 'uploads'))
app.config['GROUP_QR_PATH'] = os.environ.get('GROUP_QR_PATH', os.path.join(BASE_DIR, 'static', 'group_qr_latest.png'))
# limit uploads to 2 MB by default
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 2 * 1024 * 1024))
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Database
DATABASE = os.path.join(BASE_DIR, 'pay_group.db')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        out_trade_no TEXT UNIQUE,
        total_fee INTEGER,
        status TEXT,
        created_at TEXT
    )
    ''')
    conn.commit()
    conn.close()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# initialize db at startup (safe to call repeatedly)
init_db()

# Logging
logger = logging.getLogger('pay_group')
logger.setLevel(logging.INFO)
log_path = os.path.join(BASE_DIR, 'logs', 'pay_group.log')
handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

# simple upload protection: set UPLOAD_TOKEN in env to require a token param/header
UPLOAD_TOKEN = os.environ.get('UPLOAD_TOKEN')

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# 微信支付配置（请替换为你的商户信息）
WECHAT_APPID = os.environ.get('WECHAT_APPID')
WECHAT_MCH_ID = os.environ.get('WECHAT_MCH_ID')
WECHAT_API_KEY = os.environ.get('WECHAT_API_KEY')
WECHAT_NOTIFY_URL = os.environ.get('WECHAT_NOTIFY_URL', 'https://你的域名/pay/notify')

pay_client = None
if WECHAT_APPID and WECHAT_MCH_ID and WECHAT_API_KEY:
    try:
        pay_client = WeChatPay(WECHAT_APPID, WECHAT_MCH_ID, WECHAT_API_KEY)
    except Exception as e:
        logger.exception('初始化 WeChatPay 失败: %s', e)
        pay_client = None

# 假设有多个群二维码，文件名如 group_qr_订单号.png，存放于 static 目录


# 获取最新群二维码图片路径
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_latest_group_qr_image():
    folder = app.config['UPLOAD_FOLDER']
    files = [f for f in os.listdir(folder) if allowed_file(f)]
    if not files:
        return None
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder, x)), reverse=True)
    return os.path.join(folder, files[0])

# 解析二维码图片，返回链接
def extract_qr_link(image_path):
    # Try multiple rotations and basic preprocessing to improve decode rate
    try:
        img = Image.open(image_path).convert('RGB')
    except UnidentifiedImageError:
        logger.warning('无法识别上传的图片: %s', image_path)
        return None
    widths = img.size
    # Optionally resize if extremely large
    max_side = max(img.size)
    if max_side > 2000:
        scale = 2000 / max_side
        new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
        img = img.resize(new_size)
    for angle in (0, 90, 180, 270):
        try:
            rotated = img.rotate(angle, expand=True)
            result = decode(rotated)
            for r in result:
                if r.type == 'QRCODE':
                    link = r.data.decode('utf-8')
                    logger.info('解析到二维码链接: %s (angle=%d)', link, angle)
                    return link
        except Exception:
            logger.exception('解析二维码时出错，angle=%d', angle)
    return None

# 生成新的随机二维码图片
def generate_new_group_qr():
    latest_img = get_latest_group_qr_image()
    if not latest_img:
        logger.info('没有找到可用的上传二维码图片')
        return None
    link = extract_qr_link(latest_img)
    if not link:
        logger.info('从最新图片未解析到链接: %s', latest_img)
        return None
    # 生成新二维码图片到指定输出路径
    try:
        qr_img = qrcode.make(link)
        out_path = app.config['GROUP_QR_PATH']
        qr_img.save(out_path)
        logger.info('已生成群二维码: %s', out_path)
        # return path relative to app root for template usage (templates use /{{ group_qr }})
        rel = os.path.relpath(out_path, BASE_DIR)
        return rel.replace('\\', '/')
    except Exception:
        logger.exception('生成二维码时出错')
        return None

@app.route('/')
def index():
    # 展示最新群二维码（生成但不强制每次都重写，如果已存在则使用现有）
    if not os.path.exists(app.config['GROUP_QR_PATH']):
        group_qr_path = generate_new_group_qr()
    else:
        group_qr_path = os.path.relpath(app.config['GROUP_QR_PATH'], BASE_DIR).replace('\\', '/')
    return render_template('index.html', group_qr=group_qr_path)
@app.route('/upload_group_qr', methods=['GET', 'POST'])
def upload_group_qr():
    if request.method == 'POST':
        # optional token protection
        if UPLOAD_TOKEN:
            token = request.form.get('token') or request.headers.get('X-Upload-Token')
            if token != UPLOAD_TOKEN:
                logger.warning('上传失败：token 不匹配，remote=%s', request.remote_addr)
                flash('未授权的上传')
                return redirect(request.url)

        if 'file' not in request.files:
            flash('未选择文件')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('未选择文件')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('只允许 PNG/JPG/JPEG 格式')
            return redirect(request.url)

        # Save with timestamp to avoid collisions
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        filename = f"{name}_{ts}{ext}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Basic content validation: ensure it is an image
        try:
            file.stream.seek(0)
            img = Image.open(file.stream)
            img.verify()  # will raise if not an image
            # Reset stream and save
            file.stream.seek(0)
            file.save(save_path)
            logger.info('上传成功: %s by %s', save_path, request.remote_addr)
            flash('上传成功！')
            # 上传后自动生成新二维码
            generate_new_group_qr()
            return redirect(url_for('index'))
        except UnidentifiedImageError:
            logger.warning('上传失败：非图片文件或无法识别')
            flash('无法识别的图片文件')
            return redirect(request.url)
        except Exception:
            logger.exception('保存上传文件时发生错误')
            flash('上传失败，请稍后重试')
            return redirect(request.url)
    return render_template('upload_group_qr.html')

@app.route('/pay', methods=['POST'])
def pay():
    # 生成订单号
    out_trade_no = random_string(32)
    # 创建微信支付订单（若 pay_client 未配置则仅本地生成模拟二维码）
    total_fee = 100
    code_url = None
    if pay_client:
        try:
            order = pay_client.order.create(
                trade_type='NATIVE',
                body='微信群入群费用',
                total_fee=total_fee,  # 单位：分（如1元=100分）
                notify_url=WECHAT_NOTIFY_URL,
                out_trade_no=out_trade_no
            )
            code_url = order.get('code_url')
        except Exception:
            logger.exception('创建微信支付订单失败，使用本地模拟码')

    if not code_url:
        # 模拟一个 URL（仅用于本地测试）
        code_url = f"https://example.com/pay/{out_trade_no}"

    # persist order in sqlite
    try:
        db = get_db()
        db.execute('INSERT INTO orders (out_trade_no, total_fee, status, created_at) VALUES (?, ?, ?, ?)',
                   (out_trade_no, total_fee, 'PENDING', datetime.utcnow().isoformat()))
        db.commit()
    except Exception:
        logger.exception('写入订单数据库失败')
    # 生成支付二维码图片
    qr_img = qrcode.make(code_url)
    qr_path = os.path.join('static', f'pay_qr_{out_trade_no}.png')
    qr_img.save(qr_path)
    # 支付二维码页面，带订单号
    return render_template('pay_qr.html', qr_path=qr_path, out_trade_no=out_trade_no)

@app.route('/pay/notify', methods=['POST'])
def pay_notify():
    # 处理微信支付回调，务必校验签名（此处为简化示例）
    data = request.get_data()
    logger.info('收到支付回调: %s', data)
    # 如果可以使用 wechatpy 的 Notify 来校验签名，应在此处使用。此处仅做最简单处理：
    # 解析 out_trade_no（实际请解析 XML/JSON，根据微信回调格式）
    # 简化：尝试从 form 或 json 中读取 out_trade_no
    out_trade_no = request.form.get('out_trade_no') or (request.json and request.json.get('out_trade_no'))
    if not out_trade_no:
        logger.warning('回调请求未包含 out_trade_no')
        return 'fail'

    try:
        db = get_db()
        cur = db.execute('SELECT * FROM orders WHERE out_trade_no=?', (out_trade_no,))
        row = cur.fetchone()
        if not row:
            logger.warning('回调的订单不存在: %s', out_trade_no)
            return 'fail'
        # 更新订单状态为 SUCCESS
        db.execute('UPDATE orders SET status=? WHERE out_trade_no=?', ('SUCCESS', out_trade_no))
        db.commit()
        logger.info('订单 %s 更新为 SUCCESS', out_trade_no)
        return 'success'
    except Exception:
        logger.exception('处理回调时出错')
        return 'fail'

@app.route('/pay_success/<out_trade_no>')
def pay_success(out_trade_no):
    # 展示最新自动生成的群二维码（静态路径）
    group_qr_path = os.path.relpath(app.config['GROUP_QR_PATH'], BASE_DIR).replace('\\', '/')
    return render_template('pay_success.html', group_qr=group_qr_path)

if __name__ == '__main__':
    app.run(debug=True)
