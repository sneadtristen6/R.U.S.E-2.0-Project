# Ein Szenario bearbeiten

> **Für:** Modder · **Du brauchst:** RUSE Studio 0.9.8.4 und einen Mod · **Dauer:** ein paar Minuten

Ein **Szenario** ist das, womit eine Karte beginnt: Eroberungszonen, der Startpunkt jeder Seite, und Einheiten und
Gebäude, die schon auf dem Feld stehen. Eine Karte hat mehrere: eines für jede Art, wie das Spiel sie spielt.

## Die drei Arten, wie das Spiel eine Karte spielt

Das sind die Schaltflächen im Hauptmenü von R.U.S.E.:

| Schaltfläche | Was es ist |
|---|---|
| **KÄMPFE** | Ein freies Spiel gegen den Computer auf einer Karte, mit den Spielern, die du wählst (in anderen Spielen heißt das Gefecht oder Skirmish). |
| **OPERATION** | Eine kurze Mission mit festen Zielen, auf einem fertigen Aufbau. |
| **KAMPAGNE** | Die Geschichte, Kapitel für Kapitel. |

Das Studio benennt jedes Szenario nach der Schaltfläche, die es spielt, und eine goldene Zeile unter dem Szenario-Menü
sagt genau, wo: zum Beispiel **Im Spiel: Kämpfe › D-Day (6 Spieler)**.

## Das Szenario wählen

Wähle am Anfang der Leiste des Kartenbildschirms **Szenario** (neben **Karte**). Die eigenen Dinge der Karte (Gelände,
Gebäude, Bäume, Straßen) erscheinen blass und lassen sich nicht aus Versehen greifen; schalte zurück auf **Karte**, um
sie zu ändern. Wähle dann das Szenario im Menü oben. Startpunkte erscheinen als Säulen in der Farbe jeder Seite,
Spawnpunkte als weiße Rauten, Zonen als schattierte Flächen.

## Einen Startpunkt oder Spawnpunkt verschieben

1. Klicke auf der Seite **Szenario** auf **Verschieben**.
2. Klicke auf die Säule oder Raute, dann dahin, wo sie hin soll.
3. Um sie dahin zurückzusetzen, wo das Spiel sie hatte, klicke sie erneut an und wähle **Zurücksetzen**.

## Einheiten setzen: eine oder eine ganze Formation

1. Klicke auf der Seite **Szenario** auf **Einheit setzen**.
2. Wähle die Art (Gebäude, Boden, Infanterie, Luft), dann den Typ, dann die Einheit in der Liste (nach Nation gruppiert).
3. Wähle **Wer bekommt es?** Bei einer Operation oder einem Kampagnenkapitel zeigt die Liste die eigenen Lager dieses
   Szenarios, aus seiner Mission: **Spieler** (du: Lager 0 in der Kampagne) und die Lager des **Computer**, jedes mit
   seinem Land, dazu **Neutral**. Die Zahl in Klammern ist das, was gespeichert wird. Eine Karte für **KÄMPFE** nimmt
   nur neutrale Einheiten (das Spiel startet sie ohne Teamliste, also würden die Einheiten eines Spielers dort nie
   erscheinen).
4. **Wie viele:** 1, 2, 4, 6, 8 oder 10.
5. Für mehr als eine wähle eine **Formation**: Linie, Kolonne, Keil, Rechteck oder Kreis. Sie zeigt zum oberen
   Bildschirmrand: dreh die Ansicht, um sie auszurichten. **Abstand** legt die Meter zwischen den Einheiten fest.
6. Ringe auf der Karte zeigen, wo jede Einheit stehen wird. Klicke, um sie zu platzieren.

Eine Einheit, die du gesetzt hast, lässt sich wie jeder Spawnpunkt verschieben oder mit **Entfernen** herausnehmen.

## Mehr Spieler auf einer Karte (bis zu 8)

Jeder Spieler beginnt an einem **Startpunkt** seines Teams, einem pro Spieler: in einem 3v3 haben Team 1 und Team 2 je
die Plätze 1 bis 3. Ein 4v4 braucht in beiden Platz 4.

1. Wähle das Szenario, das das Spiel online spielt (seine goldene Zeile sagt **Kämpfe**), und klicke dann in der Leiste
   auf **Szenario**.
2. **Spieler** (rechts) zeigt die Anzahl der Karte, die des Spiels ist mit *(Spiel)* markiert. Wähle die neue Anzahl,
   höchstens 8. Die Zeile darunter nennt jeden Startpunkt, der noch fehlt, z. B. *Team 1, Platz 4*.
3. Klicke auf **Start des Hauptquartiers hinzufügen**, wähle das **Team** und klicke dann auf freies Gelände, wo dieser
   Spieler beginnt, weg von den anderen. Er bekommt den nächsten Platz des Teams, und seine Kamera und sein Intro von
   einem Mitspieler.
4. Wenn die Zeile **Jeder Spieler hat einen Startpunkt** sagt, klicke auf **Im Spiel testen** und öffne **KÄMPFE**: die
   Karte steht dort mit ihrer neuen Anzahl, z. B. *(8) Cotentin (4v4)*.

Einen Startpunkt, den du hinzugefügt hast, verschiebst du mit **Verschieben** oder nimmst ihn mit **Entfernen** weg. Mehr
als 8: nein, die Lobby des Spiels hat 8 Plätze (ausprobiert am 2026-10-02).

> [!NOTE]
> Neu, im Spiel noch nicht geprüft: sag uns in den [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions),
> wie ein Spiel mit 8 Spielern läuft.

