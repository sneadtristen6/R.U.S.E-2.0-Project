**RUSE Studio, eine Vorschau für Modder.** Durchsuche die Einheiten des Spiels in jeder seiner zehn Sprachen, ändere
sie in einem eigenen Mod und teste ihn im Spiel. Deine Steam-Installation wird nie verändert.

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
