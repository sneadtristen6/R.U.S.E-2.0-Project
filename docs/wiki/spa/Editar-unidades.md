# Editar unidades

> **Para:** modders · **Necesitas:** RUSE Studio y un mod · **Tiempo:** el que quieras

## Encontrar una unidad

La pestaña **Unidades** lista cada unidad y cada edificio. Acota la lista con:

- el cuadro **Buscar** (nombres internos o los nombres que ven los jugadores, en cualquiera de los diez idiomas del juego: el botón de idioma de arriba).
  Cada palabra que escribes debe coincidir; las **#etiquetas** acotan la lista (`#us`, `#germany`, `#air`, `#armor`,
  `#new` para las unidades nuevas de tu mod; escribe `#` para verlas todas), y tus búsquedas recientes se conservan;
- las fichas de **Tipo** y **Nación**;
- el menú **clase**: para qué sirve, como cuartel general, dinero, fábricas, fuertes y señuelos en los edificios, o la
  fábrica que construye una unidad.

## Cambiar un valor

1. Haz clic en la unidad. Sus valores se listan por secciones (precio, blindaje, velocidad, armas...).
2. Escribe un valor nuevo. Se guarda en tu mod al momento; el valor del juego se ve al lado.
3. **Deshacer**, junto a un valor, devuelve el valor del juego.

## Banderas: qué es una unidad y qué puede hacer

Las banderas son interruptores de sí o no, numerados del 0 al 104, que le dicen al juego qué es una unidad (un avión,
un camión, infantería, un edificio...) y qué puede hacer (entrar en los bosques, ver a su alrededor, disparar solo
cuando se le ordena...). En la página de una unidad se ven como fichas, cada una con su nombre: pasa el ratón por
encima de una para ver exactamente qué hace, cómo usarla y cuán seguros estamos de ello. La cruz quita una; **Añadir un
indicador…** añade una, ordenadas según para qué sirven.

**Guía de banderas: todas explicadas** (bajo las banderas) abre la lista completa, con un cuadro de búsqueda. Para cada
bandera dice:

- **qué es y qué hace** en el juego;
- **cómo usarla**;
- **cuán seguros estamos:** *probada en el juego*, *de las unidades del juego* (lo que tienen en común las propias
  unidades del juego que la tienen), *esperada, aún sin probar*, *la pone el propio juego* (las activa y desactiva
  mientras se ejecuta: en la lista de una unidad no hacen nada) o *sin uso*.

**El Studio comprueba las banderas de cada unidad** cada vez que las cambias, y otra vez antes de que empiece el juego:

- **Los cierres conocidos detienen la construcción**, así que el juego nunca se inicia con ellos. La página de la
  unidad dice por qué y ofrece el arreglo (**Quitar 62**, **Añadir 100**):
  - 62 (camión) o 63 (camión de construcción) en algo que no es un camión: el juego se cierra al empezar la partida;
  - 99 (avión de reconocimiento) en un avión con armas, sin la 100 (caza): el juego se cierra cuando se manda al avión
    a atacar. Usa el cuadro **Función** (Reconocimiento conserva sus ataques) o añade la 100;
  - 59 (transporte de paracaidistas) en algo que no sea un avión, o en un avión sin unidad que lanzar.
- **Lo que se espera que estropee una unidad es un aviso**, no una parada: la 2 (avión) en una unidad terrestre, la 4
  (edificio) o la 49 en una unidad, la 6 o la 76 en una unidad que debería moverse (se queda quieta), la 42 (infantería)
  en un vehículo, o quitar la 43 (su equipo la cuenta) o la 22 (el jugador puede darle órdenes).

Útiles, probadas en el juego: quita juntas la **11, la 21 y la 55** para que un vehículo entre en los bosques; la **1**
da a cualquier unidad fuego indirecto; la **71** ve a su alrededor; la **77** dispara solo cuando se le ordena.

**Tipos de bandera propios** (Studio 0.9.8.8): **Crear o cambiar tipos de bandera…**, bajo las banderas de una unidad,
crea un conjunto con nombre de banderas del juego, cada una **Activa** o **Desactiva**, con una línea sobre para qué
sirve. **Dar un tipo de bandera…**, en cualquier unidad, activa y desactiva esas banderas de una vez; quitárselo
devuelve las banderas de la unidad a como estaban. Cambia un tipo y cambia también cada unidad que lo tiene. El juego
solo actúa sobre sus propias banderas, así que un tipo combina lo que ya hacen. Aún sin probar en el juego.

