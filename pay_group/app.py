
from flask import Flask, render_template, request, redirect, url_for
import os
import qrcode
from wechatpy.pay import WeChatPay
from wechatpy.utils import random_string

app = Flask(__name__)

# 微信支付配置（请替换为你的商户信息）
WECHAT_APPID = '你的微信APPID'
WECHAT_MCH_ID = '你的商户号'
WECHAT_API_KEY = '你的API密钥'
WECHAT_NOTIFY_URL = 'https://你的域名/pay/notify'  # 支付结果回调地址

pay_client = WeChatPay(WECHAT_APPID, WECHAT_MCH_ID, WECHAT_API_KEY)

# 假设有多个群二维码，文件名如 group_qr_订单号.png，存放于 static 目录

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pay', methods=['POST'])
def pay():
    # 生成订单号
    out_trade_no = random_string(32)
    # 创建微信支付订单
    order = pay_client.order.create(
        trade_type='NATIVE',
        body='微信群入群费用',
        total_fee=100,  # 单位：分（如1元=100分）
        notify_url=WECHAT_NOTIFY_URL,
        out_trade_no=out_trade_no
    )
    code_url = order['code_url']
    # 生成支付二维码图片
    qr_img = qrcode.make(code_url)
    qr_path = os.path.join('static', f'pay_qr_{out_trade_no}.png')
    qr_img.save(qr_path)
    # 支付二维码页面，带订单号
    return render_template('pay_qr.html', qr_path=qr_path, out_trade_no=out_trade_no)

@app.route('/pay/notify', methods=['POST'])
def pay_notify():
    # 这里处理微信支付回调，确认支付成功
    # 实际项目需校验签名和订单状态
    # 示例：直接返回成功
    return 'success'

@app.route('/pay_success/<out_trade_no>')
def pay_success(out_trade_no):
    # 假设每个订单都分配一个群邀请链接（实际可从数据库或配置获取）
    group_invite_url = 'https://weixin.qq.com/g/your_group_invite_link'  # 替换为实际群邀请链接
    # 自动生成二维码图片
    group_qr_path = os.path.join('static', f'group_qr_{out_trade_no}.png')
    if not os.path.exists(group_qr_path):
        qr_img = qrcode.make(group_invite_url)
        qr_img.save(group_qr_path)
    return render_template('pay_success.html', group_qr=group_qr_path)

if __name__ == '__main__':
    app.run(debug=True)
