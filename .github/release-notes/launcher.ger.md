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

**0.4.6:** **Spielen** startet sofort, wenn sich nichts geändert hat, und spielt Mods, die mit Studio 0.9.6 gemacht wurden: neue
Einheiten mit einem eigenen 3D-Modell.

| Vorher | Jetzt |
|---|---|
| **Spielen** baute jedes Mal die ganze gemoddete Kopie neu, auch wenn sich nichts geändert hatte (ein Spieler: „jedes Mal 30 Minuten warten“). | Nichts geändert: das Spiel startet sofort. Eine Änderung baut neu, aber die unveränderten Dateien der letzten Kopie werden wiederverwendet, sodass eine Kopie auf einem anderen Laufwerk als dem des Spiels nicht mehr jedes Paket neu kopiert. Spielen sagt, wie viel es kopiert hat. |
| Jeder Build las die Einheitendaten des Spiels neu ein. | Zwischen Builds behalten: ein großer Test-Mod brauchte jedes Mal 213 s; jetzt brauchen die Builds nach dem ersten 68 s. |
| Eine neue Einheit eines Mods hatte das Modell der Einheit, die sie kopiert. | Ihr eigenes Modell aus dem Mod (`files/models`) ist im Spiel. **Im Spiel gesehen:** ein M1 Abrams neben dem Sherman. |
| Eine neue Einheit eines Mods mit eigener Karte ließ das Spiel abstürzen, wenn sie gebaut wurde. | Behoben. **Im Spiel gesehen.** |
| Die Farben neu bemalter Einheiten waren stellenweise etwas daneben. | Näher am Bild des Mods. Ein Mod mit neu bemalten Einheiten oder bemaltem Boden bekommt einen neuen Fingerabdruck und Beitrittscode: alle, die zusammen spielen, sollten aktualisieren. |
| Ein langsamer Start hinterließ keinen Hinweis. | **Bericht kopieren** listet die Schritte der letzten fünf Starts auf. |
| — | Spielt Mods mit dem Löschen der ganzen Karte aus Studio 0.9.6, Straßen auf umgeformtem Boden und aufgefüllten Flussbetten (neu, noch nicht im großen Maßstab im Spiel gesehen). |

**0.4.5:** spielt Mods, die mit Studio 0.9.5 gemacht wurden: neu bemalte Einheiten, ihre eigenen Karten und Einheiten mit eigenen Modellen.

| Vorher | Jetzt |
|---|---|
| Ein Mod konnte nicht ändern, wie eine Einheit aussieht. | Neu bemalte Einheiten und Karten aus einem Mod erscheinen im Spiel. **Im Spiel gesehen:** ein roter Sherman, eine im Studio gemachte Karte. |
| Einen Mod, dessen Modellpakete für Einheiten gewachsen waren, verwarf das Spiel: ein Absturz bei der ersten Fabrik. | So gebaut, wie das Spiel sie prüft. **Im Spiel gesehen:** ein zweiter Sherman mit eigenem Modell. |
| Ein Mod, der in einem Kampagnenkapitel oder einer Operation Einheiten einer anderen Nation erscheinen ließ, stürzte beim Laden ab (französische Einheiten auf Holland). | Ihre Modelle laden auch dort. **Im Spiel gesehen.** |
| Das Einebnen der Berge am Rand einer Karte ließ dort eine Klippe zurück. | Der Rand folgt dem Boden. **Im Spiel gesehen.** |

**0.4.4:** spielt Mods mit neuen Karten, gemacht mit Karte duplizieren aus Studio 0.9.4.

| Vorher | Jetzt |
|---|---|
| Neue Karten aus einem Mod waren im Spiel noch nicht ausprobiert. | **Im Spiel gesehen:** die neue Karte eines Mods steht in KÄMPFE und spielt ihren eigenen Boden, 101 auf einmal. Noch früh: melde, was du findest. |
| Updates kamen nur als ganze Versionen. | Kleine Korrekturen können zwischen Versionen kommen (0.4.4.1), angeboten wie jedes Update. |

**0.4.3:** spielt Mods, die mit Studio 0.9.3 gemacht wurden, und baut sie etwa dreimal schneller.

