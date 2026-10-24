@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo INCORE SOCIAL COVER GENERATOR v2.0.1
where node >nul 2>nul || (echo ERROR: Node.js no esta instalado o no esta en PATH. & pause & exit /b 1)
node "%~dp0generar-social.js"
if errorlevel 1 (echo ERROR: No se completaron los archivos. & pause & exit /b 1)
echo.
echo Revisa assets\portada-social.jpg y compartir.html antes de subir a GitHub.
pause
