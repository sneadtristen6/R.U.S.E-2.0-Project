# Wenn etwas schiefgeht

Such, was du siehst, und folge der Lösung.

## Probier zuerst die Fehlersuche

**Fehlersuche** prüft in einem Durchgang, was einen Test oder **Spielen** aufhalten kann: ob das Spiel gefunden wurde, ob
Steam läuft, ob R.U.S.E. noch aus einer gemoddeten Kopie läuft, das Laufwerk und sein freier Platz, übrig gebliebene
Kopien, schreibgeschützte Dateien, und ob die App dort schreiben kann, wo Kopien hinkommen. Jedes Problem, das sie
beheben kann, hat eine Schaltfläche; die übrigen sagen, was zu tun ist.

- In RUSE Studio: neben **Im Spiel testen** und unter **Einstellungen > Hilfe**. In RUSE Launcher: die untere Leiste, und
  bei jeder Problemmeldung (Studio 0.8.0, Launcher 0.3.0).
- **Bericht kopieren** gibt einen Text zum Einfügen in einen [[Fehlerbericht|Einen-Fehler-melden]] (dein Windows-Benutzername
  wird weggelassen).

## Das Spiel selbst scheint verändert (durch einen anderen Mod-Manager oder eine Änderung von Hand)

**Einstellungen > Saubere Sicherung des Spiels** behält eine saubere Kopie der Dateien des Spiels, prüft sie dagegen und
setzt zurück, was sich geändert hat. Dateien, die nicht zum Spiel gehören, werden beiseitegelegt, nie gelöscht. Oder
**Mit Steam überprüfen** lässt Steam das Spiel reparieren. Das ist die einzige Stelle, an der die Apps in deinen
Spielordner schreiben, und nur, wenn du darum bittest.

## Ein roter Balken unter der Kopfzeile des Studios

Das ist die **Mod-Prüfung**. Das Studio liest jede Datei deines Mods so, wie der Build des Spiels es tun wird, wenn du den
Mod wählst und noch einmal vor **Im Spiel testen**. Jedes Problem wird in einfachen Worten gesagt (was falsch ist, auf
welcher Karte, was zu tun ist), mit einer Schaltfläche, die es behebt, wo das geht: einen fehlenden Wert eintragen, das
eine Element oder die eine Einstellung herausnehmen, die falsch ist, oder die Datei beiseitelegen. Die Datei, wie sie
war, bleibt daneben erhalten. **Details** zeigt die eigenen Worte des Builds, praktisch, wenn du um Hilfe bittest.

- **Beiseitelegen** (neben einer kaputten Kartendatei) benennt sie in `<name>.broken.toml` neben dem Original um: nichts
  geht verloren, der Mod funktioniert ohne sie, und diese Karte beginnt sauber.
