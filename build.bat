@echo off
chcp 65001 > nul
echo ============================================================
echo   Assistente Bíblico - Script de Build Windows (PyInstaller)
echo ============================================================
echo.

echo [1/3] Verificando dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias do requirements.txt.
    exit /b 1
)

echo.
echo [2/3] Gerando o executavel com PyInstaller (onedir)...
python -m PyInstaller --clean --noconfirm assistente_biblico.spec
if errorlevel 1 (
    echo [ERRO] Falha durante o build com PyInstaller.
    exit /b 1
)

echo.
echo [3/3] Copiando arquivos auxiliares para dist/AssistenteBiblico...
if not exist "dist\AssistenteBiblico\models" (
    mkdir "dist\AssistenteBiblico\models"
)

REM Se houver pasta models local no projeto, copia os modelos baixados
if exist "models" (
    echo Copiando modelos locais para dist\AssistenteBiblico\models...
    xcopy /E /I /Y "models" "dist\AssistenteBiblico\models" > nul
)

REM Copia config.example.json
copy /Y "config.example.json" "dist\AssistenteBiblico\config.example.json" > nul

echo.
echo ============================================================
echo   BUILD CONCLUIDO COM SUCESSO!
echo   Pasta de saida: dist\AssistenteBiblico
echo   Executavel: dist\AssistenteBiblico\AssistenteBiblico.exe
echo ============================================================
