**RUSE Studio, un'anteprima per i modder.** Sfoglia le unità del gioco in una qualsiasi delle sue dieci lingue,
modificale in un mod tuo e provalo in gioco. La tua installazione di Steam non viene mai modificata.

**0.9.8.2:** arrivano le unità di altre epoche: i loro modelli, a grandezza reale, dietro una ricerca.

- **Unità di altre epoche:** le epoche WWI, WWII+, Guerra fredda e Moderno della scheda Unità ora hanno le loro
  unità: 366, ognuna il modello gratuito di un altro autore (CC0 o CC BY), citato. Ogni epoca si scarica nello Studio
  quando la scegli, dal nostro GitHub (ogni file controllato: WWI 232 MB, WWII+ 198 MB, Guerra fredda 996 MB, Moderno
  709 MB), e si aggiorna da sola man mano che altre sono pronte.
  - **A grandezza reale:** la larghezza reale di ogni unità (per un aereo, l'apertura alare) alla scala del gioco;
    modificabile da 0,2 a 5 volte.
  - **Ricercate come le unità del gioco:** da qualsiasi unità dell'edificio della sua nazione, anche dalle unità
    d'epoca della mod, così funziona una catena (un T-80, poi un T-90M), con prezzo e tempo di ricerca. Le unità WWI
    e WWII+ si comprano subito; quelle della Guerra fredda e Moderne partono ricercate da un'unità adatta.
  - **Le loro carte** nel menu di costruzione e alla selezione.
  - Visto in gioco: si caricano subito, le schede di ricerca e una catena, un Land Rover con il suo modello, le
    dimensioni. Non ancora provato: i cannoni trainati (nessun cannone del gioco a cui adattarli, per ora).
- **Importa modello…:** un modello che comincia con una figura dell'equipaggio ha ora il suo modello (le jeep copiate
  dal Kübelwagen mostravano quello del Kübelwagen); i modelli dipinti in specular-glossiness tengono la loro pittura;
  i colori dati come numeri non sono più neri; i modelli grandi si importano più in fretta.
- **Un'unità ricercata da un'unità di un altro esercito** lasciava il gioco in una schermata di caricamento infinita:
  **Nuova unità…** ora toglie quel collegamento, e la costruzione rifiuta un'unità ricercata da un'unità mancante o
  di un'altra nazione, dicendo perché e come correggere.
- **Linux e Steam Deck (con Proton):** lo Studio si apre nel tuo browser web quando la sua finestra non ci riesce.
  Non ancora provato su Linux: facci sapere com'è andata.

**0.9.8.1:** Gli strumenti di LittleGroove arrivano nello Studio, con musica e suoni e una nazione trasformata in un'altra.

- **Gli strumenti di LittleGroove, ripresi** dal suo RUSE-Mod-Manager:
  - **Scheda Economia:** denaro iniziale e rendita, depositi di rifornimento e le carte dell'inganno con cui parte ogni
    schieramento. Visto in gioco: il denaro iniziale e le carte iniziali.
  - **Scheda IA:** come giocano i giocatori controllati dal computer, le unità che preferiscono e le carte
    dell'inganno; e gli script delle mappe e delle missioni del gioco, mostrati in Python, in sola lettura. Visto in
    gioco.
  - **Riquadro Potenziamento** nella pagina di un'unità: l'unità di cui è un potenziamento, i suoi potenziamenti, il
    prezzo e il tempo della ricerca.
  - **Scheda Tutti i valori:** qualsiasi oggetto o valore del gioco, cambiato in una mod: aggiungere o togliere un
    valore, creare o eliminare un oggetto, dare a un valore di testo parole proprie.
  - **Scheda File:** qualsiasi file dei pacchetti del gioco, visibile e salvabile. Sostituiscine uno con un tuo file o
    aggiungine uno: la tua mod conserva solo le modifiche, ognuna controllata secondo il suo tipo.
  - **Missioni:** cambiare gli script di una missione; vedere se è nei menu, se ogni file che le serve si carica, e i
    suoi testi; spostarla su o giù nel suo menu.
  - **Mappe:** nomi di città e colline, punti e zone con nome, nome e orientamento di un oggetto della mappa. **Note**
    su un'unità, un valore o un giocatore del computer.
- **Scheda Musica:** ogni brano secondo dove suona, ognuno sostituito in un piccolo editor nello Studio (taglio,
  dissolvenza, volume); nuovi brani aggiunti alle liste di battaglia; le battute di un'unità nella sua pagina; il suono
  di sottofondo di una mappa. Visto in gioco: i brani, i nuovi brani e le battute.
- **Fare di una nazione un'altra.** La nuova scheda **Nazioni** dà a una delle sette nazioni del gioco un nuovo nome
  (nella lobby e per il suo esercito) e una nuova bandiera da qualsiasi immagine: per esempio la Cina al posto
  dell'Italia. Le sue unità e ciò che dicono si cambiano come prima, nella scheda Unità e nella pagina di ogni
  unità. Visto in gioco: il nuovo nome nella lobby, la nuova bandiera in partita.
- **Unità di altre epoche:** la scheda Unità offre le epoche WWI, WWII+, Guerra fredda e Moderno accanto alle unità
  del gioco. Non hanno ancora unità: arriveranno con un prossimo aggiornamento.
- **Nuova mappa: partire da zero…** è nella scheda Mappe prima che una mappa sia aperta.
- **Il terreno di Terreno vuoto è disegnato apposta.** Una nuova mappa partita da zero ha il terreno fatto dai tuoi
  tratti, non più il terreno della mappa del gioco spostato: coste rotonde da vicino e dall'alto, niente più
  ammaccature in cima alle colline, ed edifici e carri poggiano esattamente sopra. Visto in gioco su mappe di prova.
- **Oceano vuoto resta, con un avviso** sul suo pulsante: isole separate non sono pronte per vere battaglie
  (sotto).

Non ancora provato in gioco: il riquadro Potenziamento, Tutti i valori, File, gli strumenti delle missioni, le
aggiunte alle mappe e i suoni di sottofondo.

**Perché non ci sono ancora mappe navali.** Abbiamo provato mappe di isole per vere battaglie con le navi, ed è il
gioco stesso a impedirlo:

- Un'unità di terra mandata su un'isola che non può raggiungere fa andare in crash il gioco.
- Collegare le isole con una striscia di terra evita il crash, ma allora il computer ci manda semplicemente la sua
  fanteria.
- Senza una strada tra le isole, non si può piazzare nessun edificio.
- Con le armi del gioco, navi e unità di terra si fanno a malapena danno.

I soli dati della mappa non possono correggere il crash, quindi le mappe navali aspettano.

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
