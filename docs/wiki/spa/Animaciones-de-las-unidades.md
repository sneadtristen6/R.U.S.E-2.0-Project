# Animaciones de las unidades

> **Necesitas:** RUSE Studio 0.9.8.20 o posterior y un mod; Blender (gratis) para cambiar en Blender las animaciones de
> una unidad nueva · **Tiempo:** 10 minutos de lectura

La forma en que se mueve una unidad (estar de pie, andar, correr, apuntar, disparar, morir) son sus **animaciones**. Esta
página explica para qué sirven las animaciones del juego, cuál usa una unidad para cada cosa que hace, cada manera de
cambiar una (para una unidad, para todas, para las unidades que elijas, o en Blender) y cómo recuperar la del juego.

## Qué es una animación

- Una animación mueve los huesos de un modelo en el tiempo: un paso de carrera, un fusil llevado al hombro, una caída
  (mira [[Modelos y huesos|Modelos-y-huesos]]).
- Cada cosa que hace una unidad en el juego (una **acción**: se queda quieta, camina, corre, dispara...) reproduce una
  animación. Un soldado reproduce dos a la vez, una para cada mitad de su cuerpo.
- Muchas unidades comparten las animaciones del juego: todos los fusileros estadounidenses corren igual. Así que un
  cambio en una animación es, si no eliges otra cosa, un cambio para todas las unidades que la usan.
- Los tanques giran su torreta y sus ruedas sin animaciones: aquí no hay nada que cambiar para ellos.

## Las animaciones del juego y para qué sirve cada una

**RUSE Decoy** (su pestaña arriba en el Studio) lista cada animación del juego a la izquierda, bajo **Animaciones**, por
tipo:

| Tipo | Qué contiene |
|---|---|
| **Infantería** | Fusileros, bazucas, paracaidistas y conductores: de pie, andar, correr, apuntar, disparar, recargar, huir, heridos y muerte (la parte de arriba y la de abajo del cuerpo tienen las suyas) |
| **Dotaciones de cañón** | Los hombres junto a un cañón: en reposo, moviéndolo, preparándolo, disparando y recargando |
| **Vehículos y cañones** | Cañones al emplazarse y al moverse, en reposo y disparando, y otras piezas móviles |
| **Figuras del cuartel general** | Los oficiales en la mesa del cuartel general en las escenas de una misión (no los usa ninguna unidad) |
| **Animales y escenario** | Vacas, caballos, cabras, gallinas, gaviotas y molinos de los mapas |

Cada una dice cómo la llama el juego y cuántas unidades la usan. En la página de una unidad, las acciones se llaman por
lo que hace la unidad, agrupadas así:

| Grupo | Sus acciones (algunas) |
|---|---|
| Quieto | Se queda quieto, Se agacha, Mira alrededor |
| En movimiento | Camina, Camina hacia atrás, Corre, Corre a la derecha, Corre hacia atrás, Huye |
| Apuntar y disparar | Apunta de pie, Apunta caminando, Dispara, Lanza una granada, Recarga |
| El arma pesada | Apunta con el arma pesada, Dispara el arma pesada, Levanta el arma pesada, Baja el arma pesada |
| Recibir impactos | Recibe un impacto, Recibe un impacto por detrás, Recibe una explosión |
| Morir | Muere de un disparo, Muere en una explosión, Yace caído |
| Salto en paracaídas | Salta, Cae, Desciende con el paracaídas, Aterriza |
| Acciones de una dotación | Espera, Avanza con la pieza, Va a la pieza, Emplaza la pieza, Dispara (un servidor), Recarga la pieza |

## Sus animaciones: cuál usa cada acción

Una unidad con animaciones propias (un modelo con huesos propios: un caballo, un caballo con su jinete, cualquier
criatura) tiene una tabla en su página: **Aspecto y movimientos**, la fila **Sonidos y animación**, **Más**, y luego
**Sus animaciones**.

- **Se queda quieto**, **Camina** y **Corre** van primero: lo mínimo que necesita un modelo. Si una no tiene nada
  propio, la página lo dice, y qué usa en su lugar.
- Cada acción tiene una lista de las animaciones del modelo. Elige una, o déjala en la primera línea, **La más
  cercana**: entonces usa la más cercana que tenga el modelo, y la línea dice cuál. La más cercana significa, en este
  orden: una animación con el nombre de esa acción (stand o idle, walk, run o gallop, fire, death...), y si no, lo que
  usa la acción más cercana (andar usa la carrera, disparar el apuntar o el estar de pie). El juego hace lo que dice la
  página: la compilación sigue la misma regla.
- **Todas las demás acciones** lista el resto, por grupos.
- **En los trayectos largos** es su última línea. En un trayecto largo por carretera, el juego mete a un pelotón en su
  camión. Una unidad con animaciones propias puede ir como ella misma, reproduciendo una de ellas en bucle (su carrera,
  si se deja la primera línea), a la velocidad de su camión. Elige **En su camión** para conservar el camión.

Una unidad copiada de otra con animaciones propias usa las mismas.

## Cambiar una animación en RUSE Decoy

