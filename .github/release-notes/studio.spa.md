**RUSE Studio, una versión preliminar para modders.** Explora las unidades del juego en cualquiera de sus diez
idiomas, cámbialas en un mod propio y pruébalo en el juego. Tu instalación de Steam nunca se modifica.

**0.9.8.20:** Protecciones donde algunos conjuntos de mods detenían el juego; una mejora hecha en otro edificio conserva su unidad; el editor de conjuntos dice por qué, y Jugar espera la comprobación de los mods; la construcción avisa de las misiones que un conjunto deja sin sus lugares, y las unidades de los mods .rmod tienen sus modelos; Bug Watch dice por qué falló una construcción o un Jugar, y la versión 4 del acuerdo; un fallo del juego que conocemos nombra su unidad (Launcher); un soldado propio para un pelotón, cambiado en Blender (Studio); un pelotón soldado a soldado, un solo Abrir en Blender, animaciones para una sola unidad o para las unidades que elijas, modelos con animaciones propias y el Pelotón a caballo genérico (Studio); Eliminar siempre llega hasta el final (Studio); 16 arreglos de nuestras pruebas de lo que hacen los jugadores y 4 arreglos de mapas (Studio); 279 mensajes más en palabras sencillas, en tu idioma; un enlace «¿Problemas? Lee la guía» a nuevas páginas de la wiki (Studio).

