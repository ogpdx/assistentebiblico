; Script do Inno Setup para o Assistente Bíblico
; Versão: 0.1.0
; Plataforma: Windows 10 e Windows 11 (64-bit)

#define MyAppName "Assistente Bíblico"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Assistente Bíblico"
#define MyAppExeName "AssistenteBiblico.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".myp"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt
#define MyDistDir "..\..\dist\AssistenteBiblico"

[Setup]
; Identificador de aplicação único para atualizações e desinstalação segura
AppId={{9F4C547F-7885-4731-806E-C072E683982D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Requisito: Windows 64-bit (x64)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\installer
OutputBaseFilename=Instalador_AssistenteBiblico_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
; Informações do produto exibidas no assistente
AppCopyright=© 2026 Assistente Bíblico
VersionInfoVersion=0.1.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} - Controle por Voz para Holyrics
VersionInfoProductVersion=0.1.0.0

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Executável principal
Source: "{#MyDistDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Modelo Whisper SMALL e dados offline (obrigatório para funcionamento 100% offline)
Source: "{#MyDistDir}\models\*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs

; Exemplo de configuração limpa
Source: "{#MyDistDir}\config.example.json"; DestDir: "{app}"; Flags: ignoreversion

; Dependências nativas, PySide6, CTranslate2, Python runtime (_internal)
Source: "{#MyDistDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; NOTA CRÍTICA DE PRESERVAÇÃO:
; config.json e logs/ NÃO são instalados em {app} para nunca serem sobrescritos nem deletados.
; O aplicativo cria e lê as configurações do usuário em %APPDATA%\AssistenteBiblico\
; e os logs em %LOCALAPPDATA%\AssistenteBiblico\logs\.

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; REGRA DE SEGURANÇA:
; O desinstalador remove apenas arquivos temporários criados dentro da pasta {app}.
; NUNCA apaga %APPDATA%\AssistenteBiblico\ (config.json)
; NUNCA apaga %LOCALAPPDATA%\AssistenteBiblico\logs\
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\models"

[Code]
// Garante mensagens claras e preservação total de configurações
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // As configurações do usuário em %APPDATA% e logs em %LOCALAPPDATA%
    // são estritamente preservadas para uso futuro ou reinstalações.
  end;
end;
