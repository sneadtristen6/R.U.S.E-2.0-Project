# Animationen der Einheiten

> **Du brauchst:** RUSE Studio 0.9.8.20 oder neuer und einen Mod; Blender (kostenlos), um die Animationen einer neuen
> Einheit in Blender zu ändern · **Dauer:** 10 Minuten zum Lesen

Wie sich eine Einheit bewegt (stehen, gehen, laufen, zielen, schießen, sterben), das sind ihre **Animationen**. Diese
Seite sagt, wofür die Animationen des Spiels da sind, welche eine Einheit für jede ihrer Handlungen spielt, jeden Weg,
eine zu ändern (für eine Einheit, für alle, für die Einheiten, die du wählst, oder in Blender), und wie du die des
Spiels zurückbekommst.

## Was eine Animation ist

- Eine Animation bewegt die Knochen eines Modells über die Zeit: einen Laufschritt, ein Gewehr an der Schulter, einen
  Sturz (siehe [[Modelle und Knochen|Modelle-und-Knochen]]).
- Jede Handlung einer Einheit im Spiel (eine **Aktion**: steht still, geht, läuft, schießt...) spielt eine Animation.
  Ein Soldat spielt zwei zugleich, eine für jede Hälfte seines Körpers.
- Viele Einheiten teilen sich die Animationen des Spiels: Jeder US-Schütze läuft gleich. Eine Änderung an einer
  Animation gilt also, wenn du nichts anderes wählst, für alle Einheiten, die sie spielen.
- Panzer drehen Turm und Räder ohne Animationen: Für sie gibt es hier nichts zu ändern.

## Die Animationen des Spiels und wofür jede da ist

**RUSE Decoy** (sein Reiter oben im Studio) listet jede Animation des Spiels links unter **Animationen**, nach Art:

| Art | Was darin ist |
|---|---|
| **Infanterie** | Schützen, Panzerfaust, Fallschirmjäger und Fahrer: Stehen, Gehen, Laufen, Zielen, Schießen, Nachladen, Flucht, Treffer und Tod (Ober- und Unterkörper je eigene) |
| **Geschützbedienungen** | Die Männer am Geschütz: im Stand, beim Schieben, beim Aufbauen, beim Feuern und Nachladen |
| **Fahrzeuge und Geschütze** | Geschütze beim Auf- und Abbauen, im Stand und beim Feuern, und andere bewegliche Teile |
| **Figuren im Hauptquartier** | Die Offiziere am Kartentisch in den Szenen einer Mission (von keiner Einheit gespielt) |
| **Tiere und Kulisse** | Kühe, Pferde, Ziegen, Hühner, Möwen und Windräder auf den Karten |

Jede sagt, wie das Spiel sie nennt und wie viele Einheiten sie spielen. Auf der Seite einer Einheit heißen die
Handlungen nach dem, was die Einheit tut, so geordnet:

| Gruppe | Ihre Handlungen (einige davon) |
|---|---|
| Stillstehen | Steht still, Geht in die Hocke, Schaut sich um |
| In Bewegung | Geht, Geht rückwärts, Läuft, Läuft nach rechts, Läuft rückwärts, Flieht |
| Zielen und schießen | Zielt im Stehen, Zielt im Gehen, Schießt, Wirft eine Granate, Lädt nach |
| Die schwere Waffe | Zielt mit der schweren Waffe, Schießt mit der schweren Waffe, Hebt die schwere Waffe, Senkt die schwere Waffe |
| Getroffen werden | Wird getroffen, Wird von hinten getroffen, Wird von einer Explosion getroffen |
| Sterben | Stirbt durch Schuss, Stirbt in einer Explosion, Liegt gefallen |
| Fallschirmsprung | Springt ab, Fällt, Schwebt am Fallschirm herab, Landet |
| Handlungen einer Besatzung | Wartet, Geht mit dem Geschütz vorwärts, Geht zum Geschütz, Baut das Geschütz auf, Schießt (ein Besatzungsmitglied), Lädt das Geschütz nach |

## Seine Animationen: welche jede Handlung spielt

Eine Einheit mit eigenen Animationen (ein Modell mit eigenen Knochen: ein Pferd, ein Pferd mit Reiter, jedes Geschöpf)
hat auf ihrer Seite eine Tabelle: **Aussehen und Bewegung**, die Zeile **Geräusche und Animation**, **Mehr**, dann
**Seine Animationen**.