- **Protecciones donde los mods detenían el juego:** con el R.U.S.E. Field Manual y el Balance Overhaul Mod juntos, el juego se detenía en cuanto se colocaba la base blindada (informes de fallos de jugadores). Cada juego con mods tiene ahora una protección en tres puntos donde los propios scripts del juego lo detenían: cartas de investigación en la lista de un edificio para una unidad que está en otro edificio, una misión que inicia el jugador del ordenador de un bando que juega una persona, y una misión que cambia unidades después de que una de ellas muriera. Una protección no hace nada salvo donde el juego se habría detenido. Probado en el juego con la base blindada; las dos protecciones de misiones se probaron fuera del juego.
- **Una mejora hecha en otro edificio conserva su unidad:** con los mismos dos mods, investigar el T-34 en la base blindada quitaba el T-26 del cuartel, porque el juego retira una unidad en cuanto se investiga cualquier mejora suya, se fabrique donde se fabrique. La construcción convierte ahora esa mejora en una investigación propia y lo dice en un aviso. Probado en el juego con la URSS e Italia. Cambia algunos conjuntos con el Balance Overhaul Mod y los conjuntos con el Field Manual antes del Balanced Realism Mod; el aviso nombra cada unidad.
- **Códigos de partida:** un conjunto que la construcción cambia así recibe un código de partida nuevo: cada jugador de una partida con él necesita esta versión. Un conjunto con un mod que da a la dotación de un cañón un modelo propio también recibe un código nuevo: la pequeña figura de la dotación vista de lejos ahora tiene el aspecto de ese modelo. Un conjunto con Balanced Realism Mod, Navy Mod, Sand Box, cualquiera de los dos Static Commandable Battleship - All Operations o el R.U.S.E. Field Manual 1.0.0 también recibe un código nuevo: para algunas de sus unidades, los paquetes de unidades de otra nación se cargan ahora en cada escaramuza (abajo). También un conjunto con Operation Overlord u Operation Fortress Europa: con cualquiera de los dos, los paquetes de unidades de EE. UU., Alemania, Reino Unido y Francia se cargan ahora en cada partida (abajo). Los demás conjuntos conservan su código. Tras actualizar, el siguiente **Jugar** o **Probar en el juego** vuelve a construir el juego solo.
- **Misiones que un conjunto deja sin sus lugares (Studio y Launcher):** cuando los mods de un conjunto dejan un capítulo de la campaña, una Operación o el tutorial sin un lugar que su misión vigila desde el principio, la construcción avisa, nombrando el mod y cuántos capítulos de la campaña u Operaciones afecta, o el tutorial: el juego se detiene aproximadamente un segundo después de empezar una misión así. Se comprueba cada mod, sea cual sea su versión, también los tuyos: la construcción lee las misiones de tu propio juego al construir. El conjunto se construye y se juega como antes, y el recuento de avisos de la construcción los incluye. 1 VS 7 AI y 1 VS 15 AI también reciben un aviso así: sustituyen los mapas de un capítulo de la campaña por otros a los que les faltan lugares que usan sus misiones, y el aviso se queda hasta que ese capítulo se pruebe con ellos en el juego. Comprobado con construcciones de los mods de la comunidad; todavía no probado en el juego.
- **Las unidades de los mods .rmod tienen sus modelos (Studio y Launcher):** una unidad que un mod .rmod (el formato de RUSE Mod Manager) crea, o pasa a otra nación, recibe ahora la misma comprobación de modelo que la unidad de un mod del Studio, en cualquier conjunto y con el mod solo: cuando su modelo solo está en los paquetes de unidades de otra nación, la construcción hace que esos paquetes se carguen en cada escaramuza, para que tenga su modelo también en partidas donde ningún jugador tiene esa nación, y una nota nombra la unidad como su carta; donde eso no se puede, la construcción rechaza el conjunto y dice por qué. Lo mismo vale para una unidad que el mapa de un mod .rmod coloca y que la versión del juego de ese mapa no coloca: Operation Overlord y Operation Fortress Europa colocan unidades británicas y francesas, junto a unidades estadounidenses y alemanas, en el mapa del capítulo Utah Beach de la campaña, así que con cualquiera de los dos los paquetes de unidades de EE. UU., Alemania, Reino Unido y Francia se cargan ahora en cada escaramuza, cada capítulo de la campaña y cada Operación. Todavía no probado en el juego.
- **El editor de conjuntos del Launcher dice por qué:** cuando no puede crear o guardar un conjunto (ningún mod marcado, o un mod que ya no está en la biblioteca), ahora lo dice dentro del editor, bajo sus botones. Antes el mensaje iba a la página del conjunto, oculta tras el editor, y parecía que no pasaba nada. **Crear** y **Guardar** esperan a que haya un mod marcado. Probado en una vista previa de la pantalla, aún no en el Launcher instalado.
- **Jugar espera la comprobación de los mods (Launcher):** **Jugar** sigue apagado hasta que el Launcher ha comprobado si los mods del conjunto van bien juntos, y su texto de ayuda dice por qué. Antes, un **Jugar** rápido podía mandar a la construcción un conjunto cuyos mods no van bien juntos, y la construcción lo rechazaba allí. Comprobado con pruebas; todavía no probado en el Launcher instalado.
- **Misiones propias (Studio):** la misión de un mapa nuevo que crea unidades de una nación que la misión copiada no carga recibe ahora los paquetes de esa nación, así que esas unidades tienen sus modelos (el juego se detenía al crearse una unidad así). La comprobación de misiones rechaza también un evento que entrega al ordenador un bando que juega una persona. Comprobado leyendo una construcción real; aún no probado en el juego.
- **Modelos de Blender y Uniforme personalizado (Studio):** los puntos que Blender deja sin hueso siguen al hueso raíz, y la página dice cuántos son. **Importar modelo…** ahora también funciona en una unidad con **Uniforme personalizado**: quita la copia, y **Usar el modelo de la unidad copiada** la devuelve con un clic. Probado en el juego con un soldado de un pelotón ponderado en Blender; la parte del Uniforme personalizado se comprobó fuera del juego.
- **Un pelotón, soldado a soldado (Studio):** la página de un pelotón ahora empieza con su carta del pelotón y una línea para cada soldado, en lugar de su cuadro **Su propio modelo**. **Abrir en Blender**, en su carta, abre a sus soldados uno al lado del otro, cada uno con su propia copia de sus imágenes; tras **Enviar a R.U.S.E. Studio** en Blender, **Traer mis cambios** da a cada soldado solo lo que se le hizo a él. En su línea, un soldado tiene **Importar un modelo…** y, cuando tiene un modelo propio, **Volver al aspecto del juego**. Vistas de lejos, las figuritas del pelotón llevan el aspecto que lleva la mayoría de sus soldados. Probado en el juego con un pelotón en el que solo el soldado con bazuca estaba pintado de rojo.
- **Un solo Abrir en Blender (Studio):** la página de una unidad tiene un solo **Abrir en Blender**: en la carta de un pelotón, y para cualquier otra unidad en su fila **Modelo**, bajo **Más**, en el cuadro **Cambiarlo en Blender**. **Qué va a Blender ▾**, a su lado, marca lo que va: los soldados de un pelotón (para un pelotón con huesos propios, como el Pelotón a caballo genérico, qué modelo), **Sus huesos** para un modelo con huesos propios, y **Su pintura**; desmarca uno y **Traer mis cambios** lo deja como estaba. Mientras Blender tiene la unidad, el botón pasa a ser **Traer mis cambios**. Una unidad del propio juego que no es un pelotón envía solo su pintura, como hacía **Repintar en Blender**: cópiala primero para cambiar su modelo. Un modelo con huesos propios va a Blender con sus animaciones: la que no cambias allí vuelve exactamente como se fue, y de la que cambias solo son nuevos los huesos que cambiaste; un cambio hecho en RUSE Decoy mientras Blender tiene el modelo se queda cuando esa animación vuelve sin cambios, y la página lo dice. Probado: el modelo entero de un M4 Sherman nuevo cambiado en Blender, luego en el juego; en el Studio, los soldados de una copia del pelotón G.I., el Pelotón a caballo genérico con **Sus huesos** desmarcado, y la pintura del M4 Sherman del propio juego. Que las animaciones vuelvan sin cambios se comprobó con Blender en nuestro PC, todavía no en el juego.
- **Más o menos soldados (Studio):** **Añadir un soldado** trae la copia de un soldado del pelotón, un soldado de otro pelotón o un archivo de modelo; **Quitar** saca a uno; **+1 soldado** y **−1 soldado** añaden o quitan un fusilero al momento, sin Blender. Un pelotón tiene de 2 a 8 soldados, y un soldado puede tener un aspecto propio que ningún otro lleva. El juego los recibe con un pequeño parche del juego: se descarga una vez y se aplica solo a tu copia con mods, nunca al juego de tu carpeta de Steam; todos los demás pelotones quedan como los tiene el juego. Probado en el juego con pelotones de 3 y de 7 soldados hechos con estos botones, y con un solo fusilero pintado de rojo; un soldado de otro pelotón o de un archivo de modelo, y pelotones de 2 o de 8, todavía no.
- **Animaciones para una sola unidad (Studio):** la página de una unidad ahora tiene **Aspecto y movimientos**: su modelo, sus soldados, sus sonidos y animaciones y el vehículo en que viaja, fila a fila. **Cambiar en RUSE Decoy**, en la fila **Sonidos y animación**, abre RUSE Decoy sobre esa unidad, y un cambio en una de sus animaciones puede ser para **Solo esta unidad**, que entonces usa su propia copia, o para todas las unidades que la usan. **Volver a la de todas las unidades** quita la copia propia de la unidad. La **Captura de movimiento** se pone en una sola unidad del mismo modo. Probado en el juego con un pelotón que bailaba en el sitio mientras todos los demás pelotones seguían de pie como antes; una velocidad, una sustituta o un hueso cambiados para una sola unidad, todavía no.
- **Copias de una animación para las unidades que elijas (Studio):** en RUSE Decoy, **Copiar esta animación…** hace una copia de una animación en tu mod, listada en **Tus copias**. Cambia la copia y luego marca en **Quién la usa** las unidades que la usan en lugar de la animación, o, dentro de una unidad, solo algunos de sus soldados o partes; todas las demás unidades usan la animación como antes. **Volver a la animación del juego** quita tus cambios de la copia, y **Borrar la copia** la quita de tu mod. Probado en el juego con dos copias de las animaciones de los soldados de pie con un baile dentro, marcadas para un pelotón nuevo y solo para el soldado con bazuca del pelotón G.I.
- **Animaciones cambiadas en Blender (Studio):** para una unidad nueva hecha en tu mod, **Cambiar sus animaciones en Blender**, en RUSE Decoy, abre Blender con la unidad y cada animación que usa, cada una con el nombre de lo que hace en ella. Cambia una, haz clic en **Enviar a R.U.S.E. Studio** y luego en **Traer mis cambios**: las cambiadas pasan a ser propias de esa unidad, y todas las demás unidades conservan las del juego. Un envío que nunca trajiste se guarda aparte, y **Traer el envío guardado aparte** lo recoge. Probado en el juego con un pelotón que está de pie y corre con un brazo en alto, y un Pelotón a caballo genérico cuyos caballos llevan la cabeza alta.
- **Modelos con huesos y animaciones propios (Studio):** **Importar modelo…** ahora también acepta un .glb sobre huesos propios con sus animaciones: un caballo con su jinete, o cualquier criatura. **Sus animaciones** muestra qué animación usa la unidad para cada cosa que hace; elige otra, o déjala en **La más cercana**. **En los trayectos largos** un pelotón puede ir por sí mismo, usando una de ellas, en lugar de en su camión. **Sus dos mitades** elige el hueso donde el modelo se divide en las mitades superior e inferior que el juego anima a la vez (un jinete apunta mientras su caballo corre), y **¿Funcionará en el juego?** dice qué del modelo podría detener el juego o verse mal. En un pelotón, los fusileros y el soldado con arma pesada reciben cada uno su propio modelo, en su propia línea. Probado en el juego con un Pelotón a caballo genérico hecho así: fusileros y un soldado con bazuca a caballo, que disparan, van por sí mismos en los trayectos largos, y cada caballo cae con su jinete; otra animación elegida a mano u otra división, todavía no.
- **El Pelotón a caballo genérico (Studio):** fusileros y un soldado con arma pesada, cada uno en su propio caballo, ahora en la pestaña **Unidades** con las unidades de otras épocas (**IIGM+**, EE. UU.), fuera hasta que lo añadas. **Añadir a mi mod** crea sus caballos y jinetes en tu PC a partir de tu propia copia del juego (no se descarga nada), lo añade como unidad nueva de tu mod y pone a sneadtristen6 en los créditos de tu mod; **Quitarla de mi mod** lo quita todo de nuevo. Hay un solo Pelotón a caballo genérico para todas las naciones: sus jinetes siempre se hacen a partir del pelotón G.I., y en tu mod es una unidad como cualquier otra, en el menú de construcción que elijas al añadirlo (la pestaña **Naciones** lo pasa a otra nación). Probado en el juego añadido desde la pestaña **Unidades**. Todavía no probado en el juego: en un mod que alguien comparte contigo, su Pelotón a caballo genérico ahora se puede redimensionar y mover en tu PC una vez que tu Studio ha hecho los mismos archivos del caballo (añadirlo a cualquiera de tus mods los hace); y cuando el Studio vuelve a hacer esos archivos y salen distintos, van junto a los viejos, así que el Pelotón a caballo genérico de un mod nunca cambia cuando lo redimensionas o lo mueves (si sus propios archivos ya no están o cambiaron, **Cambiar tamaño** y **Moverlo** lo dicen y lo dejan como está).
- **Una carpeta demasiado profunda para Windows (Studio):** cuando **Añadir a mi mod** del Pelotón a caballo genérico se rechaza porque las carpetas del Studio son demasiado profundas para Windows, su página ofrece ahora una carpeta corta, como C:\RUSE2: **Copiar todo en C:\RUSE2 y volver a abrir** copia allí los ajustes del Studio, la biblioteca y los conjuntos del Launcher, y tus mods, mapas, archivos exportados y copias de seguridad, comprueba cada archivo, hace que las dos aplicaciones usen esa carpeta desde entonces y vuelve a abrir el Studio desde ella; **Elegir otra carpeta…** elige otra en su lugar. No se borra nada: tus carpetas antiguas se quedan donde están. Comprobado con pruebas; todavía no probado en un Studio real.
- **Su propio brillo después de Blender (Studio):** un modelo enviado a Blender con **Abrir en Blender** y traído con **Traer mis cambios** conserva su propia capa de brillo y color de bando; antes volvía con la capa simple que recibe un modelo de un archivo. Cuando no se puede conservar, la página dice de qué partes. Todavía no probado en el juego.
- **Dónde se guarda tu modelo (Studio):** la fila **Modelo** (en la página de un pelotón, **Más opciones**) dice dónde guarda tu mod el modelo propio de la unidad en tu PC, con **Mostrar en la carpeta**.
- **La pestaña Naciones (Studio):** **Empezar un mod nuevo** ahora solo pide un nombre y abre el Studio con el mod nuevo; los pasos guiados están apagados por ahora. Lo que solo ellos tenían está en la pestaña **Naciones**: **Conservar sus unidades** o **Empezarla vacía** para cada nación, y **Sin investigación** o **Conservar la investigación del juego** para todo el mod.
- **Eliminar llega hasta el final (Studio):** **Eliminar esta unidad**, **Quitarla de mi mod** y las retiradas de la pestaña **Naciones** ya no se detienen cuando otro programa tiene abierto uno de los archivos de la unidad: la unidad se va igualmente, y un archivo aún retenido se queda por ahora en la carpeta del mod. **Probar en el juego** y **Exportar mod…** lo dejan fuera, y el Studio lo quita solo más tarde, en cuanto ese programa lo suelta. Un archivo de lista del mod que otro programa retiene más de 3 segundos sigue deteniendo la eliminación, con todo puesto de nuevo en su sitio y el archivo nombrado. Comprobado con pruebas; todavía no probado en el juego.
- **Una unidad sin imagen de carta (Studio y Launcher):** una unidad mostrada en un menú de construcción sin imagen de carta ahora se rechaza al construir el juego, con lo que hay que cambiar. En una prueba el juego se detenía nada más arrancar con una unidad así (una copia del camión del cuartel general mostrada en un menú de construcción).
- **Exportar deja fuera las carpetas de tu PC (Studio):** un mod exportado ya no lleva las carpetas de tu PC que el Studio escribía en las fichas de sus modelos (a menudo con tu nombre de usuario de Windows): solo va el nombre del archivo. En tus propios archivos README, cada ruta de carpeta se corta a su propio nombre, y una ruta que termina en la carpeta propia de un usuario, y por eso nombra a ese usuario, se quita entera; Exportar enumera cada corte, y el README de tu mod queda tal como lo escribiste. Un README que Exportar no puede leer va tal como lo escribiste, y Exportar lo nombra. Tus otros textos (descripciones, créditos) van tal como los escribiste, y Exportar te avisa si alguno nombra tu carpeta personal. Los créditos de las unidades de otras épocas, también el del Pelotón a caballo genérico, ahora van con el mod.
- **Cosas más pequeñas (Studio):** cada fábrica se llama como su edificio; en persa, los nombres del juego se muestran en inglés, nunca como nombres internos; la comprobación antes de **Probar en el juego** también lee el mapa que estás editando cuando está en una carpeta propia, y también ofrece allí sus arreglos.
- **Nuevo mod… y Exportar con nombres y textos poco comunes (Studio):** **Nuevo mod…** ahora crea un mod cuyo nombre lleva un emoji o un carácter raro como 𠮷, o es muy largo; antes fallaba, y un emoji dejaba un mod roto en el menú de mods. En el nombre de la carpeta del mod y en el de su archivo exportado, una letra con acento solo pierde el acento (Équipe da equipe, antes quipe; ß, ł y ø todavía se quedan fuera), y un nombre largo les da como mucho 40 letras; el nombre en sí sigue entero. **Exportar mod…** saca una versión escrita con cifras de ancho completo o persas (１.０.０, ۱.۰.۰) en cifras normales (1.0.0), y un carácter pegado en el autor o la descripción ya no lo detiene. Cuando otro programa tiene abierto uno de los archivos del mod, Exportar nombra ese archivo (antes solo decía que se había denegado el acceso), y una exportación iniciada mientras otra está en marcha se rechaza con palabras (antes las dos escribían un solo archivo y dejaban uno a medio escribir). Comprobado con pruebas; todavía no probado en el Studio instalado.
- **Nombres y números (Studio):** **Nueva unidad…** rechaza un nombre que solo se diferencia del de otra unidad en las mayúsculas (tiger ii junto a Tiger II), como un nombre ya usado: Windows no distingue mayúsculas en los nombres de archivo, así que las dos compartían sus archivos, y eliminar una se llevaba la carta y el modelo de la otra. Un mod que ya tiene un par así lo conserva. Un número decimal demasiado grande para el juego (1e39, por ejemplo) se rechaza en la pestaña **Unidades** y en la pestaña **Ajustes de la IA y de los jugadores**, como en la pestaña **Todos los valores**, en lugar de detener cada construcción del mod. Un emoji o un carácter raro en los créditos del aspecto propio de un edificio ya no deja ese aspecto ilegible, ni en su página ni para la construcción. Comprobado con pruebas.
- **Pelotones y Blender (Studio):** **Uniforme personalizado** se rechaza, con palabras, mientras un soldado del pelotón lleva un modelo propio, porque el mod ya no se construiría: primero haz clic en **Volver al aspecto del juego** en ese soldado. La página del pelotón dice dónde se apartó un envío desde Blender que nunca trajiste, o el aspecto propio de un soldado quitado. **¿Funcionará en el juego?** lee las animaciones propias de un modelo tal como la construcción las reproduce, así que no dice que un pelotón al que se dio un modelo con animaciones propias, como los fusileros del Pelotón a caballo genérico, detendría el juego por animaciones que la construcción nunca reproduce. Una pintura nueva traída de Blender se queda cuando un viaje posterior deja **Su pintura** sin marcar. Comprobado con pruebas, la pintura también con Blender en nuestro PC; todavía no probado en el juego.
- **Archivos de un mod que no están guardados en UTF-8 (Studio y Launcher):** un archivo de un mod guardado por Excel como CSV simple o por el Bloc de notas como Unicode ahora se nombra, con su línea y cómo volver a guardarlo en UTF-8, en la construcción, en la comprobación antes de **Probar en el juego** (que ofrece **Apartar** para él) y en el Launcher al añadir el mod; antes salía un error en palabras de programador, sin nombrar ningún archivo. Un archivo que el Bloc de notas guardó como «UTF-8 con BOM» se lee. Cuando **Apartar** de la comprobación, o su cambio de nombre, se encuentra con un archivo que otro programa tiene abierto, nombra ese archivo, no el nombre que habría recibido. Comprobado con pruebas.
- **Mapas (Studio):** **Tamaño del mapa** ya no detiene la construcción cuando se agranda un mapa **Terreno en blanco** u **Océano en blanco** hecho de uno de 16 de los 32 mapas del juego (entre ellos Frontline, Tank Graveyard y Vesuvio); todo lo que se coloque en su terreno nuevo sigue deteniendo la construcción (un Frontline agrandado con un árbol allí lo hizo), y eso aún está por arreglar. Un mapa nuevo, unos cambios de mapa nuevos o la copia que hace **Editar un mod instalado**, llamados Nul u otro nombre que Windows se guarda para sí, reciben una carpeta que Windows puede crear, con el nombre tal como se escribió. Cuando **Duplicar mapa** se rechaza por un carácter que el archivo del mapa no puede guardar, no queda nada detrás; antes quedaba un mapa a medio hacer, y cada **Probar en el juego** posterior se detenía. **Crear sectores** con sectores demasiado pequeños para el mapa se rechaza y no se guarda nada; antes el ajuste se guardaba igualmente, y la vista de sectores fallaba hasta **Deshacer**. Comprobado con pruebas; todavía no probado en el juego.
- **Palabras sencillas, en tu idioma (Studio y Launcher):** 279 mensajes más llegan ahora en los 11 idiomas, en palabras sencillas: los rechazos del Launcher y la línea de arriba de su ventana; cómo terminan **Probar en el juego**, **Jugar** y las instalaciones, y un Jugar rechazado antes de empezar; las líneas de los pasos de una construcción; por qué la búsqueda de actualizaciones, la lista de mods o la de unidades de otras épocas no se alcanzan sin internet, nunca con las palabras de Windows; un archivo de mod dañado; la copia de seguridad del juego en Ajustes y el inicio de sesión con Steam; los rechazos de RUSE Decoy, de las pestañas **Música** y **Naciones**, de la pintura del terreno de los mapas y de las misiones; el archivo de cambios de tu mod roto a mano; y un nombre ya usado, dicho con el nombre de la unidad en vez de un nombre interno, o un número que no cabe, dicho con su etiqueta en la página. Comprobado con pruebas.
- **¿Problemas? Lee la guía (Studio):** un enlace pequeño al final de la ayuda de 7 cuadros donde los huesos, las animaciones o Blender necesitan explicación (la carta del pelotón, el cuadro de Blender de una unidad que no es un pelotón, **Sus dos mitades**, **Sus animaciones**, **¿Funcionará en el juego?** y dos en RUSE Decoy) abre la página de la wiki sobre ese tema en tu idioma. La wiki tiene tres páginas nuevas en los 11 idiomas, Modelos y huesos, Animaciones de las unidades y Abrir en Blender, y cinco páginas corregidas donde ya no coincidían con las aplicaciones (Jugar con amigos explica ahora los códigos de partida). El enlace se vio en una vista previa de la página, todavía no en el Studio instalado.
- **Jugadores, actualizad el Launcher:** un mod cuyos pelotones tienen soldados propios, o cuyas unidades tienen animaciones propias, necesita el Launcher 0.4.8.20 o más nuevo: uno más antiguo no puede dárselos.
- **Bug Watch dice por qué, si lo marcaste:** qué comprobación rechazó una construcción o encontró un error (un nombre fijo de nuestro código), hasta dónde llegó un **Jugar** o un **Probar en el juego**, qué mods de nuestra lista estaban activos y cuántos tuyos, los Jugar rechazados antes de empezar, y las actualizaciones ofrecidas, instaladas o fallidas. Nunca las palabras mostradas, una ruta ni los nombres, las palabras o los archivos de tus mods. El informe de fallo de un juego detenido por un error de script también dice cuántas veces las protecciones de arriba mantuvieron ese juego en marcha (todavía no probado en el juego).
- **Un fallo del juego que conocemos nombra su unidad (Launcher, si marcaste Bug Watch):** cuando el juego se cierra inesperadamente de una de las formas que conocemos, el Launcher lo dice después de **Jugar**, en tu idioma: la unidad que el juego estaba creando, por el nombre de su carta (y si la añadió un mod), y por qué, en palabras sencillas. Lo lee en tu PC, del propio informe de fallo del juego y de tu copia con mods; el nombre y el motivo nunca se envían. La unidad solo se dice cuando hayas aceptado la versión 4 del acuerdo (abajo). **Probar en el juego**, en el Studio, no lo dice. Comprobado con informes de fallo anteriores; todavía no probado en el juego.
- **El acuerdo, versión 4:** ahora enumera más de lo que envía Bug Watch, si lo marcaste: cuántos mods propios tenías y qué tipos de cosas contienen, como unidades, mapas, misiones o scripts (contados por tipo, nunca nombrados, y nunca sus palabras, rutas ni archivos); en un fallo del juego, el mapa en que estaba (un mapa del juego por su nombre, un mapa hecho por un mod solo como "un mapa de mod") y la unidad que el juego estaba creando (una unidad del juego por su número, una unidad añadida por un mod solo como "una unidad de mod"), cada uno solo cuando el informe de fallo del juego lo muestra; y qué versión del acuerdo aceptaste. Ahora también dice que los nombres y las palabras de tus propios mods nunca se envían. Nada más ha cambiado. Como ha cambiado, ambas aplicaciones te lo muestran una vez más al abrirse; tu nombre de usuario se queda, y la casilla de Bug Watch sigue como la tenías.
- **Sin cambios:** RUSE Guard, un juego sin mods, la campaña y las escaramuzas.

