**RUSE Studio, una versión preliminar para modders.** Explora las unidades del juego en cualquiera de sus diez
idiomas, cámbialas en un mod propio y pruébalo en el juego. Tu instalación de Steam nunca se modifica.

**0.9.8.9:** una lectura de imágenes más segura.

- **Imágenes más seguras:** la biblioteca con la que el Studio lee las imágenes (Pillow) pasa a la versión 13.0.0, con sus correcciones contra archivos de imagen hechos a propósito que podían cerrar la aplicación, agotar su memoria o algo peor. Nada más cambia.

**0.9.8.8:** una pantalla de inicio y un tablero de edificios, edificios propios, RUSE Decoy para sonidos y animaciones, cada regla del juego en una pestaña, y R.U.S.E. 2.0 en oro.

- **Una pantalla de inicio:** sigue con tu mod, empieza uno nuevo o sáltala (también siempre). Los pasos de un mod nuevo: su nombre, si cada nación conserva sus unidades o empieza vacía, la investigación (la del juego, ninguna o la tuya), el tablero de edificios, y luego lo que cambiará el mod. Visto en el juego.
- **El tablero de edificios:** los edificios de cada nación como filas de las unidades que ofrecen sus menús de construcción, en el orden del juego. Pon una unidad (de la nación, una copia de la unidad de otra nación, una unidad de época), arrástrala por una fila o a otro edificio, quítala, o haz que se investigue desde la unidad bajo la que va. La página de cada unidad dice dónde se construye. Visto en el juego.
- **Añadir un edificio…:** una copia de un edificio del juego que hace las mismas unidades, o un edificio con unidades propias y su propia pestaña en la barra de construcción, hasta tres por nación. El segundo y el tercero necesitan un pequeño parche del juego para más edificios: el Studio lo descarga una vez y lo aplica solo a tu copia del juego con mods, nunca al juego de tu carpeta de Steam. Visto en el juego.
- **El aspecto propio de un edificio:** en la página de un edificio nuevo, importa un modelo 3D en lugar de una pieza del aspecto que copia (el edificio principal de una fábrica o de un cuartel general, o la pieza que elijas), y dale su propia imagen en el menú de construcción. Visto en el juego.
- **Importar modelo… en la pestaña Mapas:** un modelo 3D (.glb, .gltf o .3ds) se convierte en una roca, un objeto, una planta o un árbol propio de tu mapa, colocado como los del juego, con un tamaño y el crédito de su autor (modelos de otros: solo CC0 o CC-BY). Las unidades lo derriban como a los del juego; con **Sólido** marcado, lo rodean. Visto en el juego.
- **RUSE Decoy, el diseñador de sonido y animación,** en lugar de la pestaña Música. Cada sonido del juego por tipo (armas cercanas y lejanas, impactos, motores, ambiente, interfaz, cartas de engaño, voces de las unidades, radio, frases de las misiones con lo que dice cada una, música): escúchalo, dale su propio volumen (de 0 a 200 %) o sustitúyelo. Animaciones: otro clip en lugar de un clip, un clip más lento o más rápido, un hueso más grande o girado, o captura de movimiento en los soldados, de una biblioteca de 3.205 movimientos libres (la base de datos de captura de movimiento CMU y 100STYLE, con su crédito), cada uno descargado al elegirlo. La página de una unidad abre RUSE Decoy en sus propios sonidos y animaciones. Visto en el juego. Sus mensajes de error están solo en inglés por ahora.
- **Ajustes de la IA y de los jugadores:** las pestañas Economía e IA son una sola. Ajustes de los jugadores: dinero e ingresos, depósitos de suministros, producción y cartas de engaño, como antes. Jugadores del ordenador: cada uno de sus 47 valores en el conjunto por defecto, cada dificultad y cada personalidad (un valor que el juego omite en un conjunto muestra el 0 que cuenta el juego). **Reglas del juego:** otros 172 valores del juego en 16 grupos (batalla y rendición, población, movimiento y carreteras, disparo y objetivos, daño, bosques y cobertura, aviones, las cartas de engaño en acción, colocar edificios, partidas clasificatorias en línea, contornos y efectos en pantalla, los colores de jugadores y sectores con un selector de color, y otros), cada uno con nombre y explicación. Aún no probado en el juego.
- **Todos los valores y archivos:** las pestañas Todos los valores y Archivos son una sola, con un interruptor arriba; se abre en la parte que usaste por última vez.
- **Corregido:** Todos los valores mostraba los números de un color en el orden equivocado (el juego guarda primero el azul), así que el color de jugador 1, azul, parecía naranja, y escribir el rojo cambiaba el azul. Ahora los colores se muestran y se escriben con el rojo primero; un archivo de mod conserva el orden del juego, como antes.
- **Corregido: manchas oscuras y claras en los mapas hechos por el Studio** (mapas en blanco, ampliados, de relieve y de sectores): la inclinación del suelo se escribía mal, así que la hierba y los campos se iluminaban de forma desigual. Un mapa se ilumina bien una vez construido con esta versión (su suelo se rehace la primera vez). Visto en el juego.
- **Quitar los cruces viejos (de DomesticNukes):** en las carreteras de la pestaña Mapas, con **Quitar los puentes del mapa** activado, **Cerrar los cruces de los puentes viejos** cierra también el suelo donde cada puente viejo cruzaba el agua y corta los enlaces de carretera que lo atraviesan: ya nada cruza allí; el resto de la red de carreteras se queda. Aún no probado en el juego.
- **R.U.S.E. 2.0 en oro:** el juego con mods que construye Probar en el juego se abre con una escena de batalla y un motor que arranca, y su menú principal, el título pequeño de cada menú, los contornos de los menús y las pantallas de carga dicen R.U.S.E. 2.0 en oro. Se hace en tu PC con los archivos de tu propio juego la primera vez (unos minutos una vez, luego se guarda). Ajustes tiene una casilla para conservar el título del juego. Visto en el juego.
- **Las letras del juego:** el Studio está escrito con la fuente de los menús del juego, tomada de tu juego cada vez que arranca (la fuente no viene con el Studio).
- **Corregido, avisado por un modder:** un modelo importado en una unidad nueva hecha a partir del Panther caía lejos de la unidad; en unidades hechas a partir de otras 85 (el GPF de 155 mm, el SU-85, el Carro Veloce, el StuG III, el M7 Priest...) quedaba fuera de la torreta. El Studio lee ahora bien dónde giran sus torretas. Un modelo importado antes conserva su sitio viejo: usa Importar modelo… otra vez en esa unidad. Aún no probado en el juego.
- **Corregido, avisado por un jugador:** un modelo con imágenes JPG o WebP (la mayoría de los .glb descargados) se rechazaba; ahora se importa. Un modelo que el importador aún no sabe leer (mallas comprimidas, imágenes KTX2) lo dice, y cómo arreglarlo en Blender. Aún no probado en el juego.
- **Corregido, avisado por un jugador:** un tanque del propio juego, abierto en Blender e importado de vuelta, dejaba la torreta quieta. Abrir en Blender nombra ahora el hueso de cada pieza como el juego, y la importación gira una pieza del hueso de la torreta con la torreta. Un modelo exportado antes conserva sus nombres viejos: ábrelo otra vez en Blender. Aún no probado en el juego.
- **Pon nombre a tu munición:** una munición copiada se llama en el juego como tú la llames, y la página de cada munición tiene **Su nombre en el juego**: un nombre o tipo nuevo, en todos los idiomas a la vez, y luego un idioma solo. Aún no probado en el juego.
- **Tipos de bandera propios:** bajo las banderas de una unidad, **Crear o cambiar tipos de bandera…** crea un tipo con nombre: marca las banderas del juego que activa y desactiva. Dáselo a cualquier unidad; quítaselo y sus banderas vuelven a como estaban. Cambia un tipo y cambia cada unidad que lo tiene. El juego solo actúa sobre sus propias banderas, así que un tipo combina lo que ya hacen. Aún no probado en el juego.
- **La velocidad del disparo bien explicada:** la guía de números decía que la velocidad de un disparo, su resistencia, el interruptor «sin física» y el tiempo antes de salir eran solo aspecto. Deciden cuándo llega el impacto: un disparo más lento impacta más tarde, y a un objetivo en movimiento se le apunta por delante según el tiempo de vuelo (por el funcionamiento del juego; aún no probado en una prueba).
- **Cada error en diez idiomas:** los 35 errores del Studio que llegaron con la importación de modelos y el tablero de edificios.
- **Créditos:** el README dice lo que el motor de LittleGroove sigue haciendo en el nuestro, lo que es nuestro, y que nuestro lector de texturas también usa el códec de ProLution.
- **Todavía con fallos, úsalo bajo tu propio criterio:** las texturas de Map Paint y los dos mapas en blanco (Terreno en blanco y Océano en blanco).

