# Ein Modell importieren

> **Für:** Modder · **Du brauchst:** RUSE Studio 0.9.6 oder neuer, einen Mod und ein 3D-Modell (.3ds, .glb oder .gltf) ·
> **Dauer:** ein paar Minuten

Gib einer neuen Einheit ein eigenes 3D-Modell, aus Blender oder einem anderen 3D-Programm. So entstand der
[M1-Abrams-Mod](https://github.com/sneadtristen6/Ruse-Mods): das erste Modell, das aus einem anderen 3D-Programm in
R.U.S.E. gebracht wurde, im Spiel gesehen.

Ein Modell kann auch auf ein neues Gebäude kommen, anstelle eines Teils seines Aussehens (siehe
[[Gebäude und Baumenüs|Gebäude-und-Baumenüs]]), oder als eigener Felsen, eigenes Objekt, eigener Busch oder Baum
auf deine Karte (siehe [[Gebäude und Bäume platzieren|Gebäude-und-Bäume-platzieren]]). Beides: Studio 0.9.8.8, im Spiel
gesehen.

Auf der Seite der Einheit ist all das in **Aussehen und Bewegung**: **Modell importieren…** ist die Schaltfläche der Zeile **Modell**, und die übrigen Optionen des Modells (seine Größe, **Verschieben**, **In Blender ändern**) sind unter **Mehr** dieser Zeile. **Seine Soldaten** ist eine eigene Zeile, und was die Animationen des Modells tun, steht unter **Mehr** der Zeile **Geräusche und Animation**.

## 1. Ein Modell besorgen

Eine **.3ds** mit ihren Bildern (.tga oder .png), oder eine **.glb** oder **.gltf** (die Bilder stecken darin: PNG, JPG
oder WebP). Bei einem Modell, das der Import nicht lesen kann (komprimierte Meshes, KTX2-Bilder), sagt er das und wie man
es in Blender behebt.

- **Aus Blender:** Datei > Exportieren > glTF 2.0, Format **glTF Binary (.glb)**.
- **Von einer Seite mit kostenlosen Modellen:** viele Panzer kommen als .3ds mit einem Ordner voller .tga-Bilder. Lass
  den Ordner, wie er kam: das Studio findet die Bilder neben der .3ds oder im Ordner darüber, sogar unter den gekürzten
  Namen, die .3ds-Dateien verwenden (`MAIN_DEF.TGA` für `Main_Defuse.tga`).
- Prüfe die Lizenz des Modells, bevor du deinen Mod teilst, und nenne seinen Autor in der README deines Mods.

**Was hilft:** Teile, die danach benannt sind, was sie sind. Das Studio dreht ein Teil mit *turret* im Namen (oder
*tourelle*, *tower*) mit dem Turm, und eines mit *barrel*, *gun* oder *cannon* ebenfalls. Ein Teil, das auf dem Turm
sitzt, dreht sich auch mit. Alles andere bewegt sich mit der Wanne. Die Kanone sollte gerade nach vorn zeigen.

Das Abrams-Beispiel: **„Tank Abrams“ von ags**, kostenlos auf
[downloadfree3d.com](https://downloadfree3d.com/3d-models/vehicles/tank/tank-abrams/) (eine .3ds und ihre .tga-Bilder,
Teile mit den Namen Main_Body, Main_Turre, Main_Barre...).

## 2. Die Einheit erstellen

Klicke im Reiter **Einheiten** oben auf **Neue Einheit (Modell importieren)** und wähle dann die Einheit, von der du
ausgehst (für einen Panzer einen Panzer: den Sherman für den Abrams). Gib ihr einen Namen und klicke auf **Erstellen**:
die Seite der neuen Einheit öffnet sich bei **Modell importieren…**. Das Modell der neuen Einheit wird sich drehen und
fahren wie das dieser Einheit. Die Seite einer Einheit des Spiels hat denselben Weg hinein: **Neue Einheit aus dieser…**
in der Zeile **Modell** von **Aussehen und Bewegung**. (Studio 0.9.6 hat noch keine der beiden Schaltflächen: öffne die Einheit und wähle **Neue
Einheit…** auf ihrer Seite.)

## 3. Importieren

Auf der Seite der neuen Einheit, in der Zeile **Modell** von **Aussehen und Bewegung**:

1. Klick auf **Mehr** und stell die **Größe** ein: ihre Länge im Verhältnis zur kopierten Einheit. **1** ist gleich lang; ein M1 Abrams im
   Verhältnis zu einem Sherman ist **1,36** (ihre echten Längen).
2. Klicke auf **Modell importieren…** (die Schaltfläche der Zeile) und wähle die .3ds oder .glb.

Das Studio passt es an die Einheit an: nach vorn gerichtet (dahin, wohin seine Kanone zeigt), seine Länge, dorthin
gesetzt, wo die kopierte Einheit steht, mit seinem Turm, der sich dort dreht, wo er auf deinem Modell sitzt, auf dem
Boden stehend. Seine Bilder werden zu eigenen Texturen. Die Seite zeigt es in 3D, mit den Teilen, die sich mit dem Turm
drehen. Wurde ein Bild nicht gefunden, sagt sie, welches: leg die Bilder neben das Modell und importiere es erneut.

Es wird in deinem Mod als `files/models/<the unit's name>.glb` gespeichert. **Modell der kopierten Einheit nutzen** nimmt
es wieder heraus.

**Seine Größe später:** der Schieberegler unter dem Größenfeld geht von **Winzig** bis **Riesig** (0,05 bis 20), mit
**Spielgröße** (1) und, bei einer Epocheneinheit, **Echte Größe** markiert; klicke auf **Größe ändern**, und das Modell
wird aus seiner eigenen Datei neu angepasst. Bei mehreren neuen Flugzeugen (oder Bodeneinheiten) ändert ein Klick die
Größe aller. Das Spiel liest ein Modell beim Laden, daher zeigt sich eine neue Größe ab dem nächsten Build.

**Wo es sitzt:** ein neues Modell wird auf die Mitte der Einheit gesetzt, die es kopiert, daher brauchen die meisten
Modelle hier nichts. Sitzt deines nicht richtig, nimm **Verschieben** unter der Größe, unter **Mehr** der Zeile
Modell. Dort gibst du drei Zahlen ein, **Vor**, **Rechts** und **Hoch**, in
Spieleinheiten (die Seite sagt, wie lang die kopierte Einheit in diesen Einheiten ist). Ein Minus geht in die andere
Richtung, und 0, 0, 0 setzt es dorthin zurück, wo es angepasst wurde. Klicke auf die Schaltfläche **Verschieben**, und
das Modell wird aus seiner eigenen Datei neu angepasst, um so viel verschoben; sein Turm und seine Propeller gehen mit,
also drehen sie sich weiter an der richtigen Stelle. In der 3D-Ansicht zeigt der blaue Ring, wo die kopierte Einheit
steht, und die Markierung auf dem Ring ist vorne. Eine neue Größe behält die Verschiebung. Ein Modell, das an den
Knochen der Einheit hängt (ein Soldat, eine Geschützbedienung), bleibt, wo seine Knochen sind: so eines verschiebst du
in Blender. Ein Modell, das vor Studio 0.9.8.17 importiert wurde, behält seinen alten Platz (seinen Turm auf dem Turm
der kopierten Einheit), auch mit neuer Größe, bis du es erneut importierst oder verschiebst; die Modelle der
Epocheneinheiten behalten ihren.

**Flugzeuge:** ein Flugzeug, das aus dem Studio in Blender geöffnet und zurückgeholt wird, zeigt nach vorn und behält
seine Propeller dort, wo dein Modell sie hat, so viele, wie es hat, egal, was das kopierte Flugzeug hatte:
Propellerblätter am Boden, drehende Scheiben in der Luft. Im Spiel gesehen. Ein Modell von anderswo behält seine
Propeller so, wie sie gezeichnet sind, stillstehend: der Import kann noch nicht erkennen, welche seiner Teile Propeller
sind. In der 3D-Ansicht erscheinen die Scheiben eines Flugzeugs durchscheinend, so wie das Spiel einen drehenden
Propeller zeichnet.

**Soldaten, Geschützbedienungen und mehr Flugzeuge:** Soldaten, die Bedienung eines Geschützes und die Flugzeuge, an die
das Studio vorher kein Modell anpassen konnte (zum Beispiel die P-47), bekommen auch ein eigenes Modell, wenn es an den
Knochen der Einheit hängt: etwa eines der Modelle des Spiels, aus dem Studio in Blender geöffnet und dort geändert. Es
kommt so, wie es ist, auf diese Knochen, nichts verschoben oder skaliert, und die anderen Männer eines Trupps, die mit
demselben Modell gezeichnet werden, tragen es auch. Im Spiel gesehen mit einem Schützentrupp, einer Geschützbedienung
und der P-47. Ein Soldat mit schwerer Waffe, den das Spiel mit einem eigenen Modell zeichnet (der Bazooka-Mann des
US-Schützentrupps), behält es, bis du ihm unter **Seine Soldaten** (weiter unten) eins gibst.

**Deine Spieler:** ein Mod mit einem Modell, das mit Studio 0.9.8.17 oder neuer importiert wurde, braucht Launcher
0.4.8.17 oder neuer: ein älterer Launcher gibt dem Modell das Skelett der kopierten Einheit, sodass sich sein Turm um
den falschen Punkt dreht. Version 0.4.8.17 ist ein notwendiges Update, also installiert der Launcher es von selbst.

## Dein eigener Soldat, Schritt für Schritt

Bei einem Trupp (Schützen, Fallschirmjäger, jede Infanterie) macht das Studio den Blender-Teil mit dir:

1. **Erstelle den Trupp** wie in Schritt 2 oben, ausgehend von einem Trupp (etwa den US-Schützen).
2. **Öffne seinen Soldaten in Blender.** Klicke auf der Seite des neuen Trupps unter **Eigenes Modell** auf **In Blender ändern**. Blender öffnet sich mit dem Soldaten und seinen Knochen, jeder dort, wo das Spiel ihn hat. Noch kein Blender? **Blender holen (kostenlos)** installiert es; **Blender auswählen…** zeigt dem Studio, wo es ist.
3. **Ändere ihn, oder setze dein eigenes Modell auf seine Knochen.** Zum Ändern bearbeite ihn dort. Für ein eigenes Modell: hole es mit **File > Import** in dieselbe Szene und lege es auf den Soldaten; klicke dein Modell an, **Umschalt+Klick** auf die Knochen, dann **Strg+P > With Automatic Weights**. Lösche den Soldaten des Spiels, wenn du ihn nicht behältst.
4. **Sende es.** Klicke oben in Blender auf **An das R.U.S.E. Studio senden**.
5. **Hol es zurück.** Klicke im Studio auf **Modell zurückholen**. Die Schützen des Trupps tragen dein Modell. Ein Trupp, dessen Soldaten mit schwerer Waffe das Spiel mit einem eigenen Modell zeichnet (etwa der Bazooka-Mann des US-Schützentrupps), behält ihn so, wie ihn der kopierte Trupp hat, bis du ihm eins gibst: die Zeile **Seine Soldaten** zeigt jeden von ihnen, und sein **Modell importieren…** ist nur für ihn. **Im Spiel testen** zeigt es.

Gut zu wissen:
- Deine Blender-Dateien bleiben im Ordner deines Mods: `Documents\RUSE 2.0\Mods\<dein Mod>\blender\<Name der Einheit>\`. Sie werden nicht in deinen Mod gepackt, wenn du ihn teilst. Das nächste **In Blender ändern** beginnt mit dem, was du zuletzt gesendet hast.
- Haben einige Punkte deines Modells keinen Knochen (Blenders automatische Gewichte lassen ein paar aus), sagt die Seite, wie viele: Sie bewegen sich nur mit der Hüfte des Soldaten. Male sie in **Weight Paint** auf einen Knochen und sende erneut.
- Ein Trupp mit **Eigene Uniform**: Dein Modell nimmt den Platz der Uniform ein (ihre Bemalung bleibt im Mod), und **Modell der kopierten Einheit nutzen** gibt die Uniform zurück.
- Hast du schon eine .glb auf den Knochen des Spielsoldaten? **Modell importieren…** nimmt sie, wie sie ist.
- Das Modell, das dein Trupp trägt, liegt im Ordner deines Mods als `files\models\<Name der Einheit>.glb`, sobald es drin ist; das eigene des Soldaten mit schwerer Waffe als `files\models\<Name der Einheit>@bazooka.glb`.
- **Seine Soldaten** sagt auch, welche anderen Figuren des Trupps mit welchem Modell gezeichnet werden: der gefallene Soldat und die Figur aus der Ferne (die des US-Schützentrupps mit dem Modell seines Bazooka-Manns).

## Seine Animationen: welche jede Handlung abspielt

Ein Modell auf eigenen Knochen (ein Pferd, ein Pferd mit Reiter, jedes Wesen) bringt seine Animationen mit. Auf der
Seite der Einheit zeigt **Seine Animationen**, was die Einheit für jede Handlung im Spiel abspielt:

- **Steht still**, **Geht** und **Läuft** kommen zuerst: das Mindeste, was ein Modell braucht. Hat eine davon nichts
  Eigenes, sagt die Seite das und was sie stattdessen spielt.
- Jede Handlung ist eine Liste der Animationen des Modells. Wähle eine oder lass **Nächste**: Dann spielt sie die
  ähnlichste, die das Modell hat, und die Liste sagt welche. Nächste heißt, der Reihe nach: eine Animation, die nach
  der Handlung benannt ist (stand oder idle, walk, run oder gallop, fire, death...), sonst was die nächste Handlung
  spielt (ein Gehen das Laufen, ein Laufen das Gehen, dann das Stehen; ein Schuss das Zielen, dann das Stehen; jeder
  Tod den einfachen Tod). Der Build folgt derselben Regel: Was die Seite sagt, spielt das Spiel.
- Eine Animation, deren Name mit t_ oder b_ beginnt (hr_t_fire, hr_b_run), spielt nur auf der oberen oder unteren
  Körperhälfte: die eines Reiters oben, die seines Pferdes unten.
- **Alle anderen Handlungen** listet den Rest auf, nach Art: Stillstehen, in Bewegung, Zielen und Schießen, die schwere
  Waffe, Getroffen werden, Sterben.
- **Auf langen Wegen** setzt das Spiel einen Trupp in seinen Lastwagen. Eine Einheit mit eigenen Animationen geht
  stattdessen selbst und spielt die dort gewählte Animation (ihr Laufen bei Nächste), so schnell wie ihr Lastwagen.
  Wähle **In seinem Lastwagen**, um den Lastwagen zu behalten.

**Eine Kopie behält ihre Animationen:** Eine Einheit, die von einer mit eigenen Animationen kopiert wurde, spielt
dieselben. Um eine nur für sie zu ändern, klick auf **In RUSE Decoy ändern** in ihrer Zeile **Geräusche und Animation**, dann **Nur diese Einheit**.

Die so im Studio gemachte Horse Squad lief im Spiel (November 2026).
## Ein Modell mit eigenen Knochen und Animationen

Ein Pferd, ein Pferd mit Reiter, irgendein Tier: Ein Modell auf eigenen Knochen kommt mit seinen Animationen auf einen Trupp.

1. **Mach es in Blender**: dein Modell auf einer Armature mit eigenen Knochen (benannt, wie du willst) und eine Action für jede Animation. Benenne die Actions nach dem, was sie zeigen: mindestens **stand** (oder **idle**), **walk** und **run**; **death**, **fire**, **reload**, **hit**, **crouch**, **aim**, **look**, **flee** und **grenade** werden auch erkannt.
2. **Exportiere es**: **File > Export > glTF 2.0**, Format **glTF Binary (.glb)**, mit angehaktem **Animation**.
3. **Erstelle den Trupp** wie in Schritt 2 oben. Klicke auf seiner Seite in der Zeile **Modell** von **Aussehen und Bewegung** auf **Modell importieren…** und wähle deine .glb. Das Studio sieht, dass seine Knochen nicht die des Soldaten sind, und nimmt es mit seinen eigenen Knochen und allen Animationen. Die Seite zeigt, wie viele Knochen es hat, jede Animation mit ihrer Länge und wie viele Aktionen des Trupps sie spielen.
4. **Im Spiel testen** zeigt es.

Gut zu wissen:
- Jede Aktion des Trupps spielt die Animation, die nach ihr benannt ist. Eine Aktion, nach der keine Animation benannt ist, hat noch keine: Die Seite sagt, wie viele.
- In Blender geändert? Importiere es erneut: Jede Aktion behält ihre Animation, solange eine Animation dieses Namens noch in der Datei ist.
- Dein Mod behält das Modell und jede Animation: `files\models\<Name der Einheit>.glb`, und jede Animation als `files\anim\own\<Name der Einheit>\<ihr Name>.baf`.
- **Modell der kopierten Einheit nutzen** nimmt das Modell wieder heraus, mit seinen Animationen.
- Ein Trupp mit einem Soldaten mit schwerer Waffe: Gib ihm unter **Seine Soldaten** sein eigenes Pferd mit Reiter, auf denselben Knochen gebaut wie das der Schützen, dann spielt er ihre Animationen. Auf anderen Knochen spielt er, was er im kopierten Trupp spielte, und die Seite warnt dich: Das kann das Spiel anhalten. Nimmst du das Modell der Schützen heraus, geht seines mit.
- Die so im Studio gemachte Horse Squad lief im Spiel (November 2026); nichts anderes, das so gemacht wurde, ist bisher im Spiel ausprobiert.

## 4. Seine Karte, dann testen

Dreh die 3D-Ansicht, bis das neue Modell im gestrichelten Rahmen richtig aussieht, und klicke auf **Diese Ansicht als
Karte nehmen** (siehe [[Einheiten bearbeiten|Einheiten-bearbeiten]]). Dann **Im Spiel testen**: die Einheit steht in einer
Schlacht bei ihrer Fabrik.

## In Blender ändern

`files/models/<the unit's name>.glb` öffnet sich in Blender wie jede .glb. Behalte die zwei Objektnamen (`chassis` für
die Wanne, `tourelle_01` für den Turm) und exportiere sie über dieselbe Datei (glTF Binary): der nächste Build nutzt sie.

