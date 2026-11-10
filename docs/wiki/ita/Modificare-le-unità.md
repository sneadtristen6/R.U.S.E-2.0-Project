# Modificare le unità

> **Per:** modder · **Ti serve:** RUSE Studio e una mod · **Tempo:** quanto vuoi

## Trova un'unità

La scheda **Unità** elenca ogni unità ed edificio. Restringi l'elenco con:

- il riquadro **Cerca** (nomi in codice o i nomi che vedono i giocatori, in una qualsiasi delle dieci lingue del gioco: il pulsante della lingua in alto).
  Ogni parola che scrivi deve corrispondere; i **#tag** lo restringono (`#us`, `#germany`, `#air`, `#armor`, `#new` per le
  nuove unità della tua mod; scrivi `#` per vederli tutti), e le tue ricerche recenti vengono conservate;
- i chip **Tipo** e **Nazione**;
- il menu dei **tipi**: a cosa serve, come QG, denaro, fabbriche, forti ed esche per gli edifici, o la fabbrica che
  costruisce un'unità.

## Cambia un valore

1. Clicca sull'unità. I suoi valori sono elencati per sezione (prezzo, corazza, velocità, armi...).
2. Scrivi un nuovo valore. Viene salvato subito nella tua mod; il valore del gioco appare accanto.
3. **Annulla** accanto a un valore rimette il valore del gioco.

## Flag: cos'è un'unità e cosa può fare

I flag sono interruttori acceso/spento, numerati da 0 a 104, che dicono al gioco cos'è un'unità (un aereo, un camion,
fanteria, un edificio...) e cosa può fare (entrare nei boschi, vedere tutto intorno, sparare solo su ordine...). Nella
pagina di un'unità appaiono come chip, ognuno con il suo nome: passaci sopra con il mouse per vedere esattamente cosa fa,
come usarlo e quanto ne siamo sicuri. La croce ne toglie uno; **Aggiungi un flag…** ne aggiunge uno, ordinati per ciò a cui
servono i flag.

**Guida ai flag: tutti spiegati** (sotto i flag) apre l'elenco completo, con un riquadro di ricerca. Per ogni flag dice:

- **cos'è e cosa fa** nel gioco;
- **come usarlo**;
- **quanto ne siamo sicuri:** *provato nel gioco*, *dalle unità del gioco* (ciò che hanno in comune le unità del gioco stesso
  che lo hanno), *previsto, non ancora provato*, *lo imposta il gioco da solo* (li accende e spegne mentre gira:
  nell'elenco di un'unità non fanno niente), oppure *inutilizzato*.

**Lo Studio controlla i flag di ogni unità** ogni volta che li cambi, e di nuovo prima che il gioco si avvii:

- **I crash noti fermano la build**, così il gioco non viene mai avviato con essi. La pagina dell'unità dice perché e
  propone la correzione (**Togli 62**, **Aggiungi 100**):
  - 62 (camion) o 63 (camion da costruzione) su qualcosa che non è un camion: il gioco va in crash all'inizio della partita;
  - 99 (aereo da ricognizione) su un aereo con armi, senza 100 (caccia): il gioco va in crash quando l'aereo viene mandato
    ad attaccare. Usa il riquadro **Ruolo** (Ricognitore mantiene i suoi attacchi) o aggiungi 100;
  - 59 (trasporto paracadutisti) su qualcosa che non è un aereo, o su un aereo senza unità da lanciare.
- **Ciò che dovrebbe rompere un'unità è un avviso**, non un blocco: 2 (aereo) su un'unità di terra, 4 (edificio) o 49 su
  un'unità, 6 o 76 su un'unità che dovrebbe muoversi (resta ferma), 42 (fanteria) su un veicolo, o togliere 43 (la sua
  squadra la conta) o 22 (il giocatore può darle ordini).

Utili, provati in gioco: togli **11, 21 e 55** insieme per far entrare un veicolo nei boschi; **1** dà a qualsiasi unità il
tiro indiretto; **71** vede tutto intorno; **77** spara solo su ordine.

