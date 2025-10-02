@echo off
REM ========================================
REM Windows 工作排程器設定腳本
REM 用途：設定每日自動爬取新聞
REM ========================================

echo ========================================
echo 鉅亨網新聞自動爬取 - Windows 排程設定
echo ========================================
echo.

REM 設定變數
set TASK_NAME=CnyesNewsScraper
set SCRIPT_PATH=%~dp0run_daily_scrape.bat
set PYTHON_ENV=%~dp0finance_agents_env\Scripts\python.exe
set LOG_PATH=%~dp0logs\scheduler.log

echo 準備創建 Windows 工作排程...
echo.
echo 排程名稱: %TASK_NAME%
echo 執行腳本: %SCRIPT_PATH%
echo Python 環境: %PYTHON_ENV%
echo 日誌路徑: %LOG_PATH%
echo.

REM 檢查是否有管理員權限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 需要管理員權限執行此腳本
    echo 請右鍵點擊此檔案，選擇「以系統管理員身分執行」
    pause
    exit /b 1
)

echo [步驟 1/3] 刪除舊的排程（如果存在）...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

echo [步驟 2/3] 創建新的排程任務...
echo.
echo 請輸入排程時間（24小時制）：
set /p SCHEDULE_HOUR="執行小時 (0-23, 預設 9): "
set /p SCHEDULE_MINUTE="執行分鐘 (0-59, 預設 0): "

REM 設定預設值
if "%SCHEDULE_HOUR%"=="" set SCHEDULE_HOUR=09
if "%SCHEDULE_MINUTE%"=="" set SCHEDULE_MINUTE=00

REM 格式化時間（補0）
if %SCHEDULE_HOUR% lss 10 set SCHEDULE_HOUR=0%SCHEDULE_HOUR%
if %SCHEDULE_MINUTE% lss 10 set SCHEDULE_MINUTE=0%SCHEDULE_MINUTE%

set SCHEDULE_TIME=%SCHEDULE_HOUR%:%SCHEDULE_MINUTE%

echo.
echo 將設定為每日 %SCHEDULE_TIME% 執行
echo.

REM 創建 Windows 工作排程
schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\"" /sc daily /st %SCHEDULE_TIME% /f

if %errorlevel% equ 0 (
    echo [成功] 工作排程創建成功！
    echo.
    echo [步驟 3/3] 驗證排程...
    schtasks /query /tn "%TASK_NAME%" /v /fo list
    echo.
    echo ========================================
    echo 設定完成！
    echo ========================================
    echo.
    echo 排程將於每日 %SCHEDULE_TIME% 自動執行
    echo.
    echo 管理指令：
    echo - 查看排程: schtasks /query /tn "%TASK_NAME%"
    echo - 執行一次: schtasks /run /tn "%TASK_NAME%"
    echo - 停用排程: schtasks /change /tn "%TASK_NAME%" /disable
    echo - 啟用排程: schtasks /change /tn "%TASK_NAME%" /enable
    echo - 刪除排程: schtasks /delete /tn "%TASK_NAME%" /f
    echo.
    echo 日誌位置: %LOG_PATH%
    echo.
) else (
    echo [錯誤] 創建工作排程失敗
    echo 錯誤代碼: %errorlevel%
)

pause
