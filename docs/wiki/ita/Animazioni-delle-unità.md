# Animazioni delle unità

> **Ti serve:** RUSE Studio 0.9.8.20 o successivo e una mod; Blender (gratis) per cambiare in Blender le animazioni di una
> nuova unità · **Tempo:** 10 minuti di lettura

Il modo in cui un'unità si muove (stare in piedi, camminare, correre, mirare, sparare, morire) sono le sue
**animazioni**. Questa pagina dice a cosa servono le animazioni del gioco, quale usa un'unità per ogni cosa che fa, ogni
modo di cambiarne una (per un'unità, per tutte, per le unità che scegli, o in Blender) e come riavere quella del gioco.

## Cos'è un'animazione

- Un'animazione muove nel tempo le ossa di un modello: un passo di corsa, un fucile portato alla spalla, una caduta
  (vedi [[Modelli e ossa|Modelli-e-ossa]]).
- Ogni cosa che un'unità fa nel gioco (un'**azione**: sta ferma, cammina, corre, spara...) riproduce un'animazione. Un
  soldato ne riproduce due insieme, una per ogni metà del corpo.
- Molte unità condividono le animazioni del gioco: ogni fuciliere americano corre allo stesso modo. Quindi una modifica a
  un'animazione è, se non scegli altrimenti, una modifica per tutte le unità che la usano.
- I carri girano torretta e ruote senza animazioni: qui non c'è niente da cambiare per loro.

## Le animazioni del gioco e a cosa serve ognuna

**RUSE Decoy** (la sua scheda in cima allo Studio) elenca ogni animazione del gioco a sinistra, sotto **Animazioni**, per
tipo:

| Tipo | Cosa contiene |
|---|---|
| **Fanteria** | Fucilieri, bazooka, paracadutisti e autisti: in piedi, cammino, corsa, mira, fuoco, ricarica, fuga, colpiti e morte (parte alta e bassa del corpo ognuna con le sue) |
| **Serventi dei cannoni** | Gli uomini attorno a un cannone: a riposo, mentre lo spostano, lo preparano, sparano e ricaricano |
| **Veicoli e cannoni** | Cannoni messi in batteria e trainati, a riposo e al fuoco, e altre parti mobili |
| **Figure del QG** | Gli ufficiali al tavolo del QG nelle scene di una missione (non usati da unità) |
| **Animali e scenario** | Mucche, cavalli, capre, galline, gabbiani e mulini sulle mappe |

Ognuna dice come la chiama il gioco e quante unità la usano. Nella pagina di un'unità, le azioni hanno il nome di ciò che
fa l'unità, raggruppate così:

| Gruppo | Le sue azioni (alcune) |
|---|---|
| Fermo | Sta fermo, Si accovaccia, Si guarda intorno |
| In movimento | Cammina, Cammina all'indietro, Corre, Corre a destra, Corre all'indietro, Fugge |
| Mirare e sparare | Mira, in piedi; Mira camminando; Spara; Lancia una granata; Ricarica |
| L'arma pesante | Mira con l'arma pesante, Spara con l'arma pesante, Alza l'arma pesante, Abbassa l'arma pesante |
| Essere colpiti | Viene colpito, Viene colpito alle spalle, Viene colpito da un'esplosione |
| Morire | Muore colpito, Muore in un'esplosione, Giace a terra |
| Lancio col paracadute | Si lancia, Cade, Scende col paracadute, Atterra |
| Azioni di un equipaggio | Attende, Avanza col pezzo, Va al pezzo, Mette in posizione il pezzo, Spara (un servente), Ricarica il pezzo |

## Le sue animazioni: quale usa ogni azione

Un'unità con animazioni sue (un modello con ossa sue: un cavallo, un cavallo col cavaliere, qualsiasi creatura) ha una
tabella nella sua pagina: **Aspetto e movimenti**, la riga **Suoni e animazioni**, **Altro**, poi **Le sue animazioni**.

- **Sta fermo**, **Cammina** e **Corre** vengono per prime: il minimo che serve a un modello. Se una non ha niente di
  suo, la pagina lo dice, e cosa usa al suo posto.
- Ogni azione ha un elenco delle animazioni del modello. Scegline una, o lasciala sulla prima riga, **Più vicina**: usa
  allora la più vicina che il modello ha, e la riga dice quale. Più vicina vuol dire, in quest'ordine: un'animazione con
  il nome di quell'azione (stand o idle, walk, run o gallop, fire, death...), altrimenti ciò che usa l'azione più vicina
  (un cammino usa la corsa, uno sparo la mira o lo stare fermo). Il gioco fa ciò che dice la pagina: la build segue la
  stessa regola.
- **Tutte le altre azioni** elenca il resto, per gruppo.
- **Nei lunghi spostamenti** è la sua ultima riga. In un lungo spostamento su strada il gioco mette una squadra nel suo
  camion. Un'unità con animazioni sue può andare invece come se stessa, usando una di esse in ciclo (la sua corsa, se
  resta la prima riga), alla velocità del suo camion. Scegli **Nel suo camion** per tenere il camion.

