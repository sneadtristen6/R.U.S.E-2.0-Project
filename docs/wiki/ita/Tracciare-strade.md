# Tracciare strade

> **Per:** modder · **Ti serve:** RUSE Studio 0.7.4 e una mod · **Provato in gioco:** le rotte di rifornimento seguono
> una nuova strada, ed è dipinta sul terreno

## Vedere le strade della mappa

Spunta **Strade** in cima alla mappa: le strade proprie della mappa compaiono in oro, sul terreno mentre lo modelli.

## Tracciare una nuova strada

1. Nella barra in basso, clicca **Strade e ponti** (si apre la sua scheda **Strade**). Le strade della mappa compaiono in
   oro, le tue nuove in blu.
2. Scegli uno strumento:

| Strumento | Come |
|---|---|
| **Dritta** | Clicca dove inizia la strada, poi dove finisce. |
| **Curva** | Clicca l'inizio, poi il punto verso cui la curva viene tirata, poi la fine. |
| **Libera** | Clicca lungo il percorso; fai doppio clic, premi **Enter** o clicca **Fine** per terminarla. |

3. Un nastro blu segue il puntatore, con la **lunghezza della strada** accanto (Libera mostra anche il tratto dal tuo
   ultimo clic). Un'estremità vicina a una strada qualsiasi **si aggancia a essa** (un anello mostra dove), così la nuova
   strada vi si unisce: i camion di rifornimento possono andare dall'una all'altra. Gli strumenti Strade mostrano quante
   nuove strade ha la mappa, e la loro lunghezza totale.
4. **Esc** scarta una strada che stai tracciando; **Annulla** (o **Ctrl+Z**) toglie l'ultima, **Ripeti** (o **Ctrl+Y**)
   la traccia di nuovo.

Le nuove strade vengono salvate subito nella tua mod (`maps/<map>/roads.toml`).

## Cosa fa una nuova strada nel gioco

- **Le rotte di rifornimento la usano** (provato: la rotta di un deposito di rifornimenti ha preso una nuova scorciatoia
  attraverso i campi aperti).
- **È dipinta sul terreno** nel colore delle strade della mappa stessa, così i giocatori la vedono (provato in gioco).
  Sembra una strada della mappa stessa da molto in alto e giù fino al terreno.
- **La fanteria la segue** per arrivare prima da qualche parte (provato in gioco, Studio 0.8.0).
- **Sopra l'acqua ha un ponte**: il tipo proprio della mappa (24 delle 32 mappe ne hanno uno), un solo pezzo steso da una
  sponda all'altra come i ponti del gioco stesso, e le unità possono attraversarlo. Una strada sopra uno dei ponti della
  mappa riceve il nuovo ponte al suo posto. Su una mappa senza un tipo di ponte, la build lo dice e l'acqua resta chiusa.
  (Provato in gioco: carri armati, fanteria e camion di rifornimento attraversano sul piano del ponte.)
- Le piante e gli oggetti sul suo percorso vengono tolti; **Mantieni gli alberi sulle nuove strade** tiene gli alberi e
  i cespugli (una strada sotto gli alberi).

## Togliere le strade e i ponti della mappa

Negli strumenti **Strade**:

- **Togli le strade della mappa:** le strade proprie della mappa se ne vanno: la rete che seguono i camion di
  rifornimento (che vanno invece attraverso i campi), e le strade disegnate sul terreno. Le tue nuove strade restano.
  Visto in gioco: le strade se ne vanno; i camion di rifornimento che vanno attraverso i campi non sono ancora provati.
- **Togli i ponti della mappa:** i ponti propri della mappa se ne vanno, con i piani su cui stavano le unità. Le unità
  attraversano ancora dove si trovavano, sul terreno sotto di essi, a meno che tu non spunti anche la casella seguente.
  I tuoi nuovi ponti restano.
- **Chiudi i passaggi dei vecchi ponti** (con i ponti tolti; da DomesticNukes): il terreno dove ogni vecchio ponte stava
  sopra l'acqua è chiuso alle unità, e i collegamenti stradali che lo attraversano sono tagliati: lì non passa niente,
  camion di rifornimento compresi, e il resto della rete stradale resta. Una tua nuova strada che attraversa nello stesso
  punto riceve lì il suo ponte. Se chiuderli isolasse un pezzo di terreno dal resto, lo Studio lo dice prima della build.

Non ancora provato in gioco: togliere i ponti e chiudere i loro passaggi.

## Piazzare un ponte tuo

Nella scheda **Ponti**: scegli un tipo, imposta la sua lunghezza e la rotazione, poi clicca il terreno dove va il centro
del ponte. Entrambe le estremità devono poggiare su una sponda asciutta. Anche qui funzionano **Annulla** e **Ripeti**.

**Vederla:** **Prova in gioco**, poi nel menu principale del gioco **BATTAGLIE** e la mappa. Piazza un deposito di
rifornimenti vicino alla tua strada e guarda la sua rotta.

**Avanti:** [[Posizionare edifici e alberi|Posizionare-edifici-e-alberi]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Draw-Roads]]
