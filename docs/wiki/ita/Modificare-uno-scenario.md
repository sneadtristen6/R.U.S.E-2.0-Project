# Modificare uno scenario

> **Per:** modder · **Ti serve:** RUSE Studio 0.9.8.4 e una mod · **Tempo:** qualche minuto

Uno **scenario** è ciò con cui parte una mappa: zone di cattura, il punto di partenza di ogni schieramento, e unità ed
edifici già sul campo. Una mappa ne ha diversi: uno per ogni modo in cui il gioco la fa giocare.

## I tre modi in cui il gioco fa giocare una mappa

Sono i pulsanti del menu principale di R.U.S.E.:

| Pulsante | Cos'è |
|---|---|
| **BATTAGLIE** | Una partita libera contro il computer su una mappa, con i giocatori che scegli (altri giochi la chiamano schermaglia). |
| **OPERAZIONE** | Una missione breve con obiettivi stabiliti, su una situazione già pronta. |
| **CAMPAGNA** | La storia, capitolo per capitolo. |

Lo Studio chiama ogni scenario come il pulsante che lo fa giocare, e una riga dorata sotto il menu degli scenari dice
esattamente dove: per esempio **Nel gioco: Battaglie › D-Day (6 giocatori)**.

## Scegli lo scenario

All'inizio della barra della schermata della mappa, scegli **Scenario** (accanto a **Mappa**). Le cose della mappa stessa
(terreno, edifici, alberi, strade) appaiono sbiadite e non si possono afferrare per errore; torna su **Mappa** per cambiarle.
Poi scegli lo scenario dal menu in alto. I punti di partenza appaiono come pilastri del colore di ogni schieramento, gli
spawn come rombi bianchi, le zone come aree ombreggiate.

## Sposta un punto di partenza o uno spawn

1. Sul lato **Scenario**, clicca su **Sposta**.
2. Clicca sul pilastro o sul rombo, poi clicca dove deve andare.
3. Per rimetterlo dove lo aveva il gioco, cliccalo di nuovo e scegli **Rimetti**.

## Aggiungi unità: una o un'intera formazione

1. Sul lato **Scenario**, clicca su **Aggiungi unità**.
2. Scegli il genere (Edifici, Terra, Fanteria, Aria), poi il tipo, poi l'unità nell'elenco (raggruppate per nazione).
3. Scegli **A chi va?** Per un'Operazione o un capitolo della campagna l'elenco sono i campi di quello scenario, presi dalla
   sua missione: **Giocatore** (tu: campo 0 nella campagna) e i campi del **Computer**, ognuno con il suo paese, più
   **Neutrale**. Il numero tra parentesi è ciò che viene salvato. Una mappa di **BATTAGLIE** accetta solo unità neutrali (il
   gioco la avvia senza elenco delle squadre, quindi le unità di un giocatore lì non apparirebbero mai).
4. **Quanti:** 1, 2, 4, 6, 8 o 10.
5. Per più di una, scegli una **formazione**: linea, colonna, cuneo, quadrato o cerchio. È rivolta verso l'alto dello
   schermo: ruota la vista per orientarla. **Spaziatura** imposta i metri tra le unità.
6. Degli anelli sulla mappa mostrano dove starà ogni unità. Clicca per piazzarle.

Un'unità che hai aggiunto si può spostare come qualsiasi spawn, o togliere con **Rimuovi**.

## Più giocatori su una mappa (fino a 8)

Ogni giocatore parte da un **punto di partenza** della sua squadra, uno per giocatore: in un 3 contro 3, le squadre 1 e 2
hanno ciascuna i posti da 1 a 3. Un 4 contro 4 richiede il posto 4 in entrambe.

1. Scegli lo scenario che il gioco fa giocare online (la sua riga dorata dice **Battaglie**), poi nella barra clicca su
   **Scenario**.
2. **Giocatori** (a destra) mostra il numero della mappa, quello del gioco segnato *(gioco)*. Scegli il nuovo numero, al
   massimo 8. La riga sotto nomina ogni punto di partenza che manca ancora, per esempio *squadra 1, posto 4*.
3. Clicca su **Aggiungi partenza del quartier generale**, scegli la **squadra**, poi clicca su un terreno aperto dove parte
   quel giocatore, lontano dagli altri. Prende il posto successivo della squadra, e la telecamera e l'introduzione da un
   compagno di squadra.
4. Quando la riga dice **Ogni giocatore ha un punto di partenza**, usa **Prova in gioco** e apri **BATTAGLIE**: la mappa è
   elencata con il suo nuovo numero, per esempio *(8) Cotentin (4v4)*.

Un punto di partenza che hai aggiunto si sposta con **Sposta**, o se ne va con **Rimuovi**. Più di 8: no, la lobby del gioco
ha 8 posti (provato il 2026-10-02).

