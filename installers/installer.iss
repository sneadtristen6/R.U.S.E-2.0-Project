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
AppPublisherURL=https://github.com/sneadtristen6/R.U.S.E-2.0-Project
AppSupportURL=https://github.com/sneadtristen6/R.U.S.E-2.0-Project/issues
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

[CustomMessages]
; The clean game backup offered beside the desktop icon (the owner, 2026-10-01), with why under the list. The app
; makes it on its first start (rusemod.backup.BackupCalls.backup_requested reads the mark left at the end).
english.BackupGroup=Your game
english.BackupTask=Keep a clean copy of my game's files (recommended)
english.BackupWhy=Why: RUSE Launcher and RUSE Studio never change your game's folder, but other mod managers and hand edits can, and every modded game is built from those files. With a clean copy, the app can check your game's files and put back any that changed. It's made the first time the app starts: a few minutes, and about as much disk space as the game (in RUSE-Backup, on the game's drive).
french.BackupGroup=Votre jeu
french.BackupTask=Garder une copie propre des fichiers de mon jeu (recommandé)
french.BackupWhy=Pourquoi : RUSE Launcher et RUSE Studio ne modifient jamais le dossier de votre jeu, mais d'autres gestionnaires de mods et des modifications à la main peuvent le faire, et chaque jeu moddé est construit à partir de ces fichiers. Avec une copie propre, l'application peut vérifier les fichiers du jeu et remettre ceux qui ont changé. Elle est faite au premier lancement de l'application : quelques minutes, et à peu près autant de place que le jeu (dans RUSE-Backup, sur le disque du jeu).
german.BackupGroup=Ihr Spiel
german.BackupTask=Eine saubere Kopie der Spieldateien behalten (empfohlen)
german.BackupWhy=Warum: RUSE Launcher und RUSE Studio ändern den Ordner des Spiels nie, andere Mod-Manager und Änderungen von Hand aber schon, und jedes gemoddete Spiel wird aus diesen Dateien gebaut. Mit einer sauberen Kopie kann die App die Spieldateien prüfen und geänderte zurücksetzen. Sie wird beim ersten Start der App erstellt: ein paar Minuten und etwa so viel Platz wie das Spiel (in RUSE-Backup auf dem Laufwerk des Spiels).
italian.BackupGroup=Il tuo gioco
italian.BackupTask=Conserva una copia pulita dei file del gioco (consigliato)
italian.BackupWhy=Perché: RUSE Launcher e RUSE Studio non modificano mai la cartella del gioco, ma altri gestori di mod e le modifiche a mano sì, e ogni gioco moddato è costruito da quei file. Con una copia pulita, l'app può controllare i file del gioco e rimettere quelli cambiati. Viene fatta al primo avvio dell'app: qualche minuto, e circa lo stesso spazio del gioco (in RUSE-Backup, sull'unità del gioco).
spanish.BackupGroup=Tu juego
spanish.BackupTask=Guardar una copia limpia de los archivos del juego (recomendado)
spanish.BackupWhy=Por qué: RUSE Launcher y RUSE Studio nunca cambian la carpeta del juego, pero otros gestores de mods y los cambios a mano sí pueden, y cada juego con mods se construye a partir de esos archivos. Con una copia limpia, la aplicación puede comprobar los archivos del juego y devolver los que cambiaron. Se hace la primera vez que se abre la aplicación: unos minutos, y más o menos el mismo espacio que el juego (en RUSE-Backup, en la unidad del juego).
polish.BackupGroup=Twoja gra
polish.BackupTask=Zachowaj czystą kopię plików gry (zalecane)
polish.BackupWhy=Dlaczego: RUSE Launcher i RUSE Studio nigdy nie zmieniają folderu gry, ale inne menedżery modów i ręczne zmiany mogą to robić, a każda gra z modami jest budowana z tych plików. Dzięki czystej kopii aplikacja może sprawdzić pliki gry i przywrócić te, które się zmieniły. Kopia powstaje przy pierwszym uruchomieniu aplikacji: kilka minut i mniej więcej tyle miejsca co gra (w RUSE-Backup na dysku gry).
russian.BackupGroup=Ваша игра
russian.BackupTask=Сохранить чистую копию файлов игры (рекомендуется)
russian.BackupWhy=Зачем: RUSE Launcher и RUSE Studio никогда не меняют папку игры, а другие менеджеры модов и ручные правки могут, и каждая игра с модами собирается из этих файлов. С чистой копией приложение может проверить файлы игры и вернуть изменённые. Копия делается при первом запуске приложения: несколько минут и примерно столько же места, сколько игра (в RUSE-Backup на диске с игрой).
czech.BackupGroup=Vaše hra
czech.BackupTask=Uchovat čistou kopii souborů hry (doporučeno)
czech.BackupWhy=Proč: RUSE Launcher a RUSE Studio nikdy nemění složku hry, ale jiní správci módů a ruční úpravy ano, a každá hra s módy se sestavuje z těchto souborů. S čistou kopií může aplikace zkontrolovat soubory hry a vrátit ty, které se změnily. Kopie se vytvoří při prvním spuštění aplikace: několik minut a zhruba tolik místa jako hra (v RUSE-Backup na disku s hrou).
japanese.BackupGroup=ゲーム
japanese.BackupTask=ゲームファイルのクリーンなコピーを保存する（推奨）
japanese.BackupWhy=理由：RUSE Launcher と RUSE Studio はゲームのフォルダーを変更しませんが、他の MOD マネージャーや手作業の編集は変更することがあり、MOD を入れたゲームはそのファイルから作られます。クリーンなコピーがあれば、アプリがゲームファイルを確認し、変更されたファイルを元に戻せます。コピーはアプリの初回起動時に作成されます。数分かかり、ゲームとほぼ同じ容量を使います（ゲームのドライブの RUSE-Backup）。

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "gamebackup"; Description: "{cm:BackupTask}"; GroupDescription: "{cm:BackupGroup}"

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

// Why the clean game backup is offered, under the list of tasks: the list gives up the room it takes.
procedure InitializeWizard;
var
  Why: TNewStaticText;
begin
  Why := TNewStaticText.Create(WizardForm);
  Why.Parent := WizardForm.SelectTasksPage;
  Why.Left := WizardForm.TasksList.Left;
  Why.Width := WizardForm.TasksList.Width;
  Why.WordWrap := True;
  Why.Caption := CustomMessage('BackupWhy');
  WizardForm.TasksList.Height := WizardForm.TasksList.Height - Why.Height - ScaleY(8);
  Why.Top := WizardForm.TasksList.Top + WizardForm.TasksList.Height + ScaleY(8);
end;

// The backup asked for: a mark in the platform folder (rusemod.home), which the app finds on its next start and
// clears once the backup is made. Never on a silent install (the app's own updates): the player didn't see the
// question then.
procedure AskForBackup;
var
  Folder: String;
begin
  Folder := ExpandConstant('{localappdata}\RUSE Mod Platform');
  if ForceDirectories(Folder) then
    SaveStringToFile(Folder + '\make-backup', 'Asked for in the installer of {#AppName} {#AppVersion}.' + #13#10,
      False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ErrorCode: Integer;
begin
  if (CurStep = ssPostInstall) and (not WizardSilent) and WizardIsTaskSelected('gamebackup') then
    AskForBackup;
  if (CurStep = ssPostInstall) and (not WizardSilent) and (not HasWebView2) then
    if MsgBox('{#AppName} needs Microsoft Edge WebView2 Runtime, which this PC doesn''t have yet. It''s free and '
      + 'small, from Microsoft.' + #13#10#13#10 + 'Open the download now?', mbConfirmation, MB_YESNO) = IDYES then
      ShellExec('open', 'https://go.microsoft.com/fwlink/p/?LinkId=2124703', '', '', SW_SHOWNORMAL, ewNoWait,
        ErrorCode);
end;
