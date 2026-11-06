**RUSE Studio, un'anteprima per i modder.** Sfoglia le unità del gioco in una qualsiasi delle sue dieci lingue,
modificale in un mod tuo e provalo in gioco. La tua installazione di Steam non viene mai modificata.

**0.9.8.16:** Risoluzione problemi conserva le copie del gioco che hai fatto tu.

- **Corretto: «Eliminale» in Risoluzione problemi cancellava copie fatte da te:** la stessa correzione del Launcher (un solo codice per entrambe le app). Una copia del gioco costruita a mano nella cartella delle copie, una copia di prova o una copia di riferimento contava come avanzo e veniva eliminata per sempre. Ogni copia del genere ora porta una piccola nota «da tenere», e una copia che ce l'ha non è mai un avanzo: vengono eliminati solo gli avanzi delle app stesse (copie costruite a metà, quelle che le vecchie versioni facevano per ogni set di mod). Una copia costruita prima di questa versione non ha ancora la nota: ricostruiscila una volta con questa versione, o lascia stare «Eliminale» fino ad allora.

**0.9.8.15:** Anche Originale ha il titolo R.U.S.E. 2.0 in oro.

- **Nello Studio stesso non cambia nulla:** questo aggiornamento è del Launcher (anche Originale ha il titolo R.U.S.E. 2.0 in oro). La casella del titolo in oro nelle Impostazioni dello Studio è la stessa impostazione del Launcher, quindi togliendo la spunta qui anche Originale si avvia tramite Steam.

**0.9.8.14:** Le mod con un proprio script di partita si costruiscono di nuovo.

- **Corretto: Prova in gioco si fermava con alcune mod** con «RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...»: alcune mod portano un proprio script di partita la cui intestazione chiede più spazio di quanto serva allo script (tra cui 1 VS 7 AI, 1 VS 15 AI, Operation Overlord e Sand Box). Il gioco esegue questi script senza problemi, ma lo Studio li rifiutava, quindi non si poteva costruire niente con una di queste mod. Ora li legge come fa il gioco.

**0.9.8.13:** I rapporti di crash del gioco dicono cosa ha portato al crash.

- **I rapporti di crash del gioco di Bug Watch dicono di più:** se hai spuntato Bug Watch e il gioco va in crash, il rapporto ora dice anche cosa il gioco stava cercando di leggere o scrivere, e fino a 16 punti del gioco che hanno portato al crash, letti dal rapporto di crash del gioco stesso sul tuo PC, che continua a non lasciarlo mai. Un rapporto che diceva solo dove il gioco si era fermato non poteva mostrare perché; ora possiamo risalire a crash come quello che un giocatore ci ha inviato questa settimana, e correggerli.
- **L'accordo, versione 3:** ora elenca queste due novità tra ciò che contiene un rapporto di crash del gioco, e nient'altro è cambiato. Poiché è cambiato, entrambe le app te lo mostrano ancora una volta all'apertura.

**0.9.8.12:** Prova in gioco costruisce di nuovo i giochi moddati.

- **Corretto: Prova in gioco si fermava con ogni mod** con «No such file or directory: ...fairplay_watch.bin»: agli installer della 0.9.8.10 e della 0.9.8.11 mancavano tre file di RUSE Guard, quindi non si poteva costruire nessun gioco moddato. Ora ci sono di nuovo, e un'app a cui manca uno dei suoi file non può più essere pubblicata.

**0.9.8.11:** l'accesso tramite Steam si completa nelle app; su Linux i programmi di aiuto di una build partono come su Windows.

- **Corretto: accesso tramite Steam.** Dopo che avevi effettuato l'accesso sulla pagina di Steam, il Launcher e lo Studio restavano in attesa e non chiedevano mai al nostro server se avevi finito: la finestra fermava i propri controlli prima del primo. Ora controlla ogni pochi secondi e ti fa accedere appena Steam lo conferma. Provato nell'anteprima: il controllo parte e la finestra ti mostra connesso.
- **I programmi di aiuto partono da zero su ogni sistema:** i programmi tra cui una build divide il lavoro (modelli importati, riparazione della mappa, movimento, acqua, terreno della vista della mappa) ora partono da zero anche su Linux, come hanno sempre fatto su Windows. Su Linux partivano come copie dell'app in esecuzione, il che a volte poteva bloccare una build, e faceva fallire lì uno dei nostri controlli. Non cambia nulla su Windows né con Proton sullo Steam Deck.

**0.9.8.10:** mod oltre 4 GB, liste di costruzione in gruppi, build più veloci per le mod grandi, i tuoi file in Documents\RUSE 2.0, il persiano e ogni pagina in 11 lingue, correzioni dalle segnalazioni dei tester; e RUSE Guard, il nostro anti-cheat per le vere partite multigiocatore; Bug Watch, rapporti su crash e uso che puoi attivare; l'accesso con Steam; e un accordo al primo avvio.

