@echo off
chcp 65001 > nul
echo ============================================================
echo   Assistente Bíblico - Atualização do Executável (Etapa 7)
echo ============================================================
echo.

echo [1/3] Fechando instâncias antigas do AssistenteBiblico se estiverem abertas...
taskkill /F /IM AssistenteBiblico.exe 2>nul

echo.
echo [2/3] Compilando novo executável com PyInstaller...
python -m PyInstaller --noconfirm assistente_biblico.spec
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao compilar com o PyInstaller.
    exit /b 1
)

echo.
echo [3/3] Sincronizando arquivos de configuração e modelos na pasta dist...

REM Preserva o config.json se já existir na pasta dist, caso contrário copia da raiz
if not exist "dist\AssistenteBiblico\config.json" (
    if exist "config.json" (
        echo Copiando config.json para dist\AssistenteBiblico...
        copy /Y "config.json" "dist\AssistenteBiblico\config.json" > nul
    )
)

REM Sincroniza a pasta de modelos offline
if not exist "dist\AssistenteBiblico\models" (
    mkdir "dist\AssistenteBiblico\models"
)
if exist "models" (
    echo Sincronizando pasta de modelos offline para dist\AssistenteBiblico\models...
    xcopy /E /I /Y "models" "dist\AssistenteBiblico\models" > nul
)

echo.
echo ============================================================
echo   EXECUTÁVEL ATUALIZADO COM SUCESSO!
echo   Caminho: dist\AssistenteBiblico\AssistenteBiblico.exe
echo ============================================================
