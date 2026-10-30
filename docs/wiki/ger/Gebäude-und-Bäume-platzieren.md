# Gebäude und Bäume platzieren

> **Für:** Modder · **Du brauchst:** RUSE Studio 0.7.2 und einen Mod (Raster, Rechteck, Pfad, Auswählen und
> Wiederholen: 0.9.8.7; eigene Modelle: 0.9.8.8) · **Im Spiel bestätigt:** platzierte Gebäude sind auf jeder Zoomstufe
> zu sehen, bis zum 8-Fachen ihrer Größe, und Einheiten fahren um sie herum. Noch nicht im Spiel ausprobiert: was mit
> Raster, Rechteck und Pfad platziert wurde, und verschobene Objekte

## Platzieren

1. Klick in der Leiste auf **Gebäude**, oder auf **Objekte & Bäume** und dann auf seinen Reiter **Objekte** oder **Bäume**.
2. Wähl einen Typ aus den Bildern (tipp etwas ins Suchfeld, um sie einzugrenzen). Jedes Bild ist aus dem eigenen Modell des
   Spiels gezeichnet, und die Zahl in seiner Ecke sagt, wie viele die Karte schon hat. Die Liste enthält die eigenen Typen dieser
   Karte: das Spiel nimmt nur einen Typ an, den eine Karte schon benutzt.
3. Wähl, wie ein Klick platziert:
   - **Einzeln**: ein Objekt, wo du klickst;
   - **Fläche**: ziehen, um Objekte in einem Kreis zu verteilen (**Abstand** hält sie auseinander, **Fläche** legt den Kreis fest);
   - **Linie**: klick auf den Anfang, dann auf das Ende, für eine Reihe (eine Hecke, eine Häuserzeile, eine Baumreihe), entlang
     der Linie gedreht;
   - **Raster**: Reihen von Objekten: klick, wo die erste Reihe beginnt und wo sie endet, dann zieh die Reihen mit dem
     Zeiger auf und klick (**Reihenabstand** legt den Abstand zwischen ihnen fest);
   - **Rechteck**: zieh ein Rechteck auf dem Boden auf und lass los: es füllt sich in Reihen mit dem gewählten Objekt;
   - **Pfad**: klick entlang des Wegs, dann Doppelklick, **Enter** drücken oder **Fertig**: die Objekte folgen einer
     weichen Kurve durch deine Klicks (eine Hecke, eine Baumreihe); mit einer Breite ein ganzer Gürtel davon. **Esc**
     verwirft ein halb fertiges Raster, eine halb fertige Linie oder einen halb fertigen Pfad.
4. **Zur Straße ausrichten:** nahe einer Straße kommt ein Objekt neben sie und dreht sich zu ihr hin, und eine Reihe folgt
   ihr; ein Raster oder ein Rechteck lässt die Straßen frei. Der Drehregler dreht es trotzdem (versuch 180°, wenn ein Haus
   seine Rückseite zeigt).
5. **Drehung** und **Größe** (bis 10×) sind die Schieberegler rechts. Bäume variieren von selbst ein wenig in Größe und Drehung,
   damit ein Wald nicht gestempelt aussieht.

Bevor du klickst, zeigt sich der Typ durchsichtig unter dem Zeiger, so gedreht und skaliert, wie er stehen wird. Platzierte
Objekte erscheinen als ihre eigenen Modelle, jedes mit einem kleinen goldenen Punkt am Fuß, der es von Weitem markiert.

## Auswählen, verschieben, drehen, löschen

**Auswählen** (in den Leisten **Gebäude** und **Objekte & Bäume**) wählt aus, was auf der Karte steht, ob dein Mod es
platziert hat oder es der Karte selbst gehört: klick auf eines, **Shift+Klick** fügt eines hinzu, oder zieh einen Rahmen
um mehrere. Dann zieh eines der gewählten, um sie zu verschieben, nutze **Drehung** und **Größe**, oder **Löschen**.
**Wie auf der Karte zurücksetzen** macht deine Änderungen an den eigenen Objekten der Karte rückgängig; **Esc** hebt die
Auswahl auf.

## Eigene Modelle

**Modell importieren…** (in **Objekte & Bäume**) macht ein 3D-Modell (.glb, .gltf oder .3ds) zu einem eigenen Felsen,
Objekt, Busch oder Baum deines Karten-Mods. Es wird wie die des Spiels platziert, auf jeder Karte des Mods, mit kleineren
Versionen für die mittlere und die weite Entfernung, die dafür erstellt werden. Gib ihm eine **Größe** und die
**Herkunft**: ein Modell, das jemand anderes gemacht hat, darf nur unter CC0 oder CC-BY in einen Mod, mit seinem Autor.
Angehakt: **Fest: Einheiten fahren darum herum**; nicht angehakt fahren Einheiten hindurch und werfen es um, wie die
kleinen Objekte des Spiels. **Dein Modell…** ändert es später. Im Spiel gesehen.

## Massive Gebäude

**Massiv** (standardmäßig an) lässt Einheiten um ein platziertes Gebäude herumfahren statt hindurch. Schalte es für ein Gebäude
aus, das nur zum Anschauen da sein soll.

## Sich darin verbergen

Platzierte Gebäude verbergen Einheiten nicht von selbst: öffne **Deckung**, wähl **Stadt** und klick auf die Stadt, die du gebaut hast.

## Rückgängig und Wiederholen

**Rückgängig** (oder **Ctrl+Z**) nimmt das letzte Objekt zurück, oder die ganze Fläche, Linie, das ganze Raster, Rechteck
oder den ganzen Pfad, und das letzte Verschieben, Drehen, Skalieren oder Löschen. **Wiederholen** (oder **Ctrl+Y**,
**Ctrl+Shift+Z**) stellt es wieder her. Jedes Kartenwerkzeug hat beides.

## Die eigenen Bäume und Objekte der Karte entfernen

1. Klick in der Leiste auf **Entfernen** (Studio 0.8.1).
2. Wähl, was es wegnimmt: **Bäume**, **Objekte**, **Gebäude** (beliebig gemischt). Jeder Kreis behält, was gewählt war, als du
   ihn gemalt hast.
3. Zieh über die Karte: rote Kreise markieren, was wegkommt, und was sie bedecken, ist rot getönt. **Größe** legt die Kreise fest;
   die Leiste zählt, was sie wegnehmen werden, wenn der Mod gebaut wird.

Wo Bäume verschwinden, öffnet sich der Boden für jede Einheit und verliert seine Walddeckung (im Spiel bestätigt: Panzer fahren in
einen gerodeten Wald, Infanterie dort ist nicht verborgen). Entfernte Gebäude öffnen ihren Boden ebenfalls für Einheiten.
**Rückgängig** (**Ctrl+Z**) nimmt das letzte Ziehen zurück, **Von vorn** entfernt jeden Kreis auf der Karte.

**Weiter:** [[Ein Szenario bearbeiten|Ein-Szenario-bearbeiten]]

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Place-Buildings-and-Trees]]
