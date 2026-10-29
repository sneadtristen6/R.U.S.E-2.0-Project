**RUSE Launcher 0.4, per i giocatori.** Trova R.U.S.E. tramite Steam, e **Gioca** costruisce una copia del gioco con i
tuoi mod e la avvia. La tua installazione di Steam non viene mai modificata.

**0.4.8.9:** le mod si installano su più PC, e una lettura delle immagini più sicura.

- **Corretto, segnalato da un giocatore:** su alcuni PC nessuna mod si installava: «questo PC non si fida del certificato di sicurezza del sito (unable to get issuer certificate)». Windows su quei PC non ha il certificato con cui vengono controllati i download di GitHub e non riesce a recuperarlo. Il Launcher ora prova anche con l'elenco di certificati di Firefox, che porta con sé. Fino ad allora, una mod scaricata nel browser dall'elenco delle mod si installa con **Aggiungi un file di mod…**.
- **Immagini più sicure:** la libreria con cui il Launcher legge le immagini (Pillow) passa alla versione 13.0.0, con le sue correzioni contro file d'immagine fatti apposta che potevano far chiudere l'app, esaurirne la memoria o peggio.

**0.4.8.8:** avvia le mod fatte con Studio 0.9.8.8, e il tuo gioco moddato dice R.U.S.E. 2.0 in oro.

- **Le mod fatte con Studio 0.9.8.8 si giocano:** edifici propri (il secondo e il terzo di una nazione richiedono una piccola patch del gioco, scaricata una volta e applicata solo alla tua copia moddata, mai al gioco nella tua cartella di Steam), l'aspetto proprio dei nuovi edifici e gli oggetti, suoni e animazioni cambiati con RUSE Decoy, i valori dei giocatori del computer e le regole del gioco, e i passaggi dei vecchi ponti chiusi.
- **R.U.S.E. 2.0 in oro:** il tuo gioco moddato si apre su una scena di battaglia con un motore che si avvia, e il suo menu principale, il piccolo titolo di ogni menu, i contorni dei menu e le schermate di caricamento dicono R.U.S.E. 2.0 in oro. È fatto sul tuo PC dai file del tuo gioco la prima volta (qualche minuto una volta, poi tenuto). Impostazioni ha una casella per tenere il titolo del gioco.
- **Corretto: macchie scure e chiare sulle mappe fatte con lo Studio** (mappe vuote, ingrandite, a rilievo e a settori): una mappa così è illuminata bene una volta costruita con questa versione (il suo terreno viene rifatto la prima volta).
- **Corretto, segnalato da un giocatore:** nella pagina Mod supportate, «Nuovo set di mod…» non faceva niente. Ora apre il nuovo set. Non ancora provato nell'app vera e propria.
- **Le lettere del gioco:** il Launcher è scritto con il font dei menu del gioco, preso dal tuo gioco a ogni avvio.
- **Ancora con bug, giocale a tua discrezione:** le mappe fatte con le texture di Map Paint e le mappe vuote (Terreno vuoto, Oceano vuoto).

**0.4.8.7:** avvia le mod fatte con Studio 0.9.8.7.

- **Le mod fatte con Studio 0.9.8.7 si giocano:** oggetti spostati o piazzati a griglia, a riquadro e lungo percorsi, mappe vuote più grandi con i loro settori, e modifiche all'economia solo della Nucleare.
- **Le righe della build nella tua lingua**, in tutte e dieci.
- **I risultati di build tenuti restano validi dopo un aggiornamento.**
- **Ancora con bug, giocale a tua discrezione:** le mappe fatte con le texture di Map Paint e le mappe vuote (Terreno vuoto, Oceano vuoto).

**0.4.8.6:** avvia le mod fatte con Studio 0.9.8.6.

- **Le mod fatte con Studio 0.9.8.6 si giocano:** mappe vuote con ombre sul terreno piatto, ciò che è piazzato dove la mappa copiata aveva il mare disegnato, e il pavimento della telecamera sul nuovo terreno.
- **Un crash noto rifiutato:** una mod in cui un aereo armato ha il flag da ricognizione senza quello da caccia faceva crashare il gioco quando l'aereo veniva mandato ad attaccare; ora il Launcher si rifiuta di costruirla e dice perché.
- **Ancora con bug, giocale a tua discrezione:** le mappe fatte con le texture di Map Paint e le mappe vuote (Terreno vuoto, Oceano vuoto).

**0.4.8.5:** avvia le mod fatte con Studio 0.9.8.5.

- **Le mod fatte con Studio 0.9.8.5 funzionano:** aerei in un nuovo ruolo (un bombardiere con la sua stiva, un ricognitore che tiene le sue armi), veicoli da ricognizione, armi che colpiscono gli aerei e terreno dipinto dalla libreria del pennello Texture con il dettaglio del gioco sopra. Un Launcher più vecchio non riesce a costruirne alcune.
- **Più veloce:** una mappa ridipinta allo stesso modo riprende il terreno dipinto dalla build precedente in pochi secondi.
- **Ancora con bug, giocale a tua discrezione:** le mappe fatte con le texture di Map Paint e le mappe vuote (Terreno vuoto, Oceano vuoto).