**0.9.8.7:** Rehacer y seleccionar lo colocado, colocar en Cuadrícula / Caja / Camino, mapas en blanco más grandes, y cada valor explicado.

- **Corregido, avisado por un modder:** en una unidad nueva hecha a partir de 17 unidades del juego (el Tigre Real, los cañones atómicos, la V2...), la casilla para cambiar su modelo nunca aparecía. El Studio encuentra ahora esos modelos, y si no encuentra uno, la casilla lo dice en vez de desaparecer.
- **La pestaña IA explicada:** cada valor de los jugadores del ordenador dice qué hace, en unidades sencillas, y cuál cuenta en una batalla para cada dificultad y perfil; modos, dificultades, perfiles y unidades elegidos por su nombre.
- **Cada valor explicado, en todas partes:** Todos los valores, la pestaña Unidades, los pinceles de la pestaña Mapas (tamaño en metros, fuerza según lo que hace) y la pestaña Música (cuándo suena cada lista de batalla).
- **La pestaña Economía, Normal y Nuclear por separado:** donde los dos modos difieren, cada uno tiene sus propias casillas. Un cambio solo del modo Nuclear aún no se ha probado en el juego.
- **Rehacer y seleccionar:** Rehacer en cada herramienta del mapa (Ctrl+Y o Ctrl+Mayús+Z, y un botón); en las bandejas Edificios y Objetos y árboles, selecciona lo colocado (clic, Mayús+clic o un recuadro), arrástralo, gíralo, cambia su tamaño o bórralo, también lo del propio mapa.
- **Cuadrícula, Caja y Camino:** filas de objetos en cuadrícula o en caja, edificios de cara a las carreteras, y setos, hileras y franjas de árboles a lo largo de un camino, con cobertura.
- **Mapas en blanco más grandes:** la ventana Tamaño del mapa de un mapa en blanco nuevo añade o quita franjas de terreno en cualquier lado, y Hacer sectores lo llena de sectores.
- **Menús y manejo:** filas de números en vez de deslizadores, una búsqueda con #etiquetas y tus búsquedas recientes, tarjetas emergentes, y teclas reasignables (Cambiar, Quedársela, Cancelar).
- **Más seguro:** cerrar con trabajo sin guardar pregunta antes; un mapa con terreno nuevo aislado se rechaza antes de Probar en el juego; un mod hecho con un Studio más antiguo se actualiza tras una copia de seguridad (Actualizar este mod); los resultados de construcción guardados siguen valiendo tras una actualización del Studio.
- **Cada mensaje en diez idiomas:** los errores del Studio y las líneas de la construcción.
- **Unidad nueva** deja fuera las dos unidades sin modelo del que partir (el cañón SOLO de 57 mm y los paracaidistas SOLO).
- Aún no probado en el juego: lo colocado con Cuadrícula, Caja y Camino, los objetos movidos y un mapa más grande hecho en el Studio.
- **Todavía con fallos, úsalo bajo tu propio criterio:** las texturas de Map Paint y los dos mapas en blanco (Terreno en blanco y Océano en blanco).

