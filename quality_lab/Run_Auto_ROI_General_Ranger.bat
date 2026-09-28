@echo off
setlocal
title IMG2GILB - General Auto ROI Second Fixture

set "ROOT=%~dp0.."
set "PY=D:\SF3D_QualityLab\venv\Scripts\python.exe"
set "RANGER_REPORT=D:\SF3D_QualityLab\ranger_validation\ortho_v1\auto_roi_general_v1_fullbody.json"
set "BUST_ROI=D:\SF3D_QualityLab\bust_validation\shape_ablation\auto_roi_bust_v3.json"
set "BUST_REG=D:\SF3D_QualityLab\bust_validation\shape_ablation\auto_roi_registration_v1.json"

echo.
echo ============================================================
echo   IMG2GILB - General Auto ROI / Ranger + Bust Regression
echo ============================================================
echo.

pushd "%ROOT%"

"%PY%" quality_lab\auto_roi_general_v1.py --mode fullbody --image fixtures\ranger_ortho_v1\front.png
if errorlevel 1 (
  popd
  goto :FAIL
)

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
echo   Ranger general ROI report
echo ============================================================
type "%RANGER_REPORT%"

echo.
echo ============================================================
echo   Bust ROI regression report
echo ============================================================
type "%BUST_ROI%"

echo.
echo ============================================================
echo   Bust registration regression report
echo ============================================================
type "%BUST_REG%"

echo.
echo Ranger overlay:
echo D:\SF3D_QualityLab\ranger_validation\ortho_v1\auto_roi_general_v1_fullbody_overlay.png
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
