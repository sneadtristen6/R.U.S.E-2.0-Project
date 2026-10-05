**RUSE Studio, un'anteprima per i modder.** Sfoglia le unità del gioco in una qualsiasi delle sue dieci lingue,
modificale in un mod tuo e provalo in gioco. La tua installazione di Steam non viene mai modificata.

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
