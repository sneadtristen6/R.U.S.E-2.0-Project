# Mod-Ordner und -Dateien

> **Nachschlagen** · Diese Dateien musst du nie von Hand anfassen: das Studio schreibt sie. Diese Seite ist für den Fall,
> dass etwas falsch aussieht, oder für Modder, die Dateien direkt bearbeiten.

## Wo die Dinge liegen

| Was | Wo |
|---|---|
| Die Mods des Studios | `Documents\RUSE 2.0\Mods\<mod>` (im Explorer „Dokumente“); Kartenänderungen in `Maps`, exportierte Dateien in `Exports`, Sicherungen in `Backups`. Im Studio öffnet **Einstellungen → Wo Ihre Dateien liegen** jeden davon, und **Ordner dieses Mods zeigen** (Mod-Menü) den, den du bearbeitest |
| Die installierten Mods des Launchers | `%LOCALAPPDATA%\RUSE Mod Platform\library` |
| Gemoddete Kopien des Spiels | Der Ordner, den du in den Einstellungen wählst (**Wohin Kopien mit Mods kommen**, in beiden Apps); der empfohlene Ort ist `RUSE-Instances` auf demselben Laufwerk wie das Spiel (zum Beispiel `D:\RUSE-Instances`), wo eine Kopie die Dateien des Spiels mitbenutzt. Auf einem anderen Laufwerk ist jede Kopie eine vollständige Kopie des Spiels: langsamer und größer. Die saubere Sicherung des Spiels (`RUSE-Backup`) kommt daneben. |
| Das Spiel selbst | Wird nie verändert |

Ältere Studios legten sie in `%LOCALAPPDATA%\RUSE Mod Platform` ab (`mods`, `maps`, `exports`, `mod-backups`): Das Studio verschiebt sie beim ersten Start nach Dokumente und sagt es dir.

## In einem Mod

```
my-mod/
  mod.toml                    the mod's name, id, version, author (required)
  src/studio.rndf             unit changes made in the Studio
  text/studio.baseunite.csv   names of new units
  files/replace/gen/...png    a unit's paint (from Blender) or a unit's card, under the game texture it changes
  files/cards/<unit>.png      a new unit's own card in the build menu, named after the new unit
  files/models/<unit>.glb     a new unit's own 3D model (Import model), named after the new unit
  maps/<map pack name>/       one folder per map the mod changes:
    terrain.toml                ground brushes (also water, cover and block brushes)
    scenery.toml                buildings, props and trees placed
    scenario.toml               starting points and spawns moved, units added
    cover.toml, movement.toml   cover and movement written by hand
    map.toml                    how many players; or, for a new map, the map it copies and its name
```

## Der Name des Kartenordners ist der Paketname der Karte, nicht ihr Titel

Spieler kennen eine Karte unter ihrem Titel (**Blitz**); die Dateien des Spiels nutzen ihren Paketnamen
(**SuperCrossRoads4**). Ein Kartenordner muss den Paketnamen nutzen: `maps/SuperCrossRoads4/`, nicht `maps/Blitz/`. Das
Paar jeder Karte steht in [[Kartennamen|Kartennamen]], und die Kartenliste des Studios zeigt beide: zuerst den Titel, nach
dem Punkt den Paketnamen.

## Eine neue Karte

Ein Mod kann KÄMPFE eine eigene Karte hinzufügen: eine Kopie einer mitgelieferten Karte oder einen leeren Anfang, unter einem eigenen Namen, die die anderen
Dateien des Mods dann umformen. Ihr Ordnername ist der Paketname der neuen Karte (Buchstaben, Ziffern und `_`), und ihre
`map.toml` sagt, welche Karte sie kopiert und wie die Menüs sie nennen:

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from (its pack name: Blitz)

[name]
us = "Blitz Twin"              # English, used where a language is left out
fr = "Blitz jumeau"
```

`maps/BlitzTwin/terrain.toml` und der Rest bearbeiten dann die Kopie, und Blitz bleibt, wie es war. Jede Karte, die
KÄMPFE listet, lässt sich kopieren; Karten von Kampagne und Operationen nicht. Zwei Spieler brauchen denselben Mod, um
sie zusammen zu spielen, wie bei jedem Mod. Neue Karten laufen im Spiel (2026-10-03), und **Karte duplizieren** im
Studio legt diesen Ordner für dich an.

## Häufige Fehler

| Fehler | Was passiert | Lösung |
|---|---|---|
| Die Zip-Datei enthält einen Ordner in einem Ordner | Der Launcher schaut einen Ordner tiefer und findet ihn. Bei zwei oder mehr Ebenen sagt er, dass er keinen Mod gefunden hat. | Zippe den Ordner, der `mod.toml` enthält. |
| Ein Kartenordner, benannt nach dem Titel der Karte | Der Build sagt, dass das kein Paketname einer Karte ist. | Benenne ihn in den Paketnamen um. |
| Eine von Hand bearbeitete Datei hat einen Tippfehler | Die Mod-Prüfung nennt die Datei und die Zeile. | Korrigiere ihn, oder **Beiseitelegen** im Studio. |
| Eine `.exe`, `.dll` oder ein PC-Skript im Mod | Abgelehnt: Mods enthalten nur Daten (die eigenen Missionsskripte des Spiels, so wie das Studio sie speichert, sind die einzige Ausnahme). | Nimm es heraus. |

Kann eine Datei nicht gelesen werden, schreibt das Studio nie darüber: deine Arbeit geht nie verloren. **Beiseitelegen**
benennt sie in `<name>.broken.toml` neben dem Original um.

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Mod-Folders-and-Files]]
