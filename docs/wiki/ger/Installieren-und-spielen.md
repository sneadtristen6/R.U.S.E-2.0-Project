# Installieren und spielen

> **Für:** Spieler · **Du brauchst:** R.U.S.E. auf Steam, installiert · **Dauer:** 5 Minuten

**Kurz gesagt:** lade **RUSE-Launcher-Setup** von der Release-Seite herunter, führe es aus, öffne **RUSE Launcher**,
klicke auf **Unterstützte Mods**, hake einen Mod an und drücke **Installieren**, leg ihn in ein Mod-Set, dann
**Spielen**. Jeder Schritt unten sagt genau, wo du klickst.

Zum Spielen von Mods brauchst du nur **RUSE Launcher**. **RUSE Studio** ist zum Erstellen da (siehe Ende dieser Seite).

## Schritt 1: Den Launcher herunterladen

1. Öffne die Seite der [Launcher-Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher).
2. Das neueste steht oben, markiert mit **Latest** (zum Beispiel *RUSE Launcher 0.4.8.9*).
3. Scroll darunter zu **Assets** und klicke auf **RUSE-Launcher-Setup-0.4.8.9.exe** (die Versionsnummer ändert sich; nimm
   die `.exe`, die mit `RUSE-Launcher-Setup` beginnt). Dein Browser lädt sie herunter.

Die anderen Dateien dort (`RUSE-Launcher-notes.json`, *Source code*) brauchst du nicht.

## Schritt 2: Installieren

1. Öffne die heruntergeladene Datei (meist in deinem Ordner **Downloads**).
2. **„Der Computer wurde durch Windows geschützt“?** Klicke auf **Weitere Informationen**, dann auf **Trotzdem
   ausführen**. Die App ist neu für die Reputationsprüfung von Windows; ihr Code ist öffentlich hier auf GitHub.
3. Klick dich durch das Installationsprogramm. Lass **Eine saubere Kopie der Spieldateien behalten** angehakt: die Apps
   ändern den Ordner deines Spiels nie, andere Mod-Manager und Änderungen von Hand aber schon, und jedes gemoddete Spiel
   wird aus diesen Dateien gebaut. Die Kopie wird beim ersten Start der App erstellt (ein paar Minuten, etwa so viel
   Speicherplatz wie das Spiel).
4. Starte **RUSE Launcher** (Startmenü oder Verknüpfung auf dem Desktop). Beim ersten Mal **Wählen Sie Ihre Sprache**:
   eine von elf, die zehn des Spiels und Persisch (فارسی); die Sprachschaltfläche oben ändert sie jederzeit. Er findet
   R.U.S.E. selbst über Steam. Sagt er, dass er es nicht kann: **Einstellungen > Spielordner > Ordner wählen…** und
   wähle den Ordner, der `RUSE.exe` enthält (meist `C:\Program Files (x86)\Steam\steamapps\common\R.U.S.E`).

> [!IMPORTANT]
> **R.U.S.E. 2.0 funktioniert nur mit einer Kopie des Spiels, die du auf Steam besitzt.** Bevor ein gemoddetes Spiel
> startet, prüfen der Launcher und das Studio den Spielordner: Steams Eintrag, dass R.U.S.E. dort installiert ist,
> Steams eigene Datei darin, und dass keine Dateien da sind, die das Spiel ohne Steam laufen lassen. Können sie es nicht
> bestätigen, sagt ein Fenster, warum und was zu tun ist (Spielen bleibt bis dahin aus): siehe
> [[Wenn etwas schiefgeht|Wenn-etwas-schiefgeht]].

## Schritt 3: Mods holen

**Aus unserer Liste (am einfachsten):** klicke auf **Unterstützte Mods**, hake die Mods an, die du willst, und drücke
**Installieren**. Jede Datei wird heruntergeladen und mit der Liste abgeglichen, bevor sie in deine Bibliothek kommt.

**Aus einer Datei, die jemand geteilt hat:** klicke auf **Mod-Datei hinzufügen…** und wähle die Datei, oder zieh sie auf
das Fenster. Der Launcher nimmt:
- `.rusemod`: mit RUSE Studio gemacht;
- `.rmod`: für den RUSE Mod Manager von LittleGroove gemacht;
- `.zip`: ein gezippter Mod-Ordner.

Er prüft die Datei zuerst: eine Datei, die kein Mod ist oder ein Programm enthält, wird mit Begründung abgelehnt.

**Ein alter Mod, der als eigene Dateien des Spiels kommt** (`.dat`-Pakete, die du in den Spielordner kopieren solltest):
klicke auf **Alten Mod umwandeln…**, wähle seinen Ordner, gib ihm einen Namen und klicke auf **Umwandeln und zur
Bibliothek hinzufügen**. Dein Spielordner wird nicht angerührt.

## Schritt 4: Wählen, was du spielst

