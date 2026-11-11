**RUSE Studio, eine Vorschau für Modder.** Durchsuche die Einheiten des Spiels in jeder seiner zehn Sprachen, ändere
sie in einem eigenen Mod und teste ihn im Spiel. Deine Steam-Installation wird nie verändert.

**0.9.8.20:** Schutz an Stellen, an denen manche Mod-Sets das Spiel anhielten; ein Upgrade aus einem anderen Gebäude behält seine Einheit; der Set-Editor sagt warum; Bug Watch sagt, warum ein Build oder ein Spielen fehlschlug; ein eigener Soldat für einen Trupp, in Blender geändert (Studio).

- **Schutz, wo Mods das Spiel anhielten:** Mit dem R.U.S.E. Field Manual und der Balance Overhaul Mod zusammen hielt das Spiel an, sobald die Panzerbasis gesetzt wurde (Absturzberichte von Spielern). Jedes gemoddete Spiel hat jetzt einen Schutz an drei Stellen, an denen die Skripte des Spiels selbst es anhielten: Forschungskarten in der Liste eines Gebäudes für eine Einheit, die in einem anderen Gebäude ist, eine Mission, die den Computerspieler einer Seite startet, die ein Mensch spielt, und eine Mission, die Einheiten umwandelt, nachdem eine davon zerstört wurde. Ein Schutz greift nur dort ein, wo das Spiel sonst angehalten hätte. Im Spiel mit der Panzerbasis getestet; die beiden Schutzstellen der Missionen wurden außerhalb des Spiels getestet.
- **Ein Upgrade aus einem anderen Gebäude behält seine Einheit:** Mit denselben zwei Mods nahm die Erforschung des T-34 in der Panzerbasis den T-26 aus der Kaserne, weil das Spiel eine Einheit wegnimmt, sobald irgendein Upgrade von ihr erforscht ist, egal wo es gebaut wird. Der Build macht ein solches Upgrade jetzt zu einer eigenen Forschung und sagt das in einer Warnung. Im Spiel mit der UdSSR und Italien getestet. Es ändert manche Sets mit der Balance Overhaul Mod und Sets mit dem Field Manual vor der Balanced Realism Mod; die Warnung nennt jede Einheit.
- **Beitrittscodes:** Ein Set, das der Build so ändert, bekommt einen neuen Beitrittscode: Jeder Spieler eines Gefechts damit braucht diese Version. Jedes andere Set behält seinen Code. Nach dem Update baut das nächste **Spielen** oder **Im Spiel testen** das Spiel von selbst neu.
- **Der Set-Editor des Launchers sagt warum:** Wenn er ein Set nicht erstellen oder speichern kann (keine Mod angehakt oder eine Mod, die nicht mehr in der Bibliothek ist), sagt er das jetzt im Editor, unter seinen Knöpfen. Vorher ging die Meldung auf die Seite des Sets, verdeckt vom Editor, und es schien nichts zu passieren. **Erstellen** und **Speichern** warten, bis eine Mod angehakt ist. In einer Vorschau des Bildschirms ausprobiert, noch nicht im installierten Launcher.
- **Eigene Missionen (Studio):** Die Mission einer neuen Karte, die Einheiten einer Nation erzeugt, die die kopierte Mission nicht lädt, bekommt jetzt die Pakete dieser Nation, sodass diese Einheiten ihre Modelle haben (das Spiel hielt an, wenn eine solche Einheit erzeugt wurde). Die Missionsprüfung lehnt außerdem ein Ereignis ab, das eine von einem Menschen gespielte Seite dem Computer übergibt. Durch Lesen eines echten Builds geprüft; noch nicht im Spiel ausprobiert.
- **Ein eigener Soldat für einen Trupp (Studio):** Die Seite eines Trupps bekommt **Eigenes Modell** mit **In Blender ändern**: Der Soldat des Trupps öffnet sich in Blender auf seinen eigenen Knochen, und Blender bekommt einen Knopf **An das R.U.S.E. Studio senden**. **Modell zurückholen** übernimmt ihn auf den Knochen des Spielsoldaten, ganz ohne **Eigene Uniform**. **Modell importieren…** geht jetzt auch bei einer Einheit mit **Eigene Uniform**: Es nimmt die Kopie heraus, und **Modell der kopierten Einheit nutzen** holt sie mit einem Klick zurück. Punkte, die Blender ohne Knochen lässt, folgen dem Wurzelknochen, und die Seite sagt, wie viele es sind. Im Spiel getestet mit zwei US-Trupps, die so gemacht wurden (einer mit größerem Kopf, einer mit einem neuen, in Blender gewichteten Mesh); der Rest wurde außerhalb des Spiels geprüft.
- **Bug Watch sagt warum, wenn du es angehakt hast:** welche Prüfung einen Build abgelehnt oder einen Fehler gefunden hat (ein fester Name aus unserem Code), wie weit ein **Spielen** oder **Im Spiel testen** kam, welche Mods aus unserer Liste an waren und wie viele eigene (nach Art gezählt, nie benannt), vor dem Start abgelehnte Spielen-Versuche, und angebotene, installierte oder fehlgeschlagene Updates. Nie die angezeigten Worte, ein Pfad oder was deine eigenen Mods enthalten. All das steht in der Vereinbarung, die du angenommen hast (Version 3), deshalb wird sie dir nicht noch einmal gezeigt.
- **Unverändert:** RUSE Guard, ein Spiel ohne Mods, die Kampagne und Gefechte gegen den Computer.

**0.9.8.19:** RUSE Guard: Ein mit einer Cheat-Mod gebautes Spiel spielt jetzt Mehrspieler- und Koop-Gefechte mit Spielern, die denselben Build haben. Noch nicht voll unterstützt und vielleicht noch fehlerhaft: Nutzung im Mehrspieler auf eigene Verantwortung.

- **Von einem Spieler gemeldet:** Zwei Freunde mit demselben Mod-Paket flogen aus jedem Mehrspieler-Gefecht, weil eine Mod darin (Infinite Supply Depot) als Cheat markiert ist. RUSE Guard behandelte jedes Spiel, das mit einem Cheat oder einem Testwerkzeug gebaut wurde, als reine Offline-Kopie: Es verließ jedes Mehrspieler- und Koop-Gefecht nach wenigen Sekunden und sah nie nach, wer sonst mitspielte.
- **Was wir geändert haben:** Eine Sekunde nach Beginn eines Mehrspieler- oder Koop-Gefechts teilt ein solches Spiel den Spielen der anderen Spieler jetzt mit, welcher Build es ist: ein kurzer Code aus der Spielversion und den Mods, nichts über dich. Nach etwa sieben Sekunden entscheidet es. Haben alle Spieler denselben Build (dieselbe Spielversion, dieselben Mods in derselben Reihenfolge, dieselben Mod-Versionen), zeigt es das auf dem Bildschirm an und das Gefecht geht weiter. Hat jemand einen anderen Build oder keine Mods, verlässt es das Gefecht wie bisher.
- **Ein Beitrittscode für diese Sets:** Im Launcher bekommt ein Mod-Set mit einer Cheat-Mod jetzt einen Beitrittscode wie jedes andere. Derselbe Code heißt derselbe Build: Vergleicht eure Codes, bevor ihr spielt.
- **Jeder Spieler braucht diese Version:** Das Spiel jedes Spielers im Gefecht muss mit Launcher 0.4.8.19 oder Studio 0.9.8.19 oder neuer gebaut sein. Nach dem Update baut das nächste **Spielen** oder **Im Spiel testen** es von selbst neu.
- **Noch nicht voll unterstützt:** Wir haben es im Spiel mit einem Spieler getestet, der allein ein Mehrspieler-Gefecht gegen den Computer gehostet hat, und außerhalb des Spiels mit 20 simulierten Gefechten mit bis zu vier Spielern. Zu zweit in einem echten Gefecht hat es noch niemand gespielt, es kann also noch Fehler haben: Nutze es im Mehrspieler auf eigene Verantwortung. Probier es aus und sag uns auf Discord oder GitHub, was passiert ist: welche RUSE-Guard-Meldung du gesehen hast und ob das Gefecht weiterging.
- **Unverändert:** ein ohne Cheats gebautes Spiel, das Gefecht gegen den Computer und die Kampagne.

**0.9.8.18:** Eine Korrektur hinter den Kulissen: die Prüfung einer gemoddeten Kopie listet ihre Funde auf jedem System in derselben Reihenfolge.

- **Hinter den Kulissen:** die Prüfung einer gemoddeten Kopie (welche Spieldateien sich nach dem Bauen geändert haben) listet ihre Funde jetzt unter Windows und Linux in derselben Reihenfolge. Was sie findet, ändert sich nicht.

**0.9.8.17:** Importierte Modelle stehen dort, wo die Einheit steht, ihre Türme und Propeller an ihrem eigenen Platz; eine Munition kann eine eigene Waffenklasse bekommen.

- **Ein notwendiges Update:** Ältere Versionen können nicht mehr verwendet werden. Beim Öffnen installiert die App es von selbst, und **Im Spiel testen** wartet, bis es installiert ist.
- **Importierte Modelle stehen dort, wo die Einheit steht** (Bericht eines Modders: Modelle wurden vor ihrem Auswahlring gezeichnet): **Modell importieren…** setzt ein neues Modell jetzt in die Mitte der Einheit, die es kopiert, und gibt ihm ein eigenes Skelett, sodass sein Turm sich dort dreht, wo der Turm auf deinem Modell sitzt. Jeder neue Import wird so angepasst. Ein früher importiertes Modell behält seinen alten Platz, bis du es neu importierst oder verschiebst (siehe unten), und die Einheiten aus anderen Epochen behalten ihren. Im Spiel getestet mit dem Sherman des Spiels, in Blender geöffnet und zurückgeholt, auf anderen Einheiten; noch nicht mit einem Modell von anderswo, einem anderen Turmpanzer oder einem Turm, der sich ganz herumdreht.
- **Verschieben:** Sitzt ein Modell noch nicht richtig, öffne **Verschieben** unter seiner Größe auf der Seite der Einheit (eingeklappt, bis du es brauchst; bei einem verschobenen Modell bleibt es offen). **Vor**, **Rechts** und **Hoch** verschieben es von der angepassten Stelle aus, in Spieleinheiten (die Seite sagt, wie lang die kopierte Einheit darin ist); ein Minus geht in die andere Richtung, und 0, 0, 0 setzt es zurück. Turm und Propeller gehen mit, drehen sich also weiter an der richtigen Stelle, und eine neue Größe behält die Verschiebung. In der 3D-Ansicht zeigt ein blauer Ring, wo die Einheit steht, seine Markierung vorne. Ein Modell, das an den Knochen der Einheit hängt, bleibt, wo seine Knochen sind: Verschiebe es in Blender. Auf der Kommandozeile: `ruse import-model ... --move F R U`. Im Spiel getestet mit Panzern, die nach vorn, hinten, rechts und oben verschoben wurden.
- **Flugzeuge behalten ihre eigenen Propeller:** Ein Flugzeug, das aus dem Studio in Blender geöffnet und mit **Modell importieren…** zurückgeholt wird, behält seine Propeller dort, wo dein Modell sie hat, so viele, wie es hat, egal was das kopierte Flugzeug hatte: Blätter am Boden, drehende Scheiben in der Luft. In der 3D-Ansicht sind die Scheiben eines Flugzeugs jetzt durchsichtig, so wie das Spiel einen drehenden Propeller zeichnet. Im Spiel getestet: das Modell eines dreimotorigen Bombers auf einer Kopie eines einmotorigen Jägers und umgekehrt. Ein Flugzeugmodell von anderswo behält seine Propeller so, wie es sie zeichnet, still stehend: Der Importer erkennt noch nicht, welche seiner Teile Propeller sind.
- **Jede Einheit kann ein Modell bekommen:** Soldaten, die Mannschaft eines Geschützes und Flugzeuge, an die das Studio bisher kein Modell anpassen konnte (etwa die P-47), bekommen jetzt auch ein eigenes, eines, das an den eigenen Knochen der Einheit hängt (zum Beispiel ein Modell des Spiels, aus dem Studio in Blender geöffnet und dort geändert). Es behält diese Knochen und wird so verwendet, wie es ist, und die anderen Männer eines Trupps mit denselben Knochen tragen es auch. Im Spiel getestet: ein Schützentrupp, die Mannschaft eines Geschützes und die P-47; noch nicht ein Modell von anderswo.
- **Spiel sie mit dem Launcher dieses Updates:** Ein Mod mit einem Modell, das mit dieser Version importiert wurde, braucht den Launcher dieses Updates oder einen neueren, für dich und deine Spieler: Ein älterer Launcher gibt dem Modell das Skelett der kopierten Einheit, sodass sich sein Turm um den falschen Punkt dreht. Mods mit früher importierten Modellen spielen sich wie bisher.
- **Neue Waffenklasse** (auf der Seite einer Munition): Der Kasten **Waffenklasse** legt fest, wie viel ihres Schadens eine Munition jeder Zielart zufügt. **Neue Waffenklasse…** öffnet je eine Zahl: Gebäude und Befestigungen, Flugzeuge, Fallschirmjäger im Sprung, Infanterie, leichte Fahrzeuge, Panzerung 1 bis 5 und Baufahrzeuge. 1 ist voller Schaden, 2 das Doppelte, 0,5 die Hälfte, und 0 heißt, sie kann dieses Ziel gar nicht angreifen. **Klasse speichern** gibt der Munition ihre eigene Kopie der Schadenstabelle des Spiels, sodass sich der Schaden keiner anderen Munition ändert; wie jede Änderung an einer Munition gilt sie für jede Einheit, die sie verschießt (für nur eine Einheit kopiere zuerst die Munition). **Zurück zur Klasse des Spiels** nimmt die Kopie heraus, und das Löschen einer kopierten Munition nimmt ihre Klasse mit. Im Spiel getestet: Schützentrupps, deren Munition Zahlen gegen Panzer bekam, schossen mit ihren Gewehren auf Panzer und beschädigten sie. In einer Vorschau gesehen; im App-Fenster noch nicht angeklickt.

