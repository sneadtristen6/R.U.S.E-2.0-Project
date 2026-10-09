**RUSE Studio, eine Vorschau für Modder.** Durchsuche die Einheiten des Spiels in jeder seiner zehn Sprachen, ändere
sie in einem eigenen Mod und teste ihn im Spiel. Deine Steam-Installation wird nie verändert.

**0.9.8.2:** Die Einheiten aus anderen Epochen kommen: ihre Modelle, in echter Größe, hinter Forschung.

- **Einheiten aus anderen Epochen:** Die Epochen WWI, WWII+, Kalter Krieg und Modern im Reiter Einheiten haben jetzt
  ihre Einheiten: 366, jede das kostenlose Modell eines anderen Urhebers (CC0 oder CC BY), genannt. Jede Epoche wird
  im Studio heruntergeladen, wenn du sie wählst, von unserem GitHub (jede Datei geprüft: WWI 232 MB, WWII+ 198 MB,
  Kalter Krieg 996 MB, Modern 709 MB), und aktualisiert sich selbst, sobald weitere fertig sind.
  - **In echter Größe:** die echte Breite jeder Einheit (bei einem Flugzeug die Spannweite) im Maßstab des Spiels;
    änderbar vom 0,2- bis 5-Fachen.
  - **Erforscht wie die Einheiten des Spiels:** aus jeder Einheit des Gebäudes ihrer Nation, auch aus den
    Epochen-Einheiten des Mods, sodass eine Kette geht (ein T-80, dann ein T-90M), mit Preis und Dauer der Forschung.
    Einheiten aus WWI und WWII+ sind sofort kaufbar; die aus Kalter Krieg und Modern werden zunächst aus einer
    passenden Einheit erforscht.
  - **Eigene Karten** im Baumenü und bei der Auswahl.
  - Im Spiel gesehen: Sie laden sofort, die Forschungs-Reiter und eine Kette, ein Land Rover mit eigenem Modell, die
    Größen. Noch nicht ausprobiert: gezogene Geschütze (noch kein Geschütz des Spiels, auf das sie passen).
- **Modell importieren…:** Ein Modell, das mit einer Besatzungsfigur beginnt, bekommt sein eigenes Modell (Jeeps als
  Kopie des Kübelwagens zeigten den Kübelwagen); im Specular-Glossiness-Verfahren bemalte Modelle behalten ihre
  Farbe; als Zahlen angegebene Farben sind nicht mehr schwarz; große Modelle werden schneller importiert.
- **Eine Einheit, die aus einer Einheit einer anderen Armee erforscht wird,** ließ das Spiel in einem endlosen
  Ladebildschirm: **Neue Einheit…** entfernt diese Verbindung jetzt, und der Bau lehnt eine Einheit ab, die aus einer
  fehlenden Einheit oder der einer anderen Nation erforscht wird, und sagt, warum und wie man es behebt.
- **Linux und Steam Deck (über Proton):** Das Studio öffnet sich in deinem Webbrowser, wenn sein eigenes Fenster es
  nicht kann. Unter Linux noch nicht ausprobiert: Sag uns, wie es läuft.

**0.9.8.1:** LittleGrooves Werkzeuge kommen ins Studio, dazu Musik und Klänge und eine Nation als eine andere.

- **LittleGrooves Werkzeuge, übernommen** aus seinem RUSE-Mod-Manager:
  - **Reiter Wirtschaft:** Startgeld und Einkommen, Versorgungsdepots und die Täuschungskarten, mit denen jede Seite
    beginnt. Im Spiel gesehen: das Startgeld und die Startkarten.
  - **Reiter KI:** wie die Computerspieler spielen, welche Einheiten sie bevorzugen, die Täuschungskarten; und die
    Karten- und Missionsskripte des Spiels, als Python gezeigt, nur zum Lesen. Im Spiel gesehen.
  - **Aufwertungs-Feld** auf der Seite einer Einheit: wovon sie eine Aufwertung ist, ihre eigenen Aufwertungen, Preis
    und Dauer ihrer Forschung.
  - **Reiter Alle Werte:** ein beliebiges Objekt oder ein beliebiger Wert des Spiels, in einem Mod geändert: einen Wert hinzufügen oder
    entfernen, ein Objekt anlegen oder löschen, einem Textwert eigene Worte geben.
  - **Reiter Dateien:** eine beliebige Datei der Spielpakete, ansehen und speichern. Eine durch eine eigene Datei ersetzen oder
    eine hinzufügen: dein Mod behält nur die Änderungen, jede nach ihrer Art geprüft.
  - **Missionen:** die Skripte einer Mission ändern; sehen, ob sie in den Menüs ist, ob jede nötige Datei lädt, und
    ihre Texte; sie in ihrem Menü nach oben oder unten schieben.
  - **Karten:** Namen von Städten und Hügeln, benannte Punkte und Zonen, Name und Ausrichtung eines Kartenobjekts.
    **Notizen** zu einer Einheit, einem Wert oder einem Computerspieler.