**0.9.8.6:** cada bandera y cada número de las unidades explicados, las herramientas del mapa muestran lo que hicieron, y los mapas en blanco bien dibujados.

- **Las banderas de las unidades explicadas:** cada bandera en la página de una unidad muestra su nombre, y al pasar el ratón se ve qué hace, cómo usarla y lo seguros que estamos. **Guía de banderas: todas explicadas** lista las 105, con una búsqueda. El Studio revisa las banderas de una unidad: un cierre conocido del juego (las banderas de un camión en algo que no es un camión, un avión armado con la bandera de reconocimiento sin la de caza) muestra su arreglo, y el Studio no inicia el juego hasta que esté arreglado; las banderas que se espera que rompan una unidad dan un aviso.
- **Cada número explicado:** pasa el ratón por el nombre de cualquier número de una unidad o un edificio para ver qué significa; a su lado, su valor en unidades sencillas (metros, km/h, segundos, grados, $, %), un deslizador para hacerlo más pequeño o más grande que el valor del juego (su valor base, de -90 % a +300 %), y dónde queda entre las unidades del juego de su tipo. Las velocidades van en los km/h del juego.
- **Cómo funcionan las armas y la munición**, paso a paso, en el recuadro Armas.
- **Las herramientas del mapa muestran lo que hicieron:** Cobertura, Descubrir, Pueblo, Bosque, Bloquear y Abrir marcan el suelo por el que pasó cada trazo y dicen cuántos m² cambiaron para las unidades, o que nada cambió. Pueblo funciona en metros reales y rodea primero los edificios que cubrirá un clic.
- **Colocar:** los edificios, árboles y objetos colocados muestran sus modelos reales (con un punto a sus pies); el elegido se ve transparente bajo el puntero antes del clic; la lista para colocar es una cuadrícula de imágenes. Los árboles ya no salen negros, y los números de sector se ocultan cuando la cámara está cerca.
- **Mapas en blanco** (visto en el juego en un Terreno en blanco): sombras sobre el suelo llano; lo que colocas donde el mapa copiado tenía mar se dibuja; el suelo de la cámara sigue al nuevo terreno.
- **Todavía con fallos, úsalo bajo tu propio criterio:** las texturas de Map Paint y los dos mapas en blanco (Terreno en blanco y Océano en blanco).

