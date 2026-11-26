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
; The apps' eleven languages, picked by Windows' own language. Inno Setup 6.7.1 ships nine; Chinese and Persian are
; its volunteers' unofficial translations, kept here (installers/languages, from jrsoftware/issrc at is-6_7_1, a UTF-8
; byte-order mark added; the owner, 2026-10-30: "those should switch depending on what language you have").
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "chinesesimplified"; MessagesFile: "languages\ChineseSimplified.isl"
Name: "farsi"; MessagesFile: "languages\Farsi.isl"

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
chinesesimplified.BackupGroup=你的游戏
chinesesimplified.BackupTask=保留游戏文件的干净备份（推荐）
chinesesimplified.BackupWhy=原因：RUSE Launcher 和 RUSE Studio 从不修改游戏的文件夹，但其他模组管理器和手动修改可能会，而每个加载模组的游戏都是由这些文件构建的。有了干净备份，应用可以检查游戏文件，并把被修改的文件恢复原样。备份在应用第一次启动时创建：需要几分钟，占用的空间与游戏差不多（在游戏所在驱动器的 RUSE-Backup 中）。
farsi.BackupGroup=بازی شما
farsi.BackupTask=نگه داشتن یک پشتیبان تمیز از فایل‌های بازی (توصیه‌شده)
farsi.BackupWhy=چرا: RUSE Launcher و RUSE Studio هیچ‌وقت پوشهٔ بازی شما را تغییر نمی‌دهند، اما مدیرهای ماد دیگر و ویرایش‌های دستی ممکن است تغییرش دهند، و هر بازی مادشده از همین فایل‌ها ساخته می‌شود. با یک پشتیبان تمیز، برنامه می‌تواند فایل‌های بازی را بررسی کند و هر فایلی را که تغییر کرده برگرداند. پشتیبان در اولین اجرای برنامه ساخته می‌شود: چند دقیقه طول می‌کشد و تقریباً به اندازهٔ خود بازی جا می‌گیرد (در RUSE-Backup، روی درایو بازی).
; Microsoft WebView2, ticked but the player's to untick (the owner, 2026-11-24: "in all of the first time download ones,
; it'll be something where you can choose, and it'll be automatically selected. But they can unselect it"): offered
; only where it's missing, never under Wine, never on a silent install (OfferWebView2). Microsoft's installer comes
; with the app (installers/build_app.py webview2_setup); the apps offer it again on start and in Settings.
english.WebView2Group=Microsoft WebView2
english.WebView2Task=Install Microsoft WebView2: free, and needed for the app's own window (recommended)
english.WebView2Installing=Installing Microsoft WebView2...
english.WebView2Failed=Microsoft WebView2 didn't install (code %1). The app offers it again when it starts, and in its Settings.
french.WebView2Group=Microsoft WebView2
french.WebView2Task=Installer Microsoft WebView2 : gratuit, et nécessaire à la fenêtre de l'application (recommandé)
french.WebView2Installing=Installation de Microsoft WebView2...
french.WebView2Failed=Microsoft WebView2 ne s'est pas installé (code %1). L'application le proposera de nouveau à son démarrage, et dans ses Réglages.
german.WebView2Group=Microsoft WebView2
german.WebView2Task=Microsoft WebView2 installieren: kostenlos und nötig für das eigene Fenster der App (empfohlen)
german.WebView2Installing=Microsoft WebView2 wird installiert...
german.WebView2Failed=Microsoft WebView2 wurde nicht installiert (Code %1). Die App bietet es beim Start und in ihren Einstellungen erneut an.
italian.WebView2Group=Microsoft WebView2
italian.WebView2Task=Installa Microsoft WebView2: gratuito, e necessario per la finestra dell'app (consigliato)
italian.WebView2Installing=Installazione di Microsoft WebView2...
italian.WebView2Failed=Microsoft WebView2 non è stato installato (codice %1). L'app lo proporrà di nuovo all'avvio e nelle sue Impostazioni.
spanish.WebView2Group=Microsoft WebView2
spanish.WebView2Task=Instalar Microsoft WebView2: gratis y necesario para la ventana de la aplicación (recomendado)
spanish.WebView2Installing=Instalando Microsoft WebView2...
spanish.WebView2Failed=Microsoft WebView2 no se instaló (código %1). La aplicación lo ofrecerá de nuevo al abrirse y en sus Ajustes.
polish.WebView2Group=Microsoft WebView2
polish.WebView2Task=Zainstaluj Microsoft WebView2: darmowy i potrzebny do własnego okna aplikacji (zalecane)
polish.WebView2Installing=Instalowanie Microsoft WebView2...
polish.WebView2Failed=Microsoft WebView2 się nie zainstalował (kod %1). Aplikacja zaproponuje go ponownie przy uruchomieniu i w swoich Ustawieniach.
russian.WebView2Group=Microsoft WebView2
russian.WebView2Task=Установить Microsoft WebView2: бесплатно, нужен для собственного окна приложения (рекомендуется)
russian.WebView2Installing=Установка Microsoft WebView2...
russian.WebView2Failed=Microsoft WebView2 не установился (код %1). Приложение предложит его снова при запуске и в своих Настройках.
czech.WebView2Group=Microsoft WebView2
czech.WebView2Task=Nainstalovat Microsoft WebView2: zdarma a potřebný pro vlastní okno aplikace (doporučeno)
czech.WebView2Installing=Instaluje se Microsoft WebView2...
czech.WebView2Failed=Microsoft WebView2 se nenainstaloval (kód %1). Aplikace ho nabídne znovu při spuštění a ve svém Nastavení.
japanese.WebView2Group=Microsoft WebView2
japanese.WebView2Task=Microsoft WebView2 をインストールする（無料、アプリのウィンドウに必要、推奨）
japanese.WebView2Installing=Microsoft WebView2 をインストールしています...
japanese.WebView2Failed=Microsoft WebView2 をインストールできませんでした（コード %1）。アプリの起動時と設定で、もう一度インストールできます。
chinesesimplified.WebView2Group=Microsoft WebView2
chinesesimplified.WebView2Task=安装 Microsoft WebView2：免费，应用自己的窗口需要它（推荐）
chinesesimplified.WebView2Installing=正在安装 Microsoft WebView2...
chinesesimplified.WebView2Failed=Microsoft WebView2 没有装上（代码 %1）。应用启动时和它的设置中会再次提供。
farsi.WebView2Group=Microsoft WebView2
farsi.WebView2Task=نصب Microsoft WebView2: رایگان و لازم برای پنجرهٔ خود برنامه (توصیه‌شده)
farsi.WebView2Installing=در حال نصب Microsoft WebView2...
farsi.WebView2Failed=Microsoft WebView2 نصب نشد (کد %1). برنامه هنگام اجرا و در تنظیماتش دوباره پیشنهادش می‌دهد.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "gamebackup"; Description: "{cm:BackupTask}"; GroupDescription: "{cm:BackupGroup}"
Name: "webview2"; Description: "{cm:WebView2Task}"; GroupDescription: "{cm:WebView2Group}"; Check: OfferWebView2

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
// The apps' screens need Microsoft's WebView2 Runtime (built into Windows 11, on most Windows 10 PCs). Where it's
// missing, the tasks page offers it, ticked (the WebView2Task words above); the apps offer it too.
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