1. En la página de la unidad, en **Aspecto y movimientos**, haz clic en **Cambiar en RUSE Decoy** en la fila **Sonidos y
   animación**. RUSE Decoy se abre con esa unidad: sus sonidos, y luego **Sus animaciones** con cada animación que usa.
   (O abre la pestaña **RUSE Decoy** y elige un tipo bajo **Animaciones**.)
2. Haz clic en **Ver y cambiar…** en una animación. Se reproduce en 3D sobre una unidad que la usa: arrastra para
   girarla, la rueda hace zoom. La vista 3D necesita internet una vez.
3. Abierta desde la página de una unidad, la primera línea pregunta **Cambiar para**:
   - **Solo esta unidad**: esta unidad usa su propia copia de la animación, con tus cambios; todas las demás la usan
     como antes. Es la opción de partida, salvo que la animación ya esté cambiada para todas las unidades.
   - **Todas las unidades que la usan**: el cambio va a la animación misma, para todas las unidades que la usan (el
     número dice cuántas).
   - **Tu copia** y su nombre: aparece cuando esta unidad usa una copia tuya (más abajo); entonces es la opción de
     partida.
4. Cámbiala:
   - **Velocidad**: 100 % es la del juego, 200 % el doble de rápido, 50 % la mitad. Se guarda al soltar.
   - **Usar en su lugar**: otra animación del mismo cuerpo en su lugar (los fusileros podrían correr como cuando huyen).
   - **Un hueso**, con **Tamaño**, **Girar sobre** y **Giro**: una parte del cuerpo más grande, o girada, durante toda la
     animación.
   - **Captura de movimiento**: el movimiento de una persona real en su lugar (mira [[Música y sonidos|Música-y-sonidos]]).
5. Haz clic en **Listo**. Cada cambio se guarda al momento en tu mod, y va al juego cuando lo pruebas o lo exportas.

## Una copia de una animación, para las unidades que elijas

**Copiar esta animación…** hace una copia que solo usan las unidades y los soldados que marques: una carrera tuya para
tres de tus pelotones, por ejemplo, y solo para el soldado con bazuca de un cuarto.

1. En la ventana de la animación, haz clic en **Copiar esta animación…**, ponle un nombre a la copia (solo lo ves tú) y
   haz clic en **Hacer la copia**. Empieza como está ahora la animación, y se abre en la misma ventana.
2. Cámbiala como arriba.
3. En **Quién la usa**, marca las unidades que usan la copia: primero **Tus unidades**, luego **Las unidades del
   juego**. Bajo una unidad en la que varios soldados o piezas la usan, marca solo algunos. **Buscar una unidad** busca
   por nombre o país.
4. Nada usa una copia hasta que marcas una unidad: la línea bajo su nombre dice «ninguna unidad la usa aún» hasta
   entonces.

Cada copia está a la izquierda de RUSE Decoy en **Tus copias**: ábrela ahí, o **Borrar la copia**. La copia propia de
una unidad (**Solo esta unidad**) o una animación cambiada en Blender tiene prioridad sobre una copia para esa unidad: la
lista lo dice al lado.

## Cambiar en Blender las animaciones de una unidad nueva

Para una unidad nueva hecha en tu mod (una unidad del juego necesita antes una unidad nueva hecha a partir de ella):

1. En la página de la unidad, haz clic en **Cambiar en RUSE Decoy**. Encima de sus animaciones, haz clic en **Cambiar sus
   animaciones en Blender**. Blender se abre con la unidad y cada animación que usa, cada una con el nombre de lo que
   hace en ella, seguido del nombre que le da el juego.
2. Abajo en Blender, el Action Editor las lista: elige una. **Espacio** la reproduce.
3. Haz clic en un hueso, pulsa **Ctrl+Tab** para el Pose Mode, **R** para girarlo (**G** lo mueve), y luego **I** para
   guardar la pose en este fotograma. Hazlo en cada fotograma que cambies: Blender va solo de una pose guardada a la
   siguiente.
4. Haz clic en **Enviar a R.U.S.E. Studio** arriba en la vista 3D de Blender: se va cada animación, cambiada o no.
5. En RUSE Decoy, haz clic en **Traer mis cambios**. Dice cuáles volvieron cambiadas: ahora son propias de esta unidad.
   Todas las demás unidades, y cada animación que no tocaste, quedan como antes.

Solo pon en pose los huesos: no les cambies el nombre, no los borres ni los muevas en Edit Mode. Si no, el Studio no
toma nada, y dice qué huesos.

Un modelo con huesos propios (un caballo, cualquier criatura) envía sus propias animaciones, con sus propios nombres. La
que cambies ocupa su lugar: cada acción que la usaba la usa cambiada.

## Recuperar la animación del juego

