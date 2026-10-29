**RUSE Launcher 0.4, für Spieler.** Er findet R.U.S.E. über Steam, und **Spielen** baut eine gemoddete Kopie des
Spiels mit deinen Mods und startet sie. Deine Steam-Installation wird nie verändert.

**0.4.8.9:** Mods lassen sich auf mehr PCs installieren, und sichereres Lesen von Bildern.

- **Behoben, von einem Spieler gemeldet:** auf manchen PCs ließ sich kein Mod installieren: „dieser PC vertraut dem Sicherheitszertifikat der Seite nicht (unable to get issuer certificate)“. Windows hat auf diesen PCs das Zertifikat nicht, mit dem GitHubs Downloads geprüft werden, und kann es nicht holen. Der Launcher versucht es jetzt auch mit der Zertifikatsliste von Firefox, die er mitbringt. Bis dahin installiert sich ein im Browser von der Mod-Liste heruntergeladener Mod mit **Mod-Datei hinzufügen…**.
- **Sicherere Bilder:** die Bibliothek, mit der der Launcher Bilder liest (Pillow), ist jetzt Version 13.0.0, mit ihren Korrekturen gegen präparierte Bilddateien, die die App abstürzen lassen, ihren Speicher aufbrauchen oder Schlimmeres anrichten konnten.
- **Strengerer Code:** die 12 Warnungen der Code-Prüfung von GitHub zu diesem Projekt sind erledigt. Zeigt der Launcher seine Seiten in deinem Webbrowser, öffnen sie nur seine eigenen Dateien, geprüft auf eine Weise, die diese Prüfung erkennt, und Downloads verlangen TLS 1.2 oder neuer, wie schon bisher. An der Arbeitsweise des Launchers ändert sich nichts.

**0.4.8.8:** es spielt Mods, die mit Studio 0.9.8.8 gemacht wurden, und dein gemoddetes Spiel zeigt R.U.S.E. 2.0 in Gold.

- **Mods aus Studio 0.9.8.8 laufen:** eigene Gebäude (das zweite und dritte einer Nation brauchen einen kleinen Spiel-Patch, einmal heruntergeladen und nur auf deine gemoddete Kopie angewandt, nie auf das Spiel in deinem Steam-Ordner), das eigene Aussehen neuer Gebäude und eigene Objekte, mit RUSE Decoy geänderte Sounds und Animationen, die Werte der Computerspieler und die Spielregeln, und gesperrte Übergänge alter Brücken.
- **R.U.S.E. 2.0 in Gold:** dein gemoddetes Spiel beginnt mit einer Schlachtszene und einem startenden Motor, und sein Hauptmenü, der kleine Titel jedes Menüs, die Umrisse der Menüs und die Ladebildschirme zeigen R.U.S.E. 2.0 in Gold. Es wird beim ersten Mal auf deinem PC aus den Dateien deines eigenen Spiels gemacht (einmal ein paar Minuten, dann behalten). In den Einstellungen behält ein Kästchen den eigenen Titel des Spiels.
- **Behoben: dunkle und helle Flecken auf Karten aus dem Studio** (leere, vergrößerte, Relief- und Sektorkarten): eine solche Karte ist richtig beleuchtet, sobald sie mit dieser Version gebaut wird (ihr Boden wird beim ersten Mal neu gemacht).
- **Behoben, von einem Spieler gemeldet:** auf der Seite Unterstützte Mods tat „Neues Mod-Set…“ nichts. Es öffnet jetzt das neue Set. In der App selbst noch nicht getestet.
- **Die Schrift des Spiels:** der Launcher ist in der Menüschrift des Spiels geschrieben, bei jedem Start aus deinem Spiel genommen.
- **Noch fehlerhaft, Spielen auf eigene Verantwortung:** Karten mit den Texturen von Map Paint und leere Karten (Leeres Gelände, Leerer Ozean).

**0.4.8.7:** es spielt Mods, die mit Studio 0.9.8.7 gemacht wurden.

