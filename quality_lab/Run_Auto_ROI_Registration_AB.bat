@echo off
setlocal
title IMG2GILB - Auto ROI V3 Registration A-B

set "ROOT=%~dp0.."
set "PY=D:\SF3D_QualityLab\venv\Scripts\python.exe"
set "ROI_REPORT=D:\SF3D_QualityLab\bust_validation\shape_ablation\auto_roi_bust_v3.json"
set "REG_REPORT=D:\SF3D_QualityLab\bust_validation\shape_ablation\auto_roi_registration_v1.json"

echo.
echo ============================================================
echo   IMG2GILB - Auto ROI V3 + Densified Registration A/B
echo ============================================================
echo.

pushd "%ROOT%"
"%PY%" quality_lab\auto_roi_bust_v3.py
if errorlevel 1 (
  popd
  goto :FAIL
)
"%PY%" quality_lab\auto_roi_registration_v1.py
set "ERR=%ERRORLEVEL%"
popd

if not "%ERR%"=="0" goto :FAIL

echo.
echo ============================================================
echo   Auto ROI V3 report
echo ============================================================
type "%ROI_REPORT%"

echo.
echo ============================================================
echo   Registration A/B report
echo ============================================================
type "%REG_REPORT%"

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
