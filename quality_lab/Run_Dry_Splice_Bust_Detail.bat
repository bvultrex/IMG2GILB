@echo off
setlocal
title IMG2GILB - Bust Dry Splice Diagnostic

set "ROOT=%~dp0.."
set "PY=D:\SF3D_QualityLab\venv\Scripts\python.exe"
set "BLENDER=C:\Users\Shadow\Downloads\SF3D_Tools\Blender_5.2\Blender Foundation\Blender 5.2\blender.exe"
set "REPORT=D:\SF3D_QualityLab\bust_validation\shape_ablation\detail_dry_splice.json"
set "RENDER_REPORT=D:\SF3D_QualityLab\bust_validation\shape_ablation\detail_dry_splice_render.json"

echo.
echo ============================================================
echo   IMG2GILB - Bust Dry Splice Diagnostic
echo ============================================================
echo.

pushd "%ROOT%"
"%PY%" quality_lab\dry_splice_bust_detail.py
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
  popd
  goto :FAIL
)

if exist "%BLENDER%" (
  "%BLENDER%" --background --python quality_lab\render_dry_splice.py --python-exit-code 1
  set "ERR=%ERRORLEVEL%"
  if not "%ERR%"=="0" (
    popd
    goto :FAIL
  )
) else (
  echo [WARN] Blender not found; geometry report still available.
)
popd

echo.
echo ============================================================
echo   Dry splice report
echo ============================================================
type "%REPORT%"

if exist "%RENDER_REPORT%" (
  echo.
  echo ============================================================
  echo   Render report
  echo ============================================================
  type "%RENDER_REPORT%"
)

echo.
echo Renders are under:
echo D:\SF3D_QualityLab\bust_validation\shape_ablation\dry_splice_*.png
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
