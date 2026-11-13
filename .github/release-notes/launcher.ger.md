**RUSE Launcher 0.4, für Spieler.** Er findet R.U.S.E. über Steam, und **Spielen** baut eine gemoddete Kopie des
Spiels mit deinen Mods und startet sie. Deine Steam-Installation wird nie verändert.

**0.4.8.20:** Schutz an Stellen, an denen manche Mod-Sets das Spiel anhielten; ein Upgrade aus einem anderen Gebäude behält seine Einheit; der Set-Editor sagt warum; Bug Watch sagt, warum ein Build oder ein Spielen fehlschlug; ein eigener Soldat für einen Trupp, in Blender geändert (Studio); Mods mit den neuen Trupps und Animationen des Studios; eine Einheit ohne Kartenbild wird beim Build abgelehnt.

- **Schutz, wo Mods das Spiel anhielten:** Mit dem R.U.S.E. Field Manual und der Balance Overhaul Mod zusammen hielt das Spiel an, sobald die Panzerbasis gesetzt wurde (Absturzberichte von Spielern). Jedes gemoddete Spiel hat jetzt einen Schutz an drei Stellen, an denen die Skripte des Spiels selbst es anhielten: Forschungskarten in der Liste eines Gebäudes für eine Einheit, die in einem anderen Gebäude ist, eine Mission, die den Computerspieler einer Seite startet, die ein Mensch spielt, und eine Mission, die Einheiten umwandelt, nachdem eine davon zerstört wurde. Ein Schutz greift nur dort ein, wo das Spiel sonst angehalten hätte. Im Spiel mit der Panzerbasis getestet; die beiden Schutzstellen der Missionen wurden außerhalb des Spiels getestet.
- **Ein Upgrade aus einem anderen Gebäude behält seine Einheit:** Mit denselben zwei Mods nahm die Erforschung des T-34 in der Panzerbasis den T-26 aus der Kaserne, weil das Spiel eine Einheit wegnimmt, sobald irgendein Upgrade von ihr erforscht ist, egal wo es gebaut wird. Der Build macht ein solches Upgrade jetzt zu einer eigenen Forschung und sagt das in einer Warnung. Im Spiel mit der UdSSR und Italien getestet. Es ändert manche Sets mit der Balance Overhaul Mod und Sets mit dem Field Manual vor der Balanced Realism Mod; die Warnung nennt jede Einheit.
- **Beitrittscodes:** Ein Set, das der Build so ändert, bekommt einen neuen Beitrittscode: Jeder Spieler eines Gefechts damit braucht diese Version. Jedes andere Set behält seinen Code. Nach dem Update baut das nächste **Spielen** oder **Im Spiel testen** das Spiel von selbst neu.
- **Der Set-Editor des Launchers sagt warum:** Wenn er ein Set nicht erstellen oder speichern kann (keine Mod angehakt oder eine Mod, die nicht mehr in der Bibliothek ist), sagt er das jetzt im Editor, unter seinen Knöpfen. Vorher ging die Meldung auf die Seite des Sets, verdeckt vom Editor, und es schien nichts zu passieren. **Erstellen** und **Speichern** warten, bis eine Mod angehakt ist. In einer Vorschau des Bildschirms ausprobiert, noch nicht im installierten Launcher.
- **Eigene Missionen (Studio):** Die Mission einer neuen Karte, die Einheiten einer Nation erzeugt, die die kopierte Mission nicht lädt, bekommt jetzt die Pakete dieser Nation, sodass diese Einheiten ihre Modelle haben (das Spiel hielt an, wenn eine solche Einheit erzeugt wurde). Die Missionsprüfung lehnt außerdem ein Ereignis ab, das eine von einem Menschen gespielte Seite dem Computer übergibt. Durch Lesen eines echten Builds geprüft; noch nicht im Spiel ausprobiert.
- **Ein eigener Soldat für einen Trupp (Studio):** Die Seite eines Trupps bekommt **Eigenes Modell** mit **In Blender ändern**: Der Soldat des Trupps öffnet sich in Blender auf seinen eigenen Knochen, und Blender bekommt einen Knopf **An das R.U.S.E. Studio senden**. **Modell zurückholen** übernimmt ihn auf den Knochen des Spielsoldaten, ganz ohne **Eigene Uniform**. **Modell importieren…** geht jetzt auch bei einer Einheit mit **Eigene Uniform**: Es nimmt die Kopie heraus, und **Modell der kopierten Einheit nutzen** holt sie mit einem Klick zurück. Punkte, die Blender ohne Knochen lässt, folgen dem Wurzelknochen, und die Seite sagt, wie viele es sind. Im Spiel getestet mit zwei US-Trupps, die so gemacht wurden (einer mit größerem Kopf, einer mit einem neuen, in Blender gewichteten Mesh); der Rest wurde außerhalb des Spiels geprüft.
- **Mods mit den neuen Trupps und Animationen des Studios (Launcher):** Dieser Launcher baut die Trupps eines Mods mit eigenen Soldaten und seine Einheiten mit eigenen Animationen; so ein Mod braucht ihn, denn ein älterer Launcher kann sie ihnen nicht geben. Ein Mod, dessen Trupps eigene Soldaten haben, bekommt dafür einen kleinen Spiel-Patch: einmal heruntergeladen und nur auf deine gemoddete Kopie angewendet, nie auf das Spiel in deinem Steam-Ordner. Noch nicht aus dem Launcher im Spiel ausprobiert.
- **Eine Einheit ohne Kartenbild (Studio und Launcher):** Eine Einheit, die in einem Baumenü gezeigt wird und kein Kartenbild hat, wird jetzt abgelehnt, wenn das Spiel gebaut wird, mit dem, was zu ändern ist. In einem Test hielt das Spiel mit so einer Einheit gleich beim Start an (eine Kopie des HQ-Lastwagens, in einem Baumenü gezeigt).
- **Bug Watch sagt warum, wenn du es angehakt hast:** welche Prüfung einen Build abgelehnt oder einen Fehler gefunden hat (ein fester Name aus unserem Code), wie weit ein **Spielen** oder **Im Spiel testen** kam, welche Mods aus unserer Liste an waren und wie viele eigene (nach Art gezählt, nie benannt), vor dem Start abgelehnte Spielen-Versuche, und angebotene, installierte oder fehlgeschlagene Updates. Nie die angezeigten Worte, ein Pfad oder was deine eigenen Mods enthalten. All das steht in der Vereinbarung, die du angenommen hast (Version 3), deshalb wird sie dir nicht noch einmal gezeigt.
- **Unverändert:** RUSE Guard, ein Spiel ohne Mods, die Kampagne und Gefechte gegen den Computer.

