# Exportieren und teilen

> **Für:** Modder · **Du brauchst:** RUSE Studio und einen fertigen Mod · **Dauer:** 5 Minuten

## 1. Exportieren

1. Öffne das Menü **Mod** und wähle **Mod exportieren…**.
2. Trag die **Version** ein (drei Zahlen, wie `1.0.0`), deinen Namen und eine Zeile darüber, was der Mod tut.
3. Wähle, wo gespeichert wird. Das Studio baut den Mod einmal auf deinem Spiel, um die Spielversion festzuhalten, auf der
   er gemacht wurde, und seinen **Fingerabdruck** (ein kurzer Code, der für alle mit denselben Mods gleich ist), und
   speichert dann eine Datei:
   `<your-mod>-<version>.rusemod`.

Diese Datei ist alles, was ein Spieler braucht: er fügt sie im RUSE Launcher hinzu ([[Installieren und spielen|Installieren-und-spielen]]).

**Große Karten-Mods:** bei einer überall geänderten Karte kann der Build Minuten zum Ausrechnen brauchen (zum Beispiel,
wohin Einheiten auf Gelände fahren können, das du geöffnet hast). Darauf wartest du einmal. Der Export legt das, was der
Build ausgerechnet hat, in die Datei, sodass der erste Build eines Spielers kürzer ist. Sie enthält nur unsere eigenen
Zahlen, nie eine Datei des Spiels, und sie ist mit der eigenen Datei des Spiels für diese Karte verschlossen: sie öffnet
sich nur auf einem PC, der das Spiel hat. Bisher nur die Bewegung; im Spiel noch nicht gesehen.

Ist der Export fertig, öffnet das Studio **Teilen Sie Ihren Mod** mit der Größe der Datei, ihrer SHA-256-Prüfsumme und
ihrem Eintrag für die Liste, bereit zum Kopieren. Du kannst es jederzeit wieder über das Menü **Mod** öffnen (**Mod
teilen…**).

## 2. Teilen: zu den unterstützten Mods hinzufügen

Einen Mod gemacht? Füg ihn der Liste hinzu und werde Mitwirkender. Der Reiter **Unterstützte Mods** im RUSE Launcher
zeigt die Mods der Liste unter [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods), und Spieler
installieren sie mit einem Klick (neuen Spielern werden sie beim ersten Start des Launchers angeboten):

1. Lade die `.rusemod` hoch (ein GitHub-Release ist am einfachsten: das deines eigenen Repositorys oder das der Liste).
2. Öffne einen Pull Request an [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods), der den Eintrag
   deines Mods zu `index.toml` hinzufügt: füge den Eintrag ein, den Teilen Sie Ihren Mod zeigt, und setz den Link der
   Datei in `download`. Größe und SHA-256 müssen die sein, die der Export gezeigt hat: der Launcher lehnt einen Download
   ab, der nicht passt, damit niemand deine Datei gegen eine andere austauschen kann.
3. Oder poste ihn in [Discussions > Mods & maps](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) mit
   einem Screenshot und dem, was er ändert (zieh die `.rusemod` in den Beitrag), und er wird für dich in die Liste
   aufgenommen.

Ein Cheat oder ein Testwerkzeug (kostenlose Einheiten, sofortiges Bauen...) bekommt den Tag `"cheat"`: der Launcher
zeigt ihn in einer eigenen Gruppe, „Cheats und Testwerkzeuge (optional)“, und hakt ihn nie an oder lädt ihn herunter,
außer der Spieler tut es. Eine neue Version ist eine neue Datei mit einer neuen Versionsnummer: eine veröffentlichte
Datei ändert sich nie.

Das genaue Format des Eintrags:
[MOD_FORMAT.md, Abschnitt 15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/docs/MOD_FORMAT.md#15-the-mod-index-supported-mods).

## Einen installierten Mod bearbeiten

Im Mod-Menü des Studios listet **Installierten Mod bearbeiten…** jeden Mod, den der Launcher hat (mit einem Suchfeld).
Dein eigener öffnet sein Projekt. Der Mod eines anderen wird zu einer Kopie, die dir gehört, mit einem eigenen Namen (er
kann nicht den Namen des Originals tragen): deine Änderungen kommen dort hinein, und ein Update des Originals löscht sie
nie. Ein Mod des RUSE Mod Manager (`.rmod`) wird in seiner Kopie umgewandelt, sodass seine Wertänderungen zu
Studio-Änderungen werden, die du ändern kannst.

## Was ein Mod enthalten kann

Nur Daten: Zahlen, Texte, Karten, Modelle, Texturen. Programme (`.exe`, `.dll`, Skripte, die auf einem PC laufen) lehnen
beide Apps ab. Eine Ausnahme: die eigenen Missionsskripte des Spiels, so wie das Studio sie speichert. Sie laufen im
Spiel und können alles, was es kann, also installiere sie nur von Autoren, denen du vertraust ([SECURITY.md](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/SECURITY.md)).

## Gute Gewohnheiten

- Behalte deinen Mod-Ordner: die `.rusemod` ist für Spieler, der Ordner ist das, was das Studio bearbeitet.
- Sag in deinem Beitrag, welche anderen Mods deiner braucht oder mit welchen er sich nicht verträgt.
- Nenne die Leute, auf deren Arbeit du aufbaust.

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Export-and-Share]]
