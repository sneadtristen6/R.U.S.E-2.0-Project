**RUSE Launcher 0.4, per i giocatori.** Trova R.U.S.E. tramite Steam, e **Gioca** costruisce una copia del gioco con i
tuoi mod e la avvia. La tua installazione di Steam non viene mai modificata.

**0.4.8.18:** Una correzione dietro le quinte: il controllo di una copia moddata elenca ciò che trova nello stesso ordine su ogni sistema.

- **Dietro le quinte:** il controllo di una copia moddata (quali file del gioco sono cambiati dopo la sua costruzione) ora elenca ciò che trova nello stesso ordine su Windows e su Linux. Ciò che trova non cambia.

**0.4.8.17:** I modelli importati stanno dove sta l'unità, con torrette ed eliche al loro posto; una munizione può avere una classe d'arma tutta sua.

- **Un aggiornamento obbligatorio:** le versioni precedenti non si possono più usare. All'apertura l'app lo installa da sola, e **Gioca** aspetta finché non è installato.
- **Mod con modelli importati del nuovo tipo:** lo Studio ora adatta il modello importato di un'unità dove sta l'unità, con uno scheletro tutto suo, così la torretta gira dove si trova la torretta del modello e le eliche di un aereo girano dove le ha il modello, quante ne ha; anche soldati, serventi di un cannone e altri aerei possono avere modelli tutti loro. Gioca queste mod con questo Launcher o uno più nuovo: uno più vecchio dà al modello lo scheletro dell'unità copiata, così la torretta gira intorno al punto sbagliato. Le mod fatte prima si giocano come prima. Provato in gioco su copie di prova costruite come costruisce il Launcher; non ancora giocato dal Launcher stesso.
- **Una classe d'arma propria per una munizione:** una mod ora può dare a una munizione un danno proprio contro ogni tipo di bersaglio (fatto nella pagina delle munizioni dello Studio). Nel Launcher non è cambiato nulla per questo: una mod così si costruisce come qualsiasi altra.

**0.4.8.16:** Risoluzione problemi conserva le copie del gioco che hai fatto tu.

- **Corretto: «Eliminale» in Risoluzione problemi cancellava copie fatte da te.** Una copia del gioco costruita a mano nella cartella delle copie, una copia di prova o una copia di riferimento contava come avanzo, ed «Eliminale» la cancellava per sempre, non nel Cestino. Ogni copia costruita che non sia la copia con mod dell'app ora porta una piccola nota «da tenere», e una copia che ce l'ha non è mai un avanzo: Risoluzione problemi elimina solo gli avanzi delle app stesse (copie costruite a metà, quelle che le vecchie versioni facevano per ogni set di mod). Scoperto sul nostro PC il 1° novembre, quando si è portato via ogni copia di prova. Una copia costruita prima di questa versione non ha ancora la nota: ricostruiscila una volta con questa versione, o lascia stare «Eliminale» fino ad allora.

**0.4.8.15:** Anche Originale ha il titolo R.U.S.E. 2.0 in oro.

- **Anche Originale ha il titolo R.U.S.E. 2.0 in oro:** Gioca su Originale ora costruisce la copia con le mod senza nessuna mod e con il titolo in oro, e avvia il gioco da lì, come fa un set di mod: la prima volta la costruisce, poi parte subito, a meno che nel frattempo tu abbia giocato un set di mod. RUSE Guard è attivo nelle sue partite multigiocatore, come in quelle di ogni set. Togli la spunta al titolo in oro nelle Impostazioni e Originale si avvia tramite Steam come prima. La tua installazione Steam non viene mai modificata.

**0.4.8.14:** Le mod con un proprio script di partita si costruiscono di nuovo.

- **Corretto: Gioca si fermava con alcuni set di mod** con «RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...»: alcune mod portano un proprio script di partita la cui intestazione chiede più spazio di quanto serva allo script (tra cui 1 VS 7 AI, 1 VS 15 AI, Operation Overlord e Sand Box). Il gioco esegue questi script senza problemi, ma il Launcher li rifiutava, quindi nessun set con una di queste mod si poteva costruire. Ora li legge come fa il gioco.