- **Mods aus Studio 0.9.8.7 laufen:** verschobene oder als Raster, Kasten und entlang von Pfaden platzierte Objekte, größere leere Karten mit ihren Sektoren, und Wirtschaftsänderungen nur für den Nuklear-Modus.
- **Die Zeilen des Builds in Ihrer Sprache**, in allen zehn.
- **Behaltene Build-Ergebnisse bleiben nach einem Update gültig.**
- **Noch fehlerhaft, Spielen auf eigene Verantwortung:** Karten mit den Texturen von Map Paint und leere Karten (Leeres Gelände, Leerer Ozean).

**0.4.8.6:** es spielt Mods, die mit Studio 0.9.8.6 gemacht wurden.

- **Mods aus Studio 0.9.8.6 laufen:** leere Karten mit Schatten auf flachem Boden, Platziertes dort, wo die kopierte Karte Meer hatte, dargestellt, und der Kameraboden auf dem neuen Boden.
- **Ein bekannter Absturz abgelehnt:** ein Mod, dessen bewaffnetes Flugzeug die Aufklärer-Flag ohne die Jäger-Flag trägt, ließ das Spiel abstürzen, wenn das Flugzeug zum Angriff geschickt wurde; der Launcher weigert sich jetzt, ihn zu bauen, und sagt warum.
- **Noch fehlerhaft, Spielen auf eigene Verantwortung:** Karten mit den Texturen von Map Paint und leere Karten (Leeres Gelände, Leerer Ozean).

**0.4.8.5:** er spielt Mods, die mit Studio 0.9.8.5 gemacht sind.

- **Mods aus Studio 0.9.8.5 laufen:** Flugzeuge in einer neuen Rolle (ein Bomber mit seinem Bombenschacht, ein Aufklärer, der seine Waffen behält), Aufklärungsfahrzeuge, Waffen, die Flugzeuge treffen, und Boden, gemalt aus der Bibliothek des Textur-Pinsels mit dem Spieldetail darüber. Ein älterer Launcher kann manche davon nicht bauen.
- **Schneller:** eine gleich bemalte Karte holt ihren gemalten Boden in Sekunden aus dem letzten Build zurück.
- **Noch fehlerhaft, Spielen auf eigene Verantwortung:** Karten mit den Texturen von Map Paint und leere Karten (Leeres Gelände, Leerer Ozean).

**0.4.8.4:** Mods laden auf jedem PC herunter, und er spielt Mods, die mit Studio 0.9.8.4 gemacht sind.

- **Mods laden auf jedem PC herunter:** auf manchen PCs lud kein Mod herunter („certificate verify failed: unable to get local issuer certificate“). Jetzt fragt der Launcher Windows nach dem Zertifikat, wie ein Browser, und versucht es erneut; auch bei seinen eigenen Updates. Noch nicht auf einem PC mit dem Problem getestet.
- **Mods aus Studio 0.9.8.4 laufen:** eigene Missionen, leere Karten mit ihren HQs und Sektoren, Depots mit mehr Lastwagen (ein älterer Launcher lehnt Depots über 1.000 Lastwagen ab), Einheiten mit eigenem Aussehen und eigenen Uniformen, Bearbeitungen fremder Mods unter eigenem Namen.
- **Noch fehlerhaft, Spielen auf eigene Verantwortung:** Karten mit den Texturen von Map Paint und leere Karten (Leeres Gelände, Leerer Ozean).

**0.4.8.3:** Kopien mit Mods kommen dorthin, wo du es sagst.

- **Wohin Kopien mit Mods kommen**, in den Einstellungen: Wähle den Ordner, in dem die Kopie des Spiels mit Mods gebaut
  wird, oder geh zurück zum empfohlenen Ort, `RUSE-Instances` auf dem Laufwerk des Spiels (dort teilt die Kopie die
  Dateien des Spiels und ist in Sekunden fertig; auf einem anderen Laufwerk ist sie eine vollständige Kopie des Spiels,
  langsamer und größer). Die saubere Sicherung des Spiels kommt daneben. Das nächste Spielen baut am neuen Ort; der
  alte Ordner kann von Hand gelöscht werden. Das Studio nutzt denselben Ordner.