**In Blender öffnen** auf der Seite einer Einheit benennt den Knochen jedes Teils so, wie das Spiel es tut, damit ein
Panzer des Spiels, in Blender geöffnet und zurück importiert, seinen Turm drehen kann (Studio 0.9.8.8; ein vorher
exportiertes Modell behält seine alten Namen: öffne es erneut in Blender).

**Ein Modell, das am falschen Platz saß** (Studio 0.9.8.7 und älter, auf neuen Einheiten aus dem Panther und 85 anderen
Einheiten, deren Türme das Studio falsch gelesen hat): nutze **Modell importieren…** erneut auf dieser Einheit, und es
sitzt auf dem Turm.

## Noch früh

- Ketten und Räder drehen sich noch nicht: sie bewegen sich mit der Wanne.
- Das Mündungsfeuer der Kanone und das Wrack sind die der kopierten Einheit.
- Bilder werden höchstens 1024 breit gemacht, wie die eigenen Einheitenbilder des Spiels.
- Im Spiel ausprobiert mit den eigenen Modellen des Spiels (dem Sherman, zwei Flugzeugen, einem Schützentrupp, einer
  Geschützbedienung): noch nicht mit einem Modell von anderswo, einem anderen Panzer mit Turm, einem Turm, der sich ganz
  herumdreht, oder einem Flugzeug, das eine Einheit ohne Propeller kopiert.

Über die Befehlszeile: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. Mit `--move` wird es so angepasst, wie das Studio es
anpasst: `--move 50 0 -10` schiebt es von der angepassten Stelle 50 nach vorn und 10 nach unten (vor, rechts, hoch), und
`--move 0 0 0` lässt es dort. Ohne `--move` passt der Befehl es weiter auf die alte Art an, mit seinem Turm auf dem Turm
der kopierten Einheit.

**Weiter:** [[Exportieren und teilen|Exportieren-und-teilen]]

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Import-a-Model]]
