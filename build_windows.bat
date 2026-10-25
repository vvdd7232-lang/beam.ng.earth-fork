@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Install Python 3.12 x64 from python.org with the Python launcher.
  exit /b 1
)
py -3.12 -m venv .venv-build
if errorlevel 1 exit /b 1
set "PY=%CD%\.venv-build\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%PY%" -m pip install pyinstaller -r server\requirements.txt
if errorlevel 1 exit /b 1
rem Optional performance kernels: requires Rust and MSVC Build Tools.
if /i "%~1"=="--native" (
  "%PY%" tools\build_native.py
  if errorlevel 1 exit /b 1
)
"%PY%" tools\build_app.py --stock-bootloader
if errorlevel 1 exit /b 1
for %%F in (dist\BeamNG.Earth-*.exe) do (
  "%%F" --server --help >nul
  if errorlevel 1 exit /b 1
)
echo Build complete. See dist\BeamNG.Earth-*.exe
endlocal
