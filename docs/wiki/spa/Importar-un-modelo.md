# Importar un modelo

> **Para:** modders · **Necesitas:** RUSE Studio 0.9.6 o posterior, un mod y un modelo 3D (.3ds, .glb o .gltf) ·
> **Tiempo:** unos minutos

Da a una unidad nueva un modelo 3D propio, de Blender o de cualquier otra herramienta 3D. Así se hizo el
[mod del M1 Abrams](https://github.com/sneadtristen6/Ruse-Mods): el primer modelo traído a R.U.S.E. desde otro programa
3D, visto en el juego.

Un modelo también puede ir en un edificio nuevo, en lugar de una pieza de su aspecto (consulta
[[Edificios y menús de construcción|Edificios-y-menús-de-construcción]]), o en tu mapa como roca, objeto, arbusto o árbol propio
(consulta [[Colocar edificios y árboles|Colocar-edificios-y-árboles]]). Los dos: Studio 0.9.8.8, visto en el juego.

En la página de la unidad todo esto está en **Aspecto y movimientos**: **Importar modelo…** es el botón de la fila **Modelo**, y el resto de opciones del modelo (su tamaño, **Moverlo**) está bajo **Más** de esa fila. Lo que hacen las animaciones del modelo está bajo **Más** de la fila **Sonidos y animación**. La página de un pelotón empieza en cambio por sus soldados, en su tarjeta de pelotón: mira [[Cambiar un pelotón|Cambiar-un-pelotón]].

## 1. Consigue un modelo

Un **.3ds** con sus imágenes (.tga o .png), o un **.glb** o **.gltf** (con las imágenes dentro: PNG, JPG o WebP). Un
modelo que el importador no puede leer (mallas comprimidas, imágenes KTX2) lo dice, y cómo arreglarlo en Blender.

- **Desde Blender:** File > Export > glTF 2.0, formato **glTF Binary (.glb)**.
- **Desde un sitio de modelos gratuitos:** muchos tanques vienen como .3ds con una carpeta de imágenes .tga. Deja la
  carpeta tal como vino: el Studio encuentra las imágenes junto al .3ds o en la carpeta de encima, incluso con los
  nombres acortados que usan los archivos .3ds (`MAIN_DEF.TGA` por `Main_Defuse.tga`).
- Comprueba la licencia del modelo antes de compartir tu mod, y da crédito a su autor en el README de tu mod.

**Lo que ayuda:** piezas con nombres según lo que son. El Studio gira con la torreta una pieza que tenga *turret* en su
nombre (o *tourelle*, *tower*), y también una con *barrel*, *gun* o *cannon*. Una pieza que está sobre la torreta
también gira con ella. Todo lo demás se mueve con el casco. El cañón debe apuntar recto hacia delante.

El ejemplo del Abrams: **«Tank Abrams», de ags**, gratis en
[downloadfree3d.com](https://downloadfree3d.com/3d-models/vehicles/tank/tank-abrams/) (un .3ds y sus imágenes .tga,
con piezas llamadas Main_Body, Main_Turre, Main_Barre...).

## 2. Crea la unidad

En la pestaña **Unidades**, haz clic en **Nueva unidad (importar un modelo)** arriba, y luego elige la unidad de la que
partir (para un tanque, un tanque: el Sherman para el Abrams). Dale un nombre y haz clic en **Crear**: la página de la
unidad nueva se abre en **Importar modelo…**. El modelo de la unidad nueva girará y avanzará como el de esta unidad. La
página de una unidad del juego tiene la misma entrada: **Nueva unidad a partir de esta…** en la fila **Modelo** de **Aspecto y movimientos**.
(El Studio 0.9.6 aún no tiene ninguno de los dos botones: abre la unidad y elige **Nueva unidad…** en su página.)

## 3. Importa

En la página de la unidad nueva, en la fila **Modelo** de **Aspecto y movimientos**:

1. Haz clic en **Más** y ajusta el **Tamaño**: su longitud respecto a la de la unidad copiada. **1** es igual de largo; un M1 Abrams respecto
   a un Sherman es **1.36** (sus longitudes reales).
2. Haz clic en **Importar modelo…** (el botón de la fila) y elige el .3ds o el .glb.

El Studio lo ajusta a la unidad: mirando hacia delante (hacia donde apunta su cañón), su longitud, colocado donde está
la unidad copiada, con su torreta girando en el sitio que tiene en tu modelo, apoyado en el suelo. Sus imágenes pasan a
ser texturas propias. La página lo muestra en 3D, con las piezas que giran con la torreta. Si no se encontró una imagen,
dice cuál: pon las imágenes junto al modelo e impórtalo otra vez.

Se guarda en tu mod como `files/models/<the unit's name>.glb`. **Usar el modelo de la unidad copiada** lo quita otra
vez.

**Dónde está en tu PC:** **Más** de la fila **Modelo** empieza por ahí (la página de un pelotón lo dice en **Más opciones**, debajo de sus soldados): la ruta completa, `Documents\RUSE 2.0\Mods\<tu mod>\files\models\<nombre de la unidad>.glb`, y **Mostrar en la carpeta**, que abre esa carpeta. Mientras la unidad no tenga un modelo propio, dice dónde estará el archivo. Una unidad con su propia copia del modelo (**Darle su propia copia del modelo**, o el **Uniforme personalizado** de un pelotón) se guarda en la misma carpeta, como `<nombre de la unidad>.copy.toml`, y su pintura en la carpeta del mismo nombre.

**Su tamaño más tarde:** el control deslizante bajo el cuadro del tamaño va de **Diminuto** a **Enorme** (de 0.05 a
20), con **Tamaño del juego** (1) y, en una unidad de época, **Tamaño real** marcados; haz clic en **Cambiar tamaño** y
el modelo se ajusta otra vez a partir de su propio archivo. Con varios aviones nuevos (o unidades terrestres), un clic
les cambia el tamaño a todos. El juego lee un modelo cuando carga, así que un tamaño nuevo se ve a partir de la
siguiente construcción.

**Dónde queda:** un modelo nuevo se pone en el centro de la unidad que copia, así que a la mayoría de los modelos no les
hace falta nada aquí. Si el tuyo no queda bien colocado, usa **Moverlo** bajo el tamaño, en **Más** de la fila
Modelo. Pide tres números, **Adelante**, **Derecha** y **Arriba**, en unidades del juego (la página
dice cuánto mide la unidad copiada en esas unidades). Un menos va al otro lado, y 0, 0, 0 lo devuelve a donde se ajustó.
Haz clic en **Mover** y el modelo se ajusta otra vez a partir de su propio archivo, movido esa distancia; su torreta y
sus hélices van con él, así que siguen girando en el sitio correcto. En la vista 3D, el anillo azul es donde está la
unidad copiada, y la marca del anillo es el frente. Un tamaño nuevo conserva el movimiento. Un modelo ligado a los
huesos de la unidad (un soldado, la dotación de un cañón) se queda donde están sus huesos: ese, muévelo en Blender. Un
modelo importado antes del Studio 0.9.8.17 conserva su sitio de antes (su torreta sobre la torreta de la unidad
copiada), aunque le cambies el tamaño, hasta que lo importes otra vez o lo muevas; los modelos de las unidades de época
conservan el suyo.

**Los aviones:** un avión abierto en Blender desde el Studio y traído de vuelta mira hacia delante y conserva sus
hélices donde las tiene tu modelo, tantas como tenga, sin importar las que tuviera el avión que copia: palas en el
suelo, discos girando en el aire. Visto en el juego. Un modelo de cualquier otro sitio conserva sus hélices tal como
están dibujadas, quietas: el importador aún no sabe distinguir cuáles de sus piezas son hélices. En la vista 3D, los
discos de un avión se ven transparentes, como el juego dibuja una hélice que gira.

**Soldados, dotaciones y más aviones:** los soldados, la dotación de un cañón y los aviones a los que el Studio antes no
podía ajustar un modelo (el P-47, por ejemplo) también admiten un modelo propio, si está ligado a los huesos de la
unidad: uno de los modelos del juego abierto en Blender desde el Studio y cambiado allí, por ejemplo. Va sobre esos
huesos tal cual, sin mover ni escalar nada, y los demás hombres de un pelotón dibujados con el mismo modelo también lo llevan.
Visto en el juego con un pelotón de fusileros, la dotación de un cañón y el P-47. Un soldado con arma pesada que el
juego dibuja con un modelo propio (el del bazuca del pelotón de fusileros de EE. UU.) lo conserva hasta que le des uno
en su propia línea de la página del pelotón (más abajo).

**Tus jugadores:** un mod con un modelo importado con el Studio 0.9.8.17 o posterior necesita el Launcher 0.4.8.17 o más
reciente: un Launcher más antiguo le da al modelo el esqueleto de la unidad copiada, así que su torreta gira alrededor
del punto equivocado. La 0.4.8.17 es una actualización obligatoria, así que el Launcher la instala solo.

## Tu propio soldado, paso a paso

Para un pelotón (fusileros, paracaidistas, cualquier infantería) el Studio hace la parte de Blender contigo. La página de un
pelotón empieza por su tarjeta de pelotón y una línea para cada uno de sus soldados; [[Cambiar un pelotón|Cambiar-un-pelotón]] los recorre.

1. **Crea el pelotón** como en el paso 2 de arriba, a partir de un pelotón (el pelotón de fusileros de EE. UU., por ejemplo).
2. **Abre el pelotón en Blender.** En la tarjeta de pelotón, pulsa **Cambiar el pelotón en Blender**. Blender se abre con todos los soldados del pelotón uno al lado del otro, cada uno sobre sus huesos, cada uno con su propia copia de sus imágenes. ¿Todavía no tienes Blender? **Conseguir Blender (gratis)** lo instala; **Elegir Blender…** le muestra al Studio dónde está.
3. **Cambia un soldado, o pon tu propio modelo sobre sus huesos.** Para cambiarlo, edítalo allí. Para un modelo tuyo: tráelo con **File > Import** a la misma escena y colócalo sobre el soldado; haz clic en tu modelo, **Mayús+clic** en sus huesos y luego **Ctrl+P > With Automatic Weights**. Borra el soldado del juego si no te lo quedas.
4. **Envíalo.** Pulsa **Enviar a R.U.S.E. Studio** arriba en Blender.
5. **Tráelo de vuelta.** En la tarjeta de pelotón, pulsa **Traer mis cambios**. Cada soldado recibe solo lo que se le hizo a él, y el que no tocaste se queda como estaba: la tarjeta dice quién cambió y quién no. **Probar en el juego** lo muestra.

Bueno saber:
- Los cuatro fusileros del pelotón de fusileros de EE. UU. son una sola figura en Blender: el juego les da un solo modelo, así que lo que le hagas lo llevan los cuatro. Su soldado del bazuca es una figura propia.
- Tus archivos de Blender se quedan en la carpeta de tu mod: `Documents\RUSE 2.0\Mods\<tu mod>\blender\<nombre de la unidad>\squad\`. No se empaquetan en tu mod cuando lo compartes. **Más opciones**, debajo de los soldados, dice dónde están, y su **Mostrar en la carpeta** abre la carpeta donde están.
- ¿Cerraste Blender antes de traer tus cambios? El pequeño **Traer mis cambios** bajo el botón grande toma lo último que enviaste.
- Si algunos puntos de tu modelo no tienen hueso (los pesos automáticos de Blender se saltan algunos), la página dice cuántos: se mueven solo con la cadera del soldado. Píntalos sobre un hueso en **Weight Paint** y envíalo de nuevo.
- Un pelotón con **Uniforme personalizado**: tu modelo ocupa el lugar del uniforme (su pintura queda en tu mod); cuando cada soldado vuelve al aspecto del juego (**Volver al aspecto del juego** en su línea), el uniforme vuelve.
- ¿Ya tienes un .glb hecho sobre los huesos del soldado del juego? **Importar un modelo…** en la línea de ese soldado lo toma tal cual.
- Tu mod guarda el modelo de cada soldado en `files\models\`: el de los fusileros como `<nombre de la unidad>.glb`, el del soldado con arma pesada como `<nombre de la unidad>@bazooka.glb`. **Más opciones** dice dónde se guarda cada uno (o se guardará), y qué otras figuras del pelotón se dibujan con él: el soldado caído y la figura vista de lejos (la del pelotón de fusileros de EE. UU. se dibuja con el modelo de su soldado del bazuca).
- Todo el pelotón en un solo Blender, cada soldado traído por separado: es nuevo, todavía no probado en el juego.

## Sus animaciones: cuál reproduce cada acción

Un modelo sobre huesos propios (un caballo, un caballo con su jinete, cualquier criatura) trae consigo sus animaciones.
En la página de la unidad, **Sus animaciones** muestra qué reproduce la unidad para cada cosa que hace en el juego:

- **Se queda quieto**, **Camina** y **Corre** van primero: lo mínimo que necesita un modelo. Si alguna no tiene nada
  propio, la página lo dice, y qué reproduce en su lugar.
- Cada acción es una lista de las animaciones del modelo. Elige una, o déjala en **La más cercana**: entonces
  reproduce la más parecida que tenga el modelo, y la lista dice cuál. La más cercana es, por orden: una animación con
  el nombre de esa acción (stand o idle, walk, run o gallop, fire, death...), si no, lo que reproduce la acción más
  cercana (caminar el correr, correr el caminar, luego el estar quieto; disparar el apuntar, luego el estar quieto;
  toda muerte la muerte simple). La compilación sigue la misma regla: lo que dice la página es lo que reproduce el
  juego.
- Una animación cuyo nombre empieza por t_ o b_ (hr_t_fire, hr_b_run) se reproduce solo en la mitad de arriba o de
  abajo del cuerpo: las de un jinete arriba, las de su caballo abajo.
- **Todas las demás acciones** lista el resto, por tipo: quieto, en movimiento, apuntar y disparar, el arma pesada,
  recibir impactos, morir.
- **En los trayectos largos** el juego mete a un pelotón en su camión. Una unidad con animaciones propias va por sí
  misma en su lugar, reproduciendo la animación elegida ahí (su correr si la dejas en La más cercana), tan rápido como
  su camión. Elige **En su camión** para quedarte con el camión.

**Una copia conserva sus animaciones:** una unidad copiada de otra con animaciones propias reproduce las mismas. Para
cambiar una solo para ella, haz clic en **Cambiar en RUSE Decoy** en su fila **Sonidos y animación** y luego en **Solo esta unidad**.

El Pelotón a caballo genérico hecho así en el Studio se jugó en el juego (noviembre de 2026).
## Un modelo con huesos y animaciones propios

Un caballo, un caballo con su jinete, cualquier criatura: un modelo sobre sus propios huesos va en un pelotón con sus animaciones.

1. **Hazlo en Blender**: tu modelo sobre una armadura con huesos propios (con los nombres que quieras) y una acción para cada animación. Nombra las acciones según lo que muestran: al menos **stand** (o **idle**), **walk** y **run**; también se reconocen **death**, **fire**, **reload**, **hit**, **crouch**, **aim**, **look**, **flee** y **grenade**.
2. **Expórtalo**: **File > Export > glTF 2.0**, formato **glTF Binary (.glb)**, con **Animation** marcado.
3. **Crea el pelotón** como en el paso 2 de arriba. En su página, pulsa **Importar un modelo…** en la línea de los fusileros, bajo **Cada soldado**, y elige tu .glb. El Studio ve que sus huesos no son los del soldado y lo toma con sus propios huesos y todas sus animaciones. La página muestra cuántos huesos tiene, cada animación con su duración y cuántas acciones del pelotón la hacen.
4. **Probar en el juego** lo muestra.

Bueno saberlo:
- Cada acción del pelotón hace la animación nombrada para ella. Una acción para la que no hay ninguna animación nombrada todavía no tiene ninguna: la página dice cuántas.
- ¿Lo cambiaste en Blender? Impórtalo de nuevo: cada acción mantiene su animación mientras en el archivo siga habiendo una animación con ese nombre.
- Tu mod guarda el modelo y cada animación: `files\models\<nombre de la unidad>.glb`, y cada animación como `files\anim\own\<nombre de la unidad>\<su nombre>.baf`.
- **Volver al aspecto del juego** en esa línea vuelve a quitar el modelo, con sus animaciones.
- Un pelotón con soldado con arma pesada: dale su propio caballo con jinete con **Importar un modelo…** en su línea, hecho sobre los mismos huesos que el de los fusileros, y hará sus animaciones. Sobre otros huesos hace lo que hacía en el pelotón copiado, y la página te avisa: eso puede detener el juego. Quitar el modelo de los fusileros quita también el suyo.
- El Pelotón a caballo genérico hecho así en el Studio se jugó en el juego (noviembre de 2026); nada más hecho así se ha probado todavía en el juego.

## Sus animaciones, cambiadas en Blender

Las animaciones se cambian en RUSE Decoy. En la página de la unidad, en la fila **Sonidos y animación**, pulsa **Cambiar en RUSE Decoy**, y luego **Cambiar sus animaciones en Blender** bajo sus animaciones. Blender se abre con la unidad y cada animación que reproduce (de pie, caminar, correr, disparo, muerte…), cada una con el nombre de lo que hace en ella y después el nombre del juego: `Correr, apuntando (fusilier_course_vise)`.

1. **Elige una.** Abajo en Blender, el Action Editor las enumera: elige la que quieres cambiar. **Espacio** la reproduce.
2. **Coloca los huesos.** Haz clic en un hueso, pulsa **Ctrl+Tab** para el Pose Mode, **R** para girarlo (**G** lo mueve) y luego **I** para guardar la pose en este fotograma. Hazlo en cada fotograma que cambies: Blender pasa solo de una pose guardada a la siguiente.
3. **Envíala.** Pulsa **Enviar a R.U.S.E. Studio**: van todas las animaciones, cambiadas o no.
4. **Tráela de vuelta.** En RUSE Decoy, pulsa **Traer mis cambios**. Dice cuáles volvieron cambiadas: ahora son propias de esta unidad, y RUSE Decoy las muestra en **Solo esta unidad**. Cada otra unidad, y cada animación que no tocaste, sigue siendo la del juego.

Conviene saber:
- El juego reproduce las animaciones a 30 fotogramas por segundo, y Blender las abre así. Una animación se abre con la duración que le da el juego; alárgala o acórtala en Blender y vuelve así.
- Una animación hecha en Blender (una copia de otra, renombrada) también vuelve, pero aún no la reproduce ninguna acción: el Studio lo dice. Una renombrada cuenta como nueva, y la que era se reproduce como antes.
- Los huesos en los que no se apoya ningún punto del soldado (el punto de la boca del arma, la mano de la segunda arma) se pueden animar, pero los pesos automáticos de Blender los dejan fuera.
- Solo una unidad nueva hecha en tu mod tiene animaciones propias: para una unidad del juego, crea primero una unidad nueva a partir de ella.
- Un modelo sobre sus propios huesos (un caballo, cualquier criatura) envía sus propias animaciones, con sus propios nombres. La que cambies ocupa su lugar: cada acción que la reproducía la reproduce cambiada, y la fila **Sonidos y animación** de la unidad la lista con las demás.
- Comprobado con Blender 4.5 y las pruebas del propio Studio; aún no probado en el juego.

## 4. Su tarjeta, y luego la prueba

Gira la vista 3D hasta que el nuevo modelo se vea bien dentro del marco discontinuo y haz clic en **Usar esta vista
como tarjeta** (consulta [[Editar unidades|Editar-unidades]]). Luego **Probar en el juego**: la unidad está en su fábrica en
una batalla.

## Cambiarlo en Blender

`files/models/<the unit's name>.glb` se abre en Blender como cualquier .glb. Conserva los dos nombres de objeto
(`chassis` para el casco, `tourelle_01` para la torreta) y expórtalo sobre el mismo archivo (glTF Binary): la siguiente
construcción lo usa.

**Abrir en Blender**, en la página de una unidad, nombra el hueso de cada pieza como lo hace el juego, así que uno de
los tanques del propio juego abierto en Blender e importado de vuelta conserva su torreta girando (Studio 0.9.8.8; un
modelo exportado antes conserva sus nombres viejos: ábrelo otra vez en Blender).

**Un modelo que quedaba en el sitio equivocado** (Studio 0.9.8.7 y anteriores, en unidades nuevas hechas a partir del
Panther y de otras 85 unidades cuyas torretas el Studio leía mal): usa otra vez **Importar modelo…** en esa unidad, y
queda sobre la torreta.

## En fase temprana

- Las orugas y las ruedas aún no giran: se mueven con el casco.
- El fogonazo del cañón y los restos son los de la unidad copiada.
- Las imágenes se hacen de 1024 de ancho como máximo, como las imágenes de las unidades del propio juego.
- Probado en el juego con los propios modelos del juego (el Sherman, dos aviones, un pelotón de fusileros, la dotación
  de un cañón): aún no con un modelo de otro sitio, otro tanque con torreta, una torreta que da la vuelta completa ni un
  avión que copie una unidad sin hélices.
- Una unidad nueva copiada de un cañón remolcado, del FCM F1, del Puma, de un semioruga, del Bren Carrier, de un avión
  de paracaidistas, de algunos búnkeres y de unos pocos más también admite un modelo de otro sitio, no solo uno ligado a
  sus huesos, y se dibuja como esa unidad. Aún no probado en el juego.

Desde la línea de comandos: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. Con `--move`, se ajusta como lo ajusta el Studio:
`--move 50 0 -10` lo mueve 50 hacia delante y 10 hacia abajo desde donde está ajustado (adelante, derecha, arriba), y
`--move 0 0 0` lo deja ahí. Sin `--move`, el comando aún lo ajusta a la manera antigua, con su torreta sobre la torreta
de la unidad copiada.

**Siguiente:** [[Exportar y compartir|Exportar-y-compartir]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Import-a-Model]]
