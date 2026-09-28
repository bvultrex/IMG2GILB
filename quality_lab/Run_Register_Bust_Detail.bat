@echo off
setlocal
title IMG2GILB - Bust Detail Registration Gate

set "ROOT=%~dp0.."
set "PY=D:\SF3D_QualityLab\venv\Scripts\python.exe"
set "REPORT=D:\SF3D_QualityLab\bust_validation\shape_ablation\detail_registration.json"

echo.
echo ============================================================
echo   IMG2GILB - Local Bust Detail Registration
echo ============================================================
echo.

if not exist "%PY%" (
  echo [ERROR] Lab Python not found:
  echo %PY%
  goto :FAIL
)

pushd "%ROOT%"
"%PY%" quality_lab\register_bust_detail.py
set "ERR=%ERRORLEVEL%"
popd

if not "%ERR%"=="0" (
  echo.
  echo [ERROR] Registration runner failed with exit code %ERR%.
  goto :FAIL
)

echo.
echo ============================================================
echo   Registration report
echo ============================================================
if exist "%REPORT%" (
  type "%REPORT%"
) else (
  echo [ERROR] Expected report was not created:
  echo %REPORT%
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
