# Abrir en Blender

> **Necesitas:** RUSE Studio 0.9.8.20 o posterior, un mod y Blender (gratis) · **Tiempo:** 5 minutos de lectura

**Abrir en Blender** lleva una unidad a Blender, el programa 3D gratuito, para cambiar su forma, sus huesos o su
pintura; **Traer mis cambios** pone en tu mod lo que hiciste allí. Es un solo botón para toda la unidad: **Qué va a
Blender**, al lado, dice qué se va, y todo lo que desmarques se queda como está. Esta página lo recorre paso a paso.

Las animaciones no se cambian con este botón: se cambian en RUSE Decoy (mira
[[Animaciones de las unidades|Animaciones-de-las-unidades]]). Las animaciones propias de un modelo van a Blender con él
y vuelven con él.

## Dónde está el botón

| La unidad | Dónde | Qué vuelve |
|---|---|---|
| Un pelotón que hiciste tú (una unidad nueva de tu mod) | El gran **Abrir en Blender** en su tarjeta, arriba en su página | Sus soldados, cada uno por su lado; su pintura |
| Cualquier otra unidad que hiciste (un tanque, un avión) | **Aspecto y movimientos**, la fila **Modelo**, **Más**: el recuadro **Cambiarlo en Blender** | Todo su modelo (también sus huesos, cuando son suyos), su pintura |
| Una unidad del juego (no un pelotón) | El mismo recuadro | Solo su pintura: pinta encima, el resto sigue siendo el del juego |
| Un pelotón del juego | Su tarjeta dice que hagas antes una unidad nueva a partir de él: **Nueva unidad a partir de esta…** | Solo su **Uniforme personalizado**, pintado desde su fila **Uniforme** (**Abrir en Blender**, luego **Traer**) |

¿No hay Blender en este PC? La página muestra **Conseguir Blender (gratis)**, que abre la página de descarga de Blender,
y **Elegir Blender…**, para mostrarle al Studio dónde está `blender.exe` si ya lo tienes.

## Qué va a Blender

Haz clic en **Qué va a Blender ▾** junto al botón. Al empezar está todo marcado. Desmarca una parte para dejarla como
está: **Traer mis cambios** la deja entonces como estaba, haga lo que haga Blender con ella.

| Ves | Significa |
|---|---|
| **Sus soldados**, y luego cada soldado («Fusilero 1», «Soldado con bazuca 5»...) | Los soldados marcados se abren uno al lado del otro en un solo Blender. Cambia el que quieras: solo cambia el que cambias. |
| **Qué modelo:** **El modelo de los fusileros** o **El modelo del soldado con arma pesada** | Un pelotón con huesos propios (el Pelotón a caballo genérico): un modelo cada vez, con sus huesos y sus animaciones. |
| **Su modelo** | La forma de la unidad (una unidad que no es un pelotón). |
| **Sus huesos** | Sus huesos (solo un modelo con huesos propios). Desmarcado, los huesos de tu mod se vuelven a poner como estaban. |
| **Su pintura** | Sus imágenes. Desmarcado, las imágenes de tu mod se vuelven a poner como estaban. |

Bueno saber:

- **Solo su pintura** (su modelo, o cada soldado, desmarcado): Blender se abre con las imágenes para pintar, y solo
  vuelve la pintura. Así se pinta el **Uniforme personalizado** de un pelotón, para todos los soldados a la vez. Un
  pelotón con el uniforme por defecto no puede: «Elige primero Uniforme propio» (el uniforme por defecto también lo
  llevan otros pelotones y dotaciones). Elige antes **Uniforme personalizado** en su fila **Uniforme**, en **Aspecto y
  movimientos**.
- **Sus huesos** desmarcado, pero en Blender se añadió, quitó o renombró un hueso: los huesos no se pueden conservar,
  así que vuelven como los envió Blender, y el Studio lo dice.
- Un pelotón de soldados del juego no tiene **Sus huesos**: sus soldados vuelven sobre los huesos del soldado del juego,
  haga lo que haga Blender con ellos.
- Nada marcado: el Studio dice «Marca primero lo que va a Blender: el modelo, sus huesos o su pintura.»

## Llevarlo y traerlo, paso a paso

1. **Ábrelo.** Haz clic en **Abrir en Blender**. Blender se abre (tarda unos segundos), con lo que marcaste.
2. **Cámbialo.** Pinta, cambia la forma, pon un modelo tuyo sobre los huesos de un soldado (mira
   [[Modelos y huesos|Modelos-y-huesos]], «Los pesos»). Las pocas cosas que hay que saber están escritas arriba en la
   vista 3D de Blender.
3. **Envíalo.** Haz clic en **Enviar a R.U.S.E. Studio** arriba a la izquierda en la vista 3D de Blender.
4. **Tráelo.** En el Studio, el botón dice ahora **Traer mis cambios**: haz clic. La página dice qué llegó: quién cambió
   y quién no en un pelotón, el archivo del modelo en cualquier otra unidad, y qué se conservó al estar desmarcado.
