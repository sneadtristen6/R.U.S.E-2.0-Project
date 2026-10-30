# Editar un escenario

> **Para:** modders · **Necesitas:** RUSE Studio 0.9.8.4 y un mod · **Tiempo:** unos minutos

Un **escenario** es aquello con lo que empieza un mapa: zonas de captura, el punto de inicio de cada bando, y unidades
y edificios ya en el campo. Un mapa tiene varios: uno por cada forma en que el juego lo juega.

## Las tres formas en que el juego juega un mapa

Son los botones del menú principal de R.U.S.E.:

| Botón | Qué es |
|---|---|
| **BATALLAS** | Una partida libre contra el ordenador en un mapa, con los jugadores que elijas (otros juegos lo llaman escaramuza). |
| **OPERACIÓN** | Una misión corta con objetivos fijos, en una situación ya preparada. |
| **CAMPAÑA** | La historia, capítulo a capítulo. |

El Studio nombra cada escenario por el botón que lo juega, y una línea dorada bajo el menú de escenarios dice
exactamente dónde: por ejemplo **En el juego: Batallas › Día D (6 jugadores)**.

## Elige el escenario

Al principio de la barra de la pantalla del mapa, elige **Escenario** (junto a **Mapa**). Las cosas propias del mapa
(suelo, edificios, árboles, carreteras) se ven atenuadas y no se pueden agarrar por accidente; vuelve a **Mapa** para
cambiarlas. Luego elige el escenario en el menú de arriba. Los puntos de inicio se ven como pilares del color de cada
bando, los puntos de aparición como rombos blancos y las zonas como áreas sombreadas.

## Mover un punto de inicio o de aparición

1. En el lado **Escenario**, haz clic en **Mover**.
2. Haz clic en el pilar o el rombo y luego donde va.
3. Para devolverlo adonde lo tenía el juego, haz clic en él otra vez y elige **Devolver**.

## Añadir unidades: una o toda una formación

1. En el lado **Escenario**, haz clic en **Añadir unidad**.
2. Elige el tipo (Edificios, Terrestre, Infantería, Aéreo), luego la clase y luego la unidad de la lista (agrupada por
   nación).
3. Elige **¿Para quién?** En una Operación o un capítulo de campaña, la lista son los bandos propios de ese escenario,
   sacados de su misión: **Jugador** (tú: el bando 0 en la campaña) y los bandos del **Ordenador**, cada uno con su
   país, además de **Neutral**. El número entre paréntesis es lo que se guarda. Un mapa de **BATALLAS** solo admite
   unidades neutrales (el juego lo empieza sin lista de equipos, así que las unidades de un jugador nunca aparecerían
   ahí).
4. **Cuántos:** 1, 2, 4, 6, 8 o 10.
5. Para más de una, elige una **formación**: línea, columna, cuña, cuadro o círculo. Mira hacia arriba de la pantalla:
   gira la vista para orientarla. **Separación** fija los metros entre unidades.
6. Unos anillos en el mapa muestran dónde estará cada unidad. Haz clic para colocarlas.

Una unidad que añadiste se puede mover como cualquier punto de aparición, o quitar con **Quitar**.

## Más jugadores en un mapa (hasta 8)

Cada jugador empieza en un **punto de inicio** de su equipo, uno por jugador: en un 3v3, los equipos 1 y 2 tienen cada
uno los puestos 1 a 3. Un 4v4 necesita el puesto 4 en los dos.

1. Elige el escenario que el juego juega en línea (su línea dorada dice **Batallas**) y luego, en la barra, haz clic en
   **Escenario**.
2. **Jugadores** (a la derecha) muestra el número del mapa, con el del juego marcado *(juego)*. Elige el nuevo número,
   8 como máximo. La línea de debajo nombra cada punto de inicio que aún falta, p. ej. *equipo 1, puesto 4*.
3. Haz clic en **Añadir inicio del cuartel general**, elige el **equipo** y luego haz clic en terreno despejado donde
   empieza ese jugador, lejos de los demás. Toma el siguiente puesto del equipo, y su cámara y su introducción de un
   compañero de equipo.
4. Cuando la línea diga **Cada jugador tiene un punto de inicio**, usa **Probar en el juego** y abre **BATALLAS**: el
   mapa aparece con su nuevo número, p. ej. *(8) Cotentin (4v4)*.

Un punto de inicio que añadiste se mueve con **Mover**, o se quita con **Quitar**. ¿Más de 8? No: la sala del juego
tiene 8 plazas (probado el 2026-10-02).

> [!NOTE]
> Nuevo, aún no comprobado en el juego: cuéntanos en [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions)
> cómo va una partida de 8 jugadores.

