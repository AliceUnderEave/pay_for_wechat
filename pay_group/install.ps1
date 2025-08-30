<#
install.ps1
Windows helper to create a virtual environment, attempt to install zbar via Chocolatey,
and install Python dependencies from requirements.txt.

用法（以管理员权限运行 PowerShell 以便能安装 Chocolatey/zbar）：
.\install.ps1
# 或者传参： .\install.ps1 -PythonExe C:\Python39\python.exe
#
# 注意：如果你的机器已安装 conda，建议用 conda 安装 pyzbar/zbar：
# conda install -c conda-forge pyzbar zbar
#
# 此脚本尽量安全地执行操作：不会覆盖已有虚拟环境。
#>

param(
    [string]$PythonExe = "python",
    [string]$VenvDir = ".venv"
)

Write-Output "使用 Python: $PythonExe"

if (-Not (Test-Path requirements.txt)) {
    Write-Error "找不到 requirements.txt，请在项目根目录运行此脚本。"
    exit 1
}

if (-Not (Test-Path $VenvDir)) {
    & $PythonExe -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Write-Error "创建虚拟环境失败"; exit 2 }
    Write-Output "已创建虚拟环境：$VenvDir"
} else {
    Write-Output "虚拟环境已存在：$VenvDir"
}

$activate = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-Not (Test-Path $activate)) { Write-Error "虚拟环境激活脚本未找到：$activate"; exit 3 }

Write-Output "激活虚拟环境"
. $activate

Write-Output "尝试安装或更新 pip..."
python -m pip install --upgrade pip

Write-Output "尝试通过 Chocolatey 安装 zbar（如果可用）..."
try {
    # 检查 choco
    $choco = Get-Command choco -ErrorAction SilentlyContinue
    if ($choco) {
        choco install zbar -y
    } else {
        Write-Output "Chocolatey 未安装，跳过 zbar 安装，请手动安装 zbar 或使用 conda。"
    }
} catch {
    Write-Output "通过 Chocolatey 安装 zbar 失败，继续安装 Python 依赖。"
}

Write-Output "安装 Python 依赖..."
pip install -r requirements.txt

Write-Output "安装完成。请确认 zbar 是否安装成功（pyzbar 解析依赖 zbar）。若失败，请使用 conda 安装 zbar 或手动放置 zbar DLL 到 PATH。"
<#[
install.ps1
Windows helper to create virtualenv, install Python deps, and (optionally) install zbar via Chocolatey.
Run as Administrator if you want Chocolatey/zbar installation.

Usage:
.\install.ps1
# or specify python path
.\install.ps1 -PythonPath 'C:\Python39\python.exe'
#
# This script does NOT modify system PATH except when Chocolatey installs zbar.
]#>
param(
    [string]$PythonPath = 'python'
)

Write-Output "Using python: $PythonPath"

# create venv
& $PythonPath -m venv .venv
if ($LASTEXITCODE -ne 0) { Write-Error "无法创建虚拟环境"; exit 1 }

Write-Output "激活虚拟环境并安装依赖..."
& .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Error "依赖安装失败"; exit 2 }

# try install zbar via choco if available
if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Output "检测到 Chocolatey，尝试安装 zbar（需要管理员）..."
    choco install zbar -y
} else {
    Write-Output "未检测到 Chocolatey。若需要，请手动安装 zbar 或使用 conda: conda install -c conda-forge pyzbar zbar"
}

Write-Output "安装完成。请根据 README 设置环境变量并测试运行。"