**0.9.8.19:** RUSE Guard: un juego construido con un mod de trucos ahora juega partidas multijugador y cooperativas con los jugadores que tienen la misma construcción. Aún no tiene soporte completo y puede tener fallos: úsalo en multijugador bajo tu propia responsabilidad.

- **Informado por un jugador:** dos amigos con el mismo paquete de mods eran expulsados de todas las partidas multijugador, porque un mod del paquete (Infinite Supply Depot) está marcado como truco. RUSE Guard trataba todo juego construido con un truco o una herramienta de prueba como solo sin conexión: abandonaba cada partida multijugador y cooperativa a los pocos segundos, sin mirar nunca quién más jugaba.
- **Qué hemos cambiado:** un segundo después de empezar una partida multijugador o cooperativa, un juego así ahora dice a los juegos de los demás jugadores qué construcción es: un código corto hecho con la versión del juego y los mods, nada sobre ti. Hacia los siete segundos decide. Si todos los jugadores tienen la misma construcción (la misma versión del juego, los mismos mods en el mismo orden, las mismas versiones de los mods), lo dice en pantalla y la partida sigue. Si alguien tiene otra construcción o ningún mod, abandona la partida como antes.
- **Un código de partida para estos conjuntos:** en el Launcher, un conjunto de mods con un mod de trucos ahora recibe un código de partida como cualquier otro. El mismo código significa la misma construcción: comparad los códigos antes de jugar.
- **Todos los jugadores necesitan esta versión:** el juego de cada jugador de la partida debe estar construido con el Launcher 0.4.8.19 o el Studio 0.9.8.19, o más nuevos. Tras actualizar, el siguiente **Jugar** o **Probar en el juego** lo vuelve a construir solo.
- **Aún sin soporte completo:** lo probamos en el juego con un solo jugador que alojaba una partida multijugador contra el ordenador, y fuera del juego con 20 partidas simuladas de hasta cuatro jugadores. Nadie lo ha jugado todavía entre dos personas en una partida real, así que puede tener fallos: úsalo en multijugador bajo tu propia responsabilidad. Pruébalo y cuéntanos qué pasó en Discord o GitHub: qué mensaje de RUSE Guard viste y si la partida siguió.
- **Sin cambios:** un juego construido sin trucos, la escaramuza contra el ordenador y la campaña.

**0.9.8.18:** Un arreglo interno: la comprobación de una copia con mods enumera lo que encuentra en el mismo orden en todos los sistemas.

- **Por dentro:** la comprobación de una copia con mods (qué archivos del juego cambiaron después de construirla) ahora enumera lo que encuentra en el mismo orden en Windows y en Linux. Lo que encuentra no cambia.

**0.9.8.17:** Los modelos importados se colocan donde está la unidad, con sus torretas y hélices en su propio sitio; una munición puede tener su propia clase de arma.

- **Una actualización obligatoria:** las versiones anteriores ya no se pueden usar. Al abrirse, la aplicación la instala sola, y **Probar en el juego** espera hasta que esté instalada.
- **Los modelos importados se colocan donde está la unidad** (informe de un modder: los modelos se dibujaban por delante de su anillo de selección): **Importar modelo…** ahora pone un modelo nuevo en el centro de la unidad que copia y le da su propio esqueleto, así que su torreta gira donde está la torreta de tu modelo. Cada importación nueva se ajusta así. Un modelo importado antes conserva su sitio anterior hasta que lo importes de nuevo o lo muevas (abajo), y las unidades de otras épocas conservan el suyo. Probado en el juego con el Sherman del propio juego, abierto en Blender y traído de vuelta, sobre otras unidades; aún no con un modelo de otra parte, otro tanque con torreta o una torreta que gira por completo.
- **Moverlo:** si un modelo aún no queda bien colocado, abre **Moverlo** bajo su tamaño en la página de la unidad (plegado hasta que lo necesites; sigue abierto en un modelo que hayas movido). **Adelante**, **Derecha** y **Arriba** lo mueven desde donde está ajustado, en unidades del juego (la página dice cuánto mide la unidad copiada en ellas); un menos va al otro lado, y 0, 0, 0 lo devuelve a su sitio. Su torreta y sus hélices van con él, así que siguen girando en el lugar correcto, y un tamaño nuevo conserva el movimiento. En la vista 3D, un anillo azul muestra dónde está la unidad, con su marca al frente. Un modelo ligado a los huesos de la unidad se queda donde están sus huesos: ese muévelo en Blender. Desde la línea de comandos: `ruse import-model ... --move F R U`. Probado en el juego con tanques movidos hacia delante, atrás, a la derecha y arriba.
- **Los aviones conservan sus propias hélices:** un avión abierto en Blender desde el Studio y traído de vuelta con **Importar modelo…** conserva sus hélices donde las tiene tu modelo, tantas como tenga, sea cual sea el avión que copia: palas en tierra, discos que giran en el aire. En la vista 3D los discos de un avión se ven ahora transparentes, como el juego dibuja una hélice que gira. Probado en el juego: el modelo de un bombardero trimotor sobre una copia de un caza monomotor, y al revés. Un modelo de avión de otra parte conserva sus hélices tal como las dibuja, quietas: el importador aún no sabe cuáles de sus piezas son hélices.
- **Cualquier unidad puede llevar un modelo:** los soldados, la dotación de un cañón y los aviones a los que el Studio no podía ajustar un modelo hasta ahora (el P-47, por ejemplo) también llevan uno propio, ligado a los propios huesos de la unidad (por ejemplo un modelo del juego abierto en Blender desde el Studio y cambiado allí). Conserva esos huesos y se usa tal cual, y los demás hombres de una escuadra con los mismos huesos lo llevan también. Probado en el juego: una escuadra de fusileros, la dotación de un cañón y el P-47; aún no un modelo de otra parte.
- **Juégalos con el Launcher de esta actualización:** un mod con un modelo importado por esta versión necesita el Launcher de esta actualización o uno más nuevo, para ti y para tus jugadores: un Launcher más antiguo da al modelo el esqueleto de la unidad copiada, así que su torreta gira alrededor del punto equivocado. Los mods con modelos importados antes se juegan como antes.
- **Nueva clase de arma** (en la página de una munición): el cuadro **Clase de arma** fija qué parte de su daño hace una munición a cada tipo de objetivo. **Nueva clase de arma…** abre un número para cada uno: edificios y fortificaciones, aviones, paracaidistas en descenso, infantería, vehículos ligeros, blindaje 1 a 5 y camiones de construcción. 1 es daño completo, 2 el doble, 0,5 la mitad, y 0 significa que no puede atacar ese objetivo. **Guardar clase** da a la munición su propia copia de la tabla de daños del juego, así que el daño de ninguna otra munición cambia; como cualquier cambio en una munición, vale para todas las unidades que la disparan (para una sola unidad, copia antes la munición). **Volver a la clase del juego** quita la copia, y borrar una munición copiada se lleva su clase con ella. Probado en el juego: escuadras de fusileros cuya munición tenía números contra tanques dispararon a los tanques con sus fusiles y los dañaron. Visto en una vista previa; aún no pulsado en la ventana de la aplicación.

