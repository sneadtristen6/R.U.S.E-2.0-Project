# Edificios y menús de construcción

> **Para:** modders · **Necesitas:** RUSE Studio 0.9.8.8 o posterior y un mod · **Lleva:** unos minutos

Los edificios de cada nación, lo que ofrecen sus menús de construcción y en qué orden, y edificios propios. Visto en el
juego.

## El tablero de edificios

Abre la pestaña **Naciones**: bajo cada nación, **Edificios y unidades** muestra sus edificios como filas, cada una con
las unidades que ofrece su menú de construcción, en el orden del juego. El paso **Edificios** de un mod nuevo muestra el
mismo tablero.

- **+** añade una unidad a un edificio: una de la propia nación, una copia de la de otra nación, o una
  [[unidad de época|Unidades-de-otras-épocas]]. Una copia va a tu mod, con el nombre que le da el juego.
- **Arrastra** una unidad por su fila para cambiar su puesto en el menú, o a otro edificio para construirla allí.
- **×** saca una unidad del menú de construcción. Queda oculta, no borrada: la unidad sigue en los archivos del juego.
- **Investigación…** y luego **Poner bajo esta** en la unidad tras la que viene: se investiga desde esa (en cualquiera
  de los edificios de la nación). **Construible desde el principio** no necesita investigación. **Coste de
  investigación** y **Tiempo de investigación (s)** están al lado.

Cada fila dice cuántas unidades tiene. Un edificio que se queda sin nada que construir muestra en el juego la lista de
edificios del cuartel general cuando se elige. Más de 10 unidades en un edificio, un avión en un edificio de tierra o un
vehículo en el Aeródromo: aún sin probar en el juego.

La página de una unidad en la pestaña **Unidades** dice dónde se construye («Se construye en Fábrica de tanques: puesto
2 de 6»), y **Ver en los edificios** abre su fila.

## Grupos

En el juego, la lista de construcción de un edificio muestra cada grupo en una fila: una unidad y sus mejoras (el
Panzer IV y el Panther). El tablero muestra los grupos de cada edificio, cada uno con su cuenta (**4 de 6**), y cuántos
grupos tiene el edificio (**7 de 10 grupos**).

- Una unidad nueva va al grupo de su tipo en su edificio, o a un grupo propio cuando el edificio no tiene ninguno de
  ese tipo. **+** en un grupo, o soltarla encima, la pone ahí; **Nuevo grupo** empieza uno.
- Un grupo tiene como mucho 6 (sus unidades y cartas de investigación), y un edificio como mucho 10 grupos, para que su
  lista quepa en la pantalla. Uno más se rechaza: saca una unidad, o ponla en un edificio propio (**Añadir un edificio…**).
- Una unidad sin tipo de carta en el juego (un camión, el lanzador de V2): elige su grupo.

Aún no probado en el juego.

## Añade un edificio

**Añadir un edificio…**, bajo el tablero de una nación: elige el edificio del juego que copia (**Copia de**), dale un
**Nombre**, y luego:

- **Fabrica las mismas unidades que el edificio copiado**, o
- **Fabrica unidades propias**: una fila y una pestaña propias en la barra de construcción del juego, que llenas con
  **+**. Hasta tres por nación.

El segundo y el tercer edificio con unidades propias necesitan un pequeño parche del juego para más edificios. El Studio
lo descarga una vez y lo aplica solo a tu copia del juego con mods, nunca al juego de tu carpeta de Steam.

## El aspecto propio de un edificio

En la página de un edificio nuevo, **Importar modelo** pone un modelo 3D propio (.glb, .gltf o .3ds) en lugar de una
pieza del aspecto que copia: el edificio principal de una fábrica o de un cuartel general, o la pieza que elijas. Tu
modelo toma el tamaño de esa pieza y se pone donde estaba ella; el resto del aspecto se queda. Los edificios del propio
juego se quedan como están: crea primero un edificio nuevo a partir de uno.

**Su imagen en el menú de construcción:** gira y acerca el modelo hasta que se vea bien dentro del marco discontinuo, y
luego usa esa vista. Consulta [[Importar un modelo|Importar-un-modelo]] para los modelos en general.

## Lo que se ha visto en el juego

Visto: los cambios del tablero (unidades añadidas, movidas, quitadas, investigadas desde otra), un edificio copiado, un
edificio con unidades propias y su pestaña en la barra de construcción, un segundo y un tercero con el parche del juego,
y el modelo propio de un edificio y su imagen.

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Buildings-and-Build-Menus]]