**0.4.8.19:** RUSE Guard: Ein mit einer Cheat-Mod gebautes Spiel spielt jetzt Mehrspieler- und Koop-Gefechte mit Spielern, die denselben Build haben. Noch nicht voll unterstützt und vielleicht noch fehlerhaft: Nutzung im Mehrspieler auf eigene Verantwortung.

- **Von einem Spieler gemeldet:** Zwei Freunde mit demselben Mod-Paket flogen aus jedem Mehrspieler-Gefecht, weil eine Mod darin (Infinite Supply Depot) als Cheat markiert ist. RUSE Guard behandelte jedes Spiel, das mit einem Cheat oder einem Testwerkzeug gebaut wurde, als reine Offline-Kopie: Es verließ jedes Mehrspieler- und Koop-Gefecht nach wenigen Sekunden und sah nie nach, wer sonst mitspielte.
- **Was wir geändert haben:** Eine Sekunde nach Beginn eines Mehrspieler- oder Koop-Gefechts teilt ein solches Spiel den Spielen der anderen Spieler jetzt mit, welcher Build es ist: ein kurzer Code aus der Spielversion und den Mods, nichts über dich. Nach etwa sieben Sekunden entscheidet es. Haben alle Spieler denselben Build (dieselbe Spielversion, dieselben Mods in derselben Reihenfolge, dieselben Mod-Versionen), zeigt es das auf dem Bildschirm an und das Gefecht geht weiter. Hat jemand einen anderen Build oder keine Mods, verlässt es das Gefecht wie bisher.
- **Ein Beitrittscode für diese Sets:** Im Launcher bekommt ein Mod-Set mit einer Cheat-Mod jetzt einen Beitrittscode wie jedes andere. Derselbe Code heißt derselbe Build: Vergleicht eure Codes, bevor ihr spielt.
- **Jeder Spieler braucht diese Version:** Das Spiel jedes Spielers im Gefecht muss mit Launcher 0.4.8.19 oder Studio 0.9.8.19 oder neuer gebaut sein. Nach dem Update baut das nächste **Spielen** oder **Im Spiel testen** es von selbst neu.
- **Noch nicht voll unterstützt:** Wir haben es im Spiel mit einem Spieler getestet, der allein ein Mehrspieler-Gefecht gegen den Computer gehostet hat, und außerhalb des Spiels mit 20 simulierten Gefechten mit bis zu vier Spielern. Zu zweit in einem echten Gefecht hat es noch niemand gespielt, es kann also noch Fehler haben: Nutze es im Mehrspieler auf eigene Verantwortung. Probier es aus und sag uns auf Discord oder GitHub, was passiert ist: welche RUSE-Guard-Meldung du gesehen hast und ob das Gefecht weiterging.
- **Unverändert:** ein ohne Cheats gebautes Spiel, das Gefecht gegen den Computer und die Kampagne.

