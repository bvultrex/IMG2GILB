@echo off
setlocal EnableExtensions EnableDelayedExpansion
title IMG2GILB - Codex Emergency Recovery

cd /d "%~dp0"

echo.
echo ============================================================
echo   IMG2GILB - CODEX EMERGENCY RECOVERY
echo ============================================================
echo Repo: %CD%
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git was not found in PATH.
    goto :FAIL
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This BAT is not inside a Git repository.
    echo Place it in the IMG2GILB repo root and run it again.
    goto :FAIL
)

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%I"
for /f %%I in ('git branch --show-current') do set "BRANCH=%%I"

if not defined BRANCH (
    echo [ERROR] Detached HEAD detected. Nothing will be pushed automatically.
    goto :FAIL
)

set "RECOVERY_BRANCH=codex-recovery-%TS%"
set "BACKUP=%USERPROFILE%\Desktop\IMG2GILB_CODEX_RECOVERY_%TS%"
mkdir "%BACKUP%" >nul 2>&1

echo [1/8] Recording local state...
git status > "%BACKUP%\STATUS.txt"
git rev-parse HEAD > "%BACKUP%\HEAD_BEFORE.txt"
git log -100 --date=iso-local --pretty=format:"%%H %%ad %%s" > "%BACKUP%\HISTORY.txt"
git diff --binary > "%BACKUP%\WORKTREE.patch"
git diff --cached --binary > "%BACKUP%\STAGED_BEFORE.patch"
git ls-files --others --exclude-standard > "%BACKUP%\UNTRACKED_ALL.txt"

echo [2/8] Creating Git bundle of committed history...
git bundle create "%BACKUP%\IMG2GILB_ALL_COMMITS.bundle" --all
if errorlevel 1 (
    echo [WARN] Git bundle creation failed. Continuing because the working tree is untouched.
)

echo [3/8] Copying important untracked source/docs to Desktop snapshot...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$repo=(Get-Location).Path; $dest='%BACKUP%\UNTRACKED_SOURCE';" ^
  "$exclude='^(?:_vis_export|desktop[\\/]+dist|fixtures|models|hf|app_jobs|quality_runs|\.venv|venv|node_modules|__pycache__|\.cache)(?:[\\/]|$)';" ^
  "$ext='\.(?:py|md|json|bat|cmd|ps1|js|html|css|toml|ya?ml|ini|cfg|txt)$';" ^
  "git ls-files --others --exclude-standard | ForEach-Object { if($_ -match $ext -and $_ -notmatch $exclude -and $_ -notmatch '\.bak' -and $_ -notmatch '\.localhold$' -and $_ -notmatch '(^|[\\/])_tmp_') { $src=Join-Path $repo $_; $dst=Join-Path $dest $_; New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null; Copy-Item -LiteralPath $src -Destination $dst -Force } }"
if errorlevel 1 (
    echo [WARN] Could not copy some untracked source files. The Git staging step still follows.
)

echo [4/8] Fetching remote refs only - NO pull, NO reset...
git fetch origin
if errorlevel 1 (
    echo [WARN] Fetch failed. We can still create a local recovery commit.
)

