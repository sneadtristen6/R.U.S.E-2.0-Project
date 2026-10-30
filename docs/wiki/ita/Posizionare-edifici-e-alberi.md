# Posizionare edifici e alberi

> **Per:** modder · **Ti serve:** RUSE Studio 0.7.2 e una mod (Griglia, Riquadro, Percorso, Seleziona e Ripeti: 0.9.8.7;
> modelli tuoi: 0.9.8.8) · **Provato in gioco:** gli edifici piazzati si vedono a ogni zoom, fino a 8× la loro dimensione,
> e le unità ci girano intorno. Non ancora provato in gioco: ciò che si piazza con Griglia, Riquadro e Percorso, e gli
> oggetti spostati

## Piazzare

1. Nella barra, clicca **Edifici**, oppure **Oggetti e alberi** e poi la sua scheda **Oggetti** o **Alberi**.
2. Scegli un tipo dalle immagini (scrivi nella casella di ricerca per restringerle). Ogni immagine è disegnata dal
   modello del gioco stesso, e il numero nel suo angolo dice quanti ne ha già la mappa. L'elenco contiene i tipi propri di
   questa mappa: il gioco accetta solo un tipo che una mappa usa già.
3. Scegli cosa piazza un clic:
   - **Uno**: un oggetto dove clicchi;
   - **Area**: trascina per spargere oggetti in un cerchio (**Spaziatura** li tiene distanti, **Area** imposta il
     cerchio);
   - **Linea**: clicca l'inizio, poi la fine, per una fila (una siepe, una strada, un filare di alberi), girati lungo di
     essa;
   - **Griglia**: file di oggetti: clicca dove inizia la prima fila e dove finisce, poi allontanati per aggiungere le file e
     clicca (**Tra le file** imposta lo spazio);
   - **Riquadro**: trascina un riquadro sul terreno e lascia andare: si riempie a file dell'oggetto scelto;
   - **Percorso**: clicca lungo il tragitto, poi fai doppio clic, premi **Enter** o **Fine**: gli oggetti seguono una curva
     morbida attraverso i tuoi clic (una siepe, un filare di alberi); con una larghezza, una fascia di oggetti. **Esc**
     scarta una griglia, una linea o un percorso a metà.
4. **Rivolti alle strade:** vicino a una strada, un oggetto va accanto a essa e si gira verso di essa, e una fila la
   segue; una griglia o un riquadro lasciano libere le strade. Il cursore della rotazione lo gira comunque (prova 180° se
   una casa mostra il retro).
5. **Rotazione** e **Dimensione** (fino a 10×) sono i cursori a destra. Gli alberi variano un po' di dimensione e di
   rotazione da soli, così un bosco non sembra fatto con lo stampino.

Prima che tu clicchi, il tipo compare trasparente sotto il puntatore, ruotato e dimensionato come starà. Gli oggetti
piazzati si vedono con i loro modelli, ognuno con un piccolo punto d'oro ai suoi piedi che lo segnala da lontano.

## Selezionare, spostare, ruotare, eliminare

**Seleziona** (nei pannelli **Edifici** e **Oggetti e alberi**) sceglie ciò che sta sulla mappa, ciò che ha piazzato la
tua mod o ciò che è della mappa stessa: clicca su uno, **Shift+clic** per aggiungerne, o trascina un riquadro attorno a
più oggetti. Poi trascina uno di quelli scelti per spostarli, usa **Rotazione** e **Dimensione**, o **Elimina**.
**Rimetti come nella mappa** annulla le tue modifiche a ciò che è della mappa stessa; **Esc** non sceglie niente.

## Modelli tuoi

**Importa modello…** (in **Oggetti e alberi**) fa di un modello 3D (.glb, .gltf o .3ds) una delle rocce, degli oggetti,
dei cespugli o degli alberi propri della tua mod di mappe. Si piazza come quelli del gioco, su ogni mappa della mod, con
versioni più piccole create apposta per le distanze medie e lontane. Dagli una **Dimensione** e una **Provenienza**: un
modello fatto da qualcun altro può entrare in una mod solo con licenza CC0 o CC-BY, con il suo autore. Spuntato,
**Solido: le unità lo aggirano**; senza spunta, le unità ci passano attraverso e lo abbattono, come i piccoli oggetti del
gioco. **Il tuo modello…** lo cambia più tardi. Visto in gioco.

## Edifici solidi

**Solido** (attivo di base) fa girare le unità intorno a un edificio piazzato invece di attraversarlo. Disattivalo per un
edificio che deve solo essere guardato.

## Nascondersi dentro

Gli edifici piazzati non nascondono le unità da soli: apri **Copertura**, scegli **Città** e clicca la città che hai creato.

## Annullare e ripetere

**Annulla** (o **Ctrl+Z**) toglie l'ultimo oggetto, o l'intera area, linea, griglia, riquadro o percorso, e l'ultimo
spostamento, rotazione, cambio di dimensione o eliminazione. **Ripeti** (o **Ctrl+Y**, **Ctrl+Shift+Z**) lo rimette.
Ogni strumento della mappa li ha entrambi.

## Cancellare gli alberi e gli oggetti della mappa

1. Nella barra, clicca **Rimuovi** (Studio 0.8.1).
2. Scegli cosa toglie: **alberi**, **oggetti**, **edifici** (in qualsiasi combinazione). Ogni cerchio tiene ciò che era
   scelto quando lo hai dipinto.
3. Trascina sulla mappa: i cerchi rossi segnano cosa se ne va, e ciò che coprono è tinto di rosso. **Dimensione** imposta
   i cerchi; il riquadro conta cosa toglieranno quando la mod viene costruita.

Dove spariscono gli alberi, il terreno si apre a ogni unità e perde la sua copertura di bosco (provato in gioco: i carri
armati entrano in un bosco ripulito, la fanteria lì non è nascosta). Anche gli edifici cancellati aprono il loro terreno
alle unità. **Annulla** (**Ctrl+Z**) toglie l'ultimo trascinamento, **Ricomincia** toglie ogni cerchio sulla mappa.

**Avanti:** [[Modificare uno scenario|Modificare-uno-scenario]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Place-Buildings-and-Trees]]