## Eine leere Karte: das HQ jedes Spielers platzieren

Eine Karte, die als **Leeres Gelände** oder **Leerer Ozean** begonnen wurde (mit **Karte duplizieren** im Reiter
Karten), hat nichts von der kopierten Karte darauf, auch nicht ihre HQs. **Das HQ jedes Spielers** (auf der Seite
Szenario) listet jedes HQ, das die Karte braucht: klicke auf **Platzieren**, dann auf das Gelände, wo es hin soll.
**Im Spiel testen** wartet, bis jeder Spieler ein HQ hat.

**Kartengröße** (Studio 0.9.8.7) macht eine neue leere Karte größer oder kleiner, einen Streifen nach dem anderen: drück
**+** an einer Seite, um dort einen Streifen Gelände hinzuzufügen, oder **−**, um einen wegzunehmen, dann **Diese Größe
übernehmen**. Noch nicht im Spiel ausprobiert.

> [!WARNING]
> Beide leeren Karten sind noch fehlerhaft: Nutzung auf eigene Verantwortung, und sag uns, was dir auffällt.

## Sektoren

**Sektoren** (auf der Seite Szenario) ändert die Sektoren des Szenarios, die Zonen, auf denen Täuschungskarten gespielt
werden. Eine leere Karte beginnt ohne: du legst sie an.
- **Formen:** zieh einen Eckpunkt, um eine Grenze zu verschieben (die Sektoren, die sie teilen, bewegen sich mit).
  Doppelklicke auf eine Grenze, um einen Punkt hinzuzufügen; klicke mit der rechten Maustaste auf einen Punkt, um ihn zu
  entfernen. **Neuer Sektor:** zieh ein Rechteck auf dem Gelände auf. **Kein Sektor:** zieh ein Rechteck dort auf, wo
  kein Sektor sein soll. **Sektor löschen** gibt sein ganzes Gelände den Sektoren um ihn herum.
- **Malen:** wähle einen Sektor und zieh dann über das Gelände, um ihn zu malen; „Kein Sektor“ nimmt Gelände aus jedem
  Sektor heraus.
- **Ohne Sektoren beginnen** oder **Mit den Sektoren der Karte beginnen**; **Rückgängig** nimmt die letzte Änderung
  zurück.
- **Sektoren erstellen** teilt die ganze Karte in Sektoren, etwa so breit, wie **Sektoren von etwa** angibt (die
  eigenen Karten des Spiels haben Sektoren von 1 bis 3 km Breite), mit verschlungenen Grenzen; **Andere Aufteilung**
  teilt sie anders auf. Dann zieh Eckpunkte oder male, um sie umzuformen.

Im Spiel gesehen: gemalte Sektoren auf einer leeren Karte, ein neuer Sektor, auf D-Day gezeichnet und von einer
Täuschungskarte allein erleuchtet, Gelände in keinem Sektor (eine Lücke auf dem Kartentisch, die keine Täuschungskarte
erleuchtet). Die dünnen Linien, die das Studio schneidet, damit ein Sektor ein Stück bleibt, sind im Spiel noch nicht
ausprobiert.

## Versorgungsdepots auf dieser Karte

Wähle ein Versorgungsdepot, um ihm mehr Lastwagen zu geben (mehr Lastwagen, mehr Geld darin), oder nutze **Jedes Depot
hier**: multipliziere die Lastwagen jedes Depots (**mal ihre Lastwagen**) oder gib allen dieselbe Zahl (**Lastwagen je
Depot**), dann **Anwenden**. **Zurück zum Spiel-Original** macht es rückgängig. Um jede Karte auf einmal zu ändern, nutze
**Depots auf den Karten** in den **KI- und Spielereinstellungen**
([[Wirtschaft, KI und mehr|Wirtschaft-KI-und-mehr]]). Depots mit mehr als 1.000 Lastwagen brauchen Launcher 0.4.8.4 oder
neuer.

## Eine eigene Mission

Eine neue Operation oder ein neues Kampagnenkapitel kann eine eigene Mission spielen, mit Zielen, Ereignissen und
Kamerafahrten: [[Eine Mission erstellen|Eine-Mission-erstellen]].

## Deine Einheiten im Spiel sehen

1. Klicke auf **Im Spiel testen** (oben im Studio). Das Studio baut deinen Mod in die gemoddete Kopie des Spiels
   (`RUSE-Instances\Modded game` auf dem Laufwerk deines Spiels, oder der Ordner, den du in den Einstellungen gewählt hast: einer für den ganzen PC, auch für den Launcher) und startet R.U.S.E. daraus. Die Meldung unten
   sagt, was du öffnen sollst, zum Beispiel **KÄMPFE > D-Day**.
2. Klicke im Hauptmenü des Spiels auf diese Schaltfläche (**KÄMPFE** für eine Schlacht) und wähle dann die Karte
   (**D-Day**).
3. Richte das Spiel wie gewohnt ein und starte. Deine Einheiten erscheinen dort, wo du sie platziert hast.

> [!NOTE]
> Startest du R.U.S.E. über Steam, startet das Spiel ohne deinen Mod. Nutze **Im Spiel testen** (oder **Spielen** im
> Launcher).

> [!NOTE]
> Welcher Startpunkt in einer Schlacht zu welchem Spieler der Lobby gehört, wird noch getestet. Sag uns, was dir
> auffällt, in den [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

**Weiter:** [[Exportieren und teilen|Exportieren-und-teilen]]

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Edit-a-Scenario]]