**Tipi di flag tuoi** (Studio 0.9.8.8): **Crea o cambia tipi di flag…** sotto i flag di un'unità crea un insieme con un
nome di flag del gioco, ognuno messo su **Acceso** o **Spento**, con una riga su a cosa serve. **Dai un tipo di flag…** su
qualsiasi unità accende e spegne quei flag in un colpo solo; toglierlo rimette i flag dell'unità come erano. Cambia un tipo
e cambia anche ogni unità che lo ha. Il gioco agisce solo sui suoi flag, quindi un tipo combina ciò che quelli fanno già.
Non ancora provato in gioco.

## Crea una nuova unità

Una nuova unità parte come copia di un'unità del gioco, con un nome suo, così puoi cambiarla senza toccare l'originale.
La scheda Unità ha due pulsanti in alto: **Modifica un'unità** (l'elenco, poi i valori dell'unità e Blender) e
**Nuova unità (importa un modello)**. Con **Nuova unità**, scegli l'unità da cui partire, dalle un nome e clicca su **Crea**;
poi cambiala come qualsiasi altra. Oppure scegli l'unità e scegli **Nuova unità…** nella sua pagina.

## Cambia l'aspetto di un'unità

La pagina dell'unità mostra il suo **Modello 3D**: trascina per ruotarlo, usa la rotellina per lo zoom.

- **Ridipingi in Blender:** clicca su **Apri in Blender** (Blender è gratuito; se lo Studio non lo trova, la pagina propone
  **Scarica Blender (gratis)** e **Scegli Blender…** per mostrargli dove si trova `blender.exe`). L'unità si apre con le sue
  immagini, pronta per dipingere sul modello. Dipingi, poi clicca su **Riporta**: la tua
  pittura va nella tua mod. Visto in gioco, da vicino e da lontano.
- **La sua scheda nel menu di costruzione:** ruota e ingrandisci il modello 3D finché non sta bene dentro la cornice
  tratteggiata, poi **Usa questa vista come scheda**. **Scheda del gioco** la riporta indietro. Visto in gioco. Su una nuova
  unità la scheda è sua: l'unità che copia tiene la sua immagine.
- **Una sua copia del modello:** un'unità disegnata con il modello del gioco condivide la sua pittura con ogni unità
  disegnata con esso. **Dagli una sua copia del modello** (nella sua pagina) crea lo stesso modello con texture sue: poi
  **Apri in Blender** dipinge solo questa unità. Funziona per le nuove unità e per quelle del gioco.
- **L'uniforme di una squadra:** i soldati del gioco di una nazione indossano tutti una stessa immagine (quella degli USA: i
  suoi GI, Ranger e paracadutisti, e gli equipaggi dei suoi cannoni e veicoli), quindi l'**uniforme predefinita** qui non
  viene ridipinta. Scegli **Uniforme personalizzata** per dare alla squadra la sua, poi dipingila in Blender. Visto in gioco.
- **Viaggia su:** il camion in cui si trasforma una squadra o un cannone sulle strade: quello del gioco, quello di un'altra
  nazione, o la copia di un camion che hai creato e ridipinto. Visto in gioco.
- **Un modello tutto suo (nuove unità):** **Importa modello…** porta dentro un modello 3D da Blender o da qualsiasi
  programma 3D. Vedi [[Importare un modello|Importare-un-modello]]. Un'unità del gioco tiene il suo modello: la sua pagina ha
  **Nuova unità da questa…** per creare la nuova unità su cui va il modello.

## Corazza

**Corazza** nella pagina di un'unità sceglie uno dei livelli di corazza del gioco (i carri armati hanno da 1 a 5, il numero
sullo scudo). L'unità combatte con quello, e la sua scheda e il menu di costruzione lo mostrano. Cambiare un numero dentro la
parte della corazza stessa faceva combattere un'unità con un valore mentre la sua scheda ne mostrava un altro, quindi quella
parte non si può più cambiare direttamente. Visto in gioco.

