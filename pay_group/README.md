项目说明
========

此项目为“付费入群”示例，包含自动解析微信群二维码并重新生成可用于展示的入群二维码的功能。由于微信生成的临时群码通常只有 7 天有效，本项目支持手动上传最新群二维码或使用定时任务自动更新生成的入群二维码。

主要文件
- `app.py`：Flask 应用，提供上传页面 `/upload_group_qr`，并生成 `static/group_qr_latest.png` 供前端展示。
- `templates/upload_group_qr.html`：上传页面模板。
- `update_group_qr.py`：独立运行的更新脚本，从 `static/uploads` 中读取最新上传图片并生成 `static/group_qr_latest.png`。
- `create_task.ps1`：用于在 Windows 任务计划中创建定时任务的 helper 脚本。
- `requirements.txt`：依赖清单。

运行与部署
-----------
1. 安装依赖：

```powershell
pip install -r requirements.txt
```

2. 本地开发运行：

```powershell
python app.py
```

3. 定时自动更新：
- Windows：使用“任务计划程序”（Task Scheduler）定期运行：

```powershell
python update_group_qr.py
```

- Linux：使用 `cron` 定时运行：

```bash
# 每天 00:30 运行（示例）
30 0 * * * /usr/bin/python3 /path/to/pay_group/update_group_qr.py
```

Windows 部署说明
----------------

1. 在服务器上创建并激活虚拟环境：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. 设置环境变量（建议通过系统环境变量或在任务计划中配置）：

```powershell
# 示例（根据实际值设置）：
$env:WECHAT_APPID='...'; $env:WECHAT_MCH_ID='...'; $env:WECHAT_API_KEY='...';
$env:FLASK_SECRET='...'; $env:UPLOAD_TOKEN='your-upload-token'
```

3. 测试运行（开发）：

```powershell
python app.py
```

4. 使用 `create_task.ps1` 快速在任务计划中创建每日任务（以管理员身份运行 PowerShell，并根据实际路径修改参数）：

```powershell
.\create_task.ps1 -TaskName "PayGroup_UpdateQR" -PythonPath "C:\path\to\venv\Scripts\python.exe" -ScriptPath "C:\path\to\pay_group\update_group_qr.py" -TriggerDaily
```

5. 生产环境建议：使用 Waitress 或 IIS 作为 WSGI 容器，并通过反向代理（如 IIS/NGINX）或负载均衡器提供 HTTPS 访问。

注意事项
--------
- 微信生成的群二维码通常只有 7 天有效，建议每天或每 48 小时刷新一次。
- `pyzbar` 在 Windows 上需要 zbar 支持；如果使用 pip 安装遇到问题，可通过 Chocolatey 或 conda 安装 zbar。
- 请确保 `static/uploads` 目录可写，并为上传接口启用访问控制（例如 `UPLOAD_TOKEN`）以防止滥用。

需要我继续帮你：
- 生成自动安装脚本（`install.ps1`），自动创建虚拟环境并尝试安装 zbar（通过 Chocolatey）。
- 为生产部署生成 Waitress 示例与 Task Scheduler 完整示例（含真实路径）。
说明
=====

本项目为付费入群示例，新增了自动解析微信群二维码并生成可长期使用的入群二维码的功能（定期更新或在每次上传时更新）。

主要文件：
- `app.py` - Flask 应用，增加了 `/upload_group_qr` 上传页，自动解析并生成 `static/group_qr_latest.png`。
- `templates/upload_group_qr.html` - 上传页面。
- `update_group_qr.py` - 可单独运行的脚本，用于从 `static/uploads` 解析最新上传图片并生成 `static/group_qr_latest.png`。
- `requirements.txt` - 依赖清单。

运行与部署
-----------
1. 安装依赖：

```powershell
pip install -r requirements.txt
```
2. 运行 Flask（仅开发测试）：

```powershell
python app.py
```

3. 使用定时任务自动更新：
- Windows：使用“任务计划程序”每天调用：

```powershell
python update_group_qr.py
```

- Linux：使用 cron：

```bash
# 每天 00:30 运行
30 0 * * * /usr/bin/python3 /path/to/pay_group/update_group_qr.py
```

注意事项
--------
- 微信生成的微信群二维码通常只有 7 天有效，务必定期上传最新二维码图片。
- `pyzbar` 在部分平台需要额外安装 zbar 库（系统包）。
- 请确保 `static/uploads` 可写，并限制上传来源以防滥用。

如需我帮助把更新脚本加入 Windows 任务计划或部署到 VPS 的 systemd 服务，请告诉我你的服务器环境。