**0.9.8.16:** Die Fehlersuche behält die Spielkopien, die du selbst gemacht hast.

- **Behoben: „Entfernen“ in der Fehlersuche löschte Kopien, die du selbst gemacht hast:** dieselbe Korrektur wie im Launcher (ein Code für beide Apps). Eine von Hand gebaute Spielkopie im Kopienordner, eine Testkopie oder eine Referenzkopie galt als Überbleibsel und wurde endgültig gelöscht. Jede solche Kopie trägt jetzt einen kleinen Behalten-Vermerk, und eine Kopie mit Vermerk ist nie ein Überbleibsel: Entfernt werden nur die Überbleibsel der Apps selbst (halb gebaute Kopien und die, die ältere Versionen je Mod-Set anlegten). Eine Kopie aus der Zeit vor dieser Version hat noch keinen Vermerk: Baue sie einmal mit dieser Version neu, oder lass „Entfernen“ bis dahin in Ruhe.

**0.9.8.15:** Auch Original bekommt den goldenen R.U.S.E. 2.0-Titel.

- **Im Studio selbst ändert sich nichts:** Dieses Update ist das des Launchers (Original bekommt den goldenen R.U.S.E. 2.0-Titel). Das Häkchen für den goldenen Titel in den Einstellungen des Studios ist dieselbe Einstellung wie im Launcher; nimmst du es hier weg, startet Original auch über Steam.

**0.9.8.14:** Mods mit eigenem Partie-Skript werden wieder gebaut.

- **Behoben: Im Spiel testen brach bei manchen Mods ab** mit „RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...“: Einige Mods bringen ein eigenes Partie-Skript mit, dessen Kopf mehr Platz verlangt, als das Skript braucht (darunter 1 VS 7 AI, 1 VS 15 AI, Operation Overlord und Sand Box). Das Spiel führt diese Skripte problemlos aus, aber das Studio lehnte sie ab, sodass nichts mit einem dieser Mods gebaut werden konnte. Jetzt liest es sie so wie das Spiel.

**0.9.8.13:** Absturzberichte des Spiels sagen, was zum Absturz geführt hat.

- **Bug Watchs Absturzberichte des Spiels sagen mehr:** Wenn du Bug Watch angekreuzt hast und das Spiel abstürzt, sagt der Bericht jetzt auch, was das Spiel zu lesen oder zu schreiben versuchte, und bis zu 16 Stellen im Spiel, die zum Absturz geführt haben, gelesen aus dem eigenen Absturzbericht des Spiels auf deinem PC, der ihn weiterhin nie verlässt. Ein Bericht, der nur sagte, wo das Spiel stehen blieb, konnte nicht zeigen, warum; jetzt können wir Abstürze wie den, den uns ein Spieler diese Woche geschickt hat, zurückverfolgen und beheben.
- **Die Vereinbarung, Version 3:** Sie nennt jetzt diese zwei neuen Angaben unter dem, was ein Absturzbericht des Spiels enthält; sonst hat sich nichts geändert. Weil sie sich geändert hat, zeigen beide Apps sie dir beim Öffnen noch einmal.

**0.9.8.12:** Im Spiel testen baut gemoddete Spiele wieder.

- **Behoben: Im Spiel testen brach bei jedem Mod ab** mit „No such file or directory: ...fairplay_watch.bin“: Den Installern von 0.9.8.10 und 0.9.8.11 fehlten drei Dateien von RUSE Guard, sodass kein gemoddetes Spiel gebaut werden konnte. Sie sind wieder dabei, und eine App, der eine ihrer Dateien fehlt, kann nicht mehr veröffentlicht werden.

**0.9.8.11:** die Anmeldung über Steam wird in den Apps abgeschlossen; unter Linux starten die Hilfsprogramme eines Builds so wie unter Windows.

- **Behoben: Anmeldung über Steam.** Nachdem du dich auf der Seite von Steam angemeldet hattest, warteten der Launcher und das Studio weiter und fragten unseren Server nie, ob du fertig bist: Das Fenster beendete seine eigenen Prüfungen vor der ersten. Jetzt prüft es alle paar Sekunden und meldet dich an, sobald Steam es bestätigt. In der Vorschau ausprobiert: Die Prüfung läuft, und das Fenster zeigt dich angemeldet.
- **Hilfsprogramme starten auf jedem System frisch:** Die Programme, auf die ein Build seine Arbeit verteilt (importierte Modelle, das Ausbessern der Karte, Bewegung, Wasser, das Gelände der Kartenansicht), starten jetzt auch unter Linux frisch, so wie sie es unter Windows schon immer tun. Unter Linux starteten sie als Kopien der laufenden App, was einen Build ab und zu hängen lassen konnte und dort eine unserer Prüfungen scheitern ließ. Unter Windows und unter Proton auf dem Steam Deck ändert sich nichts.

**0.9.8.10:** Mods über 4 GB, Baulisten in Gruppen, schnellere Builds großer Mods, deine Dateien in Documents\RUSE 2.0, Persisch und jede Seite in 11 Sprachen, Korrekturen aus Testerberichten; und RUSE Guard, unser Anti-Cheat für echte Mehrspieler-Gefechte; Bug Watch, Absturz- und Nutzungsberichte, die du einschalten kannst; die Anmeldung über Steam; und eine Vereinbarung beim ersten Start.

- **Behoben, von einem Spieler gemeldet: Mods über 4 GB.** Ein gemoddetes Spiel, dessen Pakete 4 GB überschritten, ließ sich nicht mehr bauen („'I' format requires 0 <= number <= 4294967295“). Pakete tragen jetzt ihre volle Länge, und eines über 4 GB wird in einem breiteren Aufbau geschrieben, den das Spiel mit einem kleinen Spiel-Patch lesen kann: einmal heruntergeladen und nur auf deine gemoddete Kopie angewendet, nie auf das Spiel in deinem Steam-Ordner. Über 32 GB oder bei einer einzelnen Datei über 4 GB sagt der Build es klar. Im Spiel getestet: Kopien über 4 GB und mit 200, 283 und allen 366 Einheiten aus anderen Epochen.
- **Viele eigene Modelle:** Das Spiel findet die Ersatztexturen eines Pakets über einen Index, und ein Build, der welche für importierte Modelle hinzufügte, schrieb ihn falsch: Mit vielen Einheiten aus anderen Epochen hing das Spiel beim Laden oder stürzte ab. Jetzt wird er so geschrieben, wie das Spiel ihn liest, für jeden Mod, der welche hinzufügt. Im Spiel getestet mit allen 366 Einheiten aus anderen Epochen.
- **Baulisten in Gruppen:** Mit vielen Einheiten lief die Bauliste eines Gebäudes über den Bildschirm hinaus, und die Einheiten darunter waren nicht erreichbar. Jede Liste zeigt jetzt eine Zeile pro Gruppe, die eigenen Linien des Spiels (eine neue Einheit kommt in die Gruppe ihrer Art): höchstens 6 Einheiten pro Gruppe und 10 Gruppen pro Gebäude, damit die ganze Liste auf dem Bildschirm bleibt. Das Studio sagt, warum, wenn eine Gruppe voll ist, und zeigt die Gruppen dort, wo du Einheiten hinzufügst; ein früher gemachter Mod über diesen Grenzen wird trotzdem gebaut, mit einer Warnung. Im Spiel getestet mit 297 Einheiten aus anderen Epochen in Gruppen.
- **Schnellere Builds:** Die Modelle, die du importierst, werden zwischen Builds aufbewahrt, und neue werden nebeneinander auf den Kernen deines PCs erstellt. Ein Mod mit 366 Einheiten aus anderen Epochen brauchte auf einem PC mit 8 Kernen etwa 18 Minuten zum Bauen; jetzt etwa 5 beim ersten Mal und etwa 3 danach, mit denselben Spieldateien, Byte für Byte.
- **Importierte Modelle (Testerberichte):** Ein Turmteil an einem Knochen, den das kopierte Aussehen nicht aufführt (ein M109, kopiert vom M7 Priest), stoppte den Import; jetzt kommt er auf die eigene Liste der Kopie. Ein Turmteil an einem Modell ohne Turm (die P-40, der M274 Mule) fährt mit der Wanne mit, ein gezogenes Geschütz zeigt von weitem sein eigenes Modell, und eine dünne Streifentextur bekommt ihre Ersatztextur. Die gezogenen Geschütze im Spiel getestet; die Turmteile noch nicht genau angesehen.
- **Brücken (ein Testerbericht):** ein einziger Reiter Brücken: eine neue Brücke, deine Brücken (jede mit Hin und Löschen) und die eigenen Brücken der Karte mit ihren Übergängen, mit einem Knopf entfernt oder zurückgesetzt. Eine neue Brücke zählt, wenn das Entfernen der alten die Karte in zwei Teile schneidet, und das Formen des Geländes hält die Enden der eigenen Brücken der Karte auf ihrer Höhe. Entfernen ist leichter zu finden (Malen & Entfernen oder die Taste X). Ein Einheiten-Mod und Kartenänderungen unter einem Namen werden zusammen gebaut, und die Kartenansicht zeigt wieder die Modelle des Spiels. Noch nicht im Spiel ausprobiert.
- **Deine Dateien in Documents\RUSE 2.0:** Deine Mods, Karten, Exporte und Sicherungen kommen in Documents\RUSE 2.0, wo der Datei-Explorer sie zeigt; was das Studio in seinem alten Ordner hatte, wird einmal dorthin verschoben, und es sagt das. Mod löschen… schickt einen Mod in den Papierkorb, Ordner dieses Mods zeigen öffnet ihn, und die Einstellungen zeigen, wo alles liegt. In einer Vorschau gesehen; noch nicht in den App-Fenstern ausprobiert.
- **Persisch und 11 Sprachen:** Persisch ist die 11. Sprache der Apps, von rechts nach links geschrieben; das README, das Wiki, diese Hinweise und die Setup-Bildschirme gibt es in allen 11.
- **Pflicht-Updates:** Ein Update, das wir als Pflicht markieren, installiert sich selbst, mit einem Fenster, das niemand schließen kann (Apps ab dieser Version können die Markierung lesen). Das Fenster Neuerungen behält seine Höhe, während du darin scrollst.
- **Nur eigene Kopien:** Bevor Spielen oder Im Spiel testen eine gemoddete Kopie baut, prüfen die Apps, ob der Spielordner eine Kopie ist, die dir gehört, anhand dessen, was Steam dort hinterlassen hat, unter Windows, unter Proton auf dem Steam Deck und unter Linux. Kann deine nicht bestätigt werden (eine Box-Version aus der Zeit, bevor R.U.S.E. auf Steam war), lässt dich ein Fenster ein Ticket öffnen, und wir schicken dir einen Freischaltcode für diesen PC.
- **Discord:** Die Apps und Seiten nutzen eine neue Einladung, die nicht abläuft.
- **Eine Vereinbarung beim ersten Start:** wenn das Studio oder der Launcher zum ersten Mal öffnet, sagt er, was RUSE Guard tut, und bittet dich, es anzunehmen (zum Online-Spielen mit den Apps ist das nötig), ob Bug Watch eingeschaltet werden soll (freiwillig), und um einen Benutzernamen, den unsere Entwickler bei deinen Berichten sehen: ein # und vier Ziffern kommen dazu, damit er eindeutig ist, etwa Nick#4821. Ein Name gilt für beide Apps. Die Vereinbarung erscheint wieder, wenn sie sich ändert. In beiden Apps gesehen. In allen 11 Sprachen.
- **RUSE Guard:** unser Anti-Cheat, nach DomesticNukes' Entwurf. Er arbeitet nur in Mehrspieler- und Koop-Gefechten, nie im Einzelspieler, im Gefecht gegen den Computer, in der Kampagne oder während du Mods machst. Eine Mod-Kopie, die mit einem Cheat oder einem Testwerkzeug gebaut wurde, ist nur für Offline-Spiele: sie verlässt Mehrspieler- und Koop-Gefechte von selbst. Während eines echten Gefechts vergleicht er die Namen deiner laufenden Programme mit einer Liste bekannter Cheat-Werkzeuge (nur die Namen; sonst wird nichts gelesen), und was er aus einem Gefecht sammelt, wird unter deinem Benutzernamen abgelegt, nie unter deinem Steam-Konto. Im Spiel testen baut seine Kopien damit. In Mehrspieler-Gefechten gegen einen echten Gegner getestet; die Belege erreichen unseren Server.
- **Bug Watch (freiwillig):** wenn du es ankreuzt, zählen Studio und Launcher, was du benutzt und wann etwas schiefgeht, die Abstürze der Apps und die des Spiels, mit den Mods, die an waren, und schicken es einmal am Tag mit deinem Benutzernamen an unsere Entwickler. Keine echten Namen, kein Steam-Konto, keine Dateien. Aus, solange du es nicht ankreuzt; kreuze es jederzeit ab, und was aufbewahrt war, wird gelöscht. In beiden Apps gesehen.
- **Über Steam anmelden:** eine Anmeldung auf Steams eigener Seite in deinem Browser bestätigt, dass du R.U.S.E. besitzt, für Online-Spiele, RUSE Guard und Inhalts-Downloads. Wir sehen nie dein Passwort, und deine Steam-ID wird nie gespeichert: nur ein Pass, der 30 Tage auf deinem PC bleibt. Das Studio fragt einmal; die Einstellungen des Launchers öffnen es jederzeit. Noch braucht es nichts. In den Apps noch nicht ausprobiert.

