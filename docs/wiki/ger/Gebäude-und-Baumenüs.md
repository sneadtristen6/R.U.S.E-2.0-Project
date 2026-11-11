# Gebäude und Baumenüs

> **Für:** Modder · **Du brauchst:** RUSE Studio 0.9.8.8 oder neuer und einen Mod · **Dauer:** ein paar Minuten

Die Gebäude jeder Nation, was ihre Baumenüs anbieten und in welcher Reihenfolge, und eigene Gebäude. Im Spiel gesehen.

## Die Gebäudetafel

Öffne den Reiter **Nationen**: unter jeder Nation zeigt **Gebäude und Einheiten** ihre Gebäude als Reihen, jede eine
Reihe der Einheiten, die ihr Baumenü anbietet, in der Reihenfolge des Spiels. Neben dem Namen jeder Nation stellt **Einheiten behalten** alle ihre eigenen Einheiten wieder in ihre Baumenüs, wie im Spiel, und **Leer beginnen** nimmt sie alle heraus, damit du ihre Gebäude selbst füllst. **Forschung**, über den Nationen: **Keine Forschung** macht jede Einheit jeder Nation von Anfang an baubar; **Die Forschung des Spiels behalten** gibt den Einheiten des Spiels ihre Forschung zurück. Beide fragen vorher.

- **+** fügt einem Gebäude eine Einheit hinzu: eine der eigenen der Nation, die Kopie einer Einheit einer anderen Nation
  oder eine [[Epocheneinheit|Einheiten-aus-anderen-Epochen]]. Eine Kopie kommt in deinen Mod, so benannt wie im Spiel.
- **Zieh** eine Einheit entlang ihrer Reihe, um ihren Platz im Menü zu ändern, oder auf ein anderes Gebäude, um sie dort
  bauen zu lassen.
- **×** nimmt eine Einheit aus dem Baumenü. Sie ist ausgeblendet, nicht gelöscht: die Einheit ist weiterhin in den
  Dateien des Spiels.
- **Forschung…** und dann **Hierunter setzen** an der Einheit, nach der sie kommt: sie wird aus dieser erforscht (in
  jedem der Gebäude der Nation). **Von Anfang an baubar** braucht keine Forschung. **Forschungskosten** und
  **Forschungszeit (s)** stehen daneben.

Jede Reihe sagt, wie viele Einheiten sie hat. Ein Gebäude, dem nichts zu bauen bleibt, zeigt im Spiel beim Anklicken die
Gebäudeliste des HQ. Mehr als 10 Einheiten in einem Gebäude, ein Flugzeug in einem Bodengebäude oder ein Fahrzeug am
Flugplatz: noch nicht im Spiel ausprobiert.

Die Seite einer Einheit im Reiter **Einheiten** sagt, wo sie gebaut wird („Gebaut in PANZERBASIS: Platz 2 von 6“), und
**In den Gebäuden zeigen** öffnet ihre Reihe.

## Gruppen

Im Spiel zeigt die Bauliste eines Gebäudes jede Gruppe als eine Zeile: eine Einheit und ihre Verbesserungen (der
Panzer IV und der Panther). Die Tafel zeigt die Gruppen jedes Gebäudes, jede mit ihrer Zahl (**4 von 6**), und wie viele
Gruppen das Gebäude hat (**7 von 10 Gruppen**).

- Eine neue Einheit kommt in die Gruppe ihrer Art in ihrem Gebäude, oder in eine eigene Gruppe, wenn das Gebäude keine
  dieser Art hat. **+** an einer Gruppe, oder darauf ablegen, setzt sie dorthin; **Neue Gruppe** beginnt eine.
- Eine Gruppe hat höchstens 6 (ihre Einheiten und Forschungskarten), ein Gebäude höchstens 10 Gruppen, damit seine Liste
  auf den Bildschirm passt. Eine mehr wird abgelehnt: nimm eine Einheit heraus oder setze sie in ein eigenes Gebäude
  (**Gebäude hinzufügen…**).
- Eine Einheit ohne Kartentyp im Spiel (ein Lastwagen, der V2-Werfer): wähle ihre Gruppe.

Im Spiel noch nicht ausprobiert.

## Ein Gebäude hinzufügen

**Gebäude hinzufügen…** unter der Tafel einer Nation: wähl das Gebäude des Spiels, das es kopiert (**Kopie von**), gib
ihm einen Namen (**Name**), dann entweder:

- **Baut dieselben Einheiten wie das kopierte Gebäude**, oder
- **Baut eigene Einheiten**: eine eigene Reihe und ein eigener Reiter in der Bauleiste des Spiels, mit **+** gefüllt. Bis
  zu drei pro Nation.

Das zweite und das dritte Gebäude mit eigenen Einheiten brauchen einen kleinen Spiel-Patch für mehr Gebäude. Das Studio
lädt ihn einmal herunter und spielt ihn nur in deine gemoddete Kopie des Spiels ein, nie in das Spiel in deinem
Steam-Ordner.

## Das eigene Aussehen eines Gebäudes

Auf der Seite eines neuen Gebäudes setzt **Modell importieren** ein eigenes 3D-Modell (.glb, .gltf oder .3ds) anstelle
eines Teils des kopierten Aussehens ein: das Hauptgebäude einer Fabrik oder eines HQ, oder das Teil, das du wählst. Dein
Modell bekommt die Größe dieses Teils und steht, wo es stand; der Rest des Aussehens bleibt. Die eigenen Gebäude des
Spiels bleiben, wie sie sind: mach zuerst aus einem von ihnen ein neues Gebäude.

**Wo dein Mod es aufbewahrt:** `files\buildings\<Name des Gebäudes>\`. Der Kasten zeigt den ganzen Pfad auf deinem PC (oder wo es sein wird, bevor das Modell drin ist), und **Im Ordner zeigen** öffnet diesen Ordner.

**Sein Bild im Baumenü:** dreh und zoom das Modell, bis es im gestrichelten Rahmen richtig aussieht, dann nimm diese
Ansicht. Zu Modellen allgemein siehe [[Ein Modell importieren|Ein-Modell-importieren]].

## Was im Spiel gesehen wurde

Gesehen: die Änderungen an der Tafel (Einheiten hinzugefügt, verschoben, herausgenommen, aus einer anderen erforscht),
ein kopiertes Gebäude, ein Gebäude mit eigenen Einheiten und seinem Reiter in der Bauleiste, ein zweites und ein drittes
mit dem Spiel-Patch, und das eigene Modell und Bild eines Gebäudes.

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Buildings-and-Build-Menus]]