**0.9.8.5:** aviones en cualquier papel, armas que alcanzan a los aviones y una biblioteca para el pincel Textura de Map Paint.

- **El papel de un avión** (aviso de un jugador: un cazabombardero al que se le daban las bombas en alfombra de un bombardero volaba hasta su objetivo y no soltaba nada): una nueva casilla Papel en la página de un avión lo convierte en Caza, Cazabombardero, Bombardero o Explorador. Su comportamiento, cómo lo usan los jugadores del ordenador y sus palabras en el menú de construcción cambian con él. Las bombas de un bombardero van en una bodega de bombas (copiada de la de un bombardero del juego), la única forma en que la pasada de un bombardero las suelta. Visto en el juego: un cazabombardero convertido en bombardero suelta sus bombas; un explorador que conserva sus armas (un Stuka, un ME109) sigue atacando y tiene la vista de los exploradores.
- **Vehículos de reconocimiento:** la casilla Papel de un vehículo terrestre lo convierte en Reconocimiento: la vista de los coches de reconocimiento (mucho más lejos que la de un tanque), cómo los usan los jugadores del ordenador, sus palabras en el menú de construcción, y puede entrar en los bosques (visto en el juego con un Panzer IV).
- **A qué alcanza un arma:** el Alcanza de cada arma elige el suelo, los aviones o ambos (una segunda arma a su lado, como los cañones antiaéreos del juego llevan una para cada cosa). Visto en el juego: proyectiles de tanque disparando a aviones. Conocido: un arma de avión puesta para alcanzar solo el suelo aún no hace daño.
- **El pincel Textura de Map Paint tiene una biblioteca:** las texturas de suelo del juego (hierba, campos, arena, nieve, roca, carreteras..., por teatro, con una búsqueda), un cuadrado del suelo de cualquier mapa, imágenes tuyas e imágenes gratuitas en línea (Poly Haven y ambientCG, CC0; fotos aéreas de EE. UU., dominio público), una imagen descargada por clic y guardada en tu mod con su crédito. Un deslizador Tamaño, las texturas usadas últimamente y **Detalle del juego de cerca**, que pone las calcomanías propias del juego de una textura del juego sobre el suelo que pintas. Aún no visto en el juego; las descargas en línea aún no probadas.
- **Los objetos colocados en terreno abierto**, lejos de los pueblos, granjas y bosques del mapa, ahora están al alcance del dibujado del juego, y los grupos grandes de objetos nuevos se ordenan como los del juego (aún no visto en el juego).
- **Repintar más rápido:** el suelo pintado se guarda de una construcción a otra, sea cual sea la copia o el mod que lo pintó: un mapa repintado igual lo recupera en segundos, no en minutos.
- **Todavía con fallos, úsalo bajo tu propio criterio:** las texturas de Map Paint y los dos mapas en blanco (Terreno en blanco y Océano en blanco).

