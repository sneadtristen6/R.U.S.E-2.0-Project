# Modellare il terreno

> **Per:** modder · **Ti serve:** RUSE Studio 0.7.2 e una mod · **Provato in gioco:** le unità si muovono sul terreno
> modificato e lì ricevono ordini

## Aprire la mappa

1. Scheda **Mappe**, scegli la mappa a sinistra (il pulsante **«** ripiega l'elenco per avere più spazio).
2. Guardati intorno: trascina per ruotare, trascina col tasto destro per spostarti, la rotellina per lo zoom (tasti:
   [[Tasti della vista mappa|Tasti-della-vista-mappa]]).
3. Nella barra in basso, clicca **Terreno e acqua**. I suoi strumenti si aprono sopra la barra, con la scheda **Terreno**
   per prima.

## Gli strumenti

| Strumento | A cosa serve | Come |
|---|---|---|
| **Collina** | una collina rotonda | un clic |
| **Alza** / **Abbassa** | alzare o scavare, poco alla volta | trascina |
| **Cratere** | un cratere con un bordo | un clic |
| **Altopiano** | una collina con la cima piatta | un clic |
| **Appiattisci** | portare le gobbe verso un'unica altezza | trascina |
| **Livella** | dipingere il terreno piatto all'altezza da cui parti | trascina |
| **Leviga** | ammorbidire i bordi netti | trascina |
| **Rampa** | un pendio regolare, per esempio fino a un altopiano | clicca dove inizia, poi dove finisce |

**Dimensione** e **Intensità** sono i cursori a destra (tasti **[ ]** e **- =**).

## Acqua

Clicca la scheda **Acqua** (in **Terreno e acqua**):

- **Acqua** allaga il terreno sotto un livello: l'altezza da cui inizi a trascinare, più l'Intensità. Trascinala lungo
  una valle per un fiume, o in un avvallamento per un lago.
- **Prosciuga** riporta l'acqua al livello di base della mappa: lì fiumi e laghi si asciugano.

## Dipingere il terreno con una texture (Studio 0.9.8.5)

**Ha ancora dei bug, usala a tua discrezione.** Nella barra in basso, clicca **Pittura mappa**, poi **Texture**. Scegli
da dove viene la texture, cliccane una, e trascina sul terreno:

- **Texture del gioco:** le texture del terreno delle mappe del gioco (erba, campi, sabbia, neve, roccia, strade...), per
  gruppo, con una ricerca. Vengono lette dal tuo gioco; nulla di esse va nella tua mod.
- **Da una mappa:** scegli una mappa, clicca un punto: un quadrato di 320 m del suo terreno diventa la tua texture.
- **Le tue immagini:** **Aggiungi un'immagine…** tiene un'immagine tua nella tua mod (`files/ground`).
- **Online (gratis):** texture di Poly Haven e ambientCG (CC0) e foto aeree degli Stati Uniti (pubblico dominio). Un clic
  scarica quella sola immagine nella tua mod, con il suo credito. Non ancora provato.
- **Questa mappa:** copia il terreno di questa stessa mappa da un punto che scegli.

**Dimensione** la stende più grande o più piccola (da un quarto a 16 volte). Con una texture del gioco, **Dettaglio del
gioco da vicino** stende anche i decal del gioco di quella texture sopra ciò che dipingi. Non ancora visto in gioco.

## Annullare e ricominciare

**Annulla** (o **Ctrl+Z**) toglie l'ultimo tratto; **Ricomincia** toglie ogni tratto su questa mappa.

## Vederlo in gioco

**Prova in gioco**, poi nel menu principale del gioco clicca **BATTAGLIE** e scegli quella mappa. Il messaggio in basso
nello Studio dice quale.

> [!TIP]
> Le scogliere ripide sembrano frastagliate: il terreno del gioco è una maglia di triangoli, e un bordo netto cade tra
> l'uno e l'altro. Le forme ampie e morbide rendono meglio.

**Avanti:** [[Copertura e movimento|Copertura-e-movimento]]

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Shape-the-Ground]]