**0.4.8.4:** le mod si scaricano su ogni PC, e avvia le mod fatte con Studio 0.9.8.4.

- **Le mod si scaricano su ogni PC:** su alcuni PC nessuna mod si scaricava ("certificate verify failed: unable to get local issuer certificate"). Ora il Launcher chiede il certificato a Windows, come fa un browser, e riprova; anche per i suoi aggiornamenti. Non ancora provato su un PC che aveva il problema.
- **Le mod fatte con Studio 0.9.8.4 funzionano:** missioni proprie, mappe vuote con i loro QG e settori, depositi con più camion (un Launcher più vecchio rifiuta i depositi oltre i 1.000 camion), unità con il loro aspetto e le loro uniformi, modifiche delle mod di altri con un nome proprio.
- **Ancora con bug, giocale a tua discrezione:** le mappe fatte con le texture di Map Paint e le mappe vuote (Terreno vuoto, Oceano vuoto).

**0.4.8.3:** le copie con le mod vanno dove dici tu.

- **Dove vanno le copie con le mod**, nelle Impostazioni: scegli la cartella in cui viene costruita la copia del gioco
  con le mod, o torna al posto consigliato, `RUSE-Instances` sull'unità del gioco (lì la copia condivide i file del
  gioco ed è pronta in pochi secondi; su un'altra unità è una copia completa del gioco, più lenta e più grande). Il
  backup pulito del gioco va accanto. Il prossimo Gioca costruisce nel nuovo posto; la vecchia cartella si può
  eliminare a mano. Lo Studio usa la stessa cartella.

**0.4.8.2:** si apre nel tuo browser web dove la sua finestra non ci riesce, e avvia le mod fatte con lo Studio
0.9.8.2.

- **Linux e Steam Deck (con Proton):** il Launcher si apre nel tuo browser web quando la sua finestra non ci riesce.
  Non ancora provato su Linux: facci sapere com'è andata.
- Le mod fatte con lo Studio 0.9.8.2 funzionano: unità di altre epoche con i loro modelli, dimensioni, ricerche e
  carte.

**0.4.8.1:** converte le vecchie mod e avvia le mod fatte con lo Studio 0.9.8.1.

- **Converti una vecchia mod…**, il Convert di LittleGroove ripreso: una mod più vecchia che arriva come pacchetti del
  gioco, da copiare nella cartella del gioco, diventa una mod che la tua libreria avvia insieme alle altre. Non ancora
  provato con una vera vecchia mod.
- **Due mod che cambiano lo stesso file del gioco:** il Launcher lo dice prima di Gioca, e **Usa quella di…** sceglie
  quale.
- Le mod fatte con lo Studio 0.9.8.1 funzionano: brani e voci, una nazione trasformata in un'altra.

**0.4.8:** gioca le mod fatte con Studio 0.9.8, tra cui le nuove mappe che partono vuote, e mostra le novità nella tua
lingua.

| Prima | Ora |
|---|---|
| Una nuova mappa mostrava le immagini del menu della mappa copiata. | Le sue immagini, come le ha fatte chi l'ha creata, con i punti di partenza dove partono i suoi giocatori. |
| Un'unità costruita su un mare prosciugato poteva mandare in crash il gioco. | Corretto (visto in gioco). |
| La vecchia acqua dei fiumi stava come muri lungo il bordo di una mappa, e i fari cancellati brillavano ancora sul mare. | Corretto (visto in gioco). |
| Una mod che cancella un'intera mappa poteva esaurire la memoria del PC durante la costruzione. | Si costruisce. |
| Le novità erano solo in inglese. | Sono nella lingua del Launcher. |

Noto: **le mappe navali non sono finite.** Oceano vuoto si costruisce e si gioca, ma le unità sotto la sua acqua non
sono ancora state provate.

**0.4.7:** i mod di mappa molto grandi ora si costruiscono in pochi minuti (prima ci voleva moltissimo), e avvia i mod
fatti con Studio 0.9.7.

| Prima | Ora |
|---|---|
| **Gioca** poteva richiedere ore per costruire un grande mod di mappa. | Il più estremo che abbiamo (la mappa "D-Day" con il mare prosciugato) richiedeva circa quattro ore; ora meno di 10 minuti, con lo stesso risultato. |
| La prima costruzione di un grande mod di mappa calcolava tutto sul tuo PC. | Un mod esportato con Studio 0.9.7 porta con sé ciò che la sua costruzione ha calcolato per il movimento della mappa: la tua prima costruzione è più breve. Ogni risposta viene controllata, e i file del gioco escono uguali. |

Noto: **le mappe navali non sono ancora pronte.** Un mare prosciugato o dipinto si costruisce e si carica, ma l'acqua
si vede ancora.
