# Colocar edificios y árboles

> **Para:** modders · **Necesitas:** RUSE Studio 0.7.2 y un mod (Cuadrícula, Recuadro, Trazado, Seleccionar y Rehacer:
> 0.9.8.7; modelos propios: 0.9.8.8) · **Probado en el juego:** los edificios colocados se ven con cualquier zoom,
> hasta 8× su tamaño, y las unidades los rodean. Aún sin probar en el juego: lo colocado con Cuadrícula, Recuadro y
> Trazado, y los objetos movidos

## Colocar

1. En la barra, haz clic en **Edificios**, o en **Objetos y árboles** y luego en su pestaña **Objetos** o **Árboles**.
2. Elige un tipo entre las imágenes (escribe en el cuadro de búsqueda para acotarlas). Cada imagen está hecha a partir
   del propio modelo del juego, y el número de su esquina es cuántos tiene ya el mapa. La lista contiene los tipos
   propios de este mapa: el juego solo acepta un tipo que un mapa ya usa.
3. Elige cómo coloca un clic:
   - **Uno**: un objeto donde haces clic;
   - **Área**: arrastra para repartir objetos en un círculo (**Separación** los mantiene apartados, **Área** fija el
     círculo);
   - **Línea**: haz clic en el inicio y luego en el final, para una fila (un seto, una calle, una hilera de árboles),
     girada a lo largo de ella;
   - **Cuadrícula**: hileras de objetos: haz clic donde empieza la primera hilera y donde termina, luego despliega las
     hileras y haz clic (**Entre hileras** fija la distancia);
   - **Recuadro**: arrastra un recuadro sobre el suelo y suelta: se llena del objeto elegido en hileras;
   - **Trazado**: haz clic a lo largo del camino y luego haz doble clic, pulsa **Enter** o **Terminar**: los objetos
     siguen una curva suave que pasa por tus clics (un seto, una hilera de árboles); con un ancho, una franja de ellos.
     **Esc** descarta una cuadrícula, una línea o un trazado a medio hacer.
4. **De cara a las carreteras:** cerca de una carretera, un objeto se pone a su lado y se gira hacia ella, y una fila
   la sigue; una cuadrícula o un recuadro dejan libres las carreteras. El deslizador de giro sigue girándolo (prueba
   180° si una casa muestra la espalda).
5. **Giro** y **Tamaño** (hasta 10×) son los deslizadores de la derecha. Los árboles varían un poco de tamaño y de
   giro por sí solos, para que un bosque no parezca hecho con un sello.

Antes de hacer clic, el tipo se ve transparente bajo el puntero, girado y con el tamaño que tendrá. Los objetos
colocados se muestran con sus propios modelos, cada uno con un pequeño punto dorado al pie que lo señala desde lejos.

## Seleccionar, mover, girar, eliminar

**Seleccionar** (en las bandejas **Edificios** y **Objetos y árboles**) elige lo que hay en el mapa, lo que colocó tu
mod o lo propio del mapa: haz clic en uno, **Shift+clic** para añadir, o arrastra un recuadro alrededor de varios.
Luego arrastra uno elegido para moverlos, usa **Giro** y **Tamaño**, o **Eliminar**. **Devolver como está en el mapa**
deshace tus cambios en lo propio del mapa; **Esc** no elige nada.

## Modelos propios

**Importar modelo…** (en **Objetos y árboles**) convierte un modelo 3D (.glb, .gltf o .3ds) en una roca, un objeto, un
arbusto o un árbol propio de tu mod de mapas. Se coloca como los del propio juego, en cada mapa del mod, con versiones
más pequeñas hechas para él para las distancias media y lejana. Dale un **Tamaño** y un **Origen**: un modelo que hizo
otra persona solo puede ir en un mod con CC0 o CC-BY, con su autor. Con **Sólido: las unidades lo rodean** marcado, las
unidades lo rodean; sin marcar, lo atraviesan y lo derriban, como los pequeños objetos del propio juego. **Tu modelo…**
lo cambia más tarde. Visto en el juego.

## Edificios sólidos

**Sólido** (activado por defecto) hace que las unidades rodeen un edificio colocado en vez de atravesarlo.
Desactívalo para un edificio que solo esté para mirarlo.

## Esconderse en ellos

Los edificios colocados no esconden unidades por sí solos: abre **Cobertura**, elige **Pueblo** y haz clic en el
pueblo que hiciste.

## Deshacer y Rehacer

**Deshacer** (o **Ctrl+Z**) quita el último objeto, o el área, la línea, la cuadrícula, el recuadro o el trazado
enteros, y el último movimiento, giro, tamaño o borrado. **Rehacer** (o **Ctrl+Y**, **Ctrl+Shift+Z**) lo devuelve.
Todas las herramientas del mapa tienen los dos.

## Quitar los árboles y objetos del propio mapa

1. En la barra, haz clic en **Quitar** (Studio 0.8.1).
2. Elige lo que quita: **árboles**, **objetos**, **edificios** (en cualquier combinación). Cada círculo conserva lo
   que estaba elegido cuando lo pintaste.
3. Arrastra sobre el mapa: los círculos rojos marcan lo que se va, y lo que cubren se tiñe de rojo. **Tamaño** fija
   los círculos; la bandeja cuenta lo que quitarán cuando se construya el mod.

Donde se van los árboles, el terreno se abre a todas las unidades y pierde su cobertura de bosque (probado en el
juego: los tanques entran en un bosque despejado, la infantería allí no queda oculta). Los edificios quitados también
abren su terreno a las unidades. **Deshacer** (**Ctrl+Z**) quita el último arrastre, **Empezar de nuevo** borra todos
los círculos del mapa.

**Siguiente:** [[Editar un escenario|Editar-un-escenario]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Place-Buildings-and-Trees]]