**0.9.8.16:** Solucionar problemas conserva las copias del juego que hiciste tú.

- **Corregido: «Borrarlas» en Solucionar problemas eliminaba copias hechas por ti:** la misma corrección que la del Launcher (un solo código para las dos apps). Una copia del juego construida a mano en la carpeta de copias, una copia de prueba o una copia de referencia contaba como sobrante y se eliminaba para siempre. Cada copia así lleva ahora una pequeña nota «conservar», y una copia que la tiene nunca es un sobrante: solo se borran los sobrantes de las propias apps (copias a medio construir, las que versiones antiguas hacían por cada conjunto de mods). Una copia construida antes de esta versión aún no tiene nota: reconstrúyela una vez con esta versión, o no toques «Borrarlas» hasta entonces.

**0.9.8.15:** Original también tiene el título R.U.S.E. 2.0 dorado.

- **Nada cambia en el propio Studio:** esta actualización es del Launcher (Original también tiene el título R.U.S.E. 2.0 dorado). La casilla del título dorado en los Ajustes del Studio es el mismo ajuste que la del Launcher, así que desmarcarla aquí también hace que Original se inicie a través de Steam.

**0.9.8.14:** Los mods con un script de partida propio vuelven a construirse.

- **Corregido: Probar en el juego se detenía con algunos mods** con «RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...»: algunos mods traen su propio script de partida, cuya cabecera pide más espacio del que el script necesita (entre ellos 1 VS 7 AI, 1 VS 15 AI, Operation Overlord y Sand Box). El juego ejecuta esos scripts sin problema, pero el Studio los rechazaba, así que no se podía construir nada con uno de esos mods. Ahora los lee como el juego.

**0.9.8.13:** Los informes de fallos del juego dicen qué llevó al fallo.

- **Los informes de fallos del juego de Bug Watch dicen más:** si marcaste Bug Watch y el juego falla, el informe ahora también dice qué intentaba leer o escribir el juego, y hasta 16 puntos del juego que llevaron al fallo, leídos del propio informe de fallo del juego en tu PC, que sigue sin salir nunca de él. Un informe que solo decía dónde se detuvo el juego no podía mostrar por qué; ahora podemos rastrear fallos como el que un jugador nos envió esta semana, y corregirlos.
- **El acuerdo, versión 3:** ahora enumera estas dos novedades entre lo que contiene un informe de fallo del juego, y nada más ha cambiado. Como ha cambiado, ambas aplicaciones te lo muestran una vez más al abrirse.

**0.9.8.12:** Probar en el juego vuelve a construir los juegos con mods.

- **Corregido: Probar en el juego se detenía con cada mod** con «No such file or directory: ...fairplay_watch.bin»: a los instaladores de 0.9.8.10 y 0.9.8.11 les faltaban tres archivos de RUSE Guard, así que no se podía construir ningún juego con mods. Ya están de vuelta, y una aplicación a la que le falte alguno de sus archivos ya no se puede publicar.

**0.9.8.11:** el inicio de sesión con Steam termina en las aplicaciones; en Linux, los programas auxiliares de una construcción arrancan como en Windows.

- **Arreglado: inicio de sesión con Steam.** Después de iniciar sesión en la página de Steam, el Launcher y el Studio seguían esperando y nunca preguntaban a nuestro servidor si habías terminado: la ventana detenía sus propias comprobaciones antes de la primera. Ahora comprueba cada pocos segundos y te conecta en cuanto Steam lo confirma. Probado en la vista previa: la comprobación se hace y la ventana te muestra conectado.
- **Los programas auxiliares arrancan de cero en todos los sistemas:** los programas entre los que una construcción reparte su trabajo (modelos importados, reparación del mapa, movimiento, agua, terreno de la vista del mapa) ahora arrancan de cero también en Linux, como siempre lo han hecho en Windows. En Linux arrancaban como copias de la aplicación en marcha, lo que a veces podía colgar una construcción, e hizo fallar allí una de nuestras comprobaciones. No cambia nada en Windows ni con Proton en Steam Deck.

**0.9.8.10:** mods de más de 4 GB, listas de construcción en grupos, construcciones más rápidas de mods grandes, tus archivos en Documents\RUSE 2.0, el persa y cada página en 11 idiomas, arreglos de informes de probadores; y RUSE Guard, nuestro anti-trampas para las partidas multijugador reales; Bug Watch, informes de fallos y uso que puedes activar; el inicio de sesión con Steam; y un acuerdo al primer inicio.

- **Arreglado, informado por un jugador: mods de más de 4 GB.** Un juego con mods cuyos paquetes pasaban de 4 GB dejaba de construirse («'I' format requires 0 <= number <= 4294967295»). Ahora los paquetes llevan su longitud completa, y uno de más de 4 GB se escribe en una disposición más amplia que el juego puede leer gracias a un pequeño parche del juego: se descarga una vez y se aplica solo a tu copia con mods, nunca al juego de tu carpeta de Steam. Por encima de 32 GB, o para un solo archivo de más de 4 GB, la construcción lo dice claramente. Probado en el juego: copias de más de 4 GB, y con 200, 283 y las 366 unidades de otras épocas.
- **Muchos modelos propios:** el juego encuentra las texturas sustitutas de un paquete mediante un índice, y una construcción que añadía algunas para modelos importados lo escribía mal: con muchas unidades de otras épocas, el juego se colgaba o fallaba al cargar. Ahora se escribe como el juego lo lee, para cada mod que las añade. Probado en el juego con las 366 unidades de otras épocas.
- **Listas de construcción en grupos:** con muchas unidades, la lista de construcción de un edificio se salía de la pantalla y no se podía llegar a las unidades de abajo. Ahora cada lista muestra una fila por grupo, las líneas del propio juego (una unidad nueva entra en el grupo de su tipo): como mucho 6 unidades por grupo y 10 grupos por edificio, para que toda la lista quepa en la pantalla. El Studio dice por qué cuando un grupo está lleno y muestra los grupos donde añades unidades; un mod hecho antes que pasa de estos límites se construye igualmente, con un aviso. Probado en el juego con 297 unidades de otras épocas en grupos.
- **Construcciones más rápidas:** los modelos que importas se guardan entre construcciones, y los nuevos se hacen en paralelo en los núcleos de tu PC. Un mod con 366 unidades de otras épocas tardaba unos 18 minutos en construirse en un PC de 8 núcleos; ahora unos 5 la primera vez y unos 3 después, con los mismos archivos del juego, byte a byte.
- **Modelos importados (informes de probadores):** una pieza de torreta en un hueso que el aspecto copiado no tiene en su lista (un M109 copiado del M7 Priest) detenía la importación; ahora va en la lista propia de la copia. Una pieza de torreta en un modelo sin torreta (el P-40, la M274 Mule) va con el casco, un cañón remolcado visto de lejos muestra su propio modelo, y una textura en tira delgada recibe su textura sustituta. Los cañones remolcados probados en el juego; las piezas de torreta aún no miradas de cerca.
- **Puentes (informe de un probador):** una sola pestaña Puentes: un puente nuevo, tus puentes (cada uno con Ir y Eliminar) y los puentes propios del mapa con sus cruces, quitados o devueltos con un solo botón. Un puente nuevo cuenta cuando quitar los antiguos corta el mapa en dos, y dar forma al terreno mantiene los extremos de los puentes del mapa a su altura. Quitar es más fácil de encontrar (Pintar y quitar, o la tecla X). Un mod de unidades y los cambios de un mapa hechos con el mismo nombre se construyen juntos, y la vista del mapa vuelve a mostrar los modelos del juego. Aún no probado en el juego.
- **Tus archivos en Documents\RUSE 2.0:** tus mods, mapas, exportaciones y copias de seguridad van a Documents\RUSE 2.0, donde el Explorador de archivos los muestra; lo que el Studio guardaba en su carpeta antigua se mueve allí una vez, y lo dice. Eliminar un mod… lo envía a la Papelera de reciclaje, Mostrar la carpeta de este mod la abre, y los Ajustes muestran dónde está todo. Visto en una vista previa; aún no probado en las ventanas de las aplicaciones.
- **Persa y 11 idiomas:** el persa es el 11.º idioma de las aplicaciones, escrito de derecha a izquierda; el README, la wiki, estas notas y las pantallas de instalación están en los 11.
- **Actualizaciones obligatorias:** una actualización que marcamos como obligatoria se instala sola, con una ventana que nadie puede cerrar (las aplicaciones desde esta versión saben leer la marca). La ventana Novedades mantiene su altura mientras te desplazas por ella.
- **Solo copias propias:** antes de que Jugar o Probar en el juego construya una copia con mods, las aplicaciones comprueban que la carpeta del juego es una copia tuya, por lo que Steam dejó allí, en Windows, con Proton en Steam Deck y en Linux. Si la tuya no se puede confirmar (una copia en caja de antes de que R.U.S.E. estuviera en Steam), una ventana te deja abrir una solicitud, y te enviamos un código de desbloqueo para ese PC.
- **Discord:** las aplicaciones y las páginas usan una invitación nueva que no caduca.
- **Un acuerdo al primer inicio:** la primera vez que el Studio o el Launcher se abre, explica qué hace RUSE Guard y te pide aceptarlo (hace falta para jugar en línea con las aplicaciones), si quieres activar Bug Watch (opcional), y un nombre de usuario que nuestros desarrolladores ven con tus informes: se le añaden un # y cuatro números para que sea único, como Nick#4821. Un solo nombre sirve para ambas aplicaciones. El acuerdo vuelve a mostrarse cuando cambia. Visto en ambas aplicaciones. En los 11 idiomas.
- **RUSE Guard:** nuestro anti-trampas, según el diseño de DomesticNukes. Solo funciona en partidas multijugador y cooperativas, nunca en un jugador, en escaramuza contra el ordenador, en la campaña ni mientras haces mods. Una copia con mods construida con un truco o una herramienta de prueba es solo para jugar sin conexión: abandona por sí misma las partidas multijugador y cooperativas. Durante una partida real compara los nombres de tus programas en ejecución con una lista de herramientas de trampas conocidas (solo los nombres; no lee nada más), y lo que recoge de una partida se archiva con tu nombre de usuario, nunca con tu cuenta de Steam. Probar en el juego construye sus copias con él. Probado en partidas multijugador contra un rival real; las pruebas llegan a nuestro servidor.
- **Bug Watch (opcional):** cuando lo marcas, el Studio y el Launcher cuentan qué usas y cuándo algo falla, los fallos de las aplicaciones y los del juego, con los mods que estaban activos, y lo envían una vez al día a nuestros desarrolladores con tu nombre de usuario. Sin nombres reales, sin cuenta de Steam, sin archivos. Desactivado salvo que lo marques; desmárcalo cuando quieras y lo guardado se borra. Visto en ambas aplicaciones.
- **Iniciar sesión con Steam:** un inicio de sesión en la propia página de Steam en tu navegador confirma que posees R.U.S.E., para el juego en línea, RUSE Guard y las descargas de contenido. Nunca vemos tu contraseña, y tu ID de Steam nunca se guarda: solo un pase guardado en tu PC durante 30 días. El Studio lo pide una vez; los Ajustes del Launcher lo abren cuando quieras. Nada lo necesita todavía. Aún no probado en las aplicaciones.