## Un mapa en blanco: coloca el cuartel general de cada jugador

Un mapa empezado como **Terreno en blanco** u **Océano en blanco** (con **Duplicar mapa** de la pestaña Mapas) no tiene
nada del mapa copiado, tampoco sus cuarteles generales. **El cuartel general de cada jugador** (en el lado Escenario)
lista cada cuartel general que necesita el mapa: haz clic en **Colocar** y luego en el suelo donde va. **Probar en el
juego** espera hasta que cada jugador tenga un cuartel general.

**Tamaño del mapa** (Studio 0.9.8.7) hace un mapa en blanco nuevo más grande o más pequeño, una franja cada vez: pulsa
**+** en un lado para añadir una franja de terreno a lo largo de él, o **−** para quitar una, y luego **Aplicar este
tamaño**. Aún sin probar en el juego.

> [!WARNING]
> Los dos mapas en blanco todavía tienen fallos: úsalos bajo tu propio criterio, y cuéntanos lo que encuentres.

## Sectores

**Sectores** (en el lado Escenario) cambia los sectores del escenario, las zonas en las que se juegan las cartas de
engaño. Un mapa en blanco empieza sin ninguno: los haces tú.
- **Formas:** arrastra el punto de una esquina para mover un borde (los sectores que lo comparten se mueven juntos).
  Haz doble clic en un borde para añadir un punto; haz clic derecho en un punto para quitarlo. **Sector nuevo:**
  arrastra un recuadro sobre el suelo. **Ningún sector:** arrastra un recuadro donde no deba haber ningún sector.
  **Borrar sector** da todo su terreno a los sectores de alrededor.
- **Pintar:** elige un sector y luego arrastra sobre el suelo para pintarlo; «Ningún sector» saca ese terreno de todos
  los sectores.
- **Empezar sin sectores** o **Empezar con los sectores del mapa**; **Deshacer** retira el último cambio.
- **Crear sectores** corta todo el mapa en sectores más o menos tan anchos como indica **Sectores de unos** (los mapas
  del propio juego tienen sectores de 1 a 3 km de ancho), con bordes irregulares; **Otra distribución** los corta de
  otra forma. Luego arrastra las esquinas o pinta para cambiarles la forma.

Visto en el juego: sectores pintados en un mapa en blanco, un sector nuevo dibujado en Día D e iluminado solo por una
carta de engaño, terreno fuera de todo sector (un hueco en la mesa del mapa que ninguna carta de engaño ilumina). Las
líneas finas que corta el Studio para que un sector siga siendo de una sola pieza aún no se han probado en el juego.

## Depósitos de suministros en este mapa

Elige un depósito de suministros para darle más camiones (más camiones, más dinero en él), o usa **Todos los depósitos
de aquí**: multiplica los camiones de cada depósito (**veces sus camiones**) o dales a todos el mismo número
(**camiones cada uno**) y luego **Aplicar**. **Volver a los del juego** lo deshace. Para cambiar todos los mapas a la
vez, usa **Depósitos en los mapas** de **Ajustes de la IA y de los jugadores**
([[Economía, IA y más|Economía-IA-y-más]]). Los depósitos con más de 1.000 camiones necesitan el Launcher 0.4.8.4 o
más reciente.

## Una misión propia

Una Operación nueva o un capítulo de campaña nuevo puede jugar su propia misión, con objetivos, eventos y movimientos
de cámara: [[Crear una misión|Crear-una-misión]].

## Ver tus unidades en el juego

1. Haz clic en **Probar en el juego** (arriba del Studio). El Studio construye tu mod en la copia con mods del juego
   (`RUSE-Instances\Modded game` en la unidad de tu juego, o la carpeta que elegiste en Ajustes: una para todo el PC, también la del Launcher) e inicia R.U.S.E. desde ella. El mensaje de abajo
   dice qué abrir, por ejemplo **BATALLAS > Día D**.
2. En el menú principal del juego, haz clic en ese botón (**BATALLAS** para una batalla) y luego elige el mapa
   (**Día D**).
3. Prepara la partida como siempre y empieza. Tus unidades aparecen donde las colocaste.

> [!NOTE]
> Iniciar R.U.S.E. desde Steam inicia el juego sin tu mod. Usa **Probar en el juego** (o **Jugar** en el Launcher).

> [!NOTE]
> Qué punto de inicio corresponde a cada jugador de la sala en una batalla aún se está probando. Cuéntanos lo que
> encuentres en [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

**Siguiente:** [[Exportar y compartir|Exportar-y-compartir]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Edit-a-Scenario]]