## Ricerca: di cosa è un potenziamento

La pagina di un'unità ha un riquadro **Potenziamento e ricerca**: l'unità di cui è un potenziamento (**Potenziamento di**), i
suoi potenziamenti, e il prezzo e il tempo della sua ricerca. Scegli un'altra unità dello stesso menu di costruzione, oppure
**Nessuna: un'unità a sé** per renderla acquistabile dall'inizio. I tempi di ricerca si possono scrivere in secondi o minuti
(il selettore accanto).

Quando togli un'unità da cui altre vengono ricercate, **Impostazioni > Ricerca** decide cosa succede: **Avvisami prima**
(il predefinito), **Rifiuta**, oppure **Ricollegale** al genitore di quell'unità. Un'unità rimasta ricercata da una che non
c'è più lo dice qui e nella barra dei controlli, e la build si ferma su di essa finché non ne scegli un'altra.

Un'unità mostrata nel suo menu di costruzione deve essere ricercata da un'unità mostrata anche lì: quella che puoi costruire
viene prima, la ricerca dopo. Un'unità mostrata in una data di battaglia in cui l'unità da cui viene ricercata è nascosta
ferma il gioco quando si apre quel menu di costruzione (visto in gioco), quindi la barra dei controlli la nomina e la build si
ferma su di essa. Mostra di nuovo l'altra unità, oppure scegli un'altra unità da cui ricercarla, o nessuna. **Nazioni >
Nascondi tutte** lo fa per te: un'unità rimasta ricercata da una nascosta diventa acquistabile dall'inizio.

## Unità di altre epoche

366 unità dalla Prima guerra mondiale a oggi, ognuna un modello 3D gratuito di un altro autore, si possono aggiungere alla
tua mod come nuove unità, alle loro dimensioni reali e dietro una ricerca: vedi [[Unità di altre epoche|Unità-di-altre-epoche]].

## Armi e munizioni

Il riquadro **Armi** nella pagina di un'unità elenca le sue armi (Arma 1 è il cannone principale). **Come funzionano armi e
munizioni**, sotto di esso, ha anche questi passi.

1. **Ogni arma spara una munizione.** L'elenco accanto sceglie quale: qualsiasi munizione del gioco, ordinata per tipo (AP,
   HE, contraerea, mitragliatrici, bombe, razzi...), o una copia che hai fatto. Il suo lampo alla bocca e il suo suono
   vengono con essa.
2. **La munizione decide cosa fa l'arma:** il suo danno, la gittata, la cadenza di tiro e cosa può colpire. **Apri la
   munizione** per vederne e cambiarne i numeri.
3. **Cambiare una munizione cambia ogni unità che la spara** (la sua pagina le elenca). Per una sola unità: nella pagina
   della munizione clicca su **Copia questa munizione…**, cambia la copia, poi scegli la copia nell'elenco dell'arma. Il
   cursore **Gittata** di un'arma chiede la stessa cosa: solo questa unità, o ogni unità con quella munizione.
