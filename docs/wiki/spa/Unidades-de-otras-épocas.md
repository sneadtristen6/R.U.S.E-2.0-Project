# Unidades de otras épocas

> **Para:** modders · **Necesitas:** RUSE Studio 0.9.8.2 o posterior y un mod · **Tiempo:** un minuto o dos por unidad

366 unidades desde la Primera Guerra Mundial hasta hoy están junto a las del propio juego en la pestaña **Unidades**:
tanques y aviones de la IGM, la IIGM+, la Guerra Fría y modernos, todos en un mismo juego. Cada una es un modelo 3D gratuito de otro autor (CC BY), ya ajustado al juego, con las
insignias de su nación y con su crédito. Ninguna está en tu mod hasta que la añades.

## Consigue las unidades de una época

1. En la pestaña **Unidades**, elige una época encima de los tipos: **IGM**, **IIGM+**, **Guerra Fría** o **Moderna**
   (**Vanilla** son las unidades del propio juego, la lista de siempre).
2. La primera vez, el Studio dice cuántas unidades tiene la época y cuánto ocupa, con **Descargar las unidades de IGM**
   (o las de esa época). Las descarga del GitHub del proyecto, comprueba cada archivo antes de usarlo y las lista.

   | Época | Unidades | Descarga |
   |---|---|---|
   | IGM | 61 | 232 MB |
   | IIGM+ | 32 | 198 MB |
   | Guerra Fría | 149 | 996 MB |
   | Moderna | 124 | 709 MB |

3. Una época descargada se actualiza sola cuando se suben unidades más nuevas: el Studio lo dice y las descarga.

Las unidades de la época se filtran como las del juego: tipo (terrestre o aérea), nación (China también), clase y el
cuadro de búsqueda.

## Añade una a tu mod

1. Haz clic en una unidad. Su página muestra la imagen de su modelo y su autor: **Modelo de** el autor, la licencia y
   un enlace a donde lo compartió.
2. Rellena el formulario:
   - **Nombre de la nueva unidad** (mostrado en todos los idiomas).
   - **Partir de**: la unidad del juego cuyos valores toma al empezar (velocidad, blindaje, armas, cómo juega). La
     sugerida va primero; se puede elegir cualquier unidad de su tipo.
   - **Precio** (en todas las fechas de batalla).
   - **Tamaño**: 1 es igual de larga que la unidad de partida. La sugerencia es su tamaño real (su anchura real, la
     envergadura de un avión, a la escala propia del juego); cualquier valor de 0.05 a 20. Arrastra el control
     deslizante, o haz clic en uno de sus puntos con nombre: **Diminuto**, **Tamaño del juego** (1: igual de larga que
     la unidad de partida, el tamaño con el que el juego dibuja ese tipo de unidad), **Tamaño real** y **Enorme**. Los
     aviones modernos a tamaño real son mucho más grandes que los aviones de la IIGM del juego (un J-16 es tan largo
     como un Lancaster).
   - **Menú de producción**: la nación y la fábrica en la que se compra.
   - **Investigada desde**: la unidad desde la que se investiga, o **Ninguna: comprable desde el principio**, con su
     **Precio de investigación** y su **Tiempo de investigación** (escribe el tiempo en segundos o en minutos: el
     selector de al lado).
3. Haz clic en **Añadir a mi mod**. Ahora es una unidad nueva de tu mod: **Abrir su página** para cambiar cualquiera de
   sus valores, su modelo o su tarjeta, como cualquier unidad. **Quitarla de mi mod** la borra otra vez.

## Cambia su tamaño más tarde

En la página de la unidad, **Su propio modelo** tiene el mismo control deslizante: elige un tamaño y haz clic en
**Cambiar tamaño** (el modelo se ajusta otra vez a partir de su propio archivo, sin nada que elegir). **Todos los
aviones de mi mod** (o unidades terrestres) los cambia todos a la vez: **Tamaño del juego**, **Tamaño real**, **Más
pequeños** (una quinta parte) o **Más grandes** (una cuarta parte). El juego lee el modelo de una unidad cuando carga,
así que un tamaño no puede cambiar mientras juegas: el nuevo tamaño se ve a partir de la siguiente construcción (Probar
en el juego).

## Cadenas de investigación

Una unidad se puede investigar desde cualquier unidad del menú de producción de su nación, también desde las unidades
de época de tu propio mod: añade un tanque de la Guerra Fría y luego uno moderno investigado desde él. Las unidades de
la IGM y la IIGM+ se pueden comprar desde el principio; las de la Guerra Fría y modernas empiezan investigadas desde
una unidad adecuada (el formulario dice cuál sugiere, y por qué).

Cuando quitas una unidad desde la que se investigan otras, **Ajustes > Investigación** decide qué pasa:

- **Avisarme antes** (lo predeterminado): el Studio lista las unidades investigadas desde ella, con **Quitarla de todos
  modos**.
- **Negarse**: la unidad se queda, y el mensaje dice cómo cambiar antes las demás.
- **Volver a enlazarlas**: cada una pasa a investigarse desde la propia unidad madre de la unidad quitada, con su propio
  precio y su propio tiempo (o pasa a poder comprarse desde el principio).

Una unidad que se queda investigada desde una que ya no está lo dice en su cuadro **Mejora e investigación** y en la
barra de comprobación, y la construcción se detiene en ella hasta que elijas otra unidad, o ninguna.

## Créditos

El autor de cada unidad de época tiene su crédito: en su página, y en el `CREDITS-era-units.md` de tu mod, que el Studio
escribe cuando añades una. Conserva ese archivo con tu mod: la licencia de los modelos lo pide. La lista completa de
autores está en la [versión de las unidades de época](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/tag/era-units).

## Lo que se ha visto en el juego

Visto: se cargan de inmediato, con sus propias tarjetas en los menús de producción; las pestañas de investigación y una
cadena de mejoras; sus propios modelos; sus tamaños. Aún sin probar: los cañones
remolcados (el importador aún no sabe ajustarlos, así que muestran el modelo de la unidad de partida), y si el juego
cuenta el tiempo de investigación en segundos.

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Units-From-Other-Eras]]
