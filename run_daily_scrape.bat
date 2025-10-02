@echo off
REM ========================================
REM 每日新聞爬取執行腳本
REM 由 Windows 工作排程器調用
REM ========================================

REM 設定環境
set PROJECT_DIR=%~dp0
set PYTHON_ENV=%PROJECT_DIR%finance_agents_env\Scripts\python.exe
set LOG_DIR=%PROJECT_DIR%logs
set LOG_FILE=%LOG_DIR%\scraper_%date:~0,4%%date:~5,2%%date:~8,2%.log

REM 創建日誌目錄（如果不存在）
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM 記錄開始時間
echo ======================================== >> "%LOG_FILE%"
echo 開始執行 - %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

REM 切換到專案目錄
cd /d "%PROJECT_DIR%"

REM 激活虛擬環境並執行爬蟲
echo 執行路徑: %CD% >> "%LOG_FILE%"
echo Python: %PYTHON_ENV% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM 執行爬蟲（手動模式，爬取 20 篇/分類）
"%PYTHON_ENV%" src\main\python\etl\news_scheduler.py --mode once --articles 20 >> "%LOG_FILE%" 2>&1

REM 記錄結束時間和狀態
if %errorlevel% equ 0 (
    echo. >> "%LOG_FILE%"
    echo [成功] 爬取完成 - %date% %time% >> "%LOG_FILE%"
    echo ======================================== >> "%LOG_FILE%"
    echo. >> "%LOG_FILE%"
) else (
    echo. >> "%LOG_FILE%"
    echo [錯誤] 爬取失敗，錯誤代碼: %errorlevel% >> "%LOG_FILE%"
    echo 時間: %date% %time% >> "%LOG_FILE%"
    echo ======================================== >> "%LOG_FILE%"
    echo. >> "%LOG_FILE%"
)

exit /b %errorlevel%