**0.4.8.13:** I rapporti di crash del gioco dicono cosa ha portato al crash.

- **I rapporti di crash del gioco di Bug Watch dicono di più:** se hai spuntato Bug Watch e il gioco va in crash, il rapporto ora dice anche cosa il gioco stava cercando di leggere o scrivere, e fino a 16 punti del gioco che hanno portato al crash, letti dal rapporto di crash del gioco stesso sul tuo PC, che continua a non lasciarlo mai. Un rapporto che diceva solo dove il gioco si era fermato non poteva mostrare perché; ora possiamo risalire a crash come quello che un giocatore ci ha inviato questa settimana, e correggerli.
- **L'accordo, versione 3:** ora elenca queste due novità tra ciò che contiene un rapporto di crash del gioco, e nient'altro è cambiato. Poiché è cambiato, entrambe le app te lo mostrano ancora una volta all'apertura.

**0.4.8.12:** Gioca costruisce di nuovo i giochi moddati.

- **Corretto: Gioca si fermava con ogni set di mod** con «No such file or directory: ...fairplay_watch.bin»: agli installer della 0.4.8.10 e della 0.4.8.11 mancavano tre file di RUSE Guard, quindi non si poteva costruire nessun gioco moddato. Ora ci sono di nuovo, e un'app a cui manca uno dei suoi file non può più essere pubblicata.

**0.4.8.11:** l'accesso tramite Steam si completa nelle app; su Linux i programmi di aiuto di una build partono come su Windows.

- **Corretto: accesso tramite Steam.** Dopo che avevi effettuato l'accesso sulla pagina di Steam, il Launcher e lo Studio restavano in attesa e non chiedevano mai al nostro server se avevi finito: la finestra fermava i propri controlli prima del primo. Ora controlla ogni pochi secondi e ti fa accedere appena Steam lo conferma. Provato nell'anteprima: il controllo parte e la finestra ti mostra connesso.
- **I programmi di aiuto partono da zero su ogni sistema:** i programmi tra cui una build divide il lavoro (modelli importati, riparazione della mappa, movimento, acqua) ora partono da zero anche su Linux, come hanno sempre fatto su Windows. Su Linux partivano come copie dell'app in esecuzione, il che a volte poteva bloccare una build, e faceva fallire lì uno dei nostri controlli. Non cambia nulla su Windows né con Proton sullo Steam Deck.

**0.4.8.10:** mod oltre 4 GB, liste di costruzione in gruppi, build più veloci per le mod grandi, il persiano e ogni pagina in 11 lingue, correzioni dalle segnalazioni dei tester; e RUSE Guard, il nostro anti-cheat per le vere partite multigiocatore, con un codice partita; Bug Watch, rapporti su crash e uso che puoi attivare; l'accesso con Steam; e un accordo al primo avvio.

