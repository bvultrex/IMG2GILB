@echo off
setlocal
title IMG2GILB - Automatic Bust ROI Diagnostic

set "ROOT=%~dp0.."
set "PY=D:\SF3D_QualityLab\venv\Scripts\python.exe"
set "REPORT=D:\SF3D_QualityLab\bust_validation\shape_ablation\auto_roi_bust_v1.json"

echo.
echo ============================================================
echo   IMG2GILB - Automatic Bust ROI Diagnostic
echo ============================================================
echo.

pushd "%ROOT%"
"%PY%" quality_lab\auto_roi_bust_v1.py
set "ERR=%ERRORLEVEL%"
popd

if not "%ERR%"=="0" goto :FAIL

echo.
echo ============================================================
echo   Auto ROI report
echo ============================================================
type "%REPORT%"

echo.
echo Overlay:
echo D:\SF3D_QualityLab\bust_validation\shape_ablation\auto_roi_bust_v1_overlay.png
echo.
echo ============================================================
echo   DONE
echo ============================================================
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
