# Musik und Klänge

> **Für:** Modder · **Du brauchst:** RUSE Studio 0.9.8.8 oder neuer, einen Mod; für ein eigenes Geräusch eine Tondatei
> (WAV, MP3, OGG oder FLAC), für eigene Bewegungen eine Motion-Capture-Datei (.bvh) · **Dauer:** jeweils ein paar Minuten

Alles hier geschieht im Studio, im Reiter **RUSE Decoy**, dem Sound- und Animationsdesigner (er hat in Studio 0.9.8.8 den
Platz des Reiters Musik eingenommen). Kein anderes Programm muss installiert werden.

## Jedes Geräusch des Spiels

**RUSE Decoy** listet links jedes Geräusch des Spiels nach Art: Waffen nah und fern, Einschläge und Zerstörung, Motoren
und Schritte, Umgebung, Kartenhintergründe, die Oberfläche, Finten-Karten, Einheitenstimmen, Hauptquartier und
Aufklärung, Funkverkehr, Missionsdialoge (mit dem, was jede Zeile sagt), Musik und Signale. Das Suchfeld findet ein
Geräusch nach seinem Namen oder nach den Worten, die darin gesprochen werden.

Für jedes Geräusch:

- **Abspielen** spielt es vor.
- **Lautstärke:** zieh sie. 100 % ist die des Spiels, bis 200 %.
- **Ersetzen…** öffnet den Editor unten, um ein eigenes Geräusch an seine Stelle zu setzen.

Änderungen werden in deinem Mod gespeichert und kommen ins Spiel, wenn du ihn testest oder exportierst.

## Ein Geräusch oder ein Stück ersetzen

1. Leg eine Tondatei auf den Editor oder wähl eine aus. Deine darf beliebig lang sein: das Studio bringt sie ins Format
   des Spiels.
2. Schneide sie mit den beiden Griffen zu, setz **Einblenden** und **Ausblenden**, stell die **Lautstärke** ein und hör
   sie dir an.
3. **Übernehmen** speichert sie in deinem Mod. Später öffnet **Ändern…** sie wieder, und **Entfernen** bringt das
   Geräusch des Spiels zurück.

## Ein Stück hinzufügen

Unter **Musik und Signale** sind die Stücke danach aufgelistet, wo sie laufen: das Hauptmenü, der Abspann, die drei
Listen, aus denen in Kämpfen gespielt wird, das Ende einer Partie, Missionsziele, und die Kampagnenkapitel und
Operationen, die sie nennen. Die drei Kampflisten: eine ruhige, während die Spieler aufbauen, eine für den Kampf, sobald
Schüsse einschlagen, und Listmusik, wenn eine Täuschungskarte gespielt wird.

Unter jeder Kampfliste **Stück hinzufügen…**: gib ihm einen Namen, leg eine Tondatei ab, schneide sie zu, dann
**Übernehmen**. Es kommt zu den Stücken, die das Spiel aus dieser Liste spielt, markiert mit Neu.

## Animationen

Unter **Animationen**: wie Einheiten sich bewegen, vom Laufen, Feuern und Nachladen bis zum Sterben und einer
Geschützbedienung bei der Arbeit. Jede sagt, wie das Spiel sie nennt und wie viele Einheiten sie spielen. **Ansehen und
ändern…** zeigt sie in 3D an einer Einheit, die sie spielt (ziehen dreht sie, das Rad zoomt; die 3D-Ansicht braucht
einmal Internet):

- **Tempo:** 100 % ist das des Spiels, 200 % doppelt so schnell, 50 % halb so schnell.
- **Stattdessen verwenden:** eine andere Animation desselben Körpers an ihrer Stelle (Schützen könnten zum Beispiel so
  laufen, wie sie fliehen).
- **Ein Knochen**, mit **Größe** und **Drehen um** / **Drehung**: ein Teil des Körpers größer gemacht oder gedreht, die
  ganze Animation hindurch (was daran hängt, wächst mit).
- **Zurück zum Spiel-Original** nimmt jede Änderung daran heraus.

## Motion Capture

Leg die Bewegung eines echten Menschen auf eine Animation, unter **Motion Capture**: wähl eine Bewegung aus der
Bewegungsbibliothek (3.205 freie Bewegungen aus der CMU-Motion-Capture-Datenbank und 100STYLE, jede beim Auswählen
heruntergeladen), oder nimm mit **Motion-Capture-Datei wählen…** deine eigene (.bvh, aus Mixamo, Blender oder einem
anderen Motion-Capture-Programm).

1. Wähl den Teil davon, den du nutzen willst: **Ab** (in Sekunden) und **Wie lang**. Für Gehen oder Laufen einen ganzen
   Schritt mit jedem Fuß; für einen Tod kurz vor dem Fallen beginnen.
2. **Auf der Stelle halten** hält Gehen und Laufen dort, wo das Spiel die Einheit hinbewegt; **Als Schleife** glättet
   die letzte Haltung in die erste, für eine Animation, die das Spiel immer wieder abspielt.
3. **Nennung (wer die Bewegung gemacht hat):** bei den Bewegungen der Bibliothek schon ausgefüllt; bei jeder anderen
   Datei schreib, wer sie gemacht hat, und ihre Lizenz. Die Nennung geht überall mit, wohin dein Mod geht.
4. **Ansehen**, dann **Übernehmen**. Tempo- und Knochenänderungen gelten weiterhin obendrauf; **Zurück zum
   Spiel-Original** nimmt sie heraus.

## Die Geräusche und Animationen einer Einheit

Die Seite einer Einheit hat einen Abschnitt **Geräusche und Animation**: ihre eigenen Sprachzeilen und Motorgeräusche,
und ihre Animationen. **Geräusche in RUSE Decoy ändern** öffnet RUSE Decoy mit den eigenen dieser Einheit. Eine Einheit
spricht die Zeilen ihrer Nation und Art, also hört man eine dort geänderte Zeile von jeder Einheit, die sie teilt. Ihre
Schüsse und Treffer stehen unter den Arten Waffen und Einschläge.

## Der Hintergrundklang einer Karte

Im Reiter **Karten** zeigt **Hintergrundklang…** den der Karte: womit er beginnt, und seine drei Schichten, jede im
selben Editor angehört und ersetzt. Eine Karte kann auch mit dem Hintergrund beginnen, den eine andere Karte spielt.

## Was im Spiel gesehen wurde

Im Spiel gesehen: die Geräusche und Animationen von RUSE Decoy (Studio 0.9.8.8), das Stück des Hauptmenüs, die Stücke
der Kampflisten 1 und 2, neue Stücke darin, und die Sprachzeilen einer Einheit. Noch nicht ausprobiert: der
Hintergrundklang einer Karte und die Liste mit der Listmusik (aus der Funktionsweise des Spiels bekannt). Die
Fehlermeldungen von RUSE Decoy sind vorerst nur auf Englisch.

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Music-and-Sounds]]
