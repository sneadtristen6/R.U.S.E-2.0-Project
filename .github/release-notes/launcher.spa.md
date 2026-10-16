**RUSE Launcher 0.4, para jugadores.** Encuentra R.U.S.E. a través de Steam, y **Jugar** construye una copia del juego
con tus mods y la inicia. Tu instalación de Steam nunca se modifica.

**0.4.8.6:** ejecuta los mods hechos con Studio 0.9.8.6.

- **Los mods hechos con Studio 0.9.8.6 se juegan:** mapas en blanco con sombras sobre el suelo llano, lo colocado donde el mapa copiado tenía mar dibujado, y el suelo de la cámara sobre el nuevo terreno.
- **Un cierre conocido rechazado:** un mod con un avión armado que lleva la bandera de reconocimiento sin la de caza cerraba el juego cuando el avión era enviado a atacar; ahora el Launcher se niega a construirlo y dice por qué.
- **Todavía con fallos, juégalo bajo tu propio criterio:** los mapas hechos con las texturas de Map Paint, y los mapas en blanco (Terreno en blanco, Océano en blanco).

**0.4.8.5:** juega los mods hechos con Studio 0.9.8.5.

- **Los mods hechos con Studio 0.9.8.5 funcionan:** aviones en un nuevo papel (un bombardero con su bodega de bombas, un explorador que conserva sus armas), vehículos de reconocimiento, armas que alcanzan a los aviones y suelo pintado desde la biblioteca del pincel Textura con el detalle del juego encima. Un Launcher más antiguo no puede construir algunos de ellos.
- **Más rápido:** un mapa repintado igual recupera su suelo pintado de la construcción anterior en segundos.
- **Todavía con fallos, juégalo bajo tu propio criterio:** los mapas hechos con las texturas de Map Paint, y los mapas en blanco (Terreno en blanco, Océano en blanco).

**0.4.8.4:** los mods se descargan en cualquier PC, y juega los mods hechos con Studio 0.9.8.4.

- **Los mods se descargan en cualquier PC:** en algunos PC no se descargaba ningún mod («certificate verify failed: unable to get local issuer certificate»). Ahora el Launcher le pide el certificado a Windows, como hace un navegador, y lo vuelve a intentar; también con sus propias actualizaciones. Aún no probado en un PC que tuviera el problema.
- **Los mods hechos con Studio 0.9.8.4 funcionan:** sus propias misiones, mapas en blanco con sus CG y sectores, depósitos con más camiones (un Launcher más antiguo rechaza depósitos con más de 1.000 camiones), unidades con su propio aspecto y uniformes, ediciones de mods de otros con su propio nombre.
- **Todavía con fallos, juégalo bajo tu propio criterio:** los mapas hechos con las texturas de Map Paint, y los mapas en blanco (Terreno en blanco, Océano en blanco).

**0.4.8.3:** las copias con mods van donde tú digas.

- **Dónde van las copias con mods**, en Ajustes: elige la carpeta donde se construye la copia del juego con mods, o
  vuelve al lugar recomendado, `RUSE-Instances` en la unidad del juego (allí la copia comparte los archivos del juego
  y está lista en segundos; en otra unidad es una copia completa del juego, más lenta y más grande). La copia de
  seguridad limpia del juego va al lado. El próximo Jugar construye en el nuevo lugar; la carpeta antigua puede
  borrarse a mano. El Studio usa la misma carpeta.

**0.4.8.2:** se abre en tu navegador web donde su propia ventana no puede, y juega mods hechos con el Studio 0.9.8.2.

- **Linux y Steam Deck (con Proton):** el Launcher se abre en tu navegador web cuando su propia ventana no puede. Aún
  no probado en Linux: cuéntanos qué tal va.
- Los mods hechos con el Studio 0.9.8.2 funcionan: unidades de otras épocas con sus propios modelos, tamaños,
  investigaciones y cartas.

**0.4.8.1:** convierte mods antiguos y juega mods hechos con el Studio 0.9.8.1.

- **Convertir un mod antiguo…**, el Convert de LittleGroove traído al Launcher: un mod antiguo que llega como paquetes
  del juego, para copiar en la carpeta del juego, se convierte en un mod que tu biblioteca juega junto a otros. Aún no
  probado con un mod antiguo real.
- **Dos mods que cambian el mismo archivo del juego:** el Launcher lo avisa antes de Jugar, y **Usar la de…** elige
  cuál.
- Los mods hechos con el Studio 0.9.8.1 funcionan: canciones y voces, una nación convertida en otra.

**0.4.8:** juega los mods hechos con Studio 0.9.8, entre ellos los mapas nuevos que empiezan en blanco, y muestra las
novedades en tu idioma.

| Antes | Ahora |
|---|---|
| Un mapa nuevo mostraba las imágenes del menú del mapa que copiaba. | Sus propias imágenes, tal como las hizo su autor, con los puntos de inicio donde empiezan sus jugadores. |
| Una unidad construida sobre un mar desecado podía colgar el juego. | Corregido (visto en el juego). |
| El agua de viejos ríos quedaba como muros a lo largo del borde de un mapa, y los faros borrados seguían brillando sobre el mar. | Corregido (visto en el juego). |
| Un mod que borra todo un mapa podía agotar la memoria del PC al construirse. | Se construye. |
| Las novedades estaban solo en inglés. | Están en el idioma del Launcher. |

Conocido: **los mapas navales no están terminados.** Océano en blanco se construye y se juega, pero las unidades bajo
su agua aún no se han probado.

**0.4.7:** los mods de mapa muy grandes ahora se construyen en minutos (antes tardaban muchísimo), y juega los mods
hechos con Studio 0.9.7.

| Antes | Ahora |
|---|---|
| **Jugar** podía tardar horas en construir un mod de mapa grande. | El más extremo que tenemos (el mapa «Día D» con el mar desecado) tardaba unas cuatro horas; ahora menos de 10 minutos, con el mismo resultado. |
| La primera construcción de un mod de mapa grande lo calculaba todo en tu PC. | Un mod exportado con Studio 0.9.7 lleva consigo lo que su construcción calculó para el movimiento del mapa: tu primera construcción es más corta. Se comprueba cada respuesta, y los archivos del juego salen iguales. |

Conocido: **los mapas navales aún no están resueltos.** Un mar desecado o pintado se construye y se carga, pero el agua
se sigue viendo.