## Crear una unidad nueva

Una unidad nueva empieza como copia de una unidad del juego, con su propio nombre, así que puedes cambiarla sin tocar
la original. La pestaña Unidades tiene dos botones arriba: **Cambiar una unidad** (la lista, luego los valores de la
unidad y Blender) y **Nueva unidad (importar un modelo)**. Con **Nueva unidad**, elige la unidad de la que partir, dale
un nombre y haz clic en **Crear**; luego cámbiala como cualquier otra. O elige la unidad y pulsa **Nueva unidad…** en
su página.

## Cambiar el aspecto de una unidad

La página de la unidad muestra su **Modelo 3D**: arrastra para girarlo, usa la rueda para acercarlo.

Debajo, **Aspecto y movimientos** reúne todo lo que tiene que ver con el aspecto y los movimientos de la unidad, una
fila para cada cosa, en el orden en que trabajas: **Modelo**, **Sus soldados** (un pelotón cuyos fusileros y soldado
con arma pesada tienen modelos distintos), **Sonidos y animación** y **Viaja en**. Cada fila dice lo que la unidad
tiene ahora y tiene un botón para lo habitual; **Más** muestra ahí mismo el resto de opciones de esa fila. Todo lo que
cambias se guarda al momento en tu mod: nada que guardar, ninguna carpeta que elegir. Repintar, su propia copia del
modelo, el uniforme de un pelotón y un modelo propio están en la fila **Modelo**; los sonidos y las animaciones se
cambian en RUSE Decoy desde la fila **Sonidos y animación** (**Cambiar en RUSE Decoy**): una animación solo para esta
unidad o para todas las unidades que la usan, un sonido para todas las unidades que lo usan.

- **Repintar en Blender:** haz clic en **Abrir en Blender** (Blender es gratis; si el Studio no lo encuentra, la página
  ofrece **Conseguir Blender (gratis)** y **Elegir Blender…** para indicarle dónde está `blender.exe`). La unidad se abre con sus imágenes,
  lista para pintar sobre el modelo. Pinta y luego haz clic en **Traer**: tu
  pintura entra en tu mod. Visto en el juego, de cerca y de lejos.
- **Su tarjeta en el menú de producción:** gira y acerca el modelo 3D hasta que se vea bien dentro del marco
  discontinuo, y luego **Usar esta vista como tarjeta**. **Tarjeta del juego** la devuelve. Visto en el juego. En una
  unidad nueva, la tarjeta es suya: la unidad que copia conserva su imagen.
- **Su propia copia del modelo:** una unidad dibujada con el modelo del juego comparte su pintura con cada unidad
  dibujada con él. **Darle su propia copia del modelo** (en su página) crea el mismo modelo con texturas propias: luego
  **Abrir en Blender** pinta solo esta unidad. Funciona con unidades nuevas y con las del juego.
- **El uniforme de un pelotón:** los soldados del juego de una nación llevan todos una misma imagen (los de EE. UU.:
  sus GI, Rangers y paracaidistas, y las dotaciones de sus cañones y vehículos), así que el **uniforme predeterminado**
  no se repinta aquí. Elige **Uniforme personalizado** para dar al pelotón uno propio, y luego píntalo en Blender. Visto
  en el juego.
- **Viaja en:** el camión en el que se convierte un pelotón o un cañón en las carreteras: el del juego, el de otra
  nación o una copia de un camión que hiciste y repintaste. Visto en el juego.
- **Un modelo propio (unidades nuevas):** **Importar modelo…** trae un modelo 3D de Blender o de cualquier herramienta
  3D. Consulta [[Importar un modelo|Importar-un-modelo]]. Una unidad del juego conserva su modelo: su página tiene **Nueva
  unidad a partir de esta…** para crear la unidad nueva en la que va el modelo.
- **Una unidad nueva, de principio a fin:** **Nueva unidad (importar un modelo)** arriba en la pestaña Unidades, elige
  la unidad de partida (un tanque para un tanque, un pelotón para soldados o para un caballo con jinete), ponle nombre
  y haz clic en **Crear**. Luego recorre **Aspecto y movimientos** de arriba abajo: su modelo, sus soldados, sus
  animaciones, sus sonidos, su camión. Dale una carta, ajusta su precio y sus valores, y **Probar en el juego**. Un
  mod grande con muchas unidades nuevas son los mismos pasos para cada una: cada unidad guarda todo eso en tu mod bajo
  su propio nombre.
