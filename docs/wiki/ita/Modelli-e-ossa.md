# Modelli e ossa

> **Ti serve:** RUSE Studio 0.9.8.20 o successivo, una mod con una nuova unità e Blender (gratis) per cambiare le ossa ·
> **Tempo:** 10 minuti di lettura

Soldati, cavalli e qualsiasi creatura si muovono in R.U.S.E. perché il loro modello 3D ha delle **ossa**. Questa pagina
dice cosa sono le ossa, come le usa il gioco, e cosa vuol dire ogni riquadro sulle ossa nella pagina di un'unità e cosa
farne. Un carro gira torretta e ruote senza animazioni, quindi questa pagina parla soprattutto di soldati, cavalli e
creature.

## Cosa sono le ossa

- Un **modello** è un guscio fatto di punti, con delle immagini dipinte sopra.
- Dentro, come uno scheletro, ci sono le **ossa**: un braccio, un avambraccio, una mano, la testa, ogni zampa di un
  cavallo. Ogni osso è appeso a un altro (la mano all'avambraccio, l'avambraccio al braccio), fino al primo osso.
- Ogni punto del guscio segue un osso, o alcuni: i punti di una manica seguono il braccio. Quanto un punto segue ogni
  osso è il suo **peso**.
- Un'**animazione** muove le ossa, fotogramma dopo fotogramma, e il guscio le segue. È così che un soldato cammina, mira
  e cade.
- In Blender, le ossa di un modello sono un solo oggetto, chiamato **armature**.

## Come le usa il gioco

- Il gioco muove le ossa di un modello **secondo il loro posto nel suo elenco di ossa**, non secondo i nomi. Quindi
  un'animazione fatta per un modello va bene solo per un modello con le stesse ossa, nello stesso ordine.
- Alcune ossa hanno un compito: un colpo parte da un osso alla bocca dell'arma, la parte alta del corpo si gira verso il
  bersaglio a un osso della schiena, un'arma viene mostrata e nascosta su un osso, una torretta o una ruota gira su un
  osso. La pagina dell'unità nomina ognuno di quelli che mancano al tuo modello (vedi **Funzionerà nel gioco?** più
  sotto).
- Un soldato riproduce **due animazioni insieme**: una sulla metà superiore del corpo (mirare, sparare) e una su quella
  inferiore (camminare, correre). Anche un cavallo e il suo cavaliere: vedi **Le sue due metà** più sotto.
- Il gioco non è stato visto animare un modello con più di 64 ossa.

## Due tipi di modello