- **Corretto, segnalato da un giocatore: mod oltre 4 GB.** Un set di mod il cui gioco moddato superava 4 GB non si costruiva più con Gioca («'I' format requires 0 <= number <= 4294967295»). Ora i pacchetti portano la loro lunghezza intera, e uno oltre 4 GB viene scritto in una disposizione più ampia che il gioco può leggere grazie a una piccola patch del gioco: scaricata una volta e applicata solo alla tua copia moddata, mai al gioco nella tua cartella di Steam. Oltre 32 GB, o per un singolo file oltre 4 GB, la build lo dice chiaramente. Provato in gioco: copie oltre 4 GB, e con 200, 283 e tutte le 366 unità di altre epoche.
- **Molti modelli tuoi:** il gioco trova le texture sostitutive di un pacchetto tramite un indice, e una build che ne aggiungeva per i modelli importati lo scriveva male: con molte unità di altre epoche il gioco si bloccava o andava in crash durante il caricamento. Ora viene scritto come il gioco lo legge, per ogni mod che ne aggiunge. Provato in gioco con tutte le 366 unità di altre epoche.
- **Liste di costruzione in gruppi:** una mod con molte unità ha la lista di costruzione di ogni edificio in gruppi, le linee del gioco stesso: al massimo 6 unità per gruppo e 10 gruppi per edificio, così l'intera lista resta sullo schermo e ogni unità si può costruire. Una mod fatta prima che supera questi limiti si costruisce comunque, con un avviso. Provato in gioco con 297 unità di altre epoche in gruppi.
- **Build più veloci:** i modelli nelle tue mod vengono tenuti da una build all'altra, e quelli nuovi vengono creati in parallelo sui core del tuo PC. Una mod con 366 unità di altre epoche richiedeva circa 18 minuti di build su un PC a 8 core; ora circa 5 la prima volta e circa 3 dopo, con gli stessi file di gioco, byte per byte.
- **Segnalazioni dei tester:** una mod di unità e le modifiche a una mappa fatte con lo stesso nome si costruiscono insieme (fermavano Gioca); una mappa con i ponti propri tolti si costruisce con i nuovi ponti; le parti di torretta e i cannoni trainati importati si costruiscono come li fa lo Studio 0.9.8.10. I ponti e le parti di torretta non ancora provati in gioco.
- **I tuoi file:** Rimuovi manda una mod della libreria nel Cestino, Mostra nella cartella apre una mod dove si trova, e le Impostazioni mostrano dove sono tenuti i tuoi file. Visto in un'anteprima; non ancora provato nella finestra dell'app.
- **Persiano e 11 lingue:** il persiano è l'11ª lingua delle app, scritto da destra a sinistra; il README, la wiki, queste note e le schermate di installazione sono in tutte e 11.
- **Aggiornamenti obbligatori:** un aggiornamento che segniamo come obbligatorio si installa da solo, con una finestra che nessuno può chiudere (le app da questa versione in poi sanno leggere il segno).
- **Solo copie possedute:** prima che Gioca costruisca una copia moddata, le app controllano che la cartella del gioco sia una copia che possiedi, da ciò che Steam vi ha lasciato, su Windows, con Proton sullo Steam Deck e su Linux. Se la tua non può essere confermata (una copia in scatola di prima che R.U.S.E. arrivasse su Steam), una finestra ti fa aprire un ticket, e ti mandiamo un codice di sblocco per quel PC.
- **Discord:** le app e le pagine usano un nuovo invito che non scade.
- **Un accordo al primo avvio:** la prima volta che lo Studio o il Launcher si apre, spiega cosa fa RUSE Guard e ti chiede di accettarlo (serve per giocare online con le app), se attivare Bug Watch (facoltativo), e un nome utente che i nostri sviluppatori vedono con i tuoi rapporti: vi si aggiungono un # e quattro numeri perché sia unico, come Nick#4821. Un solo nome vale per entrambe le app. L'accordo ricompare quando cambia. Visto in entrambe le app. In tutte e 11 le lingue.
- **RUSE Guard:** il nostro anti-cheat, dal progetto di DomesticNukes. Funziona solo nelle partite multigiocatore e cooperative, mai in giocatore singolo, nella schermaglia contro il computer o nella campagna. Il tuo gioco moddato riceve un **codice partita** da mandare a chi gioca con te: lo stesso codice vuol dire lo stesso gioco, la stessa versione, le stesse mod e versioni delle mod, così una partita non può andare fuori sincrono. Una mod che cambia gli script del gioco mostra il distintivo **Esegue script**, e Gioca aspetta che tu spunti di fidarti del suo autore; un trucco o uno strumento di prova mostra **Trucco** e rende la copia solo offline: lascia da sé le partite multigiocatore e cooperative. Durante una vera partita RUSE Guard confronta i nomi dei programmi in esecuzione con un elenco di strumenti di cheat noti (solo i nomi; non legge altro), e ciò che raccoglie è archiviato sotto il tuo nome utente, mai sotto il tuo account Steam. Provato in partite multigiocatore contro un avversario vero; le prove arrivano al nostro server.
- **Bug Watch (facoltativo):** quando lo spunti, lo Studio e il Launcher contano cosa usi e quando qualcosa va storto, i crash delle app e quelli del gioco, con le mod che erano attive, e lo mandano una volta al giorno ai nostri sviluppatori con il tuo nome utente. Niente nomi veri, niente account Steam, niente file. Spento finché non lo spunti; toglilo quando vuoi e ciò che era conservato viene cancellato. Visto in entrambe le app.
- **Accedi con Steam:** un accesso sulla pagina di Steam nel tuo browser conferma che possiedi R.U.S.E., per il gioco online, RUSE Guard e i download di contenuti. Non vediamo mai la tua password, e il tuo ID Steam non viene mai salvato: solo un pass conservato sul tuo PC per 30 giorni. È nelle Impostazioni, **Accesso con Steam**; il Launcher lo chiede una volta. Nulla lo richiede ancora. Non ancora provato nell'app.

