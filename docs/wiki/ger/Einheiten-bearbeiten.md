# Einheiten bearbeiten

> **Für:** Modder · **Du brauchst:** RUSE Studio und einen Mod · **Dauer:** so lange du willst

## Eine Einheit finden

Der Reiter **Einheiten** listet jede Einheit und jedes Gebäude. Grenze die Liste ein mit:

- dem **Suchen**-Feld (Codenamen oder die Namen, die Spieler sehen, in jeder der zehn Sprachen des Spiels: die Sprachschaltfläche oben).
  Jedes Wort, das du eingibst, muss passen; **#Tags** grenzen ein (`#us`, `#germany`, `#air`, `#armor`, `#new` für die
  neuen Einheiten deines Mods; tipp `#`, um alle zu sehen), und deine letzten Suchen werden behalten;
- den Chips für **Art** und **Nation**;
- dem **Typ**-Menü: wofür sie da ist, wie HQ, Geld, Fabriken, Festungen und Attrappen bei Gebäuden, oder die Fabrik,
  die eine Einheit baut.

## Einen Wert ändern

1. Klicke auf die Einheit. Ihre Werte sind nach Abschnitten aufgelistet (Preis, Panzerung, Geschwindigkeit, Waffen...).
2. Tippe einen neuen Wert ein. Er wird sofort in deinem Mod gespeichert; der Wert des Spiels steht daneben.
3. **Rückgängig** neben einem Wert setzt den Wert des Spiels wieder ein.

## Flags: was eine Einheit ist und was sie kann

Flags sind Ein/Aus-Schalter, nummeriert von 0 bis 104, die dem Spiel sagen, was eine Einheit ist (ein Flugzeug, ein
Lastwagen, Infanterie, ein Gebäude...) und was sie kann (in den Wald fahren, rundum sehen, nur auf Befehl feuern...). Auf
der Seite einer Einheit erscheinen sie als Chips, jedes mit seinem Namen: fahr mit der Maus über eines, um genau zu
sehen, was es bewirkt, wie du es nutzt und wie sicher wir uns darüber sind. Das Kreuz nimmt eines weg; **Flag
hinzufügen…** fügt eines hinzu, sortiert danach, wofür die Flags da sind.

**Flag-Handbuch: alle Flags erklärt** (unter den Flags) öffnet die ganze Liste, mit einem Suchfeld. Zu jedem Flag sagt es:

- **was es ist und was es bewirkt** im Spiel;
- **wie du es nutzt**;
- **wie sicher wir uns sind:** *im Spiel ausprobiert*, *aus den Einheiten des Spiels* (was die Einheiten des Spiels, die
  es haben, gemeinsam haben), *erwartet, noch nicht ausprobiert*, *setzt das Spiel selbst* (es schaltet diese während
  des Spiels ein und aus: in der Liste einer Einheit bewirken sie nichts) oder *ungenutzt*.

**Das Studio prüft die Flags jeder Einheit**, jedes Mal, wenn du sie änderst, und noch einmal, bevor das Spiel startet:

- **Bekannte Abstürze stoppen den Build**, sodass das Spiel nie mit ihnen gestartet wird. Die Seite der Einheit sagt,
  warum, und bietet die Korrektur an (**62 entfernen**, **100 hinzufügen**):
  - 62 (Lastwagen) oder 63 (Baulastwagen) bei etwas, das kein Lastwagen ist: das Spiel stürzt beim Start der Partie ab;
  - 99 (Aufklärungsflugzeug) bei einem Flugzeug mit Waffen, ohne 100 (Jäger): das Spiel stürzt ab, wenn das Flugzeug zum
    Angriff geschickt wird. Nutze das Feld **Rolle** (Aufklärer behält seine Angriffe) oder füge 100 hinzu;
  - 59 (Fallschirmjäger-Transporter) bei etwas anderem als einem Flugzeug, oder bei einem Flugzeug ohne Einheit zum
    Absetzen.
- **Was eine Einheit voraussichtlich kaputt macht, ist eine Warnung**, kein Stopp: 2 (Flugzeug) bei einer Bodeneinheit,
  4 (Gebäude) oder 49 bei einer Einheit, 6 oder 76 bei einer Einheit, die sich bewegen soll (sie bleibt stehen), 42
  (Infanterie) bei einem Fahrzeug, oder 43 (ihr Team zählt sie mit) oder 22 (der Spieler kann ihr Befehle geben)
  wegnehmen.

