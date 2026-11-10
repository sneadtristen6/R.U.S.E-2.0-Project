**RUSE Launcher 0.4, para jugadores.** Encuentra R.U.S.E. a través de Steam, y **Jugar** construye una copia del juego
con tus mods y la inicia. Tu instalación de Steam nunca se modifica.

**0.4.8.17:** Los modelos importados se colocan donde está la unidad, con sus torretas y hélices en su propio sitio; una munición puede tener su propia clase de arma.

- **Una actualización obligatoria:** las versiones anteriores ya no se pueden usar. Al abrirse, la aplicación la instala sola, y **Jugar** espera hasta que esté instalada.
- **Mods con modelos importados del nuevo tipo:** el Studio ahora ajusta el modelo importado de una unidad donde está la unidad, con su propio esqueleto, así que su torreta gira donde está la torreta del modelo y las hélices de un avión giran donde las tiene el modelo, tantas como tenga; los soldados, la dotación de un cañón y más aviones también pueden llevar modelos propios. Juega esos mods con este Launcher o uno más nuevo: uno más antiguo da al modelo el esqueleto de la unidad copiada, así que su torreta gira alrededor del punto equivocado. Los mods hechos antes se juegan como antes. Probado en el juego en copias de prueba construidas como construye el Launcher; aún no jugado desde el propio Launcher.
- **La propia clase de arma de una munición:** un mod ahora puede dar a una munición su propio daño contra cada tipo de objetivo (hecho en la página de munición del Studio). Nada cambió en el Launcher para ello: un mod así se construye como cualquier otro.

**0.4.8.16:** Solucionar problemas conserva las copias del juego que hiciste tú.

- **Corregido: «Borrarlas» en Solucionar problemas eliminaba copias hechas por ti.** Una copia del juego construida a mano en la carpeta de copias, una copia de prueba o una copia de referencia contaba como sobrante, y «Borrarlas» la eliminaba para siempre, no a la Papelera. Toda copia construida que no sea la copia con mods de la app lleva ahora una pequeña nota «conservar», y una copia que la tiene nunca es un sobrante: Solucionar problemas solo borra los sobrantes de las propias apps (copias a medio construir, las que versiones antiguas hacían por cada conjunto de mods). Lo vimos en nuestro propio PC el 1 de noviembre, cuando se llevó todas las copias de prueba. Una copia construida antes de esta versión aún no tiene nota: reconstrúyela una vez con esta versión, o no toques «Borrarlas» hasta entonces.

**0.4.8.15:** Original también tiene el título R.U.S.E. 2.0 dorado.

- **Original también tiene el título R.U.S.E. 2.0 dorado:** Jugar en Original ahora construye la copia con mods sin ningún mod y con el título dorado, e inicia el juego desde ella, como hace un conjunto de mods: la primera vez la construye y después arranca enseguida, salvo que entre medias hayas jugado un conjunto de mods. RUSE Guard funciona en sus partidas multijugador, como en las de cada conjunto. Desmarca el título dorado en Ajustes y Original se inicia a través de Steam como antes. Tu instalación de Steam nunca se modifica.

**0.4.8.14:** Los mods con un script de partida propio vuelven a construirse.

- **Corregido: Jugar se detenía con algunos conjuntos de mods** con «RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...»: algunos mods traen su propio script de partida, cuya cabecera pide más espacio del que el script necesita (entre ellos 1 VS 7 AI, 1 VS 15 AI, Operation Overlord y Sand Box). El juego ejecuta esos scripts sin problema, pero el Launcher los rechazaba, así que no se podía construir ningún conjunto con uno de esos mods. Ahora los lee como el juego.

**0.4.8.13:** Los informes de fallos del juego dicen qué llevó al fallo.

- **Los informes de fallos del juego de Bug Watch dicen más:** si marcaste Bug Watch y el juego falla, el informe ahora también dice qué intentaba leer o escribir el juego, y hasta 16 puntos del juego que llevaron al fallo, leídos del propio informe de fallo del juego en tu PC, que sigue sin salir nunca de él. Un informe que solo decía dónde se detuvo el juego no podía mostrar por qué; ahora podemos rastrear fallos como el que un jugador nos envió esta semana, y corregirlos.
- **El acuerdo, versión 3:** ahora enumera estas dos novedades entre lo que contiene un informe de fallo del juego, y nada más ha cambiado. Como ha cambiado, ambas aplicaciones te lo muestran una vez más al abrirse.