- Ein Problem in `mod.toml` oder in den Änderungen an Einheiten hat kein Beiseitelegen: öffne die Datei und korrigiere
  die Zeile, die der Balken nennt, oder frag in
  [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

> [!NOTE]
> Bekannter Fall: RUSE Studio 0.7.0 und älter speicherten **Wasser**-Striche ohne ihren Wasserstand („the water brush
> needs level“). 0.7.1 behebt das; **Beiseitelegen** räumt eine alte Datei weg.

## Die App braucht lange zum Öffnen

- **Der erste Start nach der Installation** mit angehaktem „Eine saubere Kopie der Spieldateien behalten“ erstellt diese
  Kopie (den ganzen Spielordner, etwa 5,3 GB): die Einstellungen zeigen, wie weit sie ist, und die App lässt sich
  währenddessen nutzen.
- **Der Spielindex von RUSE Studio** wird einmal pro Spielversion erstellt, und erneut, wenn ein Update des Studios ihn
  ändert (etwa eine Minute; das Studio fragt vorher). Währenddessen lassen sich der Reiter Karten und die Einstellungen
  nutzen, und die Zeile unten sagt, wann er fertig ist.
- Alles andere: öffne **Fehlersuche** und **Bericht kopieren**. Der Bericht listet, wie lange jeder der letzten Starts
  der App bei jedem Schritt gedauert hat, in Sekunden: füg ihn in einen [[Fehlerbericht|Einen-Fehler-melden]] ein. Dieselben
  Zeilen werden in `%LOCALAPPDATA%\RUSE Mod Platform\logs\studio-start.log` aufbewahrt (die des Launchers:
  `launcher-start.log`).

## „Der Computer wurde durch Windows geschützt“

Die Apps sind neu für die Reputationsprüfung von Windows. Klicke auf **Weitere Informationen**, dann auf **Trotzdem
ausführen**.

## „certificate verify failed: unable to get local issuer certificate“ (oder „unable to get issuer certificate“)

Kein Mod lädt herunter, oder das Update nicht. Windows hatte das Zertifikat, mit dem GitHub geprüft wird, noch nicht
geholt; seit Launcher 0.4.8.4 und Studio 0.9.8.4 fragen die Apps Windows danach und versuchen es erneut. Seit Launcher
0.4.8.9 und Studio 0.9.8.9 versuchen sie es auch mit der Zertifikatsliste, die Firefox nutzt und die sie mitbringen,
für einen PC, dessen Windows es nicht holen kann (seine Zertifikatsupdates ausgeschaltet oder blockiert: „unable to get
issuer certificate“ oder „der PC vertraut dem Sicherheitszertifikat der Seite nicht“). Mit einer älteren App lässt sich
auch das Update nicht herunterladen: hol das Installationsprogramm in deinem Browser von den
[Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases) und führe es aus (es installiert sich über
das alte, wie das Update). Ein Mod lässt sich immer in deinem Browser von den
[Releases](https://github.com/sneadtristen6/Ruse-Mods/releases) der Mod-Liste herunterladen und mit **Mod-Datei hinzufügen…** im Launcher hinzufügen. Sagt
eine neue App es trotzdem: ein Antivirenprogramm, das sichere (HTTPS-)Verbindungen prüft, ein Schul- oder
Firmennetzwerk oder ein falsches Datum auf dem PC können es verursachen; sag es uns in
[Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## „[WinError 5] Access is denied“ beim Testen oder Spielen

Windows hat sich geweigert, eine Kopie des Spiels zu entfernen, die die App gemacht hat (in `RUSE-Instances`). Auch:
„An old modded copy at `...\RUSE-Instances\<name>.old` can't be removed“, bei jedem zweiten **Im Spiel testen** oder
**Spielen**.

- **Zuerst aktualisieren** (die Apps bieten es beim Öffnen an): ab RUSE Studio 0.7.6 und Launcher 0.2.11 hält eine
  Kopie, die Windows nicht löscht, nie einen Test auf: sie wird nach `RUSE-Instances\.trash` verschoben und dort
  entfernt, sobald nichts sie mehr festhält.
- **Läuft R.U.S.E. noch von einem früheren Test?** Die App sagt es, mit dem Namen des Programms: schließ das Spiel (sieh
  im Task-Manager auf der Registerkarte Details nach `RUSE.exe`), dann versuch es erneut. **Fehlersuche** findet ein
  Spiel, das noch aus einer Kopie läuft, und übrig gebliebene Kopien, und entfernt sie für dich.
- **Mit einer älteren Version:** lösch den Ordner, den die Meldung nennt (`...\RUSE-Instances\<name>.partial` oder
  `.old`; Windows fragt nach schreibgeschützten Dateien: sag ja; nur die Kopie wird gelöscht, nie das Spiel), dann
  versuch es erneut. Weigert sich Windows, starte Windows zuerst neu.
- Immer noch da? [[Melde es|Einen-Fehler-melden]] mit der ganzen Meldung.

## Die App findet R.U.S.E. nicht

**Einstellungen > Spielordner > Ordner wählen…** und wähle den Ordner, der `RUSE.exe` enthält (bei Steam:
`steamapps\common\R.U.S.E`).

## „Diese Kopie von R.U.S.E. konnte nicht bestätigt werden“

R.U.S.E. 2.0 funktioniert nur mit einer Kopie des Spiels, die du besitzt. Bis der Spielordner bestätigt ist, bleiben
**Spielen** und **Im Spiel testen** aus, und dieses Fenster sagt, warum: Steam hat keinen Eintrag, dass R.U.S.E. in
diesem Ordner installiert ist; Steams eigene Datei darin (`steam_api64.dll`) fehlt, ist verändert oder nicht von Valve;
oder der Ordner enthält Dateien, die das Spiel ohne Steam laufen lassen (es nennt sie).

- **Du besitzt es auf Steam:** klicke auf **Meine Dateien in Steam prüfen** (Steam stellt jede seiner Dateien wieder
  her, die fehlt oder verändert ist), entferne alle Dateien, die das Fenster nennt, und klicke dann auf **Erneut
  prüfen**. Ein Spielordner, den du von Hand gewählt hast, muss der sein, den Steam installiert hat.
- **Du besitzt es auf andere Weise** (eine Kopie im Karton aus der Zeit, bevor R.U.S.E. auf Steam war), **oder du
  glaubst, die Prüfung liegt falsch:** das Fenster zeigt **Dein Code** (aus diesem PC und dem Spielordner gebildet).
  Klicke auf **Kopieren**, dann auf **Ticket auf Discord eröffnen** oder **Ticket auf GitHub eröffnen** und füge ihn
  ein. Wir schicken dir einen Freischaltcode: füge ihn unter **Freischaltcode** ein und klicke auf **Freischalten**. Das
  bestätigt diese Kopie auf diesem PC.

Die Prüfung ist auf Windows, Linux und Steam Deck dieselbe. Dieses Projekt hilft niemandem, R.U.S.E. zu spielen, ohne es
zu besitzen: keine Spieldateien werden weitergegeben, kein Starten ohne Steam.

## „In einem älteren Mod-Format“ oder „von einem neueren RUSE Studio gespeichert“

- **Ein älteres Mod-Format:** der Mod wurde mit einem älteren Studio erstellt. **Diesen Mod aktualisieren** schreibt
  seine Dateien so um, wie dieses Studio sie liest, und behält, was sie bedeuten; vorher kommt ein Zip des ganzen Mods
  in den Ordner `Backups` des Studios.
- **Ein neueres RUSE Studio:** aktualisiere das Studio, bevor du diesen Mod änderst: ein älteres könnte verwerfen, was
  es nicht kennt.

## Beim Schließen fragt das Studio „RUSE Studio schließen?“

Noch ist nicht alles gespeichert, und das Fenster sagt, was (ein Feld mit eingetipptem, aber nicht bestätigtem Text, eine
Änderung, die noch gespeichert wird, Im Spiel testen, das noch baut...). **Nein** lässt das Studio offen; **Ja** schließt
es, und das geht verloren.

## Das Spiel startet, aber ohne meine Änderungen

1. Wurde es über **Spielen** (Launcher) oder **Im Spiel testen** (Studio) gestartet? Über Steam startet das Spiel ohne
   Mods.
2. Kartenänderungen erscheinen nur auf dieser Karte: klicke im Hauptmenü auf **KÄMPFE** und wähle sie (die Meldung des
   Studios nach Im Spiel testen sagt, welche Schaltfläche und welche Karte).
3. Ist der Mod im Set, und ändert ein Mod weiter unten in der Reihenfolge dasselbe?

## Das Spiel stürzt ab

Schreib auf, was du kurz davor getan hast (welche Karte, welcher Befehl, was auf dem Bildschirm war), mach einen
Screenshot und [[melde es|Einen-Fehler-melden]]. Absturzberichte zu bearbeiteten Karten haben die Kartenwerkzeuge stabil
gemacht.

## Etwas anderes

[[Eine Frage stellen|Eine-Frage-stellen]].

---

[[Feldhandbuch|Feldhandbuch]] · [[English|When-Something-Goes-Wrong]]
