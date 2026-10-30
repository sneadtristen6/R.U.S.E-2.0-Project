# Einheiten aus anderen Epochen

> **Für:** Modder · **Du brauchst:** RUSE Studio 0.9.8.2 oder neuer und einen Mod · **Dauer:** ein oder zwei Minuten pro Einheit

366 Einheiten vom Ersten Weltkrieg bis heute stehen im Reiter **Einheiten** neben denen des Spiels: Panzer und Flugzeuge
aus dem Ersten Weltkrieg, dem Zweiten Weltkrieg+, dem Kalten Krieg und der Moderne, alle in einem Spiel. Jede ist das
kostenlose 3D-Modell eines anderen Erstellers (CC BY), schon an das Spiel angepasst, mit den Hoheitszeichen ihrer
Nation versehen und mit Nennung des Erstellers. Keine davon ist in deinem Mod, bis du sie hinzufügst.

## Die Einheiten einer Epoche holen

1. Wähle im Reiter **Einheiten** über den Arten eine Epoche: **Erster Weltkrieg**, **Zweiter Weltkrieg+**, **Kalter
   Krieg** oder **Moderne** (**Vanilla** sind die eigenen Einheiten des Spiels, die Liste wie immer).
2. Beim ersten Mal sagt das Studio, wie viele Einheiten die Epoche hat und wie groß sie ist, mit **Die Einheiten des
   Ersten Weltkriegs herunterladen** (oder denen dieser Epoche). Es lädt sie vom GitHub des Projekts herunter, prüft
   jede Datei, bevor sie genutzt wird, und listet sie auf.

   | Epoche | Einheiten | Download |
   |---|---|---|
   | Erster Weltkrieg | 61 | 232 MB |
   | Zweiter Weltkrieg+ | 32 | 198 MB |
   | Kalter Krieg | 149 | 996 MB |
   | Moderne | 124 | 709 MB |

3. Eine heruntergeladene Epoche aktualisiert sich selbst, wenn neuere Einheiten hochgeladen werden: das Studio sagt es
   und holt sie.

Die Einheiten der Epoche werden wie die des Spiels gefiltert: Art (Boden oder Luft), Nation (auch China), Typ und das
Suchfeld.

## Eine zu deinem Mod hinzufügen

1. Klicke auf eine Einheit. Ihre Seite zeigt das Bild ihres Modells und seinen Ersteller: **Modell von** dem Ersteller,
   die Lizenz und einen Link dorthin, wo er es geteilt hat.
2. Füll das Formular aus:
   - **Name der neuen Einheit** (in jeder Sprache angezeigt).
   - **Ausgehend von**: die Einheit des Spiels, mit deren Werten sie beginnt (Geschwindigkeit, Panzerung, Waffen, wie
     sie spielt). Die vorgeschlagene steht zuerst; jede Einheit ihrer Art lässt sich wählen.
   - **Preis** (jedes Schlachtdatum).
   - **Größe**: 1 ist so lang wie die Ausgangseinheit. Der Vorschlag ist ihre echte Größe (ihre echte Breite, die
     Spannweite eines Flugzeugs, im eigenen Maßstab des Spiels); alles von 0,05 bis 20. Zieh den Schieberegler, oder
     klicke auf einen seiner benannten Punkte: **Winzig**, **Spielgröße** (1: so lang wie die Ausgangseinheit, so groß,
     wie das Spiel diese Art Einheit zeichnet), **Echte Größe** und **Riesig**. Moderne Flugzeuge in echter Größe sind
     viel größer als die Flugzeuge des Zweiten Weltkriegs im Spiel (eine J-16 ist so lang wie eine Lancaster).
   - **Baumenü**: die Nation und die Fabrik, in der sie gekauft wird.
   - **Erforscht aus**: die Einheit, von der aus sie erforscht wird, oder **Keine: von Anfang an kaufbar**, mit ihrem
     **Forschungspreis** und ihrer **Forschungszeit** (tipp die Zeit in Sekunden oder Minuten ein: die Auswahl daneben).
3. Klicke auf **Zu meiner Mod hinzufügen**. Jetzt ist sie eine neue Einheit deines Mods: **Ihre Seite öffnen**, um jeden
   ihrer Werte, ihr Modell oder ihre Karte zu ändern, wie bei jeder Einheit. **Aus meinem Mod nehmen** löscht sie
   wieder.

## Ihre Größe später ändern

Auf der Seite der Einheit hat **Eigenes Modell** denselben Schieberegler: wähle eine Größe und klicke auf **Größe
ändern** (das Modell wird aus seiner eigenen Datei neu angepasst, nichts zu wählen). **Alle Flugzeuge meines Mods** (oder
Bodeneinheiten) macht alle auf einmal: **Spielgröße**, **Echte Größe**, **Kleiner** (ein Fünftel) oder **Größer** (ein
Viertel). Das Spiel liest das Modell einer Einheit beim Laden, daher kann sich eine Größe nicht ändern, während du
spielst: die neue Größe zeigt sich ab dem nächsten Build (Im Spiel testen).

## Forschungsketten

Eine Einheit kann von jeder Einheit des Baumenüs ihrer Nation aus erforscht werden, auch von den eigenen
Epocheneinheiten deines Mods: füge einen Panzer aus dem Kalten Krieg hinzu, dann einen modernen, der von ihm aus
erforscht wird. Einheiten aus dem Ersten Weltkrieg und dem Zweiten Weltkrieg+ lassen sich sofort kaufen; die aus dem
Kalten Krieg und der Moderne beginnen als von einer passenden Einheit aus erforscht (das Formular sagt, welche es
vorschlägt, und warum).

Nimmst du eine Einheit heraus, von der aus andere erforscht werden, entscheidet **Einstellungen > Forschung**, was
passiert:

- **Mich zuerst warnen** (der Standard): das Studio listet die Einheiten, die von ihr aus erforscht werden, mit
  **Trotzdem herausnehmen**.
- **Ablehnen**: die Einheit bleibt, und die Meldung sagt, wie du zuerst die anderen änderst.
- **Neu verknüpfen**: jede wird stattdessen von der eigenen Vorgängerin der entfernten Einheit aus erforscht, zu ihrem
  eigenen Preis und ihrer eigenen Zeit (oder wird von Anfang an kaufbar).

Eine Einheit, die noch von einer erforscht wird, die es nicht mehr gibt, sagt das in ihrem Feld **Verbesserung und
Forschung** und in der Prüfleiste, und der Build stoppt an ihr, bis du eine andere Einheit wählst, oder keine.

## Nennung der Ersteller

Der Ersteller jeder Epocheneinheit wird genannt: auf ihrer Seite und in der `CREDITS-era-units.md` deines Mods, die das
Studio schreibt, wenn du eine hinzufügst. Behalte diese Datei bei deinem Mod: die Lizenz der Modelle verlangt es. Die
vollständige Liste der Ersteller steht beim
[Release der Epocheneinheiten](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/tag/era-units).

## Was im Spiel gesehen wurde

Gesehen: sie laden sofort, mit ihren eigenen Karten in den Baumenüs; die Forschungsreiter und eine Kette von
Verbesserungen; ihre eigenen Modelle; ihre Größen. Noch nicht ausprobiert: gezogene
Geschütze (der Importer kann sie noch nicht anpassen, daher zeigen sie das Modell der Ausgangseinheit), und ob das Spiel
die Forschungszeit in Sekunden zählt.

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Units-From-Other-Eras]]
