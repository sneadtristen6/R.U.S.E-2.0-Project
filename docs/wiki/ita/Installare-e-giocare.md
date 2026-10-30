# Installare e giocare

> **Per:** giocatori · **Ti serve:** R.U.S.E. su Steam, installato · **Tempo:** 5 minuti

**In breve:** scarica **RUSE-Launcher-Setup** dalla pagina delle release, avvialo, apri **RUSE Launcher**, clicca su
**Mod supportate**, spunta una mod e premi **Installa**, mettila in un set di mod, poi **Gioca**. Ogni passo qui sotto dice
esattamente dove cliccare.

Per giocare con le mod ti serve solo **RUSE Launcher**. **RUSE Studio** serve a crearle (vedi la fine di questa pagina).

## Passo 1: scarica il Launcher

1. Apri la pagina delle [release del launcher](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher).
2. La più recente è in cima, segnata **Latest** (per esempio *RUSE Launcher 0.4.8.9*).
3. Scorri fino ad **Assets** sotto di essa e clicca su **RUSE-Launcher-Setup-0.4.8.9.exe** (il numero di versione cambia;
   prendi il `.exe` che inizia con `RUSE-Launcher-Setup`). Il tuo browser lo scarica.

Gli altri file che trovi lì (`RUSE-Launcher-notes.json`, *Source code*) non servono.

## Passo 2: installalo

1. Apri il file che hai scaricato (di solito nella cartella **Download**).
2. **«Windows ha protetto il PC»?** Clicca su **Ulteriori informazioni**, poi su **Esegui comunque**. L'app è nuova per il
   controllo della reputazione di Windows; il suo codice è pubblico su questo GitHub.
3. Procedi con l'installazione. Lascia spuntato **Conserva una copia pulita dei file del gioco**: le app non cambiano mai la
   cartella del gioco, ma altri gestori di mod e le modifiche a mano sì, e ogni gioco moddato è costruito da quei file. La
   copia viene fatta la prima volta che l'app si avvia (qualche minuto, circa lo stesso spazio su disco del gioco).
4. Avvia **RUSE Launcher** (menu Start o collegamento sul desktop). La prima volta, **Scegli la tua lingua**: una qualsiasi
   delle undici, le dieci del gioco e il persiano (فارسی); il pulsante della lingua in alto la cambia in qualsiasi momento.
   Trova R.U.S.E. da solo tramite Steam.
   Se dice che non ci riesce: **Impostazioni > Cartella del gioco > Scegli cartella…** e scegli la cartella che contiene `RUSE.exe`
   (di solito `C:\Program Files (x86)\Steam\steamapps\common\R.U.S.E`).

> [!IMPORTANT]
> **R.U.S.E. 2.0 funziona solo con una copia del gioco che possiedi su Steam.** Prima che un gioco moddato si avvii, il
> Launcher e lo Studio controllano la cartella del gioco: la registrazione di Steam di R.U.S.E. installato lì, il file di
> Steam stesso al suo interno, e nessun file che faccia girare il gioco senza Steam. Se non riescono a confermarla, un
> riquadro dice perché e cosa fare (Gioca resta disattivato fino ad allora): vedi
> [[Quando qualcosa va storto|Quando-qualcosa-va-storto]].

## Passo 3: procurati le mod

**Dal nostro elenco (il modo più facile):** clicca su **Mod supportate**, spunta le mod che vuoi e premi **Installa**. Ogni
file viene scaricato e confrontato con l'elenco prima di entrare nella tua libreria.

**Da un file che qualcuno ha condiviso:** clicca su **Aggiungi un file di mod…** e scegli il file, oppure trascinalo sulla
finestra. Il Launcher accetta:
- `.rusemod`: creato con RUSE Studio;
- `.rmod`: creato per RUSE Mod Manager di LittleGroove;
- `.zip`: una cartella di mod compressa.

Prima controlla il file: un file che non è una mod, o che contiene un programma, viene rifiutato e ti dice il motivo.

**Una vecchia mod che arriva come file del gioco stesso** (pacchetti `.dat` che ti dicevano di copiare nella cartella del
gioco): clicca su **Converti una vecchia mod…**, scegli la sua cartella, dalle un nome e clicca su **Converti e aggiungi alla
libreria**. La cartella del gioco non viene toccata.