Un'unità copiata da una con animazioni sue usa le stesse.

## Cambiare un'animazione in RUSE Decoy

1. Nella pagina dell'unità, in **Aspetto e movimenti**, clicca **Cambia in RUSE Decoy** sulla riga **Suoni e
   animazioni**. RUSE Decoy si apre su quell'unità: i suoi suoni, poi **Le sue animazioni** con ogni animazione che usa.
   (Oppure apri la scheda **RUSE Decoy** e scegli un tipo sotto **Animazioni**.)
2. Clicca **Guarda e cambia…** su un'animazione. Si riproduce in 3D su un'unità che la usa: trascina per girarla, la
   rotellina fa lo zoom. La vista 3D ha bisogno di internet una volta.
3. Aperta dalla pagina di un'unità, la prima riga chiede **Modifica per**:
   - **Solo questa unità**: questa unità usa una sua copia dell'animazione, con le tue modifiche; tutte le altre la
     usano come prima. È la scelta di partenza, a meno che l'animazione non sia già cambiata per tutte le unità.
   - **Tutte le unità che la usano**: la modifica va all'animazione stessa, per tutte le unità che la usano (il numero
     dice quante).
   - **La tua copia** e il suo nome: compare quando questa unità usa una tua copia (sotto); allora è la scelta di
     partenza.
4. Cambiala:
   - **Velocità**: 100% è quella del gioco, 200% due volte più veloce, 50% due volte più lenta. Salvata quando lasci.
   - **Usa al suo posto**: un'altra animazione dello stesso corpo al suo posto (i fucilieri potrebbero correre come
     quando fuggono).
   - **Un osso**, con **Dimensione**, **Ruota attorno a** e **Rotazione**: una parte del corpo più grande, o ruotata,
     per tutta l'animazione.
   - **Motion capture**: il movimento di una persona vera al suo posto (vedi [[Musica e suoni|Musica-e-suoni]]).
5. Clicca **Fatto**. Ogni modifica è salvata subito nella tua mod, e va nel gioco quando provi o esporti.

## Una copia di un'animazione, per le unità che scegli

**Copia questa animazione…** fa una copia che usano solo le unità e i soldati che spunti: una corsa tua per tre delle
tue squadre, per esempio, e solo per il soldato con bazooka di una quarta.

1. Nella finestra dell'animazione clicca **Copia questa animazione…**, dai un nome alla copia (lo vedi solo tu) e clicca
   **Fai la copia**. Parte dall'animazione com'è ora, e si apre nella stessa finestra.
2. Cambiala come sopra.
3. Sotto **Chi la usa**, spunta le unità che usano la copia: prima **Le tue unità**, poi **Le unità del gioco**. Sotto
   un'unità di cui più soldati o parti la usano, spuntane solo alcuni. **Trova un'unità** cerca per nome o paese.
4. Niente usa una copia finché non spunti un'unità: la riga sotto il suo nome dice «nessuna unità la usa ancora» fino ad
   allora.

Ogni copia è a sinistra in RUSE Decoy sotto **Le tue copie**: aprila lì, oppure **Elimina la copia**. La copia propria di
un'unità (**Solo questa unità**) o un'animazione cambiata in Blender ha la precedenza su una copia per quell'unità:
l'elenco lo dice accanto.

## Cambiare in Blender le animazioni di una nuova unità