- **Corretto, segnalato da un giocatore: mod oltre 4 GB.** Un gioco moddato i cui pacchetti superavano 4 GB non si costruiva più («'I' format requires 0 <= number <= 4294967295»). Ora i pacchetti portano la loro lunghezza intera, e uno oltre 4 GB viene scritto in una disposizione più ampia che il gioco può leggere grazie a una piccola patch del gioco: scaricata una volta e applicata solo alla tua copia moddata, mai al gioco nella tua cartella di Steam. Oltre 32 GB, o per un singolo file oltre 4 GB, la build lo dice chiaramente. Provato in gioco: copie oltre 4 GB, e con 200, 283 e tutte le 366 unità di altre epoche.
- **Molti modelli tuoi:** il gioco trova le texture sostitutive di un pacchetto tramite un indice, e una build che ne aggiungeva per i modelli importati lo scriveva male: con molte unità di altre epoche il gioco si bloccava o andava in crash durante il caricamento. Ora viene scritto come il gioco lo legge, per ogni mod che ne aggiunge. Provato in gioco con tutte le 366 unità di altre epoche.
- **Liste di costruzione in gruppi:** con molte unità, la lista di costruzione di un edificio usciva dallo schermo e le unità in basso non si potevano raggiungere. Ora ogni lista mostra una riga per gruppo, le linee del gioco stesso (una nuova unità entra nel gruppo del suo tipo): al massimo 6 unità per gruppo e 10 gruppi per edificio, così l'intera lista resta sullo schermo. Lo Studio dice perché quando un gruppo è pieno e mostra i gruppi dove aggiungi le unità; una mod fatta prima che supera questi limiti si costruisce comunque, con un avviso. Provato in gioco con 297 unità di altre epoche in gruppi.
- **Build più veloci:** i modelli che importi vengono tenuti da una build all'altra, e quelli nuovi vengono creati in parallelo sui core del tuo PC. Una mod con 366 unità di altre epoche richiedeva circa 18 minuti di build su un PC a 8 core; ora circa 5 la prima volta e circa 3 dopo, con gli stessi file di gioco, byte per byte.
- **Modelli importati (segnalazioni dei tester):** una parte di torretta su un osso che l'aspetto copiato non elenca (un M109 copiato dal M7 Priest) fermava l'importazione; ora va nella lista propria della copia. Una parte di torretta su un modello senza torretta (il P-40, l'M274 Mule) segue lo scafo, un cannone trainato visto da lontano mostra il proprio modello, e una texture sottile a striscia riceve la sua texture sostitutiva. I cannoni trainati provati in gioco; le parti di torretta non ancora guardate da vicino.
- **Ponti (segnalazione di un tester):** una sola scheda Ponti: un nuovo ponte, i tuoi ponti (ciascuno con Vai ed Elimina) e i ponti propri della mappa con i loro attraversamenti, tolti o rimessi con un solo pulsante. Un nuovo ponte conta quando togliere i vecchi taglia la mappa in due, e modellare il terreno tiene le estremità dei ponti della mappa alla loro altezza. Rimuovi è più facile da trovare (Dipingi e rimuovi, o il tasto X). Una mod di unità e le modifiche a una mappa fatte con lo stesso nome si costruiscono insieme, e la vista della mappa mostra di nuovo i modelli del gioco. Non ancora provato in gioco.
- **I tuoi file in Documents\RUSE 2.0:** le tue mod, mappe, esportazioni e copie di sicurezza vanno in Documents\RUSE 2.0, dove Esplora file le mostra; ciò che lo Studio teneva nella sua vecchia cartella viene spostato lì una volta, e lo dice. Elimina una mod… la manda nel Cestino, Mostra la cartella di questa mod la apre, e le Impostazioni mostrano dove si trova tutto. Visto in un'anteprima; non ancora provato nelle finestre delle app.
- **Persiano e 11 lingue:** il persiano è l'11ª lingua delle app, scritto da destra a sinistra; il README, la wiki, queste note e le schermate di installazione sono in tutte e 11.
- **Aggiornamenti obbligatori:** un aggiornamento che segniamo come obbligatorio si installa da solo, con una finestra che nessuno può chiudere (le app da questa versione in poi sanno leggere il segno). La finestra Novità mantiene la sua altezza mentre la scorri.
- **Solo copie possedute:** prima che Gioca o Prova in gioco costruisca una copia moddata, le app controllano che la cartella del gioco sia una copia che possiedi, da ciò che Steam vi ha lasciato, su Windows, con Proton sullo Steam Deck e su Linux. Se la tua non può essere confermata (una copia in scatola di prima che R.U.S.E. arrivasse su Steam), una finestra ti fa aprire un ticket, e ti mandiamo un codice di sblocco per quel PC.
- **Discord:** le app e le pagine usano un nuovo invito che non scade.
- **Un accordo al primo avvio:** la prima volta che lo Studio o il Launcher si apre, spiega cosa fa RUSE Guard e ti chiede di accettarlo (serve per giocare online con le app), se attivare Bug Watch (facoltativo), e un nome utente che i nostri sviluppatori vedono con i tuoi rapporti: vi si aggiungono un # e quattro numeri perché sia unico, come Nick#4821. Un solo nome vale per entrambe le app. L'accordo ricompare quando cambia. Visto in entrambe le app. In tutte e 11 le lingue.
- **RUSE Guard:** il nostro anti-cheat, dal progetto di DomesticNukes. Funziona solo nelle partite multigiocatore e cooperative, mai in giocatore singolo, nella schermaglia contro il computer, nella campagna o mentre fai le mod. Una copia moddata costruita con un trucco o uno strumento di prova è solo per il gioco offline: lascia da sé le partite multigiocatore e cooperative. Durante una vera partita confronta i nomi dei programmi in esecuzione con un elenco di strumenti di cheat noti (solo i nomi; non legge altro), e ciò che raccoglie da una partita è archiviato sotto il tuo nome utente, mai sotto il tuo account Steam. Prova nel gioco costruisce le sue copie con lui. Provato in partite multigiocatore contro un avversario vero; le prove arrivano al nostro server.
- **Bug Watch (facoltativo):** quando lo spunti, lo Studio e il Launcher contano cosa usi e quando qualcosa va storto, i crash delle app e quelli del gioco, con le mod che erano attive, e lo mandano una volta al giorno ai nostri sviluppatori con il tuo nome utente. Niente nomi veri, niente account Steam, niente file. Spento finché non lo spunti; toglilo quando vuoi e ciò che era conservato viene cancellato. Visto in entrambe le app.
- **Accedi con Steam:** un accesso sulla pagina di Steam nel tuo browser conferma che possiedi R.U.S.E., per il gioco online, RUSE Guard e i download di contenuti. Non vediamo mai la tua password, e il tuo ID Steam non viene mai salvato: solo un pass conservato sul tuo PC per 30 giorni. Lo Studio lo chiede una volta; le Impostazioni del Launcher lo aprono quando vuoi. Nulla lo richiede ancora. Non ancora provato nelle app.

**0.9.8.9:** download su più PC, e una lettura delle immagini più sicura.

- **Corretto, segnalato da un giocatore:** su un PC il cui Windows non ha il certificato con cui vengono controllati i download di GitHub e non riesce a recuperarlo, i download fallivano («unable to get issuer certificate»). I download dello Studio (i suoi aggiornamenti, le patch del gioco, i modelli delle unità d'epoca e le texture online di Map Paint) ora provano anche con l'elenco di certificati di Firefox, che lo Studio porta con sé.
- **Immagini più sicure:** la libreria con cui lo Studio legge le immagini (Pillow) passa alla versione 13.0.0, con le sue correzioni contro file d'immagine fatti apposta che potevano far chiudere l'app, esaurirne la memoria o peggio.
- **Codice più rigoroso:** i 12 avvisi del controllo del codice di GitHub su questo progetto sono risolti. Quando lo Studio mostra le sue pagine nel tuo browser, aprono solo i suoi file, controllati in un modo che quel controllo riconosce; i download chiedono TLS 1.2 o più recente, come già prima; e la lettura degli errori di strade di un test fallito resta rapida con qualsiasi messaggio. Per il resto, nel funzionamento dello Studio non cambia nulla.

**0.9.8.8:** una schermata iniziale e una tavola degli edifici, edifici tuoi, RUSE Decoy per suoni e animazioni, ogni regola del gioco in una scheda, e R.U.S.E. 2.0 in oro.

- **Una schermata iniziale:** continua la tua mod, iniziane una nuova o saltala (anche sempre). I passi di una nuova mod: il nome, se ogni nazione tiene le sue unità o parte vuota, la ricerca (quella del gioco, nessuna o la tua), la tavola degli edifici, poi cosa cambierà la mod. Visto in gioco.
- **La tavola degli edifici:** gli edifici di ogni nazione come file delle unità che offrono i loro menu di costruzione, nell'ordine del gioco. Mettici un'unità (della nazione, la copia di un'unità di un'altra nazione, un'unità d'epoca), trascinala lungo una fila o verso un altro edificio, toglila, o falla ricercare dall'unità sotto cui va. La pagina di ogni unità dice dove si costruisce. Visto in gioco.
- **Aggiungi un edificio…:** la copia di un edificio del gioco che fa le stesse unità, o un edificio con unità proprie e una sua scheda nella barra di costruzione, fino a tre per nazione. Il secondo e il terzo richiedono una piccola patch del gioco per più edifici: lo Studio la scarica una volta e la applica solo alla tua copia moddata, mai al gioco nella tua cartella di Steam. Visto in gioco.
- **L'aspetto proprio di un edificio:** nella pagina di un nuovo edificio importa un modello 3D al posto di un pezzo dell'aspetto che copia (l'edificio principale di una fabbrica o di un QG, o il pezzo che scegli), e dagli una sua immagine nel menu di costruzione. Visto in gioco.
- **Importa modello… nella scheda Mappe:** un modello 3D (.glb, .gltf o .3ds) diventa una roccia, un oggetto, una pianta o un albero della tua mappa, piazzato come quelli del gioco, con una dimensione e il credito del suo autore (modelli di altri: solo CC0 o CC-BY). Le unità lo abbattono come quelli del gioco; con **Solido** spuntato, ci girano intorno. Visto in gioco.
- **RUSE Decoy, il progettista di suoni e animazioni,** al posto della scheda Musica. Ogni suono del gioco per tipo (armi vicine e lontane, impatti, motori, ambiente, interfaccia, carte stratagemma, voci delle unità, radio, battute delle missioni con ciò che dice ognuna, musica): ascoltalo, dagli un suo volume (da 0 a 200 %) o sostituiscilo. Animazioni: un altro clip al posto di un clip, un clip più lento o più veloce, un osso ingrandito o ruotato, o motion capture sui soldati, da una libreria di 3.205 movimenti liberi (il database di motion capture CMU e 100STYLE, citati), ognuno scaricato quando lo scegli. La pagina di un'unità apre RUSE Decoy sui suoi suoni e animazioni. Visto in gioco. I suoi messaggi d'errore per ora sono solo in inglese.
- **Impostazioni IA e giocatori:** le schede Economia e IA sono una sola. Impostazioni dei giocatori: denaro e rendita, depositi di rifornimento, produzione e carte d'inganno, come prima. Giocatori del computer: ognuno dei loro 47 valori sull'insieme predefinito, ogni difficoltà e ogni personalità (un valore che il gioco omette in un insieme mostra lo 0 che il gioco conta). **Regole del gioco:** altri 172 valori del gioco in 16 gruppi (battaglia e resa, popolazione, movimento e strade, tiro e bersagli, danni, boschi e copertura, aerei, carte d'inganno all'opera, piazzare edifici, partite classificate online, sagome ed effetti sullo schermo, i colori dei giocatori e dei settori con un selettore di colore, e altri), ognuno con nome e spiegazione. Non ancora provato in gioco.
- **Tutti i valori e i file:** le schede Tutti i valori e File sono una sola, con un interruttore in alto; si apre sulla parte usata per ultima.
- **Corretto:** Tutti i valori mostrava i numeri di un colore nell'ordine sbagliato (il gioco tiene prima il blu), quindi il colore del giocatore 1, blu, sembrava arancione, e scrivere il rosso cambiava il blu. Ora i colori si mostrano e si scrivono col rosso prima; un file di mod tiene l'ordine del gioco, come prima.
- **Corretto: macchie scure e chiare sulle mappe fatte dallo Studio** (mappe vuote, ingrandite, a rilievo e a settori): l'inclinazione del terreno era scritta male, così erba e campi erano illuminati in modo irregolare. Una mappa è illuminata bene una volta costruita con questa versione (il suo terreno viene rifatto la prima volta). Visto in gioco.
- **Togliere i vecchi passaggi (da DomesticNukes):** nelle strade della scheda Mappe, con **Togli i ponti della mappa** attivo, **Chiudi i passaggi dei vecchi ponti** chiude anche il terreno dove ogni vecchio ponte stava sopra l'acqua e taglia i collegamenti stradali che lo attraversano: lì non passa più niente; il resto della rete stradale resta. Non ancora provato in gioco.
- **R.U.S.E. 2.0 in oro:** il gioco moddato che costruisce Prova in gioco si apre su una scena di battaglia con un motore che si avvia, e il suo menu principale, il piccolo titolo di ogni menu, i contorni dei menu e le schermate di caricamento dicono R.U.S.E. 2.0 in oro. È fatto sul tuo PC dai file del tuo gioco la prima volta (qualche minuto una volta, poi tenuto). Impostazioni ha una casella per tenere il titolo del gioco. Visto in gioco.
- **Le lettere del gioco:** lo Studio è scritto con il font dei menu del gioco, preso dal tuo gioco a ogni avvio (il font non viene fornito con lo Studio).
- **Corretto, segnalato da un modder:** un modello importato su una nuova unità fatta dal Panther finiva lontano dall'unità; su unità fatte da altre 85 (il GPF da 155 mm, il SU-85, il Carro Veloce, lo StuG III, l'M7 Priest...) stava fuori dalla torretta. Lo Studio ora legge bene dove girano le loro torrette. Un modello importato prima tiene il vecchio posto: usa di nuovo Importa modello… su quell'unità. Non ancora provato in gioco.
- **Corretto, segnalato da un giocatore:** un modello con immagini JPG o WebP (la maggior parte dei .glb scaricati) veniva rifiutato; ora si importa. Un modello che l'importazione non sa ancora leggere (mesh compresse, immagini KTX2) lo dice, e come sistemarlo in Blender. Non ancora provato in gioco.
- **Corretto, segnalato da un giocatore:** un carro del gioco, aperto in Blender e reimportato, teneva la torretta ferma. Apri in Blender ora chiama l'osso di ogni pezzo come fa il gioco, e l'importazione fa girare un pezzo sull'osso della torretta con la torretta. Un modello esportato prima tiene i vecchi nomi: aprilo di nuovo in Blender. Non ancora provato in gioco.
- **Dai un nome alle tue munizioni:** una munizione copiata si chiama in gioco col nome che le dai, e la pagina di ogni munizione ha **Il suo nome in gioco**: un nuovo nome o tipo, in tutte le lingue insieme, poi una lingua da sola. Non ancora provato in gioco.
- **Tipi di flag tuoi:** sotto le flag di un'unità, **Crea o cambia tipi di flag…** crea un tipo con un nome: spunta le flag del gioco che accende e spegne. Dallo a qualsiasi unità; toglilo e le sue flag tornano com'erano. Cambia un tipo e cambia ogni unità che lo ha. Il gioco agisce solo sulle sue flag, quindi un tipo combina ciò che già fanno. Non ancora provato in gioco.
- **La velocità del colpo spiegata bene:** la guida ai numeri diceva che la velocità di un colpo, la resistenza, l'interruttore «senza fisica» e il tempo prima che parta erano solo aspetto. Decidono quando arriva il colpo: un colpo più lento colpisce più tardi, e un bersaglio in movimento è mirato in anticipo del tempo di volo (dal funzionamento del gioco; non ancora provato in un test).
- **Ogni errore in dieci lingue:** i 35 errori dello Studio arrivati con l'importazione dei modelli e la tavola degli edifici.
- **Crediti:** il README dice cosa fa ancora il motore di LittleGroove nel nostro, cosa è nostro, e che il nostro lettore di texture usa anche il codec di ProLution.
- **Ancora con bug, usale a tua discrezione:** le texture di Map Paint e tutte e due le mappe vuote (Terreno vuoto e Oceano vuoto).

**0.9.8.7:** Ripeti e seleziona ciò che è piazzato, piazzamento a Griglia / Riquadro / Percorso, mappe vuote più grandi, e ogni valore spiegato.

- **Corretto, segnalato da un modder:** su una nuova unità fatta da una di 17 unità del gioco (il Tigre reale, i cannoni atomici, la V2...), la casella per cambiarne il modello non compariva mai. Lo Studio ora trova quei modelli, e se non ne trova uno la casella lo dice invece di sparire.
- **La scheda IA spiegata:** ogni valore dei giocatori del computer dice cosa fa, in unità semplici, e quale vale in battaglia per ogni difficoltà e profilo; modalità, difficoltà, profili e unità scelti per nome.
- **Ogni valore spiegato, ovunque:** Tutti i valori, la scheda Unità, i pennelli della scheda Mappe (dimensione in metri, forza secondo ciò che fa) e la scheda Musica (quando suona ogni lista di battaglia).
- **La scheda Economia, Normale e Nucleare separate:** dove le due modalità differiscono, ognuna ha le sue caselle. Una modifica solo alla Nucleare non è ancora stata provata in gioco.
- **Ripeti e seleziona:** Ripeti in ogni strumento della mappa (Ctrl+Y o Ctrl+Maiusc+Z, e un pulsante); nei riquadri Edifici e Oggetti & alberi seleziona ciò che è piazzato (clic, Maiusc+clic o un riquadro), trascinalo, ruotalo, ridimensionalo o eliminalo, anche quelli della mappa.
- **Griglia, Riquadro e Percorso:** file di oggetti a griglia o a riquadro, edifici rivolti alle strade, e siepi, filari e fasce d'alberi lungo un percorso, con copertura.
- **Mappe vuote più grandi:** la finestra Dimensione mappa di una nuova mappa vuota aggiunge o toglie strisce di terreno su ogni lato, e Crea settori la riempie di settori.
- **Menu e sensazioni:** righe di numeri invece dei cursori, una ricerca con #tag e le ricerche recenti, schede a comparsa, e tasti da riassegnare (Scambia, Prendilo, Annulla).
- **Più sicuro:** chiudere con lavoro non salvato chiede prima; una mappa con nuovo terreno tagliato fuori è rifiutata prima di Prova in gioco; una mod fatta con uno Studio più vecchio viene aggiornata dopo un backup (Aggiorna questa mod); i risultati di build tenuti restano validi dopo un aggiornamento dello Studio.
- **Ogni messaggio in dieci lingue:** gli errori dello Studio e le righe della build.
- **Nuova unità** lascia fuori le due unità senza modello di partenza (il cannone SOLO da 57 mm e i paracadutisti SOLO).
- Non ancora provato in gioco: ciò che è piazzato con Griglia, Riquadro e Percorso, gli oggetti spostati e una mappa più grande fatta nello Studio.
- **Ancora con bug, usale a tua discrezione:** le texture di Map Paint e tutte e due le mappe vuote (Terreno vuoto e Oceano vuoto).

**0.9.8.6:** ogni flag e ogni numero delle unità spiegati, gli strumenti della mappa mostrano cosa hanno fatto, e le mappe vuote disegnate bene.

- **I flag delle unità spiegati:** ogni flag nella pagina di un'unità mostra il suo nome, e passandoci sopra si vede cosa fa, come usarlo e quanto ne siamo sicuri. **Guida ai flag: tutti spiegati** li elenca tutti e 105, con una ricerca. Lo Studio controlla i flag di un'unità: un crash noto (i flag di un camion su qualcosa che non è un camion, un aereo armato con il flag da ricognizione senza quello da caccia) mostra la sua correzione, e lo Studio non avvia il gioco finché non è corretto; i flag che dovrebbero rompere un'unità danno un avviso.
- **Ogni numero spiegato:** passa sopra il nome di qualsiasi numero di un'unità o di un edificio per vedere cosa significa; accanto, il suo valore in unità semplici (metri, km/h, secondi, gradi, $, %), un cursore per renderlo più piccolo o più grande del valore del gioco (il suo valore base, da -90% a +300%), e dove si colloca tra le unità del gioco del suo tipo. Le velocità sono nei km/h del gioco.
- **Come funzionano armi e munizioni**, passo per passo, nel riquadro Armi.
- **Gli strumenti della mappa mostrano cosa hanno fatto:** Copertura, Scopri, Città, Foresta, Blocca e Apri segnano il terreno su cui è passato ogni tratto e dicono quanti m² sono cambiati per le unità, o che non è cambiato nulla. Città lavora in metri veri e cerchia prima gli edifici che un clic coprirà.
- **Piazzare:** edifici, alberi e oggetti piazzati mostrano i loro veri modelli (con un punto ai loro piedi); quello scelto appare trasparente sotto il puntatore prima del clic; l'elenco da piazzare è una griglia di immagini. Gli alberi non sono più neri, e i numeri dei settori si nascondono quando la telecamera è vicina.
- **Mappe vuote** (visto in gioco su un Terreno vuoto): ombre sul terreno piatto; ciò che piazzi dove la mappa copiata aveva il mare viene disegnato; il pavimento della telecamera segue il nuovo terreno.
- **Ancora con bug, usale a tua discrezione:** le texture di Map Paint e tutte e due le mappe vuote (Terreno vuoto e Oceano vuoto).

**0.9.8.5:** aerei in qualsiasi ruolo, armi che colpiscono gli aerei e una libreria per il pennello Texture di Map Paint.

- **Il ruolo di un aereo** (segnalato da un giocatore: un cacciabombardiere a cui venivano date le bombe a tappeto di un bombardiere volava fino al bersaglio e non sganciava nulla): una nuova casella Ruolo nella pagina di un aereo lo rende Caccia, Cacciabombardiere, Bombardiere o Ricognitore. Il suo comportamento, il modo in cui lo usano i giocatori del computer e le sue parole nel menu di costruzione cambiano con esso. Le bombe di un bombardiere vanno in una stiva (copiata da quella di un bombardiere del gioco), l'unico modo in cui il passaggio di un bombardiere le sgancia. Visto in gioco: un cacciabombardiere reso bombardiere sgancia le sue bombe; un ricognitore che tiene le sue armi (uno Stuka, un ME109) attacca ancora e ha la vista dei ricognitori.
- **Veicoli da ricognizione:** la casella Ruolo di un veicolo terrestre lo rende da Ricognizione: la vista delle autoblindo da ricognizione (molto più lontano di quella di un carro), il modo in cui le usano i giocatori del computer, le loro parole nel menu di costruzione, e può entrare nei boschi (visto in gioco con un Panzer IV).
- **Cosa colpisce un'arma:** il Colpisce di ogni arma sceglie il terreno, gli aerei o entrambi (una seconda arma accanto, come i cannoni contraerei del gioco ne portano una per ciascuno). Visto in gioco: proiettili di carro sparati contro aerei. Noto: un'arma d'aereo impostata per colpire solo il terreno non fa ancora danni.
- **Il pennello Texture di Map Paint ha una libreria:** le texture del terreno del gioco (erba, campi, sabbia, neve, roccia, strade..., per teatro, con una ricerca), un quadrato del terreno di qualsiasi mappa, immagini tue e immagini gratuite online (Poly Haven e ambientCG, CC0; foto aeree degli Stati Uniti, pubblico dominio), un'immagine scaricata per clic e tenuta nella tua mod con il suo credito. Un cursore Dimensione, le texture usate di recente e **Dettaglio del gioco da vicino**, che posa le decal del gioco di una texture del gioco sul terreno che dipingi. Non ancora visto in gioco; i download online non ancora provati.
- **Gli oggetti messi in campo aperto**, lontano da città, fattorie e boschi della mappa, sono ora alla portata della visualizzazione del gioco, e i grandi gruppi di nuovi oggetti sono disposti come quelli del gioco (non ancora visto in gioco).
- **Ridipingere più in fretta:** il terreno dipinto viene tenuto da una build all'altra, qualunque copia o mod l'abbia dipinto: una mappa ridipinta allo stesso modo lo riprende in pochi secondi, non in minuti.
- **Ancora con bug, usale a tua discrezione:** le texture di Map Paint e tutte e due le mappe vuote (Terreno vuoto e Oceano vuoto).

**0.9.8.4:** missioni tue, mappe vuote da costruire e molto altro da personalizzare.

- **Ancora con bug, usale a tua discrezione:** le texture di Map Paint e tutte e due le mappe vuote (Terreno vuoto e Oceano vuoto).
- **Missioni tue:** una nuova Operazione o un nuovo capitolo di campagna ha la sua missione, nel lato Scenario della schermata della mappa: schieramenti, obiettivi, eventi (Quando → Fai: far arrivare unità, muovere, attaccare, tenere una zona, artiglieria, bombardamento, paracadutisti, messaggi, denaro, vittoria, sconfitta) e movimenti di camera. Visto in gioco: il suo movimento di camera, gli obiettivi (una zona, un gruppo distrutto, un tempo), eventi che si ripetono, il denaro, uno schieramento dato al computer. Non ancora provato: i paracadutisti, un movimento di camera avviato da un evento.
- **Mappa | Scenario** nella schermata della mappa: ciò che sta dall'altro lato appare sbiadito e non si può afferrare per sbaglio.
- **Mappe vuote:** della mappa copiata non si vede più niente, e sei tu a mettere il QG di ogni giocatore (la build aspetta che siano tutti messi). Terreno vuoto funziona anche per Operazioni e capitoli di campagna.
- **Settori tuoi:** dipingili, trascina i loro angoli, disegnane uno nuovo come riquadro, lascia terreno senza settore, eliminane uno (visto in gioco).
- **Depositi di rifornimento:** la scheda Economia dà più camion a ogni deposito di ogni mappa, o di una mappa (per tot volte, o un numero ciascuno); niente più tetto di 1.000 camion.
- **Scheda Nazioni:** nascondi in un colpo tutte le unità di una nazione, mostrale di nuovo, o riempi i suoi menu con le unità di un'epoca.
- **Modifica una mod installata:** apri qualsiasi mod del Launcher; quella di un altro diventa una tua copia con un nome tutto suo. Le mod di RUSE Mod Manager (.rmod) vengono convertite così che i loro valori si possano cambiare.
- **Il controllo della mod in parole semplici**, con un pulsante per correggere ogni problema.
- **Un aspetto tutto suo per un'unità:** una sua copia del modello da ridipingere; le squadre indossano l'uniforme predefinita o una personalizzata; scegli il camion su cui viaggia una squadra o un cannone. La fanteria si vede in 3D e si apre in Blender.
- **La corazza** si sceglie tra i livelli del gioco, così la scheda mostra con cosa combatte l'unità; **gli aerei importati** tengono le eliche che girano e tornano rivolti in avanti (entrambi visti in gioco).
- **Dimensioni dei modelli su un cursore** (Minuscolo, Misura del gioco, Misura reale, Enorme: da 0,05 a 20), da cambiare quando vuoi, tutti gli aerei in un colpo.
- **Altro da cambiare:** un valore proprio di una difficoltà o di un profilo dell'IA per uno che solo Predefinito elenca; numeri oltre i cursori degli strumenti della mappa; ritocchi musicali più forti e più lunghi.
- **Corretto:** un'unità mostrata in un menu ma ricercata da una nascosta fermava il gioco: il controllo la nomina e la build la rifiuta. I carri sparano di nuovo attraverso le città cancellate, e le unità non cadono più nei buchi dove i ponti sono stati tolti (visto in gioco).
- **I download funzionano su ogni PC:** quando Windows non ha ancora preso il certificato con cui si verifica GitHub, lo Studio glielo chiede, come fa un browser, e riprova (non ancora provato su un PC che aveva il problema).

**0.9.8.3:** le copie con le mod vanno dove dici tu.

- **Dove vanno le copie con le mod**, nelle Impostazioni: scegli la cartella in cui viene costruita la copia del gioco
  con le mod, o torna al posto consigliato, `RUSE-Instances` sull'unità del gioco (lì la copia condivide i file del
  gioco ed è pronta in pochi secondi; su un'altra unità è una copia completa del gioco, più lenta e più grande). Il
  backup pulito del gioco va accanto. Il prossimo Prova in gioco costruisce nel nuovo posto; la vecchia cartella si
  può eliminare a mano. Il Launcher usa la stessa cartella.

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
- **Togliere un'unità da cui altre sono ricercate:** scegli in **Impostazioni > Ricerca** se essere avvisato prima
  (predefinito), rifiutare, o ricollegarle al suo stesso genitore; un'unità che punta a un'unità tolta lo mostra
  nella sua pagina e nel controllo. I tempi di ricerca si scrivono in secondi o minuti (che il gioco li conti in
  secondi non è ancora provato in gioco).
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

**0.9.6:** una nuova unità può avere un modello 3D tutto suo, da qualsiasi programma 3D, e **Prova in gioco** parte subito quando non è cambiato nulla. E una prima volta:

- **Il primo modello di un altro programma 3D in R.U.S.E.:** un M1 Abrams, diventato una nuova unità USA accanto allo Sherman. Si compra alla Armor Base con una sua carta, viene costruito e gira la torretta come i carri del gioco. Visto in gioco.

| Prima | Ora |
|---|---|
| Una nuova unità aveva il modello dell'unità che copia. | **Importa modello…** nella pagina di una nuova unità: scegli un **.3ds** (con le sue immagini accanto, o nella cartella sopra) o un **.glb** (da Blender e dalla maggior parte dei programmi 3D). Lo Studio lo adatta all'unità che copia: la sua lunghezza (per **Dimensione**: 1 è lungo uguale, un Abrams rispetto a uno Sherman è 1,36), la sua torretta sulla torretta di quell'unità così che il gioco la giri allo stesso modo, le sue immagini come texture tutte sue. La pagina lo mostra in 3D; **Usa il modello dell'unità copiata** lo toglie di nuovo. Va nella tua mod come `files/models/<the unit's name>.glb`, che si apre in Blender. **Visto in gioco.** Ancora agli inizi: cingoli e ruote non girano ancora, la vampa del cannone compare dove sta la bocca dell'unità copiata, e il relitto è quello dell'unità copiata. |
| Una nuova unità con una sua carta faceva crashare il gioco quando veniva costruita (0.9.5). | La sua carta sta anche dove il gioco la legge sulla mappa. **Visto in gioco.** |
| Una mappa fatta con **Duplica mappa** non si poteva eliminare nello Studio. | **Elimina mappa**, sotto Duplica mappa su una nuova mappa: chiede una volta, poi la sua cartella va nel Cestino, da dove puoi riprenderla. Le mappe del gioco stesso non si possono eliminare. |
| Lo Studio diceva che Blender non era installato se era stato estratto da uno zip invece che installato. | Trova Blender ovunque tu l'abbia estratto (la cartella principale di un'unità o una sotto, Download, Desktop, Documenti). |
| Le ridipinture uscivano con alcuni colori un po' sbagliati (una zona rossa e blu poteva diventare viola). | Ogni zona di 4 x 4 tiene i suoi colori. Le unità ridipinte e il terreno dipinto escono con dati d'immagine leggermente diversi rispetto alla 0.9.5 (lo stesso aspetto), quindi l'impronta e il codice per unirsi alla partita di una mod così cambiano: tutti i giocatori dovrebbero aggiornare prima di giocare insieme. |
| **Prova in gioco** ricostruiva ogni volta tutta la copia moddata, anche se non era cambiato nulla. | Non è cambiato nulla dall'ultima build: il gioco parte subito, senza build (una mod di prova: da 21-29 s a meno di 0,1 s). Una build riusa i file invariati dell'ultima copia invece di copiarli di nuovo. |
| Ogni build rileggeva da capo i dati delle unità del gioco. | Vengono tenuti tra una build e l'altra: una grande mod di prova richiedeva 213 s ogni volta; ora la prima build richiede circa lo stesso tempo, e le successive 68 s. Il gioco non copia più tutti i suoi dati prima di una build. |
| Cancellare la maggior parte di una grande mappa esauriva la memoria dello Studio, e una cancellazione di tutta la mappa veniva rifiutata perché troppo grande. | Le cancellazioni si contano in pochi secondi, una alla volta; **Cancella tutta la mappa** nel riquadro Rimuovi (Annulla la riprende). Lo scenario cancellato viene scritto in modo compatto. Nuovo: non ancora visto in gioco su larga scala. |
| Il terreno spianato sotto una strada lasciava la strada della vista da lontano alla vecchia altezza. | Il modello della strada segue il nuovo terreno. Nuovo: non ancora visto in gioco. |
| Il letto di un fiume spianato teneva da vicino le sue immagini di roccia e di gola. | Viene riempito da entrambe le sponde e la sua copertura bassa viene tolta. Nuovo: non ancora visto fatto dalla build in gioco. |
| Mentre si costruiva l'indice del gioco (circa un minuto), lo Studio poteva solo aspettare. | Mappe e Impostazioni restano utilizzabili; la riga in basso dice quando è pronto. |
| Un avvio lento non lasciava alcun indizio. | I passi di ogni avvio vengono cronometrati; **Copia il rapporto** in Risoluzione problemi elenca gli ultimi cinque. |
| La pagina della finestra poteva arrivare a parti dell'app oltre alle sue chiamate. | Arriva solo alle chiamate dell'app stessa. |

Inoltre `ruse import-model <file> --like <model> --unit <name>` fa lo stesso dalla riga di comando.

**0.9.5:** le unità ricevono un aspetto tutto loro. Guarda qualsiasi unità in 3D, ridipingila in Blender, dalle una tua carta nel menu di costruzione. E le nostre prime volte, tutte viste in gioco:

- **La prima unità ridipinta da una mod:** uno Sherman rosso, da vicino e da lontano.
- **La prima unità dipinta in Blender** e riportata nel gioco.
- **La prima carta del menu di costruzione fatta nello Studio,** mostrata nel menu della Armor Base del gioco stesso.
- **La prima nuova unità con un modello tutto suo,** accanto a quelle del gioco: il Tall Sherman, vicino allo Sherman (fatto durante i test; fare i propri modelli nello Studio è il prossimo passo).
- **La prima missione tutta nostra** giocata fino alla vittoria: una nuova Operazione con obiettivi, unità e un attacco d'artiglieria propri (fatta durante i test).

| Prima | Ora |
|---|---|
| La pagina di un'unità mostrava solo i suoi valori. | **Modello 3D** nella pagina dell'unità: giralo, ingrandiscilo, guarda la pittura della tua mod sopra. |
| L'aspetto di un'unità era quello del gioco. | **Ridipingere in Blender:** **Apri in Blender** apre i modelli dell'unità con le loro immagini; dipingi sul modello, poi **Riporta** salva la tua pittura e la mette nella tua mod. **Visto in gioco**, da vicino e da lontano. Blender è gratuito: se lo Studio non lo trova, **Scarica Blender (gratis)** e **Scegli Blender…** sono proprio lì. |
| L'immagine di un'unità nel menu di costruzione era quella del gioco. | **Usa questa vista come scheda:** gira e ingrandisci il modello 3D finché sta bene nella cornice tratteggiata; quella vista diventa la carta dell'unità nel menu di costruzione. **Visto in gioco.** |
| Una nuova unità mostrava la stessa carta dell'unità che copia, così le due sembravano uguali nel menu. | La carta di una nuova unità è solo sua (`files/cards/<the unit's name>.png`): fare la sua carta non cambia mai quella dell'originale. Non ancora visto in gioco. |
| Un pacchetto di modelli delle unità diventato più grande veniva scartato dal gioco, con tutti i suoi modelli mancanti: un crash alla prima fabbrica. | I pacchetti di modelli vengono scritti nel modo in cui il gioco li controlla, qualunque sia la loro dimensione. **Visto in gioco:** un secondo Sherman con un modello tutto suo. |
| Le unità di una nazione date a un altro esercito non avevano un modello nei capitoli di campagna e nelle Operazioni: una mod che faceva comparire unità francesi su Holland crashava durante il caricamento. | Anche lì i loro modelli si caricano. **Visto in gioco** (unità francesi su Colditz). |
| **Duplica mappa** faceva solo mappe di BATTAGLIE. | Fa anche una nuova **Operazione** o un nuovo **Capitolo della campagna** dalla voce di qualsiasi mappa. **Visto in gioco:** una nuova Operazione. Ancora agli inizi: un nuovo capitolo di campagna non è ancora stato provato. |
| Spianare le montagne al bordo di una mappa lasciava lì un dirupo. | Il bordo della mappa segue il terreno. **Visto in gioco** (Blitz Twin, piatta fino al bordo). |
| Le unità giravano intorno ai posti dove stavano gli edifici cittadini cancellati. | Il terreno si apre a ogni unità dove spariscono gli edifici, come per gli alberi. **Visto in gioco.** |
| Non c'era modo di dipingere il terreno della mappa. | **Map Paint:** dipingi l'immagine del terreno con un colore (la ruota, i colori della mappa stessa o il contagocce) o con il terreno della mappa stessa copiato da un altro punto. **Sgombra il terreno sotto** (attivo di default) toglie erba, colture e sassi sotto la pittura così che si veda a ogni altezza. Ancora agli inizi: visto in gioco dall'alto. |

**0.9.4:** nuove mappe, ancora agli inizi. **Duplica mappa** fa una nuova mappa da qualsiasi mappa di BATTAGLIE, e le mappe si aprono in un secondo.

| Prima | Ora |
|---|---|
| Le modifiche alle mappe potevano cambiare solo le mappe del gioco stesso. | **Duplica mappa** (scheda Mappe, sotto il nome della mappa aperta) fa una **nuova mappa**: una copia completa con un nome tutto suo, elencata in BATTAGLIE accanto all'originale, che poi cambi come qualsiasi mappa. La finestra dice cosa fa e come funziona. **Visto in gioco:** una nuova mappa si gioca sul suo terreno, e 101 nuove mappe insieme sono state tutte elencate e giocate. Ancora agli inizi: le copie di mappe diverse da Blitz si costruiscono ma non sono ancora state provate in gioco, e spianare le montagne al bordo di una mappa lascia lì un dirupo. Segnala ciò che trovi. |
| Una mappa impiegava secondi per aprirsi, ogni volta (M03_Italie: 7,6 s). | I suoi dati vengono tenuti tra una visita e l'altra e tra un avvio e l'altro: 1,7 s la seconda volta. |
| «Mod» e «Mappa» erano due menu simili. | **Mod delle unità** (con un carro) e **Modifiche alle mappe** (con una mappa). |
| Schieramenti e zone si confondevano facilmente. | **A chi va?** dice che uno schieramento è chi controlla le unità (un paese può averne diversi), e passando sopra una zona si legge che è un'area della mappa, non uno schieramento. |
| Gli aggiornamenti arrivavano solo come versioni intere. | Piccole correzioni possono arrivare tra una versione e l'altra (0.9.4.1), proposte come qualsiasi aggiornamento. |

**0.9.3:** tutto ciò che piazzi si vede da lontano, le nuove strade attraverso i boschi sembrano quelle della mappa stessa, alberi che puoi tenere su una strada, oggetti e alberi con i loro nomi nella tua lingua, e build circa tre volte più veloci.

| Prima | Ora |
|---|---|
| Oggetti, alberi ed edifici da piazzare erano elencati con nomi in codice francesi: Caillou_10, ChampsPierres_02, Osier... | Con nomi nella lingua dello Studio, in tutte e dieci, con il tipo di cosa che è ognuno: «Campo sassoso 2», «Champ de pierres 2», «Steiniges Feld 2». Cambiano con il pulsante della lingua. Il nome in codice e la sua cartella sono nel suggerimento. |
| Le rocce e la maggior parte degli altri oggetti che piazzavi sparivano appena la telecamera si allontanava, e comparivano e sparivano mentre la giravi. | Tutto ciò che una mod piazza viene disegnato fino alla distanza massima, e gli oggetti della mappa stessa non cambiano. **Visto in gioco:** le rocce piazzate si vedono a ogni altezza. |
| Dall'alto una nuova strada attraverso un bosco era una striscia chiara, e dopo una prima correzione spariva dalla media-lunga distanza. | Dipinta attraverso i boschi come le strade della mappa stessa, a ogni altezza. **Visto in gioco.** |
| Una nuova strada toglieva sempre gli alberi dal suo percorso, circa 6 m per lato. | **Mantieni gli alberi sulle nuove strade** nel riquadro Strade: alberi e cespugli restano sopra la strada, e in un bosco la strada si vede più tenue e più grigia. **Visto in gioco.** |
| **Prova in gioco** impiegava circa 5 minuti per costruire una mod con nuove strade su M03_Italie. | Circa 1½ minuti: l'aspetto delle strade di una mappa viene misurato una volta e tenuto, e le copie saltano un controllo lento che non serve loro. |

**0.9.2:** correzioni dalla mappa di campagna di un tester: ponti per le nuove strade su ogni mappa, estremità delle strade che si agganciano ai ponti (o per niente), i nomi che un giocatore conosce, unità per il giocatore, elementi del paesaggio che si vedono da lontano, e le zone dello scenario come confini sul terreno.

| Prima | Ora |
|---|---|
| Una strada sull'acqua fermava la build su 20 delle 29 mappe con ponti (Italia, Germania, Olanda...): il suo ponte «non avrebbe avuto un piano». | Riceve il suo ponte e il suo piano su ogni mappa con ponti. Non ancora visto in gioco su quelle mappe. |
| Ogni punto di una strada si agganciava alla strada più vicina, finendo su una strada anche dove avevi messo un ponte. | Si agganciano solo le due estremità di una strada, prima all'estremità di un ponte piazzato. **Aggancia le estremità a strade e ponti** nel riquadro Strade lo disattiva. |
| Edifici e unità con i loro nomi in codice, come «Descriptor_Building_VehiculeFactoryLeurre». | Con i nomi che dà loro il gioco (DECOY ARMOR BASE), con la riga del gioco stesso su cosa fa ognuno. |
| Non c'era modo di dare unità al giocatore in un capitolo di campagna: lo schieramento del giocatore (0) veniva rifiutato. | **A chi va?** elenca gli schieramenti dello scenario stesso, presi dalla sua missione: «Giocatore · USA (schieramento 0)», «Computer · Germania (schieramento 1)»... |
| Su M03_Italie e altre mappe, una nuova strada in campo aperto nascondeva da lontano lo scenario della mappa, e gli oggetti che piazzavi si vedevano solo da vicino. | La vista da lontano della mappa resta com'era, e gli oggetti piazzati si vedono da lontano come quelli della mappa stessa. Non ancora visto in gioco. |
| Le zone dello scenario erano fogli colorati sospesi sopra la mappa, che ne coprivano il terreno e le icone. | Ogni zona è una linea netta lungo il suo confine sul terreno con una tinta trasparente all'interno, come i confini di Stellaris. **Riempimento delle zone** imposta l'interno (0 %: solo i confini). |

**0.9.1:** trascina qualsiasi cosa sulla mappa, icone più chiare che puoi ridimensionare e nascondere, la tua lingua dal primo avvio, e il tipo di ogni unità come lo chiama il gioco.

| Prima | Ora |
|---|---|
| Punti di partenza, depositi di rifornimento e unità iniziali si spostavano solo con lo strumento Sposta, un clic e poi un altro. | Afferrane uno qualsiasi sulla mappa e trascinalo, senza nessuno strumento scelto, come già si ruotavano le telecamere iniziali. Depositi e QG restano agganciati alle strade mentre trascini. |
| Le icone della mappa erano omini stilizzati e scatole, e ogni bunker sembrava uguale. | Un'icona per ogni tipo: un soldato, un carro, un camion per i depositi di rifornimento, un aereo, cannoni, un QG ben segnato, la Armor Base e l'aeroporto distinti, e ogni bunker con la sua (anticarro, mitragliatrice, contraerea, artiglieria, forte, posto di osservazione). |
| Le icone erano ingombranti dall'alto, e l'unico modo per nasconderle era nascondere tutto lo scenario. | Le icone si rimpiccioliscono mentre la telecamera si allontana, un cursore ne imposta la dimensione, e il riquadro Scenario mostra o nasconde ogni tipo (partenze, telecamere, depositi, edifici, unità, zone, città). Tenuto per la volta successiva. |
| Lo Studio partiva con i nomi in codice, e la lingua stava nelle Impostazioni, così i giocatori non sapevano che parla la loro lingua. | Il primo avvio chiede: «Scegli la tua lingua», ogni lingua scritta con le sue parole, con segnata quella impostata per il tuo gioco in Steam. Poi un pulsante della lingua in alto, sempre in vista. |
| Le unità erano solo «Terra» o «Aria». | Sotto Terra, Fanteria e Aria, i tipi del gioco stesso: Carro leggero, medio e pesante, Cacciacarri, Autoblindo da ricognizione, Caccia, Cacciabombardiere, Bombardiere leggero, medio e pesante, Ricognitore... anche sulla riga di ogni unità, nella tua lingua. La ricerca li trova («bombardiere», «ricognizione»). |
| L'elenco delle app installate di Windows mostrava la prima versione mai installata. | Mostra la versione che hai. |

**0.9.0:** le strade hanno l'aspetto giusto. Una strada che disegni ora sembra le strade della mappa stessa, dall'alto e fin giù al suolo. Arrivarci ha richiesto molto tempo e molti test, più dei ponti. Provato in gioco su D-Day.

![Una nuova strada da vicino su D-Day: asfalto con una linea di mezzeria tratteggiata e banchine di ghiaia che sfumano nell'erba](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Prima | Ora |
|---|---|
| Una nuova strada spariva quando la telecamera scendeva verso di lei: si vedeva solo la sua pittura, dall'alto. | Da vicino è disegnata con le decal d'asfalto della mappa stessa, posate lungo di essa come le posa la mappa, con una decal di bordo per lato: asfalto, una linea di mezzeria tratteggiata, banchine di ghiaia. |
| La pittura era un solo colore piatto, più chiaro e più largo delle strade della mappa. | La pittura viene misurata sulle strade della mappa stessa: il loro colore, le loro banchine e come sfumano nel terreno. Ogni mappa ha la sua. |
| Erba, cespugli e alberi della fattoria crescevano attraverso una nuova strada. | Le piante e gli oggetti della mappa sul percorso della strada vengono tolti (circa 6 m per lato). I boschi tengono copertura e movimento, e gli edifici restano. |
| Si conoscevano solo le decal stradali di D-Day. | Sulle mappe del deserto si usano le loro decal, posate allo stesso modo (non ancora visto in gioco). |
| Una grande cancellazione (migliaia di cerchi) richiedeva molti minuti di build. | Molto più veloce: si guardano solo i cerchi vicini a ogni parte della mappa. |

![Tre nuove strade che partono dalla strada principale di D-Day](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-6-done-overview.jpg)

**0.8.3:** gli strumenti di scenario dell'editor di mappa dal RUSE-Mod-Manager di LittleGroove: depositi di rifornimento e QG agganciati alle strade, un'icona per ogni edificio e unità, e la telecamera iniziale di ogni giocatore mostrata, portata con sé e ruotata. Non ancora provato in gioco.

| Prima | Ora |
|---|---|
| Non si poteva piazzare un punto per un deposito di rifornimento. | **Punto per deposito di rifornimenti** è il primo sotto Aggiungi unità → Edifici → Denaro. |
| Un punto di partenza andava esattamente dove cliccavi, sulla strada o lontano da essa. | **Aggancia alle strade** (attivo di default) lo mette accanto alla strada più vicina, alla stessa distanza che usano le mappe del gioco stesso (l'ha misurata LittleGroove). Togli la spunta per piazzarlo in mezzo a un campo. |
| Le unità iniziali erano poche icone, con lettere per il paese. | Un'icona per ciò che è ognuna (QG, deposito di rifornimento, fabbrica, forte, esca, soldato, carro, anticarro, artiglieria, prototipo, aereo, torretta) e la coccarda del paese. |
| Non potevi vedere dove si apre la partita di un giocatore. | Ogni punto di partenza mostra la sua telecamera iniziale: il volo d'arrivo (tratteggiato), dove si ferma, cosa guarda, e la parte della mappa che mostra lo schermo. |
| La telecamera iniziale di un punto di partenza spostato restava al vecchio posto. | La telecamera si sposta con lui; un nuovo punto di partenza riceve una telecamera tutta sua. |
| La telecamera iniziale non si poteva cambiare. | Con **Sposta**, trascina la telecamera di una partenza intorno al suo QG per aprire la partita da un altro lato; **Telecamera com'era** lo annulla. |
| Un punto di partenza in un bosco veniva rifiutato. | Permesso: lì un QG funziona, e i camion di rifornimento attraversano i boschi. Vengono rifiutati solo acqua, dirupi e terreno bloccato. |

**0.8.2:** un test fermato da un errore nella tua mod ti dice quale e lo corregge, mod e mappe separate, colori della mappa e unità iniziali più chiari, e una sola copia del gioco per tutto il PC.

| Prima | Ora |
|---|---|
| Un test fermato da un errore nella tua mod seppelliva il motivo nel log e rimandava a Risoluzione problemi, che non può correggere una mod. | Ogni errore è elencato sopra il log con un pulsante che lo corregge: un'unità iniziale di squadra su una mappa di BATTAGLIE resa neutrale o tolta (anche tutte insieme), una strada che non si collega a niente tolta. Risoluzione problemi compare solo per gli altri errori. |
| Il messaggio in basso non si poteva chiudere. | Ogni messaggio ha una × per chiuderlo. |
| Il log del test non si poteva copiare. | **Copia il rapporto** copia il log e il messaggio, per una segnalazione di bug o per Discord. |
| Mod e mappe condividevano un solo menu. | Mod e mappe hanno ognuna il suo menu, ed Esporta mette il file direttamente nella libreria del Launcher. |
| Ogni unità iniziale sulla mappa sembrava uguale. | Ogni unità iniziale è un'icona di edificio, carro, soldato o aereo nel colore del suo schieramento, con il suo paese. |
| I colori della mappa non erano spiegati. | Una legenda dei colori per la copertura, per dove vanno le unità e per Rimuovi; la copertura dello strumento Città ha un suo colore; un cursore di trasparenza per ogni strato. |
| Colline e alberi spuntavano attraverso le zone di uno scenario. | Le zone fluttuano sopra il terreno, e un cursore **Altezza delle zone** imposta quanto in alto. |
| Ogni test teneva la sua copia del gioco. | Una sola copia moddata per tutto il PC, condivisa con il Launcher. |
| La versione non si vedeva, e Novità era un elenco. | La versione è accanto al nome, e Novità apre una tabella prima/dopo come questa. |
| Pochi suggerimenti. | Suggerimenti sui comandi principali, scritti per giocatori nuovi al modding. |
| Le nuove strade su Twilight of the Gods, Alpha, Ostfriesland e Robert non avevano il modello stradale della mappa. | Ora lo ricevono anche loro. |
| La build diceva che le nuove strade erano «disegnate da vicino». | Dice che si vedono da lontano; da vicino non si vedono ancora (resta un problema noto). |

**0.8.1:** unità di qualsiasi nazione, un nuovo aspetto, una barra degli strumenti più corta, e lo strumento Rimuovi.
- **Le unità di un'altra nazione funzionano.** Una nuova unità può andare nel menu di costruzione di qualsiasi nazione, qualunque sia l'esercito da cui viene il suo modello: un Tiger o uno Ju 87 tedesco per gli USA, anche uno Zero o un Chi-Ha giapponese. Viene costruita, combatte, mostra la sua immagine sulla sua carta e sul suo segnalino, e si può selezionare a terra e in aria, anche in una partita in cui nessuno gioca la nazione da cui viene (provato in gioco, 2026-10-02). La build fa caricare i modelli di quella nazione in ogni partita; una partita richiede un po' più di memoria e di tempo di caricamento.
- **Un nuovo aspetto:** i blu di R.U.S.E. al posto del nero e oro, e un nuovo logo: il tavolo della sala di guerra.
- **La barra degli strumenti dell'editor di mappa è più corta.** Gli strumenti che vanno insieme condividono una tessera, con una scheda per ciascuno: Terreno e acqua, Copertura e movimento, Strade e ponti, Edifici, Oggetti e alberi, poi Rimuovi, Scenario e Verifica. Una tessera si apre sulla scheda usata per ultima.
- **Strumento Rimuovi:** trascina sopra gli alberi e gli oggetti della mappa stessa (anche gli edifici, se li scegli) e spariscono quando la mod viene costruita. I cerchi rossi vengono salvati nella mod, ciò che coprono è tinto di rosso, e il riquadro conta cosa toglieranno. Dove spariscono gli alberi, il terreno si apre a ogni unità e perde la copertura del bosco. Cancellare bene edifici, strade, arbusti e rocce della mappa stessa è il prossimo passo.
- **Il programma di installazione propone un backup pulito del gioco** accanto al collegamento sul desktop, e dice perché: con esso, la risoluzione dei problemi può rimettere a posto tutto ciò che un altro gestore di mod ha cambiato.

**0.8.0:** l'editor di mappa cresce: nuovi pennelli e pannelli, ponti che le unità attraversano davvero, boschi che puoi sgombrare, e una build che controlla le regole del gioco così che ciò che fai funzioni al primo colpo. In più una risoluzione dei problemi e un backup pulito del gioco.
- **Novità nell'editor di mappa:**
  - **Pennelli Apri** (Movimento): il contrario di Blocca. Dai alle unità il terreno da cui la mappa le tiene lontane (tutte le unità, fanteria o veicoli). Aprire l'acqua è permesso, con un avviso: lì le unità stanno sul fondo del fiume.
  - **Pennello Foresta** (Copertura): alberi e copertura in un tratto solo; Annulla toglie entrambi.
  - **Pannello Ponti:** i tipi di ponte della mappa stessa, e un ponte piazzato a mano con la lunghezza e la rotazione che scegli; gli attraversamenti d'acqua delle nuove strade disegnati in oro.
  - **Verifica questa mappa:** elenca cosa andrebbe storto prima del test (terreno tagliato fuori, strade o ponti che le unità non possono usare, estremità di strade non collegate, edifici sulle strade), e cliccando su uno si vede dove.
  - I letti dei fiumi prosciugati o rialzati all'asciutto vengono aperti alle unità dalla build.
- **Togli gli alberi e gli oggetti della mappa stessa:** cerchi `[[erase]]` nel `scenery.toml` di una mod (scritti a mano per ora; uno strumento Rimuovi nello Studio è in arrivo). I carri entrano in un bosco sgombrato, e la fanteria lì non è più nascosta.
- **Gli oggetti piazzati poggiano sul terreno a qualsiasi dimensione.** Un edificio ingrandito 10× fluttuava nell'aria; ora poggia sul terreno come quelli della mappa.
- **Corretto: la copertura sulle mappe che non sono quadrate** (D-Day, Frontline, Djebel, Medjez, Handshake over the Elbe, e le mappe di campagna di Tunisia, Holland e Ardennes). La copertura dipinta o tolta lì (i pennelli Copertura, Scopri, Città e Foresta, `cover.toml`) finiva fino a un chilometro da dove era stata disegnata, e anche la vista mappa la mostrava in quel posto sbagliato. Ora sono giuste entrambe: se hai dipinto copertura su una di queste mappe, ricontrollala nella vista mappa. Le mappe quadrate (Blitz e la maggior parte delle altre) erano sempre giuste.
- **I ponti funzionano in gioco.** Una strada che disegni sull'acqua riceve il tipo di ponte della mappa stessa (anche quello delle mappe olandesi), e carri, fanteria e camion di rifornimento lo attraversano sopra l'impalcato, la fanteria all'altezza dell'impalcato. Le estremità dei ponti si collegano alle strade che le unità usano già e stanno lontane dagli edifici della mappa; un ponte che non si può collegare resta chiuso, e la nota della build dice cosa ha incontrato la strada e dove.
- **La build controlla le regole del gioco.** Ogni file che una mod cambia è stato confrontato con ciò che il gioco ne fa, e una mod che si romperebbe in gioco viene rifiutata con una nota che dice perché, prima che venga scritto qualsiasi cosa:
  - strade: ora le unità seguono le nuove strade, non solo i camion di rifornimento, e una nuova strada che non si collega a nessun'altra strada viene rifiutata (la rete stradale deve restare in un pezzo solo);
  - edifici e blocchi piazzati: le unità non possono più attraversarli; nuovi edifici, ponti e alberi si vedono a ogni distanza;
  - terreno: la nuova acqua è chiusa alle unità, la mappa dell'IA segue i tuoi boschi, blocchi, ponti e acqua, e un tratto che non può cambiare il terreno (o che raggiunge il piano di un ponte) lo dice;
  - unità: una salva, un ID, una nazione o un elenco di menu sbagliati vengono rifiutati, i flag delle unità vengono controllati, e ogni flag è spiegato nel selettore dei flag (i flag 62 e 63, che fanno crashare il gioco su un'unità che non è un camion, sono un errore); un'unità messa nella fabbrica di un'altra nazione viene rifiutata per ora (faceva crashare il gioco quando veniva costruita; farla funzionare è il prossimo passo);
  - scenario: le unità iniziali sono neutrali di default, un'unità iniziale i cui modelli la partita potrebbe non caricare viene rifiutata (faceva crashare il gioco all'avvio), una partenza dove i veicoli non possono andare viene rifiutata, una partenza spostata si porta dietro la sua telecamera, e i posti vengono contati per squadra.
- **Il rapporto della build** mostra ogni avviso (alcuni andavano persi), e una ricostruzione toglie prima la vecchia copia di prova, così una copia vecchia non si può avviare per sbaglio.
- **Copertura quadrata:** `square = true` su una pittura di `cover.toml`, o su un tratto Copertura o Scopri in `terrain.toml`, dipinge un quadrato lungo gli assi della mappa (scritto a mano per ora; la vista mappa lo disegna come un quadrato).
- **Risoluzione problemi** (accanto a *Prova in gioco*, e in Impostazioni > Aiuto): controlla in un colpo solo cosa può fermare un test (il gioco trovato, Steam, un gioco lasciato in esecuzione da una copia moddata, l'unità e il suo spazio libero, copie rimaste, file di sola lettura, se l'app può scrivere dove vanno le copie), con un pulsante per ogni correzione che può fare, e un rapporto da incollare in una segnalazione di bug, senza il tuo nome utente di Windows.
- **Backup pulito del gioco** (Impostazioni): tieni una copia pulita dei file del tuo gioco, controllali rispetto a essa, e rimetti a posto tutto ciò che un altro gestore di mod o una modifica a mano ha cambiato. I file che non sono del gioco vengono messi da parte, mai eliminati. Oppure lascia che Steam ripari il gioco (*Verifica con Steam*). È l'unico posto in cui lo Studio scrive nella cartella del tuo gioco, e solo quando lo chiedi tu.
- **Condividi la tua mod:** hai fatto una mod? Dopo l'esportazione, lo Studio mostra la sua dimensione e il suo SHA-256, e come aggiungerla all'elenco delle mod su GitHub e diventare un contributore.
- **Problema noto: le nuove strade non sono ancora disegnate da vicino.** Sono dipinte sul terreno e si vedono da lontano, e le unità le usano, ma con la telecamera vicina al terreno una nuova strada sparisce. Ci stiamo lavorando.

**0.7.6:** un secondo Prova in gioco funziona, e ponti che le unità possono sempre raggiungere.
- **Corretto:** ogni secondo *Prova in gioco* poteva fallire con «An old modded copy ... can't be removed ... (Access is denied)». Una copia che Windows non vuole eliminare (un file che una versione più vecchia aveva collegato a un file del gioco sostituito, un programma che lo tiene ancora aperto) non ferma più un test: viene messa da parte in `RUSE-Instances\.trash` ed eliminata quando niente la tiene più. Se R.U.S.E. è ancora in esecuzione dalla copia di prova, ti viene detto, con il nome del programma. Premere due volte *Prova in gioco* avvia un test, non due.
- **Corretto:** il nuovo ponte di una strada poteva far crashare il gioco quando le unità ricevevano l'ordine di salirci: il suo impalcato non raggiungeva nessun terreno usato dalle unità. Ora ogni estremità di un ponte si collega al terreno lungo la strada (fino a 62 m di accesso); un ponte che non si può collegare resta chiuso alle unità, con una nota, e la build non scrive mai terreno che le unità di terra non possono raggiungere.

**0.7.4:** Prova in gioco funziona quando i file del tuo gioco sono segnati come di sola lettura.
- **Corretto:** *Prova in gioco* falliva ogni volta con «[WinError 5] Access is denied» quando i file di R.U.S.E. sono segnati come di sola lettura (un'installazione da disco, un backup ripristinato): la copia di prova teneva il segno, così una copia lasciata costruita a metà non si poteva mai eliminare. Ora la copia di prova non tiene mai il segno, e un residuo di una versione più vecchia viene eliminato da solo (i file del tuo gioco restano esattamente com'erano). Se il gioco è ancora in esecuzione dalla copia di prova, ti viene detto di chiuderlo invece di ricevere un errore di Windows.
- **Una strada mostra la sua lunghezza** mentre la disegni, accanto al puntatore (stile Cities: Skylines); gli strumenti Strade mostrano il totale delle tue nuove strade.
- **Le nuove strade sono dipinte sul terreno** con il colore stradale della mappa stessa (dimostrato in gioco), e **una strada sull'acqua riceve un ponte**: il tipo della mappa stessa, un pezzo unico teso da sponda a sponda come i ponti del gioco stesso, così le unità possono attraversare. Una strada su uno dei ponti della mappa stessa riceve il nuovo ponte al suo posto. (I ponti sono nuovi: non ancora controllati in gioco.)

**0.7.3:** disponi la vista mappa a modo tuo. Il pannello della mappa (in alto a sinistra) e gli strumenti (in basso) si spostano ovunque con la loro maniglia (⠿) e si ripiegano con la freccia accanto: il pannello della mappa fino al suo titolo, gli strumenti fino alla loro barra. Doppio clic su una maniglia per rimettere quel pannello al suo posto. La tua disposizione viene tenuta.

**0.7.2:** strade, e test più chiari.
- **Disegna strade**, stile Cities: Skylines (il tipo Strade nella barra): **Dritta**, **Curva** e **Libera**. Un'estremità vicina a una strada si aggancia a essa e la collega. Le nuove strade si disegnano come nastri blu e **le rotte di rifornimento le usano** (dimostrato in gioco). Non sono ancora dipinte sul terreno.
- La casella **Strade** mostra in oro le strade della mappa stessa.
- Le parole del gioco stesso: uno scenario prende il nome dal pulsante del menu principale che lo avvia (**Battaglie**, Operazione, Campagna, letti dal testo del tuo gioco nella tua lingua), e una riga dorata sotto il menu degli scenari dice dove si gioca, per es. *In gioco: Battaglie › D-Day (6 giocatori)*.
- **Prova in gioco** dice dove ha costruito ed esattamente cosa aprire per vedere le tue modifiche (per es. *BATTAGLIE > D-Day*).
- Il tasto centrale del mouse ruota la vista anche nella modalità per guardarsi intorno (prima lì zoomava).

**0.7.1:** più unità alla volta, un controllo della mod, e aiuto a portata di mano.
- **Aggiungi unità** piazza 1, 2, 4, 6, 8 o 10 unità alla volta, in **linea, colonna, cuneo, riquadro o cerchio** rivolte verso l'alto dello schermo, con un cursore della spaziatura e anelli che mostrano dove starà ognuna.
- Il **controllo della mod**: ogni file della tua mod viene letto come lo legge la build del gioco, quando scegli la mod e prima di **Prova in gioco**. Una barra rossa nomina ogni problema; un file di mappa rotto si può **mettere da parte** (rinominato, mai perso), e una cartella di mappa chiamata come il titolo della mappa (maps/Blitz) si può **rinominare** con il nome del suo pacchetto (maps/SuperCrossRoads4) con un clic.
- Corretto: i tratti **Acqua** venivano salvati senza il loro livello, così la build del gioco rifiutava la mod. Ora ogni file che lo Studio scrive viene riletto prima di essere salvato.
- L'elenco delle mappe **si ripiega** («) per avere più spazio.
- **Impostazioni > Aiuto e comunità**: la wiki (il nuovo manuale da campo), Discussions, e **Segnala un problema**, che apre una segnalazione di bug con la tua versione già compilata. Un errore in basso ha il suo link **Segnala**. L'app non invia nulla: leggi tu la segnalazione e la pubblichi.

**0.7.0:** un nuovo aspetto e strumenti di movimento. Gli strumenti della mappa si sono spostati in una barra lungo il fondo, come in Cities: Skylines, nello stile dell'HUD di R.U.S.E. stesso: scegli un tipo (Terreno, Acqua, Copertura, Movimento, Edifici, Oggetti, Alberi, Scenario) e i suoi strumenti si aprono sopra; cliccalo di nuovo o premi Esc per guardarti solo intorno. I selettori dello scenario ora sono tessere, non menu a tendina. **Movimento:** la casella **Dove vanno le unità** lo mostra sulla mappa (rosso: nessuna unità; giallo: solo fanteria), e tre nuovi pennelli chiudono il terreno: **Blocca** (ogni unità), **Blocca la fanteria** e **Blocca i veicoli**. Gli edifici che piazzi fermano le unità (la casella **Solido**, attiva di default). Dimostrato in gioco: le unità pianificano il percorso intorno a una fossa bloccata e passano tra le torri piazzate.

**0.6.9:** edifici, oggetti e alberi che piazzi ora si vedono in gioco a ogni zoom (dimostrato su Blitz, fino a 8× la loro dimensione): ogni gruppo va in un nuovo blocco avvolto intorno al villaggio o alla fattoria più vicini che la mappa disegna da lontano. Controllato su tutte le 32 mappe: nient'altro si sposta. Le unità attraversano ancora gli edifici piazzati; renderli solidi è il prossimo passo.

**0.6.8:** crea città e boschi in cui le unità possono nascondersi. La vista mappa mostra dove si nascondono le unità (la casella **Copertura**, in verde), e tre nuovi pennelli la dipingono: **Copertura**, **Scopri** e **Città** (clicca su una città: la copertura va intorno a ogni suo edificio, anche a quelli piazzati). Dimostrato in gioco: la fanteria sulla copertura dipinta è nascosta.

**0.6.7:** gli oggetti piazzati arrivano fino a 10× la loro dimensione (il cursore Dimensione dello strumento Piazza; [ e ] avanzano di 0,1 fino a 3×, poi di 0,5).

**0.6.6:** anche le munizioni sono ordinate per tipo: proiettili perforanti, proiettili esplosivi, contraerea, mitragliatrici, armi di fanteria, anticarro della fanteria, bombe e razzi (l'elenco Tipo sopra le munizioni). Le mod possono anche dipingere su una mappa la copertura (dove le unità si nascondono, come in un bosco) e il terreno bloccato (`maps/<map>/cover.toml`); lo strumento dello Studio per farlo è il prossimo passo.

**0.6.5:** gli scenari si possono modificare sulla mappa. **Sposta** un punto di partenza o un'unità iniziale (cliccalo, poi clicca dove deve andare; Rimetti lo annulla). **Aggiungi unità** fa comparire un'unità o un edificio quando lo scenario inizia: scegli il suo genere (edifici, terra, fanteria, aria), poi il suo tipo (per gli edifici: QG, denaro, fabbriche, forti e difese, esche finte; per le unità: la fabbrica che le costruisce), poi l'unità (per nazione) e il suo schieramento. Salvato nel `maps/<map>/scenario.toml` della mod. L'elenco delle unità ha lo stesso filtro Tipo.

**0.6.4:** l'elenco delle mappe ha un filtro per tipo: tutte le mappe, o solo le mappe schermaglia, le Operazioni, la campagna, le mappe demo o di test (dai menu del gioco stesso; una mappa può essere di più tipi). Viene ricordato.

**0.6.3:** una scheda **Impostazioni** (accanto a Unità e Mappe): la lingua, i tasti della vista mappa, la cartella del gioco e gli aggiornamenti in un solo posto, pronta per altro.

**0.6.2:** trovare gli aggiornamenti è più affidabile: quando GitHub rifiuta l'unico controllo all'avvio (ne permette 60 all'ora per indirizzo internet, condivisi da tutto ciò che lo usa), lo Studio legge invece l'elenco delle release di GitHub. Le mod possono anche far comparire unità ed edifici in uno scenario (`[[spawn]]` in `maps/<map>/scenario.toml`).

**0.6.1:**

- **La tua lingua e i tuoi tasti vengono tenuti** attraverso riavvii, aggiornamenti e reinstallazioni (andavano persi a ogni avvio).
- **Scenari raggruppati come li usa il gioco:** Schermaglia, Operazioni, Campagna, Demo, Test, e quelli che nessun menu carica, ognuno chiamato come lo chiamano i menu del gioco («10. UTAH BEACH», «Anzio»).
- **Le mod possono spostare punti di partenza e unità iniziali** (`maps/<map>/scenario.toml`); controllato in gioco: il QG parte dove lo mette la mod.

**Novità della 0.6:**

- **Terreno che funziona in gioco:** il terreno che alzi, abbassi o spiani ora accetta gli ordini di movimento, la telecamera resta sopra di esso, e alberi ed edifici ci poggiano sopra. La ricetta di DomesticNukes e del suo Claude: il terreno di gioco si muove per primo, il terreno disegnato lo segue, e i limiti di altezza nascosti del gioco vengono allargati. Controllato su tutte le 32 mappe.
- **Scenari sulla mappa:** una riga «Scenario» sceglie uno degli scenari della mappa (schermaglia, sfide, capitoli di campagna) e mostra le sue zone, i punti di partenza (colonne nel colore di ogni alleanza), le unità iniziali (rombi bianchi) e i nomi delle città. Punta su uno per vedere cos'è. Il primo passo verso la creazione di mappe.

**0.5.2:**

- **Pennelli Acqua e Prosciuga** (Acqua sul tasto 0): allaga il terreno sotto un livello per farne un lago, o prosciuga un lago o un fiume. Di DomesticNukes e del suo Claude, controllati in gioco su Blitz.
- **Tasti tuoi:** «Cambia i tasti…» sotto la riga d'aiuto della vista mappa: clicca un'azione, premi un tasto. Predefiniti li rimette com'erano.

**0.5.1:**

- **Un cannone tiene la sua vampa e il suo suono:** quando un'arma spara le munizioni di un'altra unità, ora prende anche la vampa alla bocca e il suono di sparo di quell'unità (il cannone dello Sherman su un fuciliere spara come uno Sherman). L'arma mostra quali usa.
- **Pennello Livella** (tasto 7): rende piatto il terreno all'altezza da cui inizi a trascinare.
- **WASD si muove con la telecamera**: W è sempre avanti sullo schermo, comunque sia girata la vista.
- L'indice del gioco viene ricostruito una volta, la prima volta che si apre la 0.5.1 (circa mezzo minuto).

**Novità della 0.5:**

- **Nuove unità:** copia un'unità dalla sua pagina, dalle un nome e un prezzo e mettila in un menu di costruzione.
- **Munizioni e flag:** un tipo Munizioni con ogni munizione. Un'arma può sparare le munizioni di un'altra arma (si vede la nazione da cui vengono) o una sua copia di esse. Gli elenchi dei flag (cos'è e cosa fa un'unità) si possono modificare, come nell'editor delle unità di RUSE Mod Manager.
- **Mappe:** ogni mappa mostra il suo nome in gioco, nella tua lingua, accanto al suo nome in codice. Edifici, oggetti e alberi sono disegnati con **i veri modelli 3D e le vere texture del gioco**, grazie a DomesticNukes e al suo Claude.
- **Pennelli del terreno:** alza, abbassa, leviga e fai rampe nel terreno, salvato nella mod. **Ricomincia** azzera una mappa.
- **Strumento Piazza:** un clic piazza un edificio, un oggetto o un albero. Dipingi un'area, o clicca due volte per una linea (una siepe, una via). Annulla riprende un'intera area o linea. Per ora gli elementi piazzati sono solo estetici: le unità ci passano attraverso.
- **Tasti:** WASD / frecce muovono la vista, Q/E la ruotano, R/F zoomano. Passa sopra qualsiasi pulsante per un suggerimento.
- **Esporta .rusemod:** un solo file che il Launcher installa.
- **Si aggiorna da solo:** da questa versione in poi, una barra dice quando esce uno Studio più nuovo; **Aggiorna ora** lo installa.

È nuovo ed è stato provato appena fuori dal PC dello sviluppatore, quindi segnala qualsiasi cosa strana su GitHub Issues.

![Mappe di RUSE Studio: Centre of Gravity in 3D](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-maps.jpg)

![RUSE Studio in modalità anteprima, con unità di esempio](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-unit.jpg)