## Passo 4: scegli cosa giocare

1. Un **set di mod** sono le mod con cui giochi insieme, in ordine. Clicca su **Nuovo set di mod…**, aggiungi le mod e
   mettile in ordine (quando due mod cambiano la stessa cosa, vince quella più in basso).
2. Se due mod non si possono giocare insieme, il Launcher ti dice quali e perché, prima che tu giochi.

## Passo 5: gioca

Scegli il tuo set di mod e premi **Gioca**. La prima volta il Launcher costruisce una copia moddata del gioco (un minuto
circa); dopo, solo ciò che è cambiato. Poi R.U.S.E. si avvia, con le tue mod.

Il tuo gioco moddato dice **R.U.S.E. 2.0 in oro**: si apre su una scena di battaglia, e il suo menu principale, i menu e le
schermate di caricamento portano il titolo d'oro. Viene creato sul tuo PC dai file del tuo gioco la prima volta (qualche
minuto, una volta sola). Per tenere il titolo del gioco, togli la spunta a **Il titolo del gioco** in **Impostazioni**.

> [!NOTE]
> Avviare R.U.S.E. da **Steam** avvia il gioco **senza** mod, come sempre. Per giocare con le mod, avvialo con **Gioca**
> nel Launcher. La tua installazione di Steam non viene mai modificata.

## Aggiornamenti

Il Launcher controlla se c'è una nuova versione ogni volta che si avvia: clicca su **Aggiorna ora** quando te ne propone una.
Se l'aggiornamento fallisce con "certificate verify failed", scarica nel browser il `RUSE-Launcher-Setup` più recente dal
Passo 1 e avvialo: si installa sopra quello vecchio e tiene le tue mod.

## Problemi?

| Cosa vedi | Cosa fare |
|---|---|
| «Windows ha protetto il PC» | **Ulteriori informazioni**, poi **Esegui comunque** (Passo 2). |
| Il Launcher non trova R.U.S.E. | **Impostazioni > Cartella del gioco > Scegli cartella…**, la cartella con `RUSE.exe`. |
| "certificate verify failed: unable to get local issuer certificate" | Prendi il Launcher 0.4.8.4 o più recente (Passo 1); vedi [[Quando qualcosa va storto|Quando-qualcosa-va-storto]]. |
| "unable to get issuer certificate" o «questo PC non si fida del certificato di sicurezza del sito» quando installi mod | Prendi il Launcher 0.4.8.9 o più recente (Passo 1), oppure scarica la mod nel browser e usa **Aggiungi un file di mod…**; vedi [[Quando qualcosa va storto|Quando-qualcosa-va-storto]]. |
| Il gioco parte senza le mie mod | Avvialo con **Gioca** nel Launcher, non da Steam. |
| Gli amici non riescono a entrare nella mia partita | Tutti devono avere le stesse mod nello stesso ordine: [[Giocare con gli amici|Giocare-con-gli-amici]]. |
| Qualsiasi altra cosa | [[Quando qualcosa va storto|Quando-qualcosa-va-storto]], oppure chiedi nelle [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) o sul [Discord](https://discord.gg/h54t5baNsC). |

## Linux e Steam Deck (tramite Proton)

Quando la finestra di un'app non riesce a mostrare le sue pagine (con Proton resta blu, perché lì WebView2 di Microsoft non si
avvia), l'app si apre invece nel tuo browser, e un piccolo riquadro te lo dice: tieni il riquadro aperto mentre giochi, e
chiudilo per chiudere l'app. Non ancora provato su Linux: per favore raccontaci come va nelle
[Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## Creare mod: RUSE Studio

1. Apri la pagina delle [release dello Studio](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio). Lo
   Studio è un'anteprima, quindi le sue release sono segnate **Pre-release**: prendi la più recente.
2. Sotto **Assets**, clicca su **RUSE-Studio-Setup-0.9.8.9.exe** (la versione più recente) e avvialo come nel Passo 2.
3. Avvia **RUSE Studio**, poi segui [[La tua prima mod|La-tua-prima-mod]] (10 minuti).

**Avanti:** [[Giocare con gli amici|Giocare-con-gli-amici]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Install-and-Play]]