**0.4.8.9:** le mod si installano su più PC, e una lettura delle immagini più sicura.

- **Corretto, segnalato da un giocatore:** su alcuni PC nessuna mod si installava: «questo PC non si fida del certificato di sicurezza del sito (unable to get issuer certificate)». Windows su quei PC non ha il certificato con cui vengono controllati i download di GitHub e non riesce a recuperarlo. Il Launcher ora prova anche con l'elenco di certificati di Firefox, che porta con sé. Fino ad allora, una mod scaricata nel browser dall'elenco delle mod si installa con **Aggiungi un file di mod…**.
- **Immagini più sicure:** la libreria con cui il Launcher legge le immagini (Pillow) passa alla versione 13.0.0, con le sue correzioni contro file d'immagine fatti apposta che potevano far chiudere l'app, esaurirne la memoria o peggio.
- **Codice più rigoroso:** i 12 avvisi del controllo del codice di GitHub su questo progetto sono risolti. Quando il Launcher mostra le sue pagine nel tuo browser, aprono solo i suoi file, controllati in un modo che quel controllo riconosce, e i download chiedono TLS 1.2 o più recente, come già prima. Nel funzionamento del Launcher non cambia nulla.

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

**0.4.6:** **Gioca** parte subito quando non è cambiato nulla, e avvia le mod fatte con Studio 0.9.6: nuove unità con un
modello 3D tutto loro.

| Prima | Ora |
|---|---|
| **Gioca** ricostruiva ogni volta tutta la copia moddata, anche se non era cambiato nulla (un giocatore: «30 minuti di attesa ogni volta»). | Non è cambiato nulla: il gioco parte subito. Una modifica fa ricostruire, ma i file invariati dell'ultima copia vengono riusati, così una copia su un'unità diversa da quella del gioco non ricopia più ogni pacchetto. Gioca dice quanto ha copiato. |
| Ogni build rileggeva da capo i dati delle unità del gioco. | Tenuti tra una build e l'altra: una grande mod di prova richiedeva 213 s ogni volta; ora le build dopo la prima richiedono 68 s. |
| La nuova unità di una mod aveva il modello dell'unità che copia. | Il suo modello, preso dalla mod (`files/models`), è in gioco. **Visto in gioco:** un M1 Abrams accanto allo Sherman. |
| La nuova unità di una mod con una sua carta faceva crashare il gioco quando veniva costruita. | Corretto. **Visto in gioco.** |
| I colori delle unità ridipinte uscivano un po' sbagliati in alcuni punti. | Più vicini all'immagine della mod. Una mod con unità ridipinte o terreno dipinto riceve una nuova impronta e un nuovo codice per unirsi alla partita: chi gioca insieme dovrebbe aggiornare. |
| Un avvio lento non lasciava alcun indizio. | **Copia il rapporto** elenca i passi degli ultimi cinque avvii. |
| — | Avvia le mod con la cancellazione di tutta la mappa di Studio 0.9.6, le strade su terreno rimodellato e il riempimento dei letti dei fiumi (nuovo, non ancora visto in gioco su larga scala). |

**0.4.5:** avvia le mod fatte con Studio 0.9.5: unità ridipinte, le loro carte, e unità con modelli tutti loro.

