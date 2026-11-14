# Apri in Blender

> **Ti serve:** RUSE Studio 0.9.8.20 o successivo, una mod e Blender (gratis) · **Tempo:** 5 minuti di lettura

**Apri in Blender** porta un'unità in Blender, il programma 3D gratuito, per cambiarne la forma, le ossa o la pittura;
**Riporta le mie modifiche** mette nella tua mod ciò che ci hai fatto. È un solo pulsante per tutta l'unità: **Cosa va
in Blender**, accanto, dice cosa parte, e tutto ciò che togli dalla spunta resta com'è. Questa pagina lo percorre passo
passo.

Le animazioni non si cambiano con questo pulsante: si cambiano in RUSE Decoy (vedi
[[Animazioni delle unità|Animazioni-delle-unità]]). Le animazioni proprie di un modello vanno in Blender con lui e
tornano con lui.

## Dov'è il pulsante

| L'unità | Dove | Cosa torna |
|---|---|---|
| Una squadra che hai fatto tu (una nuova unità della tua mod) | Il grande **Apri in Blender** sulla sua scheda, in cima alla sua pagina | I suoi soldati, ognuno per conto suo; la loro pittura |
| Qualsiasi altra unità che hai fatto (un carro, un aereo) | **Aspetto e movimenti**, la riga **Modello**, **Altro**: il riquadro **Cambialo in Blender** | Tutto il suo modello (anche le ossa, se sono sue), la sua pittura |
| Un'unità del gioco (non una squadra) | Lo stesso riquadro | Solo la sua pittura: dipingici sopra, il resto resta quello del gioco |
| Una squadra del gioco | La sua scheda dice di fare prima una nuova unità da essa: **Nuova unità da questa…** | Solo la sua **Uniforme personalizzata**, dipinta dalla sua riga **Uniforme** (**Apri in Blender**, poi **Riporta**) |

Niente Blender su questo PC? La pagina mostra **Scarica Blender (gratis)**, che apre la pagina di download di Blender, e
**Scegli Blender…**, per mostrare allo Studio dov'è `blender.exe` se ce l'hai già.

## Cosa va in Blender

Clicca **Cosa va in Blender ▾** accanto al pulsante. All'inizio è tutto spuntato. Togli la spunta a una parte per
tenerla com'è: **Riporta le mie modifiche** allora la lascia com'era, qualunque cosa Blender le abbia fatto.

| Vedi | Vuol dire |
|---|---|
| **I suoi soldati**, poi ogni soldato («Fuciliere 1», «Soldato con bazooka 5»...) | I soldati spuntati si aprono fianco a fianco in un solo Blender. Cambia quello che vuoi: cambia solo quello che cambi. |
| **Quale modello:** **Il modello dei fucilieri** o **Il modello del soldato con l'arma pesante** | Una squadra con ossa sue (la Squadra a cavallo generica): un modello alla volta, con le sue ossa e animazioni. |
| **Il suo modello** | La forma dell'unità (un'unità che non è una squadra). |
| **Le sue ossa** | Le sue ossa (solo un modello con ossa sue). Senza spunta, le ossa della tua mod vengono rimesse com'erano. |
| **La sua pittura** | Le sue immagini. Senza spunta, le immagini della tua mod vengono rimesse com'erano. |

Buono a sapersi:

- **Solo la sua pittura** (il suo modello, o ogni soldato, senza spunta): Blender si apre con le immagini da dipingere, e
  torna solo la pittura. È così che si dipinge l'**Uniforme personalizzata** di una squadra, per tutti i soldati insieme.
  Una squadra con l'uniforme predefinita non può: «Scegli prima Uniforme personalizzata» (l'uniforme predefinita è
  indossata anche da altre squadre ed equipaggi). Scegli prima **Uniforme personalizzata** sulla sua riga **Uniforme**,
  in **Aspetto e movimenti**.
- **Le sue ossa** senza spunta, ma in Blender un osso è stato aggiunto, tolto o rinominato: le ossa non possono essere
  tenute, quindi tornano come le ha inviate Blender, e lo Studio lo dice.
- Una squadra di soldati del gioco non ha **Le sue ossa**: i suoi soldati tornano sulle ossa del soldato del gioco,
  qualunque cosa Blender abbia fatto loro.
- Niente spuntato: lo Studio dice «Spunta prima cosa va in Blender: il modello, le sue ossa o la sua pittura.»

## Andata e ritorno, passo passo

1. **Aprilo.** Clicca **Apri in Blender**. Blender si apre (ci vuole qualche secondo), con ciò che hai spuntato.
2. **Cambialo.** Dipingi, cambia la forma, metti un tuo modello sulle ossa di un soldato (vedi
   [[Modelli e ossa|Modelli-e-ossa]], «I pesi»). Le poche cose da sapere sono scritte in cima alla vista 3D di Blender.
