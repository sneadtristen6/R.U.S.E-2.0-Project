; The installer for either app (Inno Setup 6). installers/build_app.py passes the app's details:
; AppName, AppId, AppVersion, ExeName, AppDescription, SourceDir (the built program folder), IconFile, OutputDir,
; OutputName. It installs for the current Windows user only, so it never asks for admin rights, and it never touches
; the game. Uninstalling keeps the platform folder (mods, settings, the game index) in %LOCALAPPDATA%.

#ifndef AppName
  #error Build this through installers/build_app.py, which passes the app's details.
#endif

[Setup]
AppId={{{#AppId}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=RUSE Mod Platform
AppPublisherURL=https://github.com/sneadtristen6/Ruse-Mod-Platform
AppSupportURL=https://github.com/sneadtristen6/Ruse-Mod-Platform/issues
AppComments={#AppDescription}
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} Setup
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
OutputDir={#OutputDir}
OutputBaseFilename={#OutputName}
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\{#ExeName}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=auto
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
; The game's languages that Inno Setup ships a translation for (Chinese isn't one of them: English then).
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#ExeName}"; Comment: "{#AppDescription}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; Comment: "{#AppDescription}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; An update from the app itself (rusemod/update.py runs this installer with /SILENT /relaunch=1): start it again.
Filename: "{app}\{#ExeName}"; Flags: nowait skipifnotsilent; Check: Relaunch

[Code]
// The apps' screens need Microsoft's WebView2 Runtime (built into Windows 11, on most Windows 10 PCs). The apps check
// too, but saying it here saves a confusing first start.
function WebView2At(Root: Integer; Key: String): Boolean;
var
  Version: String;
begin
  Result := RegQueryStringValue(Root, Key, 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0');
end;

function Relaunch: Boolean;
begin
  Result := ExpandConstant('{param:relaunch|0}') = '1';
end;

function HasWebView2: Boolean;
var
  Client: String;
begin
  Client := '\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';
  Result := WebView2At(HKLM, 'SOFTWARE\WOW6432Node' + Client) or WebView2At(HKLM, 'SOFTWARE' + Client)
    or WebView2At(HKCU, 'Software' + Client);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ErrorCode: Integer;
begin
  if (CurStep = ssPostInstall) and (not WizardSilent) and (not HasWebView2) then
    if MsgBox('{#AppName} needs Microsoft Edge WebView2 Runtime, which this PC doesn''t have yet. It''s free and '
      + 'small, from Microsoft.' + #13#10#13#10 + 'Open the download now?', mbConfirmation, MB_YESNO) = IDYES then
      ShellExec('open', 'https://go.microsoft.com/fwlink/p/?LinkId=2124703', '', '', SW_SHOWNORMAL, ewNoWait,
        ErrorCode);
end;
