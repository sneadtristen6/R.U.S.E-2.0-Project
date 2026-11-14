# Modelos y huesos

> **Necesitas:** RUSE Studio 0.9.8.20 o posterior, un mod con una unidad nueva y Blender (gratis) para cambiar huesos ·
> **Tiempo:** 10 minutos de lectura

Los soldados, los caballos y cualquier criatura se mueven en R.U.S.E. porque su modelo 3D tiene **huesos**. Esta página
explica qué son los huesos, cómo los usa el juego y qué significa cada recuadro sobre huesos en la página de una unidad,
y qué hacer con él. Un tanque gira su torreta y sus ruedas sin animaciones, así que esta página trata sobre todo de
soldados, caballos y criaturas.

## Qué son los huesos

- Un **modelo** es una carcasa hecha de puntos, con imágenes pintadas encima.
- Dentro, como un esqueleto, hay **huesos**: un brazo, un antebrazo, una mano, la cabeza, cada pata de un caballo. Cada
  hueso cuelga de otro (la mano del antebrazo, el antebrazo del brazo), hasta el primer hueso.
- Cada punto de la carcasa sigue a un hueso, o a varios: los puntos de una manga siguen al brazo. Cuánto sigue un punto
  a cada hueso es su **peso**.
- Una **animación** mueve los huesos, fotograma a fotograma, y la carcasa los sigue. Así camina, apunta y cae un
  soldado.
- En Blender, los huesos de un modelo son un solo objeto, llamado **armature**.

## Cómo los usa el juego

- El juego mueve los huesos de un modelo **según su puesto en su lista de huesos**, no según sus nombres. Así que una
  animación hecha para un modelo solo sirve para un modelo con los mismos huesos, en el mismo orden.
- Algunos huesos tienen una tarea: un disparo sale de un hueso en la boca del arma, la parte de arriba del cuerpo gira
  hacia su objetivo en un hueso de la columna, un arma se muestra y se oculta en un hueso, una torreta o una rueda gira
  sobre uno. La página de la unidad nombra cada uno que le falta a tu modelo (mira **¿Funcionará en el juego?** más
  abajo).
- Un soldado reproduce **dos animaciones a la vez**: una en la mitad superior de su cuerpo (apuntar, disparar) y otra en
  la inferior (andar, correr). Un caballo y su jinete también: mira **Sus dos mitades** más abajo.
- No se ha visto al juego animar un modelo con más de 64 huesos.

## Dos tipos de modelo

| | Sobre los huesos del soldado del juego | Con huesos propios |
|---|---|---|
| **Qué es** | Un soldado cambiado en Blender, o un modelo tuyo puesto sobre los huesos de un soldado | Un caballo, un caballo con su jinete, cualquier criatura, hecho en Blender sobre huesos tuyos |
| **Cómo se hace** | **Abrir en Blender** en la tarjeta del pelotón: cada soldado se abre con sus huesos (mira [[Abrir en Blender|Abrir-en-Blender]]) | En Blender, y luego **Importar un modelo…** en la tarjeta del pelotón (mira [[Importar un modelo|Importar-un-modelo]]) |
| **Sus animaciones** | Las del juego, como el soldado | Las suyas, de su archivo |
| **Sus dos mitades** | Las del juego: no hay nada que elegir | Las eliges tú (el Studio sugiere el hueso) |
| **Su tamaño y su sitio** | Como lo hiciste en Blender, sobre sus huesos | Como en su archivo |

La página dice cuál es. En un modelo sobre los huesos del soldado del juego: «Tu modelo está sobre los huesos del
soldado del juego, así que conserva las dos mitades del juego: no hay nada que elegir.» En un modelo con huesos propios:
«Tiene huesos propios:» y cuántos. El **Pelotón a caballo genérico** (pestaña **Unidades**, **IIGM+**) es un pelotón
con huesos propios: mira [[Unidades de otras épocas|Unidades-de-otras-épocas]].

## Dónde los muestra la página

En la página de una unidad nueva, todo lo de los huesos está en **Aspecto y movimientos**:

| Recuadro | Dónde | Qué te dice |
|---|---|---|
| **Sus huesos y animaciones** | La fila **Sonidos y animación**, **Más** | Cuántos huesos tiene el modelo, y cada animación con su duración y cuántas acciones de la unidad la usan (un modelo con huesos propios) |
| **Sus dos mitades** | La fila **Sonidos y animación**, **Más** | Dónde se divide el modelo en su mitad superior y su mitad inferior |
| **Sus animaciones** | La fila **Sonidos y animación**, **Más** | Qué animación usa la unidad para cada cosa que hace: mira [[Animaciones de las unidades|Animaciones-de-las-unidades]] |
| **¿Funcionará en el juego?** | La fila **Modelo**, **Más**; en la página de un pelotón, **Más opciones** bajo los soldados y luego **El modelo de cada soldado** | Lo que en el modelo podría detener el juego o verse mal, y cómo arreglarlo |
| Puntos sin hueso | En el mismo sitio que **¿Funcionará en el juego?** | Cuántos puntos del modelo no siguen a ningún hueso |

## Sus dos mitades

El juego reproduce dos animaciones a la vez en un soldado: una en su **mitad superior** (apuntar, disparar) y otra en su
**mitad inferior** (andar, correr). Un jinete apunta y dispara mientras su caballo corre: el jinete es la mitad superior,
el caballo la inferior.

- Un modelo sobre los huesos del soldado del juego conserva las mitades del juego: la página dice «no hay nada que
  elegir».
- Un modelo con huesos propios se divide en **un hueso**: ese hueso y todos los que están debajo forman la mitad
  superior, todos los demás la inferior.

Para elegirlo:

1. En la página de la unidad, en **Aspecto y movimientos**, haz clic en **Más** en la fila **Sonidos y animación**.
2. Bajo **Sus dos mitades**, la lista **La mitad superior empieza en** muestra primero la sugerencia del Studio, marcada
   «(sugerido)». El Studio sugiere el primer hueso del jinete en un caballo con jinete (**bip01** en el Pelotón a
   caballo genérico), si no el primer hueso llamado spine (como un soldado), si no el hueso donde el esqueleto se
   ramifica por primera vez.
3. A la mayoría de los modelos les va bien la sugerencia: déjala. Para cambiarla, elige otro hueso de la lista. Se
   guarda al momento, y se ve en el juego tras la próxima compilación (**Probar en el juego**).
4. Bajo la lista, la página cuenta los huesos de cada mitad, y **Qué hueso va dónde** lista cada hueso del modelo,
   marcado mitad superior o mitad inferior.
5. Para volver a la sugerencia, elige otra vez la primera línea de la lista.

Una división distinta de la sugerida aún no se ha probado en el juego.

## Los pesos: a qué hueso sigue cada punto

Cuando pones un modelo tuyo (o un casco, una mochila, un arma) sobre los huesos de un soldado, Blender tiene que saber
a qué hueso sigue cada uno de sus puntos. Estos son los pasos del propio Blender.

**Tu modelo sobre un soldado, cada punto siguiendo a los huesos más cercanos:**

1. En la tarjeta del pelotón, haz clic en **Abrir en Blender**: Blender se abre con los soldados, cada uno sobre sus
   huesos.
2. En Blender, trae tu modelo con **File > Import** y colócalo sobre el soldado.
3. Haz clic en tu modelo y luego **Mayús+clic** en los huesos del soldado: los huesos al final.
4. Pulsa **Ctrl+P** y elige **With Automatic Weights**. Blender calcula los pesos por ti.
5. Borra lo que no conserves (la forma del soldado del juego, si tu modelo ocupa su lugar), pero conserva sus huesos.
6. Haz clic en **Enviar a R.U.S.E. Studio** arriba en la vista 3D de Blender, y luego en **Traer mis cambios** en el
   Studio.

**Una pieza rígida que sigue a un solo hueso (un casco en la cabeza):**

1. En Blender, haz clic en el casco y luego **Mayús+clic** en los huesos del soldado.
2. Pulsa **Ctrl+Tab** para el Pose Mode y haz clic en el hueso de la cabeza.
3. Pulsa **Ctrl+P** y elige **Bone**. El casco se mueve ahora con la cabeza, y solo él lo recibe cuando traes tus
   cambios.

**Puntos sin hueso.** Los pesos automáticos de Blender a veces se dejan algunos puntos. La página dice entonces «{n}
punto(s) de tu modelo no tienen hueso, así que solo se mueven con la cadera del soldado.» Para arreglarlo:

1. **Abrir en Blender** otra vez.
2. Haz clic en tu modelo y cambia el modo de Blender (arriba a la izquierda de la vista 3D) de **Object Mode** a **Weight
   Paint**.
3. En las propiedades del modelo (el triángulo verde), **Vertex Groups** tiene un grupo por hueso: elige el hueso que
   deben seguir esos puntos.
4. Pinta sobre los puntos.
5. **Enviar a R.U.S.E. Studio**, y luego **Traer mis cambios**.

## ¿Funcionará en el juego?

El Studio comprueba un modelo sobre huesos frente a las animaciones que reproduce y frente a las piezas y disparos de la
unidad que copia. Compilar el mod lo comprueba otra vez, con todos tus cambios. Un problema nunca te bloquea: dice qué
pasará y cómo arreglarlo.

**Dónde:** en la página de una unidad nueva, **Aspecto y movimientos**, la fila **Modelo**, **Más**. En la página de un
pelotón: **Más opciones**, bajo los soldados, y luego **El modelo de cada soldado**.

Cuando todo va bien, dice: «No se encontró nada que detenga el juego: cada animación que reproduce tiene sus huesos, y
está cada hueso que necesitan sus piezas y disparos.» (con el número de huesos).

### Qué significa cada respuesta

Cada problema dice tres cosas: qué no encaja, qué hace el juego con ello y cómo arreglarlo. La línea del medio es una de
estas:

| La página dice | Qué significa | Qué hacer |
|---|---|---|
| Esto puede detener el juego: ocurrió en una prueba. | El juego se detuvo así en una de nuestras pruebas. | Arréglalo antes de probar. |
| Esto puede detener el juego (aún no probado en el juego). | Se espera que el juego se detenga. | Arréglalo antes de probar. |
| El juego la reproduce, pero se verá mal (aún no probado en el juego). | Se moverían los huesos equivocados. | Arréglalo, o pruébalo y mira. |
| La unidad sigue combatiendo, pero sus disparos no se verán: ocurrió en una prueba. | Hace daño, pero no se ve ningún disparo. | Añade el hueso que nombra la página. |
| Aún no probado en el juego: puede que el juego no lo anime. | Más huesos de los que se ha visto animar al juego. | Une o borra huesos. |
| Sigue funcionando, pero quizá no sea lo que quieres. | Una nota sobre sus dos mitades. | Revisa **Sus dos mitades**. |

### Cada problema y su arreglo

**Animaciones que no encajan con los huesos del modelo.** La página dice cuántas animaciones, para cuántas acciones, y
por qué no encajan: «Mueven {a} huesos y tu modelo tiene {b}.» (o «solo tiene {b}»), o tantos huesos pero «con otros
nombres», o «en otro orden». Esas animaciones se hicieron para otros huesos.

- Si la unidad reproduce las animaciones del juego en tu modelo: da a esas acciones animaciones propias de tu modelo.
  **Importar modelo…** trae cada animación del archivo de tu modelo, y eliges cuál usa cada acción en **Sus
  animaciones** ([[Animaciones de las unidades|Animaciones-de-las-unidades]]).
- Si son las animaciones de tu modelo, hechas para otro modelo: rehazlas en Blender sobre los huesos de este modelo y
  vuelve a importar el modelo.

**Un hueso que necesita la unidad.** Por ejemplo: «Fusileros: los disparos salen de un hueso llamado Fx_Tir_01, y tu
modelo no lo tiene.» (o: la parte de arriba del cuerpo gira ahí hacia el objetivo, un arma se muestra y se oculta ahí,
una pieza se sostiene ahí, una torreta o una rueda gira ahí, el cuerpo se apoya ahí, un cañón remolcado se engancha
ahí). Para añadir el hueso en Blender:

1. Abre el modelo en Blender: **Abrir en Blender** con **Sus huesos** marcado (mira
   [[Abrir en Blender|Abrir-en-Blender]]), o tu propio archivo de Blender.
2. Haz clic en los huesos (la armature) y pulsa **Tab** para el Edit Mode.
3. Pulsa **Mayús+A**: aparece un hueso nuevo donde está el cursor 3D de Blender.
4. Pulsa **F2** y escribe exactamente el nombre que dice la página (por ejemplo `Fx_Tir_01`). Si tu modelo tiene ese
   hueso con otro nombre, cambia mejor el nombre de ese.