3. **Invialo.** Clicca **Invia al R.U.S.E. Studio** in alto a sinistra nella vista 3D di Blender.
4. **Riportalo.** Nello Studio il pulsante ora dice **Riporta le mie modifiche**: cliccalo. La pagina dice cosa è
   arrivato: chi è cambiato e chi no in una squadra, il file del modello in ogni altra unità, e cosa, senza spunta, è
   stato tenuto.
5. **Prova in gioco** lo mostra.

Puoi tenere Blender aperto e fare un altro giro: cambiare, inviare, riportare.

## Riporta le mie modifiche

- **Blender ancora aperto?** **Riporta le mie modifiche** gli chiede prima di inviare, e lo aspetta (fino a un minuto).
- **Chiudi Blender?** Clicca prima **Invia al R.U.S.E. Studio**: ciò che non hai inviato resta in Blender, e lo Studio
  non lo vede mai.
- **L'hai chiuso dopo aver inviato?** Il pulsante dice **Riporta le mie modifiche** finché non lo clicchi, e prende ciò
  che hai inviato per ultimo. Sulla scheda di una squadra, un invio fatto dopo l'ultimo ritorno (o dopo **Aggiungi un
  soldato**) appare come un piccolo **Riporta le mie modifiche** sotto il pulsante grande, una volta chiuso Blender:
  prende ciò che hai inviato per ultimo.
- **Ancora niente inviato:** «Da Blender non è ancora tornato nulla: in Blender clicca Invia al R.U.S.E. Studio in alto,
  poi Riporta le mie modifiche qui.»
- Un Blender alla volta per un'unità: finché Blender ce l'ha, il pulsante dello Studio dice **Riporta le mie
  modifiche**.

## Un invio messo da parte

Un **invio** è ciò che Blender ha mandato con **Invia al R.U.S.E. Studio**. Se riapri Blender prima di aver riportato
l'ultimo invio:

- **Una squadra:** quell'invio viene messo da parte nella cartella Blender della tua mod, in una cartella chiamata
  `sent-not-brought-` seguita da data e ora, e il nuovo Blender parte da ciò che ha la tua mod. Non si perde nulla, ma
  la scheda non lo dice ancora, e non ha un pulsante per riportarlo: i file sono in
  `Documents\RUSE 2.0\Mods\<la tua mod>\blender\<nome dell'unità>\squad\`.
- **Qualsiasi altra unità, col suo modello spuntato:** non si mette da parte nulla: il prossimo **Apri in Blender**
  parte da ciò che hai inviato per ultimo.
- **Le animazioni di RUSE Decoy:** ogni invio messo da parte è elencato sopra le animazioni dell'unità («Inviato da
  Blender, mai riportato, messo da parte il ...»), con **Riporta l'invio messo da parte** per prenderlo, o **Mettilo nel
  Cestino**.

## Dove sono i tuoi file di Blender

Nella cartella della tua mod, `Documents\RUSE 2.0\Mods\<la tua mod>\blender\<nome dell'unità>\`: quelli della squadra
in `squad`, quelli di RUSE Decoy in `animations`. Non vengono messi nella tua mod quando la esporti. Nella pagina di una
squadra, **Altre opzioni** dice dove sono, con **Mostra nella cartella**.

## Cosa può andare storto

| Cosa succede | Perché, e cosa fare |
|---|---|
| Blender si apre vuoto | Guarda nella finestra di Blender se c'è un errore (**Window > Toggle System Console**), e diccelo sul Discord. |
| Un soldato che non ho toccato risulta cambiato | Tutto ciò che è diverso conta come cambiato, anche un oggetto rinominato. Il suo aspetto resta com'era. |
| «Non è su nessun soldato, quindi non inviato: ...» | Qualcosa che hai portato in Blender non è né sulle ossa di un soldato né nella sua collezione: mettilo su di lui, poi invia di nuovo. |
| Un punto del mio modello si muove solo con i fianchi | Non ha un osso: vedi [[Modelli e ossa|Modelli-e-ossa]], «Punti senza osso». |
| Delle parti hanno perso la lucentezza o il colore di fazione | La pagina le nomina: un materiale rinominato o nuovo in Blender torna semplice. Tieni i nomi dei materiali con cui Blender si è aperto. |
| La nuova forma della mia unità del gioco non è tornata | Su un'unità del gioco torna solo la pittura. Fai una nuova unità da essa per cambiarne la forma. |

## Cosa è stato provato nel gioco

- La pittura da Blender su un'unità, vista da vicino e da lontano.
- Una squadra aperta in Blender, un soldato cambiato e riportato da solo (novembre 2026).
- Non ancora provato nel gioco: tutto il modello di un carro passato per Blender, e ciò che **Cosa va in Blender**
  tiene (provato con Blender e lo Studio, fuori dal gioco).

Ancora bloccato? Chiedi sul [Discord](https://discord.gg/h54t5baNsC), oppure vedi
[[Quando qualcosa va storto|Quando-qualcosa-va-storto]].

**Avanti:** [[Cambiare una squadra|Cambiare-una-squadra]] · [[Modelli e ossa|Modelli-e-ossa]] ·
[[Animazioni delle unità|Animazioni-delle-unità]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Open-in-Blender]]
