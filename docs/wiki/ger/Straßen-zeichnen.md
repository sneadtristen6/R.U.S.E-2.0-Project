# Straßen zeichnen

> **Für:** Modder · **Du brauchst:** RUSE Studio 0.7.4 und einen Mod · **Im Spiel bestätigt:** Versorgungsrouten folgen einer
> neuen Straße, und sie wird auf den Boden gemalt

## Die Straßen der Karte sehen

Setz oben auf der Karte ein Häkchen bei **Straßen**: die eigenen Straßen der Karte erscheinen in Gold, auf dem Boden, während du ihn formst.

## Eine neue Straße zeichnen

1. Klick in der Leiste unten auf **Straßen & Brücken** (ihr Reiter **Straßen** öffnet sich). Die Straßen der Karte erscheinen in
   Gold, deine neuen in Blau.
2. Wähl ein Werkzeug:

| Werkzeug | So geht's |
|---|---|
| **Gerade** | Klick, wo die Straße beginnt, dann, wo sie endet. |
| **Kurve** | Klick auf den Anfang, dann auf die Biegung, zu der sie gezogen wird, dann auf das Ende. |
| **Freihand** | Klick entlang des Wegs; Doppelklick, **Enter** drücken oder auf **Fertig** klicken, um sie zu beenden. |

3. Ein blaues Band folgt dem Zeiger, mit der **Länge der Straße** daneben (Freihand zeigt auch das Stück seit deinem letzten
   Klick). Ein Ende nahe einer Straße **rastet an ihr ein** (ein Ring zeigt, wo), so dass die neue Straße an sie anschließt:
   Versorgungslaster können von der einen auf die andere fahren. Die Straßen-Werkzeuge zeigen, wie viele neue Straßen die Karte
   hat, und ihre Gesamtlänge.
4. **Esc** verwirft eine Straße, die du gerade zeichnest; **Rückgängig** (oder **Ctrl+Z**) nimmt die letzte zurück,
   **Wiederholen** (oder **Ctrl+Y**) zeichnet sie erneut.

Neue Straßen werden sofort in deinem Mod gespeichert (`maps/<map>/roads.toml`).

## Was eine neue Straße im Spiel bewirkt

- **Versorgungsrouten benutzen sie** (bestätigt: die Route eines Versorgungsdepots nahm eine neue Abkürzung über offene Felder).
- **Sie wird auf den Boden gemalt**, in der eigenen Straßenfarbe der Karte, damit Spieler sie sehen (im Spiel bestätigt). Sie
  sieht aus wie die eigenen Straßen der Karte, von hoch oben und ganz unten am Boden.
- **Infanterie folgt ihr**, um schneller irgendwohin zu kommen (im Spiel bestätigt, Studio 0.8.0).
- **Über Wasser bekommt sie eine Brücke**: die eigene Art der Karte (24 der 32 Karten haben eine), ein Stück, von Ufer zu Ufer
  gestreckt, so wie die eigenen Brücken des Spiels, und Einheiten können hinüberfahren. Eine Straße über eine der eigenen Brücken
  der Karte bekommt die neue Brücke an deren Stelle. Auf einer Karte ohne Brückenart meldet der Build das, und das Wasser bleibt
  gesperrt. (Im Spiel bestätigt: Panzer, Infanterie und Versorgungslaster fahren auf der Fahrbahn hinüber.)
- Die Pflanzen und Objekte auf ihrem Weg werden entfernt; **Bäume auf neuen Straßen behalten** behält die Bäume und Büsche (eine
  Straße unter den Bäumen).

## Die eigenen Straßen und Brücken der Karte entfernen

In den Werkzeugen **Straßen**:

- **Straßen der Karte entfernen:** die eigenen Straßen der Karte verschwinden: das Netz, dem Versorgungslaster folgen
  (sie fahren stattdessen querfeldein), und die auf den Boden gemalten Straßen. Deine neuen Straßen bleiben. Im Spiel
  gesehen: die Straßen verschwinden; querfeldein fahrende Versorgungslaster sind noch nicht ausprobiert.
- **Brücken der Karte entfernen:** die eigenen Brücken der Karte verschwinden, mit den Fahrbahnen, auf denen Einheiten
  standen. Einheiten kommen dort, wo sie standen, weiterhin hinüber, auf dem Boden darunter, außer du hakst auch das
  nächste Kästchen an. Deine neuen Brücken bleiben.
- **Übergänge der alten Brücken sperren** (bei entfernten Brücken; von DomesticNukes): der Boden, wo jede alte Brücke
  über Wasser stand, wird für Einheiten gesperrt, und die Straßenverbindungen dort werden getrennt: dort kommt nichts
  mehr hinüber, Versorgungslaster eingeschlossen, und das übrige Straßennetz bleibt. Eine neue Straße von dir, die an
  derselben Stelle hinüberführt, bekommt dort ihre eigene Brücke. Würde das Sperren ein Stück Boden vom Rest
  abschneiden, sagt das Studio es vor dem Build.

Noch nicht im Spiel ausprobiert: Brücken entfernen und ihre Übergänge sperren.

## Eine eigene Brücke platzieren

Im Reiter **Brücken**: wähl eine Art, stell ihre Länge und Drehung ein, dann klick auf den Boden, wo die Mitte der Brücke
hinkommt. Beide Enden sollten auf trockenem Ufer liegen. **Rückgängig** und **Wiederholen** funktionieren auch hier.

**So siehst du es:** **Im Spiel testen**, dann im Hauptmenü des Spiels **KÄMPFE** und die Karte. Platzier ein Versorgungsdepot
nahe deiner Straße und beobachte seine Route.

**Weiter:** [[Gebäude und Bäume platzieren|Gebäude-und-Bäume-platzieren]]

---

[[Feldhandbuch|Feldhandbuch]] · [[English|Draw-Roads]]
