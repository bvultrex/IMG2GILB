@echo off
setlocal
title IMG2GILB - Bust Detail Local Warp

set "ROOT=%~dp0.."
set "PY=D:\SF3D_QualityLab\venv\Scripts\python.exe"
set "REPORT=D:\SF3D_QualityLab\bust_validation\shape_ablation\detail_localwarp.json"

echo.
echo ============================================================
echo   IMG2GILB - Bust Detail Local Warp Diagnostic
echo ============================================================
echo.

pushd "%ROOT%"
"%PY%" quality_lab\deform_bust_detail.py
set "ERR=%ERRORLEVEL%"
popd

if not "%ERR%"=="0" goto :FAIL

echo.
echo ============================================================
echo   Local warp report
echo ============================================================
if exist "%REPORT%" (
  type "%REPORT%"
) else (
  echo [ERROR] Missing report: %REPORT%
  goto :FAIL
)

echo.
echo ============================================================
echo   DONE
echo ============================================================
echo.
echo Send the report block above back to ChatGPT.
echo.
pause
exit /b 0

:FAIL
echo.
echo ============================================================
echo   STOPPED
echo ============================================================
echo.
pause
exit /b 1
