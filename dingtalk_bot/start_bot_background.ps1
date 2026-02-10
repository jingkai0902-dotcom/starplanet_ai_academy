# 斯坦星球钉钉机器人 - 后台启动脚本
$botPath = "c:\Users\Frank.J\starplanet_ai_academy\dingtalk_bot"
$pythonPath = "C:\Users\Frank.J\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$logFile = "$botPath\bot.log"

# 切换到机器人目录
Set-Location $botPath

# 启动机器人，输出重定向到日志文件
Start-Process -FilePath $pythonPath -ArgumentList "bot_stream.py" -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError "$botPath\bot_error.log" -WorkingDirectory $botPath
