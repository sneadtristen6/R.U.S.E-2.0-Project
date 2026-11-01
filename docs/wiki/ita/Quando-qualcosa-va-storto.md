# Quando qualcosa va storto

Trova ciò che vedi e segui la soluzione.

## Prova prima Risoluzione problemi

**Risoluzione problemi** controlla in un colpo solo cosa può fermare una prova o **Gioca**: il gioco trovato, Steam in
esecuzione, R.U.S.E. rimasto aperto da una copia moddata, l'unità e il suo spazio libero, copie rimaste, file di sola
lettura, e se l'app può scrivere dove vanno le copie. Ogni problema che può risolvere ha un pulsante; gli altri dicono cosa
fare.

- In RUSE Studio: accanto a **Prova in gioco**, e in **Impostazioni > Aiuto**. In RUSE Launcher: la barra in basso, e in
  ogni messaggio di problema (Studio 0.8.0, Launcher 0.3.0).
- **Copia il rapporto** dà un testo da incollare in una [[segnalazione di bug|Segnalare-un-bug]] (il tuo nome utente di Windows
  viene lasciato fuori).

## Il gioco stesso sembra cambiato (da un altro gestore di mod o da una modifica a mano)

**Impostazioni > Backup pulito del gioco** tiene una copia pulita dei file del gioco, li confronta con essa e rimette ciò che
è cambiato. I file che non sono del gioco vengono spostati da parte, mai eliminati. Oppure **Verifica con Steam** fa riparare
il gioco a Steam. Questo è l'unico punto in cui le app scrivono nella cartella del tuo gioco, e solo quando lo chiedi.

## Una barra rossa sotto l'intestazione dello Studio

È il **controllo della mod**. Lo Studio legge ogni file della tua mod come farà la build del gioco, quando scegli la mod e di
nuovo prima di **Prova in gioco**. Ogni problema è detto in parole semplici (cosa non va, su quale mappa, cosa fare), con un
pulsante che lo risolve dove si può: compilare un valore mancante, togliere l'unico elemento o impostazione sbagliata, o
mettere da parte il file. Il file com'era viene tenuto accanto. **Dettagli** mostra le parole della build stessa, utili
quando chiedi aiuto.

- **Metti da parte** (accanto a un file di mappa rotto) lo rinomina `<name>.broken.toml` accanto all'originale: non si perde
  niente, la mod funziona senza di esso, e quella mappa riparte pulita.
- Un problema in `mod.toml` o nelle modifiche alle unità non ha Metti da parte: apri il file e correggi la riga che la barra
  nomina, oppure chiedi in [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

> [!NOTE]
> Caso noto: RUSE Studio 0.7.0 e precedenti salvavano le pennellate di **Acqua** senza il loro livello dell'acqua ("the water
> brush needs level"). La 0.7.1 lo corregge; **Metti da parte** sistema un vecchio file.

## L'app ci mette molto ad aprirsi

- **Il primo avvio dopo l'installazione** con «Conserva una copia pulita dei file del gioco» spuntato fa quella copia (tutta
  la cartella del gioco, circa 5.3 GB): le Impostazioni mostrano a che punto è, e intanto l'app si può usare.
- **L'indice del gioco di RUSE Studio** viene costruito una volta per ogni versione del gioco, e di nuovo quando un
  aggiornamento dello Studio lo cambia (circa un minuto; lo Studio chiede prima). Intanto si possono usare la scheda Mappe e
  le Impostazioni, e la riga in basso dice quando è pronto.
- Qualsiasi altra cosa: apri **Risoluzione problemi** e **Copia il rapporto**. Il rapporto elenca quanto ha impiegato ogni
  passo degli ultimi avvii dell'app, in secondi: incollalo in una [[segnalazione di bug|Segnalare-un-bug]]. Le stesse righe
  vengono tenute in `%LOCALAPPDATA%\RUSE Mod Platform\logs\studio-start.log` (quelle del Launcher: `launcher-start.log`).

## «Windows ha protetto il PC»

Le app sono nuove per il controllo della reputazione di Windows. Clicca su **Ulteriori informazioni**, poi su **Esegui
comunque**.

## "certificate verify failed: unable to get local issuer certificate" (o "unable to get issuer certificate")