**0.4.8.18:** Eine Korrektur hinter den Kulissen: die Prüfung einer gemoddeten Kopie listet ihre Funde auf jedem System in derselben Reihenfolge.

- **Hinter den Kulissen:** die Prüfung einer gemoddeten Kopie (welche Spieldateien sich nach dem Bauen geändert haben) listet ihre Funde jetzt unter Windows und Linux in derselben Reihenfolge. Was sie findet, ändert sich nicht.

**0.4.8.17:** Importierte Modelle stehen dort, wo die Einheit steht, ihre Türme und Propeller an ihrem eigenen Platz; eine Munition kann eine eigene Waffenklasse bekommen.

- **Ein notwendiges Update:** Ältere Versionen können nicht mehr verwendet werden. Beim Öffnen installiert die App es von selbst, und **Spielen** wartet, bis es installiert ist.
- **Mods mit importierten Modellen der neuen Art:** Das Studio passt das importierte Modell einer Einheit jetzt dort an, wo die Einheit steht, mit einem eigenen Skelett, sodass sich sein Turm dort dreht, wo der Turm auf dem Modell sitzt, und die Propeller eines Flugzeugs sich dort drehen, wo das Modell sie hat, so viele, wie es hat; auch Soldaten, die Mannschaft eines Geschützes und weitere Flugzeuge können eigene Modelle bekommen. Spiel solche Mods mit diesem Launcher oder einem neueren: Ein älterer gibt dem Modell das Skelett der kopierten Einheit, sodass sich sein Turm um den falschen Punkt dreht. Früher gemachte Mods spielen sich wie bisher. Im Spiel getestet auf Testkopien, die so gebaut sind, wie der Launcher baut; noch nicht über den Launcher selbst gespielt.
- **Eine eigene Waffenklasse für eine Munition:** Ein Mod kann einer Munition jetzt eigenen Schaden gegen jede Zielart geben (gemacht auf der Munitionsseite des Studios). Im Launcher hat sich dafür nichts geändert: Ein solcher Mod wird gebaut wie jeder andere.

**0.4.8.16:** Die Fehlersuche behält die Spielkopien, die du selbst gemacht hast.

- **Behoben: „Entfernen“ in der Fehlersuche löschte Kopien, die du selbst gemacht hast.** Eine von Hand gebaute Spielkopie im Kopienordner, eine Testkopie oder eine Referenzkopie galt als Überbleibsel, und „Entfernen“ löschte sie endgültig, nicht in den Papierkorb. Jede Kopie, die nicht die Mod-Kopie der App selbst ist, trägt jetzt einen kleinen Behalten-Vermerk, und eine Kopie mit Vermerk ist nie ein Überbleibsel: Die Fehlersuche entfernt nur die Überbleibsel der Apps selbst (halb gebaute Kopien und die, die ältere Versionen je Mod-Set anlegten). Aufgefallen am 1. November auf unserem eigenen PC, als dort jede Testkopie verschwand. Eine Kopie aus der Zeit vor dieser Version hat noch keinen Vermerk: Baue sie einmal mit dieser Version neu, oder lass „Entfernen“ bis dahin in Ruhe.