**0.4.8.12:** Jugar vuelve a construir los juegos con mods.

- **Corregido: Jugar se detenía con cada conjunto de mods** con «No such file or directory: ...fairplay_watch.bin»: a los instaladores de 0.4.8.10 y 0.4.8.11 les faltaban tres archivos de RUSE Guard, así que no se podía construir ningún juego con mods. Ya están de vuelta, y una aplicación a la que le falte alguno de sus archivos ya no se puede publicar.

**0.4.8.11:** el inicio de sesión con Steam termina en las aplicaciones; en Linux, los programas auxiliares de una construcción arrancan como en Windows.

- **Arreglado: inicio de sesión con Steam.** Después de iniciar sesión en la página de Steam, el Launcher y el Studio seguían esperando y nunca preguntaban a nuestro servidor si habías terminado: la ventana detenía sus propias comprobaciones antes de la primera. Ahora comprueba cada pocos segundos y te conecta en cuanto Steam lo confirma. Probado en la vista previa: la comprobación se hace y la ventana te muestra conectado.
- **Los programas auxiliares arrancan de cero en todos los sistemas:** los programas entre los que una construcción reparte su trabajo (modelos importados, reparación del mapa, movimiento, agua) ahora arrancan de cero también en Linux, como siempre lo han hecho en Windows. En Linux arrancaban como copias de la aplicación en marcha, lo que a veces podía colgar una construcción, e hizo fallar allí una de nuestras comprobaciones. No cambia nada en Windows ni con Proton en Steam Deck.

**0.4.8.10:** mods de más de 4 GB, listas de construcción en grupos, construcciones más rápidas de mods grandes, el persa y cada página en 11 idiomas, arreglos de informes de probadores; y RUSE Guard, nuestro anti-trampas para las partidas multijugador reales, con un código de partida; Bug Watch, informes de fallos y uso que puedes activar; el inicio de sesión con Steam; y un acuerdo al primer inicio.