**0.9.8.9:** descargas en más PC, y una lectura de imágenes más segura.

- **Corregido, avisado por un jugador:** en un PC cuyo Windows no tiene el certificado con el que se comprueban las descargas de GitHub y no puede obtenerlo, las descargas fallaban («unable to get issuer certificate»). Las descargas del Studio (sus actualizaciones, los parches del juego, los modelos de las unidades de época y las texturas en línea de Map Paint) ahora también lo intentan con la lista de certificados de Firefox, que el Studio lleva consigo.
- **Imágenes más seguras:** la biblioteca con la que el Studio lee las imágenes (Pillow) pasa a la versión 13.0.0, con sus correcciones contra archivos de imagen hechos a propósito que podían cerrar la aplicación, agotar su memoria o algo peor.
- **Código más estricto:** los 12 avisos de la revisión de código de GitHub sobre este proyecto están resueltos. Cuando el Studio muestra sus páginas en tu navegador, solo abren sus propios archivos, comprobados de una forma que esa revisión reconoce; las descargas piden TLS 1.2 o más reciente, como ya hacían; y la lectura de los errores de carreteras de una prueba fallida sigue siendo rápida con cualquier mensaje. Nada más cambia en cómo funciona el Studio.

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

**0.9.6:** una unidad nueva puede tener un modelo 3D propio, de cualquier herramienta 3D, y **Probar en el juego**
arranca al instante cuando nada ha cambiado. Y una primicia:

- **El primer modelo de otro programa 3D en R.U.S.E.:** un M1 Abrams, convertido en una unidad nueva de EE. UU. junto
  al Sherman. Se compra en la Armor Base con su propia tarjeta, se construye y gira la torreta como los tanques del
  juego. Visto en el juego.

| Antes | Ahora |
|---|---|
| Una unidad nueva tenía el modelo de la unidad que copia. | **Importar modelo…** en la página de una unidad nueva: elige un **.3ds** (con sus imágenes al lado, o en la carpeta de arriba) o un **.glb** (de Blender y la mayoría de las herramientas 3D). El Studio lo ajusta a la unidad que copia: su longitud (por **Tamaño**: 1 es igual de largo, un Abrams sobre un Sherman es 1,36), su torreta sobre la torreta de esa unidad para que el juego la gire igual, sus imágenes como texturas propias. La página lo muestra en 3D; **Usar el modelo de la unidad copiada** lo vuelve a quitar. Va a tu mod como `files/models/<the unit's name>.glb`, que se abre en Blender. **Visto en el juego.** Aún es pronto: las orugas y las ruedas todavía no giran, el fogonazo del cañón sale donde está la boca del arma de la unidad copiada, y los restos son los de la unidad copiada. |
| Una unidad nueva con su propia tarjeta cerraba el juego al construirse (0.9.5). | Su tarjeta está también donde el juego la lee en el mapa. **Visto en el juego.** |
| Un mapa hecho con **Duplicar mapa** no se podía eliminar en el Studio. | **Eliminar mapa**, bajo Duplicar mapa en un mapa nuevo: pregunta una vez y luego su carpeta va a la Papelera de reciclaje, de donde puedes recuperarla. Los mapas propios del juego no se pueden eliminar. |
| El Studio decía que Blender no estaba instalado si estaba descomprimido en lugar de instalado. | Encuentra Blender dondequiera que lo descomprimieras (la carpeta superior de una unidad o una por debajo, Descargas, Escritorio, Documentos). |
| Los repintados salían con algunos colores un poco desviados (una zona roja y azul podía volverse morada). | Cada bloque de 4 x 4 conserva sus propios colores. Las unidades repintadas y el suelo pintado salen con datos de imagen ligeramente distintos a los de 0.9.5 (el mismo aspecto), así que cambian la huella digital y el código para unirse de un mod así: todos los jugadores deberían actualizar antes de jugar juntos. |
| **Probar en el juego** reconstruía toda la copia con mods cada vez, aunque nada hubiera cambiado. | Si nada cambió desde la última construcción, el juego arranca al instante, sin construir (un mod de prueba: de 21-29 s a menos de 0,1 s). Una construcción reutiliza los archivos sin cambios de la última copia en lugar de volver a copiarlos. |
| Cada construcción leía de nuevo los datos de las unidades del juego. | Se guardan entre construcciones: un mod de prueba grande tardaba 213 s cada vez; ahora la primera construcción tarda más o menos lo mismo, y las siguientes 68 s. El juego ya no copia todos sus datos antes de una construcción. |
| Borrar la mayor parte de un mapa grande agotaba la memoria del Studio, y un borrado de todo el mapa se rechazaba por demasiado grande. | Quitar cuenta en segundos, de uno en uno; **Borrar todo el mapa** en la bandeja Quitar (Deshacer lo revierte). El decorado borrado se escribe de forma compacta. Nuevo: aún no visto en el juego a gran escala. |
| El suelo aplanado bajo una carretera dejaba la carretera de la vista lejana a la altura antigua. | El modelo de la carretera sigue al suelo nuevo. Nuevo: aún no visto en el juego. |
| Un cauce aplanado conservaba de cerca sus imágenes de roca y de garganta. | Se rellena desde ambas orillas y se le quita la cobertura baja. Nuevo: aún no visto en el juego tal como lo hace la construcción. |
| Mientras se construía el índice del juego (alrededor de un minuto), el Studio solo podía esperar. | Mapas y Ajustes siguen utilizables; la línea de abajo dice cuándo está listo. |
| Un arranque lento no dejaba ninguna pista. | Se cronometran los pasos de cada arranque; **Copiar informe** en Solucionar problemas lista los cinco últimos. |
| La página de la ventana podía alcanzar más partes de la aplicación que sus propias llamadas. | Solo recibe las llamadas propias de la aplicación. |

También `ruse import-model <file> --like <model> --unit <name>` hace lo mismo desde la línea de comandos.

**0.9.5:** las unidades tienen un aspecto propio. Mira cualquier unidad en 3D, repíntala en Blender, dale tu propia
tarjeta en el menú de construcción. Y nuestras primicias, todas vistas en el juego:

- **La primera unidad repintada por un mod:** un Sherman rojo, de cerca y de lejos.
- **La primera unidad pintada en Blender** y traída de vuelta al juego.
- **La primera tarjeta del menú de construcción hecha en el Studio,** mostrada en el propio menú de la Armor Base del
  juego.
- **La primera unidad nueva con un modelo propio,** junto a las del juego: el Tall Sherman, al lado del Sherman (hecho
  en pruebas; hacer tus propios modelos en el Studio llega después).
- **La primera misión nuestra** jugada hasta la victoria: una Operación nueva con sus propios objetivos, unidades y un
  ataque de artillería (hecha en pruebas).

| Antes | Ahora |
|---|---|
| La página de una unidad solo mostraba sus valores. | **Modelo 3D** en la página de la unidad: gíralo, acércate, mira la pintura de tu mod sobre él. |
| El aspecto de una unidad era el del juego. | **Repintar en Blender:** **Abrir en Blender** abre los modelos de la unidad con sus imágenes; pinta sobre el modelo, y luego **Traer** guarda tu pintura y la pone en tu mod. **Visto en el juego**, de cerca y de lejos. Blender es gratis: si el Studio no lo encuentra, **Conseguir Blender (gratis)** y **Elegir Blender…** están ahí mismo. |
| La imagen de una unidad en el menú de construcción era la del juego. | **Usar esta vista como tarjeta:** gira y acerca el modelo 3D hasta que quede bien en el marco discontinuo; esa vista se convierte en la tarjeta de la unidad en el menú de construcción. **Visto en el juego.** |
| Una unidad nueva mostraba la misma tarjeta que la unidad que copia, así que las dos se veían iguales en el menú. | La tarjeta de una unidad nueva es suya (`files/cards/<the unit's name>.png`): hacer su tarjeta nunca cambia la del original. Aún no visto en el juego. |
| El juego descartaba un paquete de modelos de unidades que crecía, y faltaban todos sus modelos: un cierre en la primera fábrica. | Los paquetes de modelos se escriben como el juego los comprueba, sea cual sea su tamaño. **Visto en el juego:** un segundo Sherman con un modelo propio. |
| Las unidades de una nación dadas a otro ejército no tenían modelo en los capítulos de campaña y las Operaciones: un mod que hacía aparecer unidades francesas en Holanda se cerraba al cargar. | Sus modelos también se cargan allí. **Visto en el juego** (unidades francesas en Colditz). |
| **Duplicar mapa** solo hacía mapas de BATALLAS. | También hace una **Operación** o un **Capítulo de campaña** nuevos a partir de la entrada de cualquier mapa. **Visto en el juego:** una Operación nueva. Aún es pronto: todavía no se ha probado un capítulo de campaña nuevo. |
| Aplanar las montañas del borde de un mapa dejaba allí un acantilado. | El borde del mapa sigue al suelo. **Visto en el juego** (Blitz Twin, llano hasta el borde). |
| Las unidades rodeaban los sitios donde habían estado los edificios borrados de un pueblo. | El suelo se abre a todas las unidades donde se quitan edificios, como con los árboles. **Visto en el juego.** |
| No había forma de pintar el suelo del mapa. | **Map Paint:** pinta la imagen del suelo con un color (la rueda, los colores propios del mapa o el cuentagotas) o con el suelo propio del mapa copiado de otro sitio. **Despejar el suelo debajo** (activado por defecto) quita la hierba, los cultivos y las piedras bajo la pintura para que se vea a cualquier altura. Aún es pronto: visto en el juego desde lo alto. |

**0.9.4:** mapas nuevos, aún en fase temprana. **Duplicar mapa** hace un mapa nuevo a partir de cualquier mapa de
BATALLAS, y los mapas se abren en un segundo.

| Antes | Ahora |
|---|---|
| Los cambios de mapa solo podían cambiar los mapas propios del juego. | **Duplicar mapa** (pestaña Mapas, bajo el nombre del mapa abierto) hace un **mapa nuevo**: una copia completa con nombre propio, que aparece en BATALLAS junto al original y que luego cambias como cualquier mapa. La ventana dice lo que hace y cómo funciona. **Visto en el juego:** un mapa nuevo se juega con su propio suelo, y 101 mapas nuevos a la vez aparecieron todos en la lista y se jugaron. Aún es pronto: las copias de mapas que no son Blitz se construyen pero todavía no se han probado en el juego, y aplanar las montañas del borde de un mapa deja allí un acantilado. Cuéntanos lo que encuentres. |
| Un mapa tardaba segundos en abrirse cada vez (M03_Italie: 7,6 s). | Sus datos se guardan entre visitas y sesiones: 1,7 s la segunda vez. |
| «Mod» y «Mapa» eran dos menús parecidos. | **Mod de unidades** (con un tanque) y **Cambios de mapas** (con un mapa). |
| Era fácil confundir bandos y zonas. | **¿Para quién?** dice que un bando es quien controla las unidades (un país puede tener varios), y al pasar el ratón por una zona se dice que es un área del mapa, no un bando. |
| Las actualizaciones llegaban solo como versiones completas. | Pequeñas correcciones pueden llegar entre versiones (0.9.4.1), ofrecidas como cualquier actualización. |

