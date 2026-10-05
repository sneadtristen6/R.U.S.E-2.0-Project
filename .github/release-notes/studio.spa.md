**RUSE Studio, una versión preliminar para modders.** Explora las unidades del juego en cualquiera de sus diez
idiomas, cámbialas en un mod propio y pruébalo en el juego. Tu instalación de Steam nunca se modifica.

**0.9.7:** los mods de mapa muy grandes ahora se construyen en minutos. Antes, su construcción tardaba muchísimo, y por
eso hacía falta esta actualización. Y **Exportar mod…** lleva consigo lo que calculó la construcción, así que la
primera construcción de uno en el PC de un jugador es más corta.

- **El mod de mapa más extremo que tenemos** (el mapa «Día D» con el mar desecado: 154 trazos de aplanado, 135 trazos
  de pintura, 33.385 edificios borrados) tardaba unas cuatro horas en construirse. Ahora se construye en **menos de
  10 minutos**, sin guardar nada de una construcción anterior, y los archivos del juego salen iguales. Nos llevó unas
  15 horas; dónde se atascaba y por qué: [Cómo llegamos aquí](https://github.com/sneadtristen6/R.U.S.E-2.0-Project#how-we-got-here)
  (en inglés). Seguimos trabajando para hacerlo más rápido.

| Antes | Ahora |
|---|---|
| Un mapa remodelado a lo largo de kilómetros podía tardar horas en construirse, agotar la memoria del PC o ser rechazado por demasiado grande para el movimiento del mapa. | Su terreno se remodela en segundos, sus cauces se reparan y su terreno se pinta en todos los núcleos del PC, y su movimiento se calcula en dos más mientras se pinta el terreno. Cada paso da los mismos archivos que antes. |
| Un mar desecado seguía cerrado a las unidades. | Un cauce seco ancho recibe zonas de movimiento tan grandes como el espacio lo permite. **Aún no probado en el juego:** unidades sobre el mar abierto. |
| Reconstruir tras un cambio pequeño volvía a calcular todo un mapa grande. | Lo hecho se guarda: la pintura sin cambios tarda medio segundo, el movimiento sin cambios sale de la caché de construcción, y un trazo nuevo solo repinta las teselas que alcanza. |
| La primera construcción de un mod de mapa grande en el PC de un jugador volvía a calcularlo todo. | **Exportar mod…** pone en el mod lo que la construcción calculó para el movimiento del mapa (`maps/<map>/solved.bin`). Queda ligado al archivo del juego para ese mapa y no contiene archivos del juego. La construcción del jugador lo usa, comprueba cada respuesta y da los mismos archivos. La pintura del terreno y los cauces se siguen haciendo en cada PC. |
| Importar modelo solo aparecía en la página de una unidad nueva: difícil de encontrar. | La pestaña Unidades empieza con dos botones: **Cambiar una unidad** y **Nueva unidad (importar un modelo)**. Elige la unidad de partida, ponle nombre, Crear: su página se abre en Importar modelo. La página de una unidad del juego tiene **Nueva unidad a partir de esta…**. |
| La bandera de barco (76) decía que una unidad que la tiene se mueve sobre el agua. | Dice que la unidad no se mueve en absoluto, como un edificio (aún no probado en el juego). |

Conocido: **los mapas navales aún no están resueltos.** Un mar desecado o pintado se construye y se carga, pero el agua
se sigue viendo.