Nützliche, im Spiel ausprobiert: nimm **11, 21 und 55** zusammen weg, damit ein Fahrzeug in den Wald fahren kann; **1**
gibt jeder Einheit indirektes Feuer; **71** sieht rundum; **77** feuert nur auf Befehl.

**Eigene Flag-Typen** (Studio 0.9.8.8): **Flag-Typen anlegen oder ändern…** unter den Flags einer Einheit legt einen
benannten Satz von Flags des Spiels an, jedes auf **An** oder **Aus**, mit einer Zeile dazu, wofür er da ist. **Einen
Flag-Typ geben…** schaltet auf jeder Einheit diese Flags in einem Zug ein und aus; nimmst du ihn wieder weg, sind die
Flags der Einheit wieder wie vorher. Ändere einen Typ, und jede Einheit mit ihm ändert sich mit. Das Spiel wirkt nur auf
seine eigenen Flags, also kombiniert ein Typ, was sie schon tun. Noch nicht im Spiel ausprobiert.

## Eine neue Einheit erstellen

Eine neue Einheit beginnt als Kopie einer Einheit des Spiels, mit einem eigenen Namen, sodass du sie ändern kannst, ohne
das Original anzurühren. Der Reiter Einheiten hat oben zwei Schaltflächen: **Einheit ändern** (die Liste, dann die Werte
der Einheit und Blender) und **Neue Einheit (Modell importieren)**. Wähle mit **Neue Einheit** die Einheit, von der du
ausgehst, gib ihr einen Namen und klicke auf **Erstellen**; dann ändere sie wie jede andere. Oder wähle die Einheit und
dann **Neue Einheit…** auf ihrer Seite.

## Ändern, wie eine Einheit aussieht

Die Seite der Einheit zeigt ihr **3D-Modell**: zum Drehen ziehen, zum Zoomen scrollen.

Darunter fasst **Aussehen und Bewegung** alles zusammen, wie die Einheit aussieht und sich bewegt, eine Zeile für
jedes, in der Reihenfolge, in der du arbeitest: **Modell**, **Seine Soldaten** (ein Trupp, dessen Schützen und Soldat
mit schwerer Waffe verschiedene Modelle haben), **Geräusche und Animation** und **Fährt in**. Jede Zeile sagt, was die
Einheit jetzt hat, und hat eine Schaltfläche für das Übliche; **Mehr** zeigt die übrigen Optionen dieser Zeile direkt
dort. Alles, was du änderst, wird sofort in deinem Mod gespeichert: nichts zu speichern, kein Ordner zu wählen. Neu
bemalen, eine eigene Kopie des Modells, die Uniform eines Trupps und ein eigenes Modell sind in der Zeile **Modell**;
Geräusche und Animationen änderst du in RUSE Decoy aus der Zeile **Geräusche und Animation** (**In RUSE Decoy
ändern**): eine Animation nur für diese Einheit oder für alle Einheiten, die sie spielen, ein Geräusch für alle
Einheiten, die es spielen.

- **In Blender neu bemalen:** klicke auf **In Blender öffnen** (Blender ist kostenlos; findet das Studio es nicht, bietet
  die Seite **Blender holen (kostenlos)** und **Blender auswählen…** an, um ihm zu zeigen, wo `blender.exe` liegt). Die
  Einheit öffnet sich mit ihren Bildern, bereit zum Bemalen des Modells. Male, dann klicke auf **Zurückholen**: deine
  Farbe kommt in deinen Mod. Im Spiel gesehen, aus der Nähe und von weitem.
- **Ihre Karte im Baumenü:** dreh und zoome das 3D-Modell, bis es im gestrichelten Rahmen richtig aussieht, dann
  **Diese Ansicht als Karte nehmen**. **Karte des Spiels** nimmt sie zurück. Im Spiel gesehen. Bei einer neuen Einheit
  ist die Karte ihre eigene: die Einheit, die sie kopiert, behält ihr Bild.
