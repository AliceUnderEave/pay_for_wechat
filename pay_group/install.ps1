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