- **Reiter Musik:** jedes Musikstück nach dem Ort, an dem es spielt, jedes in einem kleinen Editor im Studio ersetzt
  (schneiden, blenden, Lautstärke); neue Stücke in den Schlachtlisten; die Sprachzeilen einer Einheit auf ihrer Seite;
  das Hintergrundgeräusch einer Karte. Im Spiel gesehen: die Stücke, die neuen Stücke und die Sprachzeilen.
- **Aus einer Nation eine andere machen.** Der neue Reiter **Nationen** gibt einer der sieben Nationen des Spiels
  einen neuen Namen (in der Lobby und für ihre Armee) und eine neue Flagge aus einem beliebigen Bild: zum Beispiel
  China an Italiens Stelle. Ihre Einheiten und was sie sagen änderst du wie bisher im Reiter Einheiten und auf der
  Seite jeder Einheit. Im Spiel gesehen: der neue Name in der Lobby, die neue Flagge im Gefecht.
- **Einheiten aus anderen Epochen:** Der Reiter Einheiten bietet die Epochen WWI, WWII+, Kalter Krieg und Modern
  neben den Einheiten des Spiels. Sie haben noch keine Einheiten: Die kommen mit einem späteren Update.
- **Neue Karte: von Grund auf…** steht im Reiter Karten, bevor eine Karte offen ist.
- **Der Boden von Leerem Gelände wird eigens gezeichnet.** Eine leer begonnene neue Karte bekommt ihren Boden aus
  deinen Geländestrichen statt des verschobenen Bodens der Spielkarte: runde Küsten aus der Nähe und von oben, keine
  Dellen mehr auf Hügelkuppen, und Gebäude und Panzer stehen genau darauf. Im Spiel auf Testkarten gesehen.
- **Leerer Ozean bleibt, mit einem Warnhinweis** auf seiner Schaltfläche: Getrennte Inseln sind noch nicht
  bereit für große Schlachten (unten).

Noch nicht im Spiel ausprobiert: das Aufwertungs-Feld, Alle Werte, Dateien, die Werkzeuge für Missionen, die
Ergänzungen an Karten und Hintergrundgeräusche.

**Warum es noch keine Marinekarten gibt.** Wir haben Inselkarten für große Schlachten mit Schiffen ausprobiert, und
das Spiel selbst steht im Weg:

- Eine Landeinheit, die auf eine unerreichbare Insel geschickt wird, bringt das Spiel zum Absturz.
- Ein Landstreifen zwischen den Inseln verhindert den Absturz, aber dann schickt der Computer einfach seine
  Infanterie hinüber.
- Ohne Straße zwischen den Inseln lässt sich nirgends ein Gebäude platzieren.
- Mit den Waffen des Spiels können Schiffe und Landeinheiten einander kaum schaden.

Kartendaten allein können den Absturz nicht beheben, deshalb warten Marinekarten.

**0.9.8:** eine neue Karte kann leer beginnen, als flaches Land oder offenes Meer, und jede Karte kann eigene Bilder
in den Menüs des Spiels haben.

- **Eine Karte leer beginnen.** **Karte duplizieren** hat eine neue Wahl, **Ausgangspunkt**: **Leeres Gelände**
  (flaches Land, auf dem nichts steht außer den Startpunkten) oder **Leerer Ozean** (das Meer über die ganze Karte).
  Im Spiel gesehen.
- **Menübilder für jede Karte.** Wähle ein PNG für das Bild der Karte und ihre 3D-Karte in den Menüs, oder geh zurück
  zu denen des Spiels; die weißen Startpunkte werden dort gezeichnet, wo die Spieler der Karte starten. **In Blender
  machen…** öffnet das eigene 3D-Modell der Karte, um sie zu machen, und **Zurückholen** bringt sie in deinen Mod. Im
  Spiel gesehen.

| Vorher | Jetzt |
|---|---|
| Eine neue Karte begann als vollständige Kopie einer Karte des Spiels. | **Karte duplizieren** kann sie leer beginnen lassen: Leeres Gelände oder Leerer Ozean. |
| Eine neue Karte zeigte die Menübilder der kopierten Karte. | **Menübilder…** gibt ihr eigene: ein PNG von dir oder ein in Blender gemachtes Bild, mit den Startpunkten dort, wo ihre Spieler starten. |
| Die Depots, Einheiten, Gebäude und Namen der Karte blieben. | **Entfernen** nimmt eins heraus, oder alle Depots oder alle Namen auf einmal (im Spiel gesehen). |
| Die Straßen und Brücken der Karte blieben. | Das Dock Straßen entfernt sie (die Straßenlinien weg: im Spiel gesehen). |
| Die Sektoren ließen das Meer und die Ränder der Karte aus. | **Sektoren über die ganze Karte**: die ganze Karte lässt sich einnehmen (im Spiel gesehen). |
| Das Wasser einer Karte kam nur aus ihren Flüssen und ihrem Meer. | **Wasser über die ganze Karte**: eine dünne Schicht, wie das gemalte Meer einer Marinekarte (im Spiel gesehen; Einheiten darunter noch nicht ausprobiert). |
| Der Karteneditor wählte Spawnpunkte einzeln aus, unter Codenamen. | Zieh einen Rahmen, um sie wie im Spiel auszuwählen; die eigenen Symbole der Karte zeigen, was ausgewählt ist und wie viele. |
| Die Felder des Karteneditors hatten eine Größe. | Jedes schwebende Feld ändert seine Größe, von 40 % bis 125 %. |
| Die Neuigkeiten gab es nur auf Englisch. | Sie sind in der Sprache des Studios. |
| Einen Mod an die Mod-Liste zu schicken hieß, seinen Eintrag von Hand zu schreiben. | **In der Mod-Liste veröffentlichen** öffnet das Formular der Liste, schon ausgefüllt, mit einer .zip-Kopie zum Hineinziehen; jeder Export sagt, dass er mit RUSE Studio gemacht wurde. |
| Modell importieren verlor die eigene Schattierung und die durchsichtigen Teile eines Modells. | Es behält sie und sagt, was es behalten hat (noch nicht im Spiel gesehen). |
| Eine auf einem trockengelegten Meer gebaute Einheit konnte das Spiel abstürzen lassen; altes Flusswasser stand als Wände am Rand einer Karte; gelöschte Leuchttürme leuchteten noch über dem Meer. | Behoben, jedes im Spiel gesehen. |

