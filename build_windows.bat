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
rem Required native kernels: Rust MSVC toolchain and C++ Build Tools.
where cargo >nul 2>nul
if errorlevel 1 (
  echo ERROR: Rust is required. Install Rust stable x64 MSVC from https://rustup.rs/
  echo Also install Visual Studio Build Tools: Desktop development with C++ and Windows SDK.
  echo Then reopen the terminal and run this script again.
  exit /b 1
)
"%PY%" tools\build_native.py
if errorlevel 1 exit /b 1
"%PY%" -c "import sys; sys.path.insert(0, 'server'); import fast; fast.require(fast.MIN_VERSION, 'Windows build')"
if errorlevel 1 exit /b 1
"%PY%" tools\build_app.py --stock-bootloader
if errorlevel 1 exit /b 1
for %%F in (dist\BeamNG.Earth-*.exe) do (
  "%%F" --server --help >nul
  if errorlevel 1 exit /b 1
)
echo Build complete. See dist\BeamNG.Earth-*.exe
endlocal
