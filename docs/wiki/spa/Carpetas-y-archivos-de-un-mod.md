# Carpetas y archivos de un mod

> **Referencia** · Nunca necesitas tocarlos a mano: el Studio los escribe. Esta página es para cuando algo
> parece ir mal, o para los modders que editan archivos directamente.

## Dónde están las cosas

| Qué | Dónde |
|---|---|
| Los mods del Studio | `%LOCALAPPDATA%\RUSE Mod Platform\mods\<mod>` (pégalo en la barra de direcciones del Explorador de archivos) |
| Los mods instalados del launcher | `%LOCALAPPDATA%\RUSE Mod Platform\library` |
| Las copias con mods del juego | La carpeta que eliges en Ajustes (**Dónde van las copias con mods**, en cualquiera de las dos aplicaciones); el lugar recomendado es `RUSE-Instances` en la misma unidad que el juego (por ejemplo `D:\RUSE-Instances`), donde una copia comparte los archivos del juego. En otra unidad, cada copia es una copia completa del juego: más lenta y más grande. La copia de seguridad limpia del juego (`RUSE-Backup`) va a su lado. |
| El propio juego | Nunca se modifica |

## Dentro de un mod

```
my-mod/
  mod.toml                    the mod's name, id, version, author (required)
  src/studio.rndf             unit changes made in the Studio
  text/studio.baseunite.csv   names of new units
  files/replace/gen/...png    a unit's paint (from Blender) or a unit's card, under the game texture it changes
  files/cards/<unit>.png      a new unit's own card in the build menu, named after the new unit
  files/models/<unit>.glb     a new unit's own 3D model (Import model), named after the new unit
  maps/<map pack name>/       one folder per map the mod changes:
    terrain.toml                ground brushes (also water, cover and block brushes)
    scenery.toml                buildings, props and trees placed
    scenario.toml               starting points and spawns moved, units added
    cover.toml, movement.toml   cover and movement written by hand
    map.toml                    how many players; or, for a new map, the map it copies and its name
```

## El nombre de la carpeta del mapa es el nombre del paquete del mapa, no su título

Los jugadores conocen un mapa por su título (**Blitz**); los archivos del juego usan su nombre de paquete
(**SuperCrossRoads4**). Una carpeta de mapa debe usar el nombre de paquete: `maps/SuperCrossRoads4/`, no `maps/Blitz/`.
La pareja de cada mapa está en [[Nombres de los mapas|Nombres-de-los-mapas]], y la lista de mapas del Studio muestra los dos: el
título primero y el nombre de paquete después del punto.

## Un mapa nuevo

Un mod puede añadir un mapa propio a BATALLAS: una copia de un mapa del juego o un comienzo en blanco, con un nombre propio, al que los demás
archivos del mod luego dan otra forma. El nombre de su carpeta es el nombre de paquete del mapa nuevo (letras, cifras y
`_`), y su `map.toml` dice qué mapa copia y cómo lo llaman los menús:

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from (its pack name: Blitz)

[name]
us = "Blitz Twin"              # English, used where a language is left out
fr = "Blitz jumeau"
```

`maps/BlitzTwin/terrain.toml` y lo demás editan luego la copia, y Blitz se queda como estaba. Cualquier mapa que liste
BATALLAS se puede copiar; los mapas de campaña y de Operación, no. Dos jugadores necesitan el mismo mod para jugarlo
juntos, como con cualquier mod. Los mapas nuevos se juegan en el juego (2026-10-03), y **Duplicar mapa** del Studio crea
esta carpeta por ti.

## Errores habituales

| Error | Qué pasa | Arreglo |
|---|---|---|
| El zip contiene una carpeta dentro de otra carpeta | El launcher mira una carpeta más abajo y lo encuentra. Dos o más niveles más abajo, dice que no encontró ningún mod. | Comprime la carpeta que contiene `mod.toml`. |
| Una carpeta de mapa con el título del mapa como nombre | La construcción dice que no es el nombre de paquete de un mapa. | Cámbiale el nombre al nombre de paquete. |
| Un archivo editado a mano tiene una errata | La comprobación del mod nombra el archivo y la línea. | Arréglalo, o usa **Apartar** en el Studio. |
| Un `.exe`, un `.dll` o un script de PC dentro del mod | Rechazado: los mods solo llevan datos (los propios scripts de misión del juego, tal como los guarda el Studio, son la única excepción). | Quítalo. |

Si un archivo no se puede leer, el Studio nunca escribe encima: tu trabajo nunca se pierde. **Apartar** le cambia el
nombre a `<name>.broken.toml` junto al original.

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Mod-Folders-and-Files]]