- **Arreglado, informado por un jugador: mods de más de 4 GB.** Un conjunto de mods cuyo juego con mods pasaba de 4 GB dejaba de construirse al pulsar Jugar («'I' format requires 0 <= number <= 4294967295»). Ahora los paquetes llevan su longitud completa, y uno de más de 4 GB se escribe en una disposición más amplia que el juego puede leer gracias a un pequeño parche del juego: se descarga una vez y se aplica solo a tu copia con mods, nunca al juego de tu carpeta de Steam. Por encima de 32 GB, o para un solo archivo de más de 4 GB, la construcción lo dice claramente. Probado en el juego: copias de más de 4 GB, y con 200, 283 y las 366 unidades de otras épocas.
- **Muchos modelos propios:** el juego encuentra las texturas sustitutas de un paquete mediante un índice, y una construcción que añadía algunas para modelos importados lo escribía mal: con muchas unidades de otras épocas, el juego se colgaba o fallaba al cargar. Ahora se escribe como el juego lo lee, para cada mod que las añade. Probado en el juego con las 366 unidades de otras épocas.
- **Listas de construcción en grupos:** un mod con muchas unidades tiene la lista de construcción de cada edificio en grupos, las líneas del propio juego: como mucho 6 unidades por grupo y 10 grupos por edificio, para que toda la lista quepa en la pantalla y cada unidad se pueda construir. Un mod hecho antes que pasa de estos límites se construye igualmente, con un aviso. Probado en el juego con 297 unidades de otras épocas en grupos.
- **Construcciones más rápidas:** los modelos de tus mods se guardan entre construcciones, y los nuevos se hacen en paralelo en los núcleos de tu PC. Un mod con 366 unidades de otras épocas tardaba unos 18 minutos en construirse en un PC de 8 núcleos; ahora unos 5 la primera vez y unos 3 después, con los mismos archivos del juego, byte a byte.
- **Informes de probadores:** un mod de unidades y los cambios de un mapa hechos con el mismo nombre se construyen juntos (detenían Jugar); un mapa cuyos puentes propios se han quitado se construye con los puentes nuevos; las piezas de torreta y los cañones remolcados importados se construyen como los hace el Studio 0.9.8.10. Los puentes y las piezas de torreta aún no probados en el juego.
- **Tus archivos:** Quitar envía un mod de la biblioteca a la Papelera de reciclaje, Mostrar en la carpeta abre un mod donde está, y los Ajustes muestran dónde se guardan tus archivos. Visto en una vista previa; aún no probado en la ventana de la aplicación.
- **Persa y 11 idiomas:** el persa es el 11.º idioma de las aplicaciones, escrito de derecha a izquierda; el README, la wiki, estas notas y las pantallas de instalación están en los 11.
- **Actualizaciones obligatorias:** una actualización que marcamos como obligatoria se instala sola, con una ventana que nadie puede cerrar (las aplicaciones desde esta versión saben leer la marca).
- **Solo copias propias:** antes de que Jugar construya una copia con mods, las aplicaciones comprueban que la carpeta del juego es una copia tuya, por lo que Steam dejó allí, en Windows, con Proton en Steam Deck y en Linux. Si la tuya no se puede confirmar (una copia en caja de antes de que R.U.S.E. estuviera en Steam), una ventana te deja abrir una solicitud, y te enviamos un código de desbloqueo para ese PC.
- **Discord:** las aplicaciones y las páginas usan una invitación nueva que no caduca.
- **Un acuerdo al primer inicio:** la primera vez que el Studio o el Launcher se abre, explica qué hace RUSE Guard y te pide aceptarlo (hace falta para jugar en línea con las aplicaciones), si quieres activar Bug Watch (opcional), y un nombre de usuario que nuestros desarrolladores ven con tus informes: se le añaden un # y cuatro números para que sea único, como Nick#4821. Un solo nombre sirve para ambas aplicaciones. El acuerdo vuelve a mostrarse cuando cambia. Visto en ambas aplicaciones. En los 11 idiomas.
- **RUSE Guard:** nuestro anti-trampas, según el diseño de DomesticNukes. Solo funciona en partidas multijugador y cooperativas, nunca en un jugador, en escaramuza contra el ordenador ni en la campaña. Tu juego con mods recibe un **código de partida** para enviar a la gente con la que juegas: el mismo código significa el mismo juego, la misma versión, los mismos mods y versiones de mods, para que una partida no pueda desincronizarse. Un mod que cambia los scripts del juego muestra la insignia **Ejecuta scripts**, y Jugar espera a que marques que confías en su autor; un truco o una herramienta de prueba muestra **Truco** y hace la copia solo sin conexión: abandona por sí misma las partidas multijugador y cooperativas. Durante una partida real RUSE Guard compara los nombres de tus programas en ejecución con una lista de herramientas de trampas conocidas (solo los nombres; no lee nada más), y lo que recoge se archiva con tu nombre de usuario, nunca con tu cuenta de Steam. Probado en partidas multijugador contra un rival real; las pruebas llegan a nuestro servidor.
- **Bug Watch (opcional):** cuando lo marcas, el Studio y el Launcher cuentan qué usas y cuándo algo falla, los fallos de las aplicaciones y los del juego, con los mods que estaban activos, y lo envían una vez al día a nuestros desarrolladores con tu nombre de usuario. Sin nombres reales, sin cuenta de Steam, sin archivos. Desactivado salvo que lo marques; desmárcalo cuando quieras y lo guardado se borra. Visto en ambas aplicaciones.
- **Iniciar sesión con Steam:** un inicio de sesión en la propia página de Steam en tu navegador confirma que posees R.U.S.E., para el juego en línea, RUSE Guard y las descargas de contenido. Nunca vemos tu contraseña, y tu ID de Steam nunca se guarda: solo un pase guardado en tu PC durante 30 días. Está en Ajustes, **Inicio de sesión con Steam**; el Launcher lo pide una vez. Nada lo necesita todavía. Aún no probado en la aplicación.

**0.4.8.9:** los mods se instalan en más PC, y una lectura de imágenes más segura.

- **Corregido, avisado por un jugador:** en algunos PC no se instalaba ningún mod: «este PC no confía en el certificado de seguridad del sitio (unable to get issuer certificate)». Windows en esos PC no tiene el certificado con el que se comprueban las descargas de GitHub y no puede obtenerlo. El Launcher ahora también lo intenta con la lista de certificados de Firefox, que lleva consigo. Mientras tanto, un mod descargado en el navegador desde la lista de mods se instala con **Añadir un archivo de mod…**.
- **Imágenes más seguras:** la biblioteca con la que el Launcher lee las imágenes (Pillow) pasa a la versión 13.0.0, con sus correcciones contra archivos de imagen hechos a propósito que podían cerrar la aplicación, agotar su memoria o algo peor.
- **Código más estricto:** los 12 avisos de la revisión de código de GitHub sobre este proyecto están resueltos. Cuando el Launcher muestra sus páginas en tu navegador, solo abren sus propios archivos, comprobados de una forma que esa revisión reconoce, y las descargas piden TLS 1.2 o más reciente, como ya hacían. Nada cambia en cómo funciona el Launcher.

