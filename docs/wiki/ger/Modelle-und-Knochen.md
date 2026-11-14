# Modelle und Knochen

> **Du brauchst:** RUSE Studio 0.9.8.20 oder neuer, einen Mod mit einer neuen Einheit darin und Blender (kostenlos),
> um Knochen zu ändern · **Dauer:** 10 Minuten zum Lesen

Soldaten, Pferde und jedes Geschöpf bewegen sich in R.U.S.E., weil ihr 3D-Modell **Knochen** hat. Diese Seite sagt,
was Knochen sind, wie das Spiel sie nutzt und was jedes Feld über Knochen auf der Seite einer Einheit bedeutet und was
du damit tust. Ein Panzer dreht Turm und Räder ohne Animationen, darum geht es auf dieser Seite vor allem um Soldaten,
Pferde und Geschöpfe.

## Was Knochen sind

- Ein **Modell** ist eine Hülle aus Punkten, mit Bildern darauf gemalt.
- In ihm stecken, wie ein Skelett, **Knochen**: ein Oberarm, ein Unterarm, eine Hand, der Kopf, jedes Bein eines
  Pferdes. Jeder Knochen hängt an einem anderen (die Hand am Unterarm, der Unterarm am Oberarm), bis zurück zum ersten
  Knochen.
- Jeder Punkt der Hülle folgt einem Knochen oder ein paar davon: Die Punkte eines Ärmels folgen dem Arm. Wie stark ein
  Punkt jedem Knochen folgt, ist sein **Gewicht**.
- Eine **Animation** bewegt die Knochen, Bild für Bild, und die Hülle folgt ihnen. So geht, zielt und fällt ein Soldat.
- In Blender sind die Knochen eines Modells ein einziges Objekt, die **Armature**.

## Wie das Spiel sie nutzt

- Das Spiel bewegt die Knochen eines Modells **nach ihrem Platz in seiner Knochenliste**, nicht nach ihren Namen. Eine
  Animation für ein Modell passt also nur zu einem Modell mit denselben Knochen in derselben Reihenfolge.
- Manche Knochen haben eine Aufgabe: Ein Schuss geht von einem Knochen an der Mündung der Waffe aus, der Oberkörper
  dreht sich an einem Knochen der Wirbelsäule zum Ziel, eine Waffe wird an einem Knochen gezeigt und versteckt, ein Turm
  oder ein Rad dreht sich an einem. Die Seite der Einheit nennt jeden, der deinem Modell fehlt (siehe **Funktioniert es
  im Spiel?** unten).
- Ein Soldat spielt **zwei Animationen zugleich**: eine auf der oberen Hälfte seines Körpers (zielen, schießen) und eine
  auf der unteren (gehen, laufen). Ein Pferd und sein Reiter auch: siehe **Seine zwei Hälften** unten.
- Das Spiel wurde noch nie gesehen, wie es ein Modell mit mehr als 64 Knochen animiert.

## Zwei Arten von Modellen

| | Auf den Knochen des Spielsoldaten | Mit eigenen Knochen |
|---|---|---|
| **Was es ist** | Ein in Blender geänderter Soldat oder ein eigenes Modell auf den Knochen eines Soldaten | Ein Pferd, ein Pferd mit Reiter, jedes Geschöpf, in Blender auf eigenen Knochen gemacht |
| **Wie du es machst** | **In Blender öffnen** auf der Karte des Trupps: Jeder Soldat öffnet sich mit seinen Knochen (siehe [[In Blender öffnen|In-Blender-öffnen]]) | In Blender, dann **Ein Modell importieren…** auf der Karte des Trupps (siehe [[Ein Modell importieren|Ein-Modell-importieren]]) |
| **Seine Animationen** | Die des Spiels, wie beim Soldaten | Seine eigenen, aus seiner Datei |
| **Seine zwei Hälften** | Die des Spiels: nichts zu wählen | Du wählst sie (das Studio schlägt den Knochen vor) |
| **Seine Größe und sein Platz** | Wie du es in Blender gemacht hast, auf seinen Knochen | Wie in seiner Datei |