**0.9.8.9:** Downloads auf mehr PCs, und sichereres Lesen von Bildern.

- **Behoben, von einem Spieler gemeldet:** auf einem PC, dessen Windows das Zertifikat nicht hat, mit dem GitHubs Downloads geprüft werden, und es nicht holen kann, schlugen Downloads fehl („unable to get issuer certificate“). Die Downloads des Studios (seine Updates, die Spiel-Patches, die Modelle der Epocheneinheiten und die Online-Texturen von Map Paint) versuchen es jetzt auch mit der Zertifikatsliste von Firefox, die es mitbringt.
- **Sicherere Bilder:** die Bibliothek, mit der das Studio Bilder liest (Pillow), ist jetzt Version 13.0.0, mit ihren Korrekturen gegen präparierte Bilddateien, die die App abstürzen lassen, ihren Speicher aufbrauchen oder Schlimmeres anrichten konnten.
- **Strengerer Code:** die 12 Warnungen der Code-Prüfung von GitHub zu diesem Projekt sind erledigt. Zeigt das Studio seine Seiten in deinem Webbrowser, öffnen sie nur seine eigenen Dateien, geprüft auf eine Weise, die diese Prüfung erkennt; Downloads verlangen TLS 1.2 oder neuer, wie schon bisher; und das Lesen der Straßenfehler eines fehlgeschlagenen Tests bleibt bei jeder Meldung schnell. Sonst ändert sich an der Arbeitsweise des Studios nichts.

**0.9.8.8:** ein Startbildschirm und eine Gebäudetafel, eigene Gebäude, RUSE Decoy für Sounds und Animationen, jede Spielregel in einem Reiter, und R.U.S.E. 2.0 in Gold.

- **Ein Startbildschirm:** mit deinem Mod weitermachen, einen neuen beginnen oder ihn überspringen (auch immer). Die Schritte eines neuen Mods: sein Name, ob jede Nation ihre Einheiten behält oder leer beginnt, die Forschung (die des Spiels, keine oder deine eigene), die Gebäudetafel, dann was der Mod ändert. Im Spiel gesehen.
- **Die Gebäudetafel:** die Gebäude jeder Nation als Reihen der Einheiten, die ihre Baumenüs anbieten, in der Reihenfolge des Spiels. Setz eine Einheit ein (eine der Nation, die Kopie einer Einheit einer anderen Nation, eine Epocheneinheit), zieh sie entlang einer Reihe oder zu einem anderen Gebäude, nimm sie heraus oder lass sie von der Einheit aus erforschen, unter der sie steht. Die Seite jeder Einheit sagt, wo sie gebaut wird. Im Spiel gesehen.
- **Gebäude hinzufügen…:** eine Kopie eines Gebäudes des Spiels, die dieselben Einheiten baut, oder ein Gebäude mit eigenen Einheiten und einem eigenen Reiter in der Bauleiste, bis zu drei pro Nation. Das zweite und das dritte brauchen einen kleinen Spiel-Patch für mehr Gebäude: das Studio lädt ihn einmal herunter und wendet ihn nur auf deine gemoddete Kopie an, nie auf das Spiel in deinem Steam-Ordner. Im Spiel gesehen.
- **Das eigene Aussehen eines Gebäudes:** auf der Seite eines neuen Gebäudes ein 3D-Modell anstelle eines Teils des kopierten Aussehens importieren (das Hauptgebäude einer Fabrik oder eines HQ, oder das gewählte Teil) und ihm ein eigenes Bild im Baumenü geben. Im Spiel gesehen.
- **Modell importieren… im Karten-Reiter:** ein 3D-Modell (.glb, .gltf oder .3ds) wird ein eigener Felsen, ein Objekt, eine Pflanze oder ein Baum deiner Karte, platziert wie die des Spiels, mit einer Größe und der Nennung seines Erstellers (Modelle anderer: nur CC0 oder CC-BY). Einheiten werfen es um wie die des Spiels; mit **Massiv** angehakt fahren sie darum herum. Im Spiel gesehen.
- **RUSE Decoy, der Sound- und Animationsdesigner,** anstelle des Musik-Reiters. Jeder Sound des Spiels nach Art (Waffen nah und fern, Einschläge, Motoren, Umgebung, Oberfläche, Finten-Karten, Einheitenstimmen, Funk, Missionssätze mit dem, was jeder sagt, Musik): abspielen, ihm eine eigene Lautstärke geben (0 bis 200 %) oder ihn ersetzen. Animationen: einen anderen Clip an die Stelle eines Clips setzen, einen langsamer oder schneller machen, einen Knochen vergrößern oder drehen, oder Motion Capture auf die Soldaten legen, aus einer Bibliothek von 3.205 freien Bewegungen (die CMU-Motion-Capture-Datenbank und 100STYLE, mit Nennung), jede beim Auswählen heruntergeladen. Die Seite einer Einheit öffnet RUSE Decoy mit ihren eigenen Sounds und Animationen. Im Spiel gesehen. Seine Fehlermeldungen sind vorerst nur auf Englisch.
- **KI- und Spielereinstellungen:** die Reiter Wirtschaft und KI sind ein Reiter. Spielereinstellungen: Geld und Einkommen, Nachschubdepots, Produktion und Täuschungskarten, wie bisher. Computerspieler: jeder ihrer 47 Werte im Standardsatz, in jeder Schwierigkeit und jeder Persönlichkeit (ein Wert, den das Spiel in einem Satz weglässt, zeigt die 0, mit der das Spiel rechnet). **Spielregeln:** 172 weitere Werte des Spiels in 16 Gruppen (Schlacht und Kapitulation, Bevölkerung, Bewegung und Straßen, Feuer und Ziele, Schaden, Wald und Deckung, Flugzeuge, Täuschungskarten im Einsatz, Gebäude platzieren, Ranglistenspiele online, Umrisse und Effekte am Bildschirm, die Farben der Spieler und Sektoren mit einer Farbauswahl, und weitere), jeder benannt und erklärt. Noch nicht im Spiel getestet.
- **Alle Werte und Dateien:** die Reiter Alle Werte und Dateien sind ein Reiter, mit einem Schalter oben; er öffnet sich auf dem zuletzt benutzten Teil.
- **Behoben:** Alle Werte zeigte die Zahlen einer Farbe in falscher Reihenfolge (das Spiel speichert Blau zuerst), daher sah Spielerfarbe 1, Blau, orange aus, und Rot einzugeben änderte Blau. Farben werden jetzt mit Rot zuerst gezeigt und eingegeben; eine Mod-Datei behält wie bisher die Reihenfolge des Spiels.
- **Behoben: dunkle und helle Flecken auf Karten, die das Studio gemacht hat** (leere, vergrößerte, Relief- und Sektorkarten): die Neigung des Bodens wurde falsch geschrieben, so wurden Gras und Felder ungleich beleuchtet. Eine Karte ist richtig beleuchtet, sobald sie mit dieser Version gebaut wird (ihr Boden wird beim ersten Mal neu gemacht). Im Spiel gesehen.
- **Die alten Übergänge entfernen (von DomesticNukes):** bei den Straßen im Karten-Reiter sperrt **Übergänge der alten Brücken sperren**, mit **Brücken der Karte entfernen** an, auch den Boden, wo jede alte Brücke über Wasser stand, und trennt die Straßenverbindungen dort: dort kommt nichts mehr hinüber; das übrige Straßennetz bleibt. Noch nicht im Spiel getestet.
- **R.U.S.E. 2.0 in Gold:** das gemoddete Spiel, das Im Spiel testen baut, beginnt mit einer Schlachtszene und einem startenden Motor, und sein Hauptmenü, der kleine Titel jedes Menüs, die Umrisse der Menüs und die Ladebildschirme zeigen R.U.S.E. 2.0 in Gold. Es wird beim ersten Mal auf deinem PC aus den Dateien deines eigenen Spiels gemacht (einmal ein paar Minuten, dann behalten). In den Einstellungen behält ein Kästchen den eigenen Titel des Spiels. Im Spiel gesehen.
- **Die Schrift des Spiels:** das Studio ist in der Menüschrift des Spiels geschrieben, bei jedem Start aus deinem Spiel genommen (die Schrift wird nicht mit dem Studio geliefert).
- **Behoben, von einem Modder gemeldet:** ein auf eine neue Einheit aus dem Panther importiertes Modell landete weit weg von der Einheit; auf Einheiten aus 85 anderen (die 155-mm-GPF, der SU-85, der Carro Veloce, das StuG III, der M7 Priest...) saß es neben dem Turm. Das Studio liest jetzt richtig, wo sich ihre Türme drehen. Ein vorher importiertes Modell behält seinen alten Platz: nutze Modell importieren… erneut auf dieser Einheit. Noch nicht im Spiel getestet.
- **Behoben, von einem Spieler gemeldet:** ein Modell mit JPG- oder WebP-Bildern (die meisten heruntergeladenen .glb) wurde abgelehnt; es wird jetzt importiert. Ein Modell, das der Import noch nicht lesen kann (komprimierte Meshes, KTX2-Bilder), sagt es und wie man es in Blender behebt. Noch nicht im Spiel getestet.
- **Behoben, von einem Spieler gemeldet:** ein Panzer des Spiels, in Blender geöffnet und zurück importiert, behielt seinen Turm starr. In Blender öffnen benennt jetzt den Knochen jedes Teils wie das Spiel, und der Import dreht ein Teil am Turmknochen mit dem Turm. Ein vorher exportiertes Modell behält seine alten Namen: öffne es erneut in Blender. Noch nicht im Spiel getestet.
- **Benenne deine Munition:** eine kopierte Munition heißt auch im Spiel so, wie du sie nennst, und die Seite jeder Munition hat **Ihr Name im Spiel**: ein neuer Name oder eine neue Art, in allen Sprachen auf einmal, dann eine Sprache allein. Noch nicht im Spiel getestet.
- **Eigene Flag-Typen:** unter den Flags einer Einheit legt **Flag-Typen anlegen oder ändern…** einen benannten Typ an: hake die Flags des Spiels an, die er ein- und ausschaltet. Gib ihn jeder Einheit; nimm ihn weg, und ihre Flags sind wieder wie vorher. Ändere einen Typ, und jede Einheit mit ihm ändert sich mit. Das Spiel wirkt nur auf seine eigenen Flags, also kombiniert ein Typ, was sie schon tun. Noch nicht im Spiel getestet.
- **Schussgeschwindigkeit richtig erklärt:** der Zahlenführer sagte, Geschwindigkeit, Luftwiderstand, der Schalter „ohne Physik“ und die Zeit vor dem Abflug eines Schusses seien nur Optik. Sie bestimmen, wann der Treffer landet: ein langsamerer Schuss trifft später, und auf ein bewegtes Ziel wird um die Flugzeit vorgehalten (aus der Funktionsweise des Spiels; noch nicht in einem Test geprüft).
- **Jeder Fehler in zehn Sprachen:** die 35 Fehler des Studios, die mit dem Modellimport und der Gebäudetafel kamen.
- **Credits:** die README sagt, was LittleGrooves Engine in unserer noch tut, was unseres ist, und dass unser Texturleser auch ProLutions Codec nutzt.
- **Noch fehlerhaft, Nutzung auf eigene Verantwortung:** die Texturen von Map Paint und beide leeren Karten (Leeres Gelände und Leerer Ozean).

**0.9.8.7:** Wiederherstellen und Platziertes auswählen, Platzieren als Raster / Kasten / Pfad, größere leere Karten, und jeder Wert erklärt.

