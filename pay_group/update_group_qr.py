"""周期性从 `static/uploads` 读取最新上传的微信群二维码图片，解析其中的邀请链接，重新生成 `static/group_qr_latest.png`。

用法示例（Windows 任务计划或 cron 调度）:
python update_group_qr.py
"""
from pyzbar.pyzbar import decode
from PIL import Image
import os
import qrcode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
OUTPUT_PATH = os.path.join(BASE_DIR, 'static', 'group_qr_latest.png')


def get_latest_file(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
    if not files:
        return None
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder, x)), reverse=True)
    return os.path.join(folder, files[0])


def extract_qr_link(image_path):
    img = Image.open(image_path)
    result = decode(img)
    for r in result:
        if r.type == 'QRCODE':
            return r.data.decode('utf-8')
    return None


def generate_qr_from_link(link, out_path=OUTPUT_PATH):
    img = qrcode.make(link)
    img.save(out_path)
    return out_path


if __name__ == '__main__':
    latest = get_latest_file(UPLOAD_DIR)
    if not latest:
        print('未找到上传的二维码图片（PNG）。')
        raise SystemExit(1)
    link = extract_qr_link(latest)
    if not link:
        print('未能从图片中解析到邀请链接。')
        raise SystemExit(2)
    out = generate_qr_from_link(link)
    print('已生成新二维码：', out)
