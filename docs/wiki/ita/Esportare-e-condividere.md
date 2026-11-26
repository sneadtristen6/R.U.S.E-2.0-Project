# Esportare e condividere

> **Per:** modder · **Ti serve:** RUSE Studio e una mod finita · **Tempo:** 5 minuti

## 1. Esporta

1. Apri il menu **Mod** e scegli **Esporta mod…**.
2. Compila la **versione** (tre numeri, come `1.0.0`), il tuo nome e una riga su cosa fa la mod.
3. Scegli dove salvare. Lo Studio costruisce la mod una volta sul tuo gioco, per registrare la build del gioco su cui è stata
   fatta e la sua **impronta** (un breve codice che è lo stesso per tutti quelli che hanno le stesse mod), poi salva un solo
   file: `<your-mod>-<version>.rusemod`.

Quel file è tutto ciò che serve a un giocatore: lo aggiunge in RUSE Launcher ([[Installare e giocare|Installare-e-giocare]]).

**Mod di mappe grandi:** una mappa cambiata ovunque può richiedere alla build minuti di calcoli (dove le unità possono andare
sul terreno che hai aperto, per esempio). Lo aspetti una volta sola. L'esportazione mette nel file ciò che la build ha
calcolato, così la prima build di un giocatore è più breve. Contiene solo numeri nostri, mai un file del gioco, ed è
bloccato con il file del gioco stesso per quella mappa: si apre solo su un PC che ha il gioco. Per ora solo il movimento;
non ancora visto in gioco.

Quando l'esportazione è finita, lo Studio apre **Condividi la tua mod** con la dimensione del file, il suo checksum SHA-256 e la
sua voce per l'elenco, pronta da copiare. Puoi riaprirlo quando vuoi dal menu **Mod** (**Condividi la tua mod…**).

**Cosa entra:** il README, i crediti, la licenza e la cartella `docs` della tua mod vengono impacchettati con essa, e tutto il tuo nome utente di Windows viene tolto dal README. Una mod troppo grande per il Launcher viene rifiutata prima di impacchettare qualsiasi cosa. Se l'esportazione sostituisce un file, dice quale. Se un file della vecchia copia della mod nella libreria del Launcher è aperto in un altro programma, l'esportazione arriva comunque in fondo, dice che la mod non è stata aggiunta alla libreria e nomina il file da chiudere.

## 2. Condividi: aggiungila alle mod supportate

Hai fatto una mod? Aggiungila all'elenco e diventa un contributore. La scheda **Mod supportate** di RUSE Launcher mostra le
mod dell'elenco su [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods), e i giocatori le installano con un
clic (ai nuovi giocatori vengono proposte al primo avvio del launcher):

1. Carica il `.rusemod` (una Release di GitHub è il modo più facile: del tuo repository, o di quello dell'elenco).
2. Apri una pull request su [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods) che aggiunge la voce della
   tua mod a `index.toml`: incolla la voce che mostra Condividi la tua mod e metti il link del file in `download`. La
   dimensione e lo SHA-256 devono essere quelli mostrati dall'esportazione: il launcher rifiuta un download che non
   corrisponde, così nessuno può scambiare il tuo file con un altro.
3. Oppure pubblicala in [Discussions > Mods & maps](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) con
   uno screenshot e cosa cambia (trascina il `.rusemod` nel post), e viene aggiunta all'elenco per te.

Un trucco o uno strumento di prova (unità gratis, costruzione istantanea...) riceve l'etichetta `"cheat"`: il launcher lo
mostra in un gruppo a parte, «Trucchi e strumenti di prova (facoltativi)», e non lo spunta né lo scarica mai se non lo fa il
giocatore. Una nuova versione è un nuovo file con un nuovo numero di versione: un file pubblicato non cambia mai.

Il formato esatto della voce:
[MOD_FORMAT.md, sezione 15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/docs/MOD_FORMAT.md#15-the-mod-index-supported-mods).

## Modifica una mod installata

Nel menu della mod dello Studio, **Modifica una mod installata…** elenca ogni mod che ha il Launcher (con un riquadro di
ricerca). Una mod tua apre il suo progetto. Quella di qualcun altro diventa una tua copia con un nome suo (non può prendere il
nome dell'originale): le tue modifiche vanno lì, e un aggiornamento dell'originale non le cancella mai. Una mod di RUSE Mod
Manager (`.rmod`) viene convertita nella sua copia, così le sue modifiche ai valori diventano modifiche dello Studio che
puoi cambiare.

## Mostrare la cartella di una mod, o eliminare una mod

Nel menu della mod dello Studio, **Mostra la cartella di questa mod** apre la cartella della mod che stai modificando, ed **Elimina una mod…** elenca le tue mod e modifiche alle mappe: **Elimina** ne manda una nel Cestino (da cui puoi recuperarla) e, se lo spunti, anche la sua copia nel Launcher. Una cartella aperta da un altro posto viene solo tolta dall'elenco. **Impostazioni → Dove sono i tuoi file** mostra dove si trova tutto ([[Cartelle e file delle mod|Cartelle-e-file-delle-mod]]). In RUSE Launcher, **Rimuovi** manda anch'esso una mod della libreria nel Cestino, e **Mostra nella cartella** apre la sua cartella.

## Cosa può contenere una mod

In alcuni casi i dati del gioco possono essere cambiati, ma ciò avviene con la tua copia del gioco: una mod cambia i
dati (numeri, testi, mappe, modelli, texture) della copia moddata che le app costruiscono, e alcune mod cambiano lì gli
script del gioco, come gli script delle missioni che lo Studio salva. Quegli script girano dentro il gioco e possono
fare tutto ciò che può fare il gioco, quindi installali solo da autori di cui ti fidi
([SECURITY.md](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/SECURITY.md)). I programmi (`.exe`,
`.dll`, script che girano su un PC) sono rifiutati da entrambe le app.

## Buone abitudini

- Tieni la cartella della tua mod: il `.rusemod` è per i giocatori, la cartella è ciò che modifica lo Studio.
- Scrivi nel tuo post di quali altre mod ha bisogno la tua o con quali va in conflitto.
- Cita le persone sul cui lavoro costruisci.

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Export-and-Share]]