Bekannt: **Marinekarten sind noch nicht fertig.** Leerer Ozean wird gebaut und gespielt, aber Einheiten unter seinem
Wasser sind noch nicht ausprobiert.

**0.9.7:** sehr große Karten-Mods werden jetzt in Minuten gebaut. Vorher dauerte ihr Bau sehr lange, und deshalb war
dieses Update nötig. Und **Mod exportieren…** nimmt mit, was der Bau ausgerechnet hat: der erste Bau eines solchen Mods
bei einem Spieler geht schneller.

- **Der extremste Karten-Mod, den wir haben** (die Karte „D-Day“ mit trockengelegtem Meer: 154 Einebnungsstriche,
  135 Malstriche, 33.385 gelöschte Gebäude) brauchte etwa vier Stunden zum Bauen. Jetzt baut er in **unter 10
  Minuten**, ohne etwas aus einem früheren Bau zu behalten, und die Spieldateien kommen gleich heraus. Es hat uns etwa
  15 Stunden gekostet; wo es hing und warum: [Wie wir hierher kamen](https://github.com/sneadtristen6/R.U.S.E-2.0-Project#how-we-got-here)
  (auf Englisch). Wir arbeiten weiter daran, es schneller zu machen.

| Vorher | Jetzt |
|---|---|
| Eine über Kilometer umgeformte Karte konnte Stunden zum Bauen brauchen, den Speicher des PCs erschöpfen oder als zu groß für die Bewegung der Karte abgelehnt werden. | Ihr Boden wird in Sekunden umgeformt, ihre Flussbetten repariert und ihr Boden auf allen Kernen des PCs bemalt, und ihre Bewegung auf zwei weiteren Kernen berechnet, während der Boden bemalt wird. Jeder Schritt ergibt dieselben Dateien wie vorher. |
| Ein trockengelegtes Meer blieb für Einheiten gesperrt. | Ein breites trockenes Bett bekommt Bewegungszonen, so groß wie Platz dafür ist. **Noch nicht im Spiel ausprobiert:** Einheiten auf dem geöffneten Meer. |
| Ein Neubau nach einer kleinen Änderung berechnete eine große Karte noch einmal ganz. | Was gemacht wurde, bleibt erhalten: unveränderte Malerei dauert eine halbe Sekunde, unveränderte Bewegung kommt aus dem Bau-Cache, und ein neuer Strich malt nur die Kacheln neu, die er erreicht. |
| Der erste Bau eines großen Karten-Mods bei einem Spieler berechnete alles noch einmal. | **Mod exportieren…** legt in den Mod, was der Bau für die Bewegung der Karte berechnet hat (`maps/<map>/solved.bin`). Es ist an die Datei des Spiels für diese Karte gebunden und enthält keine Spieldateien. Der Bau des Spielers nimmt es, prüft jede Antwort und ergibt dieselben Dateien. Bodenmalerei und Flussbetten werden weiterhin auf jedem PC gemacht. |
| Modell importieren erschien nur auf der Seite einer neuen Einheit: schwer zu finden. | Der Reiter Einheiten beginnt mit zwei Knöpfen: **Einheit ändern** und **Neue Einheit (Modell importieren)**. Wähle die Einheit, von der du ausgehst, gib ihr einen Namen, Erstellen: ihre Seite öffnet sich bei Modell importieren. Die Seite einer Einheit des Spiels hat **Neue Einheit aus dieser…**. |
| Die Schiffsflagge (76) sagte, eine Einheit mit ihr bewege sich auf dem Wasser. | Sie sagt, dass sich die Einheit gar nicht bewegt, wie ein Gebäude (noch nicht im Spiel getestet). |

Bekannt: **Marinekarten sind noch nicht ausgearbeitet.** Ein trockengelegtes oder bemaltes Meer wird gebaut und lädt,
aber das Wasser ist weiterhin zu sehen.