**0.4.8.8:** ejecuta los mods hechos con Studio 0.9.8.8, y tu juego con mods dice R.U.S.E. 2.0 en oro.

- **Los mods hechos con Studio 0.9.8.8 se juegan:** edificios propios (el segundo y el tercero de una nación necesitan un pequeño parche del juego, descargado una vez y aplicado solo a tu copia del juego con mods, nunca al juego de tu carpeta de Steam), el aspecto propio de los edificios nuevos y los objetos, sonidos y animaciones cambiados con RUSE Decoy, los valores de los jugadores del ordenador y las reglas del juego, y los cruces de los puentes viejos cerrados.
- **R.U.S.E. 2.0 en oro:** tu juego con mods se abre con una escena de batalla y un motor que arranca, y su menú principal, el título pequeño de cada menú, los contornos de los menús y las pantallas de carga dicen R.U.S.E. 2.0 en oro. Se hace en tu PC con los archivos de tu propio juego la primera vez (unos minutos una vez, luego se guarda). Ajustes tiene una casilla para conservar el título del juego.
- **Corregido: manchas oscuras y claras en los mapas hechos con el Studio** (mapas en blanco, ampliados, de relieve y de sectores): un mapa así se ilumina bien una vez construido con esta versión (su suelo se rehace la primera vez).
- **Corregido, avisado por un jugador:** en la página Mods compatibles, «Nuevo conjunto de mods…» no hacía nada. Ahora abre el conjunto nuevo. Aún no probado en la propia aplicación.
- **Las letras del juego:** el Launcher está escrito con la fuente de los menús del juego, tomada de tu juego cada vez que arranca.
- **Todavía con fallos, juégalo bajo tu propio criterio:** los mapas hechos con las texturas de Map Paint, y los mapas en blanco (Terreno en blanco, Océano en blanco).

**0.4.8.7:** ejecuta los mods hechos con Studio 0.9.8.7.

- **Los mods hechos con Studio 0.9.8.7 se juegan:** objetos movidos o colocados en cuadrícula, en caja y a lo largo de caminos, mapas en blanco más grandes con sus sectores, y cambios de economía solo del modo Nuclear.
- **Las líneas de la construcción en tu idioma**, en los diez.
- **Los resultados de construcción guardados siguen valiendo tras una actualización.**
- **Todavía con fallos, juégalo bajo tu propio criterio:** los mapas hechos con las texturas de Map Paint, y los mapas en blanco (Terreno en blanco, Océano en blanco).

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

**0.4.6:** **Jugar** arranca al instante cuando nada ha cambiado, y juega los mods hechos con Studio 0.9.6: unidades nuevas
con un modelo 3D propio.

| Antes | Ahora |
|---|---|
| **Jugar** reconstruía toda la copia con mods cada vez, aunque nada hubiera cambiado (un jugador: «esperar 30 minutos cada vez»). | Sin cambios: el juego arranca al instante. Un cambio reconstruye, pero se reutilizan los archivos sin cambios de la última copia, así que una copia en otra unidad distinta de la del juego ya no vuelve a copiar todos los paquetes. Jugar dice cuánto copió. |
| Cada construcción leía de nuevo los datos de las unidades del juego. | Se guardan entre construcciones: un mod de prueba grande tardaba 213 s cada vez; ahora las construcciones que siguen a la primera tardan 68 s. |
| La unidad nueva de un mod tenía el modelo de la unidad que copia. | Su propio modelo del mod (`files/models`) está en el juego. **Visto en el juego:** un M1 Abrams junto al Sherman. |
| La unidad nueva de un mod con su propia tarjeta cerraba el juego al construirse. | Corregido. **Visto en el juego.** |
| Los colores de las unidades repintadas salían un poco desviados en algunos sitios. | Más cerca de la imagen del mod. Un mod con unidades repintadas o suelo pintado recibe una huella digital y un código para unirse nuevos: todos los que juegan juntos deberían actualizar. |
| Un arranque lento no dejaba ninguna pista. | **Copiar el informe** lista los pasos de los cinco últimos arranques. |
| — | Juega los mods con el borrado de todo el mapa, las carreteras sobre suelo remodelado y el relleno de cauces de Studio 0.9.6 (nuevo, aún no visto en el juego a gran escala). |

