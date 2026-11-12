# Cambiar un pelotón

> **Para:** modders · **Necesitas:** RUSE Studio, un mod y Blender (gratis) para cambiar soldados en Blender ·
> **Tiempo:** unos minutos

Haz que los GI estadounidenses parezcan marines, o dale a un solo soldado un aspecto propio. La página de un pelotón
empieza por sus soldados: la tarjeta de pelotón arriba y luego una línea para cada soldado.

## 1. Tu propio pelotón

En la pestaña **Unidades**, elige un pelotón (el pelotón de fusileros de EE. UU., por ejemplo). Su tarjeta dice de qué
está hecho: «5 soldados: 4 fusileros con fusiles, 1 soldado del bazuca con un bazuca». Los pelotones del juego no se
cambian: pulsa **Nueva unidad a partir de esta…** en la tarjeta, dale un nombre a tu pelotón y pulsa **Crear**. Su
página se abre en su tarjeta.

## 2. Todo el pelotón en Blender

1. Pulsa **Cambiar el pelotón en Blender** en la tarjeta. Blender se abre con todos los soldados del pelotón uno al lado
   del otro. ¿Todavía no tienes Blender? **Conseguir Blender (gratis)** lo instala; **Elegir Blender…** le muestra al
   Studio dónde está.
2. Cambia el soldado que quieras: su forma, sus colores, su equipo. Cada soldado tiene su propia copia de sus imágenes:
   pintar uno solo lo cambia a él.
3. Tu propio casco, mochila o bazuca en un solo soldado: tráelo con **File > Import**, pónselo, haz clic en él,
   **Mayús+clic** en sus huesos y luego **Ctrl+P > With Automatic Weights**.
4. Pulsa **Enviar a R.U.S.E. Studio** arriba en Blender.
5. De vuelta en el Studio, el botón grande ahora dice **Traer mis cambios**: púlsalo. Cada soldado recibe solo lo que se
   le hizo a él, y la tarjeta dice quién cambió y quién no.
6. Pulsa **Probar en el juego** para verlos.

El juego da a los cuatro fusileros del pelotón de fusileros de EE. UU. un solo modelo: en Blender son una sola figura, y
lo que le hagas lo llevan los cuatro. El soldado del bazuca es una figura propia.

## 3. Un soldado desde un archivo de modelo

Bajo **Cada soldado**, cada soldado tiene una línea: su imagen, su nombre y cuántos hay («Fusilero ×4»), y con qué
dispara.

- **Importar un modelo…** le da un modelo desde un archivo hecho en Blender sobre los huesos del soldado del juego, o un
  modelo con huesos propios (un caballo con jinete). Los demás conservan el suyo.
- **Volver al aspecto del juego** vuelve a quitar su modelo de tu mod.

## Bueno saber

- **Más opciones**, debajo de los soldados, dice dónde guarda tu mod el modelo de cada soldado y tus archivos de Blender;
  **Mostrar en la carpeta** abre la carpeta.
- ¿Cerraste Blender antes de traer tus cambios? El pequeño **Traer mis cambios** bajo el botón grande toma lo último que
  enviaste.
- El uniforme del pelotón está en **Aspecto y movimientos**, junto a los valores: **Uniforme personalizado** le da al
  pelotón un uniforme propio, que **Repintar en Blender** pinta para todos los soldados a la vez. Un pelotón lleva o tus
  modelos o un uniforme.
- Todavía no probado en el juego: todo el pelotón en un solo Blender, cada soldado traído por separado. Añadir y quitar
  soldados aún no está en el Studio.

Más sobre modelos, huesos y animaciones: [[Importar un modelo|Importar-un-modelo]].

**Siguiente:** [[Exportar y compartir|Exportar-y-compartir]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Change-a-Squad]]