5. En las propiedades del hueso (el icono del hueso), en **Relations**, pon en **Parent** el hueso con el que se mueve
   la pieza: para un disparo, el hueso con el que se mueve el arma.
6. Pulsa **G** y lleva el hueso nuevo a donde va la pieza: para un disparo, al final del cañón del arma.
7. Pulsa **Tab** otra vez, haz clic en **Enviar a R.U.S.E. Studio** y luego en **Traer mis cambios** (o exporta tu propio
   archivo y haz clic en **Importar otro…**). **¿Funcionará en el juego?** vuelve a comprobar el modelo.

**Demasiados huesos.** «Tu modelo tiene {n} huesos. No se ha visto al juego animar un modelo con más de 64.» En Blender,
une o borra huesos hasta que tenga 64 o menos, y vuelve a traer el modelo.

**La división.** «La división en {bone}, el primer hueso de tu modelo, pone todos los huesos en la mitad superior, así
que las animaciones de la mitad inferior (andar, correr) no mueven nada.»: elige un hueso más abajo en **Sus dos
mitades**, donde empieza la parte de arriba del cuerpo. «El hueso que elegiste para la división, {bone}, ya no está en tu
modelo, así que se divide en {used}.»: vuelve a elegir el hueso.

**El segundo modelo de un pelotón sobre otros huesos.** «Su modelo tiene huesos propios que no son los del modelo de tus
fusileros: hace entonces lo que hacía en la unidad copiada, hecho sobre los huesos del soldado del juego, y eso puede
detener el juego.» El modelo de un soldado con arma pesada tiene que estar sobre los mismos huesos que el de los
fusileros para usar sus animaciones: haz el suyo a partir del modelo de los fusileros en Blender, y luego impórtalo en
su línea. Quitar el modelo de los fusileros quita también el suyo.

## Hacer un modelo con huesos propios en Blender

1. **Sus huesos:** tu modelo sobre una armature con huesos tuyos, con los nombres que quieras, y sus pesos
   (**Ctrl+P > With Automatic Weights**, arriba).
2. **Sus animaciones:** una action por animación (en Blender, **Dope Sheet > Action Editor**). Nombra cada una por lo
   que muestra: al menos **stand** (o **idle**), **walk** y **run** (o **gallop**); **fire**, **aim**, **reload**,
   **hit**, **death**, **crouch**, **look**, **flee** y **grenade** también se conocen. Un nombre como **t_fire** (o
   **hr_t_fire**) solo se reproduce en la mitad superior, y **b_run** (o **hr_b_run**) solo en la inferior: los de un
   jinete y su caballo.
3. **Expórtalo:** **File > Export > glTF 2.0**, formato **glTF Binary (.glb)**, con **Animation** marcado.
4. **Impórtalo** en un pelotón nuevo: mira [[Importar un modelo|Importar-un-modelo]].
5. **Revisa su página:** **Sus huesos y animaciones** (llegó cada animación, y cuántas acciones usan cada una), **Sus dos
   mitades**, **Sus animaciones**, **¿Funcionará en el juego?**
6. **Probar en el juego.**

¿Lo cambiaste después en Blender? Vuelve a importarlo: cada acción conserva su animación mientras una animación con ese
nombre siga en el archivo.

## Qué se ha probado en el juego

- El Pelotón a caballo genérico, hecho así (fusileros y un soldado con bazuca a caballo, un modelo con huesos propios):
  disparan, viajan como ellos mismos en los trayectos largos, y cada caballo cae con su jinete (noviembre de 2026).
- Un soldado de un pelotón cambiado en Blender sobre los huesos del soldado del juego, con puntos pesados allí
  (noviembre de 2026).
- Aún no probado en el juego: una división distinta de la sugerida, y cada problema que la página marca «aún no probado
  en el juego».

¿Sigues atascado? Pregunta en el [Discord](https://discord.gg/h54t5baNsC), o mira
[[Cuando algo sale mal|Cuando-algo-sale-mal]].

**Siguiente:** [[Animaciones de las unidades|Animaciones-de-las-unidades]] · [[Abrir en Blender|Abrir-en-Blender]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Models-and-Bones]]