- **Behoben, von einem Modder gemeldet:** bei einer neuen Einheit aus einer von 17 Einheiten des Spiels (Königstiger, Atomgeschütze, V2...) erschien das Feld zum Ändern ihres Modells nie. Das Studio findet diese Modelle jetzt, und findet es eines nicht, sagt das Feld es, statt zu verschwinden.
- **Der KI-Reiter erklärt:** jeder Wert der Computerspieler sagt, was er tut, in einfachen Einheiten, und welcher in einer Schlacht für jede Schwierigkeit und jedes Profil gilt; Modi, Schwierigkeiten, Profile und Einheiten werden nach Namen gewählt.
- **Jeder Wert erklärt, überall:** Alle Werte, der Einheiten-Reiter, die Pinsel des Karten-Reiters (Größe in Metern, Stärke nach dem, was sie tut) und der Musik-Reiter (wann jede Schlachtliste spielt).
- **Der Wirtschaft-Reiter, Normal und Nuklear getrennt:** wo sich die beiden Modi unterscheiden, hat jeder eigene Felder. Eine Änderung nur am Nuklear-Modus wurde im Spiel noch nicht getestet.
- **Wiederherstellen und auswählen:** Wiederherstellen in jedem Kartenwerkzeug (Strg+Y oder Strg+Umschalt+Z, und eine Schaltfläche); in den Leisten Gebäude und Objekte & Bäume Platziertes auswählen (Klick, Umschalt+Klick oder ein Rahmen), verschieben, drehen, in der Größe ändern oder löschen, auch die der Karte selbst.
- **Raster, Kasten und Pfad:** Reihen von Objekten als Raster oder Kasten, Gebäude zur Straße ausgerichtet, und Hecken, Baumreihen und Baumstreifen entlang eines Pfads, mit Deckung.
- **Größere leere Karten:** das Fenster Kartengröße einer neuen leeren Karte fügt an jeder Seite Geländestreifen hinzu oder nimmt sie weg, und Sektoren erstellen füllt sie mit Sektoren.
- **Menüs und Bedienung:** Zahlenzeilen statt Schiebereglern, eine Suche mit #Tags und den letzten Suchen, aufklappende Karten, und neu belegbare Tasten (Tauschen, Übernehmen, Abbrechen).
- **Sicherer:** Schließen mit ungespeicherter Arbeit fragt zuerst; eine Karte mit neu abgeschnittenem Gelände wird vor Im Spiel testen abgelehnt; ein Mod aus einem älteren Studio wird nach einer Sicherung aktualisiert (Diesen Mod aktualisieren); behaltene Build-Ergebnisse bleiben nach einem Studio-Update gültig.
- **Jede Meldung in zehn Sprachen:** die Fehler des Studios und die Zeilen des Builds.
- **Neue Einheit** lässt die zwei Einheiten ohne Modell als Vorlage weg (das SOLO-57-mm-Geschütz und die SOLO-Fallschirmjäger).
- Noch nicht im Spiel getestet: mit Raster, Kasten und Pfad Platziertes, verschobene Objekte und eine größere im Studio gemachte Karte.
- **Noch fehlerhaft, Nutzung auf eigene Verantwortung:** die Texturen von Map Paint und beide leeren Karten (Leeres Gelände und Leerer Ozean).

**0.9.8.6:** jede Flag und jede Zahl der Einheiten erklärt, die Kartenwerkzeuge zeigen, was sie getan haben, und leere Karten richtig dargestellt.

- **Einheiten-Flags erklärt:** jede Flag auf der Seite einer Einheit zeigt ihren Namen, und beim Darüberfahren sieht man, was sie tut, wie man sie benutzt und wie sicher wir sind. **Flag-Handbuch: alle Flags erklärt** listet alle 105, mit Suche. Das Studio prüft die Flags einer Einheit: ein bekannter Absturz (die Flags eines Lastwagens an etwas, das kein Lastwagen ist, ein bewaffnetes Flugzeug mit der Aufklärer-Flag ohne die Jäger-Flag) zeigt seine Lösung, und das Studio startet das Spiel nicht, bis er behoben ist; Flags, die eine Einheit voraussichtlich kaputt machen, geben eine Warnung.
- **Jede Zahl erklärt:** fahren Sie über den Namen einer beliebigen Zahl einer Einheit oder eines Gebäudes, um zu sehen, was sie bedeutet; daneben ihr Wert in einfachen Einheiten (Meter, km/h, Sekunden, Grad, $, %), ein Regler, der sie kleiner oder größer als den Wert des Spiels macht (ihr Grundwert, -90 % bis +300 %), und wo sie unter den Einheiten des Spiels ihrer Art liegt. Geschwindigkeiten sind in den km/h des Spiels.
- **So funktionieren Waffen und Munition**, Schritt für Schritt, im Feld Waffen.
- **Die Kartenwerkzeuge zeigen, was sie getan haben:** Deckung, Freilegen, Stadt, Wald, Sperren und Öffnen markieren den Boden, über den jeder Strich ging, und sagen, wie viele m² sich für Einheiten geändert haben, oder dass sich nichts geändert hat. Stadt arbeitet in echten Metern und umkreist zuerst die Gebäude, die ein Klick abdecken wird.
- **Platzieren:** platzierte Gebäude, Bäume und Objekte zeigen ihre echten Modelle (mit einem Punkt an ihrem Fuß); das gewählte erscheint vor dem Klick durchsichtig unter dem Zeiger; die Platzierliste ist ein Raster aus Bildern. Bäume sind nicht mehr schwarz, und Sektornummern verschwinden, wenn die Kamera nah ist.
- **Leere Karten** (im Spiel gesehen auf Leeres Gelände): Schatten auf flachem Boden; was Sie dort platzieren, wo die kopierte Karte Meer hatte, wird dargestellt; der Kameraboden folgt dem neuen Boden.
- **Noch fehlerhaft, Nutzung auf eigene Verantwortung:** die Texturen von Map Paint und beide leeren Karten (Leeres Gelände und Leerer Ozean).

**0.9.8.5:** Flugzeuge in jeder Rolle, Waffen, die Flugzeuge treffen, und eine Bibliothek für den Textur-Pinsel von Map Paint.

- **Die Rolle eines Flugzeugs** (Meldung eines Spielers: ein Jagdbomber mit den Bombenteppich-Bomben eines Bombers flog zu seinem Ziel und warf nichts ab): ein neues Rolle-Feld auf der Seite eines Flugzeugs macht es zum Jäger, Jagdbomber, Bomber oder Aufklärer. Sein Verhalten, wie die Computerspieler es einsetzen, und seine Worte im Baumenü ändern sich mit. Die Bomben eines Bombers kommen in einen Bombenschacht (kopiert von einem Bomber des Spiels), der einzige Weg, wie ein Bomberanflug sie abwirft. Im Spiel gesehen: ein Jagdbomber, der zum Bomber gemacht wurde, wirft seine Bomben ab; ein Aufklärer, der seine Waffen behält (eine Stuka, eine ME109), greift weiter an und hat die Sicht der Aufklärer.
- **Aufklärungsfahrzeuge:** das Rolle-Feld eines Bodenfahrzeugs macht es zur Aufklärung: die Sicht der Spähwagen (viel weiter als die eines Panzers), wie die Computerspieler sie einsetzen, ihre Worte im Baumenü, und es kann in Wälder fahren (im Spiel gesehen mit einem Panzer IV).
- **Was eine Waffe trifft:** das Trifft jeder Waffe wählt den Boden, Flugzeuge oder beides (eine zweite Waffe daneben, so wie die Flak-Geschütze des Spiels für jedes eine tragen). Im Spiel gesehen: Panzergranaten, die auf Flugzeuge feuern. Bekannt: eine Flugzeugwaffe, die nur den Boden treffen soll, richtet noch keinen Schaden an.
- **Der Textur-Pinsel von Map Paint bekommt eine Bibliothek:** die Bodentexturen des Spiels (Gras, Felder, Sand, Schnee, Fels, Straßen..., nach Kriegsschauplatz, mit Suche), ein Quadrat vom Boden jeder Karte, eigene Bilder und kostenlose Bilder aus dem Internet (Poly Haven und ambientCG, CC0; US-Luftbilder, gemeinfrei), ein Bild pro Klick heruntergeladen und mit seiner Quellenangabe in Ihrem Mod behalten. Ein Größe-Regler, die zuletzt benutzten Texturen und **Spieldetail aus der Nähe**, das die eigenen Decals des Spiels einer Spieltextur über den gemalten Boden legt. Noch nicht im Spiel gesehen; die Online-Downloads noch nicht getestet.
- **Objekte auf offenem Gelände**, fern von den Städten, Höfen und Wäldern der Karte, sind jetzt in Reichweite der Darstellung des Spiels, und große Gruppen neuer Objekte werden so angelegt wie die des Spiels (noch nicht im Spiel gesehen).
- **Schneller neu malen:** der gemalte Boden wird von Build zu Build behalten, gleich welche Kopie oder welcher Mod ihn gemalt hat: eine gleich bemalte Karte holt ihn in Sekunden zurück, nicht in Minuten.
- **Noch fehlerhaft, Nutzung auf eigene Verantwortung:** die Texturen von Map Paint und beide leeren Karten (Leeres Gelände und Leerer Ozean).

**0.9.8.4:** eigene Missionen, leere Karten zum Aufbauen und viel mehr zum Anpassen.

- **Noch fehlerhaft, Nutzung auf eigene Verantwortung:** die Texturen von Map Paint und beide leeren Karten (Leeres Gelände und Leerer Ozean).
- **Eigene Missionen:** eine neue Operation oder ein neues Kampagnenkapitel bekommt eine eigene Mission auf der Szenario-Seite des Kartenbildschirms: Seiten, Ziele, Ereignisse (Wenn → Dann: Einheiten bringen, bewegen, angreifen, eine Zone halten, Artillerie, Bombardierung, Fallschirmjäger, Meldungen, Geld, Sieg, Niederlage) und Kamerafahrten. Im Spiel gesehen: ihre Kamerafahrt, Ziele (eine Zone, eine zerstörte Gruppe, eine Zeit), sich wiederholende Ereignisse, Geld, eine Seite an den Computer übergeben. Noch nicht getestet: Fallschirmjäger, eine Kamerafahrt, die ein Ereignis startet.
- **Karte | Szenario** auf dem Kartenbildschirm: die Dinge der anderen Seite erscheinen blass und lassen sich nicht aus Versehen greifen.
- **Leere Karten:** von der kopierten Karte ist nichts mehr zu sehen, und Sie setzen das HQ jedes Spielers (der Build wartet, bis alle gesetzt sind). Leeres Gelände geht auch für Operationen und Kampagnenkapitel.
- **Eigene Sektoren:** malen, ihre Ecken ziehen, einen neuen als Rechteck ziehen, Boden ohne Sektor lassen, einen löschen (im Spiel gesehen).
- **Nachschubdepots:** der Wirtschaft-Reiter gibt jedem Depot auf jeder Karte oder auf einer Karte mehr Lastwagen (mal, oder eine Zahl je Depot); keine Obergrenze von 1.000 Lastwagen mehr.
- **Nationen-Reiter:** alle Einheiten einer Nation auf einmal ausblenden, wieder zeigen oder ihre Menüs mit den Einheiten einer Epoche füllen.
- **Installierten Mod bearbeiten:** jeden Mod des Launchers öffnen; der eines anderen wird zu Ihrer eigenen Kopie unter eigenem Namen. RUSE-Mod-Manager-Mods (.rmod) werden umgewandelt, damit ihre Werte geändert werden können.
- **Die Mod-Prüfung in einfachen Worten**, mit einem Knopf zum Beheben jedes Problems.
- **Ein eigenes Aussehen für eine Einheit:** eine eigene Kopie ihres Modells zum Neubemalen; Trupps tragen die Standarduniform oder eine eigene; den Lastwagen wählen, in dem ein Trupp oder ein Geschütz fährt. Infanterie erscheint in 3D und öffnet sich in Blender.
- **Panzerung** wird als eine Stufe des Spiels gewählt, sodass die Karte zeigt, womit die Einheit kämpft; **importierte Flugzeuge** behalten ihre drehenden Propeller und kommen nach vorne gerichtet zurück (beides im Spiel gesehen).
- **Modellgrößen per Schieberegler** (Winzig, Spielgröße, Echte Größe, Riesig: 0,05 bis 20), jederzeit änderbar, alle Flugzeuge auf einmal.
- **Mehr zum Ändern:** ein eigener Wert einer KI-Schwierigkeit oder eines KI-Profils für einen, den nur Standard hat; Zahlen über die Schieberegler der Kartenwerkzeuge hinaus; lautere und längere Musikbearbeitungen.
- **Behoben:** eine Einheit, die im Menü gezeigt, aber von einer ausgeblendeten erforscht wird, stoppte das Spiel: die Prüfung nennt sie und der Build lehnt sie ab. Panzer feuern wieder über gelöschte Städte hinweg, und Einheiten fallen nicht mehr in die Löcher, wo Brücken entfernt wurden (im Spiel gesehen).
- **Downloads gehen auf jedem PC:** hat Windows das Zertifikat, mit dem GitHub geprüft wird, noch nicht geholt, fragt das Studio Windows danach, wie ein Browser, und versucht es erneut (noch nicht auf einem PC mit dem Problem getestet).

**0.9.8.3:** Kopien mit Mods kommen dorthin, wo du es sagst.

