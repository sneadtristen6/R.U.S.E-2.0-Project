# In Blender öffnen

> **Du brauchst:** RUSE Studio 0.9.8.20 oder neuer, einen Mod und Blender (kostenlos) · **Dauer:** 5 Minuten zum Lesen

**In Blender öffnen** bringt eine Einheit nach Blender, ins kostenlose 3D-Programm, um ihre Form, ihre Knochen oder
ihre Bemalung zu ändern; **Meine Änderungen zurückholen** bringt, was du dort getan hast, in deinen Mod. Es ist ein
einziger Knopf für die ganze Einheit: **Was nach Blender geht** daneben sagt, was mitgeht, und alles, was du abhakst,
bleibt, wie es ist. Diese Seite geht es Schritt für Schritt durch.

Animationen werden nicht mit diesem Knopf geändert, sondern in RUSE Decoy (siehe
[[Animationen der Einheiten|Animationen-der-Einheiten]]). Die eigenen Animationen eines Modells gehen mit ihm nach
Blender und kommen mit ihm zurück.

## Wo der Knopf ist

| Die Einheit | Wo | Was zurückkommt |
|---|---|---|
| Ein Trupp, den du gemacht hast (eine neue Einheit deines Mods) | Das große **In Blender öffnen** auf seiner Karte, oben auf seiner Seite | Seine Soldaten, jeder für sich; ihre Bemalung |
| Jede andere Einheit, die du gemacht hast (ein Panzer, ein Flugzeug) | **Aussehen und Bewegung**, die Zeile **Modell**, **Mehr**: das Feld **In Blender ändern** | Ihr ganzes Modell (auch ihre Knochen, wenn es eigene sind), ihre Bemalung |
| Eine Einheit des Spiels (kein Trupp) | Dasselbe Feld | Nur ihre Bemalung: Male darauf, der Rest bleibt der des Spiels |
| Ein Trupp des Spiels | Seine Karte sagt, du sollst zuerst eine neue Einheit aus ihm machen: **Neue Einheit aus dieser…** | Nur seine **Eigene Uniform**, bemalt über seine Zeile **Uniform** (**In Blender öffnen**, dann **Zurückholen**) |

Kein Blender auf diesem PC? Die Seite zeigt **Blender holen (kostenlos)**, das Blenders Download-Seite öffnet, und
**Blender auswählen…**, um dem Studio zu zeigen, wo `blender.exe` ist, wenn du es schon hast.

## Was nach Blender geht

Klicke neben dem Knopf auf **Was nach Blender geht ▾**. Zu Beginn ist alles angehakt. Hake einen Teil ab, um ihn zu
behalten, wie er ist: **Meine Änderungen zurückholen** lässt ihn dann, wie er war, was auch immer Blender mit ihm tat.

| Du siehst | Das heißt |
|---|---|
| **Seine Soldaten**, dann jeden Soldaten („Schütze 1“, „Bazooka-Schütze 5“...) | Die angehakten Soldaten öffnen sich nebeneinander in einem Blender. Ändere, welchen du willst: Nur der, den du änderst, ändert sich. |
| **Welches Modell:** **Das Modell der Schützen** oder **Das Modell des Soldaten mit schwerer Waffe** | Ein Trupp mit eigenen Knochen (der Generische Reitertrupp): ein Modell auf einmal, mit seinen Knochen und Animationen. |
| **Sein Modell** | Die Form der Einheit (eine Einheit, die kein Trupp ist). |
| **Seine Knochen** | Ihre Knochen (nur ein Modell mit eigenen Knochen). Abgehakt werden die Knochen deines Mods wieder so eingesetzt, wie sie waren. |
| **Seine Bemalung** | Ihre Bilder. Abgehakt werden die Bilder deines Mods wieder so eingesetzt, wie sie waren. |

Gut zu wissen:

- **Nur ihre Bemalung** (ihr Modell oder jeder Soldat abgehakt): Blender öffnet sich mit den Bildern zum Bemalen, und
  nur die Bemalung kommt zurück. So wird die **Eigene Uniform** eines Trupps bemalt, für alle Soldaten zugleich. Ein
  Trupp in der Standarduniform kann das nicht: „Wähle zuerst Eigene Uniform“ (die Standarduniform tragen auch andere
  Trupps und Besatzungen). Wähle zuerst **Eigene Uniform** in seiner Zeile **Uniform** unter **Aussehen und Bewegung**.
- **Seine Knochen** abgehakt, aber in Blender wurde ein Knochen hinzugefügt, entfernt oder umbenannt: Die Knochen können
  nicht behalten werden, also kommen sie so zurück, wie Blender sie gesendet hat, und das Studio sagt es.
- Ein Trupp aus Soldaten des Spiels hat kein **Seine Knochen**: Seine Soldaten kommen auf den Knochen des Spielsoldaten
  zurück, was auch immer Blender mit ihnen tat.
- Nichts angehakt: Das Studio sagt „Kreuze zuerst an, was nach Blender geht: das Modell, seine Knochen oder seine
  Bemalung.“

## Hin und zurück, Schritt für Schritt

1. **Öffne es.** Klicke auf **In Blender öffnen**. Blender öffnet sich (das dauert ein paar Sekunden), mit dem, was du
   angehakt hast.
2. **Ändere es.** Male, ändere die Form, setze ein eigenes Modell auf die Knochen eines Soldaten (siehe
   [[Modelle und Knochen|Modelle-und-Knochen]], „Gewichte“). Das Wenige, was du wissen musst, steht oben in Blenders
   3D-Ansicht.
