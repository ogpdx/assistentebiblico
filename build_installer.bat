@echo off
chcp 65001 > nul
echo ============================================================
echo   Assistente Bíblico - Compilação do Instalador Inno Setup
echo ============================================================
echo.

set ISCC_PATH=""

REM Procura ISCC.exe nos locais padrão
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if %ISCC_PATH%=="" (
    echo [ERRO] O compilador do Inno Setup 6 (ISCC.exe) não foi encontrado nos caminhos padrão.
    echo Baixe e instale o Inno Setup 6 em: https://jrsoftware.org/isdl.php
    exit /b 1
)

echo [1/2] Compilador Inno Setup encontrado em: %ISCC_PATH%
echo [2/2] Compilando scripts\installer\AssistenteBiblico.iss...

if not exist "dist\installer" (
    mkdir "dist\installer"
)

%ISCC_PATH% "scripts\installer\AssistenteBiblico.iss"
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao compilar o instalador.
    exit /b 1
)

echo.
echo ============================================================
echo   INSTALADOR GERADO COM SUCESSO!
echo   Arquivo gerado na pasta: dist\installer\
echo ============================================================
dir "dist\installer"
