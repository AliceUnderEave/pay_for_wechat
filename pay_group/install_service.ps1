<#
install_service.ps1
示例：使用 NSSM 将 Waitress 命令注册为 Windows 服务。
需要预先安装 NSSM（https://nssm.cc/）。

示例命令（管理员 PowerShell）：
# nssm install PayGroupService "C:\full\path\to\.venv\Scripts\python.exe" "-m waitress --listen=0.0.0.0:5000 app:app"
# nssm set PayGroupService AppDirectory C:\full\path\to\pay_group
# nssm start PayGroupService

请根据实际路径替换并在管理员权限下运行。
#>

Write-Output "请手动使用 NSSM 注册服务，脚本只提供示例说明。"