- **Una unidad que lleva a su jinete (un caballo, una moto):** un solo modelo con el jinete y lo que monta sobre un
  mismo esqueleto, con sus propias animaciones (al menos quieto, caminar y correr), importado sobre un pelotón
  copiado: mira [[Importar un modelo|Importar-un-modelo]], su parte sobre un modelo con huesos y animaciones propios.
  La Horse Squad se hizo así en el Studio y se jugó en el juego (noviembre de 2026); nada más hecho así se ha probado
  todavía en el juego.

## Blindaje

**Blindaje**, en la página de una unidad, elige uno de los niveles de blindaje del juego (los tanques tienen del 1 al
5, el número del escudo). La unidad combate con él, y su tarjeta y su menú de producción lo muestran. Cambiar un número
dentro de la propia parte del blindaje hacía que una unidad combatiera con un valor mientras su tarjeta mostraba otro,
así que esa parte ya no se puede cambiar directamente. Visto en el juego.

## Investigación: de qué es una mejora

La página de una unidad tiene un cuadro **Mejora e investigación**: la unidad de la que es una mejora (**Mejora de**),
sus propias mejoras, y su precio y su tiempo de investigación. Elige otra unidad del mismo menú de producción, o
**Ninguna: una unidad propia** para que se pueda comprar desde el principio. Los tiempos de investigación se pueden
escribir en segundos o en minutos (el selector de al lado).

Cuando quitas una unidad desde la que se investigan otras, **Ajustes > Investigación** decide qué pasa: **Avisarme
antes** (lo predeterminado), **Negarse** o **Volver a enlazarlas** con su propia unidad madre. Una unidad que se queda
investigada desde una que ya no está lo dice aquí y en la barra de comprobación, y la construcción se detiene en ella
hasta que elijas otra.

Una unidad que se muestra en su menú de producción debe investigarse desde una unidad que también se muestre ahí: la
que puedes construir va primero, y la investigación después. Una unidad que se muestra en una fecha de batalla en la
que la unidad desde la que se investiga está oculta detiene el juego cuando se abre ese menú de producción (visto en el
juego), así que la barra de comprobación la nombra y la construcción se detiene en ella. Vuelve a mostrar la otra
unidad, o elige otra unidad desde la que investigarla, o ninguna. **Naciones > Ocultar todo** lo hace por ti: una unidad
que se queda investigada desde una oculta pasa a poder comprarse desde el principio.

## Unidades de otras épocas

366 unidades desde la Primera Guerra Mundial hasta hoy, cada una un modelo 3D gratuito de otro autor, se pueden añadir
a tu mod como unidades nuevas, a su tamaño real y tras una investigación: consulta
[[Unidades de otras épocas|Unidades-de-otras-épocas]].

## Armas y munición

El cuadro **Armas**, en la página de una unidad, lista sus armas (el Arma 1 es el cañón principal). **Cómo funcionan las
armas y la munición**, debajo, también tiene estos pasos.

1. **Cada arma dispara una munición.** La lista de al lado elige cuál: cualquier munición del juego, ordenada por tipo
   (perforante, explosiva, antiaérea, ametralladoras, bombas, cohetes...), o una copia que hiciste. Su fogonazo y su
   sonido van con ella.
2. **La munición decide lo que hace el arma:** su daño, su alcance, su cadencia de fuego y a qué puede alcanzar.
   **Abrir la munición** para ver y cambiar sus números.
3. **Cambiar una munición cambia cada unidad que la dispara** (su página las lista). Para una sola unidad: en la página
   de la munición, haz clic en **Copiar esta munición…**, cambia la copia y luego elige la copia en la lista del arma.
   El control deslizante de **Alcance** de un arma pregunta lo mismo: solo esta unidad, o cada unidad con esa munición.
4. **Alcanza** (bajo un arma) elige el suelo, los aviones o los dos. El cuadro **Función** de un avión fija cómo ataca
   (abajo).
5. **Añadir o quitar un arma aún no es posible:** las armas están ligadas a las animaciones del modelo, y todavía no
   hemos llegado tan lejos.