- **Steht still**, **Geht** und **Läuft** kommen zuerst: das Mindeste, was ein Modell braucht. Hat eine davon nichts
  Eigenes, sagt die Seite es, und was sie stattdessen spielt.
- Jede Handlung hat eine Liste der Animationen des Modells. Wähle eine oder lass die erste Zeile, **Nächste**: Sie
  spielt dann die nächstliegende, die das Modell hat, und die Zeile sagt, welche. Nächste heißt, in dieser Reihenfolge:
  eine Animation, die nach dieser Handlung benannt ist (stand oder idle, walk, run oder gallop, fire, death...), sonst
  das, was die nächstliegende Handlung spielt (Gehen spielt das Laufen, Schießen das Zielen oder das Stehen). Das Spiel
  spielt, was die Seite sagt: Das Erstellen folgt derselben Regel.
- **Alle anderen Handlungen** listet den Rest, nach Gruppen.
- **Auf langen Wegen** ist ihre letzte Zeile. Auf einem langen Weg über die Straße setzt das Spiel einen Trupp in seinen
  Lastwagen. Eine Einheit mit eigenen Animationen kann stattdessen als sie selbst reisen und eine davon in Schleife
  spielen (ihr Laufen, wenn die erste Zeile bleibt), im Tempo ihres Lastwagens. Wähle **In seinem Lastwagen**, um den
  Lastwagen zu behalten.

Eine Einheit, die von einer mit eigenen Animationen kopiert wurde, spielt dieselben.

## Eine Animation in RUSE Decoy ändern

1. Klicke auf der Seite der Einheit unter **Aussehen und Bewegung** in der Zeile **Geräusche und Animation** auf **In
   RUSE Decoy ändern**. RUSE Decoy öffnet sich mit dieser Einheit: ihre Geräusche, dann **Ihre Animationen** mit jeder
   Animation, die sie spielt. (Oder öffne den Reiter **RUSE Decoy** und wähle eine Art unter **Animationen**.)
2. Klicke bei einer Animation auf **Ansehen und ändern…**. Sie läuft in 3D auf einer Einheit, die sie spielt: Ziehen
   dreht sie, das Mausrad zoomt. Die 3D-Ansicht braucht einmal das Internet.
3. Von der Seite einer Einheit aus geöffnet, fragt die erste Zeile **Ändern für**:
   - **Nur diese Einheit**: Diese Einheit spielt ihre eigene Kopie der Animation, mit deinen Änderungen; alle anderen
     spielen sie wie vorher. Sie ist zu Beginn gewählt, außer die Animation ist schon für alle Einheiten geändert.
   - **Alle Einheiten, die sie spielen**: Die Änderung geht an die Animation selbst, für alle Einheiten, die sie
     spielen (die Zahl sagt, wie viele).
   - **Deine Kopie** und ihr Name: erscheint, wenn diese Einheit eine Kopie von dir spielt (unten); sie ist dann zu
     Beginn gewählt.
4. Ändere sie:
   - **Tempo**: 100 % ist das des Spiels, 200 % doppelt so schnell, 50 % halb so schnell. Gespeichert, wenn du loslässt.
   - **Stattdessen verwenden**: eine andere Animation desselben Körpers an ihrer Stelle (Schützen könnten so laufen, wie
     sie fliehen).
   - **Ein Knochen**, mit **Größe**, **Drehen um** und **Drehung**: ein Körperteil größer oder gedreht, die ganze
     Animation lang.
   - **Motion Capture**: die Bewegung eines echten Menschen an ihrer Stelle (siehe [[Musik und Klänge|Musik-und-Klänge]]).
5. Klicke auf **Fertig**. Jede Änderung wird sofort in deinem Mod gespeichert und kommt ins Spiel, wenn du testest oder
   exportierst.

## Eine Kopie einer Animation, für die Einheiten, die du wählst

**Diese Animation kopieren…** macht eine Kopie, die nur die Einheiten und Soldaten spielen, die du anhakst: ein eigenes
Laufen für drei deiner Trupps zum Beispiel, und nur für den Bazooka-Schützen eines vierten.

1. Klicke im Fenster der Animation auf **Diese Animation kopieren…**, gib der Kopie einen Namen (nur du siehst ihn) und
   klicke auf **Kopie machen**. Sie beginnt so, wie die Animation jetzt aussieht, und öffnet sich im selben Fenster.