**0.9.8.4:** tus propias misiones, mapas en blanco para construir y mucho más para personalizar.

- **Todavía con fallos, úsalo bajo tu propio criterio:** las texturas de Map Paint y los dos mapas en blanco (Terreno en blanco y Océano en blanco).
- **Tus propias misiones:** una nueva Operación o un nuevo capítulo de campaña tiene su propia misión en el lado Escenario de la pantalla del mapa: bandos, objetivos, eventos (Cuando → Hacer: traer unidades, mover, atacar, mantener una zona, artillería, bombardeo, paracaidistas, mensajes, dinero, victoria, derrota) y movimientos de cámara. Visto en el juego: su movimiento de cámara, los objetivos (una zona, un grupo destruido, un tiempo), eventos que se repiten, el dinero, un bando entregado al ordenador. Aún no probado: los paracaidistas, un movimiento de cámara lanzado por un evento.
- **Mapa | Escenario** en la pantalla del mapa: lo del otro lado se ve atenuado y no se puede agarrar por error.
- **Mapas en blanco:** ya no se ve nada del mapa copiado, y tú colocas el CG de cada jugador (la construcción espera a que estén todos colocados). Terreno en blanco sirve también para Operaciones y capítulos de campaña.
- **Tus propios sectores:** píntalos, arrastra sus esquinas, dibuja uno nuevo como un recuadro, deja terreno sin sector, borra uno (visto en el juego).
- **Depósitos de suministros:** la pestaña Economía da más camiones a cada depósito de cada mapa, o de un mapa (veces, o un número cada uno); se acabó el tope de 1.000 camiones.
- **Pestaña Naciones:** oculta de una vez todas las unidades de una nación, muéstralas de nuevo o llena sus menús con las unidades de una época.
- **Editar un mod instalado:** abre cualquier mod del Launcher; el de otra persona se convierte en una copia tuya con su propio nombre. Los mods de RUSE Mod Manager (.rmod) se convierten para que sus valores se puedan cambiar.
- **La comprobación del mod en palabras sencillas**, con un botón para arreglar cada problema.
- **Un aspecto propio para una unidad:** su propia copia del modelo para repintar; los pelotones llevan el uniforme por defecto o uno personalizado; elige el camión en el que viaja un pelotón o un cañón. La infantería se ve en 3D y se abre en Blender.
- **El blindaje** se elige entre los niveles del juego, así la tarjeta muestra con qué lucha la unidad; **los aviones importados** conservan sus hélices girando y vuelven mirando hacia delante (ambos vistos en el juego).
- **Tamaños de modelo en un deslizador** (Diminuto, Tamaño del juego, Tamaño real, Enorme: de 0,05 a 20), cambiables cuando quieras, todos los aviones de una vez.
- **Más para cambiar:** un valor propio de una dificultad o un perfil de la IA para uno que solo Por defecto incluye; números más allá de los deslizadores de las herramientas del mapa; retoques de música más fuertes y más largos.
- **Corregido:** una unidad mostrada en un menú pero investigada desde una oculta detenía el juego: la comprobación la nombra y la construcción la rechaza. Los tanques vuelven a disparar a través de pueblos borrados, y las unidades ya no caen en los huecos donde se quitaron puentes (visto en el juego).
- **Las descargas funcionan en cualquier PC:** cuando Windows aún no ha obtenido el certificado con el que se comprueba GitHub, el Studio se lo pide, como hace un navegador, y lo vuelve a intentar (aún no probado en un PC que tuviera el problema).

**0.9.8.3:** las copias con mods van donde tú digas.