| Para quitar | Haz clic en | Dónde |
|---|---|---|
| Un cambio para todas las unidades | **Volver a la del juego** | La línea de la animación en RUSE Decoy, o su ventana |
| La copia propia de esta unidad (**Solo esta unidad**) | **Volver a la de todas las unidades** | La línea de la animación en la lista de la unidad, o su ventana |
| Los cambios de una copia (su nombre y sus marcas se quedan) | **Volver a la animación del juego** | La ventana de la copia |
| Una copia, entera | **Borrar la copia** | **Tus copias** |
| Un cambio hecho en Blender | Deshazlo en Blender mientras ese Blender siga abierto, y luego **Traer mis cambios**: también se deshace en tu mod | Blender, luego RUSE Decoy |

Los botones de arriba no quitan un cambio hecho en Blender.

## Qué puede decirte Traer mis cambios

| Dice | Qué hacer |
|---|---|
| «Cambiadas en Blender, ahora propias de esta unidad: ...» | Nada: funcionó. **Probar en el juego** lo muestra. |
| «Cada animación volvió tal como salió.» | No se cambió nada. ¿Guardaste cada pose con **I**? |
| «Hechas en Blender, aún no las usa ninguna acción: ...» | Una animación nueva no se toma. Guárdala en Blender (**File > Save**) para conservarla. |
| «No se enviaron de vuelta (borradas o renombradas en Blender), así que se reproducen como antes: ...» | Devuélvele su nombre en Blender si quieres tu cambio dentro. |
| «Estas se reproducen solo en una mitad del cuerpo ... así que puede que no se vean en el juego» | Los huesos que moviste están en la otra mitad: mueve los de la mitad que la reproduce. |
| «Huesos hechos en Blender que el esqueleto de esta unidad no tiene ...» | Un hueso nuevo no se puede reproducir; el resto llegó. |
| «El editor NLA de Blender reproduce estas con un ritmo propio ...» | El juego las reproduce como las muestra el Action Editor. |
| «La escena de Blender iba a ... fotogramas por segundo y el juego va a 30 ...» | Pon Blender a 30 fotogramas por segundo para ver la velocidad del juego. |
| «La escena de Blender tiene el Time Stretching activado ...» | Pon Old y New en el mismo número para ver la velocidad del juego. |
| «Ninguna acción de esta unidad reproduce estas ...» | Elígela para una acción en **Sus animaciones**, en la página de la unidad. |
| «Cambiadas en el Studio desde que salieron hacia Blender, y devueltas por Blender sin cambios, así que se queda el cambio del Studio ...» | Nada: tu cambio en RUSE Decoy se queda. |
| «Cambiadas también en el Studio desde que salieron hacia Blender: el cambio de Blender ocupa el lugar del cambio del Studio ...» | Nada, si quieres el cambio de Blender; si no, vuelve a hacer tu cambio en RUSE Decoy. |
| «No ha llegado nada nuevo de Blender desde la última vez que trajiste tus cambios.» | Haz clic antes en **Enviar a R.U.S.E. Studio** en Blender. |

## Qué puede salir mal

- **No cambia nada en el juego:** un cambio para **Solo esta unidad** se ve solo en esa unidad, y una copia solo en las
  unidades marcadas para ella. Un cambio hecho en Blender tiene prioridad, para esa unidad, sobre un cambio posterior a la
  misma animación con **Solo esta unidad** o una copia (la regla del Studio; aún no probado en el juego).
- **«Solo una unidad nueva hecha en este mod tiene animaciones propias»**: la unidad es una del juego. Haz antes una
  unidad nueva a partir de ella (**Nueva unidad a partir de esta…** en su página).
- **Falta Sus animaciones en la página:** la tabla solo existe para una unidad con animaciones propias (un modelo con
  huesos propios). Todas las demás unidades usan las del juego: cámbialas en RUSE Decoy.
- **Un envío que nunca trajiste:** volver a abrir Blender lo guarda aparte. RUSE Decoy lo muestra con **Traer el envío
  guardado aparte** y **Llevarlo a la Papelera de reciclaje** (mira [[Abrir en Blender|Abrir-en-Blender]]).

## Qué se ha probado en el juego

- Los cambios de animación de RUSE Decoy para todas las unidades que las usan (Studio 0.9.8.8).
- **Solo esta unidad**: un pelotón bailando en el sitio mientras todos los demás pelotones seguían como antes
  (noviembre de 2026).
- **Copiar esta animación…**: una copia usada por un pelotón y por un soldado de otro (noviembre de 2026).
- **Cambiar sus animaciones en Blender**: un pelotón de pie y corriendo con un brazo levantado, y Pelotones a caballo
  genéricos cuyos caballos llevan la cabeza alta (noviembre de 2026).
- Las animaciones propias del Pelotón a caballo genérico, elegidas por **La más cercana**, y el viaje como él mismo en
  los trayectos largos (noviembre de 2026).
- Aún no probado en el juego: una velocidad, un sustituto o un hueso cambiados para una sola unidad, y otra animación
  elegida a mano en **Sus animaciones**.

¿Sigues atascado? Pregunta en el [Discord](https://discord.gg/h54t5baNsC), o mira
[[Cuando algo sale mal|Cuando-algo-sale-mal]].

**Siguiente:** [[Abrir en Blender|Abrir-en-Blender]] · [[Modelos y huesos|Modelos-y-huesos]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Unit-Animations]]
