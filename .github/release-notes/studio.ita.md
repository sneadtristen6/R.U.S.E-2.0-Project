**RUSE Studio, un'anteprima per i modder.** Sfoglia le unità del gioco in una qualsiasi delle sue dieci lingue,
modificale in un mod tuo e provalo in gioco. La tua installazione di Steam non viene mai modificata.

**0.9.8:** una nuova mappa può partire vuota, come terra piatta o mare aperto, e ogni mappa può avere le sue immagini
nei menu del gioco.

- **Partire da una mappa vuota.** **Duplica mappa** ha una nuova scelta, **Partire da**: **Terreno vuoto** (terra
  piatta senza niente sopra tranne i punti di partenza) o **Oceano vuoto** (il mare su tutta la mappa). Visto in gioco.
- **Immagini del menu per ogni mappa.** Scegli un PNG per l'immagine della mappa e la sua mappa 3D nei menu, o torna a
  quelle del gioco; i punti di partenza bianchi sono disegnati dove partono i giocatori della mappa. **Crea in
  Blender…** apre il modello 3D della mappa stessa per farle, e **Riporta** le mette nella tua mod. Visto in gioco.

| Prima | Ora |
|---|---|
| Una nuova mappa partiva come copia completa di una mappa del gioco. | **Duplica mappa** può farla partire vuota: Terreno vuoto o Oceano vuoto. |
| Una nuova mappa mostrava le immagini del menu della mappa copiata. | **Immagini del menu…** le dà le sue: un tuo PNG o un'immagine fatta in Blender, con i punti di partenza dove partono i suoi giocatori. |
| I depositi, le unità, gli edifici e i nomi della mappa restavano. | **Togli** ne toglie uno, o tutti i depositi o tutti i nomi in una volta (visto in gioco). |
| Le strade e i ponti della mappa restavano. | Il pannello Strade li toglie (le linee delle strade sparite: visto in gioco). |
| I settori lasciavano fuori il mare e i bordi della mappa. | **Settori su tutta la mappa**: si può prendere tutta la mappa (visto in gioco). |
| L'acqua di una mappa veniva solo dai suoi fiumi e dal suo mare. | **Acqua su tutta la mappa**: uno strato sottile, come il mare dipinto di una mappa navale (visto in gioco; le unità sotto non ancora provate). |
| L'editor di mappa sceglieva i rinforzi uno alla volta, con nomi in codice. | Trascina un riquadro per selezionarli come nel gioco; le icone della mappa mostrano cosa è selezionato e quanti. |
| I pannelli dell'editor di mappa avevano una sola dimensione. | Ogni pannello mobile si ridimensiona, dal 40% al 125%. |
| Le novità erano solo in inglese. | Sono nella lingua dello Studio. |
| Mandare una mod all'elenco delle mod voleva dire scrivere la sua voce a mano. | **Pubblica nell'elenco delle mod** apre il modulo dell'elenco, già compilato, con una copia .zip pronta da trascinare; ogni esportazione dice che è stata fatta con RUSE Studio. |
| Importa modello perdeva l'ombreggiatura e le parti trasparenti di un modello. | Le tiene, e dice cosa ha tenuto (non ancora visto in gioco). |
| Un'unità costruita su un mare prosciugato poteva mandare in crash il gioco; la vecchia acqua dei fiumi stava come muri lungo il bordo di una mappa; i fari cancellati brillavano ancora sul mare. | Corretto, ognuno visto in gioco. |

Noto: **le mappe navali non sono finite.** Oceano vuoto si costruisce e si gioca, ma le unità sotto la sua acqua non
sono ancora state provate.

**0.9.7:** i mod di mappa molto grandi ora si costruiscono in pochi minuti. Prima la loro costruzione richiedeva
moltissimo tempo, ed è per questo che serviva questo aggiornamento. E **Esporta mod…** porta con sé ciò che la
costruzione ha calcolato, così la prima costruzione di un mod simile da parte di un giocatore è più breve.

- **Il mod di mappa più estremo che abbiamo** (la mappa "D-Day" con il mare prosciugato: 154 tratti di livellamento,
  135 tratti di pittura, 33.385 edifici cancellati) richiedeva circa quattro ore di costruzione. Ora si costruisce in
  **meno di 10 minuti**, senza tenere nulla da una costruzione precedente, e i file del gioco escono uguali. Ci sono
  volute circa 15 ore; dove si bloccava e perché: [Come ci siamo arrivati](https://github.com/sneadtristen6/R.U.S.E-2.0-Project#how-we-got-here)
  (in inglese). Continuiamo a lavorare per renderlo più veloce.

| Prima | Ora |
|---|---|
| Una mappa rimodellata per chilometri poteva richiedere ore di costruzione, esaurire la memoria del PC o essere rifiutata come troppo grande per il movimento della mappa. | Il suo terreno viene rimodellato in pochi secondi, i letti dei fiumi riparati e il terreno dipinto su tutti i core del PC, e il movimento calcolato su altri due mentre il terreno viene dipinto. Ogni passaggio dà gli stessi file di prima. |
| Un mare prosciugato restava chiuso alle unità. | Un ampio letto asciutto riceve zone di movimento grandi quanto lo spazio permette. **Non ancora provato in gioco:** unità sul mare aperto. |
| Una ricostruzione dopo una piccola modifica ricalcolava da capo una grande mappa. | Ciò che è stato fatto viene tenuto: la pittura invariata richiede mezzo secondo, il movimento invariato arriva dalla cache di costruzione, e un nuovo tratto ridipinge solo le tessere che raggiunge. |
| La prima costruzione di un grande mod di mappa da parte di un giocatore ricalcolava tutto. | **Esporta mod…** mette nel mod ciò che la costruzione ha calcolato per il movimento della mappa (`maps/<map>/solved.bin`). È legato al file del gioco per quella mappa e non contiene file del gioco. La costruzione del giocatore lo usa, controlla ogni risposta e dà gli stessi file. La pittura del terreno e i letti dei fiumi vengono comunque fatti su ogni PC. |
| Importa modello compariva solo nella pagina di una nuova unità: difficile da trovare. | La scheda Unità inizia con due pulsanti: **Modifica un'unità** e **Nuova unità (importa un modello)**. Scegli l'unità di partenza, dalle un nome, Crea: la sua pagina si apre su Importa modello. La pagina di un'unità del gioco ha **Nuova unità da questa…**. |
| La bandiera nave (76) diceva che un'unità che la possiede si muove sull'acqua. | Dice che l'unità non si muove affatto, come un edificio (non ancora provato in gioco). |

Noto: **le mappe navali non sono ancora pronte.** Un mare prosciugato o dipinto si costruisce e si carica, ma l'acqua
si vede ancora.
