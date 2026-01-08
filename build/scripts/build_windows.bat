@echo off
REM ============================================================================
REM Build Robot Runner for Windows
REM ============================================================================
REM
REM Compila Robot Runner en un ejecutable standalone para Windows.
REM
REM Requisitos:
REM   - Python 3.9+
REM   - PyInstaller instalado
REM   - Todas las dependencias instaladas
REM
REM Uso:
REM   build\scripts\build_windows.bat
REM
REM Output:
REM   dist\RobotRunner\RobotRunner.exe (executable)
REM   dist\RobotRunner-Windows.zip (distributable)
REM
REM ============================================================================

echo ======================================================================
echo   Building Robot Runner for Windows
echo ======================================================================
echo.

REM Check Python
echo [*] Checking Python version...
python --version
if errorlevel 1 (
    echo [X] Python not found!
    exit /b 1
)

REM Check PyInstaller
echo [*] Checking PyInstaller...
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [X] PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Clean previous build
echo [*] Cleaning previous build...
if exist "build\RobotRunner" rmdir /s /q "build\RobotRunner"
if exist "dist\RobotRunner" rmdir /s /q "dist\RobotRunner"
if exist "dist\RobotRunner-Windows.zip" del /q "dist\RobotRunner-Windows.zip"
echo   Cleaned

REM Build
echo [*] Building with PyInstaller...
pyinstaller app.spec
if errorlevel 1 (
    echo [X] Build failed!
    exit /b 1
)
echo [+] Build successful!

REM Check output
if exist "dist\RobotRunner\RobotRunner.exe" (
    echo [+] Executable created: dist\RobotRunner\RobotRunner.exe
) else (
    echo [X] Executable not found!
    exit /b 1
)

REM Create ZIP
echo [*] Creating distribution package...
powershell -Command "Compress-Archive -Path 'dist\RobotRunner' -DestinationPath 'dist\RobotRunner-Windows.zip' -Force"
if exist "dist\RobotRunner-Windows.zip" (
    echo [+] Distribution package: dist\RobotRunner-Windows.zip
) else (
    echo [X] Failed to create distribution package
    exit /b 1
)

REM Test executable
echo [*] Testing executable...
dist\RobotRunner\RobotRunner.exe --help >nul 2>&1
echo [+] Executable runs

echo.
echo ======================================================================
echo [+] Build completed successfully!
echo ======================================================================
echo.
echo Output files:
echo   * dist\RobotRunner\RobotRunner.exe
echo   * dist\RobotRunner-Windows.zip
echo.
echo To test:
echo   cd dist\RobotRunner
echo   RobotRunner.exe
echo.

pause
