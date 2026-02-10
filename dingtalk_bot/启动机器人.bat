@echo off
chcp 65001 >nul
title 斯坦星球钉钉机器人

echo ========================================
echo    斯坦星球知识库钉钉机器人
echo ========================================
echo.

REM 检查配置文件
if not exist "config.json" (
    echo [错误] 未找到 config.json 配置文件
    echo 请复制 config.example.json 为 config.json 并填写配置
    pause
    exit /b 1
)

REM 检查知识库
if not exist "knowledge_base\_index.json" (
    echo [警告] 知识库尚未初始化，正在转换...
    python convert_kb.py
    echo.
)

echo [启动] 正在启动机器人...
echo [地址] http://localhost:8080
echo [健康检查] http://localhost:8080/
echo [回调地址] http://localhost:8080/dingtalk/callback
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python bot.py
pause