**0.4.8.15:** Auch Original bekommt den goldenen R.U.S.E. 2.0-Titel.

- **Auch Original bekommt den goldenen R.U.S.E. 2.0-Titel:** Spielen bei Original baut jetzt die Mod-Kopie ohne Mods und mit dem goldenen Titel und startet das Spiel daraus, so wie bei einem Mod-Set: Beim ersten Mal wird sie gebaut, danach startet es sofort, außer du hast dazwischen ein Mod-Set gespielt. RUSE Guard läuft in seinen Mehrspieler-Partien, wie bei jedem Set. Nimm in den Einstellungen das Häkchen beim goldenen Titel weg, und Original startet wie vorher über Steam. Deine Steam-Installation wird nie verändert.

**0.4.8.14:** Mods mit eigenem Partie-Skript werden wieder gebaut.

- **Behoben: Spielen brach bei manchen Mod-Sets ab** mit „RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...“: Einige Mods bringen ein eigenes Partie-Skript mit, dessen Kopf mehr Platz verlangt, als das Skript braucht (darunter 1 VS 7 AI, 1 VS 15 AI, Operation Overlord und Sand Box). Das Spiel führt diese Skripte problemlos aus, aber der Launcher lehnte sie ab, sodass kein Set mit einem dieser Mods gebaut werden konnte. Jetzt liest er sie so wie das Spiel.

**0.4.8.13:** Absturzberichte des Spiels sagen, was zum Absturz geführt hat.

- **Bug Watchs Absturzberichte des Spiels sagen mehr:** Wenn du Bug Watch angekreuzt hast und das Spiel abstürzt, sagt der Bericht jetzt auch, was das Spiel zu lesen oder zu schreiben versuchte, und bis zu 16 Stellen im Spiel, die zum Absturz geführt haben, gelesen aus dem eigenen Absturzbericht des Spiels auf deinem PC, der ihn weiterhin nie verlässt. Ein Bericht, der nur sagte, wo das Spiel stehen blieb, konnte nicht zeigen, warum; jetzt können wir Abstürze wie den, den uns ein Spieler diese Woche geschickt hat, zurückverfolgen und beheben.
- **Die Vereinbarung, Version 3:** Sie nennt jetzt diese zwei neuen Angaben unter dem, was ein Absturzbericht des Spiels enthält; sonst hat sich nichts geändert. Weil sie sich geändert hat, zeigen beide Apps sie dir beim Öffnen noch einmal.

**0.4.8.12:** Spielen baut gemoddete Spiele wieder.

- **Behoben: Spielen brach bei jedem Mod-Set ab** mit „No such file or directory: ...fairplay_watch.bin“: Den Installern von 0.4.8.10 und 0.4.8.11 fehlten drei Dateien von RUSE Guard, sodass kein gemoddetes Spiel gebaut werden konnte. Sie sind wieder dabei, und eine App, der eine ihrer Dateien fehlt, kann nicht mehr veröffentlicht werden.

**0.4.8.11:** die Anmeldung über Steam wird in den Apps abgeschlossen; unter Linux starten die Hilfsprogramme eines Builds so wie unter Windows.

- **Behoben: Anmeldung über Steam.** Nachdem du dich auf der Seite von Steam angemeldet hattest, warteten der Launcher und das Studio weiter und fragten unseren Server nie, ob du fertig bist: Das Fenster beendete seine eigenen Prüfungen vor der ersten. Jetzt prüft es alle paar Sekunden und meldet dich an, sobald Steam es bestätigt. In der Vorschau ausprobiert: Die Prüfung läuft, und das Fenster zeigt dich angemeldet.
- **Hilfsprogramme starten auf jedem System frisch:** Die Programme, auf die ein Build seine Arbeit verteilt (importierte Modelle, das Ausbessern der Karte, Bewegung, Wasser), starten jetzt auch unter Linux frisch, so wie sie es unter Windows schon immer tun. Unter Linux starteten sie als Kopien der laufenden App, was einen Build ab und zu hängen lassen konnte und dort eine unserer Prüfungen scheitern ließ. Unter Windows und unter Proton auf dem Steam Deck ändert sich nichts.

