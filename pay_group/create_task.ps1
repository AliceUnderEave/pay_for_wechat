<#
在 Windows 上创建一个定时任务（Task Scheduler），用于每天运行 update_group_qr.py。
用法（以管理员身份运行 PowerShell）：
.\create_task.ps1 -TaskName "PayGroup_UpdateQR" -PythonPath "C:\path\to\venv\Scripts\python.exe" -ScriptPath "C:\path\to\pay_group\update_group_qr.py" -TriggerDaily

此脚本会创建一个每天 03:00 运行的任务。
#>
param(
    [string]$TaskName = 'PayGroup_UpdateQR',
    [string]$PythonPath = 'C:\Python39\python.exe',
    [string]$ScriptPath = "$PSScriptRoot\update_group_qr.py",
    [switch]$TriggerDaily
)

$action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`""
$trigger = if ($TriggerDaily) { New-ScheduledTaskTrigger -Daily -At 3am } else { New-ScheduledTaskTrigger -AtStartup }

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -RunLevel Highest -Force

Write-Output "Scheduled task '$TaskName' created. Check Task Scheduler to confirm settings."