Nessuna mod si scarica, o l'aggiornamento non si scarica. Windows non aveva ancora recuperato il certificato con cui viene
controllato GitHub; dal Launcher 0.4.8.4 e dallo Studio 0.9.8.4 le app lo chiedono a Windows e riprovano. Dal Launcher
0.4.8.9 e dallo Studio 0.9.8.9 provano anche con l'elenco di certificati che usa Firefox, che portano con sé, per un PC il
cui Windows non riesce a recuperarlo (con gli aggiornamenti dei certificati disattivati o bloccati: "unable to get issuer
certificate", oppure «il PC non si fida del certificato di sicurezza del sito»). Con un'app più vecchia nemmeno
l'aggiornamento riesce a scaricarsi: prendi il programma di installazione dalle
[release](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases) nel tuo browser e avvialo (si installa sopra
quello vecchio, come fa l'aggiornamento). Una mod si può sempre scaricare nel browser dalle
[release](https://github.com/sneadtristen6/Ruse-Mods/releases) dell'elenco delle mod e aggiungere con **Aggiungi un file di mod…** nel Launcher. Se
un'app nuova lo dice ancora: può causarlo un antivirus che analizza le connessioni sicure (HTTPS), una rete scolastica o di
lavoro, o una data sbagliata sul PC; raccontacelo in [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## "[WinError 5] Access is denied" quando provi o giochi

Windows ha rifiutato di rimuovere una copia del gioco fatta dall'app (in `RUSE-Instances`). Oppure: «Una vecchia copia
moddata in `...\RUSE-Instances\<name>.old` non può essere rimossa», a ogni seconda **Prova in gioco** o **Gioca**.

- **Prima aggiorna** (le app lo propongono quando si aprono): da RUSE Studio 0.7.6 e Launcher 0.2.11, una copia che Windows
  non vuole eliminare non ferma mai una prova: viene spostata in `RUSE-Instances\.trash` e rimossa lì appena niente la
  tiene occupata.
- **R.U.S.E. è ancora aperto da una prova precedente?** L'app lo dice, con il nome del programma: chiudi il gioco (cerca
  `RUSE.exe` nella scheda Dettagli di Gestione attività), poi riprova. **Risoluzione problemi** trova un gioco ancora aperto
  da una copia e le copie rimaste, e le rimuove per te.
- **Con una versione più vecchia:** elimina la cartella che il messaggio nomina (`...\RUSE-Instances\<name>.partial` o
  `.old`; Windows chiede dei file di sola lettura: rispondi sì; se ne va solo la copia, mai il gioco), poi riprova. Se
  Windows rifiuta, riavvia prima Windows.
- Ancora lì? [[Segnalalo|Segnalare-un-bug]] con il messaggio completo.

## L'app non trova R.U.S.E.

**Impostazioni > Cartella del gioco > Scegli cartella…** e scegli la cartella che contiene `RUSE.exe` (su Steam:
`steamapps\common\R.U.S.E`).

## «Non siamo riusciti a confermare questa copia di R.U.S.E.»

R.U.S.E. 2.0 funziona solo con una copia del gioco che possiedi. Finché la cartella del gioco non è confermata, **Gioca** e
**Prova in gioco** restano disattivati, e questo riquadro dice perché: Steam non ha nessuna registrazione di R.U.S.E.
installato in quella cartella; il file di Steam stesso al suo interno (`steam_api64.dll`) manca, è cambiato o non è di
Valve; oppure la cartella ha file che fanno girare il gioco senza Steam (li nomina).

- **Lo possiedi su Steam:** clicca su **Verifica i miei file in Steam** (Steam rimette ogni suo file mancante o cambiato),
  togli i file che il riquadro nomina, poi clicca su **Controlla di nuovo**. Una cartella del gioco che hai scelto a mano
  deve essere quella che ha installato Steam.
- **Lo possiedi in un altro modo** (una copia in scatola di prima che R.U.S.E. arrivasse su Steam), **o pensi che il
  controllo si sia sbagliato:** il riquadro mostra **Il tuo codice** (creato da questo PC e dalla cartella del gioco).
  Clicca su **Copia**, poi su **Apri un ticket su Discord** o **Apri un ticket su GitHub** e incollalo. Ti mandiamo un
  codice di sblocco: incollalo sotto **Codice di sblocco** e clicca su **Sblocca**. Conferma quella copia su quel PC.

Il controllo è lo stesso su Windows, Linux e Steam Deck. Questo progetto non aiuta mai nessuno a giocare a R.U.S.E. senza
possederlo: nessun file del gioco distribuito, niente gioco avviato senza Steam.

## «In un formato di mod più vecchio» o «salvata da un RUSE Studio più recente»

- **Un formato di mod più vecchio:** la mod è stata creata con uno Studio più vecchio. **Aggiorna questa mod** riscrive i
  suoi file nel modo in cui li legge questo Studio, mantenendo ciò che significano; prima uno zip dell'intera mod va nella
  cartella `Backups` dello Studio.
- **Un RUSE Studio più recente:** aggiorna lo Studio prima di cambiare quella mod: uno più vecchio potrebbe perdere ciò che
  non conosce.

## Chiudendo lo Studio compare «Chiudere RUSE Studio?»

Non tutto è ancora salvato, e il riquadro dice cosa (una casella con del testo scritto ma non confermato, una modifica
ancora in salvataggio, Prova in gioco ancora in costruzione...). **No** tiene aperto lo Studio; **Sì** lo chiude e perde
quelle cose.

## Il gioco parte, ma senza le mie modifiche

1. È stato avviato da **Gioca** (launcher) o da **Prova in gioco** (Studio)? Da Steam, il gioco parte senza mod.
2. Le modifiche a una mappa si vedono solo su quella mappa: nel menu principale clicca su **BATTAGLIE** e sceglila (il
   messaggio dello Studio dopo Prova in gioco dice quale pulsante e quale mappa).
3. La mod è nel set, e c'è una mod più in basso nell'ordine che cambia la stessa cosa?

## Il gioco va in crash

Scrivi cosa hai fatto appena prima (quale mappa, quale ordine, cosa c'era sullo schermo), fai uno screenshot e
[[segnalalo|Segnalare-un-bug]]. Le segnalazioni di crash sulle mappe modificate sono il modo in cui gli strumenti per le mappe sono
diventati solidi.

## Qualcos'altro

[[Fare una domanda|Fare-una-domanda]].

---

[[Manuale da campo|Manuale-da-campo]] · [[English|When-Something-Goes-Wrong]]