echo [5/8] Staging recoverable project state...
git add -A -- . ^
  ":(exclude,glob)_vis_export/**" ^
  ":(exclude,glob)desktop/dist/**" ^
  ":(exclude,glob)fixtures/**" ^
  ":(exclude,glob)models/**" ^
  ":(exclude,glob)hf/**" ^
  ":(exclude,glob)app_jobs/**" ^
  ":(exclude,glob)quality_runs/**" ^
  ":(exclude,glob).venv/**" ^
  ":(exclude,glob)venv/**" ^
  ":(exclude,glob)node_modules/**" ^
  ":(exclude,glob)**/__pycache__/**" ^
  ":(exclude,glob)**/.cache/**" ^
  ":(exclude,glob)**/*.bak*" ^
  ":(exclude,glob)**/*.localhold" ^
  ":(exclude,glob)**/_tmp_*" ^
  ":(exclude,glob)**/*.glb" ^
  ":(exclude,glob)**/*.gltf" ^
  ":(exclude,glob)**/*.bin" ^
  ":(exclude,glob)**/*.pt" ^
  ":(exclude,glob)**/*.pth" ^
  ":(exclude,glob)**/*.ckpt" ^
  ":(exclude,glob)**/*.safetensors" ^
  ":(exclude,glob)**/*.onnx" ^
  ":(exclude,glob)**/*.npz" ^
  ":(exclude,glob)**/*.npy" ^
  ":(exclude,glob)**/*.png" ^
  ":(exclude,glob)**/*.jpg" ^
  ":(exclude,glob)**/*.jpeg" ^
  ":(exclude,glob)**/*.webp" ^
  ":(exclude,glob)**/*.gif" ^
  ":(exclude,glob)**/*.mp4" ^
  ":(exclude,glob)**/*.mov" ^
  ":(exclude,glob)**/*.zip" ^
  ":(exclude,glob)**/*.7z" ^
  ":(exclude,glob)**/*.rar" ^
  ":(exclude,glob)**/*.exe" ^
  ":(exclude,glob)**/*.dll" ^
  ":(exclude,glob)**/*.log"

git diff --cached --name-status > "%BACKUP%\STAGED_FILES.txt"
git diff --cached --binary > "%BACKUP%\STAGED_FINAL.patch"

echo.
echo Files selected for recovery commit:
git diff --cached --name-status
echo.

git diff --cached --quiet
if errorlevel 1 (
    echo [6/8] Creating WIP recovery commit...
    git commit -m "wip: automatic Codex recovery %TS%"
    if errorlevel 1 (
        echo [ERROR] Commit failed. Nothing will be pushed.
        goto :FAIL
    )
) else (
    echo [6/8] No uncommitted recoverable files. Existing commits will be pushed.
)

for /f %%I in ('git rev-parse HEAD') do set "RECOVERED_HEAD=%%I"
echo %RECOVERED_HEAD% > "%BACKUP%\HEAD_AFTER.txt"

echo [7/8] Creating and pushing safety branch: %RECOVERY_BRANCH%
git branch "%RECOVERY_BRANCH%" "%RECOVERED_HEAD%"
if errorlevel 1 (
    echo [ERROR] Could not create local recovery branch.
    goto :FAIL
)

git push -u origin "%RECOVERY_BRANCH%"
if errorlevel 1 (
    echo [ERROR] Recovery branch could not be pushed.
    echo Local commit and Desktop snapshot are still safe.
    goto :FAIL
)

echo [8/8] Pushing current branch "%BRANCH%" without force...
git push origin "%BRANCH%"
if errorlevel 1 (
    echo.
    echo [WARN] Current branch push was rejected or failed.
    echo This is SAFE: %RECOVERY_BRANCH% is already on GitHub.
    echo Main may have advanced remotely. Resolve normally later.
) else (
    echo.
    echo [OK] Current branch was updated on GitHub.
)

git status > "%BACKUP%\STATUS_AFTER.txt"

echo.
echo ============================================================
echo   RECOVERY COMPLETE
echo ============================================================
echo Local branch  : %BRANCH%
echo Recovery ref  : %RECOVERY_BRANCH%
echo Recovered HEAD: %RECOVERED_HEAD%
echo Snapshot      : %BACKUP%
echo.
echo Heavy/private/generated files were intentionally excluded.
echo NO force-push, reset, restore, clean, or deletion was used.
echo ============================================================
echo.
pause
exit /b 0

:FAIL
echo.
echo ============================================================
echo   RECOVERY STOPPED SAFELY
echo ============================================================
echo Nothing destructive was executed.
echo Check the messages above and the Desktop snapshot if created.
echo ============================================================
echo.
pause
exit /b 1
