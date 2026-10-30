# Wirtschaft, KI und mehr: die Werkzeuge von LittleGroove

> **Für:** Modder · **Du brauchst:** RUSE Studio 0.9.8.1 oder neuer und einen Mod · **Dauer:** so lange du willst

Der RUSE-Mod-Manager von LittleGroove hatte Werkzeuge, die das Studio nicht hatte. Jetzt sind sie im Studio, jedes in
deinem eigenen Mod: eine Änderung wird dort sofort gespeichert, und die Dateien des Spiels werden nie angerührt.

## Reiter KI- und Spielereinstellungen

Ein Reiter in drei Teilen: **Spielereinstellungen**, **Spielregeln** und **Computerspieler**.

### Spielereinstellungen

Startgeld und Einkommen, Versorgungsdepots (Geld pro Lastwagen, Lastwagen pro Konvoi, die Zeit zwischen den Konvois),
Produktionsgrenzen und die Täuschungskarten, mit denen jede Seite beginnt. Eine Änderung gilt für jeden Spielmodus; wo
der Atommodus einen eigenen Wert hat, bekommt er ein eigenes Feld. Versorgungsdepots und Verwaltungsgebäude sind
Gebäude: ihr Preis, ihre Bauzeit und ihre Stärke stehen im Reiter **Einheiten**.
Im Spiel gesehen: das Startgeld und die Täuschungskarten zu Beginn.

**Depots auf den Karten** (unter Versorgungsdepots): gib jedem Versorgungsdepot mehr Lastwagen, also mehr Geld, auf
**Alle Karten** oder **Eine Karte:** du wählst. Multipliziere die Lastwagen jedes Depots (**mal ihre Lastwagen**) oder
gib allen dieselbe Zahl (**Lastwagen je Depot**). Die Zeile darüber sagt, was ein Depot mit deinen Werten enthält. Ein
Depot, dem du im Reiter Karten eigene Lastwagen gegeben hast, behält sie. Spiele Mods mit mehr als 1.000 Lastwagen pro
Depot mit Launcher 0.4.8.4 oder neuer. Im Spiel gesehen (die Depots von D-Day mit 500 Lastwagen; andere Karten mit
dem Dreifachen ihrer eigenen).

### Spielregeln

Jede andere Regel, die das Spiel für alle Spieler hat, in Gruppen: Schlacht und Kapitulation, Bevölkerung, Bewegung und
Straßen, Feuer und Ziele, Einheiten von selbst, Schaden und Niederhalten, Wald und Sicht, Flugzeuge, Täuschungskarten im
Einsatz, der Gamecontroller, Gebäude platzieren, Ranglistenspiele online, Umrisse und Pfeile, Effekte auf dem
Bildschirm, die Farben der Seiten und Sektoren (jede mit einem Farbwähler), und zuletzt ein paar Werte, deren Zweck noch
nicht bekannt ist. Jede Regel sagt, was sie bewirkt und welchen Wert das Spiel hat. Im Spiel noch nicht ausprobiert.

### Computerspieler

Wie die Computerspieler spielen. Ein Computerspieler mischt drei Wertesätze: **Standard**, seine Schwierigkeit und sein
Profil (beide in der Lobby des Spiels gewählt); wähle einen, um seine Werte zu sehen und zu ändern: wann er anzugreifen
beginnt, wie stark er erst werden will, wie er verteidigt, welche Einheiten er bevorzugt, und seine Täuschungskarten.
Jeder Wert lässt sich in jedem Satz ändern: ein Wert, den ein Satz nicht aufführt, zählt im Spiel als 0, und gibst du
ihm eine Zahl, kommt er in deinen Mod. Darunter steht, was für jeden Computerspieler gilt (der Armeewert, ab dem er
angreift, seine Attrappen...).
Im Spiel gesehen: eine Täuschungskarte aus dem Menü genommen, eine darin verschoben, die Dauer einer Karte, und wann
Leicht anzugreifen beginnt. Der Rest ist im Spiel noch nicht ausprobiert.

**Karten- und Missionsskripte**, darunter: die Skripte, die das Spiel auf seinen Karten ausführt (die Kapitel der
Kampagne, Herausforderungen, Operationen), als Python zum Lesen angezeigt. **Kopieren** kopiert eines.

## Das Feld Verbesserung und Forschung einer Einheit

Auf der Seite einer Einheit: die Einheit, deren Verbesserung sie ist (**Verbesserung von**), ihre eigenen
Verbesserungen, und ihr Forschungspreis und ihre Forschungszeit. Wähle eine andere Einheit oder **Keine: eine eigene
Einheit**. Siehe [[Einheiten bearbeiten|Einheiten-bearbeiten]].

## Reiter Alle Werte und Dateien

Zwei Teile, gewählt mit dem Schalter oben in der Liste.

**Alle Werte:** jedes Objekt und jeder Wert des Spiels, geändert in deinem Mod: einen Wert hinzufügen oder herausnehmen,
ein Objekt anlegen oder löschen, einem Textwert eigene Wörter geben. Im Spiel noch nicht ausprobiert.

**Dateien:** jede Datei in den Paketen des Spiels: wähle ein Paket, dann eine Datei, um sie als das zu sehen, was sie ist
(ein Bild, eine Texttabelle, ein Missionsskript...). **Kopie speichern…** speichert sie heraus; **Durch eine eigene Datei
ersetzen…** legt deine in deinen Mod; **Eine eigene Datei zu diesem Paket hinzufügen…** fügt eine neue hinzu. Dein Mod
behält nur, was du änderst, nie eine Kopie der Datei des Spiels. Im Spiel noch nicht ausprobiert.

## Missionen und Karten

Die Skripte einer Mission lassen sich ändern, und das Studio prüft, ob sie in den Menüs steht, ob jede Datei, die sie
braucht, geladen wird, und ihre Texte; sie lässt sich in ihrem Menü nach oben oder unten verschieben. Auf einer Karte:
Namen von Städten und Hügeln, benannte Punkte und Zonen, und Name und Ausrichtung eines Kartenobjekts. **Notizen** lassen
sich zu einer Einheit, einem Wert oder einem Computerspieler festhalten. Im Spiel noch nicht ausprobiert.

## Im Launcher: Alten Mod umwandeln

Ein älterer Mod, der als eigene Pakete des Spiels kommt, gemacht, um in den Spielordner kopiert zu werden, wird zu einem
Mod, den deine Bibliothek neben anderen spielt: siehe [[Installieren und spielen|Installieren-und-spielen]].

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Economy-AI-and-More]]