2. Ändere sie wie oben.
3. Hake unter **Wer spielt sie** die Einheiten an, die die Kopie spielen: zuerst **Deine Einheiten**, dann **Die
   Einheiten des Spiels**. Unter einer Einheit, bei der mehrere Soldaten oder Teile sie spielen, hake nur einige an.
   **Einheit suchen** sucht nach Name oder Land.
4. Nichts spielt eine Kopie, bevor du eine Einheit anhakst: Die Zeile unter ihrem Namen sagt bis dahin „noch keine
   Einheit spielt sie“.

Jede Kopie steht links in RUSE Decoy unter **Deine Kopien**: Öffne sie dort, oder **Kopie löschen**. Die eigene Kopie
einer Einheit (**Nur diese Einheit**) oder eine in Blender geänderte Animation hat für diese Einheit Vorrang vor einer
Kopie: Die Liste sagt es daneben.

## Die Animationen einer neuen Einheit in Blender ändern

Für eine neue Einheit aus deinem Mod (eine Einheit des Spiels braucht zuerst eine neue Einheit aus ihr):

1. Klicke auf der Seite der Einheit auf **In RUSE Decoy ändern**. Klicke über ihren Animationen auf **Seine Animationen
   in Blender ändern**. Blender öffnet sich mit der Einheit und jeder Animation, die sie spielt, jede benannt nach dem,
   was sie darin tut, mit dem Namen des Spiels dahinter.
2. Unten in Blender listet der Action Editor sie auf: Wähle eine. **Leertaste** spielt sie ab.
3. Klicke einen Knochen an, drücke **Strg+Tab** für den Pose Mode, **R** zum Drehen (**G** verschiebt ihn), dann **I**,
   um die Pose in diesem Bild festzuhalten. Tu das in jedem Bild, das du änderst: Blender geht von selbst von einer
   festgehaltenen Pose zur nächsten.
4. Klicke oben in Blenders 3D-Ansicht auf **An das R.U.S.E. Studio senden**: Jede Animation geht mit, geändert oder
   nicht.
5. Klicke in RUSE Decoy auf **Meine Änderungen zurückholen**. Es sagt, welche geändert zurückkamen: Diese gehören jetzt
   dieser Einheit. Alle anderen Einheiten und jede Animation, die du nicht angefasst hast, bleiben wie vorher.

Bring die Knochen nur in Pose: Benenne sie nicht um, lösche sie nicht und verschiebe sie nicht im Edit Mode. Sonst
übernimmt das Studio nichts und sagt, welche Knochen.

Ein Modell mit eigenen Knochen (ein Pferd, jedes Geschöpf) sendet seine eigenen Animationen, unter ihren eigenen
Namen. Eine, die du änderst, nimmt ihren Platz ein: Jede Handlung, die sie spielte, spielt sie geändert.

## Die Animation des Spiels zurückbekommen

| Um herauszunehmen | Klicke auf | Wo |
|---|---|---|
| Eine Änderung für alle Einheiten | **Zurück zum Spiel-Original** | Die Zeile der Animation in RUSE Decoy oder ihr Fenster |
| Die eigene Kopie dieser Einheit (**Nur diese Einheit**) | **Zurück zu dem, was alle Einheiten spielen** | Die Zeile der Animation in der Liste der Einheit oder ihr Fenster |
| Die Änderungen einer Kopie (Name und Haken bleiben) | **Zurück zur Animation des Spiels** | Das Fenster der Kopie |
| Eine Kopie, ganz | **Kopie löschen** | **Deine Kopien** |
| Eine Änderung aus Blender | Mache sie in Blender rückgängig, solange dieses Blender noch offen ist, dann **Meine Änderungen zurückholen**: Sie wird auch in deinem Mod rückgängig gemacht | Blender, dann RUSE Decoy |

Die Knöpfe oben nehmen keine Änderung aus Blender heraus.

## Was Meine Änderungen zurückholen dir sagen kann