**Su nombre en el juego** (en la página de una munición, Studio 0.9.8.8): cómo llama el juego a la munición, su
**Nombre** (Calibre medio, MG 42) y su **Tipo** (Proy. perf.). Escribe palabras nuevas y guarda: todos los idiomas las
muestran hasta que cambies uno por separado con **Cambiar el texto…**; **Palabras del juego** quita las tuyas. Una
munición copiada se llama como tú la llames. Aún sin probar en el juego.

**Clase de arma** (en la página de una munición, Studio 0.9.8.17): qué parte de su daño hace la munición a cada tipo
de objetivo. **Nueva clase de arma…** abre un número para cada uno: edificios y fortificaciones, aviones, paracaidistas
en descenso, infantería, vehículos ligeros (transportes), blindaje 1 a 5 y camiones de construcción. 1 es daño
completo, 2 el doble, 0,5 la mitad, y 0 significa que no puede atacar ese objetivo en absoluto. **Guardar clase** da a
la munición su propia copia de la tabla de daños del juego, así que no cambia el daño de ninguna otra munición, pero
cada unidad que dispara esta munición la recibe (para una sola unidad, usa antes **Copiar esta munición…**). El botón
pasa a decir **Cambiar esta clase de arma…**; **Volver a la clase del juego** quita la copia, y borrar una munición
copiada se lleva su clase con ella. Visto en el juego: pelotones de fusileros cuya munición recibió números contra
tanques dispararon a los tanques con sus fusiles y los dañaron. El botón en sí aún no se ha pulsado en el Studio.

**Velocidad del disparo:** la velocidad y la resistencia del disparo de una munición deciden cuándo llega el impacto:
un disparo más lento impacta más tarde, y a un objetivo en movimiento se le apunta por delante según el tiempo de vuelo
(se sabe por cómo funciona el juego; aún no se ha comprobado en una prueba).

## Cambiar la función de un avión (Studio 0.9.8.5)

La página de un avión tiene un cuadro **Función**: **Caza**, **Cazabombardero**, **Bombardero** o **Reconocimiento**.
Con ella cambian cómo vuela y ataca, cómo lo usan los jugadores del ordenador y los textos de su menú de producción.

- **Bombardero:** un bombardero suelta sus bombas en una pasada recta, y solo desde una bodega de bombas. Elige primero
  bombas para una de sus armas (Armas, abajo) y luego hazlo Bombardero: sus bombas van a una bodega de bombas copiada de
  la de un bombardero del juego, y puedes cambiarlas ahí. Este es el arreglo para un cazabombardero con bombas de
  alfombra que no soltaba nada. Visto en el juego.
- **Reconocimiento:** un avión con ametralladoras sigue pudiendo atacar (el cuadro dice **Reconocimiento, conservando
  sus ataques**) y recibe la visión de los aviones de reconocimiento. Visto en el juego con un Stuka y un ME109.
- Un avión de paracaidistas conserva su función. **Deshacer**, junto al cuadro, devuelve la función del juego, con sus
  bombas donde estaban.

## Hacer un vehículo de reconocimiento (Studio 0.9.8.5)

El cuadro **Función** de un vehículo terrestre: **Reconocimiento** le da la visión de los coches de reconocimiento
(mucho más lejana que la de un tanque), la forma en que los usan los jugadores del ordenador, los textos de su menú de
producción, y puede entrar en los bosques. Sigue igual de resistente y armado que antes. Visto en el juego con un
Panzer IV.

## A qué alcanza un arma (Studio 0.9.8.5)

Bajo cada arma, **Alcanza** elige **El suelo**, **Los aviones** o **El suelo y los aviones**. Los aviones: el arma
dispara una copia de su munición que alcanza a los aviones (y no hace nada al suelo). Los dos: conserva su munición y
recibe una segunda arma a su lado para los aviones, como llevan una para cada cosa los cañones antiaéreos del juego. Un
tanque disparando a los aviones se ha visto en el juego; el arma de un avión ajustada para alcanzar solo el suelo aún no
hace daño.

## Pruébalo

**Probar en el juego** construye el mod e inicia R.U.S.E. Busca la unidad donde se construye (su fábrica) en una batalla (menú principal: **BATALLAS**, luego un mapa).

**Siguiente:** [[Exportar y compartir|Exportar-y-compartir]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Edit-Units]]