**0.9.3:** todo lo que colocas se ve de lejos, las carreteras nuevas a través de bosques se parecen a las del mapa,
árboles que puedes conservar sobre una carretera, objetos y árboles por sus nombres en tu idioma, y construcciones
unas tres veces más rápidas.

| Antes | Ahora |
|---|---|
| Los objetos, árboles y edificios para colocar se listaban por nombres en clave franceses: Caillou_10, ChampsPierres_02, Osier... | Por nombres en el idioma del Studio, en los diez, con el tipo de cosa que es cada uno: "Stony field 2", "Champ de pierres 2", "Steiniges Feld 2". Cambian con el botón de idioma. El nombre en clave y su carpeta están en la descripción emergente. |
| Las rocas y la mayoría de los demás objetos que colocabas desaparecían en cuanto la cámara salía de la distancia corta, y aparecían y desaparecían al girarla. | Todo lo que coloca un mod se dibuja hasta la distancia lejana, sin cambiar los objetos propios del mapa. **Visto en el juego:** las rocas colocadas se ven a cualquier altura. |
| Desde lo alto, una carretera nueva a través de un bosque era una franja clara, y tras un primer arreglo desaparecía a media-larga distancia. | Pintada a través de los bosques como las carreteras propias del mapa, a cualquier altura. **Visto en el juego.** |
| Una carretera nueva siempre quitaba los árboles de su camino, unos 6 m a cada lado. | **Mantener los árboles en las carreteras nuevas** en la bandeja Carreteras: los árboles y arbustos se quedan sobre la carretera, y en un bosque la carretera se ve más tenue y más gris. **Visto en el juego.** |
| **Probar en el juego** tardaba unos 5 minutos en construir un mod con carreteras nuevas en M03_Italie. | Alrededor de 1½ minutos: el aspecto de las carreteras de un mapa se mide una vez y se guarda, y las copias se saltan una comprobación lenta que no necesitan. |

**0.9.2:** arreglos a partir del mapa de campaña de un probador: puentes para carreteras nuevas en todos los mapas,
extremos de carretera que se ajustan a los puentes (o a nada), los nombres que conoce un jugador, unidades para el
jugador, decorado que se ve de lejos, y las zonas del escenario como fronteras sobre el suelo.

| Antes | Ahora |
|---|---|
| Una carretera sobre el agua detenía la construcción en 20 de los 29 mapas con puentes (Italia, Alemania, Holanda...): su puente «no tendría piso». | Recibe su puente y su piso en todos los mapas con puentes. Aún no visto en el juego en esos mapas. |
| Cada punto de una carretera se ajustaba a la carretera más cercana, sobre una carretera incluso cuando habías colocado un puente allí. | Solo se ajustan los dos extremos de una carretera, primero al extremo de un puente colocado. **Ajustar los extremos a carreteras y puentes** en la bandeja Carreteras lo desactiva. |
| Los edificios y las unidades aparecían por sus nombres en clave, como "Descriptor_Building_VehiculeFactoryLeurre". | Por los nombres que les da el juego (DECOY ARMOR BASE), con la propia línea del juego sobre lo que hace cada uno. |
| No había forma de dar unidades al jugador en un capítulo de campaña: el bando del jugador (0) se rechazaba. | **¿Para quién?** lista los bandos propios del escenario según su misión: «Jugador · USA (bando 0)», «Ordenador · Alemania (bando 1)»... |
| En M03_Italie y otros mapas, una carretera nueva en campo abierto ocultaba de lejos el decorado del mapa, y los objetos que colocabas solo se veían de cerca. | La vista lejana del mapa queda como estaba, y los objetos colocados se ven de lejos como los propios del mapa. Aún no visto en el juego. |
| Las zonas del escenario eran láminas de color que flotaban sobre el mapa y tapaban su suelo y los iconos. | Cada zona es una línea clara a lo largo de su frontera sobre el suelo, con un tinte transparente dentro, como las fronteras de Stellaris. **Relleno de las zonas** ajusta el interior (0 %: solo las fronteras). |

**0.9.1:** arrastra cualquier cosa en el mapa, iconos más claros que puedes cambiar de tamaño y ocultar, tu idioma desde
el primer arranque, y el tipo de cada unidad tal como lo nombra el juego.

| Antes | Ahora |
|---|---|
| Los puntos de inicio, los depósitos de suministros y las unidades que aparecen solo se movían con la herramienta Mover, un clic y luego otro. | Agarra cualquiera de ellos en el mapa y arrástralo, sin ninguna herramienta elegida, igual que ya se giraban las cámaras iniciales. Los depósitos y los CG siguen pegándose a las carreteras mientras arrastras. |
| Los iconos del mapa eran monigotes y cajas, y todos los búnkeres se veían iguales. | Un icono para cada tipo: un soldado, un tanque, un camión para los depósitos de suministros, un avión, cañones, un CG bien marcado, la Armor Base y el aeródromo diferenciados, y cada búnker con el suyo (antitanque, ametralladora, antiaéreo, artillería, fuerte, puesto de observación). |
| Los iconos eran voluminosos desde lo alto, y la única forma de ocultarlos era ocultar todo el escenario. | Los iconos se encogen a medida que la cámara se aleja, un deslizador ajusta su tamaño, y la bandeja Escenario muestra u oculta cada tipo (inicios, cámaras, depósitos, edificios, unidades, zonas, pueblos). Se guarda para la próxima vez. |
| El Studio arrancaba con los nombres en clave, y el idioma estaba en Ajustes, así que los jugadores no sabían que habla su idioma. | El primer arranque pregunta: «Elige tu idioma», cada idioma en sus propias palabras, con el idioma de tu juego en Steam marcado. Luego, un botón de idioma arriba, siempre a la vista. |
| Las unidades solo eran «Terrestre» o «Aéreo». | Bajo Terrestre, Infantería y Aéreo, los tipos propios del juego: Tanque ligero, medio y pesado, Cazacarros, Reconocimiento blindado, Caza, Cazabombardero, Bombardero ligero, medio y pesado, Reconocimiento aéreo... también en la línea de cada unidad, en tu idioma. La búsqueda los encuentra («bombardero», «reconocimiento»). |
| La lista de aplicaciones instaladas de Windows mostraba la primera versión que se instaló. | Muestra la versión que tienes. |

**0.9.0:** las carreteras se ven bien. Una carretera que dibujas ahora se parece a las carreteras propias del mapa,
desde lo alto y a ras de suelo. Llegar hasta aquí llevó mucho tiempo y muchas pruebas, más que los puentes. Probado en
el juego en «Día D».