- **Dónde van las copias con mods**, en Ajustes: elige la carpeta donde se construye la copia del juego con mods, o
  vuelve al lugar recomendado, `RUSE-Instances` en la unidad del juego (allí la copia comparte los archivos del juego
  y está lista en segundos; en otra unidad es una copia completa del juego, más lenta y más grande). La copia de
  seguridad limpia del juego va al lado. El próximo Probar en el juego construye en el nuevo lugar; la carpeta antigua
  puede borrarse a mano. El Launcher usa la misma carpeta.

**0.9.8.2:** llegan las unidades de otras épocas: sus modelos, a tamaño real, tras una investigación.

- **Unidades de otras épocas:** las épocas WWI, WWII+, Guerra Fría y Moderna de la pestaña Unidades ya tienen sus
  unidades: 366, cada una el modelo gratuito de otro autor (CC0 o CC BY), citado. Cada época se descarga en el Studio
  cuando la eliges, desde nuestro GitHub (cada archivo comprobado: WWI 232 MB, WWII+ 198 MB, Guerra Fría 996 MB,
  Moderna 709 MB), y se actualiza sola a medida que se terminan más.
  - **A tamaño real:** el ancho real de cada unidad (en un avión, su envergadura) a la escala del juego; se cambia de
    0,2 a 5 veces.
  - **Investigadas como las unidades del juego:** desde cualquier unidad del edificio de su nación, también las
    unidades de época del mod, así funciona una cadena (un T-80, luego un T-90M), con precio y tiempo de
    investigación. Las unidades WWI y WWII+ se compran directamente; las de la Guerra Fría y Modernas empiezan
    investigadas desde una unidad adecuada.
  - **Sus propias cartas** en el menú de construcción y al seleccionarlas.
  - Visto en el juego: cargan al instante, las pestañas de investigación y una cadena, un Land Rover con su propio
    modelo, los tamaños. Aún no probado: los cañones remolcados (aún no hay un cañón del juego al que ajustarlos).
- **Importar modelo…:** un modelo que empieza con una figura de tripulante tiene ahora su propio modelo (los jeeps
  copiados del Kübelwagen mostraban el del Kübelwagen); los modelos pintados en specular-glossiness conservan su
  pintura; los colores dados como números ya no salen negros; los modelos grandes se importan más rápido.
- **Una unidad investigada desde la unidad de otro ejército** dejaba el juego en una pantalla de carga sin fin:
  **Nueva unidad…** quita ahora ese enlace, y la construcción rechaza una unidad investigada desde una unidad que
  falta o de otra nación, diciendo por qué y cómo arreglarlo.
- **Quitar una unidad de la que se investigan otras:** elige en **Ajustes > Investigación** que te avise antes (por
  defecto), negarse, o volver a enlazarlas con su propio padre; una unidad que apunta a una que ya no está lo muestra
  en su página y en la comprobación. Los tiempos de investigación se escriben en segundos o minutos (que el juego los
  cuente en segundos aún no se ha probado en el juego).
- **Linux y Steam Deck (con Proton):** el Studio se abre en tu navegador web cuando su propia ventana no puede. Aún
  no probado en Linux: cuéntanos qué tal va.

**0.9.8.1:** Las herramientas de LittleGroove llegan al Studio, con música y sonidos y una nación convertida en otra.

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
- **Unidades de otras épocas:** la pestaña Unidades ofrece las épocas WWI, WWII+, Guerra Fría y Moderna junto a las
  unidades del juego. Aún no tienen unidades: llegarán en una próxima actualización.
- **Mapa nuevo: empezar desde cero…** está en la pestaña Mapas antes de abrir un mapa.
- **El suelo de Terreno en blanco se dibuja como propio.** Un mapa nuevo empezado en blanco tiene el suelo hecho a
  partir de tus trazos de terreno, no el suelo del mapa del juego desplazado: costas redondeadas de cerca y desde lo
  alto, sin abolladuras en las cimas, y edificios y tanques asentados justo encima. Visto en el juego en mapas de
  prueba.
- **Océano en blanco se queda, con un aviso** en su botón: las islas separadas no están listas para batallas
  a gran escala (abajo).

Aún no probado en el juego: el recuadro Mejora, Todos los valores, Archivos, las herramientas de misiones, los
añadidos a los mapas y los sonidos de fondo.

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
