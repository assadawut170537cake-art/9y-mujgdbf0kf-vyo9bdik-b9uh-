; Inno Setup Script for J.A.R.V.I.S. Desktop OS & Mark-LV Ecosystem
; Version: 4.0.23
; Lead Architect: Khun Assadawut

#define MyAppName "J.A.R.V.I.S. Desktop OS"
#define MyAppVersion "4.0.23"
#define MyAppPublisher "Assadawut (Supreme Commander)"
#define MyAppURL "https://github.com/assadawut/JARVIS"
#define MyAppExeName "JARVIS_Desktop_v1.4.0.exe"

[Setup]
; Basic Application Info
AppId={{9F57A18C-4D2A-4B69-A8F5-8C7E1D83569B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\JARVIS_OS
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=J:\Mark-LV\LICENSE
OutputDir=J:\Mark-LV\dist_installer
OutputBaseFilename=JARVIS_v4.0.23_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startwithwindows"; Description: "Start J.A.R.V.I.S. on Windows Startup"; GroupDescription: "Startup Options:"; Flags: unchecked

[Files]
; Main Executable from Desktop/FlashDrive package
Source: "J:\Mark-LV\JARVIS_FOR_NOTEBOOK\JARVIS_Desktop_v1.4.0.exe"; DestDir: "{app}"; Flags: ignoreversion
; Unified Launcher
Source: "J:\Mark-LV\start_jarvis_unified.bat"; DestDir: "{app}"; Flags: ignoreversion
; Core Python Engine files
Source: "J:\Mark-LV\main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "J:\Mark-LV\ui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "J:\Mark-LV\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "J:\Mark-LV\core\*"; DestDir: "{app}\core"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "J:\Mark-LV\actions\*"; DestDir: "{app}\actions"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "J:\Mark-LV\plugins\*"; DestDir: "{app}\plugins"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "J:\Mark-LV\memory\*"; DestDir: "{app}\memory"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "J:\Mark-LV\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "J:\Mark-LV\JARVIS_FOR_NOTEBOOK\*"; DestDir: "{app}\JARVIS_FOR_NOTEBOOK"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\J.A.R.V.I.S. Python Core HUD"; Filename: "{app}\start_jarvis_unified.bat"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autodesktop}\J.A.R.V.I.S. Core HUD"; Filename: "{app}\start_jarvis_unified.bat"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