**0.4.5:** juega los mods hechos con Studio 0.9.5: unidades repintadas, sus propias tarjetas y unidades con modelos propios.

| Antes | Ahora |
|---|---|
| Un mod no podía cambiar el aspecto de una unidad. | Las unidades repintadas y las tarjetas de un mod se ven en el juego. **Visto en el juego:** un Sherman rojo, una tarjeta hecha en el Studio. |
| El juego descartaba un mod cuyos paquetes de modelos de unidades crecían: un cierre en la primera fábrica. | Se construyen como el juego los comprueba. **Visto en el juego:** un segundo Sherman con un modelo propio. |
| Un mod que hacía aparecer unidades de otra nación en un capítulo de campaña o en una Operación se cerraba al cargar (unidades francesas en Holanda). | Sus modelos también se cargan allí. **Visto en el juego.** |
| Aplanar las montañas del borde de un mapa dejaba allí un acantilado. | El borde sigue al suelo. **Visto en el juego.** |

**0.4.4:** juega los mods con mapas nuevos, hechos con Duplicar mapa de Studio 0.9.4.

| Antes | Ahora |
|---|---|
| Los mapas nuevos de un mod no se habían probado en el juego. | **Visto en el juego:** el mapa nuevo de un mod aparece en BATALLAS y se juega con su propio suelo, 101 a la vez. Aún es pronto: cuéntanos lo que encuentres. |
| Las actualizaciones llegaban solo como versiones completas. | Pequeñas correcciones pueden llegar entre versiones (0.4.4.1), ofrecidas como cualquier actualización. |

**0.4.3:** juega los mods hechos con Studio 0.9.3, y los construye unas tres veces más rápido.

| Antes | Ahora |
|---|---|
| Las rocas y la mayoría de los demás objetos que colocaba un mod desaparecían en cuanto la cámara salía de la distancia corta. | Se dibujan hasta la distancia lejana; los objetos propios del mapa no cambian. **Visto en el juego.** |
| La carretera nueva de un mod a través de un bosque era una franja clara vista desde lo alto, o desaparecía a media-larga distancia. | Pintada a través de los bosques como las carreteras propias del mapa. **Visto en el juego.** |
| Las carreteras de un mod siempre quitaban los árboles de su camino. | Una carretera puede conservarlos (`keep_trees`): pasa bajo los árboles, más tenue y más gris en un bosque. |
| **Jugar** tardaba unos 5 minutos en construir un mod con carreteras nuevas en M03_Italie. | Alrededor de 1½ minutos después de la primera vez en un mapa. |

**0.4.2:** juega los mods hechos con Studio 0.9.2.

| Antes | Ahora |
|---|---|
| Un mod con una carretera sobre el agua en Italia, Alemania, Holanda y otros mapas se rechazaba: su puente «no tendría piso». | Se construye: el puente recibe el piso propio del mapa. Aún no visto en el juego en esos mapas. |
| Un mod que daba unidades al jugador en un capítulo de campaña (bando 0) se rechazaba, y las unidades para los bandos del ordenador recibían el aviso «puede que nunca aparezcan». | Se construye; solo recibe aviso un bando que la misión del capítulo no tiene. |
| En M03_Italie y otros mapas, la carretera nueva de un mod en campo abierto ocultaba de lejos el decorado del mapa, y sus objetos solo se veían de cerca. | La vista lejana del mapa queda como estaba, y los objetos del mod se ven de lejos. Aún no visto en el juego. |

**0.4.1:** tu idioma desde el primer arranque, y un editor de conjuntos de mods que encuentra los mods por su nombre.