Die Seite sagt, welches es ist. Bei einem Modell auf den Knochen des Spielsoldaten: „Dein Modell sitzt auf den Knochen
des Spielsoldaten und behält die zwei Hälften des Spiels: nichts zu wählen.“ Bei einem Modell mit eigenen Knochen: „Es
hat eigene Knochen:“ und wie viele. Der **Generische Reitertrupp** (Reiter **Einheiten**, **Zweiter Weltkrieg+**) ist
ein Trupp mit eigenen Knochen: siehe [[Einheiten aus anderen Epochen|Einheiten-aus-anderen-Epochen]].

## Wo die Seite sie zeigt

Auf der Seite einer neuen Einheit steht alles über Knochen unter **Aussehen und Bewegung**:

| Feld | Wo | Was es dir sagt |
|---|---|---|
| **Seine Knochen und Animationen** | Die Zeile **Geräusche und Animation**, **Mehr** | Wie viele Knochen das Modell hat, und jede Animation mit ihrer Länge und wie viele Handlungen der Einheit sie spielen (ein Modell mit eigenen Knochen) |
| **Seine zwei Hälften** | Die Zeile **Geräusche und Animation**, **Mehr** | Wo sich das Modell in obere und untere Hälfte teilt |
| **Seine Animationen** | Die Zeile **Geräusche und Animation**, **Mehr** | Welche Animation die Einheit für jede ihrer Handlungen spielt: siehe [[Animationen der Einheiten|Animationen-der-Einheiten]] |
| **Funktioniert es im Spiel?** | Die Zeile **Modell**, **Mehr**; auf der Seite eines Trupps **Weitere Optionen** unter den Soldaten, dann **Das Modell jedes Soldaten** | Was am Modell das Spiel anhalten oder falsch aussehen könnte, und wie du es behebst |
| Punkte ohne Knochen | Dort, wo **Funktioniert es im Spiel?** steht | Wie viele Punkte des Modells keinem Knochen folgen |

## Seine zwei Hälften

Das Spiel spielt auf einem Soldaten zwei Animationen zugleich: eine auf seiner **oberen Hälfte** (zielen, schießen) und
eine auf seiner **unteren Hälfte** (gehen, laufen). Ein Reiter zielt und schießt, während sein Pferd läuft: Der Reiter
ist die obere Hälfte, das Pferd die untere.

- Ein Modell auf den Knochen des Spielsoldaten behält die Hälften des Spiels: Die Seite sagt „nichts zu wählen“.
- Ein Modell mit eigenen Knochen teilt sich an **einem Knochen**: Dieser Knochen und alle Knochen darunter bilden die
  obere Hälfte, alle anderen die untere.

So wählst du ihn:

1. Klicke auf der Seite der Einheit unter **Aussehen und Bewegung** in der Zeile **Geräusche und Animation** auf
   **Mehr**.
2. Unter **Seine zwei Hälften** zeigt die Liste **Obere Hälfte beginnt bei** zuerst den Vorschlag des Studios, markiert
   mit „(vorgeschlagen)“. Das Studio schlägt bei einem Pferd mit Reiter den ersten Knochen des Reiters vor (**bip01**
   beim Generischen Reitertrupp), sonst den ersten Knochen namens spine (wie bei einem Soldaten), sonst den Knochen, an
   dem sich das Skelett zum ersten Mal verzweigt.
3. Für die meisten Modelle passt der Vorschlag: Lass ihn. Um ihn zu ändern, wähle einen anderen Knochen in der Liste.
   Das wird sofort gespeichert und ist nach dem nächsten Erstellen im Spiel zu sehen (**Im Spiel testen**).
4. Unter der Liste zählt die Seite die Knochen jeder Hälfte, und **Welcher Knochen wohin gehört** listet jeden Knochen
   des Modells, markiert mit obere Hälfte oder untere Hälfte.
5. Um zum Vorschlag zurückzukehren, wähle wieder die erste Zeile der Liste.