- **Ihre eigene Kopie des Modells:** eine Einheit, die mit dem Modell des Spiels gezeichnet wird, teilt ihre Farbe mit
  jeder Einheit, die damit gezeichnet wird. **Eigene Kopie des Modells geben** (auf ihrer Seite) macht dasselbe Modell
  mit eigenen Texturen: dann bemalt **In Blender öffnen** nur diese Einheit. Geht bei neuen Einheiten und denen des
  Spiels.
- **Die Uniform eines Trupps:** die Soldaten einer Nation tragen im Spiel alle ein Bild (die der USA: ihre GIs, Rangers
  und Fallschirmjäger, und die Besatzungen ihrer Geschütze und Fahrzeuge), daher wird die **Standarduniform** hier nicht
  neu bemalt. Wähle **Eigene Uniform**, um dem Trupp eine eigene zu geben, und bemale sie dann in Blender. Im Spiel
  gesehen.
- **Fährt in:** der Lastwagen, zu dem ein Trupp oder ein Geschütz auf den Straßen wird: der des Spiels, der einer
  anderen Nation, oder die Kopie eines Lastwagens, die du gemacht und neu bemalt hast. Im Spiel gesehen.
- **Ein eigenes Modell (neue Einheiten):** **Modell importieren…** holt ein 3D-Modell aus Blender oder einem anderen
  3D-Programm. Siehe [[Ein Modell importieren|Ein-Modell-importieren]]. Eine Einheit des Spiels behält ihr Modell: ihre Seite
  hat **Neue Einheit aus dieser…**, um die neue Einheit zu erstellen, die das Modell bekommt.
- **Eine neue Einheit, von Anfang bis Ende:** **Neue Einheit (Modell importieren)** oben im Reiter Einheiten, wähle
  die Einheit, von der du ausgehst (ein Panzer für einen Panzer, ein Trupp für Soldaten oder ein Pferd mit Reiter),
  gib ihr einen Namen und klick auf **Erstellen**. Dann geh **Aussehen und Bewegung** von oben nach unten durch: ihr
  Modell, ihre Soldaten, ihre Animationen, ihre Geräusche, ihr Lastwagen. Gib ihr eine Karte, stell Preis und Werte
  ein und dann **Im Spiel testen**. Ein großer Mod mit vielen neuen Einheiten sind dieselben Schritte für jede: Jede
  Einheit behält all das in deinem Mod unter ihrem eigenen Namen.
- **Eine Einheit, die ihren Reiter trägt (ein Pferd, ein Motorrad):** ein Modell mit dem Reiter und dem, worauf er
  reitet, auf einem Skelett, mit eigenen Animationen (mindestens Stehen, Gehen und Laufen), auf einen kopierten Trupp
  importiert: siehe [[Ein Modell importieren|Ein-Modell-importieren]], den Teil über ein Modell mit eigenen Knochen
  und Animationen. Die Horse Squad wurde so im Studio gemacht und im Spiel gespielt (November 2026); nichts anderes,
  das so gemacht wurde, ist bisher im Spiel ausprobiert.

## Panzerung

**Panzerung** auf der Seite einer Einheit wählt eine der Panzerungsstufen des Spiels (Panzer haben 1 bis 5, die Zahl
auf dem Schild). Die Einheit kämpft damit, und ihre Karte und das Baumenü zeigen sie. Eine Zahl im Panzerungsteil selbst
zu ändern ließ eine Einheit mit einem Wert kämpfen, während ihre Karte einen anderen zeigte, deshalb lässt sich dieser
Teil nicht mehr direkt ändern. Im Spiel gesehen.

## Forschung: wovon sie eine Verbesserung ist

Die Seite einer Einheit hat ein Feld **Verbesserung und Forschung**: die Einheit, deren Verbesserung sie ist
(**Verbesserung von**), ihre eigenen Verbesserungen, und ihr Forschungspreis und ihre Forschungszeit. Wähle eine andere
Einheit desselben Baumenüs, oder **Keine: eine eigene Einheit**, damit sie von Anfang an kaufbar ist. Forschungszeiten
lassen sich in Sekunden oder Minuten eintippen (die Auswahl daneben).