| Antes | Ahora |
|---|---|
| Al crear un conjunto de mods se listaba toda tu biblioteca con Crear al final, y no había forma de encontrar un mod por su nombre. | Crear está arriba, con los mods que ya están en el conjunto justo debajo; más abajo, «Añadir mods de tu biblioteca» con una búsqueda que va acortando la lista mientras escribes. |
| El idioma estaba en Ajustes, así que los jugadores no sabían que el Launcher habla su idioma. | El primer arranque pregunta: «Elige tu idioma», cada idioma en sus propias palabras, con el idioma de tu juego en Steam marcado (los jugadores que actualizan lo ven una vez). Luego, un botón de idioma arriba, siempre a la vista. |
| La lista de aplicaciones instaladas de Windows mostraba la primera versión que se instaló. | Muestra la versión que tienes. |

**0.4.0:** juega los mods con carreteras nuevas tal como las construye Studio 0.9: se parecen a las carreteras propias
del mapa, desde lo alto y a ras de suelo (probado en el juego en «Día D»).

![Una carretera nueva de cerca en «Día D»](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Antes | Ahora |
|---|---|
| Las carreteras nuevas de un mod desaparecían de cerca. | Se dibujan con el asfalto y las calcomanías de borde propios del mapa, pintadas como las carreteras del mapa, y se quitan las plantas de su camino. |
| Un mod con muchos círculos de borrado tardaba minutos en construirse. | Mucho más rápido. |

**0.3.3:** juega los mods hechos con Studio 0.8.3.

| Antes | Ahora |
|---|---|
| Un mod con una cámara inicial girada (Studio 0.8.3) se rechazaba. | Se construye: la cámara gira como dice el mod. |
| La cámara inicial de un punto de inicio movido se quedaba en el sitio antiguo. | La cámara se mueve con él; un punto de inicio nuevo recibe su propia cámara. |
| Un mod con un punto de inicio en un bosque se rechazaba. | Se construye: allí funciona un CG. |

**0.3.2:** una sola copia del juego para todo el PC, la versión a la vista y una biblioteca más clara.

| Antes | Ahora |
|---|---|
| Cada conjunto de mods construía su propia copia del juego. | Una sola copia con mods para todo el PC, compartida con el Studio. |
| La versión no se mostraba, y Novedades era una lista. | La versión está junto al nombre, y Novedades abre una tabla de antes/después como esta. |
| Los mapas y los mods se veían iguales en la biblioteca. | Un mapa lleva una insignia MAPA. |
| Pocas descripciones emergentes. | Descripciones emergentes en los controles principales. |
| Los mods con carreteras nuevas en Twilight of the Gods, Alpha, Ostfriesland y Robert no tenían el modelo de carretera del mapa. | También lo reciben. |

**0.3.1:** los mods con unidades de otra nación (un Tiger alemán para EE. UU., por ejemplo) funcionan, incluso en una
partida en la que nadie juega esa nación (probado en el juego, 2026-10-02). Y un aspecto nuevo: los azules de R.U.S.E.
en lugar de negro y oro, y un logotipo nuevo: un caza que sube entre las nubes. La barra lateral tiene dos pestañas,
**Conjuntos de mods** y **Biblioteca de mods**, cada una con toda la altura, así que se llega a toda tu biblioteca (la
mitad quedaba oculta tras la barra de desplazamiento), con una búsqueda y un recuento. El instalador ofrece una
**copia de seguridad limpia del juego** junto al acceso directo del escritorio, y dice por qué.

**0.3.0:** **Mods compatibles:** el Launcher muestra nuestra lista de mods
([sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods)); marca los que quieras y se descargan y
comprueban. En el primer arranque eliges tus mods; los mods de trucos se mantienen aparte y nunca se marcan por ti. Un
botón **Solucionar problemas** (en la barra inferior y en cada mensaje de problema) comprueba de una vez lo que puede
impedir **Jugar** y arregla lo que puede, con un informe para pegar en un informe de error. Una
**copia de seguridad limpia del juego** en Ajustes guarda una copia limpia de los archivos de tu juego y devuelve todo lo que cambió otro
gestor de mods (o deja que Steam lo repare). Los mods hechos con el nuevo Studio funcionan tal como se hicieron: los
tanques y la infantería cruzan los puentes nuevos por el tablero, la infantería sigue las carreteras nuevas, los
bosques despejados quedan abiertos a las unidades, los edificios colocados se asientan en el suelo a cualquier tamaño,
y la cobertura cae donde se pintó en «Día D» y en los demás mapas que no son cuadrados. Problema conocido: las
carreteras nuevas aún no se dibujan de cerca (se ven de lejos).

**0.2.11:** **Jugar** funciona siempre: una copia con mods que Windows no deja borrar (un archivo que enlazó una
versión anterior, un programa que aún lo tiene abierto) se aparta a `RUSE-Instances\.trash` en vez de detener el
juego, y se nombra un juego que aún se ejecuta desde la copia. Los mods con puentes nuevos nunca crean suelo al que
las unidades no pueden llegar (cerraba el juego).

**0.2.9:** **Jugar** funciona cuando los archivos de tu juego están marcados como de solo lectura: fallaba con
«[WinError 5] Access is denied» una vez que una copia con mods quedaba a medio construir. Si el juego aún se ejecuta
desde la copia con mods, se te dice que lo cierres en lugar de recibir un error de Windows. Los mods con carreteras
nuevas construyen sus carreteras pintadas y sus puentes.

**0.2.8:** un mod que añades se comprueba al instante, tal como lo leerá la construcción del juego: un archivo de mapa
roto, o una carpeta de mapa con el nombre del título del mapa (maps/Blitz en lugar de maps/SuperCrossRoads4), se
nombra con su arreglo antes de que Jugar se detenga en él.

**0.2.7:** **Ayuda** e **Informar de un problema** en la barra inferior: la wiki (un manual de campo para jugar con
mods), y un informe de error en tu navegador con la versión del Launcher ya rellenada. Un mensaje de problema tiene su
propio enlace **Informar**. El Launcher no envía nada: tú lees el informe y lo publicas. Los mods cuya carpeta de mapa
lleva el nombre del título del mapa (maps/Blitz en lugar de maps/SuperCrossRoads4) ahora reciben el arreglo.

**0.2.6:** un botón **Ajustes** (arriba a la derecha): el idioma, la carpeta del juego y las actualizaciones en un
solo sitio, listo para más.

**0.2.5:** buscar actualizaciones es más fiable: cuando GitHub rechaza la única comprobación del arranque (permite 60
por hora por dirección de internet, compartidas por todo lo que la usa), el Launcher lee en su lugar la lista de
versiones de GitHub.

**0.2.4:** tu idioma se conserva tras reinicios, actualizaciones y reinstalaciones.

**0.2.3:** el recuadro rojo se pliega como el amarillo (un conjunto grande puede listar docenas de conflictos).

**0.2.2: Poner en el mejor orden.** Cuando los mods de un conjunto cambian los mismos valores, el recuadro amarillo
tiene un botón **Poner en el mejor orden**: los mods que cambian más van primero y los más pequeños después, para que
cada uno conserve tantos cambios como pueda. Dice qué mods salva, y los mods se pueden seguir moviendo a mano.

**0.2.1: los mods que no van juntos no se pueden jugar, y el Launcher dice por qué.** Cuando dos mods de un conjunto
sustituyen el mismo archivo o script, un recuadro rojo nombra los mods y lo que ambos cambian, y Jugar queda
desactivado hasta que se quite uno. Cuando un mod posterior solo sobrescribe valores de uno anterior (la velocidad de
un barco, por ejemplo), un recuadro amarillo los lista y el conjunto se sigue jugando.

**Novedades de la 0.2:**

- **Conjuntos de mods hechos en la ventana:** nuevo, editar, cambiar nombre, duplicar, eliminar y poner los mods en
  orden. Ya no hay archivos que editar a mano. Una guía de tres pasos en la primera pantalla muestra el camino.
- **Añadir un archivo de mod…** (o suéltalo en la ventana): un `.rusemod` exportado por RUSE Studio, una carpeta de mod
  en un `.zip`, o un **`.rmod` de RUSE Mod Manager**, usado tal cual (aplicado por el propio motor de LittleGroove).
- **Compartir un orden de carga** como texto, e **Importar un orden de carga…** de un amigo: el Launcher dice qué mods
  tienes, cuáles faltan y cuáles son de otra versión, y luego crea el conjunto. Es el mismo texto que RUSE Mod Manager
  copia y lee, así que los órdenes de carga van en ambos sentidos.
- **Se actualiza solo:** a partir de esta versión, cuando sale un Launcher más nuevo, una barra lo dice;
  **Actualizar ahora** lo descarga, comprueba su SHA-256 y lo instala, y el Launcher vuelve a arrancar solo.

Tus conjuntos de mods de la 0.1 se conservan. Problemas e ideas: GitHub Issues.

![RUSE Launcher](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/launcher.jpg)
