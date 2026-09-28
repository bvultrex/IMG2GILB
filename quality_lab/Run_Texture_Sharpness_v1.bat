@echo off
setlocal
title IMG2GILB - Texture Sharpness V1

set "ROOT=%~dp0.."
set "PY=D:\SF3D_QualityLab\venv\Scripts\python.exe"
set "JOB=D:\SF3D_QualityLab\app_jobs\b66c77f5fb844cefae8ec485d8bab8af"
set "REPORT=D:\SF3D_QualityLab\texture_validation\texture_v1\texture_sharpness_v1.json"

echo.
echo ============================================================
echo   IMG2GILB - Texture Sharpness V1
echo   CPU-only / existing painted GLB / no shape or Paint rerun
echo ============================================================
echo.

pushd "%ROOT%"
if exist "%JOB%\output.glb" (
  "%PY%" quality_lab\texture_sharpness_v1.py --job "%JOB%"
) else (
  echo Preferred job not found; using newest complete app_job fallback.
  "%PY%" quality_lab\texture_sharpness_v1.py
)
set "ERR=%ERRORLEVEL%"
popd

if not "%ERR%"=="0" goto :FAIL

echo.
echo ============================================================
echo   Texture sharpness report
echo ============================================================
type "%REPORT%"

echo.
echo Preview folder:
echo C:\Users\Shadow\Documents\ComfyUI\_vis_export\texture_v1
echo.
echo Refined experimental GLB:
echo D:\SF3D_QualityLab\texture_validation\texture_v1\output_texture_refine_v1.glb
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