- **Wohin Kopien mit Mods kommen**, in den Einstellungen: Wähle den Ordner, in dem die Kopie des Spiels mit Mods gebaut
  wird, oder geh zurück zum empfohlenen Ort, `RUSE-Instances` auf dem Laufwerk des Spiels (dort teilt die Kopie die
  Dateien des Spiels und ist in Sekunden fertig; auf einem anderen Laufwerk ist sie eine vollständige Kopie des Spiels,
  langsamer und größer). Die saubere Sicherung des Spiels kommt daneben. Das nächste Im Spiel testen baut am neuen
  Ort; der alte Ordner kann von Hand gelöscht werden. Der Launcher nutzt denselben Ordner.

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
- **Eine Einheit entfernen, aus der andere erforscht werden:** In **Einstellungen > Forschung** wählst du, ob du
  zuerst gewarnt wirst (Standard), ob es abgelehnt wird oder ob sie neu mit deren eigener Vorgängereinheit verknüpft
  werden; eine Einheit, die auf eine entfernte zeigt, zeigt das auf ihrer Seite und in der Prüfung. Forschungszeiten
  lassen sich in Sekunden oder Minuten eingeben (dass das Spiel sie in Sekunden zählt, ist im Spiel noch nicht
  ausprobiert).
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

**0.9.6:** eine neue Einheit kann ein eigenes 3D-Modell haben, aus jedem 3D-Programm, und **Im Spiel testen** startet
sofort, wenn sich nichts geändert hat. Und eine Premiere:

- **Das erste Modell aus einem anderen 3D-Programm in R.U.S.E.:** ein M1 Abrams, als neue US-Einheit neben dem Sherman gemacht. Er wird in der Armor Base mit seiner eigenen Karte gekauft, gebaut und dreht seinen Turm wie die Panzer des Spiels. Im Spiel gesehen.

| Vorher | Jetzt |
|---|---|
| Eine neue Einheit hatte das Modell der Einheit, die sie kopiert. | **Modell importieren…** auf der Seite einer neuen Einheit: wähle eine **.3ds** (ihre Bilder daneben oder im Ordner darüber) oder eine **.glb** (aus Blender und den meisten 3D-Programmen). Das Studio passt sie an die Einheit an, die sie kopiert: ihre Länge (mal **Größe**: 1 ist gleich lang, ein Abrams gegenüber einem Sherman ist 1,36), ihren Turm auf den Turm dieser Einheit, damit das Spiel ihn genauso dreht, ihre Bilder als eigene Texturen. Die Seite zeigt sie in 3D; **Modell der kopierten Einheit nutzen** nimmt sie wieder heraus. Sie kommt als `files/models/<the unit's name>.glb` in deinen Mod und lässt sich in Blender öffnen. **Im Spiel gesehen.** Noch früh: Ketten und Räder drehen sich noch nicht, das Mündungsfeuer erscheint dort, wo die Mündung der kopierten Einheit ist, und das Wrack ist das der kopierten Einheit. |
| Eine neue Einheit mit eigener Karte ließ das Spiel abstürzen, wenn sie gebaut wurde (0.9.5). | Ihre Einheitenkarte liegt auch auf der Spielkarte dort, wo das Spiel sie liest. **Im Spiel gesehen.** |
| Eine mit **Karte duplizieren** gemachte Karte ließ sich im Studio nicht löschen. | **Karte löschen**, unter Karte duplizieren auf einer neuen Karte: fragt einmal, dann kommt ihr Ordner in den Papierkorb, wo du ihn zurückholen kannst. Die eigenen Karten des Spiels lassen sich nicht löschen. |
| Das Studio sagte, Blender sei nicht installiert, wenn es entpackt statt installiert war. | Es findet Blender, wo immer du es entpackt hast (im obersten Ordner eines Laufwerks oder eine Ebene darunter, Downloads, Desktop, Dokumente). |
| Neu bemalte Einheiten kamen mit manchen Farben etwas daneben heraus (ein roter und blauer Fleck konnte lila werden). | Jedes 4 x 4-Feld behält seine eigenen Farben. Neu bemalte Einheiten und bemalter Boden kommen mit leicht anderen Bilddaten heraus als in 0.9.5 (gleiches Aussehen), daher ändern sich Fingerabdruck und Beitrittscode eines solchen Mods: alle Spieler sollten aktualisieren, bevor sie zusammen spielen. |
| **Im Spiel testen** baute jedes Mal die ganze gemoddete Kopie neu, auch wenn sich nichts geändert hatte. | Seit dem letzten Build nichts geändert: das Spiel startet sofort, ohne Build (ein Test-Mod: von 21-29 s auf unter 0,1 s). Ein Build verwendet die unveränderten Dateien der letzten Kopie weiter, statt sie erneut zu kopieren. |
| Jeder Build las die Einheitendaten des Spiels neu ein. | Sie bleiben zwischen Builds erhalten: ein großer Test-Mod brauchte jedes Mal 213 s; jetzt dauert der erste Build etwa so lange und die folgenden 68 s. Das Spiel kopiert vor einem Build nicht mehr alle seine Daten. |
| Das Löschen des größten Teils einer großen Karte ließ dem Studio den Speicher ausgehen, und das Löschen der ganzen Karte wurde als zu groß abgelehnt. | Entfernen zählt in Sekunden, eins nach dem anderen; **Ganze Karte löschen** in der Leiste Entfernen (Rückgängig nimmt es zurück). Gelöschte Szenerie wird kompakt geschrieben. Neu: noch nicht im großen Maßstab im Spiel gesehen. |
| Unter einer Straße eingeebneter Boden ließ die Straße der Fernansicht auf der alten Höhe. | Das Straßenmodell folgt dem neuen Boden. Neu: noch nicht im Spiel gesehen. |
| Ein eingeebnetes Flussbett behielt aus der Nähe seine Fels- und Schluchtbilder. | Es wird von beiden Ufern aus aufgefüllt und sein niedriger Bewuchs entfernt. Neu: noch nicht im Spiel gesehen, wie der Build es macht. |
| Während der Spielindex gebaut wurde (etwa eine Minute), konnte das Studio nur warten. | Karten und Einstellungen bleiben nutzbar; die Zeile unten sagt, wann er fertig ist. |
| Ein langsamer Start hinterließ keinen Hinweis. | Die Schritte jedes Starts werden gestoppt; **Bericht kopieren** in der Fehlersuche listet die letzten fünf auf. |
| Die Seite des Fensters konnte mehr von der App erreichen als ihre eigenen Aufrufe. | Sie bekommt nur die eigenen Aufrufe der App. |

Außerdem macht `ruse import-model <file> --like <model> --unit <name>` dasselbe über die Befehlszeile.

**0.9.5:** Einheiten bekommen ein eigenes Aussehen. Sieh dir jede Einheit in 3D an, bemale sie in Blender neu, gib ihr
deine eigene Karte im Baumenü. Und unsere Premieren, alle im Spiel gesehen:

- **Die erste von einem Mod neu bemalte Einheit:** ein roter Sherman, aus der Nähe und von fern.
- **Die erste in Blender bemalte Einheit**, zurück ins Spiel gebracht.
- **Die erste im Studio gemachte Karte fürs Baumenü,** gezeigt im eigenen Menü der Armor Base des Spiels.
- **Die erste neue Einheit mit eigenem Modell,** neben denen des Spiels: der Tall Sherman, neben dem Sherman (beim Testen gemacht; eigene Modelle im Studio zu machen kommt als Nächstes).
- **Die erste eigene Mission**, bis zum Sieg gespielt: eine neue Operation mit eigenen Zielen, Einheiten und einem Artillerieschlag (beim Testen gemacht).

| Vorher | Jetzt |
|---|---|
| Die Seite einer Einheit zeigte nur ihre Werte. | **3D-Modell** auf der Seite der Einheit: dreh es, zoom hinein, sieh die Bemalung deines Mods darauf. |
| Das Aussehen einer Einheit war das des Spiels. | **In Blender neu bemalen:** **In Blender öffnen** öffnet die Modelle der Einheit mit ihren Bildern; male auf das Modell, dann speichert **Zurückholen** deine Bemalung und legt sie in deinen Mod. **Im Spiel gesehen**, aus der Nähe und von fern. Blender ist kostenlos: findet das Studio es nicht, sind **Blender holen (kostenlos)** und **Blender auswählen…** gleich da. |
| Das Bild einer Einheit im Baumenü war das des Spiels. | **Diese Ansicht als Karte nehmen:** dreh und zoome das 3D-Modell, bis es im gestrichelten Rahmen richtig aussieht; diese Ansicht wird die Karte der Einheit im Baumenü. **Im Spiel gesehen.** |
| Eine neue Einheit zeigte dieselbe Karte wie die Einheit, die sie kopiert, sodass beide im Menü gleich aussahen. | Die Karte einer neuen Einheit ist ihre eigene (`files/cards/<the unit's name>.png`): ihre Karte zu machen ändert nie die des Originals. Noch nicht im Spiel gesehen. |
| Ein gewachsenes Modellpaket für Einheiten wurde vom Spiel verworfen, jedes Modell darin fehlte: ein Absturz bei der ersten Fabrik. | Modellpakete werden so geschrieben, wie das Spiel sie prüft, gleich welche Größe sie haben. **Im Spiel gesehen:** ein zweiter Sherman mit eigenem Modell. |
| Die Einheiten einer Nation, einer anderen Armee gegeben, hatten in Kampagnenkapiteln und Operationen kein Modell: ein Mod, der französische Einheiten auf Holland erscheinen ließ, stürzte beim Laden ab. | Ihre Modelle laden auch dort. **Im Spiel gesehen** (französische Einheiten auf Colditz). |
| **Karte duplizieren** machte nur Karten für KÄMPFE. | Es macht auch eine neue **Operation** oder ein neues **Kampagnenkapitel** aus dem Eintrag jeder Karte. **Im Spiel gesehen:** eine neue Operation. Noch früh: ein neues Kampagnenkapitel wurde noch nicht ausprobiert. |
| Das Einebnen der Berge am Rand einer Karte ließ dort eine Klippe zurück. | Der Rand der Karte folgt dem Boden. **Im Spiel gesehen** (Blitz Twin, flach bis zum Rand). |
| Einheiten fuhren um die Stellen herum, wo gelöschte Stadtgebäude gestanden hatten. | Der Boden öffnet sich für jede Einheit, wo Gebäude entfernt werden, wie bei Bäumen. **Im Spiel gesehen.** |
| Keine Möglichkeit, den Boden der Karte zu bemalen. | **Kartenmalerei:** male das Bild des Bodens mit einer Farbe (dem Farbrad, den eigenen Farben der Karte oder der Pipette) oder mit dem eigenen Boden der Karte, kopiert von einer anderen Stelle. **Boden darunter freiräumen** (standardmäßig an) nimmt Gras, Feldfrüchte und Steine unter der Bemalung weg, sodass sie in jeder Höhe zu sehen ist. Noch früh: im Spiel von hoch oben gesehen. |

**0.9.4:** neue Karten, noch früh. **Karte duplizieren** macht aus jeder Karte von KÄMPFE eine neue Karte, und Karten
öffnen sich in einer Sekunde.

| Vorher | Jetzt |
|---|---|
| Kartenänderungen konnten nur die eigenen Karten des Spiels ändern. | **Karte duplizieren** (Reiter Karten, unter dem Namen der offenen Karte) macht eine **neue Karte**: eine vollständige Kopie mit eigenem Namen, in KÄMPFE neben dem Original aufgeführt, die du dann wie jede Karte änderst. Das Fenster sagt, was es tut und wie es funktioniert. **Im Spiel gesehen:** eine neue Karte spielt ihren eigenen Boden, und 101 neue Karten auf einmal wurden alle aufgeführt und gespielt. Noch früh: Kopien anderer Karten als Blitz werden gebaut, wurden aber noch nicht im Spiel ausprobiert, und das Einebnen der Berge am Rand einer Karte lässt dort eine Klippe. Bitte melde, was du findest. |
| Eine Karte brauchte jedes Mal Sekunden zum Öffnen (M03_Italie: 7,6 s). | Ihre Daten bleiben zwischen Besuchen und Starts erhalten: 1,7 s beim zweiten Mal. |
| „Mod“ und „Karte“ waren zwei gleich aussehende Menüs. | **Einheiten-Mod** (mit einem Panzer) und **Kartenänderungen** (mit einer Karte). |
| Seiten und Zonen ließen sich leicht verwechseln. | **Wer bekommt es?** sagt, dass eine Seite die ist, die die Einheiten steuert (ein Land kann mehrere haben), und der Hover-Text einer Zone sagt, dass sie ein Gebiet der Karte ist, keine Seite. |
| Updates kamen nur als ganze Versionen. | Kleine Korrekturen können zwischen Versionen kommen (0.9.4.1), angeboten wie jedes Update. |

**0.9.3:** alles, was du platzierst, ist von fern zu sehen, neue Straßen durch Wälder sehen aus wie die eigenen der Karte,
Bäume, die du auf einer Straße behalten kannst, Objekte und Bäume mit Namen in deiner Sprache, und Builds etwa dreimal
schneller.

