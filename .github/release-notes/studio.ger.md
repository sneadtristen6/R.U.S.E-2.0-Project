**RUSE Studio, eine Vorschau für Modder.** Durchsuche die Einheiten des Spiels in jeder seiner zehn Sprachen, ändere
sie in einem eigenen Mod und teste ihn im Spiel. Deine Steam-Installation wird nie verändert.

**0.9.8.1:** Leeres Gelände bekommt eigenen Boden, und Leerer Ozean ist entfernt.

- **Aus einer Nation eine andere machen.** Der neue Reiter **Nationen** gibt einer der sieben Nationen des Spiels
  einen neuen Namen (in der Lobby und für ihre Armee) und eine neue Flagge aus einem beliebigen Bild: zum Beispiel
  China an Italiens Stelle. Ihre Einheiten und was sie sagen ändern Sie wie bisher im Reiter Einheiten und auf der
  Seite jeder Einheit. Im Spiel gesehen: der neue Name in der Lobby, die neue Flagge im Gefecht.
- **Der Boden von Leerem Gelände wird eigens gezeichnet.** Eine leer begonnene neue Karte bekommt ihren Boden aus
  Ihren Geländestrichen statt des verschobenen Bodens der Spielkarte: runde Küsten aus der Nähe und von oben, keine
  Dellen mehr auf Hügelkuppen, und Gebäude und Panzer stehen genau darauf. Im Spiel auf Testkarten gesehen.
- **Leerer Ozean ist** aus dem Studio **entfernt**.

**Warum es noch keine Marinekarten gibt.** Wir haben Inselkarten für große Schlachten mit Schiffen ausprobiert, und
das Spiel selbst steht im Weg:

- Eine Landeinheit, die auf eine unerreichbare Insel geschickt wird, bringt das Spiel zum Absturz.
- Ein Landstreifen zwischen den Inseln verhindert den Absturz, aber dann schickt der Computer einfach seine
  Infanterie hinüber.
- Ohne Straße zwischen den Inseln lässt sich nirgends ein Gebäude platzieren.
- Mit den Waffen des Spiels können Schiffe und Landeinheiten einander kaum schaden.

Kartendaten allein können den Absturz nicht beheben: Dafür müssen die Dateien des Spiels selbst geändert werden,
deshalb warten Marinekarten auf Eugens Haltung dazu.

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