| Vorher | Jetzt |
|---|---|
| Felsen und die meisten anderen Objekte, die ein Mod platzierte, verschwanden, sobald die Kamera die Nähe verließ. | Bis in die Ferne dargestellt; die eigenen Objekte der Karte unverändert. **Im Spiel gesehen.** |
| Eine neue Straße eines Mods durch einen Wald war von hoch oben ein heller Streifen oder aus mittlerer bis großer Entfernung verschwunden. | Durch Wälder gemalt wie die eigenen Straßen der Karte. **Im Spiel gesehen.** |
| Die Straßen eines Mods nahmen immer die Bäume von ihrem Weg. | Eine Straße kann sie behalten (`keep_trees`): sie läuft unter den Bäumen, im Wald blasser und grauer. |
| **Spielen** brauchte etwa 5 Minuten, um einen Mod mit neuen Straßen auf M03_Italie zu bauen. | Etwa 1½ Minuten nach dem ersten Mal auf einer Karte. |

**0.4.2:** spielt Mods, die mit Studio 0.9.2 gemacht wurden.

| Vorher | Jetzt |
|---|---|
| Ein Mod mit einer Straße über Wasser auf Italien, Deutschland, Holland und anderen Karten wurde abgelehnt: seine Brücke „hätte keinen Boden“. | Gebaut: die Brücke bekommt den eigenen Boden der Karte. Auf diesen Karten noch nicht im Spiel gesehen. |
| Ein Mod, der dem Spieler in einem Kampagnenkapitel Einheiten gibt (Seite 0), wurde abgelehnt, und bei Einheiten für die Seiten des Computers wurde gewarnt, sie „erscheinen vielleicht nie“. | Gebaut; gewarnt wird nur bei einer Seite, die die Mission des Kapitels nicht hat. |
| Auf M03_Italie und anderen Karten verdeckte eine neue Straße eines Mods im offenen Gelände von fern die Szenerie der Karte, und seine Objekte zeigten sich nur aus der Nähe. | Die Fernansicht der Karte bleibt, wie sie war, und die Objekte des Mods zeigen sich von fern. Noch nicht im Spiel gesehen. |

**0.4.1:** deine Sprache vom ersten Start an, und ein Editor für Mod-Sets, der Mods nach ihrem Namen findet.

| Vorher | Jetzt |
|---|---|
| Beim Erstellen eines Mod-Sets wurde deine ganze Bibliothek aufgelistet, mit Erstellen ganz unten, und ohne Möglichkeit, einen Mod nach seinem Namen zu finden. | Erstellen ist oben, mit den Mods, die schon im Set sind, direkt darunter; darunter „Mods aus Ihrer Bibliothek hinzufügen“ mit einer Suche, die die Liste beim Tippen eingrenzt. |
| Die Sprache steckte in den Einstellungen, sodass Spieler nicht wussten, dass der Launcher ihre Sprache spricht. | Der erste Start fragt: „Wählen Sie Ihre Sprache“, jede Sprache in ihren eigenen Worten, die, auf die dein Spiel in Steam eingestellt ist, markiert (Spieler, die aktualisieren, sehen es einmal). Danach ein Sprachknopf oben, immer im Blick. |
| Die Windows-Liste der installierten Apps zeigte die allererste installierte Version. | Sie zeigt die Version, die du hast. |

**0.4.0:** spielt Mods mit neuen Straßen so, wie Studio 0.9 sie baut: sie sehen aus wie die eigenen Straßen der Karte, von hoch
oben bis hinunter zum Boden (im Spiel auf D-Day getestet).