Nimmst du eine Einheit heraus, von der aus andere erforscht werden, entscheidet **Einstellungen > Forschung**, was
passiert: **Mich zuerst warnen** (der Standard), **Ablehnen** oder **Neu verknüpfen** mit ihrer eigenen Vorgängerin.
Eine Einheit, die noch von einer erforscht wird, die es nicht mehr gibt, sagt das hier und in der Prüfleiste, und der
Build stoppt an ihr, bis du eine andere wählst.

Eine Einheit, die in ihrem Baumenü erscheint, muss von einer Einheit aus erforscht werden, die dort ebenfalls erscheint:
die, die du bauen kannst, kommt zuerst, die Forschung danach. Eine Einheit, die an einem Schlachtdatum erscheint, an dem
die Einheit, von der aus sie erforscht wird, verborgen ist, hält das Spiel an, wenn sich dieses Baumenü öffnet (im
Spiel gesehen), deshalb nennt die Prüfleiste sie und der Build stoppt an ihr. Zeig die andere Einheit wieder an, oder
wähle eine andere Einheit, von der aus sie erforscht wird, oder keine. **Nationen > Alle ausblenden** erledigt das für
dich: eine Einheit, die noch von einer verborgenen erforscht wird, wird von Anfang an kaufbar.

## Einheiten aus anderen Epochen

366 Einheiten vom Ersten Weltkrieg bis heute, jede das kostenlose 3D-Modell eines anderen Erstellers, lassen sich als
neue Einheiten zu deinem Mod hinzufügen, in ihrer echten Größe und hinter Forschung: siehe
[[Einheiten aus anderen Epochen|Einheiten-aus-anderen-Epochen]].

## Waffen und Munition

Das Feld **Waffen** auf der Seite einer Einheit listet ihre Waffen (Waffe 1 ist die Hauptwaffe). **So funktionieren
Waffen und Munition**, darunter, enthält diese Schritte ebenfalls.

1. **Jede Waffe feuert eine Munition.** Die Liste daneben wählt welche: jede Munition des Spiels, nach Typ sortiert
   (AP, HE, Flugabwehr, Maschinengewehre, Bomben, Raketen...), oder eine Kopie, die du gemacht hast. Ihr Mündungsfeuer
   und ihr Klang kommen mit.
2. **Die Munition entscheidet, was die Waffe tut:** ihren Schaden, ihre Reichweite, ihre Feuerrate und was sie treffen
   kann. **Munition öffnen**, um ihre Zahlen zu sehen und zu ändern.
3. **Eine Munition zu ändern ändert jede Einheit, die sie feuert** (ihre Seite listet sie). Für nur eine Einheit: klicke
   auf der Seite der Munition auf **Diese Munition kopieren…**, ändere die Kopie und wähle dann die Kopie in der Liste
   der Waffe. Der Schieberegler **Reichweite** einer Waffe fragt dasselbe: nur diese Einheit, oder jede Einheit mit
   dieser Munition.
4. **Trifft** (unter einer Waffe) wählt den Boden, Flugzeuge oder beides. Das Feld **Rolle** eines Flugzeugs legt fest,
   wie es angreift (unten).
5. **Eine Waffe hinzuzufügen oder zu entfernen geht noch nicht:** Waffen hängen an den Animationen des Modells, und so
   weit sind wir noch nicht.

**Ihr Name im Spiel** (auf der Seite einer Munition, Studio 0.9.8.8): wie das Spiel die Munition nennt, ihr **Name**
(Medium cal., MG 42) und ihre **Art** (AP shell). Gib neue Wörter ein und speichere: jede Sprache zeigt sie, bis du eine
einzeln mit **Text ändern …** änderst; **Wörter des Spiels** nimmt deine wieder heraus. Eine kopierte Munition heißt so,
wie du sie nennst. Noch nicht im Spiel ausprobiert.