// Wine (Linux, the Steam Deck through Proton), told the way the apps tell it (rusemod.browsermode.under_wine): Wine's
// ntdll has wine_get_version, Windows' doesn't. WebView2 doesn't start under Wine (issue #21), so it's never offered.
function WineGetVersion: Cardinal; external 'wine_get_version@ntdll.dll cdecl delayload';

function UnderWine: Boolean;
begin
  try
    WineGetVersion;
    Result := True;
  except
    Result := False;  // no such function: Windows
  end;
end;

// The tasks page's WebView2 box: only where it's missing, never under Wine, never on a silent install (the apps' own
// updates: the player sees no box then, and the app offers it on its next start instead)
function OfferWebView2: Boolean;
begin
  Result := (not WizardSilent) and (not HasWebView2) and (not UnderWine);
end;

// Microsoft's installer, run silently as Microsoft's distribution page gives it ("/silent /install"), while the
// installer's own page says what it's doing. When it ends without WebView2, the player is told: nothing fails silently.
procedure InstallWebView2;
var
  ResultCode: Integer;
begin
  WizardForm.StatusLabel.Caption := CustomMessage('WebView2Installing');
  WizardForm.FilenameLabel.Caption := '';
  if not Exec(ExpandConstant('{app}\webview2\MicrosoftEdgeWebview2Setup.exe'), '/silent /install', '', SW_HIDE,
    ewWaitUntilTerminated, ResultCode) then
    MsgBox(FmtMessage(CustomMessage('WebView2Failed'), [IntToStr(ResultCode)]), mbError, MB_OK)
  else if not HasWebView2 then
    MsgBox(FmtMessage(CustomMessage('WebView2Failed'), [IntToStr(ResultCode)]), mbError, MB_OK);
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
begin
  if (CurStep = ssPostInstall) and (not WizardSilent) and WizardIsTaskSelected('gamebackup') then
    AskForBackup;
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('webview2') then
    InstallWebView2;
end;