Per una nuova unità fatta nella tua mod (un'unità del gioco richiede prima una nuova unità fatta da essa):

1. Nella pagina dell'unità clicca **Cambia in RUSE Decoy**. Sopra le sue animazioni clicca **Cambia le sue animazioni in
   Blender**. Blender si apre con l'unità e ogni animazione che usa, ognuna con il nome di ciò che vi fa, seguito dal
   nome che le dà il gioco.
2. In fondo a Blender, l'Action Editor le elenca: scegline una. **Spazio** la riproduce.
3. Clicca un osso, premi **Ctrl+Tab** per la Pose Mode, **R** per ruotarlo (**G** lo sposta), poi **I** per tenere la
   posa a questo fotogramma. Fallo a ogni fotogramma che cambi: Blender va da solo da una posa tenuta alla successiva.
4. Clicca **Invia al R.U.S.E. Studio** in cima alla vista 3D di Blender: ogni animazione parte, cambiata o no.
5. In RUSE Decoy clicca **Riporta le mie modifiche**. Dice quali sono tornate cambiate: ora sono proprie di questa
   unità. Tutte le altre unità, e ogni animazione che non hai toccato, restano come prima.

Metti solo in posa le ossa: non rinominarle, non cancellarle, non spostarle in Edit Mode. Altrimenti lo Studio non
prende nulla, e dice quali ossa.

Un modello con ossa sue (un cavallo, qualsiasi creatura) invia le proprie animazioni, con i loro nomi. Quella che cambi
prende il suo posto: ogni azione che la usava la usa cambiata.

## Riavere l'animazione del gioco

| Per togliere | Clicca | Dove |
|---|---|---|
| Una modifica per tutte le unità | **Torna a quella del gioco** | La riga dell'animazione in RUSE Decoy, o la sua finestra |
| La copia propria di questa unità (**Solo questa unità**) | **Torna a quella di tutte le unità** | La riga dell'animazione nell'elenco dell'unità, o la sua finestra |
| Le modifiche di una copia (nome e spunte restano) | **Torna all'animazione del gioco** | La finestra della copia |
| Una copia, tutta | **Elimina la copia** | **Le tue copie** |
| Una modifica fatta in Blender | Annullala in Blender finché quel Blender è ancora aperto, poi **Riporta le mie modifiche**: viene annullata anche nella tua mod | Blender, poi RUSE Decoy |

I pulsanti sopra non tolgono una modifica fatta in Blender.

## Cosa può dirti Riporta le mie modifiche

| Dice | Cosa fare |
|---|---|
| «Cambiate in Blender, ora proprie di questa unità: ...» | Niente: ha funzionato. **Prova in gioco** lo mostra. |
| «Ogni animazione è tornata com'era partita.» | Non è cambiato nulla. Hai tenuto ogni posa con **I**? |
| «Fatte in Blender, non ancora usate da nessuna azione: ...» | Una nuova animazione non viene presa. Salvala in Blender (**File > Save**) per tenerla. |
| «Non rimandate (cancellate o rinominate in Blender), quindi si riproducono come prima: ...» | Ridalle il suo nome in Blender se vuoi dentro la tua modifica. |
| «Queste si riproducono su una sola metà del corpo ... quindi potrebbero non vedersi nel gioco» | Le ossa che hai mosso sono nell'altra metà: muovi quelle della metà che la riproduce. |
| «Ossa fatte in Blender, che lo scheletro di questa unità non ha ...» | Un osso nuovo non può essere riprodotto; il resto è arrivato. |
| «L'editor NLA di Blender riproduce queste con tempi propri ...» | Il gioco le riproduce come le mostra l'Action Editor. |
| «La scena di Blender andava a ... fotogrammi al secondo e il gioco va a 30 ...» | Metti Blender a 30 fotogrammi al secondo per vedere la velocità del gioco. |
| «La scena di Blender ha il Time Stretching attivo ...» | Metti Old e New allo stesso numero per vedere la velocità del gioco. |
| «Nessuna azione di questa unità esegue queste ...» | Sceglila per un'azione sotto **Le sue animazioni**, nella pagina dell'unità. |
| «Da Blender non è arrivato nulla di nuovo dall'ultima volta che hai riportato le tue modifiche.» | Clicca prima **Invia al R.U.S.E. Studio** in Blender. |

## Cosa può andare storto

- **Nel gioco non cambia nulla:** una modifica per **Solo questa unità** si vede solo su quell'unità, e una copia solo
  sulle unità spuntate per lei. Una modifica fatta in Blender ha la precedenza, per quell'unità, su una modifica fatta
  dopo alla stessa animazione con **Solo questa unità** o una copia (la regola dello Studio; non ancora provato nel
  gioco).
- **«Solo una nuova unità fatta in questa mod ha animazioni proprie»**: l'unità è una di quelle del gioco. Crea prima una
  nuova unità da essa (**Nuova unità da questa…** nella sua pagina).
- **Le sue animazioni manca nella pagina:** la tabella c'è solo per un'unità con animazioni sue (un modello con ossa
  sue). Tutte le altre unità usano quelle del gioco: cambiale in RUSE Decoy.
- **Un invio che non hai mai riportato:** riaprire Blender lo mette da parte. RUSE Decoy lo mostra con **Riporta l'invio
  messo da parte** e **Mettilo nel Cestino** (vedi [[Apri in Blender|Apri-in-Blender]]).

## Cosa è stato provato nel gioco

- Le modifiche alle animazioni di RUSE Decoy per tutte le unità che le usano (Studio 0.9.8.8).
- **Solo questa unità**: una squadra che balla sul posto mentre tutte le altre squadre stavano come prima (novembre
  2026).
- **Copia questa animazione…**: una copia usata da una squadra e da un soldato di un'altra (novembre 2026).
- **Cambia le sue animazioni in Blender**: una squadra in piedi e in corsa con un braccio alzato, e Squadre a cavallo
  generiche i cui cavalli tengono la testa alta (novembre 2026).
- Le animazioni proprie della Squadra a cavallo generica, scelte da **Più vicina**, e il viaggio come se stessa nei
  lunghi spostamenti (novembre 2026).
- Non ancora provato nel gioco: una velocità, una sostituzione o un osso cambiati per una sola unità, e un'altra
  animazione scelta a mano sotto **Le sue animazioni**.

Ancora bloccato? Chiedi sul [Discord](https://discord.gg/h54t5baNsC), oppure vedi
[[Quando qualcosa va storto|Quando-qualcosa-va-storto]].

**Avanti:** [[Apri in Blender|Apri-in-Blender]] · [[Modelli e ossa|Modelli-e-ossa]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Unit-Animations]]
