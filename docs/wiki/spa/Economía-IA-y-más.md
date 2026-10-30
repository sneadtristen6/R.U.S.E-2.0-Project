# Economía, IA y más: las herramientas de LittleGroove

> **Para:** modders · **Necesitas:** RUSE Studio 0.9.8.1 o posterior y un mod · **Tiempo:** el que quieras

El RUSE-Mod-Manager de LittleGroove tenía herramientas que el Studio no tenía. Ahora están en el Studio, cada una en tu
propio mod: un cambio se guarda ahí al momento, y los archivos del juego nunca se tocan.

## Pestaña Ajustes de la IA y de los jugadores

Una pestaña en tres partes: **Ajustes de los jugadores**, **Reglas del juego** y **Jugadores del ordenador**.

### Ajustes de los jugadores

Dinero inicial e ingresos, depósitos de suministros (dinero por camión, camiones por convoy, el tiempo entre convoyes),
límites de producción y las cartas de engaño con las que empieza cada bando. Un cambio cuenta para todos los modos de
juego; donde el modo Nuclear tiene un valor propio, tiene también su propia casilla. Los depósitos de suministros y los
edificios administrativos son edificios: su precio, su tiempo de construcción y su resistencia están en la pestaña
**Unidades**.
Visto en el juego: el dinero inicial y las cartas de engaño al empezar.

**Depósitos en los mapas** (bajo Depósitos de suministros): da a cada depósito de suministros más camiones, y así más
dinero, en **Todos los mapas** o en **Un mapa:** tú eliges. Multiplica los camiones de cada depósito (**veces sus
camiones**) o dales a todos el mismo número (**camiones cada uno**). La línea de encima dice lo que guarda un depósito
con tus valores. Un depósito al que diste sus propios camiones en la pestaña Mapas los conserva. Juega los mods con más
de 1.000 camiones por depósito con el Launcher 0.4.8.4 o más reciente. Visto en el juego (los depósitos del Día D con
500 camiones; los de otros mapas, con el triple de los suyos).

### Reglas del juego

Todas las demás reglas que el juego guarda para todos los jugadores, en grupos: batalla y rendición, población,
movimiento y carreteras, disparo y objetivos, unidades por su cuenta, daño e inmovilización, bosques y visión, aviones,
las cartas de engaño en acción, el mando de juego, colocar edificios, partidas clasificatorias en línea, contornos y
flechas, efectos en pantalla, los colores de bandos y sectores (con un selector de color cada uno) y, por último, unos
cuantos valores cuyo uso aún no se conoce. Cada una dice lo que hace y lo que tiene el juego. Aún no probado en el juego.

### Jugadores del ordenador

Cómo juegan los jugadores del ordenador. Un jugador del ordenador combina tres conjuntos de valores: **Predeterminado**,
su dificultad y su perfil (los dos se eligen en la sala del juego); elige uno para ver y cambiar sus valores: cuándo
empieza a atacar, cuánta fuerza espera tener, cómo defiende, las unidades que prefiere y sus cartas de engaño. Cada
valor se puede cambiar en cada conjunto: uno que un conjunto no incluye cuenta como 0 en el juego, y darle un número lo
añade a tu mod. Debajo, lo que vale para todos los jugadores del ordenador (el valor del ejército que le hace atacar,
sus señuelos...).
Visto en el juego: una carta de engaño quitada del menú, otra movida dentro de él, la duración de una carta y cuándo
empieza a atacar el nivel Fácil.
El resto, aún no probado en el juego.

**Scripts de mapas y misiones**, debajo: los scripts que el juego ejecuta en sus mapas (los capítulos de la campaña,
los desafíos, las Operaciones), mostrados como Python para leerlos. **Copiar** copia uno.

## El cuadro Mejora e investigación de una unidad

En la página de una unidad: la unidad de la que es una mejora (**Mejora de**), sus propias mejoras, y su precio y su
tiempo de investigación. Elige otra unidad, o **Ninguna: una unidad propia**. Consulta [[Editar unidades|Editar-unidades]].

## Pestaña Todos los valores y Archivos

Dos partes, que se eligen con el interruptor de arriba de la lista.

**Todos los valores:** cualquier objeto y valor del juego, cambiado en tu mod: añade o quita un valor, crea o borra un
objeto, da a un valor de texto sus propias palabras. Aún no probado en el juego.

**Archivos:** cualquier archivo dentro de los paquetes del juego: elige un paquete y luego un archivo para verlo como lo
que es (una imagen, una tabla de texto, un script de misión...). **Guardar una copia…** lo guarda fuera; **Cambiarlo por
un archivo mío…** pone el tuyo en tu mod; **Añadir un archivo mío a este paquete…** añade uno nuevo. Tu mod guarda solo
lo que cambias, nunca una copia del archivo del juego. Aún no probado en el juego.

## Misiones y mapas

Los scripts de una misión se pueden cambiar, y el Studio comprueba si está en los menús, si se carga cada archivo que
necesita, y sus textos; se puede subir o bajar en su menú. En un mapa: los nombres de pueblos y colinas, los puntos y
zonas con nombre, y el nombre y la orientación de un elemento del mapa. Se pueden guardar **Notas** en una unidad, un
valor o un jugador del ordenador. Aún no probado en el juego.

## En el Launcher: Convertir un mod antiguo

Un mod antiguo que viene como paquetes propios del juego, hecho para copiarse en la carpeta del juego, se convierte en
un mod que tu biblioteca juega junto a otros: consulta [[Instalar y jugar|Instalar-y-jugar]].

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Economy-AI-and-More]]
