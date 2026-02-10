# 创建定时任务 - 斯坦星球钉钉机器人
$taskName = "StanPlanetDingTalkBot"
$pythonPath = "C:\Users\Frank.J\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$workDir = "c:\Users\Frank.J\starplanet_ai_academy\dingtalk_bot"

# 删除已存在的任务
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# 创建任务
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "bot_stream.py" -WorkingDirectory $workDir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit 0
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "斯坦星球钉钉机器人"

Write-Host "任务创建成功！"