**0.4.8.2:** Er öffnet sich in deinem Webbrowser, wo sein eigenes Fenster es nicht kann, und spielt Mods aus Studio
0.9.8.2.

- **Linux und Steam Deck (über Proton):** Der Launcher öffnet sich in deinem Webbrowser, wenn sein eigenes Fenster es
  nicht kann. Unter Linux noch nicht ausprobiert: Sag uns, wie es läuft.
- Mods aus Studio 0.9.8.2 laufen: Einheiten aus anderen Epochen mit eigenen Modellen, Größen, Forschung und Karten.

**0.4.8.1:** Er wandelt alte Mods um und spielt Mods aus Studio 0.9.8.1.

- **Alten Mod umwandeln…**, LittleGrooves Umwandeln übernommen: Ein älterer Mod, der als Pakete des Spiels kommt und in
  den Spielordner kopiert werden sollte, wird ein Mod, den deine Bibliothek neben anderen spielt. Noch nicht mit einem
  echten alten Mod ausprobiert.
- **Zwei Mods ändern dieselbe Spieldatei:** Der Launcher sagt es vor Spielen, und **Die von … verwenden** wählt, welchen.
- Mods aus Studio 0.9.8.1 laufen: Musik und Stimmen, eine Nation als eine andere.

**0.4.8:** er spielt Mods, die mit Studio 0.9.8 gemacht wurden, darunter neue Karten, die leer beginnen, und zeigt
die Neuigkeiten in deiner Sprache.

| Vorher | Jetzt |
|---|---|
| Eine neue Karte zeigte die Menübilder der kopierten Karte. | Ihre eigenen Bilder, so wie ihr Macher sie gemacht hat, mit den Startpunkten dort, wo ihre Spieler starten. |
| Eine auf einem trockengelegten Meer gebaute Einheit konnte das Spiel abstürzen lassen. | Behoben (im Spiel gesehen). |
| Altes Flusswasser stand als Wände am Rand einer Karte, und gelöschte Leuchttürme leuchteten noch über dem Meer. | Behoben (im Spiel gesehen). |
| Ein Mod, der eine ganze Karte löscht, konnte beim Bauen den Speicher des PCs aufbrauchen. | Er wird gebaut. |
| Die Neuigkeiten gab es nur auf Englisch. | Sie sind in der Sprache des Launchers. |

Bekannt: **Marinekarten sind noch nicht fertig.** Leerer Ozean wird gebaut und gespielt, aber Einheiten unter seinem
Wasser sind noch nicht ausprobiert.

**0.4.7:** sehr große Karten-Mods werden jetzt in Minuten gebaut (vorher dauerte das sehr lange), und er spielt Mods,
die mit Studio 0.9.7 gemacht wurden.

| Vorher | Jetzt |
|---|---|
| **Spielen** konnte Stunden brauchen, um einen großen Karten-Mod zu bauen. | Der extremste, den wir haben (die Karte „D-Day“ mit trockengelegtem Meer), brauchte etwa vier Stunden; jetzt unter 10 Minuten, mit demselben Ergebnis. |
| Der erste Bau eines großen Karten-Mods rechnete alles auf deinem PC aus. | Ein mit Studio 0.9.7 exportierter Mod bringt mit, was sein Bau für die Bewegung der Karte ausgerechnet hat: dein erster Bau geht schneller. Jede Antwort wird geprüft, und die Spieldateien kommen gleich heraus. |

Bekannt: **Marinekarten sind noch nicht ausgearbeitet.** Ein trockengelegtes oder bemaltes Meer wird gebaut und lädt,
aber das Wasser ist weiterhin zu sehen.