> [!NOTE]
> Nuovo, non ancora verificato in gioco: raccontaci nelle [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions)
> come va una partita a 8 giocatori.

## Una mappa vuota: piazza il QG di ogni giocatore

Una mappa iniziata come **Terreno vuoto** o **Oceano vuoto** (**Duplica mappa** della scheda Mappe) non ha niente della
mappa copiata, nemmeno i suoi QG. **Il QG di ogni giocatore** (sul lato Scenario) elenca ogni QG di cui la mappa ha bisogno:
clicca su **Posiziona**, poi sul terreno dove va. **Prova in gioco** aspetta finché ogni giocatore non ha un QG.

**Dimensioni mappa** (Studio 0.9.8.7) rende una nuova mappa vuota più grande o più piccola, una striscia alla volta: premi
**+** su un lato per aggiungere una striscia di terreno lungo di esso, o **−** per toglierne una, poi **Applica queste
dimensioni**. Non ancora provato in gioco.

> [!WARNING]
> Entrambe le mappe vuote hanno ancora dei bug: usale a tua discrezione, e raccontaci cosa trovi.

## Settori

**Settori** (sul lato Scenario) cambia i settori dello scenario, le zone su cui si giocano le carte d'inganno. Una mappa
vuota parte senza: li crei tu.
- **Forme:** trascina un punto d'angolo per spostare un confine (i settori che lo condividono si spostano insieme). Fai
  doppio clic su un confine per aggiungere un punto; clic destro su un punto per toglierlo. **Nuovo settore:** trascina un
  riquadro sul terreno. **Nessun settore:** trascina un riquadro dove non deve esserci nessun settore. **Elimina settore**
  dà tutto il suo terreno ai settori intorno.
- **Dipingi:** scegli un settore, poi trascina sul terreno per dipingerlo; «Nessun settore» toglie il terreno da ogni
  settore.
- **Parti senza settori** o **Parti dai settori della mappa**; **Annulla** ritira l'ultima modifica.
- **Crea i settori** taglia l'intera mappa in settori larghi più o meno quanto dice **Settori di circa** (le mappe del gioco
  stesso hanno settori larghi da 1 a 3 km), con confini irregolari; **Altra disposizione** li taglia in un altro modo. Poi
  trascina gli angoli o dipingi per ridisegnarli.

Visto in gioco: settori dipinti su una mappa vuota, un nuovo settore disegnato su D-Day e illuminato da solo da una carta
d'inganno, terreno senza settore (un vuoto sul tavolo della mappa che nessuna carta d'inganno illumina). Le linee sottili
che lo Studio taglia perché un settore resti un pezzo unico non sono ancora state provate in gioco.

## Depositi di rifornimento su questa mappa

Scegli un deposito di rifornimento per dargli più camion (più camion, più denaro dentro), oppure usa **Tutti i depositi
qui**: moltiplica i camion di ogni deposito (**volte i loro camion**) o dai a tutti lo stesso numero (**camion ciascuno**),
poi **Applica**. **Torna a quelli del gioco** lo annulla. Per cambiare tutte le mappe in una volta, usa **Depositi sulle
mappe** in **Impostazioni IA e giocatori** ([[Economia, IA e altro|Economia-IA-e-altro]]). I depositi con più di 1.000
camion richiedono il Launcher 0.4.8.4 o più recente.

## Una missione tutta sua

Una nuova Operazione o un nuovo capitolo della campagna può giocare una missione tutta sua, con obiettivi, eventi e
movimenti di camera: [[Creare una missione|Creare-una-missione]].

## Vedi le tue unità in gioco

1. Clicca su **Prova in gioco** (in cima allo Studio). Lo Studio costruisce la tua mod nella copia moddata del gioco
   (`RUSE-Instances\Modded game` sull'unità del tuo gioco, o la cartella che hai scelto nelle Impostazioni: una per tutto il PC, anche quella del Launcher) e avvia R.U.S.E. da lì. Il messaggio in basso
   dice cosa aprire, per esempio **BATTAGLIE > D-Day**.
2. Nel menu principale del gioco, clicca su quel pulsante (**BATTAGLIE** per una battaglia), poi scegli la mappa (**D-Day**).
3. Prepara la partita come al solito e avviala. Le tue unità appaiono dove le hai piazzate.

> [!NOTE]
> Avviare R.U.S.E. da Steam avvia il gioco senza la tua mod. Usa **Prova in gioco** (o **Gioca** nel launcher).

> [!NOTE]
> Quale punto di partenza va a ciascun giocatore della lobby in una battaglia è ancora in prova. Raccontaci cosa trovi
> nelle [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

**Avanti:** [[Esportare e condividere|Esportare-e-condividere]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Edit-a-Scenario]]
