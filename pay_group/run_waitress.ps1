<#
run_waitress.ps1
Use Waitress to run the Flask app on Windows.
Usage:
.\run_waitress.ps1 -Port 5000
#>
param(
    [int]$Port = 5000
)

Write-Output "激活虚拟环境并运行 Waitress on port $Port"
& .\.venv\Scripts\Activate.ps1; python -m waitress --listen=0.0.0.0:$Port app:app