| Prima | Ora |
|---|---|
| Una mod non poteva cambiare l'aspetto di un'unità. | Le unità ridipinte e le carte di una mod si vedono in gioco. **Visto in gioco:** uno Sherman rosso, una carta fatta nello Studio. |
| Una mod i cui pacchetti di modelli delle unità diventavano più grandi veniva scartata dal gioco: un crash alla prima fabbrica. | Costruiti nel modo in cui il gioco li controlla. **Visto in gioco:** un secondo Sherman con un modello tutto suo. |
| Una mod che fa comparire unità di un'altra nazione in un capitolo di campagna o in un'Operazione crashava durante il caricamento (unità francesi su Holland). | Anche lì i loro modelli si caricano. **Visto in gioco.** |
| Spianare le montagne al bordo di una mappa lasciava lì un dirupo. | Il bordo segue il terreno. **Visto in gioco.** |

**0.4.4:** avvia le mod con nuove mappe, fatte con Duplica mappa di Studio 0.9.4.

| Prima | Ora |
|---|---|
| Le nuove mappe di una mod non erano mai state provate in gioco. | **Visto in gioco:** la nuova mappa di una mod compare in BATTAGLIE e si gioca sul suo terreno, anche 101 mappe insieme. Ancora agli inizi: segnala ciò che trovi. |
| Gli aggiornamenti arrivavano solo come versioni intere. | Piccole correzioni possono arrivare tra una versione e l'altra (0.4.4.1), proposte come qualsiasi aggiornamento. |

**0.4.3:** avvia le mod fatte con Studio 0.9.3, e le costruisce circa tre volte più in fretta.

| Prima | Ora |
|---|---|
| Le rocce e la maggior parte degli altri oggetti piazzati da una mod sparivano appena la telecamera si allontanava. | Disegnati fino alla distanza massima; gli oggetti della mappa stessa non cambiano. **Visto in gioco.** |
| La nuova strada di una mod attraverso un bosco era una striscia chiara vista dall'alto, o spariva dalla media-lunga distanza. | Dipinta attraverso i boschi come le strade della mappa stessa. **Visto in gioco.** |
| Le strade di una mod toglievano sempre gli alberi dal loro percorso. | Una strada può tenerli (`keep_trees`): passa sotto gli alberi, più tenue e più grigia in un bosco. |
| **Gioca** impiegava circa 5 minuti per costruire una mod con nuove strade su M03_Italie. | Circa 1½ minuti dopo la prima volta su una mappa. |

**0.4.2:** avvia le mod fatte con Studio 0.9.2.

| Prima | Ora |
|---|---|
| Una mod con una strada sull'acqua su Italia, Germania, Olanda e altre mappe veniva rifiutata: il suo ponte «non avrebbe avuto un piano». | Costruita: il ponte riceve il piano della mappa stessa. Non ancora visto in gioco su quelle mappe. |
| Una mod che dava unità al giocatore in un capitolo di campagna (schieramento 0) veniva rifiutata, e le unità per gli schieramenti del computer ricevevano l'avviso «potrebbero non comparire mai». | Costruita; l'avviso resta solo per uno schieramento che la missione del capitolo non ha. |
| Su M03_Italie e altre mappe, la nuova strada di una mod in campo aperto nascondeva da lontano lo scenario della mappa, e i suoi oggetti si vedevano solo da vicino. | La vista da lontano della mappa resta com'era, e gli oggetti della mod si vedono da lontano. Non ancora visto in gioco. |

**0.4.1:** la tua lingua dal primo avvio, e un editor dei set di mod che trova le mod per nome.

| Prima | Ora |
|---|---|
| Creare un set di mod elencava tutta la tua libreria con Crea in fondo, e non c'era modo di trovare una mod per nome. | Crea è in alto, con le mod già nel set subito sotto; più giù, «Aggiungi mod dalla tua libreria» con una ricerca che restringe l'elenco mentre scrivi. |
| La lingua stava nelle Impostazioni, così i giocatori non sapevano che il Launcher parla la loro lingua. | Il primo avvio chiede: «Scegli la tua lingua», ogni lingua scritta con le sue parole, con segnata quella impostata per il tuo gioco in Steam (chi aggiorna la vede una volta). Poi un pulsante della lingua in alto, sempre in vista. |
| L'elenco delle app installate di Windows mostrava la prima versione mai installata. | Mostra la versione che hai. |

**0.4.0:** avvia le mod con nuove strade come le costruisce Studio 0.9: sembrano le strade della mappa stessa, dall'alto
e fin giù al suolo (provato in gioco su D-Day).