5. **Probar en el juego** lo muestra.

Puedes dejar Blender abierto y dar otra vuelta: cambiar, enviar, traer.

## Traer mis cambios

- **¿Blender sigue abierto?** **Traer mis cambios** le pide primero que envíe, y lo espera (hasta un minuto).
- **¿Vas a cerrar Blender?** Haz clic antes en **Enviar a R.U.S.E. Studio**: lo que no enviaste se queda en Blender, y
  el Studio nunca lo ve.
- **¿Lo cerraste después de enviar?** El botón dice **Traer mis cambios** hasta que haces clic, y toma lo último que
  enviaste. En la tarjeta de un pelotón, un envío hecho después de la última vez que trajiste (o después de **Añadir un
  soldado**) aparece como un pequeño **Traer mis cambios** bajo el botón grande, una vez cerrado Blender: toma lo último
  que enviaste.
- **Aún no se envió nada:** «Todavía no ha vuelto nada de Blender: en Blender, pulsa Enviar a R.U.S.E. Studio arriba y
  luego Traer mis cambios aquí.»
- Un solo Blender a la vez para una unidad: mientras Blender la tiene, el botón del Studio dice **Traer mis cambios**.

## Un envío guardado aparte

Un **envío** es lo que Blender mandó con **Enviar a R.U.S.E. Studio**. Si vuelves a abrir Blender antes de traer el
último envío:

- **Un pelotón:** ese envío se guarda aparte en la carpeta de Blender de tu mod, en una carpeta llamada
  `sent-not-brought-` seguida de la fecha y la hora, y el nuevo Blender empieza con lo que tiene tu mod. No se pierde
  nada, pero la tarjeta aún no lo dice, y no tiene un botón para traerlo: los archivos están en
  `Documents\RUSE 2.0\Mods\<tu mod>\blender\<nombre de la unidad>\squad\`.
- **Cualquier otra unidad, con su modelo marcado:** no se guarda nada aparte: el siguiente **Abrir en Blender** empieza
  con lo último que enviaste.
- **Las animaciones de RUSE Decoy:** cada envío guardado aparte aparece encima de las animaciones de la unidad
  («Enviado desde Blender, nunca traído, guardado aparte el ...»), con **Traer el envío guardado aparte** para tomarlo, o
  **Llevarlo a la Papelera de reciclaje**.

## Dónde están tus archivos de Blender

En la carpeta de tu mod, `Documents\RUSE 2.0\Mods\<tu mod>\blender\<nombre de la unidad>\`: los del pelotón en `squad`,
los de RUSE Decoy en `animations`. No se meten en tu mod cuando lo exportas. En la página de un pelotón, **Más
opciones** dice dónde están, con **Mostrar en la carpeta**.

## Qué puede salir mal

| Qué pasa | Por qué, y qué hacer |
|---|---|
| Blender se abre vacío | Busca un error en la ventana de Blender (**Window > Toggle System Console**), y cuéntanoslo en el Discord. |
| Un soldado que no toqué aparece como cambiado | Todo lo que difiere cuenta como cambiado, también un objeto renombrado. Su aspecto se queda como estaba. |
| «No está en ningún soldado, así que no se envió: ...» | Algo que trajiste a Blender no está ni sobre los huesos de un soldado ni en su colección: ponlo sobre él y vuelve a enviar. |
| Un punto de mi modelo solo se mueve con la cadera | No tiene hueso: mira [[Modelos y huesos|Modelos-y-huesos]], «Puntos sin hueso». |
| Algunas piezas perdieron su brillo o su color de bando | La página las nombra: un material renombrado o nuevo en Blender vuelve sencillo. Conserva los nombres de material con los que se abrió Blender. |
| La forma nueva de mi unidad del juego no volvió | En una unidad del juego solo vuelve la pintura. Haz una unidad nueva a partir de ella para cambiar su forma. |

## Qué se ha probado en el juego

- La pintura desde Blender en una unidad, vista de cerca y de lejos.
- Un pelotón abierto en Blender, un soldado cambiado y traído él solo (noviembre de 2026).
- Aún no probado en el juego: todo el modelo de un tanque pasado por Blender, y lo que **Qué va a Blender** conserva
  (probado con Blender y el Studio, fuera del juego).

¿Sigues atascado? Pregunta en el [Discord](https://discord.gg/h54t5baNsC), o mira
[[Cuando algo sale mal|Cuando-algo-sale-mal]].

**Siguiente:** [[Cambiar un pelotón|Cambiar-un-pelotón]] · [[Modelos y huesos|Modelos-y-huesos]] ·
[[Animaciones de las unidades|Animaciones-de-las-unidades]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Open-in-Blender]]