![Una carretera nueva de cerca en «Día D»: asfalto con una línea central discontinua y arcenes de grava que se funden con la hierba](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Antes | Ahora |
|---|---|
| Una carretera nueva desaparecía cuando la cámara bajaba hacia ella: solo se veía su pintura, desde lo alto. | De cerca se dibuja con las calcomanías de asfalto propias del mapa, colocadas a lo largo como las coloca el mapa, con una calcomanía de borde a cada lado: asfalto, una línea central discontinua, arcenes de grava. |
| La pintura era un solo color plano, más pálido y más ancho que las carreteras del mapa. | La pintura se mide sobre las carreteras propias del mapa: su color, sus arcenes y cómo se funden con el suelo. Cada mapa tiene la suya. |
| La hierba, los arbustos y los árboles de las granjas crecían a través de una carretera nueva. | Se quitan las plantas y los objetos del mapa que hay en el camino de la carretera (unos 6 m a cada lado). Los bosques conservan su cobertura y su movimiento, y los edificios se quedan. |
| Solo se conocían las calcomanías de carretera de «Día D». | En los mapas del desierto se usan sus propias calcomanías, colocadas de la misma forma (aún no visto en el juego). |
| Un borrado grande (miles de círculos) tardaba muchos minutos en construirse. | Mucho más rápido: solo se miran los círculos cercanos a cada parte del mapa. |

![Tres carreteras nuevas que salen de la carretera principal de «Día D»](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-6-done-overview.jpg)

**0.8.3:** las herramientas de escenario del editor de mapas del RUSE-Mod-Manager de LittleGroove: los depósitos de
suministros y los CG se pegan a las carreteras, un icono para cada edificio y unidad, y la cámara inicial de cada
jugador, que se muestra, se lleva y se gira. Aún no probado en el juego.

| Antes | Ahora |
|---|---|
| No se podía colocar un punto de depósito de suministros. | **Punto de depósito de suministros** es el primero en Añadir unidad → Edificios → Dinero. |
| Un punto de inicio iba justo donde hacías clic, sobre la carretera o lejos de ella por igual. | **Pegar a las carreteras** (activado por defecto) lo pone junto a la carretera más cercana, a la misma distancia que en los mapas propios del juego (lo midió LittleGroove). Desmárcalo para colocarlo en medio de un campo. |
| Las apariciones eran unos pocos iconos, con letras para el país. | Un icono para lo que es cada una (CG, depósito de suministros, fábrica, fuerte, señuelo, soldado, tanque, antitanque, artillería, prototipo, avión, torreta) y la escarapela del país. |
| No podías ver dónde se abre la partida de un jugador. | Cada punto de inicio muestra su cámara inicial: el vuelo de entrada (punteado), dónde se detiene, lo que mira y la parte del mapa que muestra la pantalla. |
| La cámara inicial de un punto de inicio movido se quedaba en el sitio antiguo. | La cámara se mueve con él; un punto de inicio nuevo recibe su propia cámara. |
| La cámara inicial no se podía cambiar. | Con **Mover**, arrastra la cámara de un inicio alrededor de su CG para abrir la partida desde otro lado; **Cámara como estaba** lo deshace. |
| Un punto de inicio en un bosque se rechazaba. | Permitido: allí funciona un CG, y los camiones de suministro atraviesan los bosques. Solo se rechazan el agua, los acantilados y el suelo bloqueado. |

**0.8.2:** una prueba detenida por un error en tu mod te dice cuál es y lo arregla, mods y mapas por separado, colores
del mapa y apariciones más claros, y una sola copia del juego para todo el PC.

| Antes | Ahora |
|---|---|
| Una prueba detenida por un error en tu mod enterraba el motivo en el registro y remitía a Solucionar problemas, que no puede arreglar un mod. | Cada error se lista encima del registro con un botón que lo arregla: una aparición de equipo en un mapa de BATALLAS, convertida en neutral o quitada (también todas a la vez); una carretera que no une nada, quitada. Solucionar problemas solo aparece para otros fallos. |
| El mensaje de abajo no se podía cerrar. | Cada mensaje tiene una × para cerrarlo. |
| El registro de la prueba no se podía copiar. | **Copiar informe** copia el registro y el mensaje, para un informe de error o para Discord. |
| Los mods y los mapas compartían un menú. | Los mods y los mapas tienen cada uno su propio menú, y Exportar pone el archivo directamente en la biblioteca del Launcher. |
| Todas las apariciones del mapa se veían iguales. | Cada aparición es un icono de edificio, tanque, soldado o avión del color de su bando, con su país. |
| Los colores del mapa no se explicaban. | Una leyenda de colores para la cobertura, adónde van las unidades y Quitar; la cobertura de la herramienta Pueblo tiene su propio color; un deslizador de transparencia para cada capa. |
| Las colinas y los árboles atravesaban las zonas de un escenario. | Las zonas flotan sobre el suelo, y un deslizador **Altura de las zonas** ajusta a qué altura. |
| Cada prueba conservaba su propia copia del juego. | Una sola copia con mods para todo el PC, compartida con el Launcher. |
| La versión no se mostraba, y Novedades era una lista. | La versión está junto al nombre, y Novedades abre una tabla de antes/después como esta. |
| Pocas descripciones emergentes. | Descripciones emergentes en los controles principales, escritas para jugadores nuevos en el modding. |
| Las carreteras nuevas en Twilight of the Gods, Alpha, Ostfriesland y Robert no tenían el modelo de carretera del mapa. | También lo reciben. |
| La construcción decía que las carreteras nuevas se «dibujaban de cerca». | Dice que se ven de lejos; de cerca aún no se ven (sigue siendo un problema conocido). |

**0.8.1:** unidades de cualquier nación, un aspecto nuevo, una barra de herramientas más corta y la herramienta Quitar.
- **Las unidades de otra nación funcionan.** Una unidad nueva puede ir en el menú de construcción de cualquier nación,
  venga de donde venga su modelo: un Tiger o un Ju 87 alemanes para EE. UU., y también un Zero o un Chi-Ha japoneses.
  Se construye, combate, muestra su imagen en su tarjeta y en su marcador, y se puede seleccionar en tierra y en el
  aire, incluso en una partida en la que nadie juega la nación de la que procede (probado en el juego, 2026-10-02). La
  construcción hace que los modelos de esa nación se carguen en cada partida; una partida necesita un poco más de
  memoria y de tiempo de carga.
- **Un aspecto nuevo:** los azules de R.U.S.E. en lugar de negro y oro, y un logotipo nuevo: la mesa de la sala de
  guerra.
- **La barra de herramientas del editor de mapas es más corta.** Las herramientas que van juntas comparten un mosaico,
  con una pestaña para cada una: Terreno y agua, Cobertura y movimiento, Carreteras y puentes, Edificios, Objetos y
  árboles, y luego Quitar, Escenario y Comprobar. Un mosaico se abre en la pestaña que usaste por última vez.
- **Herramienta Quitar:** arrastra sobre los árboles y objetos propios del mapa (también los edificios, si los eliges)
  y desaparecen cuando se construye el mod. Los círculos rojos se guardan en el mod, lo que cubren se tiñe de rojo, y
  la bandeja cuenta lo que van a quitar. Donde se quitan árboles, el suelo se abre a todas las unidades y pierde su
  cobertura de bosque. Quitar como es debido los edificios, carreteras, arbustos y rocas propios de un mapa llega
  después.
- **El instalador ofrece una copia de seguridad limpia del juego** junto al acceso directo del escritorio, y dice por
  qué: con ella, el solucionador de problemas puede devolver todo lo que cambió otro gestor de mods.

**0.8.0:** el editor de mapas madura: pinceles y paneles nuevos, puentes que las unidades cruzan de verdad, bosques que
puedes despejar, y una construcción que comprueba las reglas del juego para que lo que hagas funcione a la primera.
Además, un solucionador de problemas y una copia de seguridad limpia del juego.
- **Novedades del editor de mapas:**
  - **Pinceles Abrir** (Movimiento): lo contrario de Bloquear. Da a las unidades suelo del que el mapa las mantiene
    fuera (todas las unidades, infantería o vehículos). Abrir el agua está permitido, con un aviso: allí las unidades
    se quedan sobre el cauce.
  - **Pincel Bosque** (Cobertura): árboles y cobertura en un solo trazo; Deshacer quita ambos.
  - **Panel Puentes:** los tipos de puente propios del mapa, y un puente colocado a mano con la longitud y el giro que
    elijas; los cruces de agua de las carreteras nuevas, dibujados en oro.
  - **Comprobar este mapa:** lista lo que saldría mal antes de probar (suelo aislado, carreteras o puentes que las
    unidades no pueden usar, extremos de carretera sin unir, edificios sobre carreteras), y al hacer clic en uno se
    muestra dónde.
  - La construcción abre a las unidades los cauces drenados o que se han secado al elevarlos.
- **Despejar los árboles y objetos propios del mapa:** círculos `[[erase]]` en el `scenery.toml` de un mod (escritos a
  mano por ahora; una herramienta Quitar en el Studio está en camino). Los tanques entran en un bosque despejado, y la
  infantería que está allí ya no queda oculta.
- **Los objetos colocados se asientan en el suelo a cualquier tamaño.** Un edificio ampliado 10× flotaba en el aire;
  ahora se asienta en el suelo como los del mapa.
- **Corregido: la cobertura en los mapas que no son cuadrados** («Día D», Frontline, Djebel, Medjez, Handshake over the
  Elbe, y los mapas de campaña de Túnez, Holanda y las Ardenas). La cobertura pintada o despejada allí (los pinceles
  Cobertura, Descubrir, Pueblo y Bosque, `cover.toml`) caía hasta a un kilómetro de donde se dibujó, y la vista de mapa
  también la mostraba en ese lugar equivocado. Ahora ambas cosas están bien: si pintaste cobertura en uno de estos
  mapas, vuelve a mirarla en la vista de mapa. Los mapas cuadrados (Blitz y la mayoría de los demás) siempre
  estuvieron bien.
- **Los puentes funcionan en el juego.** Una carretera que dibujas sobre el agua recibe el tipo de puente propio del
  mapa (también el de los mapas holandeses), y los tanques, la infantería y los camiones de suministro lo cruzan por el
  tablero, la infantería a la altura del tablero. Los extremos del puente se unen a las carreteras que las unidades ya
  usan y se mantienen lejos de los edificios del mapa; un puente que no se puede unir queda cerrado, y la nota de la
  construcción dice con qué se encontró la carretera y dónde.
- **La construcción comprueba las reglas del juego.** Cada archivo que cambia un mod se comprobó frente a lo que el
  juego hace con él, y un mod que se rompería en el juego se rechaza con una nota que dice por qué, antes de escribir
  nada:
  - carreteras: las unidades ahora siguen las carreteras nuevas, no solo los camiones de suministro, y una carretera
    nueva que no se une a ninguna otra se rechaza (la red de carreteras debe quedar de una sola pieza);
  - edificios y bloqueos colocados: las unidades ya no pueden atravesarlos; los edificios, puentes y árboles nuevos se
    ven a cualquier distancia;
  - terreno: el agua nueva queda cerrada a las unidades, el mapa de la IA sigue tus bosques, bloqueos, puentes y agua,
    y un trazo que no puede cambiar el suelo (o que llega al piso de un puente) lo dice;
  - unidades: se rechaza una salva, un ID, una nación o una lista de menú incorrectos, se comprueban las banderas de
    las unidades, y cada bandera se explica en el selector de banderas (las banderas 62 y 63, que cierran el juego en
    una unidad que no es un camión, son un error); una unidad puesta en la fábrica de otra nación se rechaza por ahora
    (cerraba el juego al construirse; hacer que funcione es lo siguiente);
  - escenario: las apariciones son neutrales por defecto, se rechaza la aparición de una unidad cuyos modelos puede
    que la partida no cargue (cerraba el juego al empezar), se rechaza un inicio adonde los vehículos no pueden ir, un
    inicio movido se lleva su cámara, y los puestos se cuentan por equipo.
- **El informe de la construcción** muestra cada aviso (algunos se perdían), y una reconstrucción quita primero la
  copia de prueba antigua, para que no se pueda arrancar una copia antigua por error.
- **Cobertura cuadrada:** `square = true` en una pintura de `cover.toml`, o en un trazo de Cobertura o Descubrir en
  `terrain.toml`, pinta un cuadrado alineado con los ejes del mapa (escrito a mano por ahora; la vista de mapa lo
  dibuja como un cuadrado).
- **Solucionar problemas** (junto a *Probar en el juego*, y en Ajustes > Ayuda): comprueba de una vez lo que puede
  detener una prueba (si se encuentra el juego, Steam, un juego que sigue abierto desde una copia con mods, la unidad y
  su espacio libre, copias sobrantes, archivos de solo lectura, si la aplicación puede escribir donde van las copias),
  con un botón para cada arreglo que puede hacer, y un informe para pegar en un informe de error, sin tu nombre de
  usuario de Windows.
- **Copia de seguridad limpia del juego** (Ajustes): guarda una copia limpia de los archivos de tu juego, compruébalos
  con ella y devuelve todo lo que cambió otro gestor de mods o una edición a mano. Los archivos que no son del juego se
  apartan, nunca se borran. O deja que Steam repare el juego (*Verificar con Steam*). Es el único lugar en el que el
  Studio escribe en la carpeta de tu juego, y solo cuando lo pides.
- **Comparte tu mod:** ¿has hecho un mod? Tras la exportación, el Studio muestra su tamaño y su SHA-256, y cómo
  añadirlo a la lista de mods en GitHub y convertirte en colaborador.
- **Problema conocido: las carreteras nuevas aún no se dibujan de cerca.** Se pintan sobre el suelo y se ven de lejos,
  y las unidades las usan, pero con la cámara cerca del suelo una carretera nueva desaparece. Estamos trabajando en
  ello.

**0.7.6:** un segundo Probar en el juego funciona, y puentes a los que las unidades siempre pueden llegar.
- **Corregido:** cada segundo *Probar en el juego* podía fallar con «An old modded copy ... can't be removed ...
  (Access is denied)». Una copia que Windows no deja borrar (un archivo que una versión anterior enlazó a un archivo
  del juego sustituido, un programa que aún lo tiene abierto) ya no detiene una prueba: se aparta a
  `RUSE-Instances\.trash` y se elimina en cuanto nada la tiene abierta. Si R.U.S.E. sigue abierto desde la copia de
  prueba, se te dice, con el nombre del programa. Pulsar *Probar en el juego* dos veces inicia una prueba, no dos.
- **Corregido:** el puente nuevo de una carretera podía cerrar el juego cuando se ordenaba a las unidades subir a él:
  su tablero no llegaba a ningún suelo que usaran las unidades. Cada extremo de un puente se une ahora al suelo a lo
  largo de la carretera (hasta 62 m de acceso); un puente que no se puede unir queda cerrado a las unidades, con una
  nota, y la construcción nunca escribe suelo al que las unidades no puedan llegar.

**0.7.4:** Probar en el juego funciona cuando los archivos de tu juego están marcados como de solo lectura.
- **Corregido:** *Probar en el juego* fallaba siempre con «[WinError 5] Access is denied» cuando los archivos de
  R.U.S.E. están marcados como de solo lectura (una instalación desde disco, una copia de seguridad restaurada): la
  copia de prueba conservaba la marca, así que una copia que quedaba a medio construir nunca se podía eliminar. La
  copia de prueba ya nunca conserva la marca, y una copia sobrante de una versión anterior se elimina sola (los
  archivos de tu juego quedan exactamente como estaban). Si el juego sigue abierto desde la copia de prueba, se te dice
  que lo cierres en lugar de recibir un error de Windows.
- **Una carretera muestra su longitud** mientras la dibujas, junto al puntero (al estilo de Cities: Skylines); las
  herramientas de Carreteras muestran el total de tus carreteras nuevas.
- **Las carreteras nuevas se pintan sobre el suelo** con el color propio de las carreteras del mapa (comprobado en el
  juego), y **una carretera sobre el agua recibe un puente**: del tipo propio del mapa, una sola pieza estirada de
  orilla a orilla como los puentes propios del juego, para que las unidades puedan cruzar. Una carretera sobre uno de
  los puentes propios del mapa recibe el puente nuevo en su lugar. (Los puentes son nuevos: aún no comprobados en el
  juego.)

**0.7.3:** organiza la vista de mapa a tu manera. El panel del mapa (arriba a la izquierda) y las herramientas (abajo)
se mueven a cualquier sitio por su asa (⠿) y se pliegan con la flecha que hay al lado: el panel del mapa hasta su
título, las herramientas hasta su barra. Haz doble clic en un asa para devolver ese panel a su sitio. Tu disposición
se guarda.

**0.7.2:** carreteras, y pruebas más claras.
- **Dibuja carreteras**, al estilo de Cities: Skylines (el tipo Carreteras de la barra): **Recta**, **Curva** y
  **Libre**. Un extremo cerca de una carretera se ajusta a ella y se une. Las carreteras nuevas se dibujan como cintas
  azules y **las rutas de suministro las usan** (comprobado en el juego). Aún no se pintan sobre el suelo.
- La casilla **Carreteras** muestra en oro las carreteras propias del mapa.
- Las propias palabras del juego: un escenario lleva el nombre del botón del menú principal que lo juega (**Batallas**,
  Operación, Campaña, leídos del texto de tu juego en tu idioma), y una línea dorada bajo el menú de escenarios dice
  dónde se juega, p. ej. *En el juego: Batallas › Día D (6 jugadores)*.
- **Probar en el juego** dice dónde construyó y exactamente qué abrir para ver tus cambios (p. ej. *BATALLAS > Día D*).
- El botón central del ratón también gira la vista en el modo de mirar alrededor (antes allí hacía zoom).

**0.7.1:** varias unidades a la vez, una comprobación del mod y ayuda a mano.
- **Añadir unidad** coloca 1, 2, 4, 6, 8 o 10 a la vez, en **línea, columna, cuña, recuadro o círculo** mirando hacia
  la parte de arriba de la pantalla, con un deslizador de separación y anillos que muestran dónde se colocará cada una.
- La **comprobación del mod**: cada archivo de tu mod se lee como lo lee la construcción del juego, cuando eliges el
  mod y antes de **Probar en el juego**. Una barra roja nombra cada problema; un archivo de mapa roto se puede
  **apartar** (se le cambia el nombre, nunca se pierde), y una carpeta de mapa con el nombre del título del mapa
  (maps/Blitz) se puede **renombrar** con el nombre de su paquete (maps/SuperCrossRoads4) en un clic.
- Corregido: los trazos de **Agua** se guardaban sin su nivel, así que la construcción del juego rechazaba el mod. Cada
  archivo que escribe el Studio ahora se vuelve a leer antes de guardarse.
- La lista de mapas **se pliega** («) para dejar más espacio.
- **Ajustes > Ayuda y comunidad**: la wiki (el nuevo manual de campo), Discussions e **Informar de un problema**, que
  abre un informe de error con tu versión ya rellenada. Un error abajo tiene su propio enlace **Informar**. La
  aplicación no envía nada: tú lees el informe y lo publicas.

**0.7.0:** un aspecto nuevo y herramientas de movimiento. Las herramientas del mapa pasaron a una barra a lo largo de
la parte inferior, como en Cities: Skylines, con el estilo del propio HUD de R.U.S.E.: elige un tipo (Terreno, Agua,
Cobertura, Movimiento, Edificios, Objetos, Árboles, Escenario) y sus herramientas se abren encima; haz clic otra vez o
pulsa Esc para solo mirar alrededor. Los selectores del escenario ahora son mosaicos, no listas desplegables.
**Movimiento:** la casilla **Adónde van las unidades** lo muestra en el mapa (rojo: ninguna unidad; amarillo: solo
infantería), y tres pinceles nuevos cierran el suelo: **Bloquear** (todas las unidades), **Bloquear infantería** y
**Bloquear vehículos**. Los edificios que colocas detienen a las unidades (la casilla **Sólido**, activada por
defecto). Comprobado en el juego: las unidades rodean un foso bloqueado y pasan entre torres colocadas.

**0.6.9:** los edificios, objetos y árboles que colocas ahora se ven en el juego con cualquier zoom (comprobado en
Blitz, hasta 8× su tamaño): cada grupo va en un bloque nuevo envuelto alrededor del pueblo o la granja más cercanos
que el mapa dibuja de lejos. Comprobado en los 32 mapas: nada más se mueve. Las unidades siguen atravesando los
edificios colocados; hacerlos sólidos es lo siguiente.

**0.6.8:** crea pueblos y bosques donde las unidades se pueden esconder. La vista de mapa muestra dónde se esconden las
unidades (la casilla **Cobertura**, en verde), y tres pinceles nuevos lo pintan: **Cobertura**, **Descubrir** y
**Pueblo** (haz clic en un pueblo: la cobertura rodea cada uno de sus edificios, también los colocados). Comprobado en
el juego: la infantería sobre cobertura pintada queda oculta.

**0.6.7:** los objetos colocados llegan hasta 10× su tamaño (el deslizador Tamaño de la herramienta Colocar; [ y ]
avanzan de 0,1 en 0,1 hasta 3×, y luego de 0,5 en 0,5).

**0.6.6:** la munición también se ordena por tipo: proyectiles AP, proyectiles HE, antiaérea, ametralladoras, armas de
infantería, antitanque de infantería, bombas y cohetes (la lista Tipo encima de la munición). Los mods también pueden
pintar cobertura (donde las unidades se esconden, como en un bosque) y suelo bloqueado en un mapa
(`maps/<map>/cover.toml`); la herramienta del Studio para ello llega después.

**0.6.5:** los escenarios se pueden editar en el mapa. **Mover** un punto de inicio o una aparición (haz clic en él y
luego donde va; Devolver lo deshace). **Añadir unidad** hace aparecer una unidad o un edificio cuando empieza el
escenario: elige su categoría (edificios, terrestres, infantería, aéreos), luego su tipo (para edificios: CG, dinero,
fábricas, fuertes y defensas, señuelos falsos; para unidades: la fábrica que las construye), luego la unidad (por
nación) y su bando. Se guarda en el `maps/<map>/scenario.toml` del mod. La lista de unidades tiene el mismo filtro
Tipo.

**0.6.4:** la lista de mapas tiene un filtro por tipo: todos los mapas, o solo los mapas de escaramuza, Operaciones,
campaña, demo o prueba (según los propios menús del juego; un mapa puede ser de varios). Se recuerda.

**0.6.3:** una pestaña **Ajustes** (junto a Unidades y Mapas): el idioma, las teclas de la vista de mapa, la carpeta
del juego y las actualizaciones en un solo sitio, listo para más.

**0.6.2:** buscar actualizaciones es más fiable: cuando GitHub rechaza la única comprobación del arranque (permite 60
por hora por dirección de internet, compartidas por todo lo que la usa), el Studio lee en su lugar la lista de
versiones de GitHub. Los mods también pueden hacer aparecer unidades y edificios en un escenario (`[[spawn]]` en
`maps/<map>/scenario.toml`).

**0.6.1:**

- **Tu idioma y tus teclas se conservan** tras reinicios, actualizaciones y reinstalaciones (se perdían en cada
  arranque).
- **Escenarios agrupados como los usa el juego:** Escaramuza, Operaciones, Campaña, Demo, Prueba, y los que ningún menú
  carga, cada uno con el nombre que le dan los menús del juego («10. UTAH BEACH», «Anzio»).
- **Los mods pueden mover los puntos de inicio y las apariciones** (`maps/<map>/scenario.toml`); comprobado en el
  juego: el CG empieza donde lo pone el mod.

**Novedades de la 0.6:**

- **Terreno que funciona en el juego:** el suelo que elevas, bajas o aplanas ahora acepta órdenes de movimiento, la
  cámara se queda por encima, y los árboles y edificios se asientan sobre él. La receta de DomesticNukes y su Claude:
  primero se mueve el suelo de juego, el suelo dibujado lo sigue, y se amplían los límites de altura ocultos del juego.
  Comprobado en los 32 mapas.
- **Escenarios en el mapa:** una fila «Escenario» elige uno de los escenarios del mapa (escaramuza, desafíos,
  capítulos de campaña) y muestra sus zonas, puntos de inicio (pilares del color de cada alianza), apariciones (rombos
  blancos) y nombres de pueblos. Señala uno para ver qué es. El primer paso hacia hacer mapas.

**0.5.2:**

- **Pinceles Agua y Drenar** (Agua en la tecla 0): inunda el suelo por debajo de un nivel para hacer un lago, o seca
  un lago o un río. De DomesticNukes y su Claude, comprobado en el juego en Blitz.
- **Tus propias teclas:** «Cambiar teclas…» bajo la línea de ayuda de la vista de mapa: haz clic en una acción, pulsa
  una tecla. Predeterminados las devuelve a como estaban.

**0.5.1:**

- **Un arma conserva su propio fogonazo y su sonido:** cuando un arma dispara la munición de otra unidad, ahora también
  toma el fogonazo y el sonido de disparo de esa unidad (el cañón del Sherman en un fusilero dispara como un Sherman).
  El arma muestra cuál reproduce.
- **Pincel Nivelar** (tecla 7): pinta el suelo llano a la altura donde empiezas a arrastrar.
- **WASD se mueve con la cámara**: W siempre es hacia delante en la pantalla, sea cual sea el giro de la vista.
- El índice del juego se vuelve a construir una vez, la primera vez que se abre 0.5.1 (alrededor de medio minuto).

**Novedades de la 0.5:**

- **Unidades nuevas:** copia una unidad desde su página, ponle nombre y precio, y ponla en un menú de construcción.
- **Munición y banderas:** un tipo Munición con todas las municiones. Un arma puede disparar la munición de otra arma
  (se muestra la nación de la que procede) o su propia copia de ella. Las listas de banderas (lo que es y lo que hace
  una unidad) se pueden editar, como en el editor de unidades de RUSE Mod Manager.
- **Mapas:** cada mapa muestra su nombre en el juego, en tu idioma, junto a su nombre en clave. Los edificios, objetos y
  árboles se dibujan con **los modelos 3D y las texturas reales del juego**, gracias a DomesticNukes y su Claude.
- **Pinceles de terreno:** eleva, baja, suaviza y haz rampas en el suelo, guardado en el mod. **Empezar de nuevo**
  limpia un mapa.
- **Herramienta Colocar:** un clic coloca un edificio, un objeto o un árbol. Pinta un área, o haz clic dos veces para
  una línea (un seto, una calle). Deshacer revierte toda un área o una línea. Por ahora el decorado es solo de aspecto:
  las unidades lo atraviesan.
- **Teclas:** WASD / flechas mueven la vista, Q/E la giran, R/F hacen zoom. Pasa el ratón por cualquier botón para ver
  su descripción emergente.
- **Exportar .rusemod:** un solo archivo que instala el Launcher.
- **Se actualiza solo:** a partir de esta versión, una barra avisa cuando sale un Studio más nuevo;
  **Actualizar ahora** lo instala.

Es nuevo y apenas se ha probado fuera del PC del desarrollador, así que cuéntanos cualquier cosa rara en GitHub Issues.

![La pestaña Mapas de RUSE Studio: Centre of Gravity en 3D](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-maps.jpg)

![RUSE Studio en su modo de vista previa, con unidades de ejemplo](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-unit.jpg)