4. **Colpisce** (sotto un'arma) sceglie il suolo, gli aerei o entrambi. Il riquadro **Ruolo** di un aereo imposta come
   attacca (sotto).
5. **Aggiungere o togliere un'arma non è ancora possibile:** le armi sono legate alle animazioni del modello, e non siamo
   ancora arrivati a quel punto.

**Il suo nome in gioco** (nella pagina di una munizione, Studio 0.9.8.8): come il gioco chiama la munizione, il suo
**Nome** (Medium cal., MG 42) e il suo **Tipo** (AP shell). Scrivi nuove parole e salva: ogni lingua le mostra finché non
ne cambi una da sola con **Cambia le parole…**; **Parole del gioco** toglie le tue. Una munizione copiata si chiama con il
nome che le dai. Non ancora provato in gioco.

**Classe d'arma** (nella pagina di una munizione, Studio 0.9.8.17): quanta parte del suo danno la munizione infligge a
ogni tipo di bersaglio. **Nuova classe d'arma…** apre un numero per ciascuno: edifici e fortificazioni, aerei,
paracadutisti in discesa, fanteria, veicoli leggeri (trasporti), corazza da 1 a 5 e camion da costruzione. 1 è il danno
pieno, 2 il doppio, 0,5 la metà, e 0 significa che non può attaccare affatto quel bersaglio. **Salva classe** dà alla
munizione una propria copia della tabella dei danni del gioco, così non cambia il danno di nessun'altra munizione, ma
ogni unità che spara questa munizione la riceve (per una sola unità, usa prima **Copia questa munizione…**). Il
pulsante diventa allora **Cambia questa classe d'arma…**; **Torna alla classe del gioco** toglie la copia, ed
eliminare una munizione copiata elimina anche la sua classe. Visto in gioco: squadre di fucilieri la cui munizione
aveva ricevuto numeri contro i carri armati hanno sparato ai carri con i fucili e li hanno danneggiati. Il pulsante in
sé non è ancora stato cliccato nello Studio.

**Velocità del colpo:** la velocità del colpo di una munizione e la sua resistenza dell'aria decidono quando arriva il
colpo: un colpo più lento colpisce più tardi, e un bersaglio in movimento viene puntato in anticipo, in base al tempo di
volo (noto da come funziona il gioco; non ancora provato in un test).

## Cambia il ruolo di un aereo (Studio 0.9.8.5)

La pagina di un aereo ha un riquadro **Ruolo**: **Caccia**, **Cacciabombardiere**, **Bombardiere** o **Ricognitore**. Come
vola e attacca, come lo usano i giocatori del computer e le parole del suo menu di costruzione cambiano con esso.

- **Bombardiere:** un bombardiere sgancia le sue bombe in un passaggio rettilineo, e solo da un vano bombe. Scegli prima le
  bombe per una delle sue armi (Armi, sotto), poi rendilo un Bombardiere: le sue bombe vanno in un vano bombe copiato da
  quello di un bombardiere del gioco, e lì puoi cambiarle. È la correzione per un cacciabombardiere a cui erano state date
  bombe a tappeto che non sganciava niente. Visto in gioco.
- **Ricognitore:** un aereo con armi resta in grado di attaccare (il riquadro dice **Ricognitore, che mantiene i suoi
  attacchi**) e riceve la vista dei ricognitori. Visto in gioco con uno Stuka e un ME109.
- Un aereo per paracadutisti tiene il suo ruolo. **Annulla** accanto al riquadro ridà il ruolo del gioco, con le bombe dove
  erano.

## Rendi un veicolo da ricognizione (Studio 0.9.8.5)

Il riquadro **Ruolo** di un veicolo di terra: **Ricognizione** gli dà la vista delle auto da ricognizione (molto più lontana
di quella di un carro armato), il modo in cui le usano i giocatori del computer, le parole del loro menu di costruzione, e
può entrare nei boschi. Resta resistente e armato come è. Visto in gioco con un Panzer IV.

## Cosa colpisce un'arma (Studio 0.9.8.5)

Sotto ogni arma, **Colpisce** sceglie **Il suolo**, **Gli aerei** o **Il suolo e gli aerei**. Aerei: l'arma spara una copia
della sua munizione che colpisce gli aerei (e non fa niente al suolo). Entrambi: tiene la sua munizione e riceve una seconda
arma accanto per gli aerei, come i cannoni contraerei del gioco ne portano una per ciascuno. Un carro armato che spara agli
aerei è visto in gioco; il cannone di un aereo impostato per colpire solo il suolo per ora non fa danni.

## Provala

**Prova in gioco** costruisce la mod e avvia R.U.S.E. Cerca l'unità dove viene costruita (la sua fabbrica) in una battaglia (menu principale: **BATTAGLIE**, poi una mappa).

**Avanti:** [[Esportare e condividere|Esportare-e-condividere]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Edit-Units]]