Eine andere Teilung als die vorgeschlagene wurde im Spiel noch nicht ausprobiert.

## Gewichte: welchem Knochen jeder Punkt folgt

Wenn du ein eigenes Modell (oder einen Helm, einen Rucksack, eine Waffe) auf die Knochen eines Soldaten setzt, muss
Blender wissen, welchem Knochen jeder seiner Punkte folgt. Das sind Blenders eigene Schritte.

**Dein Modell auf einem Soldaten, jeder Punkt folgt den nächsten Knochen:**

1. Klicke auf der Karte des Trupps auf **In Blender öffnen**: Blender öffnet sich mit den Soldaten, jeder auf seinen
   Knochen.
2. Importiere in Blender dein Modell mit **File > Import** und setze es über den Soldaten.
3. Klicke dein Modell an, dann **Umschalt+Klick** auf die Knochen des Soldaten: die Knochen zuletzt.
4. Drücke **Strg+P** und wähle **With Automatic Weights**. Blender berechnet die Gewichte für dich.
5. Lösche, was du nicht behältst (die Form des Spielsoldaten, wenn dein Modell seinen Platz einnimmt), aber behalte
   seine Knochen.
6. Klicke oben in Blenders 3D-Ansicht auf **An das R.U.S.E. Studio senden**, dann im Studio auf **Meine Änderungen
   zurückholen**.

**Ein steifes Teil, das nur einem Knochen folgt (ein Helm auf dem Kopf):**

1. Klicke in Blender den Helm an, dann **Umschalt+Klick** auf die Knochen des Soldaten.
2. Drücke **Strg+Tab** für den Pose Mode und klicke den Kopfknochen an.
3. Drücke **Strg+P** und wähle **Bone**. Der Helm bewegt sich jetzt mit dem Kopf, und nur er bekommt ihn, wenn du
   deine Änderungen zurückholst.

**Punkte ohne Knochen.** Blenders automatische Gewichte vergessen manchmal ein paar Punkte. Die Seite sagt dann „{n}
Punkt(e) deines Modells haben keinen Knochen und bewegen sich nur mit der Hüfte des Soldaten.“ So behebst du es:

1. Wieder **In Blender öffnen**.
2. Klicke dein Modell an und stelle Blenders Modus (oben links in der 3D-Ansicht) von **Object Mode** auf **Weight
   Paint**.
3. In den Eigenschaften des Modells (das grüne Dreieck) hat **Vertex Groups** eine Gruppe pro Knochen: Wähle den
   Knochen, dem diese Punkte folgen sollen.
4. Male über die Punkte.
5. **An das R.U.S.E. Studio senden**, dann **Meine Änderungen zurückholen**.

## Funktioniert es im Spiel?

Das Studio prüft ein Modell auf Knochen gegen die Animationen, die es spielt, und gegen die Teile und Schüsse der
Einheit, die es kopiert. Das Erstellen des Mods prüft noch einmal, mit all deinen Änderungen. Ein Problem hält dich nie
auf: Es sagt, was passieren wird und wie du es behebst.

**Wo:** auf der Seite einer neuen Einheit, **Aussehen und Bewegung**, die Zeile **Modell**, **Mehr**. Auf der Seite
eines Trupps: **Weitere Optionen** unter den Soldaten, dann **Das Modell jedes Soldaten**.

Wenn alles stimmt, sagt es: „Nichts gefunden, was das Spiel anhalten würde: Jede Animation, die es spielt, hat seine
Knochen, und jeder Knochen, den seine Teile und Schüsse brauchen, ist da.“ (mit der Zahl der Knochen).

### Was jede Antwort bedeutet

Jedes Problem sagt drei Dinge: was nicht passt, was das Spiel damit macht und wie du es behebst. Die mittlere Zeile ist
eine von diesen:

| Die Seite sagt | Was es bedeutet | Was tun |
|---|---|---|
| Das kann das Spiel anhalten: In einem Test ist es passiert. | Das Spiel hielt in einem unserer Tests so an. | Vor dem Testen beheben. |
| Das kann das Spiel anhalten (im Spiel noch nicht ausprobiert). | Es wird erwartet, dass das Spiel anhält. | Vor dem Testen beheben. |
| Das Spiel spielt es, aber es wird falsch aussehen (im Spiel noch nicht ausprobiert). | Die falschen Knochen würden sich bewegen. | Beheben, oder testen und hinsehen. |
| Die Einheit kämpft weiter, aber ihre Schüsse sieht man nicht: In einem Test ist es passiert. | Sie richtet Schaden an, aber kein Schuss ist zu sehen. | Den Knochen hinzufügen, den die Seite nennt. |
| Im Spiel noch nicht ausprobiert: Das Spiel animiert es vielleicht nicht. | Mehr Knochen, als das Spiel je animiert gesehen wurde. | Knochen zusammenfügen oder löschen. |
| Es funktioniert trotzdem, ist aber vielleicht nicht, was du willst. | Ein Hinweis zu seinen zwei Hälften. | **Seine zwei Hälften** prüfen. |

### Jedes Problem und seine Behebung

**Animationen, die nicht zu den Knochen des Modells passen.** Die Seite sagt, wie viele Animationen, für wie viele
Handlungen, und warum sie nicht passen: „Sie bewegen {a} Knochen, und dein Modell hat {b}.“ (oder „nur {b}“), oder so
viele Knochen „mit anderen Namen“ oder „in anderer Reihenfolge“. Diese Animationen wurden für andere Knochen gemacht.

- Wenn die Einheit die Animationen des Spiels auf deinem Modell spielt: Gib diesen Handlungen eigene Animationen deines
  Modells. **Modell importieren…** bringt jede Animation aus der Datei deines Modells mit, und unter **Seine
  Animationen** wählst du, welche jede Handlung spielt ([[Animationen der Einheiten|Animationen-der-Einheiten]]).
- Wenn es die eigenen Animationen deines Modells sind, gemacht für ein anderes Modell: Mache sie in Blender auf den
  Knochen dieses Modells neu und importiere das Modell erneut.

**Ein Knochen, den die Einheit braucht.** Zum Beispiel: „Schützen: Schüsse gehen von einem Knochen namens Fx_Tir_01
aus, und dein Modell hat keinen.“ (oder: der Oberkörper dreht sich dort zum Ziel, eine Waffe wird dort gezeigt und
versteckt, ein Teil wird dort gehalten, ein Turm oder ein Rad dreht sich dort, der Körper ruht dort, ein gezogenes
Geschütz hängt sich dort an). So fügst du den Knochen in Blender hinzu:

1. Öffne das Modell in Blender: **In Blender öffnen** mit angehakten **Seine Knochen** (siehe
   [[In Blender öffnen|In-Blender-öffnen]]) oder deine eigene Blender-Datei.
2. Klicke die Knochen (die Armature) an und drücke **Tab** für den Edit Mode.
3. Drücke **Umschalt+A**: Ein neuer Knochen erscheint dort, wo Blenders 3D-Cursor ist.
4. Drücke **F2** und tippe genau den Namen, den die Seite nennt (zum Beispiel `Fx_Tir_01`). Hat dein Modell den Knochen
   unter einem anderen Namen, benenne lieber diesen um.
5. In den Eigenschaften des Knochens (das Knochensymbol) setze unter **Relations** bei **Parent** den Knochen, mit dem
   sich das Teil bewegt: für einen Schuss den Knochen, mit dem sich die Waffe bewegt.
6. Drücke **G** und schiebe den neuen Knochen dorthin, wo das Teil hingehört: für einen Schuss an das Ende des Laufs.
7. Drücke wieder **Tab**, klicke auf **An das R.U.S.E. Studio senden**, dann auf **Meine Änderungen zurückholen** (oder
   exportiere deine eigene Datei und klicke auf **Anderes importieren…**). **Funktioniert es im Spiel?** prüft das Modell
   erneut.