| Vorher | Jetzt |
|---|---|
| Zu platzierende Objekte, Bäume und Gebäude waren unter französischen Codenamen aufgeführt: Caillou_10, ChampsPierres_02, Osier... | Mit Namen in der Sprache des Studios, in allen zehn, mit der Art jedes Dings: „Stony field 2“, „Champ de pierres 2“, „Steiniges Feld 2“. Sie wechseln mit dem Sprachknopf. Der Codename und sein Ordner stehen im Tooltip. |
| Felsen und die meisten anderen Objekte, die du platziert hast, verschwanden, sobald die Kamera die Nähe verließ, und kamen und gingen, während du sie drehtest. | Alles, was ein Mod platziert, wird bis in die Ferne dargestellt, die eigenen Objekte der Karte unverändert. **Im Spiel gesehen:** platzierte Felsen sind in jeder Höhe zu sehen. |
| Von hoch oben war eine neue Straße durch einen Wald ein heller Streifen, und nach einer ersten Korrektur war sie aus mittlerer bis großer Entfernung verschwunden. | Durch Wälder gemalt wie die eigenen Straßen der Karte, in jeder Höhe. **Im Spiel gesehen.** |
| Eine neue Straße nahm immer die Bäume von ihrem Weg, etwa 6 m zu beiden Seiten. | **Bäume auf neuen Straßen behalten** in der Leiste Straßen: die Bäume und Büsche bleiben über der Straße, und im Wald zeigt sich die Straße blasser und grauer. **Im Spiel gesehen.** |
| **Im Spiel testen** brauchte etwa 5 Minuten, um einen Mod mit neuen Straßen auf M03_Italie zu bauen. | Etwa 1½ Minuten: wie die Straßen einer Karte aussehen, wird einmal gemessen und behalten, und Kopien überspringen eine langsame Prüfung, die sie nicht brauchen. |

**0.9.2:** Korrekturen aus der Kampagnenkarte eines Testers: Brücken für neue Straßen auf jeder Karte, Straßenenden, die
an Brücken einrasten (oder gar nicht), die Namen, die ein Spieler kennt, Einheiten für den Spieler, Szenerie, die von fern
zu sehen ist, und die Zonen des Szenarios als Grenzen auf dem Boden.

| Vorher | Jetzt |
|---|---|
| Eine Straße über Wasser stoppte den Build auf 20 der 29 Karten mit Brücken (Italien, Deutschland, Holland...): ihre Brücke „hätte keinen Boden“. | Sie bekommt ihre Brücke und ihren Boden auf jeder Karte mit Brücken. Auf diesen Karten noch nicht im Spiel gesehen. |
| Jeder Punkt einer Straße rastete an der nächsten Straße ein, sogar auf eine Straße, wenn du dort eine Brücke platziert hattest. | Nur die zwei Enden einer Straße rasten ein, zuerst am Ende einer platzierten Brücke. **Enden an Straßen und Brücken einrasten** in der Leiste Straßen schaltet es aus. |
| Gebäude und Einheiten unter ihren Codenamen, wie „Descriptor_Building_VehiculeFactoryLeurre“. | Unter den Namen, die das Spiel ihnen gibt (DECOY ARMOR BASE), mit der eigenen Zeile des Spiels dazu, was jedes tut. |
| Keine Möglichkeit, dem Spieler in einem Kampagnenkapitel Einheiten zu geben: die Seite des Spielers (0) wurde abgelehnt. | **Wer bekommt es?** listet die eigenen Seiten des Szenarios aus seiner Mission auf: „Spieler · USA (Seite 0)“, „Computer · Deutschland (Seite 1)“... |
| Auf M03_Italie und anderen Karten verdeckte eine neue Straße im offenen Gelände von fern die Szenerie der Karte, und platzierte Objekte zeigten sich nur aus der Nähe. | Die Fernansicht der Karte bleibt, wie sie war, und platzierte Objekte zeigen sich von fern wie die eigenen der Karte. Noch nicht im Spiel gesehen. |
| Die Zonen des Szenarios waren farbige Flächen, die über der Karte schwebten und ihren Boden und die Symbole verdeckten. | Jede Zone ist eine klare Linie entlang ihrer Grenze auf dem Boden, innen mit einer durchsichtigen Tönung, wie die Grenzen in Stellaris. **Füllung der Zonen** stellt das Innere ein (0 %: nur die Grenzen). |

**0.9.1:** alles auf der Karte ziehen, klarere Symbole, die du in der Größe ändern und ausblenden kannst, deine Sprache vom
ersten Start an, und die Art jeder Einheit so, wie das Spiel sie nennt.

| Vorher | Jetzt |
|---|---|
| Startpunkte, Versorgungsdepots und gespawnte Einheiten ließen sich nur mit dem Werkzeug Verschieben bewegen, ein Klick und dann noch einer. | Greif eines davon auf der Karte und zieh es, ohne gewähltes Werkzeug, so wie sich die Eröffnungskameras schon drehen ließen. Depots und HQs haften beim Ziehen weiter an Straßen. |
| Kartensymbole waren Strichmännchen und Kästchen, und jeder Bunker sah gleich aus. | Ein Symbol für jede Art: ein Soldat, ein Panzer, ein Lastwagen für Versorgungsdepots, ein Flugzeug, Geschütze, ein deutlich markiertes HQ, Armor Base und Flugplatz unterscheidbar, und jeder Bunker mit seinem eigenen (Panzerabwehr, Maschinengewehr, Flugabwehr, Artillerie, Festung, Beobachtungsposten). |
| Symbole waren von hoch oben klobig, und man konnte sie nur ausblenden, indem man das ganze Szenario ausblendete. | Symbole werden kleiner, wenn die Kamera wegzieht, ein Regler stellt ihre Größe ein, und die Leiste Szenario zeigt oder verbirgt jede Art (Starts, Kameras, Depots, Gebäude, Einheiten, Zonen, Orte). Für das nächste Mal behalten. |
| Das Studio startete mit den Codenamen, und die Sprache steckte in den Einstellungen, sodass Spieler nicht wussten, dass es ihre Sprache spricht. | Der erste Start fragt: „Wählen Sie Ihre Sprache“, jede Sprache in ihren eigenen Worten, die, auf die dein Spiel in Steam eingestellt ist, markiert. Danach ein Sprachknopf oben, immer im Blick. |
| Einheiten waren nur „Boden“ oder „Luft“. | Unter Boden, Infanterie und Luft die eigenen Arten des Spiels: Leichter, Mittlerer und Schwerer Panzer, Jagdpanzer, Panzerspähwagen, Jäger, Jagdbomber, Leichter, Mittlerer und Schwerer Bomber, Aufklärungsflugzeug... auch in der Zeile jeder Einheit, in deiner Sprache. Die Suche findet sie („Bomber“, „Aufklärung“). |
| Die Windows-Liste der installierten Apps zeigte die allererste installierte Version. | Sie zeigt die Version, die du hast. |

**0.9.0:** Straßen sehen richtig aus. Eine Straße, die du zeichnest, sieht jetzt aus wie die eigenen Straßen der Karte, von
hoch oben bis hinunter zum Boden. Es hat viel Zeit und viele Tests gekostet, dorthin zu kommen, länger als bei den
Brücken. Im Spiel auf D-Day getestet.

