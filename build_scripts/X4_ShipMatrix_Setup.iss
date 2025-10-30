; X4 ShipMatrix Installer Script
; Created with Inno Setup 6
; https://jrsoftware.org/isinfo.php

#define MyAppName "X4 ShipMatrix"
#define MyAppVersion "0.1.3"
#define MyAppPublisher "jongreg288"
#define MyAppURL "https://github.com/jongreg288/X4_Ship_Parse"
#define MyAppExeName "X4 ShipMatrix.exe"
#define MyAppUpdaterExeName "X4_Updater.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{X4ShipMatrix-8F9E2D3C-4A5B-6C7D-8E9F-0A1B2C3D4E5F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\releases\latest
OutputBaseFilename=X4_ShipMatrix_v{#MyAppVersion}_Setup
SetupIconFile=dist\X4 ShipMatrix.exe,0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executables
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#MyAppUpdaterExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README_USERS.txt"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Any additional files should be placed in the dist folder before building the installer

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} Updater"; Filename: "{app}\{#MyAppUpdaterExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeWizard;
var
  InfoPage: TOutputMsgMemoWizardPage;
begin
  InfoPage := CreateOutputMsgMemoPage(wpWelcome,
    'Welcome to X4 ShipMatrix Setup',
    'Ship Analysis Tool for X4: Foundations',
    'X4 ShipMatrix is a comprehensive tool for analyzing and comparing ships in X4: Foundations.' + #13#10 + #13#10 +
    'Key Features:' + #13#10 +
    '• Multi-language support (14+ languages)' + #13#10 +
    '• Smart engine filtering by ship size' + #13#10 +
    '• Visual comparison charts' + #13#10 +
    '• Automatic game data extraction' + #13#10 +
    '• Travel speed calculations' + #13#10 + #13#10 +
    'Click Next to continue with the installation.');
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Check if .NET Framework or other prerequisites are needed
  // Currently no additional prerequisites required
end;