1. Ein **Mod-Set** sind die Mods, die du zusammen spielst, in einer Reihenfolge. Klicke auf **Neues Mod-Set…**, füge die
   Mods hinzu und bring sie in eine Reihenfolge (wenn zwei Mods dasselbe ändern, gewinnt der untere).
2. Lassen sich zwei Mods nicht zusammen spielen, sagt der Launcher dir, welche und warum, bevor du spielst.

## Schritt 5: Spielen

Wähle dein Mod-Set und drücke **Spielen**. Beim ersten Mal baut der Launcher eine gemoddete Kopie des Spiels (etwa eine
Minute); danach nur das, was sich geändert hat. Dann startet R.U.S.E., mit deinen Mods.

Dein gemoddetes Spiel zeigt **R.U.S.E. 2.0 in Gold**: es öffnet sich mit einer Schlachtszene, und sein Hauptmenü, die
Menüs und die Ladebildschirme tragen den goldenen Titel. Er wird beim ersten Mal auf deinem PC aus den Dateien deines
eigenen Spiels gemacht (ein paar Minuten, einmal). Um den eigenen Titel des Spiels zu behalten, nimm in den
**Einstellungen** unter **Der Titel des Spiels** den Haken weg.

> [!NOTE]
> Startest du R.U.S.E. über **Steam**, startet das Spiel **ohne** Mods, wie immer. Um mit Mods zu spielen, starte es
> über **Spielen** im Launcher. Deine Steam-Installation wird nie verändert.

## Updates

Der Launcher prüft bei jedem Start, ob es eine neue Version gibt: klicke auf **Jetzt aktualisieren**, wenn er eine
anbietet. Schlägt das Update mit „certificate verify failed“ fehl, lade das neueste `RUSE-Launcher-Setup` aus Schritt 1 in
deinem Browser herunter und führe es aus: es installiert sich über das alte und behält deine Mods.

**Notwendige Updates:** Ein als notwendig markiertes Update (ein wichtiges, etwa eine Sicherheitskorrektur) lässt sich nicht überspringen. Ein Fenster legt sich über den Launcher, das Update installiert sich von selbst, und der Launcher öffnet sich wieder; bis es installiert ist, bleibt **Spielen** gesperrt. Ohne Internet sagt das Fenster das: Verbinden Sie sich und klicken Sie auf **Erneut versuchen**. Das Studio macht es genauso, mit **Im Spiel testen**.

## Probleme?

| Was du siehst | Was du tun kannst |
|---|---|
| „Der Computer wurde durch Windows geschützt“ | **Weitere Informationen**, dann **Trotzdem ausführen** (Schritt 2). |
| Der Launcher findet R.U.S.E. nicht | **Einstellungen > Spielordner > Ordner wählen…**, der Ordner mit `RUSE.exe`. |
| „certificate verify failed: unable to get local issuer certificate“ | Hol dir Launcher 0.4.8.4 oder neuer (Schritt 1); siehe [[Wenn etwas schiefgeht|Wenn-etwas-schiefgeht]]. |
| „unable to get issuer certificate“ oder „dieser PC vertraut dem Sicherheitszertifikat der Seite nicht“ beim Installieren von Mods | Hol dir Launcher 0.4.8.9 oder neuer (Schritt 1), oder lade den Mod in deinem Browser herunter und nutze **Mod-Datei hinzufügen…**; siehe [[Wenn etwas schiefgeht|Wenn-etwas-schiefgeht]]. |
| Das Spiel startet ohne meine Mods | Starte es über **Spielen** im Launcher, nicht über Steam. |
| Freunde können meinem Spiel nicht beitreten | Alle brauchen dieselben Mods in derselben Reihenfolge: [[Mit Freunden spielen|Mit-Freunden-spielen]]. |
| Etwas anderes | [[Wenn etwas schiefgeht|Wenn-etwas-schiefgeht]], oder frag in den [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) oder auf dem [Discord](https://discord.gg/h54t5baNsC). |

## Linux und Steam Deck (über Proton)

Kann das eigene Fenster einer App ihre Seiten nicht zeigen (unter Proton bleibt es blau, weil WebView2 von Microsoft dort
nicht startet), öffnet sich die App stattdessen in deinem Webbrowser, und ein kleines Fenster sagt das: lass das
Fenster offen, während du spielst, und schließ es, um die App zu schließen. Auf Linux noch nicht ausprobiert: bitte sag
uns in den [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions), wie es läuft.

## Mods erstellen: RUSE Studio

1. Öffne die Seite der [Studio-Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio). Das
   Studio ist eine Vorschau, daher sind seine Releases mit **Pre-release** markiert: nimm das neueste.
2. Klicke unter **Assets** auf **RUSE-Studio-Setup-0.9.8.9.exe** (die neueste Version) und führe es aus wie in Schritt 2.
3. Starte **RUSE Studio** und folge dann [[Die erste Mod|Die-erste-Mod]] (10 Minuten).

**Weiter:** [[Mit Freunden spielen|Mit-Freunden-spielen]]

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Install-and-Play]]
