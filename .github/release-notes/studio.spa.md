**RUSE Studio, una versión preliminar para modders.** Explora las unidades del juego en cualquiera de sus diez
idiomas, cámbialas en un mod propio y pruébalo en el juego. Tu instalación de Steam nunca se modifica.

**0.9.8.1:** Las herramientas de LittleGroove llegan al Studio, con música y sonidos, una nación convertida en otra y unidades de otras épocas.

- **Las herramientas de LittleGroove, traídas** de su RUSE-Mod-Manager:
  - **Pestaña Economía:** dinero inicial e ingresos, depósitos de suministros y las cartas de engaño con que empieza
    cada bando. Visto en el juego: el dinero inicial y las cartas iniciales.
  - **Pestaña IA:** cómo juegan los jugadores del ordenador, las unidades que prefieren y las cartas de engaño; y
    los scripts de mapas y misiones del juego, mostrados en Python, solo de lectura. Visto en el juego.
  - **Recuadro Mejora** en la página de una unidad: la unidad de la que es mejora, sus propias mejoras, el precio y el
    tiempo de su investigación.
  - **Pestaña Todos los valores:** cualquier objeto o valor del juego, cambiado en un mod: añadir o quitar un
    valor, crear o borrar un objeto, dar a un valor de texto palabras propias.
  - **Pestaña Archivos:** cualquier archivo de los paquetes del juego, visible y guardable. Cambia uno por un archivo tuyo o
    añade uno: tu mod guarda solo los cambios, cada uno comprobado según su tipo.
  - **Misiones:** cambiar los scripts de una misión; ver si está en los menús, si carga cada archivo que necesita, y
    sus textos; subirla o bajarla en su menú.
  - **Mapas:** nombres de ciudades y colinas, puntos y zonas con nombre, nombre y orientación de un objeto del mapa.
    **Notas** sobre una unidad, un valor o un jugador del ordenador.
- **Pestaña Música:** cada canción según dónde suena, cada una cambiada en un pequeño editor del Studio (cortar,
  fundido, volumen); canciones nuevas añadidas a las listas de batalla; las frases de una unidad en su página; el
  sonido de fondo de un mapa. Visto en el juego: las canciones, las canciones nuevas y las frases.
- **Convertir una nación en otra.** La nueva pestaña **Naciones** da a una de las siete naciones del juego un nombre
  nuevo (en la sala y para su ejército) y una bandera nueva a partir de cualquier imagen: por ejemplo, China en
  lugar de Italia. Sus unidades y lo que dicen se cambian como antes, en la pestaña Unidades y en la página de cada
  unidad. Visto en el juego: el nombre nuevo en la sala, la bandera nueva en la partida.
- **Unidades de otras épocas:** la pestaña Unidades ofrece WWI, WWII+, Guerra Fría y Moderna junto a las unidades del
  juego. Cada época se descarga en el Studio cuando la eliges, desde nuestro GitHub (cada archivo comprobado), y se actualiza sola a medida que se terminan más unidades. Añade una a tu mod y se convierte en una unidad nueva con su propio modelo, su autor citado; no se añade nada
  hasta que la eliges.
- **Mapa nuevo: empezar desde cero…** está en la pestaña Mapas antes de abrir un mapa.
- **El suelo de Terreno en blanco se dibuja como propio.** Un mapa nuevo empezado en blanco tiene el suelo hecho a
  partir de tus trazos de terreno, no el suelo del mapa del juego desplazado: costas redondeadas de cerca y desde lo
  alto, sin abolladuras en las cimas, y edificios y tanques asentados justo encima. Visto en el juego en mapas de
  prueba.
- **Océano en blanco se queda, con un aviso** en su botón: las islas separadas no están listas para batallas
  a gran escala (abajo).

Aún no probado en el juego: el recuadro Mejora, Todos los valores, Archivos, las herramientas de misiones, los
añadidos a los mapas, los sonidos de fondo y las unidades de otras épocas.

