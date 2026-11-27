; The installer for either app (Inno Setup 6). installers/build_app.py passes the app's details:
; AppName, AppId, AppVersion, ExeName, AppDescription, SourceDir (the built program folder), IconFile, OutputDir,
; OutputName. It installs for the current Windows user only, so it never asks for admin rights, and it never touches
; the game. Uninstalling keeps the platform folder (mods, settings, the game index) in %LOCALAPPDATA% unless the
; player says Yes to the question at uninstall (it starts on No; not asked while the other app is still installed).

#ifndef AppName
  #error Build this through installers/build_app.py, which passes the app's details.
#endif
#ifndef OtherAppId
  #error Build this through installers/build_app.py, which passes the other app's id (OtherAppId) too.
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
; Off (FL-125, the owner's "A A", 2026-11-26): Inno Setup 6.7 turns Windows' Redirection Guard on in Setup by default,
; and the app Setup opens (the Launch box at the end, the app opened again after an in-app update) inherits it: a game
; folder reached through a junction a non-admin made (D:\Steam linked to another drive) then couldn't be read, "error
; 448" (Launcher 0.4.8.23, his screenshot). Inno Setup's help: child processes started by Setup inherit RedirectionGuard.
RedirectionGuard=no
OutputDir={#OutputDir}
OutputBaseFilename={#OutputName}
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\{#ExeName}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; The first page says the terms and privacy notice are shown at the app's first start, where to read them,
; and that updates are asked for only once they're accepted (agreement version 5).
DisableWelcomePage=no
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

[Messages]
; The Welcome page's text, in each of the eleven languages ({#AppName}: RUSE Launcher or RUSE Studio).
english.WelcomeLabel2={#AppName} is a free, fan-made app for R.U.S.E. At its first start it shows our terms of use and privacy notice, which you can also read at https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md. Once you've accepted them, it asks GitHub at each start whether there's a new version, and an update we mark required installs by itself.
french.WelcomeLabel2={#AppName} est une application gratuite, faite par des fans, pour R.U.S.E. À son premier démarrage, elle montre nos conditions d'utilisation et notre notice de confidentialité, que vous pouvez aussi lire sur https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md. Une fois que vous les avez acceptées, elle demande à GitHub à chaque démarrage s'il existe une nouvelle version, et une mise à jour que nous marquons comme obligatoire s'installe toute seule.
german.WelcomeLabel2={#AppName} ist eine kostenlose, von Fans gemachte App für R.U.S.E. Beim ersten Start zeigt sie unsere Nutzungsbedingungen und Datenschutzerklärung, die du auch unter https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md lesen kannst. Sobald du sie akzeptiert hast, fragt sie bei jedem Start bei GitHub, ob es eine neue Version gibt, und ein Update, das wir als erforderlich markieren, installiert sich von selbst.
italian.WelcomeLabel2={#AppName} è un'app gratuita, fatta dai fan, per R.U.S.E. Al primo avvio mostra i nostri termini di utilizzo e l'informativa sulla privacy, che puoi leggere anche su https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md. Una volta che li hai accettati, a ogni avvio chiede a GitHub se c'è una nuova versione, e un aggiornamento che segniamo come obbligatorio si installa da solo.
spanish.WelcomeLabel2={#AppName} es una aplicación gratuita, hecha por aficionados, para R.U.S.E. En su primer inicio muestra nuestros términos de uso y aviso de privacidad, que también puedes leer en https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md. Una vez que los hayas aceptado, pregunta a GitHub en cada inicio si hay una versión nueva, y una actualización que marcamos como obligatoria se instala sola.
polish.WelcomeLabel2={#AppName} to darmowa aplikacja tworzona przez fanów dla R.U.S.E. Przy pierwszym uruchomieniu pokazuje nasze warunki korzystania i informację o prywatności, które możesz też przeczytać pod adresem https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md. Gdy je zaakceptujesz, przy każdym uruchomieniu pyta GitHub, czy jest nowa wersja, a aktualizacja, którą oznaczymy jako wymaganą, instaluje się sama.
russian.WelcomeLabel2={#AppName} — бесплатное приложение для R.U.S.E., созданное фанатами. При первом запуске оно показывает наши условия использования и уведомление о конфиденциальности, которые можно прочитать и по адресу https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md. После того как вы их приняли, оно при каждом запуске спрашивает у GitHub, есть ли новая версия, а обновление, которое мы помечаем как обязательное, устанавливается само.
czech.WelcomeLabel2={#AppName} je bezplatná aplikace pro R.U.S.E. vytvořená fanoušky. Při prvním spuštění ukáže naše podmínky používání a oznámení o ochraně soukromí, které si můžete přečíst také na https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md. Jakmile je přijmete, při každém spuštění se ptá GitHubu, zda existuje nová verze, a aktualizace, kterou označíme jako povinnou, se nainstaluje sama.
japanese.WelcomeLabel2={#AppName} は、R.U.S.E. のための、ファンメイドの無料アプリです。最初の起動時に、私たちの利用規約とプライバシー通知を表示します。これは https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md でも読めます。同意すると、アプリは起動のたびに GitHub に新しいバージョンがあるかを尋ね、私たちが必須とした更新は自動でインストールされます。
chinesesimplified.WelcomeLabel2={#AppName} 是一个免费的、同人制作的 R.U.S.E. 应用。它在第一次启动时会显示我们的用户条款与隐私声明,你也可以在 https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md 阅读。你接受它们之后,它每次启动都会向 GitHub 询问是否有新版本,我们标记为必需的更新会自动安装。
farsi.WelcomeLabel2={#AppName} یک برنامهٔ رایگان ساختهٔ طرفداران برای R.U.S.E. است. در اولین شروع شرایط استفاده و اعلامیهٔ حریم خصوصی ما را نشان می‌دهد، که می‌توانید در https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/PRIVACY.md هم بخوانید. وقتی آن‌ها را پذیرفتید، در هر بار شروع از GitHub می‌پرسد نسخهٔ تازه‌ای هست یا نه، و به‌روزرسانی‌ای که الزامی علامت بزنیم خودش نصب می‌شود.

[CustomMessages]
; The clean game backup offered beside the desktop icon (the owner, 2026-10-01), with why under the list. The app
; makes it on its first start (rusemod.backup.BackupCalls.backup_requested reads the mark left at the end).
english.BackupGroup=Your game
english.BackupTask=Keep a clean copy of my game's files (recommended)
english.BackupWhy=Why: RUSE Launcher and RUSE Studio never change your game's folder unless you ask them to restore it from this copy, but other mod managers and hand edits can, and every modded game is built from those files. With a clean copy, the app can check your game's files and put back any that changed. It's made the first time the app starts: a few minutes, and about as much disk space as the game (in RUSE-Backup, on the game's drive).
french.BackupGroup=Votre jeu
french.BackupTask=Garder une copie propre des fichiers de mon jeu (recommandé)
french.BackupWhy=Pourquoi : RUSE Launcher et RUSE Studio ne modifient jamais le dossier de votre jeu, sauf si vous leur demandez de le restaurer depuis cette copie, mais d'autres gestionnaires de mods et des modifications à la main le peuvent, et chaque jeu moddé est construit à partir de ces fichiers. Avec une copie propre, l'application peut vérifier les fichiers de votre jeu et remettre ceux qui ont changé. Elle est faite au premier démarrage de l'application : quelques minutes, et à peu près autant d'espace disque que le jeu (dans RUSE-Backup, sur le disque du jeu).
german.BackupGroup=Ihr Spiel
german.BackupTask=Eine saubere Kopie der Spieldateien behalten (empfohlen)
german.BackupWhy=Warum: RUSE Launcher und RUSE Studio ändern den Ordner deines Spiels nie, es sei denn, du bittest sie, ihn aus dieser Kopie wiederherzustellen, andere Mod-Manager und Änderungen von Hand aber schon, und jedes gemoddete Spiel wird aus diesen Dateien gebaut. Mit einer sauberen Kopie kann die App die Spieldateien prüfen und geänderte zurücksetzen. Sie wird beim ersten Start der App erstellt: ein paar Minuten und etwa so viel Platz wie das Spiel (in RUSE-Backup auf dem Laufwerk des Spiels).
italian.BackupGroup=Il tuo gioco
italian.BackupTask=Conserva una copia pulita dei file del gioco (consigliato)
italian.BackupWhy=Perché: RUSE Launcher e RUSE Studio non cambiano mai la cartella del tuo gioco a meno che tu chieda loro di ripristinarla da questa copia, ma altri gestori di mod e le modifiche a mano possono farlo, e ogni gioco moddato è costruito da quei file. Con una copia pulita, l'app può controllare i file del tuo gioco e rimettere a posto quelli che sono cambiati. Viene fatta la prima volta che l'app si avvia: qualche minuto, e circa lo stesso spazio su disco del gioco (in RUSE-Backup, sul disco del gioco).
spanish.BackupGroup=Tu juego
spanish.BackupTask=Guardar una copia limpia de los archivos del juego (recomendado)
spanish.BackupWhy=Por qué: RUSE Launcher y RUSE Studio nunca cambian la carpeta de tu juego salvo que les pidas restaurarla desde esta copia, pero otros gestores de mods y los cambios a mano sí pueden, y cada juego con mods se construye a partir de esos archivos. Con una copia limpia, la aplicación puede comprobar los archivos de tu juego y devolver los que cambiaron. Se hace la primera vez que se abre la aplicación: unos minutos, y más o menos el mismo espacio en disco que el juego (en RUSE-Backup, en la unidad del juego).
polish.BackupGroup=Twoja gra
polish.BackupTask=Zachowaj czystą kopię plików gry (zalecane)
polish.BackupWhy=Dlaczego: RUSE Launcher i RUSE Studio nigdy nie zmieniają folderu twojej gry, chyba że poprosisz je o przywrócenie go z tej kopii, ale inne menedżery modów i ręczne zmiany mogą to zrobić, a każda gra z modami jest budowana z tych plików. Dzięki czystej kopii aplikacja może sprawdzić pliki twojej gry i przywrócić te, które się zmieniły. Powstaje przy pierwszym uruchomieniu aplikacji: kilka minut i mniej więcej tyle miejsca na dysku, ile zajmuje gra (w RUSE-Backup, na dysku gry).
russian.BackupGroup=Ваша игра
russian.BackupTask=Сохранить чистую копию файлов игры (рекомендуется)
russian.BackupWhy=Зачем: RUSE Launcher и RUSE Studio никогда не меняют папку вашей игры, если только вы не попросите восстановить её из этой копии, но другие менеджеры модов и ручные правки могут, а каждая игра с модами собирается из этих файлов. С чистой копией приложение может проверить файлы вашей игры и вернуть на место изменившиеся. Она создаётся при первом запуске приложения: несколько минут и примерно столько же места на диске, сколько занимает игра (в RUSE-Backup, на диске с игрой).
czech.BackupGroup=Vaše hra
czech.BackupTask=Uchovat čistou kopii souborů hry (doporučeno)
czech.BackupWhy=Proč: RUSE Launcher a RUSE Studio nikdy nemění složku vaší hry, pokud je nepožádáte, aby ji obnovily z této kopie, ale jiní správci módů a ruční úpravy ji změnit mohou a každá hra s módy se sestavuje z těchto souborů. S čistou kopií může aplikace zkontrolovat soubory vaší hry a vrátit ty, které se změnily. Vytvoří se při prvním spuštění aplikace: několik minut a zhruba tolik místa na disku jako hra (v RUSE-Backup, na disku hry).
japanese.BackupGroup=ゲーム
japanese.BackupTask=ゲームファイルのクリーンなコピーを保存する（推奨）
japanese.BackupWhy=理由: RUSE Launcher と RUSE Studio は、このコピーから復元するよう頼まれない限りゲームのフォルダーを変更しませんが、ほかの MOD マネージャーや手作業の編集は変更することがあり、MOD入りのゲームはすべてそれらのファイルから作られます。クリーンなコピーがあれば、アプリはゲームのファイルを確認し、変わったものを元に戻せます。これはアプリの最初の起動時に作られます。数分かかり、ゲームと同じくらいのディスク容量が必要です（ゲームのドライブの RUSE-Backup に）。
chinesesimplified.BackupGroup=你的游戏
chinesesimplified.BackupTask=保留游戏文件的干净备份（推荐）
chinesesimplified.BackupWhy=为什么:除非你要求从这份副本中恢复,否则 RUSE Launcher 和 RUSE Studio 不会改动你游戏的文件夹,但其他模组管理器和手动修改可能会,而且每个模组版游戏都是用这些文件构建的。有了干净副本,应用就能检查你游戏的文件,并把改变了的文件放回去。它在应用第一次启动时制作:需要几分钟,占用的磁盘空间与游戏差不多(在游戏所在驱动器的 RUSE-Backup 中)。
farsi.BackupGroup=بازی شما
farsi.BackupTask=نگه داشتن یک پشتیبان تمیز از فایل‌های بازی (توصیه‌شده)
farsi.BackupWhy=چرا: RUSE Launcher و RUSE Studio پوشهٔ بازی شما را تغییر نمی‌دهند مگر این‌که از آن‌ها بخواهید آن را از این نسخه بازگردانند، اما مدیرهای ماد دیگر و ویرایش‌های دستی می‌توانند، و هر بازی مادشده از همان فایل‌ها ساخته می‌شود. با یک نسخهٔ تمیز، برنامه می‌تواند فایل‌های بازی شما را بررسی کند و هر فایلی را که تغییر کرده سر جایش برگرداند. این نسخه اولین باری که برنامه شروع می‌شود ساخته می‌شود: چند دقیقه، و فضای دیسکی تقریباً به اندازهٔ خود بازی (در RUSE-Backup، روی درایو بازی).
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
