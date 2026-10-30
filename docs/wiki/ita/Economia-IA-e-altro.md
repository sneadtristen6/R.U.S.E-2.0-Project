# Economia, IA e altro: gli strumenti di LittleGroove

> **Per:** modder · **Ti serve:** RUSE Studio 0.9.8.1 o successivo e una mod · **Tempo:** quanto vuoi

RUSE-Mod-Manager di LittleGroove aveva strumenti che lo Studio non aveva. Ora sono nello Studio, ognuno nella tua mod: una
modifica viene salvata lì subito, e i file del gioco non vengono mai toccati.

## La scheda Impostazioni IA e giocatori

Una scheda in tre parti: **Impostazioni dei giocatori**, **Regole del gioco** e **Giocatori del computer**.

### Impostazioni dei giocatori

Denaro iniziale e rendita, depositi di rifornimento (denaro per camion, camion per convoglio, il tempo tra i convogli), limiti
di produzione, e le carte d'inganno con cui parte ogni schieramento. Una modifica vale per ogni modalità di gioco; dove la
modalità Nucleare ha un valore suo, ha anche un riquadro suo. I depositi di rifornimento e gli edifici amministrativi sono
edifici: il loro prezzo, tempo di costruzione e resistenza sono nella scheda **Unità**.
Visto in gioco: il denaro iniziale e le carte d'inganno all'inizio.

**Depositi sulle mappe** (sotto Depositi di rifornimento): dai a ogni deposito di rifornimento più camion, quindi più denaro,
su **Tutte le mappe** o **Una mappa:** scegli tu. Moltiplica i camion di ogni deposito (**volte i loro camion**) o dai a tutti
lo stesso numero (**camion ciascuno**). La riga sopra dice cosa contiene un deposito con i tuoi valori. Un deposito a cui hai
dato camion suoi nella scheda Mappe li tiene. Gioca le mod con più di 1.000 camion per deposito con il Launcher 0.4.8.4 o più
recente. Visto in gioco (i depositi di D-Day con 500 camion; le altre mappe con il triplo dei loro).

### Regole del gioco

Ogni altra regola che il gioco tiene per tutti i giocatori, in gruppi: battaglia e resa, popolazione, movimento e strade,
tiro e bersagli, le unità da sole, danni e inchiodamento, boschi e vista, aerei, le carte d'inganno all'opera, il controller,
piazzare edifici, partite classificate online, sagome e frecce, effetti sullo schermo, i colori degli schieramenti e dei
settori (un selettore di colore ciascuno), e per ultimi alcuni valori il cui uso non è ancora noto. Ognuna dice cosa fa e
che valore ha nel gioco. Non ancora provato in gioco.

### Giocatori del computer

Come giocano i giocatori del computer. Un giocatore del computer mescola tre insiemi di valori: **Predefinito**, la sua
difficoltà e il suo profilo (entrambi scelti nella lobby del gioco); scegline uno per vederne e cambiarne i valori: quando
inizia ad attaccare, quanto forte aspetta di essere, come si difende, le unità che preferisce e le sue carte d'inganno. Ogni
valore si può cambiare in ogni insieme: uno che un insieme non elenca vale 0 nel gioco, e dargli un numero lo aggiunge alla
tua mod. Sotto gli insiemi, ciò che vale per ogni giocatore del computer (il valore dell'esercito che lo fa attaccare, le sue
esche...).
Visto in gioco: una carta d'inganno tolta dal menu, una spostata al suo interno, la durata di una carta, e quando Facile
inizia ad attaccare. Il resto non ancora provato in gioco.

**Script delle mappe e delle missioni**, più sotto: gli script che il gioco esegue sulle sue mappe (i capitoli della
campagna, le sfide, le Operazioni), mostrati come Python da leggere. **Copia** ne copia uno.

## Il riquadro Potenziamento e ricerca di un'unità

Nella pagina di un'unità: l'unità di cui è un potenziamento (**Potenziamento di**), i suoi potenziamenti, e il prezzo e il
tempo della sua ricerca. Scegli un'altra unità, oppure **Nessuna: un'unità a sé**. Vedi [[Modificare le unità|Modificare-le-unità]].

## La scheda Tutti i valori e i file

Due parti, scelte con l'interruttore in cima all'elenco.

**Tutti i valori:** qualsiasi oggetto e valore del gioco, cambiato nella tua mod: aggiungi o togli un valore, crea o elimina
un oggetto, dai a un valore di testo parole sue. Non ancora provato in gioco.

**File:** qualsiasi file dentro i pacchetti del gioco: scegli un pacchetto, poi un file per vederlo per ciò che è
(un'immagine, una tabella di testo, uno script di missione...). **Salva una copia…** lo salva fuori; **Sostituiscilo con un
mio file…** mette il tuo nella tua mod; **Aggiungi un mio file a questo pacchetto…** ne aggiunge uno nuovo. La tua mod tiene
solo ciò che cambi, mai una copia del file del gioco. Non ancora provato in gioco.

## Missioni e mappe

Gli script di una missione si possono cambiare, e lo Studio controlla se la missione è nei menu, se ogni file di cui ha
bisogno si carica, e i suoi testi; si può spostare su o giù nel suo menu. Su una mappa: nomi di città e colline, punti e
zone con nome, e il nome e l'orientamento di un elemento della mappa. Si possono tenere **Note** su un'unità, un valore o un
giocatore del computer. Non ancora provato in gioco.

## Nel Launcher: Converti una vecchia mod

Una mod più vecchia che arriva come pacchetti del gioco stesso, fatta per essere copiata nella cartella del gioco, diventa
una mod che la tua libreria gioca accanto ad altre: vedi [[Installare e giocare|Installare-e-giocare]].

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Economy-AI-and-More]]
