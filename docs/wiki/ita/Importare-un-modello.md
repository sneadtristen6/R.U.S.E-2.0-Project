# Importare un modello

> **Per:** modder · **Ti serve:** RUSE Studio 0.9.6 o successivo, una mod e un modello 3D (.3ds, .glb o .gltf) ·
> **Tempo:** qualche minuto

Dai a una nuova unità un modello 3D tutto suo, da Blender o da qualsiasi altro programma 3D. È così che è stata fatta la
[mod M1 Abrams](https://github.com/sneadtristen6/Ruse-Mods): il primo modello portato in R.U.S.E. da un altro programma 3D,
visto in gioco.

Un modello può anche andare su un nuovo edificio, al posto di un pezzo del suo aspetto (vedi
[[Edifici e menu di costruzione|Edifici-e-menu-di-costruzione]]), o sulla tua mappa come una roccia, un oggetto, un cespuglio o
un albero tuo (vedi [[Posizionare edifici e alberi|Posizionare-edifici-e-alberi]]). Entrambi: Studio 0.9.8.8, visti in gioco.

Nella pagina dell'unità tutto questo è in **Aspetto e movimenti**: **Importa modello…** è il pulsante della riga **Modello**, e il resto delle opzioni del modello (la dimensione, **Spostalo**, **Cambialo in Blender**) è sotto **Altro** di quella riga. **I suoi soldati** è una riga a sé, e cosa fanno le animazioni del modello è sotto **Altro** della riga **Suoni e animazioni**.

## 1. Procurati un modello

Un **.3ds** con le sue immagini (.tga o .png), oppure un **.glb** o **.gltf** (immagini al suo interno: PNG, JPG o WebP).
Un modello che l'importatore non sa leggere (mesh compresse, immagini KTX2) lo dice, e dice come sistemarlo in Blender.

- **Da Blender:** File > Export > glTF 2.0, formato **glTF Binary (.glb)**.
- **Da un sito di modelli gratuiti:** molti carri armati arrivano come .3ds con una cartella di immagini .tga. Tieni la
  cartella com'è arrivata: lo Studio trova le immagini accanto al .3ds o nella cartella sopra, anche con i nomi accorciati
  che usano i file .3ds (`MAIN_DEF.TGA` per `Main_Defuse.tga`).
- Controlla la licenza del modello prima di condividere la tua mod, e cita il suo autore nel README della tua mod.

**Cosa aiuta:** parti con il nome di ciò che sono. Lo Studio fa girare con la torretta una parte che ha *turret* nel nome (o
*tourelle*, *tower*), e anche una con *barrel*, *gun* o *cannon*. Anche una parte appoggiata sulla torretta gira con
essa. Tutto il resto si muove con lo scafo. Il cannone deve puntare dritto in avanti.

L'esempio dell'Abrams: **"Tank Abrams" di ags**, gratuito su
[downloadfree3d.com](https://downloadfree3d.com/3d-models/vehicles/tank/tank-abrams/) (un .3ds e le sue immagini .tga,
parti chiamate Main_Body, Main_Turre, Main_Barre...).

## 2. Crea l'unità

Nella scheda **Unità**, clicca su **Nuova unità (importa un modello)** in alto, poi scegli l'unità da cui partire (per un
carro armato, un carro armato: lo Sherman per l'Abrams). Dalle un nome e clicca su **Crea**: la pagina della nuova unità si
apre su **Importa modello…**. Il modello della nuova unità girerà e si muoverà come quello di questa unità. La pagina di
un'unità del gioco ha lo stesso ingresso: **Nuova unità da questa…** sulla riga **Modello** di **Aspetto e movimenti**. (Lo Studio 0.9.6 non
ha ancora nessuno dei due pulsanti: apri l'unità e scegli **Nuova unità…** nella sua pagina.)

## 3. Importa

Nella pagina della nuova unità, sulla riga **Modello** di **Aspetto e movimenti**:

1. Clicca **Altro** e imposta **Dimensione**: la sua lunghezza rispetto a quella dell'unità copiata. **1** è lunga uguale; un M1 Abrams
   rispetto a uno Sherman è **1.36** (le loro lunghezze reali).
2. Clicca su **Importa modello…** (il pulsante della riga) e scegli il .3ds o il .glb.

Lo Studio lo adatta all'unità: rivolto in avanti (dove punta il suo cannone), la sua lunghezza, messo dove sta l'unità
copiata, con la torretta che gira dove si trova sul tuo modello, appoggiato a terra. Le sue immagini diventano texture
sue. La pagina lo mostra in 3D, con le parti che girano con la torretta. Se un'immagine non è stata trovata, dice quale:
metti le immagini accanto al modello e importa di nuovo.

Viene salvato nella tua mod come `files/models/<the unit's name>.glb`. **Usa il modello dell'unità copiata** lo toglie di
nuovo.

**La sua dimensione in seguito:** il cursore sotto il riquadro della dimensione va da **Minuscolo** a **Enorme** (da 0.05 a
20), con **Dimensione del gioco** (1) e, per un'unità d'epoca, **Dal vero** segnati; clicca su **Ridimensiona** e il modello
viene adattato di nuovo dal suo file. Con diversi nuovi aerei (o unità di terra), un clic li ridimensiona tutti. Il gioco
legge un modello quando carica, quindi una nuova dimensione si vede dalla build successiva.

**Dove sta:** un nuovo modello viene messo al centro dell'unità che copia, quindi alla maggior parte dei modelli qui non
serve niente. Se il tuo non è al posto giusto, usa **Spostalo** sotto la dimensione, in **Altro** della riga
Modello. Chiede tre numeri, **Avanti**, **Destra** e **Su**, in unità del gioco (la pagina dice quanto
è lunga l'unità copiata, in queste unità). Un meno va dall'altra parte, e 0, 0, 0 lo rimette dove era stato adattato.
Clicca su **Sposta** e il modello viene adattato di nuovo dal suo file, spostato di tanto; la torretta e le eliche vanno
con lui, così girano ancora nel punto giusto. Nella vista 3D l'anello blu è dove sta l'unità copiata, e il segno
sull'anello è il davanti. Una nuova dimensione mantiene lo spostamento. Un modello legato alle ossa dell'unità (un
soldato, i serventi di un cannone) resta dove sono le sue ossa: quello spostalo in Blender. Un modello importato prima
dello Studio 0.9.8.17 mantiene il suo vecchio posto (la torretta sulla torretta dell'unità copiata), anche
ridimensionato, finché non lo importi di nuovo o lo sposti; i modelli delle unità d'epoca mantengono il loro.

**Aerei:** un aereo aperto in Blender dallo Studio e riportato indietro è rivolto in avanti e mantiene le eliche dove le
ha il tuo modello, quante ne ha, qualunque cosa avesse l'aereo che copia: pale a terra, dischi che girano in volo. Visto
in gioco. Un modello preso altrove mantiene le eliche come sono disegnate, ferme: l'importatore non sa ancora
riconoscere quali sue parti sono eliche. Nella vista 3D i dischi di un aereo si vedono trasparenti, come il gioco
disegna un'elica che gira.

**Soldati, serventi e altri aerei:** i soldati, i serventi di un cannone e gli aerei a cui prima lo Studio non sapeva
adattare un modello (il P-47, per esempio) prendono anche loro un modello tutto loro, se è legato alle ossa dell'unità:
per esempio uno dei modelli del gioco aperto in Blender dallo Studio e cambiato lì. Va su quelle ossa così com'è, senza
spostare né scalare niente, e anche gli altri uomini di una squadra disegnati con lo stesso modello lo indossano. Visto in gioco con
una squadra di fucilieri, i serventi di un cannone e il P-47. Un soldato con arma pesante che il gioco disegna con un
modello suo (l'uomo col bazooka della squadra di fucilieri USA) lo tiene finché non gliene dai uno sotto
**I suoi soldati** (più sotto).

**I tuoi giocatori:** una mod con un modello importato dallo Studio 0.9.8.17 o successivo richiede il Launcher 0.4.8.17
o più recente: un Launcher più vecchio dà al modello lo scheletro dell'unità copiata, così la torretta gira attorno al
punto sbagliato. La 0.4.8.17 è un aggiornamento obbligatorio, quindi il Launcher lo installa da solo.

## Il tuo soldato, passo per passo

Per una squadra (fucilieri, paracadutisti, qualsiasi fanteria) lo Studio fa con te la parte in Blender:

1. **Crea la squadra** come al passo 2 qui sopra, partendo da una squadra (i fucilieri americani, per esempio).
2. **Apri il suo soldato in Blender.** Nella pagina della nuova squadra, sotto **Un modello tutto suo**, clicca **Cambialo in Blender**. Blender si apre con il soldato e le sue ossa, ognuna dove la mette il gioco. Non hai ancora Blender? **Scarica Blender (gratis)** lo installa; **Scegli Blender…** mostra allo Studio dov'è.
3. **Modificalo, o metti il tuo modello sulle sue ossa.** Per modificarlo, lavoralo lì. Per un tuo modello: importalo con **File > Import** nella stessa scena e posalo sul soldato; clicca il tuo modello, **Maiusc+clic** sulle ossa, poi **Ctrl+P > With Automatic Weights**. Elimina il soldato del gioco se non lo tieni.
4. **Invialo.** Clicca **Invia al R.U.S.E. Studio** in alto in Blender.
5. **Riportalo.** Nello Studio clicca **Riporta il modello**. I fucilieri della squadra indossano il tuo modello. Una squadra il cui soldato con arma pesante il gioco disegna con un modello suo (l'uomo col bazooka della squadra di fucilieri USA, per esempio) lo tiene come lo ha la squadra copiata finché non gliene dai uno: la riga **I suoi soldati** mostra ognuno di loro, e il suo **Importa modello…** è solo per lui. **Prova in gioco** lo mostra.

Buono a sapersi:
- I tuoi file di Blender restano nella cartella della tua mod: `Documents\RUSE 2.0\Mods\<la tua mod>\blender\<nome dell'unità>\`. Non vengono messi nella mod quando la condividi. Il prossimo **Cambialo in Blender** riparte da ciò che hai inviato per ultimo.
- Se alcuni punti del tuo modello non hanno un osso (i pesi automatici di Blender ne saltano qualcuno), la pagina dice quanti: si muovono solo con i fianchi del soldato. Dipingili su un osso in **Weight Paint** e invia di nuovo.
- Una squadra con **Uniforme personalizzata**: il tuo modello prende il posto dell'uniforme (i suoi colori restano nella mod), e **Usa il modello dell'unità copiata** rimette l'uniforme.
- Hai già un .glb fatto sulle ossa del soldato del gioco? **Importa modello…** lo prende così com'è.
- Il modello che indossa la tua squadra è tenuto nella cartella della mod come `files\models\<nome dell'unità>.glb`, una volta dentro; quello del soldato con arma pesante come `files\models\<nome dell'unità>@bazooka.glb`.
- **I suoi soldati** dice anche quali altre figure della squadra sono disegnate con ciascun modello: il soldato caduto, e la figura vista da lontano (quella della squadra di fucilieri USA è disegnata col modello del suo uomo col bazooka).

## Le sue animazioni: quale esegue ogni azione

Un modello su ossa proprie (un cavallo, un cavallo col suo cavaliere, qualsiasi creatura) porta con sé le sue
animazioni. Nella pagina dell'unità, **Le sue animazioni** mostra cosa esegue l'unità per ogni cosa che fa in gioco:

- **Sta fermo**, **Cammina** e **Corre** vengono per prime: il minimo che serve a un modello. Se una di esse non ha
  niente di suo, la pagina lo dice, e cosa esegue al suo posto.
- Ogni azione è una lista delle animazioni del modello. Scegline una, o lasciala su **Più vicina**: esegue allora
  quella del modello più somigliante, e la lista dice quale. Più vicina vuol dire, nell'ordine: un'animazione col nome
  di quell'azione (stand o idle, walk, run o gallop, fire, death...), altrimenti quella che esegue l'azione più vicina
  (una camminata la corsa, una corsa la camminata, poi la posa ferma; uno sparo la mira, poi la posa ferma; ogni morte
  la morte semplice). La build segue la stessa regola: ciò che dice la pagina è ciò che esegue il gioco.
- Un'animazione il cui nome inizia con t_ o b_ (hr_t_fire, hr_b_run) si esegue solo sulla metà superiore o inferiore
  del corpo: quelle di un cavaliere sopra, quelle del suo cavallo sotto.
- **Tutte le altre azioni** elenca il resto, per tipo: fermo, in movimento, mirare e sparare, l'arma pesante, essere
  colpiti, morire.
- **Nei lunghi spostamenti** il gioco mette una squadra nel suo camion. Un'unità con animazioni sue va invece da sé,
  eseguendo l'animazione scelta lì (la sua corsa se lasci Più vicina), veloce quanto il suo camion. Scegli **Nel suo
  camion** per tenere il camion.

**Una copia tiene le sue animazioni:** un'unità copiata da una con animazioni sue esegue le stesse. Per cambiarne una
solo per lei, clicca **Cambia in RUSE Decoy** sulla sua riga **Suoni e animazioni**, poi **Solo questa unità**.

La Horse Squad fatta così nello Studio è stata giocata (novembre 2026).
## Un modello con ossa e animazioni tutte sue

Un cavallo, un cavallo con il suo cavaliere, qualsiasi creatura: un modello sulle sue ossa va su una squadra con le sue animazioni.

1. **Fallo in Blender**: il tuo modello su un'armatura con ossa tue (chiamate come vuoi) e un'azione per ogni animazione. Chiama le azioni come ciò che mostrano: almeno **stand** (o **idle**), **walk** e **run**; si riconoscono anche **death**, **fire**, **reload**, **hit**, **crouch**, **aim**, **look**, **flee** e **grenade**.
2. **Esportalo**: **File > Export > glTF 2.0**, formato **glTF Binary (.glb)**, con **Animation** spuntato.
3. **Crea la squadra** come al passo 2 sopra. Sulla sua pagina, clicca **Importa modello…** sulla riga **Modello** di **Aspetto e movimenti** e scegli il tuo .glb. Lo Studio vede che le sue ossa non sono quelle del soldato e lo prende con le sue ossa e tutte le sue animazioni. La pagina mostra quante ossa ha, ogni animazione con la sua durata e quante azioni della squadra la fanno.
4. **Prova in gioco** lo mostra.

Buono a sapersi:
- Ogni azione della squadra fa l'animazione chiamata per lei. Un'azione per cui nessuna animazione è chiamata non ne ha ancora: la pagina dice quante.
- Cambiato in Blender? Importalo di nuovo: ogni azione tiene la sua animazione finché nel file c'è ancora un'animazione con quel nome.
- Il tuo mod tiene il modello e ogni animazione: `files\models\<nome dell'unità>.glb`, e ogni animazione come `files\anim\own\<nome dell'unità>\<il suo nome>.baf`.
- **Usa il modello dell'unità copiata** toglie di nuovo il modello, con le sue animazioni.
- Una squadra con un soldato con arma pesante: dagli il suo cavallo con cavaliere sotto **I suoi soldati**, fatto sulle stesse ossa di quello dei fucilieri, ed esegue le loro animazioni. Su altre ossa esegue ciò che eseguiva nella squadra copiata, e la pagina ti avvisa: questo può fermare il gioco. Togliere il modello dei fucilieri toglie anche il suo.
- La Horse Squad fatta così nello Studio è stata giocata (novembre 2026); nient'altro fatto così è ancora stato provato in gioco.

## 4. La sua scheda, poi la prova

Ruota la vista 3D finché il nuovo modello non sta bene nella cornice tratteggiata e clicca su **Usa questa vista come
scheda** (vedi [[Modificare le unità|Modificare-le-unità]]). Poi **Prova in gioco**: l'unità è nella sua fabbrica in una battaglia.

## Cambialo in Blender

`files/models/<the unit's name>.glb` si apre in Blender come qualsiasi .glb. Tieni i due nomi degli oggetti (`chassis` per lo
scafo, `tourelle_01` per la torretta) ed esportalo sopra lo stesso file (glTF Binary): la build successiva lo usa.

**Apri in Blender** nella pagina di un'unità chiama l'osso di ogni parte come fa il gioco, così uno dei carri armati del
gioco aperto in Blender e importato di nuovo mantiene la torretta che gira (Studio 0.9.8.8; un modello esportato prima
mantiene i suoi vecchi nomi: aprilo di nuovo in Blender).

**Un modello che stava nel posto sbagliato** (Studio 0.9.8.7 e precedenti, su nuove unità fatte dal Panther e da altre 85
unità di cui lo Studio leggeva male la torretta): usa di nuovo **Importa modello…** su quell'unità, e si appoggia sulla
torretta.

## In fase iniziale

- Cingoli e ruote per ora non girano: si muovono con lo scafo.
- Il lampo del cannone e il relitto sono quelli dell'unità copiata.
- Le immagini vengono fatte larghe al massimo 1024, come le immagini delle unità del gioco stesso.
- Provato in gioco con i modelli del gioco stesso (lo Sherman, due aerei, una squadra di fucilieri, i serventi di un
  cannone): non ancora con un modello preso altrove, un altro carro armato con torretta, una torretta che fa il giro
  completo o un aereo che copia un'unità senza eliche.

Dalla riga di comando: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. Con `--move`, viene adattato come lo adatta lo
Studio: `--move 50 0 -10` lo sposta di 50 in avanti e di 10 in basso da dove è adattato (avanti, destra, su), e
`--move 0 0 0` lo lascia lì. Senza `--move`, il comando lo adatta ancora alla vecchia maniera, con la torretta sulla
torretta dell'unità copiata.

**Avanti:** [[Esportare e condividere|Esportare-e-condividere]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Import-a-Model]]