![Una nuova strada da vicino su D-Day](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Prima | Ora |
|---|---|
| Le nuove strade di una mod sparivano da vicino. | Sono disegnate con l'asfalto e le decal dei bordi della mappa stessa, dipinte come le strade della mappa, e le piante sul loro percorso vengono tolte. |
| Una mod con molti cerchi da cancellare richiedeva minuti per essere costruita. | Molto più veloce. |

**0.3.3:** avvia le mod fatte con Studio 0.8.3.

| Prima | Ora |
|---|---|
| Una mod con una telecamera iniziale ruotata (Studio 0.8.3) veniva rifiutata. | Costruita: la telecamera è ruotata come dice la mod. |
| La telecamera iniziale di un punto di partenza spostato restava al vecchio posto. | La telecamera si sposta con lui; un nuovo punto di partenza riceve una telecamera tutta sua. |
| Una mod con un punto di partenza in un bosco veniva rifiutata. | Costruita: lì un QG funziona. |

**0.3.2:** una sola copia del gioco per tutto il PC, la versione in vista, e una libreria più chiara.

| Prima | Ora |
|---|---|
| Ogni set di mod costruiva la sua copia del gioco. | Una sola copia moddata per tutto il PC, condivisa con lo Studio. |
| La versione non si vedeva, e Novità era un elenco. | La versione è accanto al nome, e Novità apre una tabella prima/dopo come questa. |
| Mappe e mod sembravano uguali nella libreria. | Una mappa ha un'etichetta MAPPA. |
| Pochi suggerimenti. | Suggerimenti sui comandi principali. |
| Le mod con nuove strade su Twilight of the Gods, Alpha, Ostfriesland e Robert non avevano il modello stradale della mappa. | Ora lo ricevono anche loro. |

**0.3.1:** le mod con unità di un'altra nazione (un Tiger tedesco per gli USA, per esempio) funzionano, anche in una
partita in cui nessuno gioca quella nazione (provato in gioco, 2026-10-02). E un nuovo aspetto: i blu di R.U.S.E. al
posto del nero e oro, e un nuovo logo: un caccia che sale tra le nuvole. La barra laterale ha due schede, **Set di
mod** e **Libreria delle mod**, ognuna a tutta altezza, così si raggiunge tutta la tua libreria (metà era nascosta
dietro la barra di scorrimento), con una ricerca e un conteggio. Il programma di installazione propone un **backup
pulito del gioco** accanto al collegamento sul desktop, e dice perché.

**0.3.0:** **Mod supportate:** il Launcher mostra il nostro elenco delle mod
([sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods)); spunta quelle che vuoi e vengono scaricate e
controllate. Al primo avvio scegli le tue mod; le mod cheat sono tenute a parte e mai spuntate al posto tuo. Un
pulsante **Risoluzione problemi** (nella barra in basso, e in ogni messaggio di problema) controlla in un colpo solo ciò
che può fermare **Gioca** e corregge ciò che può, con un rapporto da incollare in una segnalazione di bug. Un **backup
pulito del gioco** nelle Impostazioni tiene una copia pulita dei file del tuo gioco e rimette a posto tutto ciò che un
altro gestore di mod ha cambiato (oppure lascia che lo ripari Steam). Le mod fatte con il nuovo Studio funzionano come
sono state fatte: carri e fanteria attraversano i nuovi ponti sopra l'impalcato, la fanteria segue le nuove strade, i
boschi sgombrati sono aperti alle unità, gli edifici piazzati poggiano sul terreno a qualsiasi dimensione, e la
copertura cade dove è stata dipinta su D-Day e sulle altre mappe che non sono quadrate. Problema noto: le nuove strade
non sono ancora disegnate da vicino (si vedono da lontano).

**0.2.11:** **Gioca** funziona ogni volta: una copia moddata che Windows non vuole eliminare (un file collegato da una
versione più vecchia, un programma che lo tiene ancora aperto) viene messa da parte in `RUSE-Instances\.trash` invece di
fermare il gioco, e un gioco ancora in esecuzione dalla copia viene indicato per nome. Le mod con nuovi ponti non creano
mai terreno che le unità di terra non possono raggiungere (faceva crashare il gioco).

**0.2.9:** **Gioca** funziona quando i file del tuo gioco sono segnati come di sola lettura: falliva con «[WinError 5]
Access is denied» quando una copia moddata restava costruita a metà. Se il gioco è ancora in esecuzione dalla copia
moddata, ti viene detto di chiuderlo invece di ricevere un errore di Windows. Le mod con nuove strade costruiscono le
loro strade dipinte e i loro ponti.

**0.2.8:** una mod che aggiungi viene controllata subito, nel modo in cui la leggerà la build del gioco: un file di mappa
rotto, o una cartella di mappa chiamata come il titolo della mappa (maps/Blitz invece di maps/SuperCrossRoads4), viene
indicato con la sua correzione prima che Gioca si fermi lì.

**0.2.7:** **Aiuto** e **Segnala un problema** nella barra in basso: la wiki (un manuale da campo per giocare con le
mod), e una segnalazione di bug nel tuo browser con la versione del Launcher già compilata. Un messaggio di problema ha
il suo link **Segnala**. Il Launcher non invia nulla: leggi tu la segnalazione e la pubblichi. Le mod la cui cartella di
mappa è chiamata come il titolo della mappa (maps/Blitz invece di maps/SuperCrossRoads4) ora ricevono l'indicazione
della correzione.

**0.2.6:** un pulsante **Impostazioni** (in alto a destra): la lingua, la cartella del gioco e gli aggiornamenti in un
solo posto, pronto per altro.

**0.2.5:** trovare gli aggiornamenti è più affidabile: quando GitHub rifiuta l'unico controllo all'avvio (ne permette 60
all'ora per indirizzo internet, condivisi da tutto ciò che lo usa), il Launcher legge invece l'elenco delle release di
GitHub.

**0.2.4:** la tua lingua viene tenuta attraverso riavvii, aggiornamenti e reinstallazioni.

**0.2.3:** il riquadro rosso si ripiega come quello giallo (un set grande può elencare decine di conflitti).

**0.2.2: Metti nell'ordine migliore.** Quando le mod di un set cambiano gli stessi valori, il riquadro giallo ha un
pulsante **Metti nell'ordine migliore**: le mod che cambiano di più vanno prima e quelle più piccole dopo, così ognuna
tiene quante più modifiche possibile. Dice quali mod salva, e le mod si possono ancora spostare a mano.

**0.2.1: le mod che non vanno insieme non si possono giocare, e il Launcher dice perché.** Quando due mod di un set
sostituiscono lo stesso file o script, un riquadro rosso nomina le mod e ciò che cambiano entrambe, e Gioca resta
spento finché una non viene tolta. Quando una mod successiva sovrascrive solo valori di una precedente (la velocità di
una nave, per esempio), un riquadro giallo li elenca e il set si gioca comunque.

**Novità della 0.2:**

- **Set di mod fatti nella finestra:** nuovo, modifica, rinomina, duplica, elimina, e metti le mod in ordine. Niente più
  file da modificare a mano. Una guida in tre passi nella prima schermata mostra la strada.
- **Aggiungi un file di mod…** (o trascinalo sulla finestra): un `.rusemod` esportato da RUSE Studio, una cartella di
  mod in uno `.zip`, o un **`.rmod` di RUSE Mod Manager**, usato così com'è (applicato dal motore di LittleGroove
  stesso).
- **Condividi un ordine di caricamento** come testo, e **Importa un ordine di caricamento…** da un amico: il Launcher
  dice quali mod hai, quali mancano e quali sono di un'altra versione, poi crea il set. È lo stesso testo che RUSE Mod
  Manager copia e legge, così gli ordini di caricamento vanno in tutte e due le direzioni.
- **Si aggiorna da solo:** da questa versione in poi, quando esce un Launcher più nuovo, una barra lo dice; **Aggiorna
  ora** lo scarica, controlla il suo SHA-256 e lo installa, e il Launcher si riavvia da solo.

I tuoi set di mod della 0.1 vengono tenuti. Problemi e idee: GitHub Issues.

![RUSE Launcher](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/launcher.jpg)