![Eine neue Straße aus der Nähe auf D-Day: Asphalt mit gestrichelter Mittellinie und Schotterbanketten, die ins Gras übergehen](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Vorher | Jetzt |
|---|---|
| Eine neue Straße verschwand, wenn die Kamera zu ihr herunterkam: nur ihre Bemalung war zu sehen, von hoch oben. | Aus der Nähe wird sie mit den eigenen Asphalt-Aufklebern der Karte gezeichnet, entlang der Straße so gelegt, wie die Karte sie legt, mit einem Rand-Aufkleber auf jeder Seite: Asphalt, eine gestrichelte Mittellinie, Schotterbankette. |
| Die Bemalung war eine einzige flache Farbe, blasser und breiter als die Straßen der Karte. | Die Bemalung wird an den eigenen Straßen der Karte gemessen: ihre Farbe, ihre Bankette und wie sie in den Boden übergehen. Jede Karte bekommt ihre eigene. |
| Gras, Büsche und die Bäume der Höfe wuchsen durch eine neue Straße. | Die Pflanzen und Objekte der Karte auf dem Weg der Straße werden entfernt (etwa 6 m zu beiden Seiten). Wälder behalten ihre Deckung und Bewegung, und Gebäude bleiben. |
| Nur die Straßen-Aufkleber von D-Day waren bekannt. | Die eigenen Aufkleber der Wüstenkarten werden dort verwendet, auf dieselbe Weise gelegt (noch nicht im Spiel gesehen). |
| Ein großes Entfernen (Tausende Kreise) brauchte viele Minuten zum Bauen. | Viel schneller: nur die Kreise nahe jedem Teil der Karte werden betrachtet. |

![Drei neue Straßen, die von der Hauptstraße von D-Day abgehen](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-6-done-overview.jpg)

**0.8.3:** die Szenario-Werkzeuge des Karteneditors aus LittleGrooves RUSE-Mod-Manager: Versorgungsdepots und HQs haften an
Straßen, ein Symbol für jedes Gebäude und jede Einheit, und die Eröffnungskamera jedes Spielers gezeigt, mitgeführt und
gedreht. Noch nicht im Spiel ausprobiert.

| Vorher | Jetzt |
|---|---|
| Ein Platz für ein Versorgungsdepot ließ sich nicht setzen. | **Platz für ein Versorgungsdepot** steht als Erstes unter Einheit setzen → Gebäude → Geld. |
| Ein Startpunkt kam genau dorthin, wo du geklickt hast, ob auf die Straße oder weit weg davon. | **An Straßen ausrichten** (standardmäßig an) setzt ihn neben die nächste Straße, so weit davon entfernt wie auf den eigenen Karten des Spiels (LittleGroove hat es gemessen). Nimm den Haken weg, um mitten auf ein Feld zu setzen. |
| Spawnpunkte waren ein paar Symbole, mit Buchstaben für das Land. | Ein Symbol für das, was jeder ist (HQ, Versorgungsdepot, Fabrik, Festung, Attrappe, Soldat, Panzer, Panzerabwehr, Artillerie, Prototyp, Flugzeug, Geschützturm), und die Kokarde des Landes. |
| Du konntest nicht sehen, wo das Match eines Spielers beginnt. | Jeder Startpunkt zeigt seine Eröffnungskamera: den Anflug (gepunktet), wo er endet, worauf sie blickt und den Teil der Karte, den der Bildschirm zeigt. |
| Die Eröffnungskamera eines verschobenen Startpunkts blieb am alten Ort. | Die Kamera zieht mit; ein neuer Startpunkt bekommt eine eigene Kamera. |
| Die Eröffnungskamera ließ sich nicht ändern. | Mit **Verschieben** die Kamera eines Starts um ihr HQ ziehen, um das Match von einer anderen Seite zu eröffnen; **Kamera zurück** macht es rückgängig. |
| Ein Startpunkt in einem Wald wurde abgelehnt. | Erlaubt: ein HQ funktioniert dort, und Versorgungslastwagen fahren durch Wälder. Nur Wasser, Klippen und gesperrter Boden werden abgelehnt. |

**0.8.2:** ein Test, der an einem Fehler in deinem Mod scheitert, sagt dir, an welchem, und behebt ihn, Mods und Karten
getrennt, klarere Kartenfarben und Spawnpunkte, und eine Spielkopie für den ganzen PC.

| Vorher | Jetzt |
|---|---|
| Ein Test, der an einem Fehler in deinem Mod scheiterte, vergrub den Grund im Log und verwies auf die Fehlersuche, die einen Mod nicht beheben kann. | Jeder Fehler wird über dem Log aufgeführt, mit einem Knopf, der ihn behebt: ein Team-Spawnpunkt auf einer Karte für KÄMPFE wird neutral gemacht oder herausgenommen (auch alle auf einmal), eine Straße, die nichts verbindet, herausgenommen. Die Fehlersuche erscheint nur bei anderen Fehlschlägen. |
| Die Meldung unten ließ sich nicht schließen. | Jede Meldung hat ein ×, um sie zu schließen. |
| Das Test-Log ließ sich nicht kopieren. | **Bericht kopieren** kopiert das Log und die Meldung, für einen Fehlerbericht oder Discord. |
| Mods und Karten teilten sich ein Menü. | Mods und Karten haben jeweils ihr eigenes Menü, und Exportieren legt die Datei direkt in die Bibliothek des Launchers. |
| Jeder Spawnpunkt auf der Karte sah gleich aus. | Jeder Spawnpunkt ist ein Gebäude-, Panzer-, Soldaten- oder Flugzeugsymbol in der Farbe seiner Seite, mit seinem Land. |
| Die Farben der Karte wurden nicht erklärt. | Eine Farblegende für Deckung, wo Einheiten hinkommen und Entfernen; die Deckung des Werkzeugs Stadt hat eine eigene Farbe; ein Durchsichtigkeitsregler für jede Ebene. |
| Hügel und Bäume ragten durch die Zonen eines Szenarios. | Zonen schweben über dem Boden, und ein Regler **Höhe der Zonen** stellt ein, wie hoch. |
| Jeder Test behielt seine eigene Kopie des Spiels. | Eine gemoddete Kopie für den ganzen PC, geteilt mit dem Launcher. |
| Die Version wurde nicht angezeigt, und Neuerungen war eine Liste. | Die Version steht neben dem Namen, und Neuerungen öffnet eine Vorher/Jetzt-Tabelle wie diese. |
| Wenige Tooltips. | Tooltips an den wichtigsten Bedienelementen, geschrieben für Spieler, die neu im Modding sind. |
| Neuen Straßen auf Twilight of the Gods, Alpha, Ostfriesland und Robert fehlte das Straßenmodell der Karte. | Sie bekommen es auch. |
| Der Build sagte, neue Straßen würden „aus der Nähe gezeichnet“. | Er sagt, dass sie von fern zu sehen sind; aus der Nähe erscheinen sie noch nicht (weiterhin ein bekanntes Problem). |

**0.8.1:** Einheiten aus jeder Nation, ein neuer Look, eine kürzere Werkzeugleiste und das Werkzeug Entfernen.
- **Einheiten aus einer anderen Nation funktionieren.** Eine neue Einheit kann in das Baumenü jeder Nation, gleich aus welcher Armee ihr Modell kommt: ein deutscher Tiger oder eine Ju 87 für die USA, auch ein japanischer Zero oder Chi-Ha. Sie wird gebaut, kämpft, zeigt ihr Bild auf ihrer Karte und ihrer Markierung und lässt sich am Boden und in der Luft auswählen, sogar in einem Match, in dem niemand die Nation spielt, aus der sie kommt (im Spiel getestet, 2026-10-02). Der Build lässt die Modelle dieser Nation in jedem Match laden; ein Match braucht etwas mehr Speicher und Ladezeit.
- **Ein neuer Look:** die Blautöne von R.U.S.E. statt Schwarz und Gold, und ein neues Logo: der Tisch des Lagezentrums.
- **Die Werkzeugleiste des Karteneditors ist kürzer.** Werkzeuge, die zusammengehören, teilen sich eine Kachel, mit einem Reiter für jedes: Gelände & Wasser, Deckung & Bewegung, Straßen & Brücken, Gebäude, Objekte & Bäume, dann Entfernen, Szenario und Prüfen. Eine Kachel öffnet sich auf dem zuletzt benutzten Reiter.
- **Werkzeug Entfernen:** zieh über die eigenen Bäume und Objekte der Karte (auch Gebäude, wenn du sie wählst), und sie sind weg, wenn der Mod gebaut wird. Die roten Kreise werden im Mod gespeichert, was sie abdecken, wird rot getönt, und die Leiste zählt, was sie wegnehmen werden. Wo Bäume verschwinden, öffnet sich der Boden für jede Einheit und verliert seine Walddeckung. Gebäude, Straßen, Sträucher und Felsen der Karte richtig zu entfernen kommt als Nächstes.
- **Das Installationsprogramm bietet eine saubere Sicherung des Spiels an**, neben der Desktop-Verknüpfung, und sagt, warum: damit kann die Fehlersuche alles wiederherstellen, was ein anderer Mod-Manager geändert hat.

**0.8.0:** der Karteneditor wird erwachsen: neue Pinsel und Docks, Brücken, die Einheiten wirklich überqueren, Wälder, die
du roden kannst, und ein Build, der die Regeln des Spiels prüft, damit, was du machst, beim ersten Mal funktioniert. Dazu
eine Fehlersuche und eine saubere Sicherung des Spiels.
- **Neu im Karteneditor:**
  - **Öffnen-Pinsel** (Bewegung): das Gegenteil von Sperren. Gib Einheiten Boden, von dem die Karte sie fernhält (alle Einheiten, Infanterie oder Fahrzeuge). Wasser zu öffnen ist erlaubt und wird gewarnt: Einheiten stehen dort auf dem Flussbett.
  - **Wald-Pinsel** (Deckung): Bäume und Deckung in einem Strich; Rückgängig nimmt beides weg.
  - **Dock Brücken:** die eigenen Brückenarten der Karte, und eine von Hand platzierte Brücke in der Länge und Drehung, die du wählst; die Wasserquerungen neuer Straßen in Gold gezeichnet.
  - **Diese Karte prüfen:** listet auf, was schiefgehen würde, bevor du testest (abgeschnittener Boden, Straßen oder Brücken, die Einheiten nicht nutzen können, nicht verbundene Straßenenden, Gebäude auf Straßen), und ein Klick auf einen Eintrag zeigt, wo.
  - Trockengelegte oder trocken angehobene Flussbetten werden vom Build für Einheiten geöffnet.
- **Die eigenen Bäume und Objekte der Karte entfernen:** `[[erase]]`-Kreise in der `scenery.toml` eines Mods (vorerst von Hand geschrieben; ein Werkzeug Entfernen im Studio ist unterwegs). Panzer fahren in einen gerodeten Wald, und Infanterie dort ist nicht mehr versteckt.
- **Platzierte Objekte stehen in jeder Größe auf dem Boden.** Ein 10× vergrößertes Gebäude schwebte in der Luft; jetzt sitzt es auf dem Boden wie die eigenen der Karte.
- **Behoben: Deckung auf den Karten, die nicht quadratisch sind** (D-Day, Frontline, Djebel, Medjez, Handshake over the Elbe und die Kampagnenkarten Tunesien, Holland und Ardennen). Dort gemalte oder entfernte Deckung (die Pinsel Deckung, Freilegen, Stadt und Wald, `cover.toml`) landete bis zu einem Kilometer von dort entfernt, wo sie gezeichnet wurde, und die Kartenansicht zeigte sie auch an dieser falschen Stelle. Beides stimmt jetzt: wenn du auf einer dieser Karten Deckung gemalt hast, sieh sie dir in der Kartenansicht noch einmal an. Quadratische Karten (Blitz und die meisten anderen) waren immer richtig.
- **Brücken funktionieren im Spiel.** Eine Straße, die du über Wasser zeichnest, bekommt die eigene Brückenart der Karte (auch die der niederländischen Karten), und Panzer, Infanterie und Versorgungslastwagen überqueren sie auf der Fahrbahn, Infanterie auf der Höhe der Fahrbahn. Brückenenden schließen an die Straßen an, die Einheiten schon nutzen, und halten Abstand zu den Gebäuden der Karte; eine Brücke, die sich nicht anschließen lässt, bleibt gesperrt, und die Notiz des Builds sagt, worauf die Straße traf und wo.
- **Der Build prüft die Regeln des Spiels.** Bei jeder Datei, die ein Mod ändert, wurde geprüft, was das Spiel mit ihr macht, und ein Mod, der im Spiel kaputtgehen würde, wird abgelehnt, mit einer Notiz, die sagt, warum, bevor irgendetwas geschrieben wird:
  - Straßen: Einheiten folgen jetzt neuen Straßen, nicht nur Versorgungslastwagen, und eine neue Straße, die an keine andere Straße anschließt, wird abgelehnt (das Straßennetz muss in einem Stück bleiben);
  - platzierte Gebäude und Sperren: Einheiten können nicht mehr hindurchfahren; neue Gebäude, Brücken und Bäume sind in jeder Entfernung zu sehen;
  - Gelände: neues Wasser ist für Einheiten gesperrt, die Karte der KI folgt deinen Wäldern, Sperren, Brücken und Gewässern, und ein Strich, der den Boden nicht ändern kann (oder den Boden einer Brücke erreicht), sagt es;
  - Einheiten: eine falsche Salve, ID, Nation oder Menüliste wird abgelehnt, Einheiten-Flags werden geprüft, und jede Flag wird in der Flag-Auswahl erklärt (die Flags 62 und 63, die das Spiel bei einer Einheit, die kein Lastwagen ist, abstürzen lassen, sind ein Fehler); eine Einheit in der Fabrik einer anderen Nation wird vorerst abgelehnt (sie ließ das Spiel beim Bauen abstürzen; sie zum Laufen zu bringen kommt als Nächstes);
  - Szenario: Spawnpunkte sind standardmäßig neutral, ein Spawnpunkt einer Einheit, deren Modelle das Match vielleicht nicht lädt, wird abgelehnt (er ließ das Spiel beim Start abstürzen), ein Start, wo Fahrzeuge nicht hinkommen, wird abgelehnt, ein verschobener Start nimmt seine Kamera mit, und Plätze werden pro Team gezählt.
- **Der Bericht des Builds** zeigt jede Warnung (manche gingen verloren), und ein Neubau nimmt zuerst die alte Testkopie weg, sodass eine alte Kopie nicht aus Versehen gestartet werden kann.
- **Quadratische Deckung:** `square = true` an einer Malung in `cover.toml` oder an einem Strich Deckung oder Freilegen in `terrain.toml` malt ein Quadrat entlang der Achsen der Karte (vorerst von Hand geschrieben; die Kartenansicht zeichnet es als Quadrat).
- **Fehlersuche** (neben *Im Spiel testen* und unter Einstellungen > Hilfe): prüft auf einmal, was einen Test verhindern kann (das Spiel gefunden, Steam, ein Spiel, das noch aus einer gemoddeten Kopie läuft, das Laufwerk und sein freier Platz, übrig gebliebene Kopien, schreibgeschützte Dateien, ob die App dort schreiben darf, wo Kopien hinkommen), mit einem Knopf für jede Korrektur, die sie machen kann, und einem Bericht zum Einfügen in einen Fehlerbericht, ohne deinen Windows-Benutzernamen.
- **Saubere Sicherung des Spiels** (Einstellungen): behalte eine saubere Kopie der Dateien deines Spiels, prüfe sie dagegen und stelle alles wieder her, was ein anderer Mod-Manager oder eine Bearbeitung von Hand geändert hat. Dateien, die nicht zum Spiel gehören, werden beiseitegelegt, nie gelöscht. Oder lass Steam das Spiel reparieren (*Mit Steam überprüfen*). Das ist der einzige Ort, an dem das Studio je in deinen Spielordner schreibt, und nur, wenn du darum bittest.
- **Teile deinen Mod:** einen Mod gemacht? Nach dem Export zeigt das Studio seine Größe und SHA-256 und wie man ihn zur Mod-Liste auf GitHub hinzufügt und Mitwirkender wird.
- **Bekanntes Problem: neue Straßen werden aus der Nähe noch nicht gezeichnet.** Sie sind auf den Boden gemalt und von fern zu sehen, und Einheiten nutzen sie, aber mit der Kamera nahe am Boden verschwindet eine neue Straße. Daran wird gearbeitet.

**0.7.6:** ein zweites Im Spiel testen funktioniert, und Brücken, die Einheiten immer erreichen können.
- **Behoben:** jedes zweite *Im Spiel testen* konnte mit „Eine alte gemoddete Kopie ... kann nicht entfernt werden ... (Access is denied)“ fehlschlagen. Eine Kopie, die Windows nicht löschen will (eine Datei, die eine ältere Version mit einer ersetzten Spieldatei verknüpft hat, ein Programm, das sie noch festhält), stoppt keinen Test mehr: sie wird nach `RUSE-Instances\.trash` beiseitegelegt und entfernt, sobald nichts sie mehr festhält. Läuft R.U.S.E. noch aus der Testkopie, wird es dir gesagt, mit dem Namen des Programms. Zweimal *Im Spiel testen* zu drücken startet einen Test, nicht zwei.
- **Behoben:** die neue Brücke einer Straße konnte das Spiel abstürzen lassen, wenn Einheiten auf sie geschickt wurden: ihre Fahrbahn erreichte keinen Boden, den Einheiten nutzen. Jedes Ende einer Brücke schließt jetzt entlang der Straße an den Boden an (bis zu 62 m Zufahrt); eine Brücke, die sich nicht anschließen lässt, bleibt für Einheiten gesperrt, mit einer Notiz, und der Build schreibt nie Boden, den Bodeneinheiten nicht erreichen können.

**0.7.4:** Im Spiel testen funktioniert, wenn die Dateien deines Spiels schreibgeschützt sind.
- **Behoben:** *Im Spiel testen* schlug jedes Mal mit „[WinError 5] Access is denied“ fehl, wenn die Dateien von R.U.S.E. schreibgeschützt sind (eine Installation von Disc, eine wiederhergestellte Sicherung): die Testkopie behielt die Markierung, sodass eine halb gebaute Kopie nie entfernt werden konnte. Die Testkopie behält die Markierung jetzt nie, und ein Überbleibsel einer älteren Version wird von selbst entfernt (die Dateien deines Spiels bleiben genau so, wie sie waren). Läuft das Spiel noch aus der Testkopie, wird dir gesagt, es zu schließen, statt dass du einen Windows-Fehler bekommst.
- **Eine Straße zeigt ihre Länge**, während du sie zeichnest, neben dem Zeiger (wie in Cities: Skylines); die Straßenwerkzeuge zeigen die Gesamtlänge deiner neuen Straßen.
- **Neue Straßen werden auf den Boden gemalt**, in der eigenen Straßenfarbe der Karte (im Spiel nachgewiesen), und **eine Straße über Wasser bekommt eine Brücke**: die eigene Art der Karte, ein Stück von Ufer zu Ufer gestreckt, wie die eigenen Brücken des Spiels, damit Einheiten hinüberkommen. Eine Straße über eine der eigenen Brücken der Karte bekommt die neue Brücke an ihrer Stelle. (Brücken sind neu: noch nicht im Spiel geprüft.)

**0.7.3:** ordne die Kartenansicht nach deinem Geschmack. Das Kartenfeld (oben links) und die Werkzeuge (unten) lassen
sich an ihrem Griff (⠿) überallhin verschieben und mit dem Pfeil daneben einklappen: das Kartenfeld bis auf seinen Titel,
die Werkzeuge bis auf ihre Leiste. Ein Doppelklick auf einen Griff setzt dieses Feld zurück. Deine Anordnung bleibt
erhalten.

**0.7.2:** Straßen, und klarere Tests.
- **Straßen zeichnen**, wie in Cities: Skylines (die Art Straßen in der Leiste): **Gerade**, **Kurve** und **Freihand**. Ein Ende nahe einer Straße rastet an ihr ein und verbindet sich mit ihr. Neue Straßen erscheinen als blaue Bänder, und **Versorgungsrouten nutzen sie** (im Spiel nachgewiesen). Sie werden noch nicht auf den Boden gemalt.
- Das Kästchen **Straßen** zeigt die eigenen Straßen der Karte in Gold.
- Die eigenen Worte des Spiels: ein Szenario wird nach dem Knopf im Hauptmenü benannt, der es spielt (**Kämpfe**, Operation, Kampagne, aus dem Text deines Spiels in deiner Sprache gelesen), und eine goldene Zeile unter dem Szenario-Menü sagt, wo es gespielt wird, z. B. *Im Spiel: Kämpfe › D-Day (6 Spieler)*.
- **Im Spiel testen** sagt, wo es gebaut hat und genau, was du öffnen musst, um deine Änderungen zu sehen (z. B. *KÄMPFE > D-Day*).
- Die mittlere Maustaste dreht die Ansicht auch im Umschau-Modus (dort zoomte sie vorher).

**0.7.1:** mehrere Einheiten auf einmal, eine Mod-Prüfung und Hilfe zur Hand.
- **Einheit setzen** platziert 1, 2, 4, 6, 8 oder 10 auf einmal, in **Linie, Kolonne, Keil, Block oder Kreis**, zum oberen Bildschirmrand gerichtet, mit einem Abstandsregler und Ringen, die zeigen, wo jede stehen wird.
- Die **Mod-Prüfung**: jede Datei deines Mods wird so gelesen, wie der Spiel-Build sie liest, wenn du den Mod wählst und vor **Im Spiel testen**. Eine rote Leiste nennt jedes Problem; eine kaputte Kartendatei kann **beiseitegelegt** werden (umbenannt, nie verloren), und ein Kartenordner, der nach dem Titel der Karte benannt ist (maps/Blitz), kann mit einem Klick in seinen Paketnamen (maps/SuperCrossRoads4) **umbenannt** werden.
- Behoben: **Wasser**-Striche wurden ohne ihre Höhe gespeichert, sodass der Spiel-Build den Mod ablehnte. Jede Datei, die das Studio schreibt, wird jetzt zurückgelesen, bevor sie gespeichert wird.
- Die Kartenliste **klappt weg** («) für mehr Platz.
- **Einstellungen > Hilfe & Community**: das Wiki (das neue Handbuch), Discussions und **Problem melden**, das einen Fehlerbericht öffnet, in dem deine Version schon eingetragen ist. Ein Fehler unten hat einen eigenen Link **Melden**. Die App sendet nichts: du liest den Bericht und postest ihn.

**0.7.0:** ein neuer Look und Bewegungswerkzeuge. Die Kartenwerkzeuge sind in eine Leiste am unteren Rand gewandert, wie in
Cities: Skylines, im eigenen HUD-Stil von R.U.S.E.: wähle eine Art (Gelände, Wasser, Deckung, Bewegung, Gebäude, Objekte,
Bäume, Szenario), und ihre Werkzeuge öffnen sich darüber; klick sie erneut an oder drück Esc, um dich nur umzusehen. Die
Auswahlen des Szenarios sind jetzt Kacheln, keine Aufklapplisten. **Bewegung:** das Kästchen **Wo Einheiten hinkommen**
zeigt es auf der Karte (rot: keine Einheit; gelb: nur Infanterie), und drei neue Pinsel sperren Boden: **Sperren** (jede
Einheit), **Infanterie sperren** und **Fahrzeuge sperren**. Gebäude, die du platzierst, halten Einheiten auf (das Kästchen
**Massiv**, standardmäßig an). Im Spiel nachgewiesen: Einheiten planen um eine gesperrte Grube herum und gehen zwischen
platzierten Türmen hindurch.

**0.6.9:** Gebäude, Objekte und Bäume, die du platzierst, sind jetzt im Spiel in jeder Zoomstufe zu sehen (nachgewiesen
auf Blitz, bis zu 8× ihrer Größe): jede Gruppe kommt in einen neuen Block, der um das nächste Dorf oder den nächsten Hof
gelegt wird, den die Karte von fern zeichnet. Auf allen 32 Karten geprüft: sonst bewegt sich nichts. Einheiten laufen noch
durch platzierte Gebäude; sie massiv zu machen kommt als Nächstes.

**0.6.8:** mach Städte und Wälder, in denen sich Einheiten verstecken können. Die Kartenansicht zeigt, wo sich Einheiten
verstecken (das Kästchen **Deckung**, in Grün), und drei neue Pinsel malen es: **Deckung**, **Freilegen** und **Stadt**
(klick auf eine Stadt: Deckung kommt um jedes ihrer Gebäude, auch um platzierte). Im Spiel nachgewiesen: Infanterie auf
gemalter Deckung ist versteckt.

**0.6.7:** platzierte Objekte gehen bis zu 10× ihrer Größe (der Größe-Regler des Werkzeugs Platzieren; [ und ] gehen in
Schritten von 0,1 bis 3×, dann in Schritten von 0,5).

**0.6.6:** die Munition ist auch nach Typ sortiert: Panzergranaten, Sprenggranaten, Flugabwehr, Maschinengewehre,
Infanteriewaffen, Panzerabwehr der Infanterie, Bomben und Raketen (die Typ-Liste über der Munition). Mods können auch
Deckung (wo sich Einheiten verstecken, wie in einem Wald) und gesperrten Boden auf eine Karte malen
(`maps/<map>/cover.toml`); das Studio-Werkzeug dafür kommt als Nächstes.

**0.6.5:** Szenarien lassen sich auf der Karte bearbeiten. **Verschieben** versetzt einen Startpunkt oder Spawnpunkt (klick
ihn an, dann dorthin, wo er hin soll; Zurücksetzen macht es rückgängig). **Einheit setzen** lässt eine Einheit oder ein
Gebäude erscheinen, wenn das Szenario beginnt: wähle ihre Art (Gebäude, Boden, Infanterie, Luft), dann ihren Typ (bei
Gebäuden: HQ, Geld, Fabriken, Festungen und Verteidigung, Attrappen; bei Einheiten: die Fabrik, die sie baut), dann die
Einheit (nach Nation) und ihre Seite. Gespeichert in der `maps/<map>/scenario.toml` des Mods. Die Einheitenliste hat
denselben Typ-Filter.

**0.6.4:** die Kartenliste hat einen Typ-Filter: alle Karten, oder nur die Gefechtskarten, Operationen, Kampagnen-, Demo-
oder Testkarten (aus den eigenen Menüs des Spiels; eine Karte kann mehreres sein). Er wird gemerkt.

**0.6.3:** ein Reiter **Einstellungen** (neben Einheiten und Karten): die Sprache, die Tasten der Kartenansicht, der
Spielordner und Updates an einem Ort, bereit für mehr.

**0.6.2:** Updates zu finden ist robuster: wenn GitHub die eine Prüfung beim Start abweist (es erlaubt 60 pro Stunde je
Internetadresse, geteilt mit allem, was daran hängt), liest das Studio stattdessen die Release-Liste von GitHub. Mods
können auch Einheiten und Gebäude in einem Szenario erscheinen lassen (`[[spawn]]` in `maps/<map>/scenario.toml`).

**0.6.1:**

- **Deine Sprache und Tasten bleiben erhalten**, über Neustarts, Updates und Neuinstallationen hinweg (sie gingen bei jedem Start verloren).
- **Szenarien so gruppiert, wie das Spiel sie nutzt:** Gefecht, Operationen, Kampagne, Demo, Test und die, die kein Menü lädt, jedes so benannt, wie die Menüs des Spiels es nennen („10. UTAH BEACH“, „Anzio“).
- **Mods können Startpunkte und Spawnpunkte verschieben** (`maps/<map>/scenario.toml`); im Spiel geprüft: das HQ startet dort, wo der Mod es hinsetzt.

**Neu in 0.6:**

- **Gelände, das im Spiel funktioniert:** Boden, den du anhebst, absenkst oder einebnest, nimmt jetzt Bewegungsbefehle an, die Kamera bleibt darüber, und Bäume und Gebäude stehen darauf. Das Rezept von DomesticNukes und seinem Claude: der Boden des Spielgeschehens bewegt sich zuerst, der gezeichnete Boden folgt ihm, und die versteckten Höhengrenzen des Spiels werden erweitert. Auf allen 32 Karten geprüft.
- **Szenarien auf der Karte:** eine Zeile „Szenario“ wählt eines der Szenarien der Karte (Gefecht, Herausforderungen, Kampagnenkapitel) und zeigt seine Zonen, Startpunkte (Säulen in der Farbe jeder Allianz), Spawnpunkte (weiße Rauten) und Ortsnamen. Zeig auf eines, um zu sehen, was es ist. Der erste Schritt dazu, Karten zu machen.

**0.5.2:**

- **Pinsel Wasser und Trockenlegen** (Wasser auf Taste 0): flute den Boden unter einer Höhe zu einem See, oder leg einen See oder Fluss trocken. Von DomesticNukes und seinem Claude, im Spiel auf Blitz geprüft.
- **Deine eigenen Tasten:** „Tasten ändern…“ unter der Hilfezeile der Kartenansicht: klick eine Aktion an, drück eine Taste. Standard setzt sie zurück.

**0.5.1:**

- **Eine Waffe behält ihr eigenes Mündungsfeuer und ihren eigenen Klang:** wenn eine Waffe die Munition einer anderen Einheit verschießt, übernimmt sie jetzt auch deren Mündungsfeuer und Schussgeräusch (die Kanone des Shermans an einem Schützen feuert wie ein Sherman). Die Waffe zeigt, welches sie abspielt.
- **Pinsel Nivellieren** (Taste 7): malt den Boden flach auf die Höhe, an der du zu ziehen beginnst.
- **WASD bewegt sich mit der Kamera**: W ist auf dem Bildschirm immer vorwärts, wie auch immer die Ansicht gedreht ist.
- Der Spielindex wird einmal neu gebaut, beim ersten Öffnen von 0.5.1 (etwa eine halbe Minute).

**Neu in 0.5:**

- **Neue Einheiten:** kopiere eine Einheit von ihrer Seite aus, benenne sie, gib ihr einen Preis und setz sie in ein Baumenü.
- **Munition und Flags:** eine Art Munition mit jeder Munition. Eine Waffe kann die Munition einer anderen Waffe verschießen (die Nation, aus der sie kommt, wird gezeigt) oder ihre eigene Kopie davon. Flag-Listen (was eine Einheit ist und tut) lassen sich bearbeiten, wie im Einheiten-Editor von RUSE Mod Manager.
- **Karten:** jede Karte zeigt ihren Namen im Spiel, in deiner Sprache, neben ihrem Codenamen. Gebäude, Objekte und Bäume werden mit **den echten 3D-Modellen und Texturen des Spiels** gezeichnet, dank DomesticNukes und seinem Claude.
- **Gelände-Pinsel:** Boden anheben, absenken, glätten und zur Rampe formen, im Mod gespeichert. **Von vorn** leert eine Karte.
- **Werkzeug Platzieren:** ein Klick platziert ein Gebäude, ein Objekt oder einen Baum. Male eine Fläche, oder klick zweimal für eine Linie (eine Hecke, eine Straße). Rückgängig nimmt eine ganze Fläche oder Linie zurück. Szenerie ist vorerst nur fürs Aussehen: Einheiten fahren hindurch.
- **Tasten:** WASD / Pfeiltasten bewegen die Ansicht, Q/E drehen sie, R/F zoomen. Fahr über einen beliebigen Knopf, um einen Tooltip zu sehen.
- **.rusemod exportieren:** eine Datei, die der Launcher installiert.
- **Es aktualisiert sich selbst:** ab dieser Version sagt eine Leiste, wenn ein neueres Studio da ist; **Jetzt aktualisieren** installiert es.

Es ist neu und wurde außerhalb des PCs des Entwicklers kaum getestet, also melde bitte alles Seltsame auf GitHub Issues.

![Die Karten von RUSE Studio: Centre of Gravity in 3D](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-maps.jpg)

![RUSE Studio in seinem Vorschaumodus, mit Beispieleinheiten](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-unit.jpg)