**Por qué aún no hay mapas navales.** Probamos mapas de islas para batallas a gran escala con barcos, y el propio
juego lo impide:

- Una unidad terrestre enviada a una isla a la que no puede llegar hace que el juego se cuelgue.
- Unir las islas con una franja de tierra evita el cuelgue, pero entonces el ordenador simplemente envía su
  infantería por ella.
- Sin carretera entre las islas, no se puede colocar ningún edificio.
- Con las armas del propio juego, los barcos y las unidades terrestres apenas se hacen daño.

Los datos del mapa por sí solos no pueden arreglar el cuelgue, así que los mapas navales esperan.

**0.9.8:** un mapa nuevo puede empezar en blanco, como tierra llana o mar abierto, y cada mapa puede tener sus propias
imágenes en los menús del juego.

- **Empezar un mapa en blanco.** **Duplicar mapa** tiene una nueva opción, **Empezar desde**: **Terreno en blanco**
  (tierra llana sin nada encima salvo los puntos de inicio) u **Océano en blanco** (el mar sobre todo el mapa). Visto
  en el juego.
- **Imágenes del menú para cualquier mapa.** Elige un PNG para la imagen del mapa y su mapa 3D en los menús, o vuelve
  a las del juego; los puntos de inicio blancos se dibujan donde empiezan los jugadores del mapa. **Crear en
  Blender…** abre el propio modelo 3D del mapa para hacerlas, y **Traer** las pone en tu mod. Visto en el juego.

| Antes | Ahora |
|---|---|
| Un mapa nuevo empezaba como copia completa de un mapa del juego. | **Duplicar mapa** puede hacerlo empezar en blanco: Terreno en blanco u Océano en blanco. |
| Un mapa nuevo mostraba las imágenes del menú del mapa que copiaba. | **Imágenes del menú…** le da las suyas: un PNG tuyo o una imagen hecha en Blender, con los puntos de inicio donde empiezan sus jugadores. |
| Los depósitos, unidades, edificios y nombres del mapa se quedaban. | **Quitar** quita uno, o todos los depósitos o todos los nombres de una vez (visto en el juego). |
| Las carreteras y los puentes del mapa se quedaban. | El panel Carreteras los quita (las líneas de las carreteras desaparecen: visto en el juego). |
| Los sectores dejaban fuera el mar y los bordes del mapa. | **Sectores en todo el mapa**: se puede tomar todo el mapa (visto en el juego). |
| El agua de un mapa venía solo de sus ríos y su mar. | **Agua en todo el mapa**: una capa fina, como el mar pintado de un mapa naval (visto en el juego; las unidades por debajo aún no se han probado). |
| El editor de mapas elegía las apariciones de una en una, por nombres en clave. | Arrastra un recuadro para seleccionarlas como en el juego; los iconos del mapa muestran qué está seleccionado y cuántos. |
| Los paneles del editor de mapas tenían un solo tamaño. | Cada panel flotante cambia de tamaño, del 40 % al 125 %. |
| Las novedades estaban solo en inglés. | Están en el idioma del Studio. |
| Enviar un mod a la lista de mods era escribir su entrada a mano. | **Publicar en la lista de mods** abre el formulario de la lista, ya rellenado, con una copia .zip lista para arrastrar; cada exportación dice que se hizo con RUSE Studio. |
| Importar modelo perdía el sombreado y las partes transparentes de un modelo. | Las conserva, y dice qué conservó (aún no visto en el juego). |
| Una unidad construida sobre un mar desecado podía colgar el juego; el agua de viejos ríos quedaba como muros a lo largo del borde de un mapa; los faros borrados seguían brillando sobre el mar. | Corregido, cada uno visto en el juego. |

Conocido: **los mapas navales no están terminados.** Océano en blanco se construye y se juega, pero las unidades bajo
su agua aún no se han probado.

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