| | Sulle ossa del soldato del gioco | Con ossa tutte sue |
|---|---|---|
| **Cos'è** | Un soldato cambiato in Blender, o un tuo modello messo sulle ossa di un soldato | Un cavallo, un cavallo col cavaliere, qualsiasi creatura, fatto in Blender su ossa tue |
| **Come si fa** | **Apri in Blender** sulla scheda della squadra: ogni soldato si apre con le sue ossa (vedi [[Apri in Blender|Apri-in-Blender]]) | In Blender, poi **Importa un modello…** sulla riga di un soldato, sotto **Ogni soldato** (vedi [[Importare un modello|Importare-un-modello]]) |
| **Le sue animazioni** | Quelle del gioco, come il soldato | Le sue, dal suo file |
| **Le sue due metà** | Quelle del gioco: niente da scegliere | Le scegli tu (lo Studio suggerisce l'osso) |
| **Dimensione e posizione** | Come l'hai fatto in Blender, sulle sue ossa | Come nel suo file |

La pagina dice di quale si tratta. Su un modello sulle ossa del soldato del gioco: «Il tuo modello è sulle ossa del
soldato del gioco, quindi tiene le due metà del gioco: niente da scegliere.» Su un modello con ossa sue: «Ha ossa tutte
sue:» e quante. La **Squadra a cavallo generica** (scheda **Unità**, **Seconda guerra mondiale+**) è una squadra con ossa
sue: vedi [[Unità di altre epoche|Unità-di-altre-epoche]].

## Dove la pagina le mostra

Nella pagina di una nuova unità, tutto ciò che riguarda le ossa è in **Aspetto e movimenti**:

| Riquadro | Dove | Cosa ti dice |
|---|---|---|
| **Le sue ossa e animazioni** | La riga **Suoni e animazioni**, **Altro** | Quante ossa ha il modello, e ogni animazione con la sua durata e quante azioni dell'unità la usano (un modello con ossa sue) |
| **Le sue due metà** | La riga **Suoni e animazioni**, **Altro** | Dove il modello si divide nella metà superiore e in quella inferiore |
| **Le sue animazioni** | La riga **Suoni e animazioni**, **Altro** | Quale animazione l'unità usa per ogni cosa che fa: vedi [[Animazioni delle unità|Animazioni-delle-unità]] |
| **Funzionerà nel gioco?** | La riga **Modello**, **Altro**; nella pagina di una squadra, **Altre opzioni** sotto i soldati, poi **Il modello di ogni soldato** | Cosa, nel modello, potrebbe fermare il gioco o sembrare sbagliato, e come correggerlo |
| Punti senza osso | Nello stesso posto di **Funzionerà nel gioco?** | Quanti punti del modello non seguono nessun osso |

## Le sue due metà

Il gioco riproduce due animazioni insieme su un soldato: una sulla sua **metà superiore** (mirare, sparare) e una sulla
sua **metà inferiore** (camminare, correre). Un cavaliere mira e spara mentre il suo cavallo corre: il cavaliere è la metà
superiore, il cavallo quella inferiore.

- Un modello sulle ossa del soldato del gioco tiene le metà del gioco: la pagina dice «niente da scegliere».
- Un modello con ossa sue si divide a **un osso**: quell'osso e tutte le ossa sotto formano la metà superiore, tutte le
  altre quella inferiore.

Per sceglierlo:

1. Nella pagina dell'unità, in **Aspetto e movimenti**, clicca **Altro** sulla riga **Suoni e animazioni**.
2. Sotto **Le sue due metà**, l'elenco **La metà superiore inizia da** mostra per primo il suggerimento dello Studio,
   segnato «(suggerito)». Lo Studio suggerisce il primo osso del cavaliere su un cavallo con cavaliere (**bip01** nella
   Squadra a cavallo generica), altrimenti il primo osso chiamato spine (come un soldato), altrimenti l'osso dove lo
   scheletro si divide per la prima volta.
3. Per la maggior parte dei modelli il suggerimento va bene: lascialo. Per cambiarlo, scegli un altro osso
   nell'elenco. Viene salvato subito, e si vede nel gioco dopo la prossima build (**Prova in gioco**).
4. Sotto l'elenco, la pagina conta le ossa di ogni metà, e **Quale osso va dove** elenca ogni osso del modello, segnato
   metà superiore o metà inferiore.
5. Per tornare al suggerimento, scegli di nuovo la prima riga dell'elenco.

Una divisione diversa da quella suggerita non è ancora stata provata nel gioco.

## I pesi: quale osso segue ogni punto

Quando metti un tuo modello (o un elmetto, uno zaino, un'arma) sulle ossa di un soldato, Blender deve sapere quale osso
segue ciascuno dei suoi punti. Questi sono i passi di Blender stesso.

**Il tuo modello su un soldato, ogni punto segue le ossa più vicine:**

1. Sulla scheda della squadra, clicca **Apri in Blender**: Blender si apre con i soldati, ognuno sulle sue ossa.
2. In Blender importa il tuo modello con **File > Import** e mettilo sopra il soldato.
3. Clicca il tuo modello, poi **Maiusc+clic** sulle ossa del soldato: le ossa per ultime.
4. Premi **Ctrl+P** e scegli **With Automatic Weights**. Blender calcola i pesi per te.
5. Cancella ciò che non tieni (la forma del soldato del gioco, se il tuo modello prende il suo posto), ma tieni le sue
   ossa.
6. Clicca **Invia al R.U.S.E. Studio** in cima alla vista 3D di Blender, poi **Riporta le mie modifiche** nello Studio.

**Un pezzo rigido che segue un solo osso (un elmetto sulla testa):**

1. In Blender clicca l'elmetto, poi **Maiusc+clic** sulle ossa del soldato.
2. Premi **Ctrl+Tab** per la Pose Mode e clicca l'osso della testa.
3. Premi **Ctrl+P** e scegli **Bone**. L'elmetto ora si muove con la testa, e lo riceve solo lui quando riporti le tue
   modifiche.

**Punti senza osso.** I pesi automatici di Blender a volte dimenticano qualche punto. La pagina allora dice «{n}
punto/i del tuo modello non hanno un osso, quindi si muovono solo con i fianchi del soldato.» Per correggere:

1. Di nuovo **Apri in Blender**.
2. Clicca il tuo modello, poi passa la modalità di Blender (in alto a sinistra nella vista 3D) da **Object Mode** a
   **Weight Paint**.
3. Nelle proprietà del modello (il triangolo verde), **Vertex Groups** ha un gruppo per osso: scegli l'osso che quei
   punti devono seguire.
4. Dipingi sopra i punti.
5. **Invia al R.U.S.E. Studio**, poi **Riporta le mie modifiche**.

## Funzionerà nel gioco?

Lo Studio controlla un modello su ossa rispetto alle animazioni che riproduce e alle parti e ai colpi dell'unità che
copia. La build della mod controlla di nuovo, con tutte le tue modifiche. Un problema non ti blocca mai: dice cosa
succederà e come correggerlo.

**Dove:** nella pagina di una nuova unità, **Aspetto e movimenti**, la riga **Modello**, **Altro**. Nella pagina di una
squadra: **Altre opzioni**, sotto i soldati, poi **Il modello di ogni soldato**.

Quando va tutto bene dice: «Nulla che fermerebbe il gioco: ogni animazione che riproduce ha le sue ossa, e ogni osso che
servono alle sue parti e ai suoi colpi c'è.» (con il numero di ossa).

### Cosa vuol dire ogni risposta

Ogni problema dice tre cose: cosa non va, cosa ne fa il gioco e come correggerlo. La riga di mezzo è una di queste:

| La pagina dice | Cosa vuol dire | Cosa fare |
|---|---|---|
| Questo può fermare il gioco: è successo in un test. | Il gioco si è fermato così in uno dei nostri test. | Correggi prima di provare. |
| Questo può fermare il gioco (non ancora provato nel gioco). | Ci si aspetta che il gioco si fermi. | Correggi prima di provare. |
| Il gioco la riproduce, ma avrà un aspetto sbagliato (non ancora provato nel gioco). | Si muoverebbero le ossa sbagliate. | Correggi, oppure prova e guarda. |
| L'unità combatte ancora, ma i suoi colpi non si vedranno: è successo in un test. | Fa danni, ma nessun colpo si vede. | Aggiungi l'osso che la pagina nomina. |
| Non ancora provato nel gioco: il gioco potrebbe non animarlo. | Più ossa di quante il gioco sia stato visto animare. | Unisci o cancella delle ossa. |
| Funziona lo stesso, ma forse non è ciò che vuoi. | Una nota sulle sue due metà. | Controlla **Le sue due metà**. |

### Ogni problema e come correggerlo

**Animazioni che non vanno bene per le ossa del modello.** La pagina dice quante animazioni, per quante azioni, e perché
non vanno: «Muovono {a} ossa e il tuo modello ne ha {b}.» (oppure «solo {b}»), oppure tante ossa ma «con altri nomi», o
«in un altro ordine». Quelle animazioni sono state fatte per altre ossa.

- Se l'unità riproduce le animazioni del gioco sul tuo modello: dai a quelle azioni animazioni proprie del tuo modello.
  **Importa modello…** porta dentro ogni animazione del file del tuo modello, e scegli quale usa ogni azione sotto **Le
  sue animazioni** ([[Animazioni delle unità|Animazioni-delle-unità]]).
- Se sono le animazioni del tuo modello, fatte per un altro modello: rifalle in Blender sulle ossa di questo modello,
  poi importa di nuovo il modello.

**Un osso che serve all'unità.** Per esempio: «Fucilieri: i colpi partono da un osso chiamato Fx_Tir_01, e il tuo
modello non ce l'ha.» (oppure: la parte alta del corpo lì si gira verso il bersaglio, un'arma lì viene mostrata e
nascosta, un pezzo lì viene tenuto, una torretta o una ruota lì gira, il corpo lì poggia, un cannone trainato lì si
aggancia). Per aggiungere l'osso in Blender:

1. Apri il modello in Blender: **Apri in Blender** con **Le sue ossa** spuntato (vedi
   [[Apri in Blender|Apri-in-Blender]]), oppure il tuo file di Blender.
2. Clicca le ossa (l'armature) e premi **Tab** per la Edit Mode.
3. Premi **Maiusc+A**: un nuovo osso appare dove si trova il cursore 3D di Blender.
4. Premi **F2** e scrivi esattamente il nome che dice la pagina (per esempio `Fx_Tir_01`). Se il tuo modello ha
   quell'osso con un altro nome, rinomina invece quello.
5. Nelle proprietà dell'osso (l'icona dell'osso), sotto **Relations**, metti in **Parent** l'osso con cui si muove il
   pezzo: per un colpo, l'osso con cui si muove l'arma.
6. Premi **G** e sposta il nuovo osso dove deve stare il pezzo: per un colpo, in fondo alla canna dell'arma.
7. Premi di nuovo **Tab**, clicca **Invia al R.U.S.E. Studio**, poi **Riporta le mie modifiche** (oppure esporta il tuo
   file e clicca **Importane un altro…**). **Funzionerà nel gioco?** controlla di nuovo il modello.

**Troppe ossa.** «Il tuo modello ha {n} ossa. Il gioco non è stato visto animare un modello con più di 64 ossa.» In
Blender unisci o cancella ossa finché ne ha 64 o meno, poi riporta il modello.

**La divisione.** «La divisione a {bone}, il primo osso del tuo modello, mette tutte le ossa nella metà superiore,
quindi le animazioni della metà inferiore (camminare, correre) non muovono nulla.»: scegli un osso più in basso sotto
**Le sue due metà**, dove comincia la parte alta del corpo. «L'osso scelto per la divisione, {bone}, non è più nel tuo
modello, quindi si divide a {used}.»: scegli di nuovo l'osso.

**Il secondo modello di una squadra su altre ossa.** «Il suo modello ha ossa proprie che non sono quelle del modello dei
tuoi fucilieri: esegue quindi ciò che eseguiva nell'unità copiata, fatto sulle ossa del soldato del gioco, e questo può
fermare il gioco.» Il modello di un soldato con l'arma pesante deve essere sulle stesse ossa di quello dei fucilieri per
usare le loro animazioni: fai il suo partendo dal modello dei fucilieri in Blender, poi importalo sulla sua riga.
Togliere il modello dei fucilieri toglie anche il suo.

## Fare un modello con ossa sue in Blender

1. **Le sue ossa:** il tuo modello su un'armature con ossa tue, chiamate come vuoi, e i suoi pesi
   (**Ctrl+P > With Automatic Weights**, sopra).
2. **Le sue animazioni:** un'action per ogni animazione (in Blender, **Dope Sheet > Action Editor**). Chiama ognuna per
   ciò che mostra: almeno **stand** (o **idle**), **walk** e **run** (o **gallop**); anche **fire**, **aim**,
   **reload**, **hit**, **death**, **crouch**, **look**, **flee** e **grenade** sono riconosciuti. Un nome come
   **t_fire** (o **hr_t_fire**) si riproduce solo sulla metà superiore, e **b_run** (o **hr_b_run**) solo su quella
   inferiore: quelli di un cavaliere e del suo cavallo.
3. **Esportalo:** **File > Export > glTF 2.0**, formato **glTF Binary (.glb)**, con **Animation** spuntato.
4. **Importalo** su una nuova squadra: vedi [[Importare un modello|Importare-un-modello]].
5. **Controlla la sua pagina:** **Le sue ossa e animazioni** (ogni animazione è arrivata, e quante azioni usano
   ognuna), **Le sue due metà**, **Le sue animazioni**, **Funzionerà nel gioco?**
6. **Prova in gioco.**

L'hai cambiato poi in Blender? Importalo di nuovo: ogni azione tiene la sua animazione finché nel file c'è ancora
un'animazione con quel nome.

## Cosa è stato provato nel gioco

- La Squadra a cavallo generica, fatta così (fucilieri e un soldato con bazooka a cavallo, un modello con ossa sue):
  sparano, viaggiano come se stessi nei lunghi spostamenti, e ogni cavallo cade col suo cavaliere (novembre 2026).
- Un soldato di una squadra cambiato in Blender sulle ossa del soldato del gioco, con punti pesati lì (novembre 2026).
- Non ancora provato nel gioco: una divisione diversa da quella suggerita, e ogni problema che la pagina segna «non
  ancora provato nel gioco».

Ancora bloccato? Chiedi sul [Discord](https://discord.gg/h54t5baNsC), oppure vedi
[[Quando qualcosa va storto|Quando-qualcosa-va-storto]].

**Avanti:** [[Animazioni delle unità|Animazioni-delle-unità]] · [[Apri in Blender|Apri-in-Blender]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Models-and-Bones]]