**0.4.8.10:** Mods über 4 GB, Baulisten in Gruppen, schnellere Builds großer Mods, Persisch und jede Seite in 11 Sprachen, Korrekturen aus Testerberichten; und RUSE Guard, unser Anti-Cheat für echte Mehrspieler-Gefechte, mit einem Beitrittscode; Bug Watch, Absturz- und Nutzungsberichte, die du einschalten kannst; die Anmeldung über Steam; und eine Vereinbarung beim ersten Start.

- **Behoben, von einem Spieler gemeldet: Mods über 4 GB.** Ein Mod-Set, dessen gemoddetes Spiel 4 GB überschritt, ließ sich mit Spielen nicht mehr bauen („'I' format requires 0 <= number <= 4294967295“). Pakete tragen jetzt ihre volle Länge, und eines über 4 GB wird in einem breiteren Aufbau geschrieben, den das Spiel mit einem kleinen Spiel-Patch lesen kann: einmal heruntergeladen und nur auf deine gemoddete Kopie angewendet, nie auf das Spiel in deinem Steam-Ordner. Über 32 GB oder bei einer einzelnen Datei über 4 GB sagt der Build es klar. Im Spiel getestet: Kopien über 4 GB und mit 200, 283 und allen 366 Einheiten aus anderen Epochen.
- **Viele eigene Modelle:** Das Spiel findet die Ersatztexturen eines Pakets über einen Index, und ein Build, der welche für importierte Modelle hinzufügte, schrieb ihn falsch: Mit vielen Einheiten aus anderen Epochen hing das Spiel beim Laden oder stürzte ab. Jetzt wird er so geschrieben, wie das Spiel ihn liest, für jeden Mod, der welche hinzufügt. Im Spiel getestet mit allen 366 Einheiten aus anderen Epochen.
- **Baulisten in Gruppen:** Ein Mod mit vielen Einheiten bekommt die Bauliste jedes Gebäudes in Gruppen, die eigenen Linien des Spiels: höchstens 6 Einheiten pro Gruppe und 10 Gruppen pro Gebäude, damit die ganze Liste auf dem Bildschirm bleibt und jede Einheit gebaut werden kann. Ein früher gemachter Mod über diesen Grenzen wird trotzdem gebaut, mit einer Warnung. Im Spiel getestet mit 297 Einheiten aus anderen Epochen in Gruppen.
- **Schnellere Builds:** Die Modelle in deinen Mods werden zwischen Builds aufbewahrt, und neue werden nebeneinander auf den Kernen deines PCs erstellt. Ein Mod mit 366 Einheiten aus anderen Epochen brauchte auf einem PC mit 8 Kernen etwa 18 Minuten zum Bauen; jetzt etwa 5 beim ersten Mal und etwa 3 danach, mit denselben Spieldateien, Byte für Byte.
- **Testerberichte:** Ein Einheiten-Mod und Kartenänderungen unter einem Namen werden zusammen gebaut (sie stoppten Spielen); eine Karte, deren eigene Brücken entfernt sind, wird mit den neuen Brücken gebaut; importierte Turmteile und gezogene Geschütze werden so gebaut, wie Studio 0.9.8.10 sie macht. Die Brücken und Turmteile noch nicht im Spiel ausprobiert.
- **Deine Dateien:** Entfernen schickt einen Mod der Bibliothek in den Papierkorb, Im Ordner zeigen öffnet einen Mod dort, wo er liegt, und die Einstellungen zeigen, wo deine Dateien aufbewahrt werden. In einer Vorschau gesehen; noch nicht im App-Fenster ausprobiert.
- **Persisch und 11 Sprachen:** Persisch ist die 11. Sprache der Apps, von rechts nach links geschrieben; das README, das Wiki, diese Hinweise und die Setup-Bildschirme gibt es in allen 11.
- **Pflicht-Updates:** Ein Update, das wir als Pflicht markieren, installiert sich selbst, mit einem Fenster, das niemand schließen kann (Apps ab dieser Version können die Markierung lesen).
- **Nur eigene Kopien:** Bevor Spielen eine gemoddete Kopie baut, prüfen die Apps, ob der Spielordner eine Kopie ist, die dir gehört, anhand dessen, was Steam dort hinterlassen hat, unter Windows, unter Proton auf dem Steam Deck und unter Linux. Kann deine nicht bestätigt werden (eine Box-Version aus der Zeit, bevor R.U.S.E. auf Steam war), lässt dich ein Fenster ein Ticket öffnen, und wir schicken dir einen Freischaltcode für diesen PC.
- **Discord:** Die Apps und Seiten nutzen eine neue Einladung, die nicht abläuft.
- **Eine Vereinbarung beim ersten Start:** wenn das Studio oder der Launcher zum ersten Mal öffnet, sagt er, was RUSE Guard tut, und bittet dich, es anzunehmen (zum Online-Spielen mit den Apps ist das nötig), ob Bug Watch eingeschaltet werden soll (freiwillig), und um einen Benutzernamen, den unsere Entwickler bei deinen Berichten sehen: ein # und vier Ziffern kommen dazu, damit er eindeutig ist, etwa Nick#4821. Ein Name gilt für beide Apps. Die Vereinbarung erscheint wieder, wenn sie sich ändert. In beiden Apps gesehen. In allen 11 Sprachen.
- **RUSE Guard:** unser Anti-Cheat, nach DomesticNukes' Entwurf. Er arbeitet nur in Mehrspieler- und Koop-Gefechten, nie im Einzelspieler, im Gefecht gegen den Computer oder in der Kampagne. Dein Mod-Spiel bekommt einen **Beitrittscode** für die Leute, mit denen du spielst: derselbe Code heißt dasselbe Spiel, dieselbe Version, dieselben Mods und Mod-Versionen, damit ein Gefecht nicht auseinanderlaufen kann. Eine Mod, die die Skripte des Spiels ändert, zeigt das Abzeichen **Führt Skripte aus**, und Spielen wartet, bis du ankreuzt, dass du ihrem Autor vertraust; ein Cheat oder ein Testwerkzeug zeigt **Cheat** und macht die Kopie zur reinen Offline-Kopie: sie verlässt Mehrspieler- und Koop-Gefechte von selbst. Während eines echten Gefechts vergleicht RUSE Guard die Namen deiner laufenden Programme mit einer Liste bekannter Cheat-Werkzeuge (nur die Namen; sonst wird nichts gelesen), und was er sammelt, wird unter deinem Benutzernamen abgelegt, nie unter deinem Steam-Konto. In Mehrspieler-Gefechten gegen einen echten Gegner getestet; die Belege erreichen unseren Server.
- **Bug Watch (freiwillig):** wenn du es ankreuzt, zählen Studio und Launcher, was du benutzt und wann etwas schiefgeht, die Abstürze der Apps und die des Spiels, mit den Mods, die an waren, und schicken es einmal am Tag mit deinem Benutzernamen an unsere Entwickler. Keine echten Namen, kein Steam-Konto, keine Dateien. Aus, solange du es nicht ankreuzt; kreuze es jederzeit ab, und was aufbewahrt war, wird gelöscht. In beiden Apps gesehen.
- **Über Steam anmelden:** eine Anmeldung auf Steams eigener Seite in deinem Browser bestätigt, dass du R.U.S.E. besitzt, für Online-Spiele, RUSE Guard und Inhalts-Downloads. Wir sehen nie dein Passwort, und deine Steam-ID wird nie gespeichert: nur ein Pass, der 30 Tage auf deinem PC bleibt. Es steht in den Einstellungen unter **Steam-Anmeldung**; der Launcher fragt einmal. Noch braucht es nichts. In der App noch nicht ausprobiert.

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
