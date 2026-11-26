; The installer for either app (Inno Setup 6). installers/build_app.py passes the app's details:
; AppName, AppId, AppVersion, ExeName, AppDescription, SourceDir (the built program folder), IconFile, OutputDir,
; OutputName. It installs for the current Windows user only, so it never asks for admin rights, and it never touches
; the game. Uninstalling keeps the platform folder (mods, settings, the game index) in %LOCALAPPDATA% unless the
; player says Yes to the question at uninstall (it starts on No; not asked while the other app is still installed).

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

; Asked when the app is uninstalled (the owner, 2026-11-25, decision 19: "add a second setting for that"): also delete the
; apps' settings and data (the platform folder, rusemod.home). Never ticked for the player: the default answer is No.
english.DeleteDataQuestion=Also delete the settings and data of RUSE Launcher and RUSE Studio on this PC?%n%nBoth apps share them: your saved choices and the apps' stored files. Your game, the copies made from it and your Documents\RUSE 2.0 folder are never deleted.%n%nAny mods, maps, exports or backups still kept in that folder from an older version are kept too.%n%nChoose No to keep them, for a later install.
french.DeleteDataQuestion=Supprimer aussi les réglages et les données de RUSE Launcher et de RUSE Studio sur ce PC ?%n%nLes deux applications les partagent : vos choix enregistrés et les fichiers que les applications conservent. Votre jeu, les copies faites à partir de lui et votre dossier Documents\RUSE 2.0 ne sont jamais supprimés.%n%nLes mods, cartes, exports ou sauvegardes encore conservés dans ce dossier par une ancienne version sont conservés aussi.%n%nChoisissez Non pour les garder, pour une installation ultérieure.
german.DeleteDataQuestion=Auch die Einstellungen und Daten von RUSE Launcher und RUSE Studio auf diesem PC löschen?%n%nBeide Apps teilen sie: deine gespeicherten Einstellungen und die Dateien, die die Apps aufbewahren. Dein Spiel, die daraus gemachten Kopien und dein Ordner Dokumente\RUSE 2.0 werden nie gelöscht.%n%nMods, Karten, Exporte oder Sicherungen, die noch von einer älteren Version in diesem Ordner liegen, bleiben ebenfalls erhalten.%n%nWähle Nein, um sie für eine spätere Installation zu behalten.
italian.DeleteDataQuestion=Eliminare anche le impostazioni e i dati di RUSE Launcher e RUSE Studio su questo PC?%n%nLe due app li condividono: le tue scelte salvate e i file che le app conservano. Il tuo gioco, le copie fatte da esso e la cartella Documenti\RUSE 2.0 non vengono mai eliminati.%n%nAnche mod, mappe, esportazioni o backup rimasti in quella cartella da una versione precedente vengono conservati.%n%nScegli No per conservarli, per un'installazione futura.
spanish.DeleteDataQuestion=¿Borrar también los ajustes y los datos de RUSE Launcher y RUSE Studio en este PC?%n%nLas dos aplicaciones los comparten: tus opciones guardadas y los archivos que guardan las aplicaciones. Tu juego, las copias hechas a partir de él y tu carpeta Documentos\RUSE 2.0 nunca se borran.%n%nLos mods, mapas, exportaciones o copias de seguridad que una versión anterior aún guarde en esa carpeta también se conservan.%n%nElige No para conservarlos, para una instalación posterior.
polish.DeleteDataQuestion=Usunąć też ustawienia i dane RUSE Launcher i RUSE Studio na tym komputerze?%n%nObie aplikacje korzystają z nich wspólnie: zapisane wybory i pliki przechowywane przez aplikacje. Twoja gra, kopie z niej zrobione i folder Dokumenty\RUSE 2.0 nigdy nie są usuwane.%n%nMody, mapy, eksporty lub kopie zapasowe, które starsza wersja nadal trzyma w tym folderze, również zostają.%n%nWybierz Nie, aby je zachować na późniejszą instalację.
russian.DeleteDataQuestion=Удалить также настройки и данные RUSE Launcher и RUSE Studio на этом компьютере?%n%nОба приложения используют их вместе: ваши сохранённые выборы и файлы, которые хранят приложения. Ваша игра, сделанные из неё копии и папка Документы\RUSE 2.0 никогда не удаляются.%n%nМоды, карты, экспорты и резервные копии, которые старая версия всё ещё хранит в этой папке, тоже сохраняются.%n%nВыберите Нет, чтобы сохранить их для будущей установки.
czech.DeleteDataQuestion=Smazat také nastavení a data RUSE Launcheru a RUSE Studia na tomto počítači?%n%nObě aplikace je sdílejí: vaše uložené volby a soubory, které aplikace uchovávají. Vaše hra, kopie z ní vytvořené a složka Dokumenty\RUSE 2.0 se nikdy nemažou.%n%nMódy, mapy, exporty nebo zálohy, které v této složce ještě uchovává starší verze, se také zachovají.%n%nVyberte Ne, abyste je zachovali pro pozdější instalaci.
japanese.DeleteDataQuestion=このPCにある RUSE Launcher と RUSE Studio の設定とデータも削除しますか？%n%n2つのアプリが共有している、保存した選択内容とアプリが保管しているファイルです。ゲーム本体、そこから作ったコピー、ドキュメント\RUSE 2.0 フォルダーは削除されません。%n%n古いバージョンがこのフォルダーにまだ保管しているMod、マップ、エクスポート、バックアップも残ります。%n%n後でインストールし直すときのために残すには「いいえ」を選んでください。
chinesesimplified.DeleteDataQuestion=是否同时删除这台电脑上 RUSE Launcher 和 RUSE Studio 的设置和数据？%n%n两个应用共用它们：你保存的选择和应用保存的文件。你的游戏、由它制作的副本以及“文档\RUSE 2.0”文件夹永远不会被删除。%n%n旧版本仍保存在该文件夹中的模组、地图、导出文件和备份也会保留。%n%n选择“否”可保留它们，以便以后重新安装。
farsi.DeleteDataQuestion=تنظیمات و داده‌های RUSE Launcher و RUSE Studio روی این رایانه هم پاک شود؟%n%nهر دو برنامه آن‌ها را مشترک دارند: انتخاب‌های ذخیره‌شدهٔ شما و فایل‌هایی که برنامه‌ها نگه می‌دارند. بازی شما، نسخه‌هایی که از آن ساخته شده و پوشهٔ Documents\RUSE 2.0 هرگز پاک نمی‌شوند.%n%nمادها، نقشه‌ها، خروجی‌ها یا نسخه‌های پشتیبانی که نسخهٔ قدیمی‌تر هنوز در آن پوشه نگه می‌دارد نیز نگه داشته می‌شوند.%n%nبرای نگه داشتن آن‌ها برای نصب بعدی، «خیر» را انتخاب کنید.

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

