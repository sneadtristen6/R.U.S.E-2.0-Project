# Música y sonidos

> **Para:** modders · **Necesitas:** RUSE Studio 0.9.8.8 o posterior, un mod; para un sonido propio, un archivo de
> sonido (WAV, MP3, OGG o FLAC), para movimientos propios, un archivo de captura de movimiento (.bvh) · **Lleva:** unos
> minutos cada cosa

Todo aquí se hace dentro del Studio, en la pestaña **RUSE Decoy**, el diseñador de sonido y animación (sustituyó a la
pestaña Música en Studio 0.9.8.8). No hay que instalar ningún otro programa.

## Cada sonido del juego

**RUSE Decoy** lista cada sonido que tiene el juego, por tipo, a la izquierda: armas de cerca y a lo lejos, impactos y
destrucción, motores y pasos, entorno, fondos de los mapas, la interfaz, cartas de engaño, voces de las unidades,
cuartel general e inteligencia, charla por radio, diálogos de las misiones (con lo que dice cada frase), música y
sintonías. El cuadro de búsqueda encuentra un sonido por su nombre o por las palabras que se dicen en él.

Para cada sonido:

- **Escuchar** lo reproduce.
- **Volumen:** arrástralo. 100 % es el del propio juego, hasta 200 %.
- **Reemplazar…** abre el editor de abajo, para poner un sonido tuyo en su lugar.

Los cambios se guardan en tu mod y llegan al juego cuando lo pruebas o lo exportas.

## Sustituye un sonido o una canción

1. Suelta un archivo de sonido en el editor, o elige uno. El tuyo puede durar lo que sea: el Studio lo pasa al formato
   del juego.
2. Recórtalo con los dos tiradores, **Fundido de entrada** y **Fundido de salida**, ajusta el **Volumen**, y
   escúchalo.
3. **Usar esto** lo guarda en tu mod. Después, **Cambiar…** lo vuelve a abrir y **Quitar** devuelve el sonido del
   juego.

## Añade una canción

Bajo **Música y sintonías**, las canciones se listan según dónde suenan: el menú principal, los créditos, las tres
listas de las que tiran las batallas, el final de una partida, los objetivos de misión, y los capítulos de campaña y
las Operaciones que las nombran. Las tres listas de batalla: una tranquila mientras los jugadores se desarrollan, una de
combate en cuanto caen los disparos, y la música de los engaños cuando se juega una carta de engaño.

Bajo cada lista de batalla, **Añadir una canción…**: dale un nombre, suelta un archivo de sonido, recórtalo, y luego
**Usar esto**. Se une a las canciones que el juego pone de esa lista, marcada como Nueva.

## Animaciones

Bajo **Animaciones**: cómo se mueven las unidades, desde correr, disparar y recargar hasta morir y la dotación de un
cañón trabajando. Cada una dice cómo la llama el juego y cuántas unidades la usan. **Ver y cambiar…** la muestra en 3D
en una unidad que la usa (arrastra para girarla, la rueda acerca; la vista 3D necesita internet una vez):

- **Velocidad:** 100 % es la del juego, 200 % el doble de rápido, 50 % la mitad de rápido.
- **Usar en su lugar:** otra animación del mismo cuerpo en su lugar (los fusileros podrían correr como cuando huyen,
  por ejemplo).
- **Un hueso**, con **Tamaño** y **Girar sobre** / **Giro**: una parte del cuerpo más grande, o girada, durante toda
  la animación (lo que va unido a ella crece con ella).
- **Volver a la del juego** quita todos sus cambios.

## Captura de movimiento

Pon el movimiento de una persona real en una animación, bajo **Captura de movimiento**: elige un movimiento de la
biblioteca de movimientos (3.205 movimientos libres de la base de datos de captura de movimiento CMU y de 100STYLE,
cada uno descargado cuando lo eliges), o **Elegir un archivo de captura…** propio (.bvh, de Mixamo, Blender o cualquier
programa de captura de movimiento).

1. Elige la parte que usar: **Desde** (en segundos) y **Duración**. Para andar o correr, un paso entero con cada pie;
   para una muerte, empieza justo antes de la caída.
2. **Mantener en el sitio** mantiene los andares y las carreras en el punto donde el juego mueve la unidad; **Hacer que
   se repita** suaviza la última postura hacia la primera, para una animación que el juego pone una y otra vez.
3. **Crédito (quién hizo el movimiento):** ya relleno para los movimientos de la biblioteca; para cualquier otro
   archivo, escribe quién lo hizo y su licencia. Va a donde vaya tu mod.
4. **Ver**, y luego **Usar**. Los cambios de velocidad y de huesos se siguen aplicando encima; **Volver a la del
   juego** la quita.

## Los sonidos y animaciones de una unidad

La página de una unidad tiene una sección **Sonidos y animación**: sus propias frases y sonidos de motor, y sus
animaciones. **Cambiar sus sonidos en RUSE Decoy** abre RUSE Decoy en los de esa unidad. Una unidad dice las frases de
su nación y de su tipo, así que una frase cambiada allí se oye en todas las unidades que la comparten. Sus disparos e
impactos están en los tipos de armas y de impactos.

## El sonido de fondo de un mapa

En la pestaña **Mapas**, **Sonido de fondo…** muestra el del mapa: de cuál parte, y sus tres capas, cada una escuchada
y sustituida en el mismo editor. Un mapa también puede partir del fondo que suena en otro mapa.

## Lo que se ha visto en el juego

Visto en el juego: los sonidos y animaciones de RUSE Decoy (Studio 0.9.8.8), la canción del menú principal, las
canciones de las listas de batalla 1 y 2, canciones nuevas añadidas a ellas, y las frases de voz de una unidad. Aún sin
probar: el sonido de fondo de un mapa, y la lista de la música de los engaños (se sabe por cómo funciona el juego). Los
mensajes de error de RUSE Decoy solo están en inglés por ahora.

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Music-and-Sounds]]