3. **Sende es.** Klicke oben links in Blenders 3D-Ansicht auf **An das R.U.S.E. Studio senden**.
4. **Hol es zurück.** Im Studio heißt der Knopf jetzt **Meine Änderungen zurückholen**: Klicke darauf. Die Seite sagt,
   was hereinkam: bei einem Trupp, wer sich geändert hat und wer nicht, bei jeder anderen Einheit die Datei des Modells,
   und was abgehakt behalten wurde.
5. **Im Spiel testen** zeigt es.

Du kannst Blender offen lassen und noch eine Runde drehen: ändern, senden, zurückholen.

## Meine Änderungen zurückholen

- **Blender noch offen?** **Meine Änderungen zurückholen** bittet es zuerst zu senden und wartet darauf (bis zu einer
  Minute).
- **Du schließt Blender?** Klicke vorher auf **An das R.U.S.E. Studio senden**: Was du nicht gesendet hast, bleibt in
  Blender, und das Studio sieht es nie.
- **Nach dem Senden geschlossen?** Der Knopf heißt **Meine Änderungen zurückholen**, bis du darauf klickst, und er nimmt,
  was du zuletzt gesendet hast. Auf der Karte eines Trupps erscheint eine Sendung nach deinem letzten Zurückholen (oder
  nach **Einen Soldaten hinzufügen**) als kleines **Meine Änderungen zurückholen** unter dem großen Knopf, sobald
  Blender zu ist: Es nimmt, was du zuletzt gesendet hast.
- **Noch nichts gesendet:** „Aus Blender ist noch nichts zurückgekommen: klicke in Blender oben auf An das R.U.S.E.
  Studio senden, dann hier auf Meine Änderungen zurückholen.“
- Ein Blender auf einmal pro Einheit: Solange Blender sie hat, heißt der Knopf des Studios **Meine Änderungen
  zurückholen**.

## Eine beiseitegelegte Sendung

Eine **Sendung** ist, was Blender mit **An das R.U.S.E. Studio senden** geschickt hat. Öffnest du Blender wieder, bevor
die letzte Sendung zurückgeholt ist:

- **Ein Trupp:** Diese Sendung wird im Blender-Ordner deines Mods beiseitegelegt, in einem Ordner namens
  `sent-not-brought-` mit Datum und Uhrzeit, und das neue Blender beginnt mit dem, was dein Mod hat. Nichts geht
  verloren, aber die Karte sagt es noch nicht, und sie hat keinen Knopf, um sie zurückzuholen: Die Dateien liegen in
  `Documents\RUSE 2.0\Mods\<dein Mod>\blender\<Name der Einheit>\squad\`.
- **Jede andere Einheit, ihr Modell angehakt:** Nichts wird beiseitegelegt: Das nächste **In Blender öffnen** beginnt
  mit dem, was du zuletzt gesendet hast.
- **Die Animationen in RUSE Decoy:** Jede beiseitegelegte Sendung steht über den Animationen der Einheit („Aus Blender
  gesendet, nie zurückgeholt, am ... beiseitegelegt“), mit **Beiseitegelegte Sendung zurückholen**, um sie zu
  übernehmen, oder **In den Papierkorb legen**.

## Wo deine Blender-Dateien sind

Im Ordner deines Mods, `Documents\RUSE 2.0\Mods\<dein Mod>\blender\<Name der Einheit>\`: die des Trupps in `squad`, die
von RUSE Decoy in `animations`. Sie kommen nicht in deinen Mod, wenn du ihn exportierst. Auf der Seite eines Trupps
sagt **Weitere Optionen**, wo sie sind, mit **Im Ordner zeigen**.

## Was schiefgehen kann

| Was passiert | Warum, und was tun |
|---|---|
| Blender öffnet sich leer | Sieh im Fenster von Blender nach einem Fehler (**Window > Toggle System Console**) und sag es uns auf dem Discord. |
| Ein Soldat, den ich nicht angefasst habe, gilt als geändert | Alles, was abweicht, zählt als geändert, auch ein umbenanntes Objekt. Sein Aussehen bleibt, wie es war. |
| „Auf keinem Soldaten, also nicht gesendet: ...“ | Etwas, das du nach Blender gebracht hast, sitzt weder auf den Knochen eines Soldaten noch in seiner Collection: Setze es auf ihn und sende erneut. |
| Ein Punkt meines Modells bewegt sich nur mit der Hüfte | Er hat keinen Knochen: siehe [[Modelle und Knochen|Modelle-und-Knochen]], „Punkte ohne Knochen“. |
| Teile haben ihren Glanz oder ihre Seitenfarbe verloren | Die Seite nennt sie: Ein in Blender umbenanntes oder neues Material kommt schlicht zurück. Behalte die Materialnamen, mit denen Blender sich geöffnet hat. |
| Die neue Form meiner Spieleinheit kam nicht zurück | Bei einer Einheit des Spiels kommt nur die Bemalung zurück. Mache eine neue Einheit aus ihr, um ihre Form zu ändern. |

## Was im Spiel ausprobiert wurde

- Bemalung aus Blender auf einer Einheit, aus der Nähe und von weitem gesehen.
- Ein Trupp, in Blender geöffnet, ein Soldat geändert und für sich allein zurückgeholt (November 2026).
- Im Spiel noch nicht ausprobiert: das ganze Modell eines Panzers durch Blender, und was **Was nach Blender geht**
  behält (mit Blender und dem Studio ausprobiert, außerhalb des Spiels).

Kommst du nicht weiter? Frag auf dem [Discord](https://discord.gg/h54t5baNsC) oder sieh unter
[[Wenn etwas schiefgeht|Wenn-etwas-schiefgeht]] nach.

**Weiter:** [[Einen Trupp ändern|Einen-Trupp-ändern]] · [[Modelle und Knochen|Modelle-und-Knochen]] ·
[[Animationen der Einheiten|Animationen-der-Einheiten]]

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Open-in-Blender]]