**Waffenklasse** (auf der Seite einer Munition, Studio 0.9.8.17): wie viel ihres Schadens die Munition jeder Zielart
zufügt. **Neue Waffenklasse…** öffnet eine Zahl pro Zielart: Gebäude und Befestigungen, Flugzeuge, Fallschirmjäger im
Sprung, Infanterie, leichte Fahrzeuge (Transporter), Panzerung 1 bis 5 und Baufahrzeuge. 1 ist voller Schaden, 2 das
Doppelte, 0,5 die Hälfte, und 0 heißt, sie kann dieses Ziel gar nicht angreifen. **Klasse speichern** gibt der Munition
ihre eigene Kopie der Schadenstabelle des Spiels: der Schaden keiner anderen Munition ändert sich, aber jede Einheit,
die diese Munition verschießt, bekommt sie (für nur eine Einheit zuerst **Diese Munition kopieren…**). Die
Schaltfläche heißt dann **Diese Waffenklasse ändern…**; **Zurück zur Klasse des Spiels** nimmt die Kopie wieder
heraus, und das Löschen einer kopierten Munition nimmt ihre Klasse mit. Im Spiel gesehen: Schützengruppen, deren
Munition Zahlen gegen Panzer bekam, schossen mit ihren Gewehren auf Panzer und beschädigten sie. Die Schaltfläche
selbst wurde im Studio noch nicht angeklickt.

**Schussgeschwindigkeit:** Schussgeschwindigkeit und Luftwiderstand einer Munition bestimmen, wann der Treffer landet:
ein langsamerer Schuss trifft später, und auf ein bewegtes Ziel wird um die Flugzeit vorgehalten (aus der
Funktionsweise des Spiels bekannt; noch nicht in einem Test ausprobiert).

## Die Rolle eines Flugzeugs ändern (Studio 0.9.8.5)

Die Seite eines Flugzeugs hat ein Feld **Rolle**: **Jäger**, **Jagdbomber**, **Bomber** oder **Aufklärer**. Wie es
fliegt und angreift, wie die Computerspieler es nutzen und die Wörter seines Baumenüs ändern sich damit.

- **Bomber:** ein Bomber wirft seine Bomben in einem geraden Anflug ab, und nur aus einem Bombenschacht. Wähle zuerst
  Bomben für eine seiner Waffen (Waffen, unten), dann mach ihn zum Bomber: seine Bomben kommen in einen Bombenschacht,
  kopiert von dem eines Bombers des Spiels, und du kannst sie dort ändern. Das ist die Korrektur für einen Jagdbomber
  mit Bombenteppichen, der nichts abwarf. Im Spiel gesehen.
- **Aufklärer:** ein Flugzeug mit Geschützen kann weiter angreifen (das Feld sagt **Aufklärer, behält seine Angriffe**)
  und bekommt die Sicht der Aufklärer. Im Spiel gesehen mit einer Stuka und einer ME109.
- Ein Fallschirmjäger-Flugzeug behält seine Rolle. **Rückgängig** neben dem Feld gibt die Rolle des Spiels zurück, die
  Bomben dort, wo sie waren.

## Ein Fahrzeug zum Aufklärer machen (Studio 0.9.8.5)

Das Feld **Rolle** eines Bodenfahrzeugs: **Aufklärung** gibt ihm die Sicht der Aufklärungswagen (viel weiter als die
eines Panzers), wie die Computerspieler sie nutzen, die Wörter ihres Baumenüs, und es kann in den Wald fahren. Es bleibt
so zäh und bewaffnet, wie es ist.
Im Spiel gesehen mit einem Panzer IV.

## Was eine Waffe trifft (Studio 0.9.8.5)

Unter jeder Waffe wählt **Trifft** **Bodenziele**, **Flugzeuge** oder **Boden und Flugzeuge**. Flugzeuge: die Waffe
feuert eine Kopie ihrer Munition, die Flugzeuge trifft (und dem Boden nichts tut). Beides: sie behält ihre Munition und
bekommt daneben eine zweite Waffe für Flugzeuge, so wie die Flak des Spiels für jedes eine hat. Ein Panzer, der auf
Flugzeuge feuert, ist im Spiel gesehen; das Geschütz eines Flugzeugs, das nur den Boden treffen soll, macht noch keinen
Schaden.

## Testen

**Im Spiel testen** baut den Mod und startet R.U.S.E. Such die Einheit dort, wo sie gebaut wird (ihre Fabrik), in einer Schlacht (Hauptmenü: **KÄMPFE**, dann eine Karte).

**Weiter:** [[Exportieren und teilen|Exportieren-und-teilen]]

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Edit-Units]]