![Eine neue Straße aus der Nähe auf D-Day](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Vorher | Jetzt |
|---|---|
| Die neuen Straßen eines Mods verschwanden aus der Nähe. | Sie werden mit den eigenen Asphalt- und Rand-Aufklebern der Karte gezeichnet, gemalt wie die Straßen der Karte, und die Pflanzen auf ihrem Weg werden entfernt. |
| Ein Mod mit vielen Löschkreisen brauchte Minuten zum Bauen. | Viel schneller. |

**0.3.3:** spielt Mods, die mit Studio 0.8.3 gemacht wurden.

| Vorher | Jetzt |
|---|---|
| Ein Mod mit einer gedrehten Eröffnungskamera (Studio 0.8.3) wurde abgelehnt. | Gebaut: die Kamera ist so gedreht, wie der Mod es sagt. |
| Die Eröffnungskamera eines verschobenen Startpunkts blieb am alten Ort. | Die Kamera zieht mit; ein neuer Startpunkt bekommt eine eigene Kamera. |
| Ein Mod mit einem Startpunkt in einem Wald wurde abgelehnt. | Gebaut: ein HQ funktioniert dort. |

**0.3.2:** eine Spielkopie für den ganzen PC, die Version wird angezeigt, und eine übersichtlichere Bibliothek.

| Vorher | Jetzt |
|---|---|
| Jedes Mod-Set baute seine eigene Kopie des Spiels. | Eine gemoddete Kopie für den ganzen PC, geteilt mit dem Studio. |
| Die Version wurde nicht angezeigt, und Neuerungen war eine Liste. | Die Version steht neben dem Namen, und Neuerungen öffnet eine Vorher/Jetzt-Tabelle wie diese. |
| Karten und Mods sahen in der Bibliothek gleich aus. | Eine Karte hat ein Abzeichen KARTE. |
| Wenige Tooltips. | Tooltips an den wichtigsten Bedienelementen. |
| Mods mit neuen Straßen auf Twilight of the Gods, Alpha, Ostfriesland und Robert fehlte das Straßenmodell der Karte. | Sie bekommen es auch. |

**0.3.1:** Mods mit Einheiten einer anderen Nation (etwa ein deutscher Tiger für die USA) funktionieren, sogar in einem Match,
in dem niemand diese Nation spielt (im Spiel getestet, 2026-10-02). Und ein neuer Look: die Blautöne von R.U.S.E. statt
Schwarz und Gold, und ein neues Logo: ein Jagdflugzeug, das durch die Wolken steigt. Die Seitenleiste hat zwei Reiter,
**Mod-Sets** und **Mod-Bibliothek**, jeder mit der ganzen Höhe, sodass deine ganze Bibliothek erreichbar ist (die Hälfte
war hinter der Bildlaufleiste versteckt), mit einer Suche und einer Anzahl. Das Installationsprogramm bietet neben der
Desktop-Verknüpfung eine **saubere Sicherung des Spiels** an und sagt, warum.

**0.3.0:** **Unterstützte Mods:** der Launcher zeigt unsere Mod-Liste
([sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods)); hake die an, die du willst, und sie werden
heruntergeladen und geprüft. Beim ersten Start wählst du deine Mods; Cheat-Mods werden getrennt gehalten und nie für dich
angehakt. Ein Knopf **Fehlersuche** (untere Leiste, und in jeder Problemmeldung) prüft auf einmal, was **Spielen**
verhindern kann, und behebt, was er kann, mit einem Bericht zum Einfügen in einen Fehlerbericht. Eine
**saubere Sicherung des Spiels** in den Einstellungen behält eine saubere Kopie der Dateien deines Spiels und stellt alles wieder her, was ein
anderer Mod-Manager geändert hat (oder lass Steam es reparieren). Mods, die mit dem neuen Studio gemacht wurden,
funktionieren so, wie sie gemacht wurden: Panzer und Infanterie überqueren neue Brücken auf der Fahrbahn, Infanterie folgt
neuen Straßen, gerodete Wälder sind für Einheiten offen, platzierte Gebäude stehen in jeder Größe auf dem Boden, und
Deckung landet dort, wo sie gemalt wurde, auf D-Day und den anderen Karten, die nicht quadratisch sind. Bekanntes Problem:
neue Straßen werden aus der Nähe noch nicht gezeichnet (von fern sind sie zu sehen).

**0.2.11:** **Spielen** funktioniert jedes Mal: eine gemoddete Kopie, die Windows nicht löschen will (eine Datei, die eine
ältere Version verknüpft hat, ein Programm, das sie noch festhält), wird nach `RUSE-Instances\.trash` beiseitegelegt,
statt das Spiel zu stoppen, und ein Spiel, das noch aus der Kopie läuft, wird genannt. Mods mit neuen Brücken schaffen nie
Boden, den Bodeneinheiten nicht erreichen können (das ließ das Spiel abstürzen).

**0.2.9:** **Spielen** funktioniert, wenn die Dateien deines Spiels schreibgeschützt sind: es schlug mit „[WinError 5]
Access is denied“ fehl, sobald eine gemoddete Kopie halb gebaut liegen blieb. Läuft das Spiel noch aus der gemoddeten
Kopie, wird dir gesagt, es zu schließen, statt dass du einen Windows-Fehler bekommst. Mods mit neuen Straßen bauen ihre
gemalten Straßen und Brücken.

**0.2.8:** ein Mod, den du hinzufügst, wird sofort geprüft, so wie der Spiel-Build ihn lesen wird: eine kaputte
Kartendatei oder ein Kartenordner, der nach dem Titel der Karte benannt ist (maps/Blitz statt maps/SuperCrossRoads4),
wird mit seiner Lösung genannt, bevor Spielen daran scheitern würde.

**0.2.7:** **Hilfe** und **Problem melden** in der unteren Leiste: das Wiki (ein Handbuch zum Spielen von Mods) und ein
Fehlerbericht in deinem Browser, in dem die Version des Launchers schon eingetragen ist. Eine Problemmeldung hat einen
eigenen Link **Melden**. Der Launcher sendet nichts: du liest den Bericht und postest ihn. Mods, deren Kartenordner nach
dem Titel der Karte benannt ist (maps/Blitz statt maps/SuperCrossRoads4), bekommen jetzt die Lösung gesagt.

**0.2.6:** ein Knopf **Einstellungen** (oben rechts): die Sprache, der Spielordner und Updates an einem Ort, bereit für
mehr.

**0.2.5:** Updates zu finden ist robuster: wenn GitHub die eine Prüfung beim Start abweist (es erlaubt 60 pro Stunde je
Internetadresse, geteilt mit allem, was daran hängt), liest der Launcher stattdessen die Release-Liste von GitHub.

**0.2.4:** deine Sprache bleibt über Neustarts, Updates und Neuinstallationen erhalten.

**0.2.3:** der rote Kasten klappt zusammen wie der gelbe (ein großes Set kann Dutzende Konflikte auflisten).

**0.2.2: In die beste Reihenfolge bringen.** Wenn Mods in einem Set dieselben Werte ändern, hat der gelbe Kasten einen
Knopf **In die beste Reihenfolge bringen**: Mods, die mehr ändern, kommen zuerst und kleinere danach, sodass jeder so viel
von seinen Änderungen behält, wie er kann. Er sagt, welche Mods er rettet, und die Mods lassen sich weiterhin von Hand
verschieben.

**0.2.1: Mods, die nicht zusammenpassen, lassen sich nicht spielen, und der Launcher sagt, warum.** Wenn zwei Mods in
einem Set dieselbe Datei oder dasselbe Skript ersetzen, nennt ein roter Kasten die Mods und was beide ändern, und Spielen
bleibt aus, bis einer herausgenommen wird. Wenn ein späterer Mod nur Werte eines früheren überschreibt (etwa die
Geschwindigkeit eines Schiffs), listet ein gelber Kasten sie auf, und das Set lässt sich trotzdem spielen.

**Neu in 0.2:**

- **Mod-Sets im Fenster erstellt:** neu, bearbeiten, umbenennen, duplizieren, löschen und die Mods in Reihenfolge bringen.
  Keine Dateien mehr, die von Hand bearbeitet werden müssen. Eine Anleitung in drei Schritten auf dem ersten Bildschirm
  zeigt den Weg.
- **Mod-Datei hinzufügen…** (oder sie auf das Fenster ziehen): eine von RUSE Studio exportierte `.rusemod`, ein
  Mod-Ordner in einer `.zip` oder eine **RUSE Mod Manager `.rmod`**, so verwendet, wie sie ist (angewandt von
  LittleGrooves eigener Engine).
- **Diese Ladereihenfolge teilen** als Text, und **Ladereihenfolge importieren…** von einem Freund: der Launcher sagt,
  welche Mods du hast, welche fehlen und welche eine andere Version sind, und macht dann das Set. Es ist derselbe Text,
  den RUSE Mod Manager kopiert und liest, also gehen Ladereihenfolgen in beide Richtungen.
- **Er aktualisiert sich selbst:** ab dieser Version sagt eine Leiste, wenn ein neuerer Launcher da ist;
  **Jetzt aktualisieren** lädt ihn herunter, prüft seine SHA-256 und installiert ihn, und der Launcher startet von
  selbst neu.

Deine Mod-Sets aus 0.1 bleiben erhalten. Probleme und Ideen: GitHub Issues.

![RUSE Launcher](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/launcher.jpg)