| Es sagt | Was tun |
|---|---|
| „In Blender geändert, jetzt die eigenen dieser Einheit: ...“ | Nichts: Es hat geklappt. **Im Spiel testen** zeigt es. |
| „Jede Animation kam so zurück, wie sie hinausging.“ | Nichts wurde geändert. Hast du jede Pose mit **I** festgehalten? |
| „In Blender gemacht, von noch keiner Aktion gespielt: ...“ | Eine neue Animation wird nicht übernommen. Speichere sie in Blender (**File > Save**), um sie zu behalten. |
| „Nicht zurückgesendet (in Blender gelöscht oder umbenannt), sie laufen also wie vorher: ...“ | Gib ihr in Blender ihren Namen zurück, wenn deine Änderung hinein soll. |
| „Diese laufen nur auf einer Körperhälfte ... also sind sie im Spiel vielleicht nicht zu sehen“ | Die bewegten Knochen liegen in der anderen Hälfte: Bewege die Knochen der Hälfte, die sie spielt. |
| „In Blender gemachte Knochen, die das Skelett dieser Einheit nicht hat ...“ | Ein neuer Knochen kann nicht abgespielt werden; der Rest kam an. |
| „Blenders NLA-Editor spielt diese mit eigenem Timing ...“ | Das Spiel spielt sie so, wie der Action Editor sie zeigt. |
| „Blenders Szene lief mit ... Bildern pro Sekunde, das Spiel läuft mit 30 ...“ | Stelle Blender auf 30 Bilder pro Sekunde, um das Tempo des Spiels zu sehen. |
| „In Blenders Szene ist Time Stretching an ...“ | Setze Old und New auf dieselbe Zahl, um das Tempo des Spiels zu sehen. |
| „Keine Handlung dieser Einheit spielt diese ab ...“ | Wähle eine für eine Handlung unter **Seine Animationen** auf der Seite der Einheit. |
| „Seit dem letzten Zurückholen deiner Änderungen kam nichts Neues aus Blender.“ | Klicke zuerst in Blender auf **An das R.U.S.E. Studio senden**. |

## Was schiefgehen kann

- **Im Spiel ändert sich nichts:** Eine Änderung für **Nur diese Einheit** läuft nur auf dieser Einheit, eine Kopie nur
  auf den Einheiten, die für sie angehakt sind. Eine Änderung aus Blender hat für diese Einheit Vorrang vor einer
  späteren Änderung derselben Animation mit **Nur diese Einheit** oder einer Kopie (die Regel des Studios; im Spiel noch
  nicht ausprobiert).
- **„Nur eine neue Einheit aus diesem Mod bekommt eigene Animationen“**: Die Einheit ist eine des Spiels. Mache zuerst
  eine neue Einheit aus ihr (**Neue Einheit aus dieser…** auf ihrer Seite).
- **Seine Animationen fehlt auf der Seite:** Die Tabelle gibt es nur für eine Einheit mit eigenen Animationen (ein
  Modell mit eigenen Knochen). Alle anderen Einheiten spielen die des Spiels: Ändere sie in RUSE Decoy.
- **Eine Sendung, die du nie zurückgeholt hast:** Blender erneut zu öffnen legt sie beiseite. RUSE Decoy zeigt sie mit
  **Beiseitegelegte Sendung zurückholen** und **In den Papierkorb legen** (siehe [[In Blender öffnen|In-Blender-öffnen]]).

## Was im Spiel ausprobiert wurde

- Die Animationsänderungen von RUSE Decoy für alle Einheiten, die sie spielen (Studio 0.9.8.8).
- **Nur diese Einheit**: ein Trupp, der auf der Stelle tanzt, während alle anderen Trupps wie vorher standen (November
  2026).
- **Diese Animation kopieren…**: eine Kopie, gespielt von einem Trupp und von einem Soldaten eines anderen (November
  2026).
- **Seine Animationen in Blender ändern**: ein Trupp, der mit erhobenem Arm steht und läuft, und Generische
  Reitertrupps, deren Pferde den Kopf hochhalten (November 2026).
- Die eigenen Animationen des Generischen Reitertrupps, gewählt mit **Nächste**, und das Reisen als er selbst auf langen
  Wegen (November 2026).
- Im Spiel noch nicht ausprobiert: ein Tempo, ein Ersatz oder ein Knochen, nur für eine Einheit geändert, und eine
  andere Animation, von Hand unter **Seine Animationen** gewählt.

Kommst du nicht weiter? Frag auf dem [Discord](https://discord.gg/h54t5baNsC) oder sieh unter
[[Wenn etwas schiefgeht|Wenn-etwas-schiefgeht]] nach.

**Weiter:** [[In Blender öffnen|In-Blender-öffnen]] · [[Modelle und Knochen|Modelle-und-Knochen]]

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Unit-Animations]]
