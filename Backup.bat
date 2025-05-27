@echo off
setlocal

REM ===== Set up timestamp =====
set TIMESTAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM ===== Define paths and credentials =====
set BACKUP_DIR=C:\School_Backup\bin
set MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin
set DB_NAME=School
set DB_USER=admin_user
set DB_PASS=admin_pass

REM ===== Create backup directory if it doesn't exist =====
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
)

REM ===== Check if mysqldump exists =====
if not exist "%MYSQL_BIN%\mysqldump.exe" (
    echo [%DATE% %TIME%] ERROR: mysqldump.exe not found at "%MYSQL_BIN%" >> "%BACKUP_DIR%\mysql_backup_log.txt"
    echo mysqldump.exe not found. Exiting...
    exit /b 1
)

REM ===== Run the backup =====
set BACKUP_FILE=%BACKUP_DIR%\%DB_NAME%_backup_%TIMESTAMP%.sql
"%MYSQL_BIN%\mysqldump.exe" -u %DB_USER% -p%DB_PASS% --databases %DB_NAME% > "%BACKUP_FILE%"

set ERRORLEVEL_SAVE=%ERRORLEVEL%

REM ===== Log the result =====
if %ERRORLEVEL_SAVE% neq 0 (
    echo [%DATE% %TIME%] Backup FAILED for database "%DB_NAME%" >> "%BACKUP_DIR%\mysql_backup_log.txt"
    echo [%DATE% %TIME%] Error code: %ERRORLEVEL_SAVE% >> "%BACKUP_DIR%\mysql_backup_log.txt"
    echo Backup failed. See log for details.
) else (
    echo [%DATE% %TIME%] Backup SUCCESSFUL: %BACKUP_FILE% >> "%BACKUP_DIR%\mysql_backup_log.txt"
    echo Backup completed successfully.

    REM Delete old backups older than 7 days
    forfiles /p "%BACKUP_DIR%" /s /m *.sql /d -90 /c "cmd /c del @path"
)


endlocal
pause