**Zu viele Knochen.** „Dein Modell hat {n} Knochen. Das Spiel animiert, soweit gesehen, kein Modell mit mehr als 64.“
Füge in Blender Knochen zusammen oder lösche welche, bis es 64 oder weniger hat, dann hole das Modell zurück.

**Die Teilung.** „Die Teilung bei {bone}, dem ersten Knochen deines Modells, legt alle Knochen in die obere Hälfte,
also bewegen die Animationen der unteren Hälfte (gehen, laufen) nichts.“: Wähle unter **Seine zwei Hälften** einen
Knochen weiter unten, wo der Oberkörper beginnt. „Der Knochen, den du für die Teilung gewählt hast, {bone}, ist nicht
mehr in deinem Modell, also teilt es sich bei {used}.“: Wähle den Knochen erneut.

**Das zweite Modell eines Trupps auf anderen Knochen.** „Sein Modell hat eigene Knochen, die nicht die des Modells
deiner Schützen sind: Er spielt also, was er in der kopierten Einheit spielte, gemacht auf den Knochen des
Spielsoldaten, und das kann das Spiel anhalten.“ Das Modell eines Soldaten mit schwerer Waffe muss auf denselben
Knochen wie das der Schützen sitzen, um ihre Animationen zu spielen: Mache seines in Blender aus dem Modell der
Schützen, dann importiere es in seiner Zeile. Nimmst du das Modell der Schützen heraus, geht seines mit.

## Ein Modell mit eigenen Knochen in Blender machen

1. **Seine Knochen:** dein Modell auf einer Armature mit eigenen Knochen, benannt, wie du willst, und seine Gewichte
   (**Strg+P > With Automatic Weights**, oben).
2. **Seine Animationen:** eine Action pro Animation (in Blender **Dope Sheet > Action Editor**). Benenne jede nach dem,
   was sie zeigt: mindestens **stand** (oder **idle**), **walk** und **run** (oder **gallop**); **fire**, **aim**,
   **reload**, **hit**, **death**, **crouch**, **look**, **flee** und **grenade** sind auch bekannt. Ein Name wie
   **t_fire** (oder **hr_t_fire**) läuft nur auf der oberen Hälfte, **b_run** (oder **hr_b_run**) nur auf der unteren:
   die eines Reiters und seines Pferdes.
3. **Exportiere es:** **File > Export > glTF 2.0**, Format **glTF Binary (.glb)**, mit angehaktem **Animation**.
4. **Importiere es** auf einen neuen Trupp: siehe [[Ein Modell importieren|Ein-Modell-importieren]].
5. **Prüfe seine Seite:** **Seine Knochen und Animationen** (jede Animation ist angekommen, und wie viele Handlungen
   jede spielen), **Seine zwei Hälften**, **Seine Animationen**, **Funktioniert es im Spiel?**
6. **Im Spiel testen.**

Später in Blender geändert? Importiere es erneut: Jede Handlung behält ihre Animation, solange eine Animation dieses
Namens noch in der Datei ist.

## Was im Spiel ausprobiert wurde

- Der Generische Reitertrupp, so gemacht (Schützen und ein Bazooka-Schütze auf Pferden, ein Modell mit eigenen
  Knochen): Sie schießen, reisen auf langen Wegen als sie selbst, und jedes Pferd fällt mit seinem Reiter (November
  2026).
- Ein Soldat eines Trupps, in Blender auf den Knochen des Spielsoldaten geändert, mit dort gewichteten Punkten (November
  2026).
- Im Spiel noch nicht ausprobiert: eine andere Teilung als die vorgeschlagene, und jedes Problem, das die Seite mit „im
  Spiel noch nicht ausprobiert“ markiert.

Kommst du nicht weiter? Frag auf dem [Discord](https://discord.gg/h54t5baNsC) oder sieh unter
[[Wenn etwas schiefgeht|Wenn-etwas-schiefgeht]] nach.

**Weiter:** [[Animationen der Einheiten|Animationen-der-Einheiten]] · [[In Blender öffnen|In-Blender-öffnen]]

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Models-and-Bones]]
