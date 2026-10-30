# Importare un modello

> **Per:** modder · **Ti serve:** RUSE Studio 0.9.6 o successivo, una mod e un modello 3D (.3ds, .glb o .gltf) ·
> **Tempo:** qualche minuto

Dai a una nuova unità un modello 3D tutto suo, da Blender o da qualsiasi altro programma 3D. È così che è stata fatta la
[mod M1 Abrams](https://github.com/sneadtristen6/Ruse-Mods): il primo modello portato in R.U.S.E. da un altro programma 3D,
visto in gioco.

Un modello può anche andare su un nuovo edificio, al posto di un pezzo del suo aspetto (vedi
[[Edifici e menu di costruzione|Edifici-e-menu-di-costruzione]]), o sulla tua mappa come una roccia, un oggetto, un cespuglio o
un albero tuo (vedi [[Posizionare edifici e alberi|Posizionare-edifici-e-alberi]]). Entrambi: Studio 0.9.8.8, visti in gioco.

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
un'unità del gioco ha lo stesso ingresso: **Nuova unità da questa…** sotto **Un modello tutto suo**. (Lo Studio 0.9.6 non
ha ancora nessuno dei due pulsanti: apri l'unità e scegli **Nuova unità…** nella sua pagina.)

## 3. Importa

Nella pagina della nuova unità, sotto **Un modello tutto suo**:

1. Imposta **Dimensione**: la sua lunghezza rispetto a quella dell'unità copiata. **1** è lunga uguale; un M1 Abrams
   rispetto a uno Sherman è **1.36** (le loro lunghezze reali).
2. Clicca su **Importa modello…** e scegli il .3ds o il .glb.

Lo Studio lo adatta all'unità: rivolto in avanti (dove punta il suo cannone), la sua lunghezza, l'anello della sua torretta
sulla torretta dell'unità copiata, appoggiato a terra. Le sue immagini diventano texture sue. La pagina lo mostra in 3D,
con le parti che girano con la torretta. Se un'immagine non è stata trovata, dice quale: metti le immagini accanto al
modello e importa di nuovo.

Viene salvato nella tua mod come `files/models/<the unit's name>.glb`. **Usa il modello dell'unità copiata** lo toglie di
nuovo.

**La sua dimensione in seguito:** il cursore sotto il riquadro della dimensione va da **Minuscolo** a **Enorme** (da 0.05 a
20), con **Dimensione del gioco** (1) e, per un'unità d'epoca, **Dal vero** segnati; clicca su **Ridimensiona** e il modello
viene adattato di nuovo dal suo file. Con diversi nuovi aerei (o unità di terra), un clic li ridimensiona tutti. Il gioco
legge un modello quando carica, quindi una nuova dimensione si vede dalla build successiva.

**Aerei:** un aereo aperto in Blender dallo Studio e riportato indietro mantiene le sue eliche che girano ed è rivolto in
avanti. Visto in gioco.

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

Dalla riga di comando, la stessa cosa: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`.

**Avanti:** [[Esportare e condividere|Esportare-e-condividere]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Import-a-Model]]