// The question at uninstall (not on a silent uninstall: the player didn't see it then): also delete the apps' settings
// and data, the platform folder in %LOCALAPPDATA% that RUSE Launcher and RUSE Studio share (rusemod.home). The answer
// starts on No. Only that folder is ever deleted; a folder set by hand ($RUSE_PLATFORM_HOME) is not touched. Before
// 2026-10-30 the player's mods, maps, exports and backups lived in it (rusemod.yourfiles OLD_NAMES) until the Studio
// moved them to Documents on its first start: those four folders are kept, never deleted here.
function IsOldPlayerFolder(Name: String): Boolean;
begin
  Result := (CompareText(Name, 'mods') = 0) or (CompareText(Name, 'maps') = 0) or
    (CompareText(Name, 'exports') = 0) or (CompareText(Name, 'mod-backups') = 0);
end;

procedure DeleteSettingsAndData(Folder: String);
var
  Found: TFindRec;
  Path: String;
begin
  if FindFirst(Folder + '\*', Found) then
  begin
    try
      repeat
        if (Found.Name <> '.') and (Found.Name <> '..') then
        begin
          Path := Folder + '\' + Found.Name;
          if (Found.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0 then
          begin
            if not IsOldPlayerFolder(Found.Name) then
              DelTree(Path, True, True, True);
          end
          else
            DeleteFile(Path);
        end;
      until not FindNext(Found);
    finally
      FindClose(Found);
    end;
  end;
  RemoveDir(Folder);   // only when nothing is left in it
end;

// Is the other app (RUSE Launcher or RUSE Studio, built from this same script with its own id) still installed? Inno
// Setup records an install as the uninstall entry "{AppId}_is1": for this user (HKCU) or, when it was installed for
// all users, in the 64-bit view of HKLM (the installer runs in 64-bit mode).
function OtherAppStillInstalled: Boolean;
var
  Key: String;
begin
  Key := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{' + '{#OtherAppId}' + '}_is1';
  Result := RegKeyExists(HKCU, Key) or RegKeyExists(HKLM64, Key);
end;

// While the other app is still installed, the shared folder is its settings too: nothing is asked and nothing of it is
// deleted (the lead's reading of the owner's round 3 answer, 2026-11-25); the question comes with the last of the two.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Folder: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    Folder := ExpandConstant('{localappdata}\RUSE Mod Platform');
    if (not UninstallSilent) and DirExists(Folder) and (not OtherAppStillInstalled) then
      if MsgBox(CustomMessage('DeleteDataQuestion'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DeleteSettingsAndData(Folder);
  end;
end;
