# Cartelle e file delle mod

> **Riferimento** · Non devi mai toccarli a mano: li scrive lo Studio. Questa pagina serve quando qualcosa
> sembra sbagliato, o ai modder che modificano i file direttamente.

## Dove si trovano le cose

| Cosa | Dove |
|---|---|
| Le mod dello Studio | `Documents\RUSE 2.0\Mods\<mod>` (la cartella Documenti); le modifiche alle mappe in `Maps`, i file esportati in `Exports`, i backup in `Backups`. Nello Studio, **Impostazioni → Dove sono i tuoi file** le apre una per una, e **Mostra la cartella di questa mod** (menu della mod) apre quella che stai modificando |
| Le mod installate dal launcher | `%LOCALAPPDATA%\RUSE Mod Platform\library` |
| Le copie moddate del gioco | La cartella che scegli nelle Impostazioni (**Dove vanno le copie con le mod**, in entrambe le app); il posto consigliato è `RUSE-Instances` sulla stessa unità del gioco (per esempio `D:\RUSE-Instances`), dove una copia condivide i file del gioco. Su un'altra unità ogni copia è una copia completa del gioco: più lenta e più grande. Il backup pulito del gioco (`RUSE-Backup`) va accanto. |
| Il gioco stesso | Mai modificato |

Gli Studio più vecchi le tenevano in `%LOCALAPPDATA%\RUSE Mod Platform` (`mods`, `maps`, `exports`, `mod-backups`): lo Studio le sposta in Documenti al primo avvio, e lo dice.

## Dentro una mod

```
my-mod/
  mod.toml                    the mod's name, id, version, author (required)
  src/studio.rndf             unit changes made in the Studio
  text/studio.baseunite.csv   names of new units
  files/replace/gen/...png    a unit's paint (from Blender) or a unit's card, under the game texture it changes
  files/cards/<unit>.png      a new unit's own card in the build menu, named after the new unit
  files/models/<unit>.glb     a new unit's own 3D model (Import model), named after the new unit
  menu_groups.toml            the group of its building's build list each new unit stands in (the Studio writes it)
  maps/<map pack name>/       one folder per map the mod changes:
    terrain.toml                ground brushes (also water, cover and block brushes)
    scenery.toml                buildings, props and trees placed
    scenario.toml               starting points and spawns moved, units added
    cover.toml, movement.toml   cover and movement written by hand
    map.toml                    how many players; or, for a new map, the map it copies and its name
```

## Il nome della cartella di una mappa è il nome del pacchetto della mappa, non il suo titolo

I giocatori conoscono una mappa per il suo titolo (**Blitz**); i file del gioco usano il nome del suo pacchetto
(**SuperCrossRoads4**). La cartella di una mappa deve usare il nome del pacchetto: `maps/SuperCrossRoads4/`, non
`maps/Blitz/`. La coppia di ogni mappa è in [[Nomi delle mappe|Nomi-delle-mappe]], e l'elenco delle mappe dello Studio le mostra
entrambe: prima il titolo, il nome del pacchetto dopo il punto.

## Una nuova mappa

Una mod può aggiungere una mappa sua a BATTAGLIE: una copia di una mappa del gioco o un inizio vuoto, con un nome suo, che gli
altri file della mod poi rimodellano. Il nome della sua cartella è il nome del pacchetto della nuova mappa (lettere, cifre e
`_`), e il suo `map.toml` dice quale mappa copia e come la chiamano i menu:

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from (its pack name: Blitz)

[name]
us = "Blitz Twin"              # English, used where a language is left out
fr = "Blitz jumeau"
```

`maps/BlitzTwin/terrain.toml` e il resto poi modificano la copia, e Blitz resta com'era. Qualsiasi mappa elencata in
BATTAGLIE si può copiare; le mappe della campagna e delle Operazioni no. Due giocatori hanno bisogno della stessa mod per
giocarla insieme, come per qualsiasi mod. Le nuove mappe funzionano nel gioco (2026-10-03), e **Duplica mappa** dello Studio
crea questa cartella per te.

## Errori comuni

| Errore | Cosa succede | Soluzione |
|---|---|---|
| Lo zip contiene una cartella dentro una cartella | Il launcher guarda una cartella più in basso e la trova. Due o più livelli sotto, dice che non ha trovato nessuna mod. | Comprimi la cartella che contiene `mod.toml`. |
| Una cartella di mappa chiamata come il titolo della mappa | La build dice che non è il nome del pacchetto di una mappa. | Rinominala con il nome del pacchetto. |
| Un file modificato a mano ha un errore di battitura | Il controllo della mod nomina il file e la riga. | Correggilo, oppure **Metti da parte** nello Studio. |
| Un `.exe`, un `.dll` o uno script per PC dentro la mod | Rifiutato: le mod portano solo dati (gli script di missione del gioco stesso, come li salva lo Studio, sono l'unica eccezione). | Toglilo. |

Se un file non si può leggere, lo Studio non lo sovrascrive mai: il tuo lavoro non va mai perso. **Metti da parte** lo
rinomina `<name>.broken.toml` accanto all'originale.

---

[[Manuale da campo|Manuale-da-campo]] · [[English|Mod-Folders-and-Files]]
